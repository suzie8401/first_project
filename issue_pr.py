from flask import Flask, request, jsonify

app = Flask(__name__)

# 데이터베이스를 코드 내부에 저장 (관리하기 쉽게 구조화)
BOT_DATA = {
    "우선순위": "우선순위는 이슈를 얼마나 빨리 처리해야 하는지를 나타냅니다.",
    "심각도": "심각도는 이슈가 서비스와 사용자에게 미치는 영향의 크기를 나타냅니다.",
    "차이": "우선순위는 처리 시급성(빨리), 심각도는 장애 영향도(크기)입니다.",
    "highest": "[Highest]\n전체 서비스 사용이 불가능하거나 즉시 대응이 필요한 최상위 우선순위입니다.",
    "high": "[High]\n핵심 기능 장애로 인해 빠른 대응이 필요한 우선순위입니다.",
    "medium": "[Medium]\n일반 기능 문제로 일정 내 수정이 필요한 우선순위입니다.",
    "low": "[Low]\n영향도가 낮은 개선 사항 또는 경미한 문제에 해당하는 우선순위입니다.",
    "critical": "[Critical]\n서비스 운영 불가, 데이터 손실, 결제 불가 등 치명적인 장애입니다.",
    "major": "[Major]\n핵심 기능 수행이 어렵지만 일부 우회가 가능한 수준의 장애입니다.",
    "minor": "[Minor]\n기능 영향은 낮고 사용성 저하 또는 일부 화면 문제 수준의 장애입니다.",
    "trivial": "[Trivial]\n오탈자, 문구, 정렬 오류 등 매우 경미한 수준의 문제입니다.",
    "qa": "Quality Assurance (품질 보증)\n문제가 생기지 않도록 과정 전체를 관리하는 활동입니다.",
    "qc": "Quality Control (품질 관리)\n이미 만들어진 결과물을 검사하여 버그를 찾는 활동입니다.",
    "품질": "사용자가 기대하는 수준에 맞고 만족할 수 있는 상태인가를 판단하는 기준입니다.",
    "페이징": "페이징/페이지네이션\nQA 포인트: 마지막 페이지 버튼 비활성화 여부 확인",
    "뒤로가기": "뒤로가기\nQA 포인트: 이전 상태 유지(스크롤/필터) 확인"
}

def find_answer(user_input: str) -> str:
    # 1. 전처리 (공백 제거 및 소문자화)
    text = user_input.replace(" ", "").lower()
    
    # 2. 키워드 매칭
    # 입력받은 문장에 데이터베이스의 키가 포함되어 있는지 확인
    for key, value in BOT_DATA.items():
        if key in text:
            return value

    # 3. 매칭되는 것이 없을 때 반환할 메시지
    return (
        "질문을 이해하지 못했어요. 🧐\n\n"
        "예시 키워드:\n"
        "• 우선순위, 심각도, 차이\n"
        "• Highest, High, Critical\n"
        "• QA, QC, 품질, 페이징"
    )

@app.route("/", methods=["GET"])
def home():
    return "QA 챗봇 서버 실행 중 (고정 데이터 모드)"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        body = request.get_json(silent=True) or {}
        user_input = body.get("userRequest", {}).get("utterance", "")
        answer = find_answer(user_input)

        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [{"simpleText": {"text": answer}}]
            }
        })
    except Exception as e:
        print(f"에러 발생: {e}")
        return jsonify({
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": "서버 처리 중 오류가 발생했습니다."}}]}
        })

if __name__ == "__main__":
    # 포트 5000번으로 실행
    app.run(host="0.0.0.0", port=5000)
