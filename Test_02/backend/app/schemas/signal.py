from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class SignalStatus(str, Enum):
    NEW = "new"
    REVIEWED = "reviewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class SignalCategory(str, Enum):
    RISK = "RISK"
    SECTOR = "SECTOR"
    PORTFOLIO = "PORTFOLIO"
    THEME = "THEME"


class EvidenceItem(BaseModel):
    module: str
    field: str
    value: Optional[object] = None
    label: str
    timestamp: Optional[str] = None


class GapItem(BaseModel):
    module: str
    reason: str
    impact: Optional[str] = None
    staleness_hours: Optional[float] = None


class SignalGenerateRequest(BaseModel):
    days: int = 3


class SignalStatusUpdate(BaseModel):
    status: SignalStatus


class SignalResponse(BaseModel):
    id: int
    signal_id: str
    rule_id: str
    title: str
    description: Optional[str] = None
    category: str
    signal_type: str = "cross"
    confidence: float
    data_sources: List[str] = []
    evidence: List[dict] = []
    suggested_action: Optional[str] = None
    ai_interpretation: Optional[str] = None
    data_gaps: List[dict] = []
    status: str = "new"
    related_idea_id: Optional[int] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SignalListResponse(BaseModel):
    total: int
    signals: List[SignalResponse]


class SignalGenerateResponse(BaseModel):
    generated_at: str
    signals_count: int
    signals: List[SignalResponse]


class SignalAcceptResponse(BaseModel):
    signal_id: str
    status: str
    idea: dict
