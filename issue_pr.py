from flask import Flask, request, jsonify

app = Flask(__name__)

qa_data = {
    "guide": {
        "priority_definition": "우선순위는 이슈를 얼마나 빨리 처리해야 하는지를 나타냅니다.",
        "severity_definition": "심각도는 이슈가 서비스와 사용자에게 미치는 영향의 크기를 나타냅니다.",
        "difference": "우선순위는 처리 시급성, 심각도는 장애 영향도입니다."
    },
    "priority": {
        "Highest": "전체 서비스 사용이 불가능하거나 즉시 대응이 필요한 최상위 우선순위입니다.",
        "High": "핵심 기능 장애로 인해 빠른 대응이 필요한 우선순위입니다.",
        "Medium": "일반 기능 문제로 일정 내 수정이 필요한 우선순위입니다.",
        "Low": "영향도가 낮은 개선 사항 또는 경미한 문제에 해당하는 우선순위입니다."
    },
    "severity": {
        "Critical": "서비스 운영 불가, 데이터 손실, 결제 불가 등 치명적인 장애입니다.",
        "Major": "핵심 기능 수행이 어렵지만 일부 우회가 가능한 수준의 장애입니다.",
        "Minor": "기능 영향은 낮고 사용성 저하 또는 일부 화면 문제 수준의 장애입니다.",
        "Trivial": "오탈자, 문구, 정렬 오류 등 매우 경미한 수준의 문제입니다."
    }
}

def find_answer(user_input: str) -> str:
    text = user_input.strip().lower()

    if "차이" in text and "우선순위" in text and "심각도" in text:
        return qa_data["guide"]["difference"]

    if "우선순위" in text:
        return qa_data["guide"]["priority_definition"]

    if "심각도" in text:
        return qa_data["guide"]["severity_definition"]

    if "highest" in text:
        return f"[Highest]\n{qa_data['priority']['Highest']}"
    if "high" in text:
        return f"[High]\n{qa_data['priority']['High']}"
    if "medium" in text:
        return f"[Medium]\n{qa_data['priority']['Medium']}"
    if "low" in text:
        return f"[Low]\n{qa_data['priority']['Low']}"

    if "critical" in text:
        return f"[Critical]\n{qa_data['severity']['Critical']}"
    if "major" in text:
        return f"[Major]\n{qa_data['severity']['Major']}"
    if "minor" in text:
        return f"[Minor]\n{qa_data['severity']['Minor']}"
    if "trivial" in text:
        return f"[Trivial]\n{qa_data['severity']['Trivial']}"

    if "최상" in text or "최고" in text:
        return f"[Highest]\n{qa_data['priority']['Highest']}"
    if "높음" in text:
        return f"[High]\n{qa_data['priority']['High']}"
    if "보통" in text or "중간" in text:
        return f"[Medium]\n{qa_data['priority']['Medium']}"
    if "낮음" in text:
        return f"[Low]\n{qa_data['priority']['Low']}"

    if "치명" in text:
        return f"[Critical]\n{qa_data['severity']['Critical']}"
    if "주요" in text:
        return f"[Major]\n{qa_data['severity']['Major']}"
    if "경미" in text:
        return f"[Minor]\n{qa_data['severity']['Minor']}"
    if "오탈자" in text or "사소" in text:
        return f"[Trivial]\n{qa_data['severity']['Trivial']}"

    return (
        "질문을 이해하지 못했어요.\n\n"
        "예시 질문:\n"
        "- 우선순위 정의\n"
        "- 심각도 정의\n"
        "- 우선순위와 심각도 차이\n"
        "- Highest 뜻\n"
        "- Critical 뜻"
    )

@app.route("/", methods=["GET"])
def home():
    return "QA 챗봇 서버 실행 중!"

@app.route("/webhook", methods=["POST"])
def webhook():
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
