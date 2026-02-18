#!/usr/bin/env python3
"""KIND HTML 구조 진단 — onclick/href 패턴 확인용"""
import sys, time, re, requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

KIND_BASE = "https://kind.krx.co.kr"
KIND_URL = f"{KIND_BASE}/disclosure/todaydisclosure.do"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": KIND_URL,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Content-Type": "application/x-www-form-urlencoded",
}

from datetime import date
target = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()

form_data = {
    "method": "searchTodayDisclosureSub",
    "currentPageSize": "15",
    "pageIndex": "1",
    "orderMode": "0",
    "orderStat": "D",
    "forward": "todaydisclosure_sub",
    "chose_marketType": "",
    "textCr498": target.replace("-", ""),
    "marketType": "",
}

session = requests.Session()
session.get(KIND_URL, headers=HEADERS, timeout=15)
time.sleep(1)
resp = session.post(KIND_URL, data=form_data, headers=HEADERS, timeout=30)
resp.encoding = resp.apparent_encoding or "utf-8"

print(f"Status: {resp.status_code}")
print(f"Encoding: {resp.encoding}")
print(f"Content length: {len(resp.text)}")
print("=" * 80)

soup = BeautifulSoup(resp.text, "html.parser")

# 모든 <a> 태그 검사
all_links = soup.find_all("a")
print(f"\n총 <a> 태그 수: {len(all_links)}")

# onclick 패턴 분석
onclick_patterns = set()
for a in all_links:
    onclick = a.get("onclick", "")
    href = a.get("href", "")
    text = a.get_text(strip=True)[:40]
    if onclick:
        # 함수명만 추출
        func_match = re.match(r"(\w+)\(", onclick)
        func_name = func_match.group(1) if func_match else "unknown"
        onclick_patterns.add(func_name)
        print(f"  [onclick] func={func_name} | href={href} | text={text}")
        print(f"           full: {onclick[:150]}")
        print()

print(f"\n발견된 onclick 함수들: {onclick_patterns}")
print("=" * 80)

# 테이블 구조 분석
tables = soup.find_all("table")
print(f"\n총 <table> 수: {len(tables)}")
for i, t in enumerate(tables):
    cls = t.get("class", [])
    rows = t.find_all("tr")
    print(f"  table[{i}]: class={cls}, rows={len(rows)}")

# 첫 번째 테이블 행 상세 분석
table = soup.find("table", class_="list") or (tables[0] if tables else None)
if table:
    tbody = table.find("tbody") or table
    rows = tbody.find_all("tr")
    print(f"\n첫 5행 상세 분석:")
    for idx, row in enumerate(rows[:5]):
        cols = row.find_all("td")
        print(f"\n--- Row {idx} ({len(cols)} cols) ---")
        for ci, col in enumerate(cols):
            links = col.find_all("a")
            text = col.get_text(strip=True)[:50]
            print(f"  col[{ci}]: text={text}")
            for link in links:
                print(f"    <a> href={link.get('href', '')} onclick={link.get('onclick', '')[:120]}")

# Raw HTML 일부 저장 (디버그용)
with open("kind_debug.html", "w", encoding="utf-8") as f:
    f.write(resp.text)
print("\n전체 HTML → kind_debug.html 저장 완료")
