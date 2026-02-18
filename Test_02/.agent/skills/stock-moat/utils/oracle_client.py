"""
Oracle financials client (Oracle -> TTM revenue/op income)

- Primary: python-oracledb thin mode
- Fallback: thick mode for old Oracle server versions (DPY-3010)
- SQL: Oracle 11g compatible (ROWNUM)
"""

import sys
from typing import List, Optional

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

try:
    import oracledb

    ORACLEDB_AVAILABLE = True
except ImportError:
    ORACLEDB_AVAILABLE = False

from data_quality import DataQuality, TTMFinancials


MILLION_TO_WON = 1_000_000
VIEW_NAME = '"V_FN_JEJO_LOAD_잠정포함"'


class OracleFinancialsClient:
    """Read TTM financials from Oracle view."""

    def __init__(self, dsn: str = None, user: str = None, password: str = None):
        self.dsn = dsn
        self.user = user
        self.password = password
        self._conn = None
        self._mode = "thin"

    def _connect_once(self):
        return oracledb.connect(user=self.user, password=self.password, dsn=self.dsn)

    def connect(self) -> bool:
        """Try Oracle connection. Return True on success, False otherwise."""
        if not ORACLEDB_AVAILABLE:
            print("    [INFO] oracledb not installed. Oracle lookup unavailable.")
            return False

        if not self.dsn or not self.user:
            print("    [INFO] Oracle config missing (.env)")
            return False

        try:
            self._conn = self._connect_once()
            self._mode = "thin"
            return True
        except Exception as thin_err:
            if "DPY-3010" in str(thin_err):
                try:
                    try:
                        oracledb.init_oracle_client()
                    except Exception as init_err:
                        # Ignore "already initialized" and proceed.
                        if "DPY-2019" not in str(init_err):
                            raise

                    self._conn = self._connect_once()
                    self._mode = "thick"
                    print("    [INFO] Oracle thick mode fallback: connected")
                    return True
                except Exception as thick_err:
                    print(f"    [WARN] Oracle thick mode fallback failed: {thick_err}")
                    self._conn = None
                    return False

            print(f"    [WARN] Oracle connection failed: {thin_err}")
            self._conn = None
            return False

    def close(self):
        """Close Oracle connection."""
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def is_connected(self) -> bool:
        return self._conn is not None

    def get_ttm(self, ticker: str) -> Optional[TTMFinancials]:
        """Get latest TTM row for ticker. Returns won-based values."""
        if not self._conn:
            return None

        stnd_cd = f"A{ticker}"

        sql = f"""
            SELECT YYYYQQ, SALE_AQ, BIZ_PRFT_AQ, COMPANY_NM
            FROM (
                SELECT YYYYQQ, SALE_AQ, BIZ_PRFT_AQ, COMPANY_NM
                FROM {VIEW_NAME}
                WHERE STND_CD = :stnd_cd
                  AND CON_GB = :con_gb
                ORDER BY YYYYQQ DESC
            )
            WHERE ROWNUM = 1
        """

        try:
            for con_gb in ("연결", "개별"):
                cursor = self._conn.cursor()
                cursor.execute(sql, {"stnd_cd": stnd_cd, "con_gb": con_gb})
                row = cursor.fetchone()
                cursor.close()

                if not row:
                    continue

                yyyyqq, sale_aq, biz_prft_aq, company_nm = row
                ttm_revenue = int((sale_aq or 0) * MILLION_TO_WON)
                ttm_op_income = int((biz_prft_aq or 0) * MILLION_TO_WON)

                dq = DataQuality(source="oracle", confidence="high", ttm_quarter=str(yyyyqq))

                return TTMFinancials(
                    ttm_revenue=ttm_revenue,
                    ttm_op_income=ttm_op_income,
                    ttm_quarter=str(yyyyqq),
                    company_name=company_nm or "",
                    data_quality=dq,
                )

            return None
        except Exception as e:
            print(f"    [WARN] Oracle TTM query failed: {e}")
            return None

    def get_trend(self, ticker: str, years: int = 3) -> Optional[List[dict]]:
        """Get annual-end TTM trend periods (latest first)."""
        if not self._conn:
            return None

        stnd_cd = f"A{ticker}"
        limit = years + 1

        sql = f"""
            SELECT YYYYQQ, SALE_AQ, BIZ_PRFT_AQ
            FROM (
                SELECT YYYYQQ, SALE_AQ, BIZ_PRFT_AQ
                FROM {VIEW_NAME}
                WHERE STND_CD = :stnd_cd
                  AND CON_GB = :con_gb
                  AND YYYYQQ IN (
                      SELECT MAX(YYYYQQ)
                      FROM {VIEW_NAME}
                      WHERE STND_CD = :stnd_cd2
                        AND CON_GB = :con_gb2
                      GROUP BY SUBSTR(TO_CHAR(YYYYQQ), 1, 4)
                  )
                ORDER BY YYYYQQ DESC
            )
            WHERE ROWNUM <= :limit
        """

        try:
            rows = []
            for con_gb in ("연결", "개별"):
                cursor = self._conn.cursor()
                cursor.execute(
                    sql,
                    {
                        "stnd_cd": stnd_cd,
                        "con_gb": con_gb,
                        "stnd_cd2": stnd_cd,
                        "con_gb2": con_gb,
                        "limit": limit,
                    },
                )
                rows = cursor.fetchall()
                cursor.close()
                if rows:
                    break

            if not rows:
                return None

            periods = []
            for yyyyqq, sale_aq, biz_prft_aq in rows:
                revenue = int((sale_aq or 0) * MILLION_TO_WON)
                op_income = int((biz_prft_aq or 0) * MILLION_TO_WON)
                op_margin = op_income / revenue if revenue > 0 else 0.0
                periods.append(
                    {
                        "quarter": str(yyyyqq),
                        "revenue": revenue,
                        "op_income": op_income,
                        "op_margin": op_margin,
                    }
                )

            return periods
        except Exception as e:
            print(f"    [WARN] Oracle trend query failed: {e}")
            return None
