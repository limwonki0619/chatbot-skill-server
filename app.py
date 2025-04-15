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

    discount_map = {
        "0": None,
        "1": "D.partner",
        "2": "D.earlybird",
        "3": "D.review",
        "4": "D.sunday",
        "5": "D.evening"
    }

    label_map = {
        "F.snsHighlight": "SNS용 1분 H/L (세로형)",
        "F.subVideoDirector": "서브 영상감독 추가",
        "F.videoDesignated": "감독 지정",
        "F.videoDirector": "대표감독 지정",
        "F.usb": "USB추가",
        "S.iphoneSnap": "아이폰스냅 추가",
        "S.iphoneSnapPremium": "아이폰스냅 프리미엄 추가",
        "S.subSnap": "서브스냅 추가",
        "S.snapDesignated": "작가 지정",
        "S.snapDirector": "대표작가 지정",
        "D.partner": "짝궁",
        "D.earlybird": "얼리버드(예식 1년 전 예약)",
        "D.review": "계약 또는 촬영후기",
        "D.sunday": "일요일예식",
        "D.evening": "저녁예식(오후 4시 이후)"
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

    # ✅ 문자열 숫자 → 매핑 함수 (공백 제거 포함)
    def map_nums(nums, table):
        return [
            table[n.strip()]
            for n in nums.split(",")
            if n.strip() in table and table[n.strip()] is not None
        ] if nums else []

    # ✅ 매핑 처리
    snap_opts = map_nums(snapOptions, snap_option_map)
    film_opts = map_nums(filmOptions, film_option_map)
    discounts = map_nums(discountEvent, discount_map)

    # ✅ 기본 상품 가격
    snap_base = snap_prices.get(snapProduct, 0)
    film_base = film_prices.get(filmProduct, 0)

    # 🎁 상품 결합 할인 (상품가만 적용)
    product_total = snap_base + film_base
    if snapProduct != "선택안함" and filmProduct != "선택안함":
        product_total *= 0.9

    # ✅ 옵션 가격 합산
    total = product_total
    total += sum(snap_option_prices.get(opt, 0) for opt in snap_opts)
    total += sum(film_option_prices.get(opt, 0) for opt in film_opts)

    # ✅ 기타 할인
    for d in discounts:
        total -= discount_values.get(d, 0)

    # ✅ 계산 정리
    total = max(total, 0)
    total_price = int(total * 10000)
    vat = int(total_price * 0.1)

    def label(items):
        return "없음" if not items else ", ".join(label_map.get(i, i) for i in items)

    summary = f"""요청해주신 구성으로 견적 안내드릴게요 :)

🎬 [영상상품] {filmProduct}
🔶 [영상옵션] {label(film_opts)}

📷 [스냅상품] {snapProduct}
🔷 [스냅옵션] {label(snap_opts)}

🎁 [할인이벤트] {label(discounts)}

💰 [금액] {total_price:,}원
✔️ [부가세(10%)] {vat:,}원

※ 대전/세종/청주 이외 지역은 출장비가 발생 됩니다.
※ 원판, 연회, 폐백, 2부 촬영에 대한 자세한 내용은 상담을 통해 안내드립니다.
"""

    return {
        "summary": summary,
        "totalPrice": total_price,
        "vat": vat
    }

@app.route("/calculator", methods=["POST"])
def calculator():
    try:
        data = request.get_json(force=True)
        params = data.get("action", {}).get("params", {})

        result = calculate_price_with_korean_labels(
            snapProduct=params.get("snapProduct", "선택안함"),
            snapOptions=params.get("snapOptions", ""),
            filmProduct=params.get("filmProduct", "선택안함"),
            filmOptions=params.get("filmOptions", ""),
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
            },
            "data": {
                "error": str(e)
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
        # 1. 사용자 입력값 파싱
        data = request.get_json()
        raw_input = data.get("action", {}).get("params", {}).get("Weddingday", "")
        is_admin = raw_input.startswith("!")
        clean_input = raw_input.lstrip("!").strip()

        # 2. 날짜 파싱
        parsed_dt = parse(clean_input, fuzzy=True)
        year = parsed_dt.strftime("%Y")
        date_str = parsed_dt.strftime("%Y-%m-%d")
        pretty_date = parsed_dt.strftime("%Y년 %m월 %d일")

        # 3. GAS 서버에 요청
        gas_url = "https://script.google.com/macros/s/AKfycbwgjfl-RFHGMAS-VF5-asFwhG34fElcsq7vJRVDrepl_NXYipmJdvg-1-khgb3vwHVn2w/exec"
        gas_response = requests.post(gas_url, json={"year": year, "date": date_str})
        gas_result = gas_response.json()

        found = gas_result.get("foundCount", 0)
        sheet_exists = gas_result.get("sheetExists", False)
        details = gas_result.get("details", [])

        # 4. 응답 메시지 생성
        if not sheet_exists:
            message = f"{pretty_date}은 예약 가능합니다."
        elif is_admin:
            if found == 0:
                message = f"{pretty_date}은 등록된 예약이 없습니다."
            else:
                detail_lines = [
                    f"{i+1}. {d.get('time', '시간 없음')} / {d.get('hall', '웨딩홀 정보 없음')}"
                    for i, d in enumerate(details)
                ]
                detail_text = "\n".join(detail_lines)
                message = f"{pretty_date}은 총 {found}건 등록되어 있습니다.\n\n{detail_text}"
        elif found >= 10:
            message = f"{pretty_date}은 현재 해당 날짜에는 예약이 몰려 있어 상담 후 가능 여부를 안내드리고 있어요."
        else:
            message = f"{pretty_date}은 예약 가능합니다."

        # 5. 챗봇 응답
        response = {
            "version": "2.0",
            "template": {
                "outputs": [
                    { "simpleText": { "text": message } }
                ]
            },
            "data": {
                "mode": "admin" if is_admin else "user",
                "date": date_str,
                "foundCount": found,
                "details": details
            }
        }

        return make_response(json.dumps(response, ensure_ascii=False), 200, {
            "Content-Type": "application/json"
        })

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
