"""
News Intelligence Monitor - DB Models
- NewsArticle: 뉴스 기사 (multi-source 확장 가능)
- MarketNarrative: AI 분석 결과 (날짜별 유니크)
- SectorPerformance: 섹터별 일간 퍼포먼스
- IndustryPerformance: 인더스트리별 일간 퍼포먼스 (섹터 매핑)
- IndustryStock: 인더스트리별 개별 종목 퍼포먼스
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON, UniqueConstraint
from sqlalchemy.sql import func
from ..database import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(500), nullable=False)
    publisher = Column(String(100))
    published_at = Column(DateTime(timezone=True), index=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    summary = Column(Text)

    __table_args__ = (
        UniqueConstraint('source', 'url', name='uq_news_source_url'),
    )


class MarketNarrative(Base):
    __tablename__ = "market_narratives"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), unique=True, nullable=False, index=True)
    key_issues = Column(JSON)
    narrative = Column(Text)
    sector_impact = Column(JSON)
    sentiment_score = Column(Float)
    sentiment_label = Column(String(20))
    article_count = Column(Integer)
    index_data = Column(JSON)  # DOW/NASDAQ/S&P500 intraday snapshots
    generated_by = Column(String(50))
    model_used = Column(String(50))  # AI model used for analysis
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SectorPerformance(Base):
    __tablename__ = "sector_performances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False, index=True)
    sector = Column(String(50), nullable=False, index=True)
    change_pct = Column(Float)
    market_cap = Column(String(20))       # e.g. "12.5T"
    pe_ratio = Column(Float)
    volume = Column(String(20))
    source = Column(String(20), default="finviz")
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('date', 'sector', name='uq_sector_date'),
    )


class IndustryPerformance(Base):
    __tablename__ = "industry_performances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False, index=True)
    industry = Column(String(100), nullable=False, index=True)
    sector = Column(String(50), nullable=False, index=True)  # 섹터 매핑
    change_pct = Column(Float)
    market_cap = Column(String(20))
    pe_ratio = Column(Float)
    volume = Column(String(20))
    source = Column(String(20), default="finviz")
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('date', 'industry', name='uq_industry_date'),
    )


class IndustryStock(Base):
    __tablename__ = "industry_stocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False, index=True)
    industry = Column(String(100), nullable=False, index=True)
    sector = Column(String(50), nullable=False, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    company = Column(String(200))
    price = Column(Float)
    change_pct = Column(Float)                  # 당일 변화율
    perf_week = Column(Float)
    perf_month = Column(Float)
    perf_quarter = Column(Float)
    perf_half = Column(Float)
    perf_ytd = Column(Float)
    perf_year = Column(Float)                   # 1년 퍼포먼스 (추세 방향성)
    market_cap = Column(String(20))
    pe_ratio = Column(Float)
    volume = Column(String(20))
    source = Column(String(20), default="finviz")
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('date', 'ticker', name='uq_stock_date_ticker'),
    )
