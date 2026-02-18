from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Idea(Base):
    __tablename__ = "ideas"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)  # 아이디어 제목
    content = Column(Text, nullable=False)       # 아이디어 상세 내용
    source = Column(String(100), default="Manual") # 소스 (DailyWork_Excel, Chat_Claude 등)

    # 카테고리 및 투자 가설
    category = Column(String(50), nullable=True, index=True)  # SECTOR, US_MARKET, THEME, RISK, NEXT_DAY, PORTFOLIO, AI_RESEARCH, CROSS
    thesis = Column(Text, nullable=True)         # 투자 가설

    # 상태 관리
    status = Column(String(50), default="draft")  # draft, active, testing, validated, invalidated, archived
    priority = Column(Integer, default=3)          # 1(P1-즉시) ~ 5(P5-참고)
    
    # 메타데이터
    tags = Column(JSON, default=list)            # 태그 리스트 (예: ["risk", "system"])
    author = Column(String(100), nullable=True)  # 작성자/제안자
    
    # Action Item 연결 (선택적)
    action_item_id = Column(String(100), nullable=True) # REQ-XXX 등과 연결
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Idea(id={self.id}, title='{self.title}', status='{self.status}')>"
