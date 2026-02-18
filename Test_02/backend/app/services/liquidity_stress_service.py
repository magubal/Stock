"""
Liquidity & Credit Stress Monitor Service
- 종합 스트레스 인덱스 조회
- 히스토리 조회
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional

from ..models import (
    LiquidityMacro, LiquidityPrice, LiquidityNews,
    FedTone, StressIndex,
)

LEVEL_MAP = {
    "normal":  {"label": "안정", "color": "#22c55e"},
    "watch":   {"label": "관심", "color": "#eab308"},
    "caution": {"label": "주의", "color": "#f97316"},
    "stress":  {"label": "경계", "color": "#ef4444"},
    "crisis":  {"label": "위기", "color": "#dc2626"},
}


class LiquidityStressService:
    def __init__(self, db: Session):
        self.db = db

    async def get_latest_stress(self) -> dict:
        """최신 스트레스 데이터 반환"""
        si = (
            self.db.query(StressIndex)
            .order_by(desc(StressIndex.date))
            .first()
        )
        if not si:
            return self._empty_response()

        macro = self.db.query(LiquidityMacro).filter_by(date=si.date).first()
        if not macro:
            # FRED 데이터는 당일 미발행 가능 → 가장 최근 macro로 fallback
            macro = (
                self.db.query(LiquidityMacro)
                .filter(LiquidityMacro.date <= si.date)
                .order_by(desc(LiquidityMacro.date))
                .first()
            )
        vix_row = (
            self.db.query(LiquidityPrice)
            .filter_by(date=si.date, symbol="^VIX")
            .first()
        )
        tlt_row = (
            self.db.query(LiquidityPrice)
            .filter_by(date=si.date, symbol="TLT")
            .first()
        )

        # VIX 전일 대비 변화
        vix_prev = (
            self.db.query(LiquidityPrice)
            .filter(LiquidityPrice.symbol == "^VIX", LiquidityPrice.date < si.date)
            .order_by(desc(LiquidityPrice.date))
            .first()
        )
        vix_val = vix_row.close if vix_row else None
        vix_change = None
        if vix_val and vix_prev and vix_prev.close:
            vix_change = round(((vix_val - vix_prev.close) / vix_prev.close) * 100, 1)

        # 전일 macro (변화량 계산용)
        prev_macro = None
        if macro:
            prev_macro = (
                self.db.query(LiquidityMacro)
                .filter(LiquidityMacro.date < macro.date)
                .order_by(desc(LiquidityMacro.date))
                .first()
            )

        # 전일 TLT
        tlt_prev = (
            self.db.query(LiquidityPrice)
            .filter(LiquidityPrice.symbol == "TLT", LiquidityPrice.date < si.date)
            .order_by(desc(LiquidityPrice.date))
            .first()
        )

        # 뉴스 집계
        news_rows = self.db.query(LiquidityNews).filter_by(date=si.date).all()
        total_news = sum(n.count for n in news_rows)
        top_kw = max(news_rows, key=lambda n: n.count).keyword if news_rows else None

        # 전일 뉴스
        prev_si = (
            self.db.query(StressIndex)
            .filter(StressIndex.date < si.date)
            .order_by(desc(StressIndex.date))
            .first()
        )
        prev_news_count = None
        if prev_si:
            prev_news_rows = self.db.query(LiquidityNews).filter_by(date=prev_si.date).all()
            prev_news_count = sum(n.count for n in prev_news_rows) if prev_news_rows else None

        # Fed 톤
        fed = self.db.query(FedTone).filter_by(date=si.date).first()
        prev_fed = None
        if prev_si:
            prev_fed = self.db.query(FedTone).filter_by(date=prev_si.date).first()

        level_info = LEVEL_MAP.get(si.level, LEVEL_MAP["normal"])

        def _chg(cur, prev):
            """절대 변화량 계산"""
            if cur is None or prev is None:
                return None
            return round(cur - prev, 4)

        def _pct_chg(cur, prev):
            """퍼센트 변화율 계산"""
            if cur is None or prev is None or prev == 0:
                return None
            return round(((cur - prev) / abs(prev)) * 100, 1)

        return {
            "date": si.date,
            "totalScore": round(si.total_score, 3) if si.total_score else 0,
            "level": si.level or "normal",
            "levelLabel": level_info["label"],
            "levelColor": level_info["color"],
            "modules": {
                "volatility": {
                    "score": round(si.vol_score or 0, 3),
                    "vix": vix_val,
                    "vixChange": vix_change,
                    "prevScore": round(prev_si.vol_score or 0, 3) if prev_si else None,
                },
                "credit": {
                    "score": round(si.credit_score or 0, 3),
                    "hyOas": macro.hy_oas if macro else None,
                    "igOas": macro.ig_oas if macro else None,
                    "hyOasChg": _chg(macro.hy_oas if macro else None, prev_macro.hy_oas if prev_macro else None),
                    "igOasChg": _chg(macro.ig_oas if macro else None, prev_macro.ig_oas if prev_macro else None),
                    "prevScore": round(prev_si.credit_score or 0, 3) if prev_si else None,
                },
                "funding": {
                    "score": round(si.funding_score or 0, 3),
                    "sofr": macro.sofr if macro else None,
                    "rrpBalance": macro.rrp_balance if macro else None,
                    "sofrChg": _chg(macro.sofr if macro else None, prev_macro.sofr if prev_macro else None),
                    "rrpChg": _chg(macro.rrp_balance if macro else None, prev_macro.rrp_balance if prev_macro else None),
                    "prevScore": round(prev_si.funding_score or 0, 3) if prev_si else None,
                },
                "treasury": {
                    "score": round(si.treasury_score or 0, 3),
                    "dgs10": macro.dgs10 if macro else None,
                    "tltClose": tlt_row.close if tlt_row else None,
                    "dgs10Chg": _chg(macro.dgs10 if macro else None, prev_macro.dgs10 if prev_macro else None),
                    "tltChg": _pct_chg(tlt_row.close if tlt_row else None, tlt_prev.close if tlt_prev else None),
                    "prevScore": round(prev_si.treasury_score or 0, 3) if prev_si else None,
                },
                "news": {
                    "score": round(si.news_score or 0, 3),
                    "totalCount": total_news,
                    "topKeyword": top_kw,
                    "countChg": _chg(total_news, prev_news_count),
                    "prevScore": round(prev_si.news_score or 0, 3) if prev_si else None,
                },
                "fedTone": {
                    "score": round(si.fed_tone_score or 0, 3),
                    "liquidityFocus": fed.liquidity_score if fed else 0,
                    "stabilityFocus": fed.stability_score if fed else 0,
                    "liqChg": _chg(fed.liquidity_score if fed else None, prev_fed.liquidity_score if prev_fed else None),
                    "stabChg": _chg(fed.stability_score if fed else None, prev_fed.stability_score if prev_fed else None),
                    "prevScore": round(prev_si.fed_tone_score or 0, 3) if prev_si else None,
                },
            },
            "macro": {
                "dgs2": macro.dgs2 if macro else None,
                "dgs10": macro.dgs10 if macro else None,
                "dgs30": macro.dgs30 if macro else None,
                "hyOas": macro.hy_oas if macro else None,
                "igOas": macro.ig_oas if macro else None,
                "sofr": macro.sofr if macro else None,
                "dgs2Chg": _chg(macro.dgs2 if macro else None, prev_macro.dgs2 if prev_macro else None),
                "dgs10Chg": _chg(macro.dgs10 if macro else None, prev_macro.dgs10 if prev_macro else None),
                "dgs30Chg": _chg(macro.dgs30 if macro else None, prev_macro.dgs30 if prev_macro else None),
            },
        }

    async def get_stress_history(self, days: int = 30) -> dict:
        """스트레스 히스토리 반환 (원시 데이터 포함)"""
        rows = (
            self.db.query(StressIndex)
            .order_by(desc(StressIndex.date))
            .limit(days)
            .all()
        )
        if not rows:
            return {"history": []}

        dates = [si.date for si in rows]

        # Batch query macro data
        macro_rows = self.db.query(LiquidityMacro).filter(
            LiquidityMacro.date.in_(dates)
        ).all()
        macro_map = {m.date: m for m in macro_rows}

        # Batch query price data (VIX, TLT)
        price_rows = self.db.query(LiquidityPrice).filter(
            LiquidityPrice.date.in_(dates),
            LiquidityPrice.symbol.in_(["^VIX", "TLT"])
        ).all()
        price_map = {}
        for p in price_rows:
            price_map.setdefault(p.date, {})[p.symbol] = p

        # Batch query news counts
        news_agg = self.db.query(
            LiquidityNews.date,
            func.sum(LiquidityNews.count).label('total')
        ).filter(
            LiquidityNews.date.in_(dates)
        ).group_by(LiquidityNews.date).all()
        news_map = {n.date: n.total for n in news_agg}

        # Batch query fed tone
        fed_rows = self.db.query(FedTone).filter(
            FedTone.date.in_(dates)
        ).all()
        fed_map = {f.date: f for f in fed_rows}

        history = []
        for si in reversed(rows):
            level_info = LEVEL_MAP.get(si.level, LEVEL_MAP["normal"])
            macro = macro_map.get(si.date)
            prices = price_map.get(si.date, {})
            vix_row = prices.get("^VIX")
            tlt_row = prices.get("TLT")
            fed = fed_map.get(si.date)

            history.append({
                "date": si.date,
                "totalScore": round(si.total_score or 0, 3),
                "level": si.level or "normal",
                "levelLabel": level_info["label"],
                "levelColor": level_info["color"],
                "volScore": round(si.vol_score or 0, 3),
                "creditScore": round(si.credit_score or 0, 3),
                "fundingScore": round(si.funding_score or 0, 3),
                "treasuryScore": round(si.treasury_score or 0, 3),
                "newsScore": round(si.news_score or 0, 3),
                "fedToneScore": round(si.fed_tone_score or 0, 3),
                # Raw values for chart switching
                "vix": vix_row.close if vix_row else None,
                "hyOas": macro.hy_oas if macro else None,
                "igOas": macro.ig_oas if macro else None,
                "sofr": macro.sofr if macro else None,
                "rrpBalance": macro.rrp_balance if macro else None,
                "dgs10": macro.dgs10 if macro else None,
                "dgs2": macro.dgs2 if macro else None,
                "dgs30": macro.dgs30 if macro else None,
                "tltClose": tlt_row.close if tlt_row else None,
                "newsCount": news_map.get(si.date, 0),
                "fedLiquidity": fed.liquidity_score if fed else None,
                "fedStability": fed.stability_score if fed else None,
            })
        return {"history": history}

    def _empty_response(self) -> dict:
        return {
            "date": None,
            "totalScore": 0,
            "level": "normal",
            "levelLabel": "안정",
            "levelColor": "#22c55e",
            "modules": {
                "volatility": {"score": 0, "vix": None, "vixChange": None},
                "credit": {"score": 0, "hyOas": None, "igOas": None},
                "funding": {"score": 0, "sofr": None, "rrpBalance": None},
                "treasury": {"score": 0, "dgs10": None, "tltClose": None},
                "news": {"score": 0, "totalCount": 0, "topKeyword": None},
                "fedTone": {"score": 0, "liquidityFocus": 0, "stabilityFocus": 0},
            },
            "macro": {},
        }
