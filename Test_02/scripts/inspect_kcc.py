#!/usr/bin/env python3
"""KCC건설 정정 공시 원본 vs 최신 상세 비교"""
import sys, json, re, time
sys.stdout.reconfigure(encoding='utf-8')

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Referer": "https://kind.krx.co.kr/",
}

with open("dashboard/data/latest_disclosures.json", encoding="utf-8") as f:
    data = json.load(f)

kcc = [x for x in data["disclosures"] if "KCC건설" in x["company"] and x["event_class"] == "supply_contract"][0]
print(f"KCC건설: {kcc['title']}")
print(f"URL: {kcc['url']}")

# viewer에서 문서 목록 가져오기
resp = requests.get(kcc["url"], headers=HEADERS, timeout=15)
resp.encoding = resp.apparent_encoding or "utf-8"
soup = BeautifulSoup(resp.text, "html.parser")
select = soup.find("select", id="mainDoc")
options = []
for opt in select.find_all("option"):
    val = opt.get("value", "")
    text = opt.get_text(strip=True)
    if "|" in val:
        options.append((val.split("|")[0], text))
        print(f"  옵션: [{val.split('|')[0]}] {text}")

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

# 원본 (첫 번째)
print(f"\n{'='*60}")
print(f"[원본] {options[0][1]}")
print(f"{'='*60}")
orig = get_htm(options[0][0])
time.sleep(1)
if orig:
    s = BeautifulSoup(orig, "html.parser")
    for table in s.find_all("table"):
        for row in table.find_all("tr"):
            cells = [td.get_text(strip=True)[:50] for td in row.find_all(["td", "th"])]
            joined = " ".join(cells)
            if any(k in joined for k in ["계약금액", "매출액", "종료일", "시작일", "계약기간"]):
                print(f"  {cells}")

# 최신 (마지막)
print(f"\n{'='*60}")
print(f"[최신] {options[-1][1]}")
print(f"{'='*60}")
latest = get_htm(options[-1][0])
time.sleep(1)
if latest:
    s = BeautifulSoup(latest, "html.parser")
    for table in s.find_all("table"):
        for row in table.find_all("tr"):
            cells = [td.get_text(strip=True)[:50] for td in row.find_all(["td", "th"])]
            joined = " ".join(cells)
            if any(k in joined for k in ["계약금액", "매출액", "종료일", "시작일", "계약기간"]):
                print(f"  {cells}")
