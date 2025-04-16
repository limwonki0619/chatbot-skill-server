from flask import Flask, request, jsonify, make_response
import json
import os
import requests
import re
from dateutil.parser import parse
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

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
    # 1. 느낌표 제거 (관리자모드 구분 외에는 영향 없음)
    text = text.lstrip('!').strip()

    # 2. '25년' → '2025년' 으로 보정
    text = re.sub(r'\b(\d{2})년', lambda m: f"20{m.group(1)}년", text)

    # 3. 오후/오전 시간 → 24시간 보정
    if '오후' in text:
        match = re.search(r'오후\s*(\d{1,2})시', text)
        if match:
            hour = int(match.group(1))
            hour = 12 if hour == 12 else hour + 12
            text = text.replace(match.group(0), f"{hour}시")
    elif '오전' in text:
        match = re.search(r'오전\s*(\d{1,2})시', text)
        if match:
            hour = int(match.group(1))
            hour = 0 if hour == 12 else hour
            text = text.replace(match.group(0), f"{hour}시")

    # 4. 특수문자 제거 (년/월/일/시 제외), 점이나 슬래시도 띄어쓰기로 바꿈
    text = text.replace('.', ' ').replace('/', ' ')
    text = re.sub(r'[^\d\s시]', ' ', text)  # '2025 6 1 14시' 형태 유도
    text = re.sub(r'\s+', ' ', text).strip()

    # 5. 파싱
    return parse(text, fuzzy=True)


# ✅ 날짜 파싱 + GAS 예약 확인 통합
# ✅ 한글 날짜 입력 보정 함수
def parse_korean_date(text):
    text = text.lstrip('!').strip()

    # 25년 → 2025년 처리
    text = re.sub(r'\b(\d{2})년', lambda m: f"20{m.group(1)}년", text)

    # 오전/오후 시각 보정
    if '오후' in text:
        match = re.search(r'오후\s*(\d{1,2})시', text)
        if match:
            hour = int(match.group(1))
            hour = 12 if hour == 12 else hour + 12
            text = text.replace(match.group(0), f"{hour}시")
    elif '오전' in text:
        match = re.search(r'오전\s*(\d{1,2})시', text)
        if match:
            hour = int(match.group(1))
            hour = 0 if hour == 12 else hour
            text = text.replace(match.group(0), f"{hour}시")

    # 특수문자 및 단위 제거
    text = text.replace('.', ' ').replace('/', ' ')
    text = re.sub(r'[^\d\s시]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    return parse(text, fuzzy=True)

# ✅ 날짜 확인 엔드포인트
@app.route("/parse-and-check", methods=["POST"])
def parse_and_check():
    try:
        data = request.get_json()
        raw_input = data.get("action", {}).get("params", {}).get("Weddingday", "")
        is_admin = raw_input.startswith("!")
        clean_input = raw_input.lstrip("!").strip()

        # 보정된 날짜 파싱
        parsed_dt = parse_korean_date(clean_input)
        year = parsed_dt.strftime("%Y")
        date_str = parsed_dt.strftime("%Y-%m-%d")
        pretty_date = parsed_dt.strftime("%Y년 %m월 %d일")

        # GAS 서버 요청
        gas_url = os.getenv("GAS_URL")  # 반드시 .env 파일에 GAS_URL 설정 필요
        gas_response = requests.post(gas_url, json={"year": year, "date": date_str})
        gas_result = gas_response.json()

        found = gas_result.get("foundCount", 0)
        sheet_exists = gas_result.get("sheetExists", False)
        details = gas_result.get("details", [])

        # 응답 메시지 생성
        if not sheet_exists:
            message = f"{pretty_date}은 예약 가능합니다. (해당 연도 시트 없음)"
        elif is_admin:
            if found > 0 and details:
                detail_lines = [f"{row.get('time', '')} - {row.get('hall', '')}" for row in details]
                joined = "\n".join(detail_lines)
                message = f"{pretty_date}은 예약 {found}건 등록되어 있습니다.\n\n📋 등록 내역:\n{joined}"
            else:
                message = f"{pretty_date}은 등록된 예약이 없습니다."
        elif found >= 10:
            message = f"{pretty_date}은 예약이 많아 상담 후 예약 가능 여부를 안내드릴게요."
        else:
            message = f"{pretty_date}은 예약 가능합니다."

        # 챗봇 응답 반환
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
                "foundCount": found
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
