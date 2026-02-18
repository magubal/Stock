from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from ..database import Base


class MonitoringIncident(Base):
    __tablename__ = "monitoring_incidents"

    id = Column(Integer, primary_key=True, index=True)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    source_path = Column(String(200), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(120), nullable=False, index=True)
    rule_code = Column(String(80), nullable=False, index=True)
    severity = Column(String(20), nullable=False, default="high")
    status = Column(String(40), nullable=False, default="blocked_pending_codex", index=True)
    payload_json = Column(Text, nullable=False, default="{}")
    requires_reconfirm = Column(Boolean, nullable=False, default=True)
    approver = Column(String(40), nullable=False, default="codex")


class MonitoringDecision(Base):
    __tablename__ = "monitoring_decisions"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("monitoring_incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    decider = Column(String(40), nullable=False, default="codex")
    decision = Column(String(20), nullable=False, index=True)  # approve/reject/resolve
    note = Column(Text)
    decided_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MonitoringEvent(Base):
    __tablename__ = "monitoring_events"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("monitoring_incidents.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(30), nullable=False, index=True)  # pass/block/retry
    source_path = Column(String(200), nullable=False, index=True)
    entity_id = Column(String(120), nullable=False, index=True)
    message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
