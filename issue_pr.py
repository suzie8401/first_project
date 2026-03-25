from flask import Flask, request, jsonify
import csv
import io
from urllib.request import urlopen

app = Flask(__name__)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1OQG4QlSQLRdElB0VdXO7gmI0dMGtXddChglK_pJCJh8/export?format=csv&gid=0"


def load_sheet_data():
    with urlopen(SHEET_URL) as response:
        content = response.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    return list(reader)


def find_answer(user_input: str) -> str:
    text = user_input.strip().lower()
    rows = load_sheet_data()

    rows.sort(key=lambda r: len(str(r.get("keyword", ""))), reverse=True)

    for row in rows:
        keyword = str(row.get("keyword", "")).strip().lower()
        answer = str(row.get("answer", "")).strip()

        if keyword and keyword in text:
            return answer.replace("\\n", "\n")

    return (
        "질문을 이해하지 못했어요.\n\n"
        "예시 입력:\n"
        "- 우선순위\n"
        "- 심각도\n"
        "- 우선순위와 심각도 차이\n"
        "- Highest\n"
        "- High\n"
        "- Critical\n"
        "- QA\n"
        "- QC\n"
        "- 품질\n"
        "- 이슈 등록"
    )


@app.route("/", methods=["GET"])
def home():
    return "QA 챗봇 서버 실행 중!"


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        body = request.get_json(silent=True) or {}
        user_input = body.get("userRequest", {}).get("utterance", "")
        answer = find_answer(user_input)

        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": answer
                        }
                    }
                ]
            }
        })
    except Exception as e:
        print("에러:", e)
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "서버 처리 중 오류가 발생했습니다."
                        }
                    }
                ]
            }
        })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
