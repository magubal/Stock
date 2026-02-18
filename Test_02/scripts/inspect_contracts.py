#!/usr/bin/env python3
"""계약 공시 패턴 분석 + KIND 상세 페이지 구조 파악"""
import sys, json, re, time
sys.stdout.reconfigure(encoding='utf-8')

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Referer": "https://kind.krx.co.kr/",
}

# 1) 수집된 계약 공시 패턴 분석
with open("dashboard/data/latest_disclosures.json", encoding="utf-8") as f:
    data = json.load(f)

contracts = [x for x in data["disclosures"] if x["event_class"] == "supply_contract"]
print(f"계약 공시 총 {len(contracts)}건\n")

# 해지, 정정, 일반 분류
cancel = [x for x in contracts if "해지" in x["title"]]
correction = [x for x in contracts if "정정" in x["title"] and "해지" not in x["title"]]
normal = [x for x in contracts if "해지" not in x["title"] and "정정" not in x["title"]]

print(f"해지: {len(cancel)}건")
for c in cancel:
    print(f"  {c['company']:15} | {c['title'][:60]}")

print(f"\n정정: {len(correction)}건")
for c in correction[:5]:
    print(f"  {c['company']:15} | {c['title'][:60]}")

print(f"\n일반: {len(normal)}건")
for c in normal[:3]:
    print(f"  {c['company']:15} | {c['title'][:60]}")

# 2) 샘플 1건의 KIND 상세 페이지 구조 확인
print("\n" + "="*80)
print("KIND 상세 페이지 구조 분석")
print("="*80)

# 일반 공급계약 1건 선택
sample = None
for c in contracts:
    if c.get("url") and "해지" not in c["title"]:
        sample = c
        break

if not sample:
    print("분석할 계약 공시 없음")
    sys.exit(0)

print(f"\n샘플: {sample['company']} - {sample['title']}")
print(f"URL: {sample['url']}")

# 2a) viewer 페이지에서 docNo 추출
resp = requests.get(sample["url"], headers=HEADERS, timeout=15)
resp.encoding = resp.apparent_encoding or "utf-8"
soup = BeautifulSoup(resp.text, "html.parser")

select = soup.find("select", id="mainDoc")
if select:
    for opt in select.find_all("option"):
        val = opt.get("value", "")
        text = opt.get_text(strip=True)
        print(f"  mainDoc option: [{val}] {text}")
        if "|" in val:
            doc_no = val.split("|")[0]
else:
    print("  mainDoc select 없음")
    sys.exit(0)

time.sleep(1)

# 2b) searchContents에서 HTM URL 추출
url2 = f"https://kind.krx.co.kr/common/disclsviewer.do?method=searchContents&docNo={doc_no}"
resp2 = requests.get(url2, headers=HEADERS, timeout=15)
resp2.encoding = "utf-8"
match = re.search(r"setPath\([^,]*,\s*'(https://[^']+\.htm)'", resp2.text)
if match:
    htm_url = match.group(1)
    print(f"\n  HTM URL: {htm_url}")
else:
    print("  HTM URL 추출 실패")
    print(f"  Response: {resp2.text[:500]}")
    sys.exit(0)

time.sleep(1)

# 2c) 실제 문서 파싱 — 계약 관련 테이블 구조 파악
resp3 = requests.get(htm_url, headers=HEADERS, timeout=15)
resp3.encoding = resp3.apparent_encoding or "euc-kr"
soup3 = BeautifulSoup(resp3.text, "html.parser")

print(f"\n  문서 전체 텍스트 길이: {len(resp3.text)}")

# 모든 테이블의 텍스트 요약
tables = soup3.find_all("table")
print(f"  테이블 개수: {len(tables)}")

for i, table in enumerate(tables):
    rows = table.find_all("tr")
    print(f"\n  --- Table {i} ({len(rows)} rows) ---")
    for j, row in enumerate(rows[:15]):  # 최대 15행
        cells = [td.get_text(strip=True)[:40] for td in row.find_all(["td", "th"])]
        print(f"    Row {j}: {cells}")
    if len(rows) > 15:
        print(f"    ... ({len(rows) - 15} more rows)")

# 핵심 키워드 검색: 계약금액, 매출액, 최근매출액, 계약기간
full_text = soup3.get_text()
for keyword in ["계약금액", "매출액", "최근매출", "계약기간", "계약종료", "납품", "공급"]:
    if keyword in full_text:
        # 해당 키워드가 있는 행 찾기
        for table in tables:
            for row in table.find_all("tr"):
                row_text = row.get_text(strip=True)
                if keyword in row_text:
                    cells = [td.get_text(strip=True)[:50] for td in row.find_all(["td", "th"])]
                    print(f"\n  FOUND '{keyword}': {cells}")
                    break
