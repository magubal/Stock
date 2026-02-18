"""
Growth Scorer - 업종별 성장 임계치 기반 해자 가감점 산출

Rules:
  +1: 양적+질적 성장 (CAGR >= 업종임계치 AND 이익률 개선)
  +1: 적자→흑자 전환 (턴어라운드)
   0: 양적 성장만 (CAGR >= 임계치 BUT 이익률 하락)
   0: 일회성 이익 (300%+ 급증)
   0: 데이터 부족 (<2 기간)
   0: 초대형주 경기민감 업종 역성장
  -1: 역성장 + 이익률 하락 (구조적 악화)
"""

import sys
import json
from typing import Tuple, List, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from data_quality import GrowthTrend


class GrowthScorer:
    """업종별 성장 임계치 기반 해자 가감점 산출"""

    def __init__(self, thresholds_path: str = None):
        self._config = self._load_config(thresholds_path)
        self._thresholds = self._config.get('thresholds', {})
        self._cyclical = self._config.get('cyclical_sectors', [])
        self._mega_cap = self._config.get('mega_cap_threshold', 10_000_000_000_000)
        self._spike_ratio = self._config.get('one_time_spike_ratio', 3.0)

    def _load_config(self, path: str = None) -> dict:
        if not path:
            try:
                from config import get_growth_thresholds_path
                path = get_growth_thresholds_path()
            except Exception:
                return {'thresholds': {'default': 0.10}}

        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {'thresholds': {'default': 0.10}}

    def build_trend(self, periods: List[dict]) -> GrowthTrend:
        """
        기간별 데이터로 GrowthTrend 구성.
        periods: [{quarter, revenue, op_income, op_margin}, ...] (최신순)
        """
        trend = GrowthTrend(periods=periods)

        if len(periods) < 2:
            return trend

        # CAGR 계산: 최신 vs 가장 오래된 기간
        latest = periods[0]
        oldest = periods[-1]

        if oldest['revenue'] > 0 and latest['revenue'] > 0:
            n_years = len(periods) - 1
            ratio = latest['revenue'] / oldest['revenue']
            if ratio > 0:
                trend.revenue_cagr = ratio ** (1 / n_years) - 1
            else:
                trend.revenue_cagr = -1.0

        # 영업이익률 변화 (최신 - 가장 오래된, %p)
        latest_margin = latest.get('op_margin', 0.0)
        oldest_margin = oldest.get('op_margin', 0.0)
        trend.op_margin_delta = (latest_margin - oldest_margin) * 100  # %p

        # 적자→흑자 전환 판별
        if len(periods) >= 2:
            prev_op = periods[1]['op_income']
            curr_op = periods[0]['op_income']
            trend.is_turnaround = (prev_op < 0 and curr_op > 0)

        # 일회성 이익 감지 (직전 대비 300%+)
        if len(periods) >= 2:
            prev_op = periods[1]['op_income']
            curr_op = periods[0]['op_income']
            if prev_op > 0 and curr_op > 0:
                spike = curr_op / prev_op
                trend.one_time_flag = (spike >= self._spike_ratio)

        return trend

    def score(
        self,
        trend: GrowthTrend,
        gics_sector: str,
        ttm_revenue: int = 0
    ) -> Tuple[int, str]:
        """
        성장 가감점 산출.

        Returns:
            (adjustment, reason)
        """
        if not trend or len(trend.periods) < 2:
            return (0, "데이터 부족")

        # 1. 적자→흑자 전환 (최우선)
        if trend.is_turnaround:
            return (+1, "턴어라운드 (적자→흑자)")

        # 2. 일회성 이익 (300%+ 급증)
        if trend.one_time_flag:
            return (0, "일회성 이익 의심 (제외)")

        threshold = self._get_threshold(gics_sector)
        cagr = trend.revenue_cagr
        margin_delta = trend.op_margin_delta  # %p

        # 3. 양적+질적 성장
        if cagr >= threshold and margin_delta > 0:
            return (+1, f"성장 우수 (CAGR {cagr:.1%} >= {threshold:.0%}, 마진 +{margin_delta:.1f}%p)")

        # 4. 양적 성장만 (이익률 하락)
        if cagr >= threshold and margin_delta <= 0:
            return (0, f"성장↑ 질↓ (CAGR {cagr:.1%}, 마진 {margin_delta:+.1f}%p)")

        # 5. 역성장 + 이익률 하락
        if cagr < 0 and margin_delta < 0:
            # 초대형주 경기민감 예외
            is_mega = ttm_revenue >= self._mega_cap
            is_cyclical = self._is_cyclical_sector(gics_sector)
            if is_mega and is_cyclical:
                return (0, f"사이클 예외 (초대형 {gics_sector})")
            return (-1, f"구조적 악화 (CAGR {cagr:.1%}, 마진 {margin_delta:+.1f}%p)")

        # 6. 역성장만 (이익률은 유지/개선)
        if cagr < 0 and margin_delta >= 0:
            return (0, f"매출↓ 마진유지 (CAGR {cagr:.1%})")

        # 7. 기타 (저성장)
        return (0, f"중립 (CAGR {cagr:.1%}, 임계치 {threshold:.0%})")

    def _get_threshold(self, gics_sector: str) -> float:
        return self._thresholds.get(gics_sector, self._thresholds.get('default', 0.10))

    def _is_cyclical_sector(self, gics_sector: str) -> bool:
        return gics_sector in self._cyclical
