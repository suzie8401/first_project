from flask import Flask, request, jsonify
import csv
import io
import requests
from collections import OrderedDict

app = Flask(__name__)

# 사용 중인 구글시트
SPREADSHEET_ID = "1OQG4QlSQLRdElB0VdXO7gmI0dMGtXddChglK_pJCJh8"
GID = "0"

# 공개 시트일 때 바로 CSV로 읽는 주소
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GID}"

# 네트워크 문제 시 임시 응답용
FALLBACK_MESSAGE = (
    "질문을 이해하지 못했어요. 🧐\n\n"
    "예시 키워드:\n"
    "• 우선순위, 심각도, 차이\n"
    "• Highest, High, Critical\n"
    "• QA, QC, 품질, 페이징, 뒤로가기"
)


def normalize_text(text: str) -> str:
    """공백/줄바꿈 제거 + 소문자화"""
    return str(text).replace(" ", "").replace("\n", "").replace("\r", "").strip().lower()


def load_sheet_rows():
    """
    구글시트에서 CSV를 읽어 A열(keyword), B열(answer)을 가져온다.
    시트 헤더는 keyword, answer 라고 가정.
    """
    resp = requests.get(CSV_URL, timeout=10)
    resp.raise_for_status()

    # utf-8-sig: BOM 제거 대응
    content = resp.content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))

    rows = []
    for row in reader:
        keyword = (row.get("keyword") or "").strip()
        answer = (row.get("answer") or "").strip()

        if not keyword or not answer:
            continue

        rows.append({
            "keyword": keyword,
            "answer": answer
        })

    return rows


def build_bot_data():
    """
    같은 answer를 기준으로 키워드를 묶어서
    [
      {"answer": "...", "keywords": ["우선순위", "priority"]},
      ...
    ]
    형태로 변환
    """
    rows = load_sheet_rows()

    grouped = OrderedDict()

    for row in rows:
        answer = row["answer"]
        keyword = normalize_text(row["keyword"])

        if answer not in grouped:
            grouped[answer] = []

        if keyword not in grouped[answer]:
            grouped[answer].append(keyword)

    bot_data = []
    for answer, keywords in grouped.items():
        # 긴 키워드 우선 정렬 (highest가 high보다 먼저 매칭되게)
        keywords = sorted(keywords, key=len, reverse=True)
        bot_data.append({
            "answer": answer,
            "keywords": keywords
        })

    return bot_data


def find_answer(user_input: str) -> str:
    text = normalize_text(user_input)

    if not text:
        return "질문을 입력해주세요."

    try:
        bot_data = build_bot_data()
    except Exception as e:
        print(f"[시트 로딩 오류] {e}")
        return "구글시트 데이터를 불러오지 못했어요. 시트 공개 여부와 URL을 확인해주세요."

    matched_answers = []

    for item in bot_data:
        for keyword in item["keywords"]:
            if keyword and keyword in text:
                matched_answers.append(item["answer"])
                break  # 같은 answer 중복 방지

    # 중복 제거
    matched_answers = list(dict.fromkeys(matched_answers))

    if matched_answers:
        return "\n\n".join(matched_answers)

    return FALLBACK_MESSAGE


@app.route("/", methods=["GET"])
def home():
    return "QA 챗봇 서버 실행 중 (Google Sheets CSV 연동 모드)"


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
        print(f"[웹훅 오류] {e}")
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


@app.route("/test-sheet", methods=["GET"])
def test_sheet():
    """
    시트가 실제로 잘 읽히는지 확인용
    """
    try:
        rows = load_sheet_rows()
        bot_data = build_bot_data()

        return jsonify({
            "raw_rows_preview": rows[:10],
            "grouped_preview": bot_data[:10],
            "row_count": len(rows),
            "grouped_count": len(bot_data)
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "csv_url": CSV_URL
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
