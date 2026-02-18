#!/usr/bin/env python3
"""KIND 뷰어 페이지 JavaScript 분석 — 문서 URL 패턴 추출"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

for fname in ["kind_earnings_잠정.html", "kind_earnings_손익구조.html"]:
    try:
        with open(fname, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        continue

    print(f"\n=== {fname} ===")

    # script 태그 추출
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
    for i, s in enumerate(scripts):
        if len(s.strip()) > 50:
            print(f"\n--- Script {i} ({len(s)} chars) ---")
            print(s[:3000])
            print("..." if len(s) > 3000 else "")

    # acptno, docNo, rcpNo 관련 패턴 찾기
    all_vars = re.findall(r'var\s+(\w+)\s*=\s*["\']?([^"\';\n]+)["\']?', content)
    for name, val in all_vars:
        if val.strip():
            print(f"  VAR: {name} = {val.strip()[:80]}")

    # URL 패턴 찾기
    urls = re.findall(r'(?:src|href|url)\s*[=:]\s*["\']([^"\']+)["\']', content)
    for u in urls:
        if u and len(u) > 5 and not u.startswith("#"):
            print(f"  URL: {u[:120]}")

    # function 이름 찾기
    funcs = re.findall(r'function\s+(\w+)', content)
    print(f"  Functions: {funcs}")
