"""
Market Daily Digest - DB Model
시장 종합정리: 7개 모니터링 모듈 요약 + AI 총평 저장
"""
from sqlalchemy import Column, String, DateTime, Text, JSON, Float
from sqlalchemy.sql import func
from ..database import Base


class DailyDigest(Base):
    __tablename__ = "daily_digests"

    date = Column(String(10), primary_key=True, index=True)       # "2026-02-20"
    module_summaries = Column(JSON, nullable=True)                  # 7개 모듈 요약 스냅샷
    mindmap_data = Column(JSON, nullable=True)                      # 마인드맵 노드/링크 구조
    ai_summary = Column(Text, nullable=True)                        # AI 생성 총평
    user_summary = Column(Text, nullable=True)                      # 사용자 수정/추가 총평
    ai_model = Column(String(50), nullable=True)                    # 사용된 AI 모델명
    sentiment_score = Column(Float, nullable=True)                  # 시장 심리 점수 (-1.0~1.0)
    sentiment_label = Column(String(20), nullable=True)             # "Bullish"/"Bearish"/"Neutral"
    source = Column(String(20), default="REAL")                     # "DEMO" or "REAL"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
