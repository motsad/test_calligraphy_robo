#!/usr/bin/env python3

import sys
import json
import requests
import xml.etree.ElementTree as ET

from svgpathtools import parse_path
import pyperclip


def kanji_to_json(character):
    code = ord(character)
    filename = f"{code:05x}.svg"

    url = (
        "https://raw.githubusercontent.com/"
        f"KanjiVG/kanjivg/master/kanji/{filename}"
    )

    response = requests.get(url)
    response.raise_for_status()

    root = ET.fromstring(response.content)

    ns = {"svg": "http://www.w3.org/2000/svg"}

    strokes = []

    paths = root.findall(".//svg:path", ns)

    for index, path_element in enumerate(paths):

        stroke_id = path_element.attrib.get("id", "")

        # 筆画以外を除外
        if "-s" not in stroke_id:
            continue

        d = path_element.attrib["d"]

        path = parse_path(d)

        points = []

        # 各画を50点に分割
        for i in range(51):
            t = i / 50
            p = path.point(t)

            points.append({
                "x": round(p.real, 3),
                "y": round(p.imag, 3)
            })

        strokes.append({
            "order": len(strokes) + 1,
            "stroke_id": stroke_id,
            "points": points
        })

    return {
        "character": character,
        "stroke_count": len(strokes),
        "strokes": strokes
    }


def main():
    # コマンドライン引数のチェック
    # 使い方: python script.py <漢字> <出力jsonファイル名>
    if len(sys.argv) < 3:
        print(f"Usage: python {sys.argv[0]} <漢字> <出力JSONファイル名>")
        print("Example: python script.py 永 ei.json")
        sys.exit(1)

    character = sys.argv[1]
    output_filename = sys.argv[2]

    print(f"Fetching stroke data for '{character}' from KanjiVG...")
    try:
        result = kanji_to_json(character)
    except Exception as e:
        print(f"Error fetching data: {e}")
        sys.exit(1)

    # JSON文字列を生成
    json_string = json.dumps(result, ensure_ascii=False, separators=(",", ":"))

    # 指定されたファイル名でJSONを保存
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(json_string)

    prompt_string = """# 指示
下記の筆順軌跡座標データを、書道の楷書風に座標データに変換してください。
# 制約条件
- 起筆・終筆・はねを楷書風の効果を入れる
- 効果は書道作品用に極端に加える
- 終筆の払いはそのままにする（効果を入れない）
- 座標データはなるべく省略しない
# 入力形式
- JSON
# 出力形式
- JSON
- 変数は、character,stroke_count,strokes,order, stroke_id, points, x, yのみを使用
# 筆順軌跡座標データ
    """ + json_string

    # クリップボードにコピー
    pyperclip.copy(prompt_string)

    print(f"\nSuccessfully saved to '{output_filename}'")
    print("JSON copied to clipboard!")

if __name__ == "__main__":
    main()


