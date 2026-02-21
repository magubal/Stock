#!/usr/bin/env python3
"""삭제 후 검증 스크립트 (1회용)."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_PATH = ROOT / "backend" / "stock_research.db"
engine = create_engine(f"sqlite:///{DB_PATH}?timeout=30", echo=False)
Session = sessionmaker(bind=engine)
session = Session()

total = session.execute(text("SELECT count(*) FROM blog_posts")).scalar()
feb21 = session.execute(text(
    "SELECT count(*) FROM blog_posts WHERE date(collected_at) = '2026-02-21'"
)).scalar()
summ = session.execute(text("SELECT count(*) FROM blog_summaries")).scalar()

print(f"blog_posts: {total}건 (21일자: {feb21}건)")
print(f"blog_summaries: {summ}건 (보존됨)")

print("\n날짜별 분포:")
rows = session.execute(text("""
    SELECT date(collected_at) as dt, count(*) as cnt
    FROM blog_posts GROUP BY dt ORDER BY dt
""")).fetchall()
for r in rows:
    print(f"  {r[0]}: {r[1]}건")

session.close()
