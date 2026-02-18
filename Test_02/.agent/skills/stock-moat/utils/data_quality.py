"""
Data quality and temporal consistency models.
"""

import sys
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class AsOfDate:
    """Unified temporal baseline metadata."""

    price_date: str = ""      # YYYY-MM-DD
    ttm_quarter: str = ""     # YYYYQQ (e.g. 202403)
    report_base: str = ""     # report label/year
    gap_days: int = 0
    gap_warning: bool = False

    def __post_init__(self):
        if not (self.ttm_quarter and self.price_date):
            return
        try:
            yyyy = int(self.ttm_quarter[:4])
            qq = int(self.ttm_quarter[4:])
            quarter_end_month = qq * 3
            days_in_month = {
                1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
                7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31,
            }
            quarter_end_day = days_in_month.get(quarter_end_month, 30)
            ttm_end = date(yyyy, quarter_end_month, quarter_end_day)
            price_d = date.fromisoformat(self.price_date)
            self.gap_days = (price_d - ttm_end).days
            self.gap_warning = self.gap_days > 90
        except (ValueError, TypeError):
            pass

    def to_dict(self) -> dict:
        return {
            "price_date": self.price_date,
            "ttm_quarter": self.ttm_quarter,
            "report_base": self.report_base,
            "gap_days": self.gap_days,
            "gap_warning": self.gap_warning,
        }


@dataclass
class DataQuality:
    """Result data source/quality metadata."""

    source: str                           # oracle | dart_quarterly | dart_annual
    freshness_days: int = 0
    confidence: str = "low"               # high | medium | low
    metric_name: str = "op_multiple"
    ttm_quarter: str = ""
    price_date: str = ""
    as_of_date: Optional[AsOfDate] = None
    warnings: List[str] = field(default_factory=list)
    unit: str = "KRW"

    def __post_init__(self):
        if self.as_of_date:
            if self.freshness_days <= 0 and self.as_of_date.gap_days > 0:
                self.freshness_days = self.as_of_date.gap_days
            if self.as_of_date.gap_warning and "stale_ttm_gap_gt_90d" not in self.warnings:
                self.warnings.append("stale_ttm_gap_gt_90d")

    def to_dict(self) -> dict:
        return {
            "data_source": self.source,
            "data_confidence": self.confidence,
            "data_freshness_days": self.freshness_days,
            "data_warnings": " | ".join(self.warnings) if self.warnings else "",
            "ttm_quarter": self.ttm_quarter,
            "price_date": self.price_date,
        }

    def label(self) -> str:
        return f"[{self.source}/{self.confidence}]"


@dataclass
class TTMFinancials:
    """Unified TTM financials model in KRW."""

    ttm_revenue: int = 0
    ttm_op_income: int = 0
    ttm_quarter: str = ""
    company_name: str = ""
    data_quality: Optional[DataQuality] = None

    @property
    def ttm_op_margin(self) -> float:
        if self.ttm_revenue and self.ttm_revenue > 0:
            return self.ttm_op_income / self.ttm_revenue
        return 0.0


@dataclass
class GrowthTrend:
    """3Y trend data."""

    periods: List[dict] = field(default_factory=list)
    revenue_cagr: float = 0.0
    op_margin_delta: float = 0.0
    is_turnaround: bool = False
    one_time_flag: bool = False
    growth_score: int = 0
    score_reason: str = ""


def format_krw(value: int) -> str:
    """Format KRW amount to readable Korean units."""
    if value is None:
        return "N/A"
    if abs(value) >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:.1f}조원"
    if abs(value) >= 100_000_000:
        return f"{value / 100_000_000:,.0f}억원"
    return f"{value:,}원"
