#!/usr/bin/env python3
"""KIND 실적 공시 — 실제 문서 내용 가져오기 테스트"""
import sys, re, time, json
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://kind.krx.co.kr/",
}

# 테스트용 URL 2건
with open("data/disclosures/2026-02-14.json", encoding="utf-8") as f:
    data = json.load(f)

test_cases = []
for d in data:
    if "손익구조" in d["title"] and len(test_cases) < 1:
        test_cases.append(d)
    if "잠정" in d["title"] and len(test_cases) < 2:
        test_cases.append(d)
    if len(test_cases) >= 2:
        break

for item in test_cases:
    print(f"\n{'='*80}")
    print(f"{item['company']} — {item['title'][:60]}")

    # Step 1: viewer 페이지에서 mainDoc select의 option 값(docNo) 추출
    resp = requests.get(item["url"], headers=HEADERS, timeout=15)
    resp.encoding = resp.apparent_encoding or "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    select = soup.find("select", id="mainDoc")
    if select:
        options = select.find_all("option")
        print(f"  mainDoc options: {len(options)}")
        for opt in options:
            val = opt.get("value", "")
            text = opt.get_text(strip=True)
            print(f"    value={val} text={text}")

    # docNo 추출
    doc_no = ""
    if select:
        for opt in select.find_all("option"):
            val = opt.get("value", "")
            if "|" in val:
                doc_no = val.split("|")[0]
                break

    if not doc_no:
        print("  docNo를 찾을 수 없음")
        time.sleep(2)
        continue

    print(f"  docNo: {doc_no}")

    # Step 2: search 함수가 호출하는 URL 확인
    # viewer.js의 search() 함수는 보통 /common/disclsviewer.do?method=searchContents 호출
    # 또는 iframe src를 docpath로 설정

    # 방법 1: searchContents API 시도
    search_url = f"https://kind.krx.co.kr/common/disclsviewer.do?method=searchContents&docNo={doc_no}"
    print(f"  searchContents URL: {search_url}")

    resp2 = requests.get(search_url, headers=HEADERS, timeout=15)
    resp2.encoding = resp2.apparent_encoding or "utf-8"
    print(f"  Status: {resp2.status_code}, Length: {len(resp2.text)}")

    if len(resp2.text) > 100:
        soup2 = BeautifulSoup(resp2.text, "html.parser")
        tables = soup2.find_all("table")
        print(f"  Tables in content: {len(tables)}")

        # 테이블 내용 출력 (매출액, 영업이익 찾기)
        for ti, t in enumerate(tables):
            text = t.get_text()
            if "매출" in text or "영업이익" in text or "증감" in text:
                print(f"\n  --- Table {ti} (relevant) ---")
                rows = t.find_all("tr")
                for ri, row in enumerate(rows[:15]):
                    cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                    print(f"    Row {ri}: {cells}")

    # 방법 2: docpath 직접 접근 시도
    # viewer.js에서 setPath(docLocPath) → iframe.src = "/common/JLDDST60200_i2.jsp?docpath=" + docLocPath
    form = soup.find("form", id="docdownloadform") or soup.find("form", attrs={"name": "docdownloadform"})
    if form:
        doc_loc = form.find("input", attrs={"name": "docLocPath"})
        if doc_loc:
            docpath = doc_loc.get("value", "")
            print(f"\n  docLocPath: {docpath}")
            if docpath:
                content_url = f"https://kind.krx.co.kr/common/JLDDST60200_i2.jsp?docpath={docpath}"
                print(f"  Content URL: {content_url}")
                resp3 = requests.get(content_url, headers=HEADERS, timeout=15)
                resp3.encoding = resp3.apparent_encoding or "utf-8"
                print(f"  Status: {resp3.status_code}, Length: {len(resp3.text)}")

    time.sleep(2)
