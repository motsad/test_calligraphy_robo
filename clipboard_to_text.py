
import sys
import pyperclip


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <出力JSONファイル名>")
        print(f"Example: python {sys.argv[0]} ei.json")
        sys.exit(1)

    output_filename = sys.argv[1]

    # クリップボードの内容を取得
    text = pyperclip.paste()

    # テキストファイルに書き出す
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"{output_filename} に保存しました")

if __name__ == "__main__":
    main()

