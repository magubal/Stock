#!/usr/bin/env python3
"""2026-02-21 잘못 수집된 데이터 삭제 스크립트 (1회용)."""
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

# 건수 확인
count = session.execute(
    text("SELECT count(*) FROM blog_posts WHERE date(collected_at) = '2026-02-21'")
).scalar()
print(f"21일자 블로그 글: {count}건")

if count == 0:
    print("삭제할 데이터 없음")
    session.close()
    sys.exit(0)

# 연관 summaries 먼저 삭제
sum_del = session.execute(
    text("""DELETE FROM blog_summaries WHERE post_id IN
            (SELECT id FROM blog_posts WHERE date(collected_at) = '2026-02-21')""")
).rowcount
print(f"  summaries 삭제: {sum_del}건")

# posts 삭제
post_del = session.execute(
    text("DELETE FROM blog_posts WHERE date(collected_at) = '2026-02-21'")
).rowcount
print(f"  posts 삭제: {post_del}건")

session.commit()
session.close()
print("[DONE] 21일자 데이터 삭제 완료")
