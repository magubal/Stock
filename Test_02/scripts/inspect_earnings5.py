#!/usr/bin/env python3
"""손익구조 30% 변동 공시 — 테이블 구조 확인"""
import sys, re, time
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://kind.krx.co.kr/",
}

# 유진테크 손익구조 HTM
htm_url = "https://kind.krx.co.kr/external/2026/02/13/002140/20260204003163/70443.htm"
resp = requests.get(htm_url, headers=HEADERS, timeout=15)
resp.encoding = resp.apparent_encoding or "euc-kr"

soup = BeautifulSoup(resp.text, "html.parser")
tables = soup.find_all("table")
print(f"Total tables: {len(tables)}")

for ti, t in enumerate(tables):
    rows = t.find_all("tr")
    print(f"\n--- Table {ti} ({len(rows)} rows) ---")
    for ri, row in enumerate(rows):
        cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
        print(f"  Row {ri}: {cells}")
