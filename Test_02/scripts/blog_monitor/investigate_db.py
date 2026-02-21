#!/usr/bin/env python3
"""DB 조사 스크립트: 21일자 데이터 현황 파악 (1회용, 조회만)."""
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

print("=" * 70)
print("  DB 데이터 조사 보고서")
print("=" * 70)

# 1. 전체 blog_posts 건수
total = session.execute(text("SELECT count(*) FROM blog_posts")).scalar()
print(f"\n[1] blog_posts 전체: {total}건")

# 2. 날짜별 분포 (collected_at 기준)
print("\n[2] 날짜별 분포 (collected_at 기준):")
rows = session.execute(text("""
    SELECT date(collected_at) as dt, count(*) as cnt
    FROM blog_posts
    GROUP BY date(collected_at)
    ORDER BY dt
""")).fetchall()
for r in rows:
    print(f"    {r[0]}: {r[1]}건")

# 3. 21일자 상세 (블로거별)
print("\n[3] 21일자 블로거별 분포:")
rows = session.execute(text("""
    SELECT blogger, count(*) as cnt,
           min(time(collected_at)) as earliest,
           max(time(collected_at)) as latest
    FROM blog_posts
    WHERE date(collected_at) = '2026-02-21'
    GROUP BY blogger
    ORDER BY cnt DESC
""")).fetchall()
for r in rows:
    print(f"    {r[0]}: {r[1]}건 (시간: {r[2]} ~ {r[3]})")

# 4. 21일자 source 분포
print("\n[4] 21일자 source 분포:")
rows = session.execute(text("""
    SELECT source, count(*) as cnt
    FROM blog_posts
    WHERE date(collected_at) = '2026-02-21'
    GROUP BY source
""")).fetchall()
for r in rows:
    print(f"    {r[0]}: {r[1]}건")

# 5. 21일자 pub_date 분포 (실제 발행일)
print("\n[5] 21일자 수집 데이터의 실제 발행일(pub_date) 분포:")
rows = session.execute(text("""
    SELECT date(pub_date) as pd, count(*) as cnt
    FROM blog_posts
    WHERE date(collected_at) = '2026-02-21'
    GROUP BY date(pub_date)
    ORDER BY pd
""")).fetchall()
for r in rows:
    print(f"    발행일 {r[0]}: {r[1]}건")

# 6. 21일자 이전 날짜에 수집된 데이터 있는지
print("\n[6] 21일 이전에 수집된 데이터 존재 여부:")
before = session.execute(text("""
    SELECT count(*) FROM blog_posts
    WHERE date(collected_at) < '2026-02-21'
""")).scalar()
print(f"    21일 이전 수집: {before}건")

# 7. blog_summaries 현황
print("\n[7] blog_summaries 현황:")
try:
    sum_total = session.execute(text("SELECT count(*) FROM blog_summaries")).scalar()
    sum_21 = session.execute(text("""
        SELECT count(*) FROM blog_summaries WHERE post_id IN
        (SELECT id FROM blog_posts WHERE date(collected_at) = '2026-02-21')
    """)).scalar()
    print(f"    전체: {sum_total}건, 21일자 연관: {sum_21}건")
except Exception as e:
    print(f"    (테이블 없음 또는 오류: {e})")

# 8. --date 2026-02-21로 등록한 데이터 식별 시도
print("\n[8] --date로 등록된 데이터 식별 (FILE_IMPORT source):")
rows = session.execute(text("""
    SELECT source, count(*) FROM blog_posts
    WHERE date(collected_at) = '2026-02-21'
    GROUP BY source
""")).fetchall()
for r in rows:
    print(f"    source='{r[0]}': {r[1]}건")

# 9. 21일자 샘플 데이터 (처음/마지막 각 3건)
print("\n[9] 21일자 데이터 샘플 (처음 5건):")
rows = session.execute(text("""
    SELECT id, blogger, substr(title, 1, 40) as title,
           datetime(collected_at) as cat, source
    FROM blog_posts
    WHERE date(collected_at) = '2026-02-21'
    ORDER BY collected_at ASC
    LIMIT 5
""")).fetchall()
for r in rows:
    print(f"    id={r[0]} | {r[1]} | {r[2]}... | {r[3]} | src={r[4]}")

print("\n[9b] 21일자 데이터 샘플 (마지막 5건):")
rows = session.execute(text("""
    SELECT id, blogger, substr(title, 1, 40) as title,
           datetime(collected_at) as cat, source
    FROM blog_posts
    WHERE date(collected_at) = '2026-02-21'
    ORDER BY collected_at DESC
    LIMIT 5
""")).fetchall()
for r in rows:
    print(f"    id={r[0]} | {r[1]} | {r[2]}... | {r[3]} | src={r[4]}")

session.close()
print("\n" + "=" * 70)
print("  조사 완료 - 삭제 전 사용자 승인 필요")
print("=" * 70)
