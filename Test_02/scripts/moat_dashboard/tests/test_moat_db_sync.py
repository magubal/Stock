import importlib.util
import os
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite://")

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "extract_moat_data.py"
SPEC = importlib.util.spec_from_file_location("extract_moat_data", SCRIPT_PATH)
extract_moat_data = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(extract_moat_data)

from backend.app.database import Base
from backend.app.models.moat_data import MoatStockHistory, MoatStockSnapshot


class MoatDbSyncTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def tearDown(self):
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def test_insert_creates_snapshot_and_history(self):
        stocks = [
            {
                "ticker": "005930",
                "name": "삼성전자",
                "eval_date": "2026-02-18",
                "moat_score": 5,
                "investment_value": 4,
                "bm": "반도체/메모리",
                "bigo_raw": "해자 5/5 | 증거3건(q6)",
                "details": {"evidence_count": 3},
            },
            {
                "ticker": "000660",
                "name": "SK하이닉스",
                "eval_date": "2026-02-18",
                "moat_score": 4,
                "investment_value": 4,
                "bm": "반도체/메모리",
                "bigo_raw": "해자 4/5 | 증거2건(q4)",
                "details": {"evidence_count": 2},
            },
        ]

        db = self.session_local()
        try:
            stats = extract_moat_data.sync_stocks_to_db(
                db=db,
                stocks=stocks,
                duplicate_count=0,
                source_file="국내상장종목 해자 투자가치.xlsx",
                imported_at=datetime(2026, 2, 18, 0, 0, 0),
                verify_wics_on_insert=False,
            )
            db.commit()
        finally:
            db.close()

        self.assertEqual(stats["inserted"], 2)
        self.assertEqual(stats["updated"], 0)
        self.assertEqual(stats["deactivated"], 0)

        db = self.session_local()
        try:
            snapshots = db.query(MoatStockSnapshot).all()
            self.assertEqual(len(snapshots), 2)
            samsung = next((row for row in snapshots if row.ticker == "005930"), None)
            self.assertIsNotNone(samsung)
            self.assertEqual(samsung.bigo_raw, "해자 5/5 | 증거3건(q6)")
            actions = [h.action for h in db.query(MoatStockHistory).all()]
            self.assertEqual(actions.count("insert"), 2)
        finally:
            db.close()

    def test_update_and_deactivate_are_logged(self):
        first = [
            {
                "ticker": "005930",
                "name": "삼성전자",
                "eval_date": "2026-02-18",
                "moat_score": 5,
                "investment_value": 4,
                "bm": "반도체/메모리",
                "bigo_raw": "해자 5/5 | 증거10건(q20)",
                "details": {},
            },
            {
                "ticker": "000660",
                "name": "SK하이닉스",
                "eval_date": "2026-02-18",
                "moat_score": 4,
                "investment_value": 4,
                "bm": "반도체/메모리",
                "bigo_raw": "해자 4/5 | 증거8건(q14)",
                "details": {},
            },
        ]
        second = [
            {
                "ticker": "005930",
                "name": "삼성전자",
                "eval_date": "2026-02-19",
                "moat_score": 4,
                "investment_value": 4,
                "bm": "반도체/메모리",
                "bigo_raw": "해자 4/5 | 증거11건(q21)",
                "details": {},
            },
            {
                "ticker": "035420",
                "name": "NAVER",
                "eval_date": "2026-02-19",
                "moat_score": 4,
                "investment_value": 3,
                "bm": "인터넷",
                "bigo_raw": "해자 4/5 | 증거7건(q10)",
                "details": {},
            },
        ]

        db = self.session_local()
        try:
            extract_moat_data.sync_stocks_to_db(
                db=db,
                stocks=first,
                duplicate_count=0,
                source_file="국내상장종목 해자 투자가치.xlsx",
                imported_at=datetime(2026, 2, 18, 0, 0, 0),
                verify_wics_on_insert=False,
            )
            db.commit()

            stats = extract_moat_data.sync_stocks_to_db(
                db=db,
                stocks=second,
                duplicate_count=0,
                source_file="국내상장종목 해자 투자가치.xlsx",
                imported_at=datetime(2026, 2, 19, 0, 0, 0),
                verify_wics_on_insert=False,
            )
            db.commit()
        finally:
            db.close()

        self.assertEqual(stats["inserted"], 1)
        self.assertEqual(stats["updated"], 1)
        self.assertEqual(stats["deactivated"], 1)

        db = self.session_local()
        try:
            removed = (
                db.query(MoatStockSnapshot)
                .filter(MoatStockSnapshot.ticker == "000660")
                .first()
            )
            self.assertIsNotNone(removed)
            self.assertFalse(removed.is_active)

            history_actions = [h.action for h in db.query(MoatStockHistory).all()]
            self.assertIn("update", history_actions)
            self.assertIn("deactivate", history_actions)
        finally:
            db.close()

    def test_new_insert_applies_wics_mapping_when_available(self):
        stocks = [
            {
                "ticker": "123456",
                "name": "테스트신규",
                "eval_date": "2026-02-19",
                "moat_score": 3,
                "investment_value": 3,
                "bm": "미분류",
                "bigo_raw": "해자 3/5 | 증거3건(q6)",
                "details": {"evidence_count": 3},
            }
        ]

        db = self.session_local()
        try:
            with patch.object(
                extract_moat_data,
                "resolve_wics_for_new_tickers",
                return_value={"123456": {"wics": "화장품", "status": "fetched", "error": ""}},
            ):
                stats = extract_moat_data.sync_stocks_to_db(
                    db=db,
                    stocks=stocks,
                    duplicate_count=0,
                    source_file="국내상장종목 해자 투자가치.xlsx",
                    imported_at=datetime(2026, 2, 19, 0, 0, 0),
                    verify_wics_on_insert=True,
                )
                db.commit()
        finally:
            db.close()

        self.assertEqual(stats["inserted"], 1)
        db = self.session_local()
        try:
            row = db.query(MoatStockSnapshot).filter(MoatStockSnapshot.ticker == "123456").first()
            self.assertIsNotNone(row)
            self.assertEqual(row.bm, "화장품")
            history = (
                db.query(MoatStockHistory)
                .filter(MoatStockHistory.ticker == "123456", MoatStockHistory.action == "insert")
                .first()
            )
            self.assertIsNotNone(history)
            payload = history.change_json
            self.assertIn("wics_verification", payload)
            self.assertIn("화장품", payload)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
