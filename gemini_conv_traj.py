from google import genai
import sys
import pyperclip

client = genai.Client(
    api_key="xxxxxxxx"
)

def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <出力JSONファイル名>")
        print(f"Example: python {sys.argv[0]} ei.json")
        sys.exit(1)

    # クリップボードの内容を取得
    s_prompt = pyperclip.paste()

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=s_prompt
    )

    print(response.text)

    s_ret = response.text

    pattern = r"```json\s*(.*?)```"
    match = re.search(pattern, s_ret, re.DOTALL)

    if match:
        json_content = match.group(1).strip()
    else:
        json_content = s_ret

    output_filename = sys.argv[1]

    # JSONファイルに書き出す
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(json_content)

    print(f"{output_filename} に保存しました")

if __name__ == "__main__":
    main()

