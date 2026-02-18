from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from typing import List, Optional
from datetime import date
from ..database import get_db
from ..models.daily_work import DailyWork as DailyWorkModel
from ..schemas.daily_work import DailyWork, DailyWorkCreate, DailyWorkStats

router = APIRouter(
    prefix="/api/v1/daily-work",
    tags=["daily-work"],
)


@router.post("/", response_model=DailyWork)
def create_daily_work(item: DailyWorkCreate, db: Session = Depends(get_db)):
    db_item = DailyWorkModel(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.get("/", response_model=List[DailyWork])
def list_daily_work(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
):
    query = db.query(DailyWorkModel)
    if category:
        query = query.filter(DailyWorkModel.category == category)
    if date_from:
        query = query.filter(DailyWorkModel.date >= date_from)
    if date_to:
        query = query.filter(DailyWorkModel.date <= date_to)
    return query.order_by(DailyWorkModel.date.desc()).offset(skip).limit(limit).all()


@router.get("/stats", response_model=List[DailyWorkStats])
def daily_work_stats(db: Session = Depends(get_db)):
    rows = (
        db.query(DailyWorkModel.category, sa_func.count(DailyWorkModel.id).label("count"))
        .group_by(DailyWorkModel.category)
        .all()
    )
    return [DailyWorkStats(category=r.category, count=r.count) for r in rows]


@router.get("/{item_id}", response_model=DailyWork)
def get_daily_work(item_id: int, db: Session = Depends(get_db)):
    item = db.query(DailyWorkModel).filter(DailyWorkModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Daily work not found")
    return item


@router.delete("/{item_id}")
def delete_daily_work(item_id: int, db: Session = Depends(get_db)):
    item = db.query(DailyWorkModel).filter(DailyWorkModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Daily work not found")
    db.delete(item)
    db.commit()
    return {"ok": True}
