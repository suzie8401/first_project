from flask import Flask, request, jsonify
import csv
import io
from urllib.request import urlopen
from difflib import SequenceMatcher

app = Flask(__name__)

# 구글 시트 '웹에 게시' -> CSV URL (주신 URL을 그대로 사용하되, 로직을 보강합니다)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQXNJX95FQ9nuyvwKmUJy9fGHnmrRDLkOBV7X4a6d3uAkHlYKuFo6k2RF3Xv4KBg6b2jWOJcamau9D8/pub?gid=0&single=true&output=csv"

def load_sheet_data():
    try:
        # 캐시 방지를 위해 URL 뒤에 타임스탬프를 붙일 수도 있으나, 우선 기본 호출
        with urlopen(SHEET_URL) as response:
            content = response.read().decode("utf-8")
        
        # BOM(Byte Order Mark) 제거 및 공백 정리
        content = content.lstrip('\ufeff')
        reader = csv.DictReader(io.StringIO(content))
        
        # 컬럼명에서 발생할 수 있는 공백 제거 및 소문자화하여 리스트 생성
        data = []
        for row in reader:
            clean_row = {k.strip().lower(): v for k, v in row.items() if k}
            data.append(clean_row)
        return data
    except Exception as e:
        print(f"시트 로딩 에러: {e}")
        return []

def normalize_text(text: str) -> str:
    if not text: return ""
    # 특수 공백(\xa0), 줄바꿈, 양끝 공백을 모두 제거하고 소문자로 변환
    return str(text).replace("\xa0", "").replace("\n", "").replace(" ", "").strip().lower()

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def find_answer(user_input: str) -> str:
    raw_text = user_input.strip()
    text = normalize_text(raw_text)
    rows = load_sheet_data()

    if not rows:
        return "데이터를 불러오는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

    best_score = 0.0
    best_answer = None
    best_keyword = None

    for row in rows:
        # 시트의 'keyword'와 'answer' 컬럼을 가져옴 (대소문자 무관)
        keyword_raw = str(row.get("keyword", ""))
        answer_raw = str(row.get("answer", ""))
        
        if not keyword_raw or not answer_raw:
            continue

        normalized_keyword = normalize_text(keyword_raw)

        # 1) 정확히 일치하거나 키워드가 포함된 경우 (가장 높은 우선순위)
        if normalized_keyword in text or text in normalized_keyword:
            return answer_raw.replace("\\n", "\n")

        # 2) 유사도 점수 계산
        score = similarity(text, normalized_keyword)
        if score > best_score:
            best_score = score
            best_answer = answer_raw
            best_keyword = keyword_raw

    # 로깅 (디버깅용)
    print(f"입력: {raw_text} | 최선의 키워드: {best_keyword} | 점수: {best_score}")

    # 3) 유사도 기준 완화 (0.55 -> 0.45)
    if best_score >= 0.45:
        return best_answer.replace("\\n", "\n")

    return (
        "질문을 이해하지 못했어요. 🧐\n\n"
        "아래 키워드 위주로 질문해보세요!\n"
        "예: 우선순위, 심각도, 페이징, QA/QC, GNB"
    )

@app.route("/", methods=["GET"])
def home():
    return "QA 챗봇 서버 정상 작동 중!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        body = request.get_json(silent=True) or {}
        # 카카오톡 utterance 추출
        user_input = body.get("userRequest", {}).get("utterance", "")
        
        if not user_input:
            return jsonify({"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "말씀을 입력해주세요!"}}]}})

        answer = find_answer(user_input)

        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [{"simpleText": {"text": answer}}]
            }
        })
    except Exception as e:
        print(f"Webhook 에러: {e}")
        return jsonify({
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": "잠시 후 다시 시도해주세요."}}]}
        })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
