#!/usr/bin/env python3
"""KIND 실적 공시 — HTM 파일에서 재무 데이터 파싱 테스트"""
import sys, re, time, json
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Referer": "https://kind.krx.co.kr/",
}

def get_doc_url(acpt_no: str, doc_no: str) -> str:
    """searchContents에서 실제 문서 HTM URL을 추출합니다."""
    url = f"https://kind.krx.co.kr/common/disclsviewer.do?method=searchContents&docNo={doc_no}"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.encoding = "utf-8"
    # parent.setPath('','https://kind.krx.co.kr/external/.../70443.htm',...)
    match = re.search(r"setPath\([^,]*,\s*'(https://[^']+\.htm)'", resp.text)
    if match:
        return match.group(1)
    return ""

def get_doc_no(viewer_url: str) -> str:
    """viewer 페이지에서 mainDoc select의 docNo를 추출합니다."""
    resp = requests.get(viewer_url, headers=HEADERS, timeout=15)
    resp.encoding = resp.apparent_encoding or "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    select = soup.find("select", id="mainDoc")
    if select:
        for opt in select.find_all("option"):
            val = opt.get("value", "")
            if "|" in val:
                return val.split("|")[0]
    return ""

def parse_financial_table(html: str) -> dict:
    """HTM 문서에서 매출액/영업이익 증감비율을 추출합니다."""
    soup = BeautifulSoup(html, "html.parser")
    result = {"revenue_yoy": None, "operating_profit_yoy": None, "raw_data": {}}

    tables = soup.find_all("table")
    for t in tables:
        text = t.get_text()
        if "매출" not in text and "영업" not in text:
            continue

        rows = t.find_all("tr")
        for row in rows:
            cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            cell_text = " ".join(cells)

            # 매출액 행 찾기
            if re.search(r"^매출", cells[0] if cells else ""):
                # 숫자 값들 추출 (음수 포함)
                numbers = re.findall(r'[-]?[\d,]+\.?\d*', cell_text)
                pcts = [n for n in numbers if "." in n or abs(float(n.replace(",", ""))) < 1000]
                result["raw_data"]["매출액_row"] = cells
                # 증감비율은 보통 마지막 몇 개 셀에 있음
                for c in reversed(cells):
                    pct_match = re.search(r'([-]?\d+\.?\d*)', c.replace(",", ""))
                    if pct_match:
                        val = float(pct_match.group(1))
                        if -500 < val < 500:  # 비율은 보통 이 범위
                            result["revenue_yoy"] = val
                            break

            # 영업이익 행 찾기
            if re.search(r"^영업이익|^영업손익", cells[0] if cells else ""):
                result["raw_data"]["영업이익_row"] = cells
                for c in reversed(cells):
                    pct_match = re.search(r'([-]?\d+\.?\d*)', c.replace(",", ""))
                    if pct_match:
                        val = float(pct_match.group(1))
                        if -500 < val < 500:
                            result["operating_profit_yoy"] = val
                            break

    return result


# 테스트
with open("data/disclosures/2026-02-14.json", encoding="utf-8") as f:
    data = json.load(f)

test_cases = []
for d in data:
    if "손익구조" in d["title"] and len(test_cases) < 2:
        test_cases.append(d)
    if "잠정" in d["title"] and len(test_cases) < 4:
        test_cases.append(d)

for item in test_cases[:4]:
    print(f"\n{'='*80}")
    print(f"{item['company']} — {item['title'][:60]}")

    # Step 1: viewer에서 docNo 추출
    doc_no = get_doc_no(item["url"])
    if not doc_no:
        print("  docNo 추출 실패")
        time.sleep(2)
        continue
    print(f"  docNo: {doc_no}")

    time.sleep(1)

    # Step 2: searchContents에서 HTM URL 추출
    htm_url = get_doc_url("", doc_no)
    if not htm_url:
        print("  HTM URL 추출 실패")
        time.sleep(2)
        continue
    print(f"  HTM URL: {htm_url}")

    time.sleep(1)

    # Step 3: HTM 파일에서 재무 데이터 파싱
    resp = requests.get(htm_url, headers=HEADERS, timeout=15)
    resp.encoding = resp.apparent_encoding or "euc-kr"
    print(f"  HTM Status: {resp.status_code}, Length: {len(resp.text)}")

    result = parse_financial_table(resp.text)
    print(f"  매출액 YoY: {result['revenue_yoy']}")
    print(f"  영업이익 YoY: {result['operating_profit_yoy']}")
    if result["raw_data"]:
        for k, v in result["raw_data"].items():
            print(f"    {k}: {v}")

    time.sleep(2)
