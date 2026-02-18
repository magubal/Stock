#!/usr/bin/env python3
"""계약 공시 점수 검증"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')

with open("dashboard/data/latest_disclosures.json", encoding="utf-8") as f:
    data = json.load(f)

contracts = [d for d in data["disclosures"] if d["event_class"] == "supply_contract"]

print(f"계약 공시 총 {len(contracts)}건\n")
print(f"{'점수':>6} | {'감성':8} | {'회사':15} | {'제목':40} | {'상세'}")
print("=" * 130)

for d in sorted(contracts, key=lambda x: x["impact_score"], reverse=True):
    score = d["impact_score"]
    marker = "***" if score >= 30 else "---" if score <= -10 else "   "
    print(f"{marker} {score:+6.1f} | {d['sentiment']:8} | {d['company']:15} | {d['title'][:40]:40} | {d.get('detail', '')[:60]}")

print(f"\n점수 분포:")
for threshold, label in [(50, "+50 (매출대비 30%↑)"), (30, "+30 (매출대비 20%↑ 또는 정정 금액+20%)"),
                         (10, "+10 (매출대비 10%↑)"), (3.5, "+3.5 (기본)"), (-30, "-30 (해지)")]:
    count = len([d for d in contracts if d["impact_score"] == threshold])
    if count:
        print(f"  {label}: {count}건")

# 기타 점수
other = [d for d in contracts if d["impact_score"] not in (50, 30, 10, 3.5, -30)]
if other:
    print(f"  기타: {len(other)}건")
    for d in other:
        print(f"    {d['company']} score={d['impact_score']} | {d.get('detail','')}")
