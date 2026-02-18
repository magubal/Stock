from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.monitoring import MonitoringIncident
from ..schemas.monitoring import (
    MonitoringDecisionRequest,
    MonitoringDecisionResponse,
    MonitoringIncidentResponse,
)
from ..services.monitoring_guard_service import MonitoringGuardService


router = APIRouter(
    prefix="/api/v1/monitoring",
    tags=["monitoring"],
)


def _resolve_decider(raw_decider: str) -> str:
    value = (raw_decider or "").strip()
    if value and value.lower() != "codex":
        raise HTTPException(status_code=400, detail="decider_must_be_codex")
    return "codex"


@router.get("/incidents", response_model=List[MonitoringIncidentResponse])
def list_incidents(status: str = "blocked_pending_codex", limit: int = 100, db: Session = Depends(get_db)):
    service = MonitoringGuardService(db)
    if status != "blocked_pending_codex":
        rows = (
            db.query(MonitoringIncident)
            .filter(MonitoringIncident.status == status)
            .order_by(MonitoringIncident.id.desc())
            .limit(limit)
            .all()
        )
        return rows
    return service.list_pending(limit=limit)


@router.post("/incidents/{incident_id}/approve", response_model=MonitoringDecisionResponse)
def approve_incident(incident_id: int, req: MonitoringDecisionRequest, db: Session = Depends(get_db)):
    service = MonitoringGuardService(db)
    try:
        decision = service.approve_incident(incident_id, req.note, _resolve_decider(req.decider))
        db.commit()
        db.refresh(decision)
        return decision
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/incidents/{incident_id}/reject", response_model=MonitoringDecisionResponse)
def reject_incident(incident_id: int, req: MonitoringDecisionRequest, db: Session = Depends(get_db)):
    service = MonitoringGuardService(db)
    try:
        decision = service.reject_incident(incident_id, req.note, _resolve_decider(req.decider))
        db.commit()
        db.refresh(decision)
        return decision
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/incidents/{incident_id}/resolve", response_model=MonitoringDecisionResponse)
def resolve_incident(incident_id: int, req: MonitoringDecisionRequest, db: Session = Depends(get_db)):
    service = MonitoringGuardService(db)
    try:
        decision = service.resolve_incident(incident_id, req.note, _resolve_decider(req.decider))
        db.commit()
        db.refresh(decision)
        return decision
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
