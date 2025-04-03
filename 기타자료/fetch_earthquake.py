import requests
import pandas as pd
from datetime import datetime
import calendar
import time
import os

#기상청 API 설정
API_KEY = "IgNe-epfS8mDXvnqXwvJiQ"
BASE_URL = "https://apihub.kma.go.kr/api/typ01/url/eqk_list.php"

#기상청 명세 기준 열
columns = ["TP", "TM_FC", "SEQ", "TM_EQK", "MSC", "MT",
        "LAT", "LON", "LOC", "INT", "REM", "COR"]

#수집 기간 설정
start_year, start_month = 2001, 11
end_year, end_month = 2024, 11

all_data = []

#디버그 로그 저장 경로
os.makedirs("debug_logs", exist_ok=True)

#월별 데이터 수집
for year in range(start_year, end_year + 1):
    for month in range(1, 13):
        if (year == start_year and month < start_month) or (year == end_year and month > end_month):
            continue

        first_day = datetime(year, month, 1, 0, 0)
        last_day = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59)

        from_date = first_day.strftime("%Y%m%d%H%M")
        to_date = last_day.strftime("%Y%m%d%H%M")

        print(f"\n[INFO] {from_date} ~ {to_date} 지진 데이터 요청 중...")

        params = {
            "tm1": from_date,
            "tm2": to_date,
            "disp": 1,  # 쉼표 구분 CSV
            "authKey": API_KEY
        }

        try:
            response = requests.get(BASE_URL, params=params)
            response.encoding = "euc-kr"
            raw_text = response.text

            # 유효한 줄만 필터링
            lines = [line for line in raw_text.splitlines() if line.strip() and not line.startswith("#")]
            print(f"[DEBUG] 응답 줄 수: {len(lines)}")

            if not lines:
                print(f"[SKIP] {from_date} → 유효한 데이터 없음")
                continue

            # 디버그용 원본 응답 저장
            with open(f"debug_logs/raw_{from_date}.csv", "w", encoding="euc-kr") as f:
                f.write("\n".join(lines))

            for line_num, line in enumerate(lines, start=1):
                parts = line.strip().split(",")

                if len(parts) < 5:
                    print(f"[SKIP] 줄 무시: {line_num} → 필드 수 부족 ({len(parts)})")
                    continue

                # 필드 수 정리
                if len(parts) > len(columns):
                    print(f"[WARN] {from_date} 줄 {line_num} → 열 초과: {len(parts)} → 자름")
                    parts = parts[:len(columns)]
                elif len(parts) < len(columns):
                    print(f"[WARN] {from_date} 줄 {line_num} → 열 부족: {len(parts)} → 공백 추가")
                    parts += [""] * (len(columns) - len(parts))

                row = dict(zip(columns, parts))
                all_data.append(row)

        except Exception as e:
            print(f"[ERROR] {from_date} 요청 실패: {e}")

        time.sleep(0.3)  # API 과부하 방지

#최종 XML, csv로 저장
if all_data:
    df = pd.DataFrame(all_data)
    df.to_xml("earthquake_200111_to_202411.xml", index=False, encoding="utf-8", xml_declaration=True)
    print(f"\n[SUCCESS] 총 {len(df)}건 저장 완료 → earthquake_200111_to_202411.xml")
    df.to_csv("earthquake_data.csv", index=False, encoding="utf-8-sig")
    print(f"\n[SUCCESS] 총 {len(df)}건 저장 완료 → earthquake_200111_to_202411.csv")
    df.to_json("earthquake_200111_to_202411.json", orient="records", force_ascii=False, indent=2)
    print(f"\n[SUCCESS] 총 {len(df)}건 저장 완료 → earthquake_200111_to_202411.csv")

else:
    print("\n[FAIL] 저장할 데이터가 없습니다.")
