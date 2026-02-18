import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.insight import Insight as InsightModel
from ..models.daily_work import DailyWork as DailyWorkModel
from ..schemas.insight import Insight, InsightCreate, InsightExtractRequest

router = APIRouter(
    prefix="/api/v1/insights",
    tags=["insights"],
)


@router.post("/", response_model=Insight)
def create_insight(item: InsightCreate, db: Session = Depends(get_db)):
    data = item.model_dump()
    # keywords를 JSON 문자열로 저장
    data["keywords"] = json.dumps(data.get("keywords", []), ensure_ascii=False)
    db_item = InsightModel(**data)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    # keywords를 리스트로 다시 변환하여 반환
    result = _to_response(db_item)
    return result


@router.get("/", response_model=List[Insight])
def list_insights(
    skip: int = 0,
    limit: int = 100,
    type: Optional[str] = None,
    work_id: Optional[int] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(InsightModel)
    if type:
        query = query.filter(InsightModel.type == type)
    if work_id:
        query = query.filter(InsightModel.work_id == work_id)
    items = query.order_by(InsightModel.created_at.desc()).offset(skip).limit(limit).all()

    # keyword 필터: Python 레벨 (SQLite JSON 쿼리 제한)
    if keyword:
        items = [i for i in items if keyword.lower() in (i.keywords or "").lower()]

    return [_to_response(i) for i in items]


@router.get("/{item_id}", response_model=Insight)
def get_insight(item_id: int, db: Session = Depends(get_db)):
    item = db.query(InsightModel).filter(InsightModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Insight not found")
    return _to_response(item)


@router.post("/extract", response_model=List[Insight])
def extract_insights(req: InsightExtractRequest, db: Session = Depends(get_db)):
    """LLM으로 인사이트 자동 추출 (work_id 기반)"""
    work = db.query(DailyWorkModel).filter(DailyWorkModel.id == req.work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Daily work not found")

    from ..services.insight_extractor import InsightExtractor
    from ..config import settings

    extractor = InsightExtractor(api_key=getattr(settings, "ANTHROPIC_API_KEY", None))
    results = extractor.extract(work.content, work.category)

    saved = []
    for r in results:
        db_item = InsightModel(
            work_id=work.id,
            type=r["type"],
            text=r["text"],
            confidence=r.get("confidence", 0.5),
            keywords=json.dumps(r.get("keywords", []), ensure_ascii=False),
            source_ai="claude",
        )
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        saved.append(_to_response(db_item))

    return saved


@router.delete("/{item_id}")
def delete_insight(item_id: int, db: Session = Depends(get_db)):
    item = db.query(InsightModel).filter(InsightModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Insight not found")
    db.delete(item)
    db.commit()
    return {"ok": True}


def _to_response(item: InsightModel) -> dict:
    """InsightModel → response dict (keywords JSON 파싱)"""
    keywords = []
    if item.keywords:
        try:
            keywords = json.loads(item.keywords)
        except (json.JSONDecodeError, TypeError):
            keywords = []
    return {
        "id": item.id,
        "work_id": item.work_id,
        "type": item.type,
        "text": item.text,
        "confidence": item.confidence,
        "keywords": keywords,
        "source_ai": item.source_ai,
        "created_at": item.created_at,
    }
