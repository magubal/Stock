"""liquidity_macro 전체 조회"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')
from sqlalchemy import create_engine, text
from config import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH}")
with engine.connect() as conn:
    rows = conn.execute(text("SELECT * FROM liquidity_macro ORDER BY date")).fetchall()

    print("=" * 90)
    print("  liquidity_macro - FRED Macro Indicators (ALL rows)")
    print("=" * 90)
    print(f"  {'date':12s} | {'HY_OAS':>7s} | {'IG_OAS':>7s} | {'SOFR':>7s} | {'RRP(B$)':>9s} | {'2Y':>6s} | {'10Y':>6s} | {'30Y':>6s}")
    print("  " + "-" * 86)

    for r in rows:
        def fmt(v):
            return "   N/A" if v is None else f"{v:7.3f}"

        rrp = "      N/A" if r[4] is None else f"{r[4]:9.3f}"
        print(f"  {r[0]:12s} | {fmt(r[1])} | {fmt(r[2])} | {fmt(r[3])} | {rrp} | {fmt(r[5]):>6s} | {fmt(r[6]):>6s} | {fmt(r[7]):>6s}")

    print(f"\n  Total: {len(rows)} rows")

    # Seed vs Real 구분
    seed = [r for r in rows if r[0] < "2026-02-09"]
    real = [r for r in rows if r[0] >= "2026-02-09"]
    print(f"  Seed data: {len(seed)} rows (01-15 ~ 02-08)")
    print(f"  Real FRED: {len(real)} rows (02-09 ~ 02-13)")
