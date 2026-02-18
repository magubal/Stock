from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class MonitoringIncidentResponse(BaseModel):
    id: int
    occurred_at: datetime
    source_path: str
    entity_type: str
    entity_id: str
    rule_code: str
    severity: str
    status: str
    payload_json: str
    requires_reconfirm: bool
    approver: str

    class Config:
        from_attributes = True


class MonitoringEventResponse(BaseModel):
    id: int
    incident_id: Optional[int] = None
    event_type: str
    source_path: str
    entity_id: str
    message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MonitoringDecisionRequest(BaseModel):
    note: Optional[str] = None
    decider: str = "codex"


class MonitoringDecisionResponse(BaseModel):
    id: int
    incident_id: int
    decider: str
    decision: str
    note: Optional[str] = None
    decided_at: datetime

    class Config:
        from_attributes = True


class MonitoringBlockDetail(BaseModel):
    blocked: bool = True
    incident_id: int
    rule_code: str
    reasons: List[str]
    reconfirm_required: bool = True
    approver: str = "codex"
