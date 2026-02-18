from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models.idea import Idea as IdeaModel
from ..models.idea_evidence import IdeaEvidence as EvidenceModel
from ..models.insight import Insight as InsightModel
from ..schemas.idea import (
    Idea,
    IdeaCreate,
    IdeaEvidenceCreate,
    IdeaEvidenceResponse,
    IdeaStats,
    IdeaStatus,
    IdeaUpdate,
)

router = APIRouter(
    prefix="/ideas",
    tags=["ideas"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Idea)
def create_idea(idea: IdeaCreate, db: Session = Depends(get_db)):
    db_idea = IdeaModel(**idea.model_dump())
    db.add(db_idea)
    db.commit()
    db.refresh(db_idea)
    return db_idea


@router.get("/", response_model=List[Idea])
def read_ideas(
    skip: int = 0,
    limit: int = 100,
    status: Optional[IdeaStatus] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(IdeaModel)

    if status:
        query = query.filter(IdeaModel.status == status)

    ordered_query = query.order_by(IdeaModel.updated_at.desc(), IdeaModel.created_at.desc())

    # SQLite JSON compatibility: apply tag filtering in Python, then paginate.
    if tag:
        ideas = ordered_query.all()
        ideas = [idea for idea in ideas if tag in (idea.tags or [])]
        return ideas[skip : skip + limit]

    return ordered_query.offset(skip).limit(limit).all()


@router.get("/stats/by-category", response_model=List[IdeaStats])
def idea_stats_by_category(db: Session = Depends(get_db)):
    rows = (
        db.query(IdeaModel.category, IdeaModel.status, sa_func.count(IdeaModel.id).label("count"))
        .group_by(IdeaModel.category, IdeaModel.status)
        .all()
    )
    stats = {}
    for row in rows:
        category = row.category or "uncategorized"
        if category not in stats:
            stats[category] = {"category": category, "count": 0, "by_status": {}}
        stats[category]["count"] += row.count
        stats[category]["by_status"][row.status or "draft"] = row.count
    return list(stats.values())


@router.get("/{idea_id}", response_model=Idea)
def read_idea(idea_id: int, db: Session = Depends(get_db)):
    db_idea = db.query(IdeaModel).filter(IdeaModel.id == idea_id).first()
    if db_idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")
    return db_idea


@router.put("/{idea_id}", response_model=Idea)
def update_idea(idea_id: int, idea: IdeaUpdate, db: Session = Depends(get_db)):
    db_idea = db.query(IdeaModel).filter(IdeaModel.id == idea_id).first()
    if db_idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")

    update_data = idea.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_idea, key, value)

    db.commit()
    db.refresh(db_idea)
    return db_idea


@router.delete("/{idea_id}")
def delete_idea(idea_id: int, db: Session = Depends(get_db)):
    db_idea = db.query(IdeaModel).filter(IdeaModel.id == idea_id).first()
    if db_idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")

    db.delete(db_idea)
    db.commit()
    return {"ok": True}


@router.post("/{idea_id}/evidence", response_model=IdeaEvidenceResponse)
def add_evidence(idea_id: int, ev: IdeaEvidenceCreate, db: Session = Depends(get_db)):
    idea = db.query(IdeaModel).filter(IdeaModel.id == idea_id).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    insight = db.query(InsightModel).filter(InsightModel.id == ev.insight_id).first()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    db_ev = EvidenceModel(idea_id=idea_id, insight_id=ev.insight_id, relation_type=ev.relation_type)
    db.add(db_ev)
    db.commit()
    db.refresh(db_ev)
    return db_ev


@router.get("/{idea_id}/evidence", response_model=List[IdeaEvidenceResponse])
def list_evidence(idea_id: int, db: Session = Depends(get_db)):
    return db.query(EvidenceModel).filter(EvidenceModel.idea_id == idea_id).all()
