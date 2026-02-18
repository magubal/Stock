"""
Investment Intelligence Engine — 시그널 생성 배치 스크립트
run_eod.py 이후 실행하거나 단독 실행 가능.

사용법:
    python scripts/intelligence/generate_signals.py [--days 3]
"""
import sys
import os
import argparse

sys.stdout.reconfigure(encoding="utf-8")

# 프로젝트 루트 → sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

# SQLite DB 경로 설정 (PostgreSQL 미사용 시)
_db_path = os.path.join(PROJECT_ROOT, "backend", "stock_research.db")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_db_path}")
os.environ.setdefault("DEBUG", "false")

from backend.app.database import SessionLocal
from backend.app.models import Base
from backend.app.database import engine


def main():
    parser = argparse.ArgumentParser(description="Investment Intelligence 시그널 생성")
    parser.add_argument("--days", type=int, default=3, help="컨텍스트 수집 기간 (일)")
    args = parser.parse_args()

    # 테이블 생성 보장
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        from backend.app.services.signal_service import SignalDetectionEngine

        print(f"[Signal] 시그널 생성 시작 (기간: {args.days}일)")
        engine_svc = SignalDetectionEngine(db)

        print(f"[Signal] 로드된 규칙: {len(engine_svc.rules)}개")
        for rule in engine_svc.rules:
            print(f"  - {rule['id']}: {rule['title']} ({len(rule['conditions'])}개 조건)")

        signals = engine_svc.generate_signals(days=args.days)

        print(f"\n[Signal] 생성 결과: {len(signals)}개 시그널")
        for sig in signals:
            conf = sig.get("confidence", 0)
            level = "HIGH" if conf >= 0.8 else "MED" if conf >= 0.6 else "LOW"
            print(f"  [{level}] {sig['signal_id']}: {sig['title']} (confidence={conf:.0%})")
            for ev in sig.get("evidence", []):
                print(f"       └─ {ev['label']}: {ev['value']}")

        if not signals:
            print("  (매칭된 시그널 없음 — 조건 미충족)")

    finally:
        db.close()

    print("\n[Signal] 완료")


if __name__ == "__main__":
    main()
