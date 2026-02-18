"""
Oracle repository for industry outlook / consensus / scenario snapshots.

Append-only snapshot storage with as_of_date semantics.
"""

import json
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional


class ForecastRepository:
    def __init__(self, oracle_client):
        self.oracle_client = oracle_client
        self._ready = False

    def is_available(self) -> bool:
        return bool(self.oracle_client and self.oracle_client.is_connected())

    def ensure_tables(self):
        if self._ready or not self.is_available():
            return

        self._ensure_table(
            "SR_INDUSTRY_OUTLOOK",
            """
            CREATE TABLE SR_INDUSTRY_OUTLOOK (
                ID VARCHAR2(40) PRIMARY KEY,
                SECTOR_KEY VARCHAR2(120) NOT NULL,
                SECTOR_TOP VARCHAR2(80),
                SECTOR_SUB VARCHAR2(120),
                SUMMARY CLOB,
                KEY_FACTORS_JSON CLOB,
                SOURCE VARCHAR2(30),
                CONFIDENCE VARCHAR2(20),
                AS_OF_DATE DATE,
                VALID_UNTIL DATE,
                CREATED_AT DATE DEFAULT SYSDATE
            )
            """,
        )
        self._ensure_table(
            "SR_STOCK_CONSENSUS",
            """
            CREATE TABLE SR_STOCK_CONSENSUS (
                ID VARCHAR2(40) PRIMARY KEY,
                TICKER VARCHAR2(20) NOT NULL,
                FISCAL_YEAR VARCHAR2(8) NOT NULL,
                REVENUE_EST NUMBER,
                OP_INCOME_EST NUMBER,
                UNIT VARCHAR2(20),
                RAW_JSON CLOB,
                SOURCE VARCHAR2(30),
                CONFIDENCE VARCHAR2(20),
                AS_OF_DATE DATE,
                FRESHNESS_DAYS NUMBER,
                CREATED_AT DATE DEFAULT SYSDATE
            )
            """,
        )
        self._ensure_table(
            "SR_FORECAST_SCENARIO",
            """
            CREATE TABLE SR_FORECAST_SCENARIO (
                ID VARCHAR2(40) PRIMARY KEY,
                TICKER VARCHAR2(20) NOT NULL,
                FISCAL_YEAR VARCHAR2(8) NOT NULL,
                SCENARIO VARCHAR2(12) NOT NULL,
                REVENUE_EST NUMBER,
                OP_INCOME_EST NUMBER,
                PROBABILITY NUMBER,
                SOURCE VARCHAR2(30),
                CONFIDENCE VARCHAR2(20),
                AS_OF_DATE DATE,
                CREATED_AT DATE DEFAULT SYSDATE
            )
            """,
        )
        self._ready = True

    def get_latest_outlook(self, sector_key: str) -> Optional[Dict[str, Any]]:
        if not self.is_available():
            return None
        self.ensure_tables()

        sql = """
            SELECT *
            FROM (
                SELECT
                    SECTOR_KEY,
                    SECTOR_TOP,
                    SECTOR_SUB,
                    SUMMARY,
                    KEY_FACTORS_JSON,
                    SOURCE,
                    CONFIDENCE,
                    AS_OF_DATE,
                    VALID_UNTIL,
                    CREATED_AT
                FROM SR_INDUSTRY_OUTLOOK
                WHERE SECTOR_KEY = :sector_key
                ORDER BY AS_OF_DATE DESC, CREATED_AT DESC
            )
            WHERE ROWNUM = 1
        """
        row = self._fetchone(sql, {"sector_key": sector_key})
        if not row:
            return None

        return {
            "sector_key": row[0],
            "sector_top": row[1],
            "sector_sub": row[2],
            "summary": row[3] or "",
            "key_factors": self._loads(row[4]),
            "source": row[5] or "unknown",
            "confidence": row[6] or "low",
            "as_of_date": self._date_to_iso(row[7]),
            "valid_until": self._date_to_iso(row[8]),
            "created_at": self._date_to_iso(row[9]),
            "reused": True,
        }

    def save_outlook(
        self,
        sector_key: str,
        sector_top: str,
        sector_sub: str,
        summary: str,
        key_factors: List[str],
        source: str,
        confidence: str,
        as_of_date: str,
        valid_until: str,
    ):
        if not self.is_available():
            return
        self.ensure_tables()

        sql = """
            INSERT INTO SR_INDUSTRY_OUTLOOK (
                ID, SECTOR_KEY, SECTOR_TOP, SECTOR_SUB, SUMMARY,
                KEY_FACTORS_JSON, SOURCE, CONFIDENCE, AS_OF_DATE, VALID_UNTIL
            ) VALUES (
                :id, :sector_key, :sector_top, :sector_sub, :summary,
                :key_factors_json, :source, :confidence, TO_DATE(:as_of_date, 'YYYY-MM-DD'), TO_DATE(:valid_until, 'YYYY-MM-DD')
            )
        """
        self._execute(
            sql,
            {
                "id": str(uuid.uuid4()),
                "sector_key": sector_key,
                "sector_top": sector_top,
                "sector_sub": sector_sub,
                "summary": summary,
                "key_factors_json": json.dumps(key_factors, ensure_ascii=False),
                "source": source,
                "confidence": confidence,
                "as_of_date": as_of_date,
                "valid_until": valid_until,
            },
        )

    def get_latest_consensus(self, ticker: str, fiscal_year: str) -> Optional[Dict[str, Any]]:
        if not self.is_available():
            return None
        self.ensure_tables()

        sql = """
            SELECT *
            FROM (
                SELECT
                    TICKER,
                    FISCAL_YEAR,
                    REVENUE_EST,
                    OP_INCOME_EST,
                    UNIT,
                    RAW_JSON,
                    SOURCE,
                    CONFIDENCE,
                    AS_OF_DATE,
                    FRESHNESS_DAYS,
                    CREATED_AT
                FROM SR_STOCK_CONSENSUS
                WHERE TICKER = :ticker
                  AND FISCAL_YEAR = :fiscal_year
                ORDER BY AS_OF_DATE DESC, CREATED_AT DESC
            )
            WHERE ROWNUM = 1
        """

        row = self._fetchone(sql, {"ticker": ticker, "fiscal_year": fiscal_year})
        if not row:
            return None

        return {
            "ticker": row[0],
            "fiscal_year": row[1],
            "revenue_est": float(row[2]) if row[2] is not None else None,
            "op_income_est": float(row[3]) if row[3] is not None else None,
            "unit": row[4] or "억원",
            "raw": self._loads(row[5]),
            "source": row[6] or "unknown",
            "confidence": row[7] or "low",
            "as_of_date": self._date_to_iso(row[8]),
            "freshness_days": int(row[9]) if row[9] is not None else None,
            "created_at": self._date_to_iso(row[10]),
            "reused": True,
        }

    def save_consensus(self, data: Dict[str, Any]):
        if not self.is_available():
            return
        self.ensure_tables()

        sql = """
            INSERT INTO SR_STOCK_CONSENSUS (
                ID, TICKER, FISCAL_YEAR, REVENUE_EST, OP_INCOME_EST,
                UNIT, RAW_JSON, SOURCE, CONFIDENCE, AS_OF_DATE, FRESHNESS_DAYS
            ) VALUES (
                :id, :ticker, :fiscal_year, :revenue_est, :op_income_est,
                :unit, :raw_json, :source, :confidence, TO_DATE(:as_of_date, 'YYYY-MM-DD'), :freshness_days
            )
        """
        self._execute(
            sql,
            {
                "id": str(uuid.uuid4()),
                "ticker": data.get("ticker"),
                "fiscal_year": str(data.get("fiscal_year")),
                "revenue_est": data.get("revenue_est"),
                "op_income_est": data.get("op_income_est"),
                "unit": data.get("unit", "억원"),
                "raw_json": json.dumps(data.get("raw", {}), ensure_ascii=False),
                "source": data.get("source", "fnguide"),
                "confidence": data.get("confidence", "medium"),
                "as_of_date": data.get("as_of_date", date.today().isoformat()),
                "freshness_days": data.get("freshness_days", 0),
            },
        )

    def save_scenarios(
        self,
        ticker: str,
        fiscal_year: str,
        scenarios: List[Dict[str, Any]],
        as_of_date: str,
        source: str = "scenario_model",
        confidence: str = "medium",
    ):
        if not self.is_available() or not scenarios:
            return
        self.ensure_tables()

        sql = """
            INSERT INTO SR_FORECAST_SCENARIO (
                ID, TICKER, FISCAL_YEAR, SCENARIO, REVENUE_EST, OP_INCOME_EST,
                PROBABILITY, SOURCE, CONFIDENCE, AS_OF_DATE
            ) VALUES (
                :id, :ticker, :fiscal_year, :scenario, :revenue_est, :op_income_est,
                :probability, :source, :confidence, TO_DATE(:as_of_date, 'YYYY-MM-DD')
            )
        """

        for item in scenarios:
            self._execute(
                sql,
                {
                    "id": str(uuid.uuid4()),
                    "ticker": ticker,
                    "fiscal_year": str(fiscal_year),
                    "scenario": item.get("scenario"),
                    "revenue_est": item.get("revenue_est"),
                    "op_income_est": item.get("op_income_est"),
                    "probability": item.get("probability"),
                    "source": source,
                    "confidence": confidence,
                    "as_of_date": as_of_date,
                },
            )

    def _ensure_table(self, table_name: str, ddl_sql: str):
        exists_sql = "SELECT COUNT(*) FROM USER_TABLES WHERE TABLE_NAME = :table_name"
        row = self._fetchone(exists_sql, {"table_name": table_name.upper()})
        if row and int(row[0]) > 0:
            return
        self._execute(ddl_sql, {})

    def _execute(self, sql: str, binds: Dict[str, Any]):
        conn = self.oracle_client._conn
        cursor = conn.cursor()
        try:
            cursor.execute(sql, binds)
            conn.commit()
        finally:
            cursor.close()

    def _fetchone(self, sql: str, binds: Dict[str, Any]):
        conn = self.oracle_client._conn
        cursor = conn.cursor()
        try:
            cursor.execute(sql, binds)
            return cursor.fetchone()
        finally:
            cursor.close()

    @staticmethod
    def _loads(payload: Any) -> Any:
        if payload is None:
            return {}
        if hasattr(payload, "read"):
            payload = payload.read()
        if not payload:
            return {}
        try:
            return json.loads(payload)
        except Exception:
            return {}

    @staticmethod
    def _date_to_iso(value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return str(value)
