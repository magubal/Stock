"""
Dashboard Service - 투자 대시보드 비즈니스 로직
5개 엔드포인트에 대응하는 서비스 메서드 제공
"""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ..models import (
    InvestorSentiment, MarketData, PortfolioHolding,
    ResearchReport, FlywheelState
)

# 감성 레이블 매핑
SENTIMENT_MAP = {
    "positive": ("optimistic", "낙관적"),
    "neutral": ("cautious", "보수적"),
    "negative": ("pessimistic", "비관적"),
}

FLYWHEEL_STEPS = [
    "데이터 수집",
    "맥락 분석",
    "중요도 평가",
    "시나리오 작성",
    "실질 확인",
    "투자 결정",
    "사후 검증",
]


def _map_sentiment(score: float) -> tuple[str, str]:
    """감성 점수(-1~1)를 (sentiment, label) 튜플로 변환"""
    if score > 0.2:
        return "optimistic", "낙관적"
    elif score < -0.2:
        return "pessimistic", "비관적"
    return "cautious", "보수적"


def _score_color(score: float) -> str:
    if score >= 75:
        return "positive"
    elif score >= 50:
        return "warning"
    return "danger"


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    # ── 1. Psychology Metrics ──────────────────────────────
    async def get_psychology_metrics(self) -> dict:
        latest = (
            self.db.query(InvestorSentiment)
            .order_by(desc(InvestorSentiment.date))
            .first()
        )

        if not latest:
            return {
                "marketHeat": 0,
                "empathy": 50,
                "expectation": 50,
                "investorTypes": [],
            }

        market_heat = (latest.market_heat or 0) * 100
        empathy = ((latest.overall_score or 0) + 1) / 2 * 100
        short = latest.short_term_sentiment or 0
        long = latest.long_term_sentiment or 0
        expectation = (short * 0.4 + long * 0.6 + 1) / 2 * 100

        st_sent, st_label = _map_sentiment(short)
        lt_sent, lt_label = _map_sentiment(long)
        ov_sent, ov_label = _map_sentiment(latest.overall_score or 0)
        fg_sent, fg_label = _map_sentiment(latest.fear_greed_index or 0)

        return {
            "marketHeat": round(market_heat, 1),
            "empathy": round(empathy, 1),
            "expectation": round(expectation, 1),
            "investorTypes": [
                {"type": "단기 투자자", "sentiment": st_sent, "label": st_label},
                {"type": "중장기 투자자", "sentiment": lt_sent, "label": lt_label},
                {"type": "보유자", "sentiment": ov_sent, "label": ov_label},
                {"type": "잠재 투자자", "sentiment": fg_sent, "label": fg_label},
            ],
        }

    # ── 2. Timing Analysis ─────────────────────────────────
    async def get_timing_analysis(self) -> list:
        now = datetime.utcnow()
        results = []

        for months, period_label in [(3, "3개월"), (6, "6개월"), (12, "12개월")]:
            since = now - timedelta(days=months * 30)

            avg_row = (
                self.db.query(
                    func.avg(InvestorSentiment.overall_score).label("avg_sentiment"),
                    func.avg(InvestorSentiment.market_heat).label("avg_heat"),
                )
                .filter(InvestorSentiment.date >= since)
                .first()
            )

            avg_sentiment = float(avg_row.avg_sentiment or 0) if avg_row else 0
            avg_heat = float(avg_row.avg_heat or 0) if avg_row else 0

            if avg_heat >= 0.8 and avg_sentiment < -0.3:
                signal, label, reason = "danger", "투자 위험", "시장 과열 + 부정 심리"
            elif avg_heat >= 0.6 or avg_sentiment <= 0:
                signal, label, reason = "caution", "주의 필요", "과열 또는 보합 심리"
            else:
                signal, label, reason = "good", "투자 적합", "기대요소 > 우려요소"

            results.append({
                "period": period_label,
                "signal": signal,
                "label": label,
                "reason": reason,
            })

        return results

    # ── 3. Portfolio Overview ──────────────────────────────
    async def get_portfolio_overview(self) -> dict:
        holdings = (
            self.db.query(PortfolioHolding)
            .filter(PortfolioHolding.is_active == True)
            .all()
        )

        if not holdings:
            return {
                "totalStocks": 0,
                "avgReturn": 0,
                "sellSignals": 0,
                "alerts": [],
            }

        total = len(holdings)
        alerts: List[dict] = []
        sell_signals = 0
        total_return = 0.0

        # 최신 심리 지표 1회 조회 (루프 밖 — 성능 최적화)
        latest_sentiment = (
            self.db.query(InvestorSentiment)
            .order_by(desc(InvestorSentiment.date))
            .first()
        )

        for h in holdings:
            # 최신 시장 데이터 조회
            market = (
                self.db.query(MarketData)
                .filter(MarketData.stock_code == h.stock_code)
                .order_by(desc(MarketData.date))
                .first()
            )
            if not market or not market.close_price:
                continue

            ret = (market.close_price - h.buy_price) / h.buy_price * 100
            total_return += ret

            # 가격부담 알림: RSI > 70 또는 price > MA60 * 1.3
            if market.rsi and market.rsi > 70:
                alerts.append({
                    "type": "price-burden",
                    "title": "가격부담 신호",
                    "description": f"{h.stock_name}: RSI {market.rsi:.0f}",
                })
            elif market.moving_avg_60 and market.close_price > market.moving_avg_60 * 1.3:
                alerts.append({
                    "type": "price-burden",
                    "title": "가격부담 신호",
                    "description": f"{h.stock_name}: 60일선 대비 30%+ 괴리",
                })

            # 변동성 알림: 3일 연속 일일 변동 > 3%
            recent_prices = (
                self.db.query(MarketData)
                .filter(MarketData.stock_code == h.stock_code)
                .order_by(desc(MarketData.date))
                .limit(4)
                .all()
            )
            if len(recent_prices) >= 4:
                consecutive = 0
                for i in range(len(recent_prices) - 1):
                    cur = recent_prices[i].close_price
                    prev = recent_prices[i + 1].close_price
                    if cur and prev and prev > 0:
                        daily_change = abs((cur - prev) / prev * 100)
                        if daily_change > 3:
                            consecutive += 1
                        else:
                            break
                if consecutive >= 3:
                    alerts.append({
                        "type": "volatility",
                        "title": "변동성 경고",
                        "description": f"{h.stock_name}: {consecutive}일 연속 3%+ 변동",
                    })

            # 매도 신호 카운트
            if latest_sentiment and (latest_sentiment.market_heat or 0) > 0.7:
                if (latest_sentiment.overall_score or 0) < 0:
                    sell_signals += 1

        avg_return = total_return / total if total else 0

        return {
            "totalStocks": total,
            "avgReturn": round(avg_return, 1),
            "sellSignals": sell_signals,
            "alerts": alerts[:5],  # 최대 5개
        }

    # ── 4. Company Evaluation ──────────────────────────────
    async def get_company_evaluation(self, stock_code: Optional[str] = None) -> dict:
        query = self.db.query(ResearchReport)
        if stock_code:
            query = query.filter(ResearchReport.stock_code == stock_code)

        reports = query.order_by(desc(ResearchReport.published_at)).limit(10).all()

        # 리포트 기반 평가 점수 계산
        buy_count = sum(1 for r in reports if r.recommendation == "buy")
        hold_count = sum(1 for r in reports if r.recommendation == "hold")
        total = len(reports) or 1

        philosophy_score = min(100, buy_count / total * 100 + 20) if reports else 0
        execution_score = min(100, (buy_count + hold_count) / total * 80) if reports else 0
        competitiveness_score = min(100, buy_count / total * 90) if reports else 0

        # 산업 평가 (리포트 데이터 기반 추정)
        trend_score = min(100, (buy_count / total * 100)) if reports else 50
        moat_score = min(100, philosophy_score * 0.8) if reports else 50
        growth_score = min(100, execution_score * 0.7) if reports else 50

        return {
            "valueProposition": [
                {"checked": philosophy_score >= 60, "label": "차별적 혜택 철학 보유"},
                {"checked": execution_score >= 60, "label": "실질적 실행 증거 확인"},
                {"checked": competitiveness_score >= 60, "label": "경쟁력 상승 지속성"},
            ],
            "industryEvaluation": [
                {"name": "빅트렌드 부합도", "score": round(trend_score, 1), "color": _score_color(trend_score)},
                {"name": "해자 요인", "score": round(moat_score, 1), "color": _score_color(moat_score)},
                {"name": "성장 변수", "score": round(growth_score, 1), "color": _score_color(growth_score)},
            ],
        }

    # ── 5. Flywheel Status ─────────────────────────────────
    async def get_flywheel_status(self) -> dict:
        # 최신 사이클의 step들 조회
        latest_cycle = (
            self.db.query(func.max(FlywheelState.cycle_number)).scalar()
        )

        if not latest_cycle:
            # 데이터 없으면 기본 7단계 반환 (전부 pending)
            return {
                "currentStep": 1,
                "totalSteps": 7,
                "currentPhase": FLYWHEEL_STEPS[0],
                "progress": [
                    {"step": name, "status": "current" if i == 0 else "pending"}
                    for i, name in enumerate(FLYWHEEL_STEPS)
                ],
            }

        steps = (
            self.db.query(FlywheelState)
            .filter(FlywheelState.cycle_number == latest_cycle)
            .order_by(FlywheelState.current_step)
            .all()
        )

        current_step = 1
        current_phase = FLYWHEEL_STEPS[0]
        progress = []

        for s in steps:
            progress.append({"step": s.step_name, "status": s.status})
            if s.status == "current":
                current_step = s.current_step
                current_phase = s.step_name

        # DB에 없는 나머지 step은 pending으로 채움
        existing_names = {s.step_name for s in steps}
        for name in FLYWHEEL_STEPS:
            if name not in existing_names:
                progress.append({"step": name, "status": "pending"})

        return {
            "currentStep": current_step,
            "totalSteps": 7,
            "currentPhase": current_phase,
            "progress": progress,
        }
