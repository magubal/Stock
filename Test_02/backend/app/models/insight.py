from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.sql import func
from ..database import Base


class Insight(Base):
    """추출된 인사이트"""
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, index=True)
    work_id = Column(Integer, ForeignKey("daily_work.id", ondelete="SET NULL"), nullable=True, index=True)
    type = Column(String(20), nullable=False)  # claim, prediction, pattern
    text = Column(Text, nullable=False)
    confidence = Column(Float, default=0.5)  # 0.0 ~ 1.0
    keywords = Column(Text, default="[]")  # JSON array stored as TEXT
    source_ai = Column(String(20))  # claude, gemini, chatgpt, manual
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Insight(id={self.id}, type='{self.type}', confidence={self.confidence})>"
