from flask import Flask, request, jsonify
import csv
import io
import os
from collections import OrderedDict
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

app = Flask(__name__)

SPREADSHEET_ID = "1OQG4QlSQLRdElB0VdXO7gmI0dMGtXddChglK_pJCJh8"
GID = "0"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GID}"

FALLBACK_MESSAGE = (
    "질문을 이해하지 못했어요. 🧐\n\n"
    "예시 키워드:\n"
    "• 우선순위, 심각도, 차이\n"
    "• Highest, High, Critical\n"
    "• QA, QC, 품질, 페이징, 뒤로가기"
)

import re

def normalize_text(text: str) -> str:
    text = str(text)
    text = re.sub(r"\s+", "", text)   # 모든 공백/줄바꿈 제거
    text = text.replace("\u200b", "") # 제로폭 공백 제거
    return text.lower()

def load_sheet_rows():
    try:
        with urlopen(CSV_URL, timeout=10) as response:
            content = response.read().decode("utf-8-sig")
    except HTTPError as e:
        raise Exception(f"구글시트 HTTP 오류: {e.code}")
    except URLError as e:
        raise Exception(f"구글시트 연결 오류: {e.reason}")

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
                break

    matched_answers = list(dict.fromkeys(matched_answers))

    if matched_answers:
        return "\n\n".join(matched_answers)

    return FALLBACK_MESSAGE

@app.route("/", methods=["GET"])
def home():
    return "QA 챗봇 서버 실행 중"

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
                    {"simpleText": {"text": answer}}
                ]
            }
        })
    except Exception as e:
        print(f"[웹훅 오류] {e}")
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [
                    {"simpleText": {"text": "서버 처리 중 오류가 발생했습니다."}}
                ]
            }
        })

@app.route("/test-sheet", methods=["GET"])
def test_sheet():
    try:
        rows = load_sheet_rows()
        bot_data = build_bot_data()
        return jsonify({
            "row_count": len(rows),
            "grouped_count": len(bot_data),
            "raw_rows_preview": rows[:5],
            "grouped_preview": bot_data[:5]
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "csv_url": CSV_URL
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
