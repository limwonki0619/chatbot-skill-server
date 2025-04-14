from flask import Flask, request, jsonify
import os
import requests
import re
from dateutil.parser import parse

app = Flask(__name__)

# ✅ 기존 기능: snapClassic, snapSig 가격 계산
@app.route('/skill', methods=['POST'])
def skill():
    data = request.get_json()
    params = data.get("action", {}).get("params", {})

    classic = params.get("snapClassic", "")
    sig = params.get("snapSig", "")

    price_map = {
        "클래식": 600000,
        "시그니처": 700000
    }

    classic_price = price_map.get(classic, 0)
    sig_price = price_map.get(sig, 0)
    total = classic_price + sig_price

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": f"📝 선택 요약\n클래식: {classic_price:,}원\n시그니처: {sig_price:,}원\n\n💰 총합: {total:,}원"
                    }
                }
            ]
        },
        "data": {
            "summary": f"클래식: {classic_price}원, 시그니처: {sig_price}원",
            "total": total
        }
    })


# ✅ 새로운 기능: 자연어 날짜 파싱 + 예약 여부 체크
# ✅ 한국어 날짜 문자열 보정 함수
def parse_korean_date(text):
    # 오전/오후 처리
    if '오후' in text and re.search(r'\d+시', text):
        hour_match = re.search(r'(\d+)시', text)
        if hour_match:
            hour = int(hour_match.group(1))
            # 오후 12시는 그대로, 오후 1시~11시는 +12
            if 1 <= hour < 12:
                text = text.replace(f'{hour}시', f'{hour + 12}시')
    text = text.replace('오전', '').replace('오후', '')

    # 숫자만 남기고 나머지는 공백 처리
    cleaned = re.sub(r'[^\d]', ' ', text)  # 예: "2025년 2월 25일 14시" → "2025 2 25 14"
    return parse(cleaned, fuzzy=True)

# ✅ 날짜 파싱 + GAS 예약 확인 통합
@app.route('/parse-and-check', methods=['POST'])
def parse_and_check():
    try:
        data = request.get_json()
        raw_input = data.get("action", {}).get("params", {}).get("Weddingday")

        if not raw_input:
            raise ValueError("사용자 입력값(Weddingday)이 없습니다.")

        # ⏳ 파싱 보완
        parsed_dt = parse_korean_date(raw_input)
        year = parsed_dt.strftime("%Y")
        date_only = parsed_dt.strftime("%Y-%m-%d")

        # GAS 웹앱 URL (너의 실제 스크립트 ID로 대체할 것!)
        GAS_URL = "https://script.google.com/macros/s/AKfycbzQ9KYakQ7BcB5LeGgBZ3-d-Q61LsfQw8AZjFLwdzBomAn7iE3Uuk8rlDu3QTBtQVu1jA/exec"
    
        res = requests.post(GAS_URL, json={"year": year, "date": date_only}, timeout=5)

        if res.status_code != 200:
            raise Exception("GAS 응답 오류")

        result = res.json()
        count = result.get("foundCount", 0)
        sheet_exists = result.get("sheetExists", True)

        # 💬 응답 메시지 구성
        if not sheet_exists:
            message = f"{date_only}은 예약 가능합니다. (해당 연도 시트 없음)"
        elif count < 10:
            message = f"{date_only}은 예약 가능합니다. ({count}건 등록됨)"
        else:
            message = f"{date_only}은 현재 {count}건 등록되어 있습니다.\n상담원과 상의가 필요합니다."

        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [
                    {"simpleText": {"text": message}}
                ]
            },
            "data": {
                "reservationDate": date_only,
                "reservationCount": count,
                "status": "예약 가능" if count < 10 else "상담 필요"
            }
        })

    except Exception as e:
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [
                    {"simpleText": {"text": f"❗ 오류 발생: {str(e)}"}}
                ]
            }
        })

# 포트 설정
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port)
