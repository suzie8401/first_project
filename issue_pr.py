from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1OQG4QlSQLRdElB0VdXO7gmI0dMGtXddChglK_pJCJh8/export?format=csv&gid=0"


def load_sheet_data():
    df = pd.read_csv(SHEET_URL)
    df = df.fillna("")
    return df


def find_answer(user_input: str) -> str:
    text = user_input.strip().lower()
    df = load_sheet_data()

    # 더 긴 키워드를 먼저 검사해서
    # "high"보다 "highest"가 먼저 매칭되게 함
    df["keyword_len"] = df["keyword"].astype(str).apply(len)
    df = df.sort_values(by="keyword_len", ascending=False)

    for _, row in df.iterrows():
        keyword = str(row["keyword"]).strip().lower()
        answer = str(row["answer"]).strip()

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

