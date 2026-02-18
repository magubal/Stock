"""통합 수집 CLI — 파일 확장자에 따라 파서 자동 선택 후 DB 저장"""
import os
import sys
import argparse

sys.stdout.reconfigure(encoding="utf-8")

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _project_root)

# backend/.env의 SQLite 경로를 절대경로로 설정
_db_path = os.path.join(_project_root, "backend", "stock_research.db")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_db_path}")
os.environ.setdefault("DEBUG", "true")

from parsers.base_parser import DailyWorkRow
from parsers.excel_parser import ExcelParser
from parsers.text_parser import TextParser

# 파서 레지스트리
PARSERS = [ExcelParser(), TextParser()]


def select_parser(file_path: str):
    for p in PARSERS:
        if p.supports(file_path):
            return p
    return None


def save_to_db(rows: list):
    """DailyWorkRow 리스트를 DB에 저장"""
    import hashlib
    from backend.app.database import SessionLocal, engine, Base
    import backend.app.models  # noqa: F401 — register all models
    Base.metadata.create_all(bind=engine)
    from backend.app.models.daily_work import DailyWork

    db = SessionLocal()
    saved, skipped = 0, 0
    try:
        for row in rows:
            c_hash = hashlib.sha256(row.content.encode("utf-8")).hexdigest()

            existing = (
                db.query(DailyWork)
                .filter(
                    DailyWork.date == row.date,
                    DailyWork.category == row.category,
                    DailyWork.content_hash == c_hash,
                )
                .first()
            )
            if existing:
                skipped += 1
                continue

            db_item = DailyWork(
                date=row.date,
                category=row.category,
                description=row.description,
                content=row.content,
                source_link=row.source_link,
                source_type=row.source_type,
                content_hash=c_hash,
            )
            db.add(db_item)
            saved += 1

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[ERROR] DB 저장 실패: {e}")
        raise
    finally:
        db.close()

    return saved, skipped


def run_extract(work_ids: list):
    """저장된 daily_work에서 인사이트 추출"""
    from backend.app.database import SessionLocal
    from backend.app.models.daily_work import DailyWork
    from backend.app.models.insight import Insight
    from backend.app.services.insight_extractor import InsightExtractor
    from backend.app.config import settings
    import json

    api_key = getattr(settings, "ANTHROPIC_API_KEY", None)
    extractor = InsightExtractor(api_key=api_key)

    if not extractor.client:
        print("[WARN] ANTHROPIC_API_KEY 미설정 — 인사이트 추출 건너뜀")
        return 0

    db = SessionLocal()
    total = 0
    try:
        for wid in work_ids:
            work = db.query(DailyWork).filter(DailyWork.id == wid).first()
            if not work:
                continue
            results = extractor.extract(work.content, work.category)
            for r in results:
                db_item = Insight(
                    work_id=work.id,
                    type=r["type"],
                    text=r["text"],
                    confidence=r.get("confidence", 0.5),
                    keywords=json.dumps(r.get("keywords", []), ensure_ascii=False),
                    source_ai="claude",
                )
                db.add(db_item)
                total += 1
        db.commit()
    finally:
        db.close()

    return total


def main():
    parser = argparse.ArgumentParser(description="아이디어 파이프라인 — 데이터 수집 CLI")
    parser.add_argument("file", help="수집할 파일 경로")
    parser.add_argument("--extract", action="store_true", help="LLM 인사이트 추출도 실행")
    parser.add_argument("--dry-run", action="store_true", help="DB 저장 없이 파싱 결과만 출력")
    args = parser.parse_args()

    file_path = os.path.abspath(args.file)
    if not os.path.exists(file_path):
        print(f"[ERROR] 파일 없음: {file_path}")
        sys.exit(1)

    p = select_parser(file_path)
    if not p:
        print(f"[ERROR] 지원하지 않는 파일 형식: {file_path}")
        sys.exit(1)

    print(f"[INFO] 파서: {p.__class__.__name__}")
    print(f"[INFO] 파일: {file_path}")

    rows = p.parse(file_path)
    print(f"[INFO] 파싱 완료: {len(rows)}건")

    # 카테고리별 통계
    cat_counts = {}
    for r in rows:
        cat_counts[r.category] = cat_counts.get(r.category, 0) + 1
    for cat, cnt in sorted(cat_counts.items()):
        print(f"  {cat}: {cnt}건")

    if args.dry_run:
        print("[DRY-RUN] DB 저장 건너뜀")
        for i, r in enumerate(rows[:5]):
            print(f"  [{i}] {r.date} | {r.category} | {r.description[:50]}...")
        return

    saved, skipped = save_to_db(rows)
    print(f"[INFO] DB 저장: {saved}건 신규, {skipped}건 중복 스킵")

    if args.extract and saved > 0:
        # 방금 저장한 work ID로 추출
        from backend.app.database import SessionLocal
        from backend.app.models.daily_work import DailyWork
        db = SessionLocal()
        recent = db.query(DailyWork.id).order_by(DailyWork.id.desc()).limit(saved).all()
        db.close()
        work_ids = [r.id for r in recent]
        extracted = run_extract(work_ids)
        print(f"[INFO] 인사이트 추출: {extracted}건")


if __name__ == "__main__":
    main()
