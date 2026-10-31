#!/usr/bin/env python3

import rclpy
import json
import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path

from rclpy.node import Node
from rclpy.action import ActionClient

from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint
from builtin_interfaces.msg import Duration

plt.rcParams["font.family"] = "Noto Sans CJK JP"


class TrajectorySender(Node):

    def __init__(self):
        super().__init__("trajectory_sender")

        self._action_client = ActionClient(
            self,
            FollowJointTrajectory,
            "/joint_trajectory_controller/follow_joint_trajectory"
        )

        # ==========================================
        # Joint names
        # ==========================================

        self.joint_names = [
            "shoulder_pan_joint",
            "shoulder_lift_joint",
            "elbow_joint",
            "wrist_1_joint",
            "wrist_2_joint",
            "wrist_3_joint"
        ]

        # ==========================================
        # JSON file
        # ==========================================

        self.json_path = (
            Path(__file__).resolve().parent / "traj.json"
        )

        # ==========================================
        # Initial joint position [rad]
        # ==========================================

        self.initial_joints = [
            0.40,
            -0.80,
            1.00,
            -1.50,
            -1.57,
            0.50
        ]

        # ==========================================
        # Trajectory parameters
        # ==========================================

        self.point_interval = 0.1

        self.stroke_interval = 1.0

        self.trajectory_data = []

        self.strokes = []

        self.character = ""

        self.stroke_times = []

        # Load JSON
        self.load_trajectory()

    # ==========================================
    # Load JSON trajectory
    # ==========================================

    def load_trajectory(self):

        if not self.json_path.exists():

            raise FileNotFoundError(
                f"JSON file not found: {self.json_path}"
            )

        with open(
            self.json_path,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        self.character = data["character"]

        self.strokes = sorted(
            data["strokes"],
            key=lambda stroke: stroke["order"]
        )

        self.get_logger().info(
            f"Character: {self.character}"
        )

        self.get_logger().info(
            f"Stroke count: {len(self.strokes)}"
        )

        # ======================================
        # Extract XY coordinates
        # ======================================

        all_points = []

        for stroke in self.strokes:

            points = stroke["points"]

            for point in points:

                all_points.append([
                    float(point["x"]),
                    float(point["y"])
                ])

        self.xy_points = np.array(all_points)

        self.get_logger().info(
            f"Loaded {len(self.xy_points)} trajectory points."
        )

        # Convert XY coordinates to joint positions
        self.convert_to_joint_trajectory()

    # ==========================================
    # Convert XY coordinates to joint angles
    # ==========================================

    def xy_to_joint_positions(self, x, y):

        # --------------------------------------
        # Normalize coordinates
        # --------------------------------------

        x_min = np.min(self.xy_points[:, 0])
        x_max = np.max(self.xy_points[:, 0])

        y_min = np.min(self.xy_points[:, 1])
        y_max = np.max(self.xy_points[:, 1])

        x_norm = (
            (x - x_min) / (x_max - x_min) * 2.0 - 1.0
        )

        y_norm = (
            (y - y_min) / (y_max - y_min) * 2.0 - 1.0
        )

        # --------------------------------------
        # Temporary mapping
        #
        # IMPORTANT:
        # This is NOT inverse kinematics.
        # Replace this function with actual IK.
        # --------------------------------------

        joints = self.initial_joints.copy()

        joints[0] = self.initial_joints[0] + 0.1 * x_norm

        joints[1] = self.initial_joints[1] + 0.1 * y_norm

        return joints

    # ==========================================
    # Convert complete trajectory
    # ==========================================

    '''
    def convert_to_joint_trajectory(self):

        self.trajectory_data = []

        current_time = 2.0

        # Initial position
        self.trajectory_data.append(
            (
                self.initial_joints.copy(),
                current_time
            )
        )

        for stroke_index, stroke in enumerate(self.strokes):

            points = stroke["points"]

            for point in points:

                x = float(point["x"])
                y = float(point["y"])

                joints = self.xy_to_joint_positions(x, y)

                current_time += self.point_interval

                self.trajectory_data.append(
                    (
                        joints,
                        current_time
                    )
                )

            # Pause between strokes
            current_time += self.stroke_interval

        self.get_logger().info(
            f"Generated {len(self.trajectory_data)} joint points."
        )
    '''

    def convert_to_joint_trajectory(self):

        self.trajectory_data = []

        self.stroke_times = []

        current_time = 2.0

        # Initial position
        self.trajectory_data.append(
            (
                self.initial_joints.copy(),
                current_time
            )
        )

        for stroke_index, stroke in enumerate(self.strokes):

            points = stroke["points"]

            # この画の開始時間
            stroke_start_time = current_time

            for point in points:

                x = float(point["x"])
                y = float(point["y"])

                joints = self.xy_to_joint_positions(x, y)

                current_time += self.point_interval

                self.trajectory_data.append(
                    (
                        joints,
                        current_time
                    )
                )

            # この画の終了時間
            stroke_end_time = current_time

            self.stroke_times.append({
                "order": stroke["order"],
                "start": stroke_start_time,
                "end": stroke_end_time
            })

            # Pause between strokes
            current_time += self.stroke_interval

        self.get_logger().info(
            f"Generated {len(self.trajectory_data)} joint points."
        )

    # ==========================================
    # Plot trajectory
    # ==========================================

    def plot_trajectory(self):

        plt.figure(figsize=(8, 8))

        for i, stroke in enumerate(self.strokes):

            points = stroke["points"]

            x = [p["x"] for p in points]

            y = [p["y"] for p in points]

            plt.plot(
                x,
                y,
                marker="o",
                markersize=2,
                linewidth=2,
                label=f"Stroke {stroke['order']}"
            )

            # Start point
            plt.scatter(
                x[0],
                y[0],
                color="green",
                s=40
            )

            # End point
            plt.scatter(
                x[-1],
                y[-1],
                color="red",
                s=40
            )

        plt.xlabel("X")
        plt.ylabel("Y")

        plt.title(
            f"Trajectory for Character {self.character}"
        )

        plt.gca().invert_yaxis()

        plt.axis("equal")

        plt.grid(True)

        plt.legend()

        plt.tight_layout()

        plt.show()

    # ==========================================
    # Send trajectory to UR5e
    # ==========================================

    def send_goal(self):

        # Show trajectory first
        self.plot_trajectory()

        answer = input(
            "\n軌道を確認しましたか？"
            "\n実行する場合は RUN と入力してください: "
        )

        if answer.strip() != "RUN":

            self.get_logger().warning(
                "Trajectory execution cancelled."
            )

            return

        self.get_logger().info(
            "Waiting for trajectory action server..."
        )

        if not self._action_client.wait_for_server(
            timeout_sec=10.0
        ):

            self.get_logger().error(
                "Action server not available!"
            )

            return

        goal_msg = FollowJointTrajectory.Goal()

        goal_msg.trajectory.joint_names = self.joint_names

        # ======================================
        # Create trajectory points
        # ======================================

        # 速度倍率
        SPEED_FACTOR = 2.0

        for joints, t in self.trajectory_data:

            point = JointTrajectoryPoint()

            # 6軸の関節角度
            point.positions = [float(x) for x in joints]

            # 3倍速にする
            scaled_time = float(t) / SPEED_FACTOR

            # 秒とナノ秒に分割
            sec = int(scaled_time)

            nanosec = int(
                (scaled_time - sec) * 1e9
            )

            point.time_from_start.sec = sec

            point.time_from_start.nanosec = nanosec

            goal_msg.trajectory.points.append(point)


        # ======================================
        # Send goal
        # ======================================

        self.get_logger().info(
            f"Sending trajectory for {self.character}..."
        )

        # 画数カウンタ
        current_stroke = 0

        # Feedback受信時に呼び出す関数
        def feedback_callback(feedback_msg):

            nonlocal current_stroke

            feedback = feedback_msg.feedback

            # desiredの軌道時間を取得
            desired_time = (
                feedback.desired.time_from_start.sec
                + feedback.desired.time_from_start.nanosec / 1e9
            )

            # 3倍速を元の時間に戻す
            actual_time = desired_time * SPEED_FACTOR

            #self.get_logger().info(
            #    f"Desired time: {desired_time:.3f} sec"
            #)

            for i, stroke in enumerate(self.stroke_times):

                if (
                    stroke["start"] <= actual_time
                    <= stroke["end"]
                ):

                    stroke_number = i + 1

                    if stroke_number > current_stroke:

                        current_stroke = stroke_number

                        self.get_logger().info(
                            f"========== "
                            f"{stroke_number} / {len(self.strokes)}画目完了 =========="
                        )

                    break


        # Action送信
        send_goal_future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=feedback_callback
        )

        rclpy.spin_until_future_complete(
            self,
            send_goal_future
        )

        goal_handle = send_goal_future.result()

        if goal_handle is None or not goal_handle.accepted:

            self.get_logger().error("Goal rejected!")

            return

        self.get_logger().info(
            "Goal accepted. Waiting for result..."
        )

        result_future = goal_handle.get_result_async()

        rclpy.spin_until_future_complete(
            self,
            result_future
        )

        wrapped_result = result_future.result()

        if wrapped_result is None:

            self.get_logger().error(
                "No trajectory result received."
            )

            return

        result = wrapped_result.result

        self.get_logger().info(
            f"Trajectory finished. Error code: {result.error_code}"
        )

        self.get_logger().info(
            f"Result message: {result.error_string}"
        )


# ==============================================
# Main
# ==============================================

def main(args=None):

    rclpy.init(args=args)

    node = None
    try:
        node = TrajectorySender()
        node.send_goal()
    except KeyboardInterrupt:
        if node is not None:
            node.get_logger().warning(
                "Program interrupted by user."
            )
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
