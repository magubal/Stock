from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, Index
from sqlalchemy.sql import func
from ..database import Base


class Signal(Base):
    """투자 시그널 — Cross-Data Signal Engine이 생성"""
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_id = Column(String(50), nullable=False, unique=True)  # SIG-CASH-UP-20260215-001
    rule_id = Column(String(50), nullable=False)                  # SIG-CASH-UP
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False, index=True)     # RISK, SECTOR, PORTFOLIO, THEME
    signal_type = Column(String(20), default="cross")             # cross, single, ai
    confidence = Column(Float, default=0.5)                       # 0.0 ~ 1.0
    data_sources = Column(Text, default="[]")                     # JSON array of module names
    evidence = Column(Text, default="[]")                         # JSON array of evidence items
    suggested_action = Column(Text)
    ai_interpretation = Column(Text)                              # AI 전략가 해석 (Phase 2)
    data_gaps = Column(Text, default="[]")                        # JSON array of gap items
    status = Column(String(20), default="new", index=True)        # new, reviewed, accepted, rejected, expired
    related_idea_id = Column(Integer, ForeignKey("ideas.id", ondelete="SET NULL"), nullable=True)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    reviewed_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<Signal(signal_id='{self.signal_id}', title='{self.title}', confidence={self.confidence})>"
