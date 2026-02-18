from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from ..database import Base


class CollabPacket(Base):
    """AI 협업 Context Packet"""
    __tablename__ = "collab_packets"

    id = Column(Integer, primary_key=True, index=True)
    packet_id = Column(String(36), nullable=False, unique=True, index=True)  # UUID
    source_ai = Column(String(20), nullable=False)  # claude, gemini, chatgpt
    topic = Column(String(200), nullable=False)
    category = Column(String(50))
    content_json = Column(Text, nullable=False)  # Full Context Packet JSON
    request_action = Column(String(20))  # validate, extend, challenge, synthesize
    request_ask = Column(Text)
    status = Column(String(20), default="pending")  # pending, reviewed, synthesized
    related_idea_id = Column(Integer, ForeignKey("ideas.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<CollabPacket(id={self.id}, source='{self.source_ai}', topic='{self.topic}')>"


class CollabSession(Base):
    """AI 세션 레지스트리"""
    __tablename__ = "collab_sessions"

    id = Column(Integer, primary_key=True, index=True)
    ai_type = Column(String(20), nullable=False)  # claude, gemini, chatgpt
    session_link = Column(String(500))
    assigned_task = Column(Text)
    status = Column(String(20), default="active")  # active, completed, abandoned
    last_exchange_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CollabPacketHistory(Base):
    """Packet lifecycle history for audit and analytics."""
    __tablename__ = "collab_packet_history"

    id = Column(Integer, primary_key=True, index=True)
    packet_id = Column(String(36), ForeignKey("collab_packets.packet_id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(30), nullable=False)  # created, status_updated, triaged
    action = Column(String(30))
    packet_type = Column(String(50))
    assignee_ai = Column(String(100))
    due_at = Column(DateTime(timezone=True))
    note = Column(Text)
    work_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    created_at = Column(DateTime(timezone=True), server_default=func.now())
