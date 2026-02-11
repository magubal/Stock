from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

# 데이터 소스 테이블
class DataSource(Base):
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # news, report, telegram, blog
    url = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    news_items = relationship("News", back_populates="source")

# 뉴스/기사 테이블
class News(Base):
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("data_sources.id"))
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(500), unique=True, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=False)
    author = Column(String(100))
    
    # 분석 관련 필드
    sentiment_score = Column(Float)  # -1(부정) ~ 1(긍정)
    importance_score = Column(Float)  # 0 ~ 1
    stock_mentions = Column(Text)  # 언급된 종목 코드 (JSON 형식)
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계
    source = relationship("DataSource", back_populates="news_items")

# 증권사 리포트 테이블
class ResearchReport(Base):
    __tablename__ = "research_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    pdf_url = Column(String(500))
    brokerage = Column(String(100), nullable=False)
    author = Column(String(100))
    target_price = Column(Float)
    recommendation = Column(String(50))  # buy, hold, sell
    published_at = Column(DateTime(timezone=True), nullable=False)
    
    # 종목 관련
    stock_code = Column(String(10))
    stock_name = Column(String(100))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# 텔레그램 메시지 테이블
class TelegramMessage(Base):
    __tablename__ = "telegram_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_name = Column(String(100), nullable=False)
    message_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(100))
    views = Column(Integer)
    posted_at = Column(DateTime(timezone=True), nullable=False)
    
    # 분석 관련
    sentiment_score = Column(Float)
    stock_mentions = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# 투자자 심리 지표 테이블
class InvestorSentiment(Base):
    __tablename__ = "investor_sentiment"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), nullable=False)
    overall_score = Column(Float, nullable=False)  # 전체 심리 지수
    market_heat = Column(Float)  # 시장 과열도
    fear_greed_index = Column(Float)  # 공포/탐욕 지수
    
    # 투자자 유형별 심리
    short_term_sentiment = Column(Float)  # 단기 투자자
    long_term_sentiment = Column(Float)   # 중장기 투자자
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# 시장 데이터 테이블
class MarketData(Base):
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), nullable=False)
    stock_name = Column(String(100), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    
    # 가격 정보
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)
    
    # 기술적 지표
    moving_avg_5 = Column(Float)
    moving_avg_20 = Column(Float)
    moving_avg_60 = Column(Float)
    rsi = Column(Float)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

# 포트폴리오 보유 종목 테이블
class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"

    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), nullable=False)
    stock_name = Column(String(100), nullable=False)
    buy_price = Column(Float, nullable=False)
    buy_date = Column(DateTime(timezone=True), nullable=False)
    quantity = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# 플라이휠 상태 테이블
class FlywheelState(Base):
    __tablename__ = "flywheel_state"

    id = Column(Integer, primary_key=True, index=True)
    cycle_number = Column(Integer, nullable=False, default=1)
    current_step = Column(Integer, nullable=False, default=1)
    step_name = Column(String(100), nullable=False)
    status = Column(String(20), default="pending")  # pending, current, completed
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())