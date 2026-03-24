from flask import Flask, request, jsonify

app = Flask(__name__)

bot_data = {
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
    },
    "qa_terms": {
        "QA": "Quality Assurance, 품질 보증\n문제가 생기지 않도록 과정 자체를 관리하는 것입니다. 개발 프로세스를 정의하고, 테스트 전략을 수립하고, 품질 기준을 정하고, 재발 방지 프로세스를 만드는 활동입니다.",
        "QC": "Quality Control, 품질 관리\n이미 만들어진 결과물을 검사하여 문제를 찾는 것입니다. 예를 들면 완성된 앱에서 버그를 테스트하거나, 제품 출고 전에 불량 검사를 하는 것입니다.",
        "Quality": "품질\n사용자가 기대하는 수준에 맞고 만족할 수 있는 상태인가를 판단하는 기준입니다."
    }
}


def find_answer(user_input: str) -> str:
    text = user_input.strip().lower()

    # 차이 설명
    if "차이" in text and "우선순위" in text and "심각도" in text:
        return bot_data["guide"]["difference"]

    # 공통 정의
    if "우선순위" in text:
        return bot_data["guide"]["priority_definition"]

    if "심각도" in text or "이슈등급" in text or "등급" in text:
        return bot_data["guide"]["severity_definition"]

    # QA / QC / 품질
    if "qa" in text or "큐에이" in text or "품질보증" in text or "품질 보증" in text:
        return bot_data["qa_terms"]["QA"]

    if "qc" in text or "품질관리" in text or "품질 관리" in text:
        return bot_data["qa_terms"]["QC"]

    if "품질" in text:
        return bot_data["qa_terms"]["Quality"]

    # Priority 상세
    if "highest" in text or "하이스트" in text or "최상" in text or "최고" in text:
        return f"[Highest]\n{bot_data['priority']['Highest']}"

    if "high" in text or "높음" in text:
        return f"[High]\n{bot_data['priority']['High']}"

    if "medium" in text or "미디엄" in text or "중간" in text or "보통" in text:
        return f"[Medium]\n{bot_data['priority']['Medium']}"

    if "low" in text or "로우" in text or "낮음" in text:
        return f"[Low]\n{bot_data['priority']['Low']}"

    # Severity 상세
    if "critical" in text or "크리티컬" in text or "치명" in text:
        return f"[Critical]\n{bot_data['severity']['Critical']}"

    if "major" in text or "메이저" in text or "주요" in text:
        return f"[Major]\n{bot_data['severity']['Major']}"

    if "minor" in text or "마이너" in text or "경미" in text:
        return f"[Minor]\n{bot_data['severity']['Minor']}"

    if "trivial" in text or "트리비얼" in text or "사소" in text or "오탈자" in text:
        return f"[Trivial]\n{bot_data['severity']['Trivial']}"

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
        "- 품질"
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
