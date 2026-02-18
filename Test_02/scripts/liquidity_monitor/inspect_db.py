"""DB 상태 조회 스크립트"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import create_engine, text
from config import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH}")
with engine.connect() as conn:
    tables = ['liquidity_macro','liquidity_price','liquidity_news','fed_tone','stress_index']
    print("=" * 70)
    print("  Liquidity Stress Monitor - DB Status")
    print("=" * 70)
    for t in tables:
        count = conn.execute(text(f'SELECT COUNT(*) FROM {t}')).scalar()
        latest = conn.execute(text(f'SELECT date FROM {t} ORDER BY date DESC LIMIT 1')).scalar()
        oldest = conn.execute(text(f'SELECT date FROM {t} ORDER BY date ASC LIMIT 1')).scalar()
        print(f"  {t:20s} | {count:4d} rows | {oldest} ~ {latest}")

    print("\n--- liquidity_macro (FRED data, last 5 days) ---")
    rows = conn.execute(text('SELECT * FROM liquidity_macro ORDER BY date DESC LIMIT 5')).fetchall()
    for r in rows:
        print(f"  {r[0]} | HY_OAS={r[1]} IG_OAS={r[2]} SOFR={r[3]} RRP={r[4]} 2Y={r[5]} 10Y={r[6]} 30Y={r[7]}")

    print("\n--- liquidity_price (VIX/TLT, last 6) ---")
    rows = conn.execute(text("SELECT * FROM liquidity_price WHERE symbol IN ('^VIX','TLT') ORDER BY date DESC LIMIT 6")).fetchall()
    for r in rows:
        print(f"  {r[0]} {r[1]:6s} | close={r[2]} high={r[3]} low={r[4]}")

    print("\n--- liquidity_news (latest date) ---")
    rows = conn.execute(text('SELECT date,keyword,count FROM liquidity_news ORDER BY date DESC, count DESC LIMIT 8')).fetchall()
    for r in rows:
        print(f"  {r[0]} | {r[1]:20s} | {r[2]} articles")

    print("\n--- fed_tone (last 3) ---")
    rows = conn.execute(text('SELECT * FROM fed_tone ORDER BY date DESC LIMIT 3')).fetchall()
    for r in rows:
        print(f"  {r[0]} | liq={r[1]} credit={r[2]} stability={r[3]}")

    print("\n--- stress_index (last 8 days) ---")
    rows = conn.execute(text('SELECT * FROM stress_index ORDER BY date DESC LIMIT 8')).fetchall()
    for r in rows:
        print(f"  {r[0]} | vol={r[1]} credit={r[2]} funding={r[3]} treasury={r[4]} news={r[5]} fed={r[6]} | total={r[7]} level={r[8]}")
