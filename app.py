from flask import Flask, request, jsonify

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
