"""
Financials Resolver
- Layer 1: Oracle TTM
- Layer 2: DART quarterly reconstruction (preferred fallback)
- Layer 3: DART annual fallback
"""

import sys
from datetime import date
from typing import List, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from data_quality import DataQuality, TTMFinancials


class FinancialsResolver:
    """Resolve TTM/trend with Oracle-first fallback strategy."""

    def __init__(self, oracle_client=None, dart_client=None):
        self.oracle = oracle_client
        self.dart = dart_client

    def resolve_ttm(self, ticker: str, corp_code: str, as_of_date: Optional[str] = None) -> Optional[TTMFinancials]:
        # Layer 1: Oracle
        result = self._layer1_oracle(ticker)
        if result:
            print(f"    {result.data_quality.label()} TTM 기준: {result.ttm_quarter}")
            return result

        # Layer 2: DART quarterly reconstruction
        result = self._layer2_dart_quarterly(corp_code, as_of_date=as_of_date)
        if result:
            print(f"    {result.data_quality.label()} TTM 기준: {result.ttm_quarter}")
            return result

        # Layer 3: DART annual fallback
        result = self._layer3_dart_annual(corp_code, as_of_date=as_of_date)
        if result:
            print(f"    {result.data_quality.label()} TTM 기준: {result.ttm_quarter}")
            return result

        print("    [WARN] TTM 조회 실패: all layers")
        return None

    def resolve_trend(
        self,
        ticker: str,
        corp_code: str,
        years: int = 3,
        as_of_date: Optional[str] = None,
    ) -> Optional[List[dict]]:
        # Layer 1: Oracle
        if self.oracle and self.oracle.is_connected():
            periods = self.oracle.get_trend(ticker, years)
            if periods and len(periods) >= 2:
                return periods

        # Layer 2: DART annual trend
        if self.dart:
            periods = self._dart_multi_year_trend(corp_code, years, as_of_date=as_of_date)
            if periods and len(periods) >= 2:
                return periods

        return None

    def _layer1_oracle(self, ticker: str) -> Optional[TTMFinancials]:
        if not self.oracle or not self.oracle.is_connected():
            return None
        return self.oracle.get_ttm(ticker)

    def _layer2_dart_quarterly(self, corp_code: str, as_of_date: Optional[str] = None) -> Optional[TTMFinancials]:
        """Reconstruct TTM using cumulative quarterly disclosures.

        TTM = current_cumulative + (prior_annual - prior_same_cumulative)
        Example: 2025Q3 cumulative + (2024 annual - 2024Q3 cumulative)
        """
        if not self.dart:
            return None

        print("    [INFO] DART quarterly reconstruction attempt...")
        current_year = self._base_year(as_of_date)

        for year in [current_year, current_year - 1]:
            for reprt_code, qtr_num in [("11014", "03"), ("11012", "02"), ("11013", "01")]:
                try:
                    current_partial = self.dart.get_financial_statements(corp_code, str(year), reprt_code)
                    if not current_partial or current_partial.get("revenue", 0) <= 0:
                        continue

                    prior_partial = self.dart.get_financial_statements(corp_code, str(year - 1), reprt_code)
                    prior_annual = self.dart.get_financial_statements(corp_code, str(year - 1), "11011")
                    if not prior_partial or not prior_annual:
                        continue
                    if prior_partial.get("revenue", 0) <= 0 or prior_annual.get("revenue", 0) <= 0:
                        continue

                    ttm_rev = current_partial["revenue"] + (prior_annual["revenue"] - prior_partial["revenue"])
                    ttm_op = current_partial.get("operating_income", 0) + (
                        prior_annual.get("operating_income", 0) - prior_partial.get("operating_income", 0)
                    )

                    quarter_label = f"{year}{qtr_num}"
                    dq = DataQuality(
                        source="dart_quarterly",
                        confidence="medium",
                        ttm_quarter=quarter_label,
                    )
                    return TTMFinancials(
                        ttm_revenue=ttm_rev,
                        ttm_op_income=ttm_op,
                        ttm_quarter=quarter_label,
                        data_quality=dq,
                    )
                except Exception:
                    continue

        return None

    def _layer3_dart_annual(self, corp_code: str, as_of_date: Optional[str] = None) -> Optional[TTMFinancials]:
        """Last fallback: use annual numbers as proxy for TTM."""
        if not self.dart:
            return None

        print("    [WARN] DART quarterly unavailable, annual fallback...")
        current_year = self._base_year(as_of_date)

        for year in range(current_year, current_year - 3, -1):
            try:
                data = self.dart.get_financial_statements(corp_code, str(year), "11011")
                if data and data.get("revenue", 0) > 0:
                    dq = DataQuality(
                        source="dart_annual",
                        confidence="low",
                        ttm_quarter=f"{year}04",
                    )
                    return TTMFinancials(
                        ttm_revenue=data.get("revenue", 0),
                        ttm_op_income=data.get("operating_income", 0),
                        ttm_quarter=f"{year}04",
                        data_quality=dq,
                    )
            except Exception:
                continue

        return None

    def _dart_multi_year_trend(
        self,
        corp_code: str,
        years: int,
        as_of_date: Optional[str] = None,
    ) -> Optional[List[dict]]:
        """Build annual trend periods from DART multi-year financials."""
        if not self.dart:
            return None

        try:
            base_year = self._base_year(as_of_date)
            query_years = [str(y) for y in range(base_year - (years + 1), base_year)]
            multi_year = self.dart.get_multi_year_financials(corp_code, years=query_years)
            if not multi_year:
                return None

            periods = []
            for year_str in sorted(multi_year.keys(), reverse=True):
                fin = multi_year[year_str]
                revenue = fin.get("revenue", 0)
                op_income = fin.get("operating_income", 0)
                if revenue > 0:
                    periods.append(
                        {
                            "quarter": f"{year_str}04",
                            "revenue": revenue,
                            "op_income": op_income,
                            "op_margin": op_income / revenue if revenue > 0 else 0.0,
                        }
                    )
                if len(periods) >= years + 1:
                    break

            return periods if len(periods) >= 2 else None
        except Exception:
            return None

    def _base_year(self, as_of_date: Optional[str]) -> int:
        if as_of_date:
            try:
                return date.fromisoformat(as_of_date).year
            except Exception:
                pass
        return date.today().year
