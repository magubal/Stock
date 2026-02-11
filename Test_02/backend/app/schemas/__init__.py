from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enums
class DataSourceType(str, Enum):
    NEWS = "news"
    REPORT = "report"
    TELEGRAM = "telegram"
    BLOG = "blog"

class Recommendation(str, Enum):
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"

# Data Source Schemas
class DataSourceBase(BaseModel):
    name: str = Field(..., max_length=100)
    type: DataSourceType
    url: str = Field(..., max_length=500)
    is_active: bool = True

class DataSourceCreate(DataSourceBase):
    pass

class DataSource(DataSourceBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# News Schemas
class NewsBase(BaseModel):
    title: str = Field(..., max_length=500)
    content: str
    url: str = Field(..., max_length=500)
    published_at: datetime
    author: Optional[str] = Field(None, max_length=100)

class NewsCreate(NewsBase):
    source_id: int

class News(NewsBase):
    id: int
    source_id: int
    sentiment_score: Optional[float] = None
    importance_score: Optional[float] = None
    stock_mentions: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Research Report Schemas
class ResearchReportBase(BaseModel):
    title: str = Field(..., max_length=500)
    content: str
    pdf_url: Optional[str] = Field(None, max_length=500)
    brokerage: str = Field(..., max_length=100)
    author: Optional[str] = Field(None, max_length=100)
    target_price: Optional[float] = None
    recommendation: Optional[Recommendation] = None
    published_at: datetime
    stock_code: Optional[str] = Field(None, max_length=10)
    stock_name: Optional[str] = Field(None, max_length=100)

class ResearchReportCreate(ResearchReportBase):
    pass

class ResearchReport(ResearchReportBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Telegram Message Schemas
class TelegramMessageBase(BaseModel):
    channel_name: str = Field(..., max_length=100)
    message_id: int
    content: str
    author: Optional[str] = Field(None, max_length=100)
    views: Optional[int] = None
    posted_at: datetime

class TelegramMessageCreate(TelegramMessageBase):
    pass

class TelegramMessage(TelegramMessageBase):
    id: int
    sentiment_score: Optional[float] = None
    stock_mentions: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Investor Sentiment Schemas
class InvestorSentimentBase(BaseModel):
    date: datetime
    overall_score: float
    market_heat: Optional[float] = None
    fear_greed_index: Optional[float] = None
    short_term_sentiment: Optional[float] = None
    long_term_sentiment: Optional[float] = None

class InvestorSentimentCreate(InvestorSentimentBase):
    pass

class InvestorSentiment(InvestorSentimentBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Market Data Schemas
class MarketDataBase(BaseModel):
    stock_code: str = Field(..., max_length=10)
    stock_name: str = Field(..., max_length=100)
    date: datetime
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    close_price: Optional[float] = None
    volume: Optional[int] = None
    moving_avg_5: Optional[float] = None
    moving_avg_20: Optional[float] = None
    moving_avg_60: Optional[float] = None
    rsi: Optional[float] = None

class MarketDataCreate(MarketDataBase):
    pass

class MarketData(MarketDataBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Response Schemas
class DashboardSummary(BaseModel):
    total_news: int
    total_reports: int
    total_telegram_messages: int
    latest_sentiment: Optional[InvestorSentiment] = None
    market_overview: Optional[List[MarketData]] = None

class AnalysisResult(BaseModel):
    news_id: int
    sentiment_score: float
    importance_score: float
    stock_mentions: List[str]
    key_points: List[str]

# ── Dashboard Response Schemas ──

class InvestorTypeInfo(BaseModel):
    type: str
    sentiment: str
    label: str

class PsychologyResponse(BaseModel):
    marketHeat: float
    empathy: float
    expectation: float
    investorTypes: List[InvestorTypeInfo]

class TimingItem(BaseModel):
    period: str
    signal: str  # good, caution, danger
    label: str
    reason: str

class PortfolioAlert(BaseModel):
    type: str
    title: str
    description: str

class PortfolioResponse(BaseModel):
    totalStocks: int
    avgReturn: float
    sellSignals: int
    alerts: List[PortfolioAlert]

class ValuePropositionItem(BaseModel):
    checked: bool
    label: str

class IndustryEvaluationItem(BaseModel):
    name: str
    score: float
    color: str  # positive, warning, danger

class EvaluationResponse(BaseModel):
    valueProposition: List[ValuePropositionItem]
    industryEvaluation: List[IndustryEvaluationItem]

class FlywheelStep(BaseModel):
    step: str
    status: str  # completed, current, pending

class FlywheelResponse(BaseModel):
    currentStep: int
    totalSteps: int
    currentPhase: str
    progress: List[FlywheelStep]

# Portfolio Holding Schemas
class PortfolioHoldingBase(BaseModel):
    stock_code: str = Field(..., max_length=10)
    stock_name: str = Field(..., max_length=100)
    buy_price: float
    buy_date: datetime
    quantity: int
    is_active: bool = True

class PortfolioHoldingCreate(PortfolioHoldingBase):
    pass

class PortfolioHolding(PortfolioHoldingBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Flywheel State Schemas
class FlywheelStateBase(BaseModel):
    cycle_number: int = 1
    current_step: int = 1
    step_name: str = Field(..., max_length=100)
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

class FlywheelStateCreate(FlywheelStateBase):
    pass

class FlywheelState(FlywheelStateBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True