"""
Moat Analysis Dashboard Service
Default source: DB moat_stock_snapshot (synced from Excel)
Fallback source: data/moat_analysis_summary.json
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from sqlalchemy import inspect as sa_inspect, text as sa_text

from ..database import SessionLocal
from ..models.moat_data import MoatStockSnapshot

DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "moat_analysis_summary.json"


def _get_sector_key_from_bm(bm_text: str) -> str:
    if not bm_text:
        return ""
    parts = [p.strip() for p in str(bm_text).split("/") if p and p.strip()]
    if not parts:
        return ""
    top = parts[0]
    if top == "제조업" and len(parts) >= 2:
        return parts[1]
    return top


def _build_dashboard_payload(stocks: List[dict], extracted_at: Optional[str] = None) -> dict:
    evaluated = [s for s in stocks if s["moat_score"] is not None]
    unevaluated = [s for s in stocks if s["moat_score"] is None]

    moat_dist = {str(i): 0 for i in range(6)}
    value_dist = {str(i): 0 for i in range(6)}
    matrix = {f"{m},{v}": 0 for m in range(6) for v in range(6)}
    sectors = {}

    moat_sum = 0
    value_sum = 0

    for stock in evaluated:
        moat = stock["moat_score"]
        value = stock["investment_value"] if stock["investment_value"] is not None else 0

        moat_dist[str(moat)] = moat_dist.get(str(moat), 0) + 1
        value_dist[str(value)] = value_dist.get(str(value), 0) + 1
        matrix[f"{moat},{value}"] = matrix.get(f"{moat},{value}", 0) + 1

        moat_sum += moat
        value_sum += value

        sector_key = _get_sector_key_from_bm(stock.get("bm", ""))
        if sector_key and sector_key not in ("분석실패", "None", ""):
            sectors[sector_key] = sectors.get(sector_key, 0) + 1

    high_value = [s for s in evaluated if (s["investment_value"] or 0) >= 4]

    return {
        "meta": {
            "total_stocks": len(stocks),
            "evaluated_count": len(evaluated),
            "unevaluated_count": len(unevaluated),
            "avg_moat": round(moat_sum / len(evaluated), 2) if evaluated else 0,
            "avg_value": round(value_sum / len(evaluated), 2) if evaluated else 0,
            "high_value_count": len(high_value),
            "extracted_at": extracted_at,
        },
        "distributions": {
            "moat": moat_dist,
            "investment_value": value_dist,
            "matrix": matrix,
        },
        "sectors": sectors,
        "stocks": stocks,
    }


class MoatDashboardService:
    def __init__(self):
        self._data = None
        self._load()

    def _load(self):
        db_data = self._load_from_db()
        if db_data:
            self._data = db_data
            return
        self._data = self._load_from_json()

    def _load_from_db(self) -> Optional[dict]:
        db = SessionLocal()
        try:
            inspector = sa_inspect(db.bind)
            if not inspector.has_table("moat_stock_snapshot"):
                return None
            self._ensure_snapshot_schema(db)

            rows = (
                db.query(MoatStockSnapshot)
                .filter(MoatStockSnapshot.is_active.is_(True))
                .all()
            )
            if not rows:
                return None

            latest_at = None
            stocks = []
            for row in rows:
                details = {}
                if row.details_json:
                    try:
                        details = json.loads(row.details_json)
                    except json.JSONDecodeError:
                        details = {}

                stocks.append(
                    {
                        "ticker": row.ticker,
                        "name": row.name,
                        "eval_date": row.eval_date or "",
                        "moat_score": row.moat_score,
                        "investment_value": row.investment_value,
                        "bm": row.bm or "",
                        "bigo_raw": row.bigo_raw or "",
                        "details": details,
                    }
                )
                if row.source_updated_at and (latest_at is None or row.source_updated_at > latest_at):
                    latest_at = row.source_updated_at

            extracted_at = None
            if latest_at:
                extracted_at = latest_at.astimezone(timezone.utc).isoformat()

            return _build_dashboard_payload(stocks, extracted_at=extracted_at)
        finally:
            db.close()

    def _ensure_snapshot_schema(self, db) -> None:
        inspector = sa_inspect(db.bind)
        columns = {col["name"] for col in inspector.get_columns("moat_stock_snapshot")}
        if "bigo_raw" in columns:
            return
        db.execute(sa_text("ALTER TABLE moat_stock_snapshot ADD COLUMN bigo_raw TEXT DEFAULT ''"))
        db.commit()

    def _load_from_json(self) -> Optional[dict]:
        if not DATA_PATH.exists():
            return None
        with open(DATA_PATH, "r", encoding="utf-8") as file:
            return json.load(file)

    def reload(self):
        self._load()

    def get_summary(self) -> dict:
        if not self._data:
            return self._empty()
        return {
            "meta": self._data["meta"],
            "distributions": self._data["distributions"],
            "sectors": self._data["sectors"],
        }

    def get_top_stocks(
        self,
        min_value: int = 4,
        sort_by: str = "investment_value",
        sort_desc: bool = True,
        limit: int = 50,
        sector: Optional[str] = None,
    ) -> List[dict]:
        if not self._data:
            return []
        filtered = [
            s for s in self._data["stocks"]
            if s.get("investment_value") is not None
            and s["investment_value"] >= min_value
            and s.get("moat_score") is not None
        ]
        if sector:
            filtered = [s for s in filtered if sector in (s.get("bm") or "")]
        filtered.sort(
            key=lambda s: (s.get(sort_by) or 0, s.get("moat_score") or 0),
            reverse=sort_desc,
        )
        return filtered[:limit]

    def get_stocks(
        self,
        min_moat: int = 0,
        min_value: int = 0,
        sector: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        if not self._data:
            return {"stocks": [], "total": 0}
        filtered = [
            s for s in self._data["stocks"]
            if s.get("moat_score") is not None
            and s["moat_score"] >= min_moat
            and (s.get("investment_value") or 0) >= min_value
        ]
        if sector:
            filtered = [s for s in filtered if sector in (s.get("bm") or "")]
        total = len(filtered)
        filtered.sort(
            key=lambda s: (s.get("investment_value") or 0, s.get("moat_score") or 0),
            reverse=True,
        )
        return {"stocks": filtered[offset: offset + limit], "total": total}

    def _empty(self) -> dict:
        return {
            "meta": {
                "total_stocks": 0,
                "evaluated_count": 0,
                "unevaluated_count": 0,
                "avg_moat": 0,
                "avg_value": 0,
                "high_value_count": 0,
                "extracted_at": datetime.now(timezone.utc).isoformat(),
            },
            "distributions": {"moat": {}, "investment_value": {}, "matrix": {}},
            "sectors": {},
        }
