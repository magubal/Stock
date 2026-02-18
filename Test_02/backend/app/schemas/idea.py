from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class IdeaStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    TESTING = "testing"
    VALIDATED = "validated"
    INVALIDATED = "invalidated"
    ARCHIVED = "archived"


class IdeaBase(BaseModel):
    title: str
    content: str
    source: Optional[str] = "Manual"
    category: Optional[str] = None
    thesis: Optional[str] = None
    status: Optional[IdeaStatus] = IdeaStatus.DRAFT
    priority: Optional[int] = 3
    tags: Optional[List[str]] = []
    author: Optional[str] = None
    action_item_id: Optional[str] = None


class IdeaCreate(IdeaBase):
    pass


class IdeaUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = None
    category: Optional[str] = None
    thesis: Optional[str] = None
    status: Optional[IdeaStatus] = None
    priority: Optional[int] = None
    tags: Optional[List[str]] = None
    author: Optional[str] = None
    action_item_id: Optional[str] = None


class Idea(IdeaBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IdeaEvidenceCreate(BaseModel):
    insight_id: int
    relation_type: Optional[str] = "supports"


class IdeaEvidenceResponse(BaseModel):
    id: int
    idea_id: int
    insight_id: int
    relation_type: str

    class Config:
        from_attributes = True


class IdeaStats(BaseModel):
    category: str
    count: int
    by_status: dict
