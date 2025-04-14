from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# ✅ 기존 계산 기능: snapClassic + snapSig 계산
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

    response = {
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
    }

    return jsonify(response)


# ✅ 추가 기능: 날짜 기반 GAS 연동 예약 가능 여부 체크
@app.route('/check-date', methods=['POST'])
def check_date():
    try:
        data = request.get_json()
        datetime_param = data.get("action", {}).get("params", {}).get("Weddingday")  # ← 여기 수정

        if not datetime_param:
            raise ValueError("날짜 파라미터가 없습니다.")

        date_only = datetime_param.split("T")[0]  # "2025-02-25"
        year = date_only.split("-")[0]            # "2025"

        # 여기에 너의 GAS 웹앱 URL
        GAS_URL = "https://script.google.com/macros/s/AKfycbxBFKpceaLSUF78Z5uZ289zK4J7d11ecWl1BjjQLOmlZIteTwI8z2VpyssBB1XnWGo5Sw/exec"

        res = requests.post(GAS_URL, json={"year": year, "date": date_only}, timeout=5)
        result = res.json()
        count = result.get("foundCount", 0)
        sheet_exists = result.get("sheetExists", True)

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
            }
        })

    except Exception as e:
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [
                    {"simpleText": {"text": f"오류가 발생했습니다: {str(e)}"}}
                ]
            }
        })


# ✅ Render 포트 설정
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port)
