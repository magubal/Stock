#!/usr/bin/env python3
"""정정 공시: 원본 vs 최신 비교 구조 분석"""
import sys, json, re, time
sys.stdout.reconfigure(encoding='utf-8')

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Referer": "https://kind.krx.co.kr/",
}


def get_htm_content(doc_no):
    url = f"https://kind.krx.co.kr/common/disclsviewer.do?method=searchContents&docNo={doc_no}"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.encoding = "utf-8"
    match = re.search(r"setPath\([^,]*,\s*'(https://[^']+\.htm)'", resp.text)
    if not match:
        return None
    time.sleep(0.5)
    htm_url = match.group(1)
    resp2 = requests.get(htm_url, headers=HEADERS, timeout=15)
    resp2.encoding = resp2.apparent_encoding or "euc-kr"
    return resp2.text


def parse_contract_fields(html):
    """계약금액, 매출액, 매출대비%, 계약종료일 추출"""
    soup = BeautifulSoup(html, "html.parser")
    result = {"contract_amount": None, "revenue": None, "revenue_pct": None, "end_date": None}

    for table in soup.find_all("table"):
        prev_label = ""
        for row in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            if not cells:
                continue

            label = cells[0]
            # 계약금액 총액
            if "계약금액" in label and "총액" in label and len(cells) >= 2:
                val = cells[1].replace(",", "").replace("-", "").strip()
                if val.isdigit():
                    result["contract_amount"] = int(val)
            # 해지금액
            elif "해지금액" in label and len(cells) >= 2:
                val = cells[1].replace(",", "").replace("-", "").strip()
                if val.isdigit():
                    result["contract_amount"] = int(val)
            # 최근 매출액
            elif "최근" in label and "매출액" in label and len(cells) >= 2:
                val = cells[1].replace(",", "").replace("-", "").strip()
                if val.isdigit():
                    result["revenue"] = int(val)
            elif label == "최근매출액(원)" and len(cells) >= 2:
                val = cells[1].replace(",", "").replace("-", "").strip()
                if val.isdigit():
                    result["revenue"] = int(val)
            # 매출액 대비
            elif "매출액" in label and "대비" in label and len(cells) >= 2:
                val = cells[1].replace(",", "").strip()
                try:
                    result["revenue_pct"] = float(val)
                except ValueError:
                    pass
            elif label == "매출액대비(%)" and len(cells) >= 2:
                val = cells[1].replace(",", "").strip()
                try:
                    result["revenue_pct"] = float(val)
                except ValueError:
                    pass
            # 계약 종료일
            elif "종료일" in label and len(cells) >= 2:
                result["end_date"] = cells[-1].strip()  # 마지막 셀
            elif prev_label.startswith("5.") and "계약기간" in prev_label:
                # 시작일, 종료일이 별도 행
                pass

            # 종료일이 같은 행에 있는 경우
            if "종료일" in " ".join(cells) and len(cells) >= 2:
                for c in cells:
                    if re.match(r"\d{4}-\d{2}-\d{2}", c):
                        if prev_label == "" or "종료" in " ".join(cells):
                            result["end_date"] = c

            prev_label = label

    return result


# ── 기가비스 정정 공시: 원본 vs 최신 ──
# 원본: 20250421001933
# 최신: 20260213002812
print("기가비스 정정 공시 비교")
print("="*60)

print("\n[원본] 20250421001933")
orig_html = get_htm_content("20250421001933")
time.sleep(1)
if orig_html:
    orig = parse_contract_fields(orig_html)
    for k, v in orig.items():
        print(f"  {k}: {v}")

print("\n[최신] 20260213002812")
latest_html = get_htm_content("20260213002812")
time.sleep(1)
if latest_html:
    latest = parse_contract_fields(latest_html)
    for k, v in latest.items():
        print(f"  {k}: {v}")

if orig_html and latest_html:
    print("\n비교:")
    if orig["contract_amount"] and latest["contract_amount"]:
        change = (latest["contract_amount"] - orig["contract_amount"]) / orig["contract_amount"] * 100
        print(f"  계약금액 변동: {orig['contract_amount']:,} → {latest['contract_amount']:,} ({change:+.1f}%)")
    if orig["end_date"] and latest["end_date"]:
        print(f"  종료일 변동: {orig['end_date']} → {latest['end_date']}")
