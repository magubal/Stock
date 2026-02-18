#!/usr/bin/env python3
"""실적 공시 상세 페이지 HTML 구조 진단"""
import sys, json, time, re
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

# 실적 관련 공시 URL 가져오기
with open("data/disclosures/2026-02-14.json", encoding="utf-8") as f:
    data = json.load(f)

earnings = [d for d in data if "손익구조" in d["title"] or "잠정" in d["title"]]
print(f"실적 관련 공시: {len(earnings)}건")

# 각 타입별 1건씩 테스트
test_cases = {}
for e in earnings:
    if "손익구조" in e["title"] and "손익구조" not in test_cases:
        test_cases["손익구조"] = e
    if "잠정" in e["title"] and "잠정" not in test_cases:
        test_cases["잠정"] = e
    if len(test_cases) >= 2:
        break

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

for label, item in test_cases.items():
    print(f"\n{'='*80}")
    print(f"[{label}] {item['company']} — {item['title'][:60]}")
    print(f"URL: {item['url']}")

    resp = requests.get(item["url"], headers=HEADERS, timeout=15)
    resp.encoding = resp.apparent_encoding or "utf-8"
    print(f"Status: {resp.status_code}, Length: {len(resp.text)}")

    soup = BeautifulSoup(resp.text, "html.parser")

    # iframe/frame 찾기
    frames = soup.find_all(["frame", "iframe"])
    print(f"Frames: {len(frames)}")
    for fr in frames:
        src = fr.get("src", "")
        name = fr.get("name", "")
        print(f"  name={name} src={src[:120]}")

    # 테이블 찾기 (혹시 직접 내용이 있는지)
    tables = soup.find_all("table")
    print(f"Tables: {len(tables)}")

    # script 태그에서 document URL 패턴 찾기
    scripts = soup.find_all("script")
    for s in scripts:
        text = s.string or ""
        if "dcmNo" in text or "eleId" in text or "viewer" in text.lower() or "dart" in text.lower():
            # 관련 URL 패턴 추출
            urls = re.findall(r'https?://[^\s"\'<>]+', text)
            vars_match = re.findall(r'(var\s+\w+\s*=\s*["\'][^"\']*["\'])', text)
            if urls or vars_match:
                print(f"  Script URLs: {urls[:3]}")
                print(f"  Script vars: {vars_match[:5]}")

    # HTML 저장
    fname = f"kind_earnings_{label}.html"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(resp.text)
    print(f"  → {fname} 저장")

    time.sleep(2)
