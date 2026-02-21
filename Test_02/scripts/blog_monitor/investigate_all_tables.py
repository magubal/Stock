#!/usr/bin/env python3
"""DB 전체 테이블 조사: 21일자 블로그 관련 데이터 전수 확인 (조회만)."""
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
print("  DB 전체 테이블 조사 보고서")
print("=" * 70)

# 1. 전체 테이블 목록
print("\n[1] DB 내 전체 테이블 목록:")
tables = session.execute(text(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
)).fetchall()
for t in tables:
    cnt = session.execute(text(f"SELECT count(*) FROM [{t[0]}]")).scalar()
    print(f"    {t[0]}: {cnt}건")

# 2. blog 관련 테이블 식별
blog_tables = [t[0] for t in tables if 'blog' in t[0].lower()]
print(f"\n[2] blog 관련 테이블: {blog_tables}")

# 3. 각 blog 테이블의 스키마 확인
for tname in blog_tables:
    print(f"\n[3-{tname}] 테이블 스키마:")
    cols = session.execute(text(f"PRAGMA table_info([{tname}])")).fetchall()
    for c in cols:
        print(f"    {c[1]} ({c[2]}) {'PK' if c[5] else ''} {'NOT NULL' if c[3] else ''}")

# 4. blog_summaries 상세 (post_id FK 관계)
print("\n[4] blog_summaries 전체 데이터:")
try:
    rows = session.execute(text("""
        SELECT bs.id, bs.post_id, substr(bs.summary, 1, 50) as summary,
               bp.blogger, date(bp.collected_at) as collected_date
        FROM blog_summaries bs
        LEFT JOIN blog_posts bp ON bs.post_id = bp.id
        ORDER BY bs.id
    """)).fetchall()
    if rows:
        for r in rows:
            print(f"    summary_id={r[0]} | post_id={r[1]} | {r[2]}... | blogger={r[3]} | collected={r[4]}")
    else:
        print("    (데이터 없음)")
except Exception as e:
    print(f"    오류: {e}")

# 5. 다른 테이블에 blog_posts.id를 참조하는 FK가 있는지 확인
print("\n[5] Foreign Key 관계 확인:")
for t in tables:
    tname = t[0]
    fks = session.execute(text(f"PRAGMA foreign_key_list([{tname}])")).fetchall()
    if fks:
        for fk in fks:
            print(f"    {tname}.{fk[3]} → {fk[2]}.{fk[4]}")

# 6. 21일자와 시간대가 겹치는 다른 테이블 데이터 확인
print("\n[6] 다른 테이블의 21일자 데이터 존재 여부:")
for t in tables:
    tname = t[0]
    if tname in blog_tables:
        continue
    # created_at, collected_at, date 등 날짜 컬럼 탐색
    cols = session.execute(text(f"PRAGMA table_info([{tname}])")).fetchall()
    date_cols = [c[1] for c in cols if any(k in c[1].lower() for k in ['date', 'created', 'collected', 'updated', 'at'])]
    for dc in date_cols:
        try:
            cnt = session.execute(text(
                f"SELECT count(*) FROM [{tname}] WHERE date([{dc}]) = '2026-02-21'"
            )).scalar()
            if cnt > 0:
                print(f"    {tname}.{dc}: {cnt}건 (21일자)")
        except Exception:
            pass

print("\n" + "=" * 70)
print("  전체 테이블 조사 완료")
print("=" * 70)
