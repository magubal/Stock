from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class DailyWorkBase(BaseModel):
    date: date
    category: str
    description: Optional[str] = None
    content: str
    source_link: Optional[str] = None
    source_type: Optional[str] = "excel"


class DailyWorkCreate(DailyWorkBase):
    pass


class DailyWork(DailyWorkBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DailyWorkStats(BaseModel):
    category: str
    count: int
