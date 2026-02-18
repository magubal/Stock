from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from ..database import Base


class IdeaEvidence(Base):
    """아이디어 ↔ 인사이트 연결"""
    __tablename__ = "idea_evidence"

    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False, index=True)
    insight_id = Column(Integer, ForeignKey("insights.id", ondelete="CASCADE"), nullable=False, index=True)
    relation_type = Column(String(20), default="supports")  # supports, primary, reference

    __table_args__ = (
        UniqueConstraint("idea_id", "insight_id", name="uq_idea_insight"),
    )
