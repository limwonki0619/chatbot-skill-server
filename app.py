from flask import Flask, request, jsonify, make_response
import json
import os
import requests
import re
from dateutil.parser import parse

app = Flask(__name__)

# 계산 함수
def calculate_price_with_korean_labels(
    snapProduct,
    snapOptions,
    filmProduct,
    filmOptions,
    additionalShoot,
    discountEvent
):
    snap_option_map = {
        "0": None,
        "1": "S.iphoneSnap",
        "2": "S.iphoneSnapPremium",
        "3": "S.subSnap",
        "4": "S.snapDesignated",
        "5": "S.snapDirector"
    }

    film_option_map = {
        "0": None,
        "1": "F.snsHighlight",
        "2": "F.subVideoDirector",
        "3": "F.videoDesignated",
        "4": "F.videoDirector",
        "5": "F.usb"
    }

    additional_map = {
        "0": None,
        "1": "A.portrait",
        "2": "A.pyebaek",
        "3": "A.banquet",
        "4": "A.secondPart"
    }

    discount_map = {
        "0": None,
        "2": "D.partner",
        "3": "D.earlybird",
        "4": "D.review",
        "5": "D.sunday",
        "6": "D.evening"
    }

    label_map = {
        "F.snsHighlight": "SNS용 1분 H/L (세로형) +5",
        "F.subVideoDirector": "서브 영상감독 추가 +25",
        "F.videoDesignated": "감독 지정 +10",
        "F.videoDirector": "대표감독 지정 +30",
        "F.usb": "USB추가 +5",
        "S.iphoneSnap": "아이폰스냅 추가 +15",
        "S.iphoneSnapPremium": "아이폰스냅 프리미엄 추가 +25",
        "S.subSnap": "서브스냅 추가 +20",
        "S.snapDesignated": "작가 지정 +10",
        "S.snapDirector": "대표작가 지정 +30",
        "A.portrait": "원판",
        "A.pyebaek": "폐백",
        "A.banquet": "연회",
        "A.secondPart": "2부",
        "D.partner": "짝궁 -2",
        "D.earlybird": "얼리버드(예식 1년 전 예약) -1",
        "D.review": "계약 또는 촬영후기 -2",
        "D.sunday": "일요일예식 -1",
        "D.evening": "저녁예식(오후 4시 이후) -1"
    }

    film_prices = {"클래식": 60, "시그니처": 75, "노블레스": 99, "선택안함": 0}
    snap_prices = {"클래식": 60, "시그니처": 80, "노블레스": 99, "선택안함": 0}

    snap_option_prices = {
        "S.iphoneSnap": 15,
        "S.iphoneSnapPremium": 25,
        "S.subSnap": 20,
        "S.snapDesignated": 10,
        "S.snapDirector": 30
    }

    film_option_prices = {
        "F.snsHighlight": 5,
        "F.subVideoDirector": 25,
        "F.videoDesignated": 10,
        "F.videoDirector": 30,
        "F.usb": 5
    }

    discount_values = {
        "D.partner": 2,
        "D.earlybird": 1,
        "D.review": 2,
        "D.sunday": 1,
        "D.evening": 1
    }

    def map_nums(nums, table):
        return [table[n.strip()] for n in nums.split(",") if n.strip() in table and table[n.strip()] is not None] if nums else []

    snap_opts = map_nums(snapOptions, snap_option_map)
    film_opts = map_nums(filmOptions, film_option_map)
    adds = map_nums(additionalShoot, additional_map)
    discounts = map_nums(discountEvent, discount_map)

    snap_base = snap_prices.get(snapProduct, 0)
    film_base = film_prices.get(filmProduct, 0)

    # 🎁 상품 결합할인
    product_total = snap_base + film_base
    if snapProduct != "선택안함" and filmProduct != "선택안함":
        product_total *= 0.9

    total = product_total
    total += sum(snap_option_prices.get(opt, 0) for opt in snap_opts)
    total += sum(film_option_prices.get(opt, 0) for opt in film_opts)

    # 📱 아이폰스냅 자동 무료
    if snapProduct in ["시그니처", "노블레스"] and filmProduct in ["시그니처", "노블레스"]:
        if "S.iphoneSnap" in snap_opts:
            total -= snap_option_prices.get("S.iphoneSnap", 0)

    # 📸 추가촬영 비용 조건
    if snapProduct == "노블레스" and filmProduct == "노블레스":
        add_total = 0
    elif snapProduct != "선택안함" and filmProduct != "선택안함":
        add_total = len(adds) * 20
    elif snapProduct != "선택안함" or filmProduct != "선택안함":
        add_total = len(adds) * 10
    else:
        add_total = 0
    total += add_total

    # 🎉 기타 할인
    for d in discounts:
        total -= discount_values.get(d, 0)

    total = max(total, 0)
    total_price = int(total * 10000)
    vat = int(total_price * 0.1)

    def label(items):
        return "없음" if not items else ", ".join(label_map.get(i, i) for i in items)

    summary = f"""요청해주신 구성으로 견적 안내드릴게요 :)

[영상상품] {filmProduct}
[영상옵션] {label(film_opts)}

[스냅상품] {snapProduct}
[스냅옵션] {label(snap_opts)}

[추가촬영] {label(adds)}
[할인이벤트] {label(discounts)}

[금액] {total_price:,}원
[부가세(10%)] {vat:,}원
※ 대전/청주 이외 지역은 출장비가 발생할 수 있습니다."""

    return {
        "summary": summary,
        "totalPrice": total_price,
        "vat": vat
    }

@app.route("/calculator", methods=["POST"])
def calculator():
    try:
        data = request.get_json()
        params = data.get("action", {}).get("params", {})

        result = calculate_price_with_korean_labels(
            snapProduct=params.get("snapProduct", "선택안함"),
            snapOptions=params.get("snapOptions", ""),
            filmProduct=params.get("filmProduct", "선택안함"),
            filmOptions=params.get("filmOptions", ""),
            additionalShoot=params.get("additionalShoot", ""),
            discountEvent=params.get("discountEvent", "")
        )

        response = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": result["summary"]
                        }
                    }
                ]
            },
            "data": {
                "summary": result["summary"],
                "totalPrice": result["totalPrice"],
                "vat": result["vat"]
            }
        }

        return make_response(
            json.dumps(response, ensure_ascii=False),
            200,
            {"Content-Type": "application/json"}
        )

    except Exception as e:
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": f"⚠️ 계산 중 오류 발생: {str(e)}"
                        }
                    }
                ]
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
@app.route("/parse-and-check", methods=["POST"])
def parse_and_check():
    try:
        data = request.get_json()
        raw_input = data.get("action", {}).get("params", {}).get("Weddingday", "")
        is_admin = raw_input.startswith("!")
        clean_input = raw_input.lstrip("!").strip()

        # 날짜 파싱
        parsed = parse(clean_input, fuzzy=True)
        year = parsed.strftime("%Y")
        date = parsed.strftime("%Y-%m-%d")
        pretty_date = parsed.strftime("%Y년 %m월 %d일")

        # GAS 요청
        gas_url = "https://script.google.com/macros/s/AKfyc.../exec"  # 네 GAS URL로 대체
        res = requests.post(gas_url, json={"year": year, "date": date})
        result = res.json()

        found = result.get("foundCount", 0)
        sheet_exists = result.get("sheetExists", False)

        # 응답 구성
        if not sheet_exists:
            message = f"{pretty_date}은 예약 가능합니다."
        elif is_admin:
            message = f"{pretty_date}은 예약 {found}건 등록되어 있습니다."
        elif found >= 10:
            message = f"{pretty_date}은 예약이 많은 날짜예요. 정확한 가능 여부는 상담 후 안내드릴 수 있어요."
        else:
            message = f"{pretty_date}은 예약 가능합니다."

        return make_response(json.dumps({
            "version": "2.0",
            "template": {
                "outputs": [
                    { "simpleText": { "text": message } }
                ]
            },
            "data": {
                "mode": "admin" if is_admin else "user",
                "count": found
            }
        }, ensure_ascii=False), 200, {"Content-Type": "application/json"})

    except Exception as e:
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [
                    { "simpleText": { "text": f"❌ 오류 발생: {str(e)}" } }
                ]
            }
        })

# 포트 설정
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port)
