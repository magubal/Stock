#!/usr/bin/env python3
"""해지 / 정정 계약 공시 상세 페이지 구조 분석"""
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

contracts = [x for x in data["disclosures"] if x["event_class"] == "supply_contract"]


def fetch_htm(viewer_url):
    """viewer URL -> docNo -> HTM URL -> HTM content"""
    resp = requests.get(viewer_url, headers=HEADERS, timeout=15)
    resp.encoding = resp.apparent_encoding or "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    select = soup.find("select", id="mainDoc")
    if not select:
        return None, []

    options = []
    for opt in select.find_all("option"):
        val = opt.get("value", "")
        text = opt.get_text(strip=True)
        if "|" in val:
            options.append((val.split("|")[0], text))

    if not options:
        return None, []

    # 첫 번째(최신) 문서
    doc_no = options[0][0]
    time.sleep(0.5)

    url2 = f"https://kind.krx.co.kr/common/disclsviewer.do?method=searchContents&docNo={doc_no}"
    resp2 = requests.get(url2, headers=HEADERS, timeout=15)
    resp2.encoding = "utf-8"
    match = re.search(r"setPath\([^,]*,\s*'(https://[^']+\.htm)'", resp2.text)
    if not match:
        return None, options

    htm_url = match.group(1)
    time.sleep(0.5)

    resp3 = requests.get(htm_url, headers=HEADERS, timeout=15)
    resp3.encoding = resp3.apparent_encoding or "euc-kr"
    return resp3.text, options


# ── 해지 공시 분석 ──
cancel = [x for x in contracts if "해지" in x["title"]]
if cancel:
    c = cancel[0]
    print(f"{'='*80}")
    print(f"[해지] {c['company']} — {c['title']}")
    print(f"URL: {c['url']}")
    print(f"{'='*80}")

    html, options = fetch_htm(c["url"])
    print(f"문서 옵션: {options}")

    if html:
        soup = BeautifulSoup(html, "html.parser")
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            print(f"\n  테이블 ({len(rows)} rows):")
            for j, row in enumerate(rows[:20]):
                cells = [td.get_text(strip=True)[:50] for td in row.find_all(["td", "th"])]
                print(f"    Row {j}: {cells}")

time.sleep(1)

# ── 정정 공시 분석 ──
correction = [x for x in contracts if "정정" in x["title"] and "해지" not in x["title"]]
if correction:
    c = correction[0]
    print(f"\n{'='*80}")
    print(f"[정정] {c['company']} — {c['title']}")
    print(f"URL: {c['url']}")
    print(f"{'='*80}")

    html, options = fetch_htm(c["url"])
    print(f"문서 옵션: {len(options)}개")
    for opt in options:
        print(f"  - [{opt[0]}] {opt[1]}")

    if html:
        soup = BeautifulSoup(html, "html.parser")
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            print(f"\n  테이블 ({len(rows)} rows):")
            for j, row in enumerate(rows[:30]):
                cells = [td.get_text(strip=True)[:50] for td in row.find_all(["td", "th"])]
                print(f"    Row {j}: {cells}")
            if len(rows) > 30:
                print(f"    ... ({len(rows) - 30} more rows)")
