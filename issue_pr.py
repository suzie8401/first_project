from flask import Flask, request, jsonify
import csv
import io
from urllib.request import urlopen
from difflib import SequenceMatcher

app = Flask(__name__)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1OQG4QlSQLRdElB0VdXO7gmI0dMGtXddChglK_pJCJh8/export?format=csv&gid=0"


def load_sheet_data():
    with urlopen(SHEET_URL) as response:
        content = response.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    return list(reader)


def normalize_text(text: str) -> str:
    return text.strip().lower().replace(" ", "")


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def find_answer(user_input: str) -> str:
    raw_text = user_input.strip()
    text = normalize_text(raw_text)
    rows = load_sheet_data()

    # 1) 정확/부분 매칭 먼저
    for row in rows:
        keyword = normalize_text(str(row.get("keyword", "")))
        answer = str(row.get("answer", "")).strip()

        if keyword and keyword in text:
            return answer.replace("\\n", "\n")

    # 2) 유사도 검색
    best_score = 0.0
    best_answer = None
    best_keyword = None

    for row in rows:
        keyword = normalize_text(str(row.get("keyword", "")))
        answer = str(row.get("answer", "")).strip()

        if not keyword:
            continue

        score = similarity(text, keyword)

        if score > best_score:
            best_score = score
            best_answer = answer
            best_keyword = keyword

    print("입력값:", raw_text)
    print("최고 유사 키워드:", best_keyword)
    print("유사도 점수:", best_score)

    # 3) 일정 점수 이상일 때만 반환
    if best_score >= 0.55:
        return best_answer.replace("\\n", "\n")

    return (
        "질문을 이해하지 못했어요.\n\n"
        "예시 입력:\n"
        "- 우선순위\n"
        "- 심각도\n"
        "- QA\n"
        "- QC\n"
        "- 품질\n"
        "- 레이어\n"
        "- 에러메시지"
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
