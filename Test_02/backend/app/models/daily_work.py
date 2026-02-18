from sqlalchemy import Column, Integer, String, DateTime, Text, Date, UniqueConstraint
from sqlalchemy.sql import func
from ..database import Base


class DailyWork(Base):
    """일일 작업 원본 데이터"""
    __tablename__ = "daily_work"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # SECTOR, US_MARKET, THEME, RISK, NEXT_DAY, PORTFOLIO, AI_RESEARCH
    description = Column(Text)
    content = Column(Text, nullable=False)
    source_link = Column(String(500))
    source_type = Column(String(50), default="excel")  # excel, csv, text, manual
    content_hash = Column(String(64), index=True)  # SHA-256 of content for dedup
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("date", "category", "content_hash", name="uq_daily_work_date_cat_hash"),
    )

    def __repr__(self):
        return f"<DailyWork(id={self.id}, date={self.date}, category='{self.category}')>"
