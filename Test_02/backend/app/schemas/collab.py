from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


class CollabPacketBase(BaseModel):
    packet_id: str
    source_ai: str
    topic: str
    category: Optional[str] = None
    content_json: str
    request_action: Optional[str] = None
    request_ask: Optional[str] = None
    related_idea_id: Optional[int] = None


class CollabPacketCreate(CollabPacketBase):
    packet_type: Optional[str] = None


class CollabPacket(CollabPacketBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CollabPacketStatusUpdate(BaseModel):
    status: str  # pending, reviewed, synthesized


class CollabAction(str, Enum):
    VALIDATE = "validate"
    EXTEND = "extend"
    CHALLENGE = "challenge"
    INFER = "infer"
    SYNTHESIZE = "synthesize"


class CollabPacketTriageRequest(BaseModel):
    action: CollabAction
    packet_type: Optional[str] = None
    assignee_ai: Optional[str] = None
    due_at: Optional[datetime] = None
    note: Optional[str] = None
    result_summary: Optional[str] = None
    result_evidence: Optional[str] = None
    result_risks: Optional[str] = None
    result_next_step: Optional[str] = None
    result_confidence: Optional[int] = Field(default=None, ge=0, le=100)
    result_industry_outlook: Optional[str] = None
    result_consensus_revenue: Optional[float] = None
    result_consensus_op_income: Optional[float] = None
    result_consensus_unit: Optional[str] = None
    result_scenario_bear: Optional[str] = None
    result_scenario_base: Optional[str] = None
    result_scenario_bull: Optional[str] = None
    result_final_comment: Optional[str] = None
    run_stock_pipeline: bool = False
    stock_ticker: Optional[str] = None
    stock_name: Optional[str] = None
    stock_year: Optional[str] = "auto"
    create_idea: bool = True
    force_create_idea: bool = False
    idea_priority: int = Field(default=3, ge=1, le=5)
    idea_status: Optional[str] = None


class CollabIdeaSummary(BaseModel):
    id: int
    title: str
    status: str
    category: Optional[str] = None
    priority: int


class CollabIdeaGate(BaseModel):
    should_create: bool
    reasons: List[str] = []


class CollabPacketTriageResponse(BaseModel):
    packet: CollabPacket
    idea: Optional[CollabIdeaSummary] = None
    idea_gate: Optional[CollabIdeaGate] = None


class CollabInboxItem(BaseModel):
    packet_id: str
    source_ai: str
    topic: str
    category: Optional[str] = None
    packet_type: Optional[str] = None
    work_date: Optional[str] = None
    status: str
    request_action: Optional[str] = None
    request_ask: Optional[str] = None
    related_idea_id: Optional[int] = None
    created_at: datetime
    assignee_ai: Optional[str] = None
    due_at: Optional[datetime] = None
    triage_action: Optional[str] = None
    triage_note: Optional[str] = None
    overdue: bool = False


class CollabPacketHistoryItem(BaseModel):
    id: int
    packet_id: str
    event_type: str
    action: Optional[str] = None
    packet_type: Optional[str] = None
    assignee_ai: Optional[str] = None
    due_at: Optional[datetime] = None
    note: Optional[str] = None
    work_date: str
    created_at: datetime

    class Config:
        from_attributes = True


class CollabSessionBase(BaseModel):
    ai_type: str
    session_link: Optional[str] = None
    assigned_task: Optional[str] = None


class CollabSessionCreate(CollabSessionBase):
    pass


class CollabSession(CollabSessionBase):
    id: int
    status: str
    last_exchange_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CollabState(BaseModel):
    active_ideas_count: int
    pending_packets_count: int
    active_sessions_count: int
