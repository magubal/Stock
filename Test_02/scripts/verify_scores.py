#!/usr/bin/env python3
"""실적 공시 점수 검증"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')

with open("dashboard/data/latest_disclosures.json", encoding="utf-8") as f:
    data = json.load(f)

earnings = [d for d in data["disclosures"]
            if d["event_class"] in ("earnings_surprise", "earnings_guidance", "earnings_variance")]

print(f"실적 공시 총 {len(earnings)}건")
print(f"\n{'='*100}")

for d in sorted(earnings, key=lambda x: x["impact_score"]):
    score = d["impact_score"]
    marker = "***" if score == 30 else "---" if score == -10 else "   "
    print(f"  {marker} {score:+4} | {d['sentiment']:8} | {d['company']:12} | {d['title'][:45]} | {d['detail'][:50]}")

print(f"\n점수 분포:")
score_30 = [d for d in earnings if d["impact_score"] == 30]
score_neg10 = [d for d in earnings if d["impact_score"] == -10]
score_other = [d for d in earnings if d["impact_score"] not in (30, -10)]
print(f"  +30 (30%이상 성장): {len(score_30)}건")
print(f"  -10 (전년대비 감소): {len(score_neg10)}건")
print(f"  기타 (상세 미확보): {len(score_other)}건")
