#!/usr/bin/env python3
"""KIND 문서 내용 URL 탐색"""
import sys, re, time
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Referer": "https://kind.krx.co.kr/common/disclsviewer.do",
}

acpt_no = "20260213002140"  # 유진테크
doc_no = "20260204003163"

# 방법 1: searchContents — 실제 반환 내용 확인
url1 = f"https://kind.krx.co.kr/common/disclsviewer.do?method=searchContents&docNo={doc_no}"
resp1 = requests.get(url1, headers=HEADERS, timeout=15)
resp1.encoding = "utf-8"
print(f"[searchContents] Status={resp1.status_code} Length={len(resp1.text)}")
print(resp1.text[:1500])
print()

time.sleep(1)

# 방법 2: POST로 searchContents 시도
url2 = "https://kind.krx.co.kr/common/disclsviewer.do"
resp2 = requests.post(url2, data={"method": "searchContents", "docNo": doc_no}, headers=HEADERS, timeout=15)
resp2.encoding = "utf-8"
print(f"[searchContents POST] Status={resp2.status_code} Length={len(resp2.text)}")
print(resp2.text[:1500])
print()

time.sleep(1)

# 방법 3: DART API (Open DART에서 문서 접근)
# acptNo → rcpNo 매핑 시도
dart_url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={acpt_no}"
print(f"[DART] {dart_url}")
resp3 = requests.get(dart_url, headers=HEADERS, timeout=15, allow_redirects=True)
resp3.encoding = resp3.apparent_encoding or "utf-8"
print(f"  Status={resp3.status_code} Length={len(resp3.text)}")
soup3 = BeautifulSoup(resp3.text, "html.parser")
# iframe 찾기
iframes = soup3.find_all(["iframe", "frame"])
for ifr in iframes:
    print(f"  frame: name={ifr.get('name','')} src={ifr.get('src','')[:150]}")
# 테이블 개수
tables = soup3.find_all("table")
print(f"  Tables: {len(tables)}")
# dcmNo 찾기
dcm_matches = re.findall(r'dcmNo["\s:=]+["\']?(\d+)', resp3.text)
print(f"  dcmNo values: {dcm_matches[:5]}")

if dcm_matches:
    dcm_no = dcm_matches[0]
    # DART 문서 직접 URL
    time.sleep(1)
    doc_url = f"https://dart.fss.or.kr/report/viewer.do?rcpNo={acpt_no}&dcmNo={dcm_no}&eleId=0&offset=0&length=0&dtd=dart3.xsd"
    print(f"\n[DART doc] {doc_url}")
    resp4 = requests.get(doc_url, headers=HEADERS, timeout=15)
    resp4.encoding = resp4.apparent_encoding or "utf-8"
    print(f"  Status={resp4.status_code} Length={len(resp4.text)}")
    soup4 = BeautifulSoup(resp4.text, "html.parser")
    tables4 = soup4.find_all("table")
    print(f"  Tables: {len(tables4)}")
    for ti, t in enumerate(tables4):
        text = t.get_text()
        if "매출" in text or "영업" in text or "증감" in text:
            print(f"\n  --- Table {ti} (has financial keywords) ---")
            rows = t.find_all("tr")
            for ri, row in enumerate(rows[:12]):
                cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                print(f"    Row {ri}: {cells}")
