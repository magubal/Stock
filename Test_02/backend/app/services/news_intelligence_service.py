"""
News Intelligence Monitor - Service Layer
기사 목록 조회, 내러티브 조회
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from fastapi import HTTPException

from ..models.news_article import NewsArticle, MarketNarrative, SectorPerformance, IndustryPerformance, IndustryStock


class NewsIntelligenceService:
    def __init__(self, db: Session):
        self.db = db

    async def get_articles(
        self,
        category: str = None,
        date: str = None,
        source: str = None,
        limit: int = 50,
    ) -> dict:
        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # fetched_at 기준 필터 (KST/UTC 타임존 차이 대응: 해당일 + 전일 포함)
        date_start = f"{date} 00:00:00"
        date_end = f"{date} 23:59:59"
        prev_date = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

        query = self.db.query(NewsArticle).filter(
            or_(
                NewsArticle.fetched_at.between(date_start, date_end),
                NewsArticle.published_at.between(date_start, date_end),
                # 타임존 차이 대응: 전일 UTC 15:00 이후 = KST 당일
                NewsArticle.fetched_at.between(f"{prev_date} 15:00:00", date_end),
            )
        )
        if category:
            query = query.filter(NewsArticle.category == category)
        if source:
            query = query.filter(NewsArticle.source == source)

        total = query.count()
        articles = (
            query.order_by(desc(NewsArticle.published_at))
            .limit(min(limit, 1000))
            .all()
        )

        return {
            "date": date,
            "total": total,
            "articles": [
                {
                    "id": a.id,
                    "source": a.source,
                    "category": a.category,
                    "title": a.title,
                    "url": a.url,
                    "publisher": a.publisher or "",
                    "published_at": a.published_at.isoformat() if a.published_at else None,
                    "fetched_at": a.fetched_at.isoformat() if a.fetched_at else None,
                }
                for a in articles
            ],
        }

    async def get_industries(
        self,
        sector: str = None,
        date: str = None,
    ) -> dict:
        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # 섹터 퍼포먼스
        sector_q = self.db.query(SectorPerformance).filter_by(date=date)
        sectors = sector_q.order_by(desc(SectorPerformance.change_pct)).all()

        # 인더스트리 퍼포먼스
        ind_q = self.db.query(IndustryPerformance).filter_by(date=date)
        if sector:
            ind_q = ind_q.filter(IndustryPerformance.sector == sector)
        industries = ind_q.order_by(desc(IndustryPerformance.change_pct)).all()

        return {
            "date": date,
            "sectors": [
                {
                    "sector": s.sector,
                    "change_pct": s.change_pct,
                    "market_cap": s.market_cap,
                    "pe_ratio": s.pe_ratio,
                    "volume": s.volume,
                }
                for s in sectors
            ],
            "industries": [
                {
                    "industry": ind.industry,
                    "sector": ind.sector,
                    "change_pct": ind.change_pct,
                    "market_cap": ind.market_cap,
                    "pe_ratio": ind.pe_ratio,
                    "volume": ind.volume,
                }
                for ind in industries
            ],
            "sector_count": len(sectors),
            "industry_count": len(industries),
        }

    async def get_stocks(
        self,
        industry: str = None,
        sector: str = None,
        date: str = None,
    ) -> dict:
        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        query = self.db.query(IndustryStock).filter_by(date=date)
        if industry:
            query = query.filter(IndustryStock.industry == industry)
        elif sector:
            query = query.filter(IndustryStock.sector == sector)

        stocks = query.order_by(desc(IndustryStock.change_pct)).all()

        return {
            "date": date,
            "filter": {"industry": industry, "sector": sector},
            "total": len(stocks),
            "stocks": [
                {
                    "ticker": s.ticker,
                    "company": s.company,
                    "industry": s.industry,
                    "sector": s.sector,
                    "price": s.price,
                    "change_pct": s.change_pct,
                    "perf_week": s.perf_week,
                    "perf_month": s.perf_month,
                    "perf_quarter": s.perf_quarter,
                    "perf_half": s.perf_half,
                    "perf_ytd": s.perf_ytd,
                    "perf_year": s.perf_year,
                    "market_cap": s.market_cap,
                    "pe_ratio": s.pe_ratio,
                    "volume": s.volume,
                }
                for s in stocks
            ],
        }

    async def get_stock_coverage(self, date: str = None) -> dict:
        """종목 수집 진척률: 수집된 인더스트리 수 / 전체 144개."""
        from sqlalchemy import func

        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        collected = (
            self.db.query(func.count(func.distinct(IndustryStock.industry)))
            .filter_by(date=date)
            .scalar()
        ) or 0

        total_stocks = (
            self.db.query(func.count(IndustryStock.id))
            .filter_by(date=date)
            .scalar()
        ) or 0

        total_industries = 144  # Finviz 전체 인더스트리 수
        pct = round(collected / total_industries * 100, 1) if total_industries > 0 else 0

        return {
            "date": date,
            "collected_industries": collected,
            "total_industries": total_industries,
            "total_stocks": total_stocks,
            "coverage_pct": pct,
        }

    async def get_narrative(self, date: str = None) -> dict:
        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        row = self.db.query(MarketNarrative).filter_by(date=date).first()
        if not row:
            raise HTTPException(
                status_code=404,
                detail={
                    "detail": "해당 날짜의 분석 결과가 없습니다",
                    "error_code": "NARRATIVE_NOT_FOUND",
                },
            )

        index_data = getattr(row, 'index_data', None) or {}
        model_used = getattr(row, 'model_used', None) or row.generated_by or ""

        return {
            "date": row.date,
            "key_issues": row.key_issues or [],
            "narrative": row.narrative or "",
            "sector_impact": row.sector_impact or [],
            "sentiment": {
                "score": row.sentiment_score or 0.0,
                "label": row.sentiment_label or "neutral",
            },
            "index_data": index_data,
            "article_count": row.article_count or 0,
            "generated_by": row.generated_by or "",
            "model_used": model_used,
        }
