#!/usr/bin/env python3
"""KCC건설 직전 버전 vs 최신 비교"""
import sys, re, time
sys.stdout.reconfigure(encoding='utf-8')

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Referer": "https://kind.krx.co.kr/",
}

def get_htm(doc_no):
    url = f"https://kind.krx.co.kr/common/disclsviewer.do?method=searchContents&docNo={doc_no}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.encoding = "utf-8"
    m = re.search(r"setPath\([^,]*,\s*'(https://[^']+\.htm)'", r.text)
    if not m:
        return None
    time.sleep(0.5)
    r2 = requests.get(m.group(1), headers=HEADERS, timeout=15)
    r2.encoding = r2.apparent_encoding or "euc-kr"
    return r2.text

# 직전 (2025.12.23)
print("=== [직전] 20251223000057 (2025.12.23) ===")
prev = get_htm("20251223000057")
time.sleep(1)
if prev:
    s = BeautifulSoup(prev, "html.parser")
    for table in s.find_all("table"):
        for row in table.find_all("tr"):
            cells = [td.get_text(strip=True)[:60] for td in row.find_all(["td", "th"])]
            joined = " ".join(cells)
            if any(k in joined for k in ["계약금액", "매출액", "종료일", "시작일", "계약기간", "정정"]):
                print(f"  {cells}")

# 최신 (2026.02.13)
print("\n=== [최신] 20260213000677 (2026.02.13) ===")
latest = get_htm("20260213000677")
if latest:
    s = BeautifulSoup(latest, "html.parser")
    for table in s.find_all("table"):
        for row in table.find_all("tr"):
            cells = [td.get_text(strip=True)[:60] for td in row.find_all(["td", "th"])]
            joined = " ".join(cells)
            if any(k in joined for k in ["계약금액", "매출액", "종료일", "시작일", "계약기간", "정정"]):
                print(f"  {cells}")
