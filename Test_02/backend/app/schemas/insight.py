from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class InsightBase(BaseModel):
    work_id: Optional[int] = None
    type: str  # claim, prediction, pattern
    text: str
    confidence: Optional[float] = 0.5
    keywords: Optional[List[str]] = []
    source_ai: Optional[str] = None


class InsightCreate(InsightBase):
    pass


class Insight(InsightBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class InsightExtractRequest(BaseModel):
    work_id: int
