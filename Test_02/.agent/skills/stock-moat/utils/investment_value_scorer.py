"""
Investment Value Scorer — 투자가치 0~5점 자동 채점

채점 요소 (가중합산 → 0~5 정수):
  1. 수익성 (0~2점): 영업이익률 기반
  2. 해자강도 (0~1.5점): 해자 점수 비례
  3. 밸류에이션 (0~1점): op_multiple 기반 (낮을수록 매력)
  4. 성장성 (0~0.5점): CAGR + 마진 개선

감점 규칙:
  - 영업적자 → 수익성 0, 밸류에이션 0
  - 데이터 시점 괴리 90일+ → -0.5
  - BM 완성도 20% 미만 → -0.5
"""

import sys
from typing import Optional, Tuple

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


class InvestmentValueScorer:
    """투자가치 0-5점 자동 채점기"""

    # 영업이익률 → 수익성 점수 (0~2)
    MARGIN_TIERS = [
        (0.20, 2.0),   # 20%+ → 2점
        (0.10, 1.5),   # 10%+ → 1.5점
        (0.05, 1.0),   # 5%+  → 1점
        (0.00, 0.5),   # 0%+  → 0.5점 (흑자)
    ]

    # op_multiple → 밸류 점수 (0~1)
    MULTIPLE_TIERS = [
        (10,  1.0),   # 10x 이하 → 1점 (저평가)
        (20,  0.75),  # 20x 이하 → 0.75점
        (30,  0.5),   # 30x 이하 → 0.5점
        (50,  0.25),  # 50x 이하 → 0.25점
    ]

    def score(
        self,
        moat_strength: int,
        ttm_op_margin: float,
        ttm_op_income: int,
        op_multiple: Optional[float],
        revenue_cagr: Optional[float],
        margin_delta: Optional[float],
        bm_completeness: float = 0.0,
        data_gap_days: int = 0,
    ) -> Tuple[int, str]:
        """
        투자가치 점수 산출.

        Args:
            moat_strength: 해자강도 (0-5)
            ttm_op_margin: TTM 영업이익률 (0.0~1.0)
            ttm_op_income: TTM 영업이익 (원)
            op_multiple: 시총/영업이익 배수 (None이면 산출 불가)
            revenue_cagr: 매출 CAGR (0.0~, None이면 데이터 없음)
            margin_delta: 영업이익률 변화 (%p, None이면 데이터 없음)
            bm_completeness: BM 분석 완성도 (0.0~1.0)
            data_gap_days: 가격-TTM 시점 괴리 일수

        Returns:
            (score: int 0-5, reason: str)
        """
        details = []
        total = 0.0

        # ── 1. 수익성 (0~2점) ──
        profitability = 0.0
        if ttm_op_income <= 0:
            profitability = 0.0
            details.append("수익성 0 (영업적자)")
        else:
            for threshold, pts in self.MARGIN_TIERS:
                if ttm_op_margin >= threshold:
                    profitability = pts
                    break
            details.append(f"수익성 {profitability} (마진 {ttm_op_margin:.1%})")
        total += profitability

        # ── 2. 해자강도 (0~1.5점) ──
        moat_pts = min(moat_strength, 5) * 0.3  # 5*0.3 = 1.5
        total += moat_pts
        details.append(f"해자 {moat_pts:.1f} ({moat_strength}/5)")

        # ── 3. 밸류에이션 (0~1점) ──
        valuation_pts = 0.0
        if ttm_op_income <= 0 or op_multiple is None:
            valuation_pts = 0.0
            details.append("밸류 0 (산출불가)")
        else:
            for threshold, pts in self.MULTIPLE_TIERS:
                if op_multiple <= threshold:
                    valuation_pts = pts
                    break
            details.append(f"밸류 {valuation_pts} (op_multiple {op_multiple:.1f}x)")
        total += valuation_pts

        # ── 4. 성장성 (0~0.5점) ──
        growth_pts = 0.0
        if revenue_cagr is not None and margin_delta is not None:
            if revenue_cagr >= 0.10 and margin_delta > 0:
                growth_pts = 0.5
            elif revenue_cagr >= 0.05 and margin_delta >= 0:
                growth_pts = 0.25
            details.append(f"성장 {growth_pts} (CAGR {revenue_cagr:.1%}, Δ{margin_delta:+.1f}%p)")
        else:
            details.append("성장 0 (데이터부족)")
        total += growth_pts

        # ── 감점 ──
        penalty = 0.0
        if data_gap_days > 90:
            penalty += 0.5
            details.append(f"감점 -0.5 (시점괴리 {data_gap_days}일)")
        if bm_completeness < 0.20:
            penalty += 0.5
            details.append(f"감점 -0.5 (BM완성도 {bm_completeness:.0%})")
        total -= penalty

        # ── 최종 점수 (0~5 정수) ──
        final = max(0, min(5, round(total)))
        reason = " | ".join(details)

        return (final, reason)
