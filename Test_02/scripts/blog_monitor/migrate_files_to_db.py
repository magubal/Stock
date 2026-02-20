#!/usr/bin/env python3
"""
기존 파일 데이터(data/naver_blog_data/)를 DB(blog_posts)로 마이그레이션.
JSON 메타 + 이미지 파일을 읽어 blog_posts 테이블에 INSERT.
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

# project root
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_PATH = ROOT / "backend" / "stock_research.db"
BLOG_DIR = ROOT / "data" / "naver_blog_data"

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Session = sessionmaker(bind=engine)

# import model after engine (avoid circular)
from app.models.blog_post import BlogPost


def migrate():
    session = Session()
    inserted = 0
    skipped = 0

    # 날짜 폴더 순회
    for date_dir in sorted(BLOG_DIR.iterdir()):
        if not date_dir.is_dir() or date_dir.name == "index":
            continue

        date_str = date_dir.name  # YYYY-MM-DD

        for json_file in sorted(date_dir.glob("*.json")):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"  [SKIP] {json_file.name}: {e}")
                skipped += 1
                continue

            link = data.get("link", "")
            if not link:
                skipped += 1
                continue

            # 중복 체크
            existing = session.query(BlogPost).filter(BlogPost.link == link).first()
            if existing:
                skipped += 1
                continue

            # 이미지 경로 찾기
            stem = json_file.stem  # e.g., daybyday_001
            image_path = None
            image_size_kb = 0
            for ext in (".jpg", ".jpeg", ".png"):
                candidate = date_dir / f"{stem}{ext}"
                if candidate.exists():
                    image_path = str(candidate.relative_to(ROOT)).replace("\\", "/")
                    image_size_kb = int(candidate.stat().st_size / 1024)
                    break

            # pub_date 파싱
            pub_date = None
            raw_date = data.get("pub_date", "")
            if raw_date:
                try:
                    from email.utils import parsedate_to_datetime
                    pub_date = parsedate_to_datetime(raw_date)
                except Exception:
                    pass

            # collected_at
            collected_at = None
            raw_collected = data.get("collected_date", "")
            if raw_collected:
                try:
                    collected_at = datetime.fromisoformat(raw_collected)
                except Exception:
                    pass

            post = BlogPost(
                blogger=data.get("blogger", "unknown"),
                title=data.get("title", json_file.stem),
                link=link,
                pub_date=pub_date,
                text_content=None,  # 기존 데이터에는 텍스트 없음
                image_path=image_path,
                image_size_kb=image_size_kb,
                collected_at=collected_at,
                source="COLLECTOR",
            )
            session.add(post)
            inserted += 1

        if inserted > 0 and inserted % 50 == 0:
            session.commit()
            print(f"  ... {inserted} inserted so far")

    session.commit()
    session.close()
    print(f"\n[DONE] Inserted: {inserted}, Skipped: {skipped}")


if __name__ == "__main__":
    print("[MIGRATE] File data -> DB (blog_posts)")
    migrate()
