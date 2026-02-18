from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from ..database import get_db
from ..models.signal import Signal as SignalModel
from ..schemas.signal import (
    SignalGenerateRequest,
    SignalGenerateResponse,
    SignalListResponse,
    SignalResponse,
    SignalStatusUpdate,
    SignalAcceptResponse,
)
from ..services.signal_service import SignalDetectionEngine
from ..services.strategist_service import StrategistService
from ..services.gap_analyzer import GapAnalyzer
from ..services.cross_module_service import CrossModuleService
import json
from datetime import datetime

router = APIRouter(
    prefix="/api/v1/signals",
    tags=["signals"],
    responses={404: {"description": "Not found"}},
)


def _model_to_response(s: SignalModel) -> dict:
    """ORM 모델을 응답 dict로 변환"""
    return {
        "id": s.id,
        "signal_id": s.signal_id,
        "rule_id": s.rule_id,
        "title": s.title,
        "description": s.description,
        "category": s.category,
        "signal_type": s.signal_type or "cross",
        "confidence": s.confidence or 0.0,
        "data_sources": json.loads(s.data_sources) if s.data_sources else [],
        "evidence": json.loads(s.evidence) if s.evidence else [],
        "suggested_action": s.suggested_action,
        "ai_interpretation": s.ai_interpretation,
        "data_gaps": json.loads(s.data_gaps) if s.data_gaps else [],
        "status": s.status,
        "related_idea_id": s.related_idea_id,
        "expires_at": s.expires_at,
        "created_at": s.created_at,
        "reviewed_at": s.reviewed_at,
    }


@router.post("/generate", response_model=SignalGenerateResponse)
def generate_signals(
    req: SignalGenerateRequest = SignalGenerateRequest(),
    db: Session = Depends(get_db),
):
    """시그널 생성 실행 (규칙 엔진 트리거)"""
    engine = SignalDetectionEngine(db)
    signals = engine.generate_signals(days=req.days)
    return SignalGenerateResponse(
        generated_at=datetime.utcnow().isoformat() + "Z",
        signals_count=len(signals),
        signals=signals,
    )


@router.get("", response_model=SignalListResponse)
def list_signals(
    status: Optional[str] = Query(None, description="Comma-separated statuses: new,reviewed"),
    category: Optional[str] = Query(None, description="Signal category filter"),
    min_confidence: Optional[float] = Query(None, description="Minimum confidence threshold"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """시그널 목록 조회"""
    query = db.query(SignalModel)

    if status:
        statuses = [s.strip() for s in status.split(",")]
        query = query.filter(SignalModel.status.in_(statuses))
    if category:
        query = query.filter(SignalModel.category == category)
    if min_confidence is not None:
        query = query.filter(SignalModel.confidence >= min_confidence)

    total = query.count()
    signals = (
        query.order_by(desc(SignalModel.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    return SignalListResponse(
        total=total,
        signals=[_model_to_response(s) for s in signals],
    )


@router.get("/{signal_id}", response_model=SignalResponse)
def get_signal(signal_id: int, db: Session = Depends(get_db)):
    """시그널 상세 조회"""
    signal = db.query(SignalModel).filter(SignalModel.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return _model_to_response(signal)


@router.put("/{signal_id}/status")
def update_signal_status(
    signal_id: int,
    update: SignalStatusUpdate,
    db: Session = Depends(get_db),
):
    """시그널 상태 변경 (reviewed/accepted/rejected)"""
    signal = db.query(SignalModel).filter(SignalModel.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    signal.status = update.status.value
    signal.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(signal)

    return _model_to_response(signal)


@router.post("/{signal_id}/interpret")
def interpret_signal(signal_id: int, db: Session = Depends(get_db)):
    """AI 전략가 해석 요청 (Phase 2)"""
    signal = db.query(SignalModel).filter(SignalModel.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    signal_dict = _model_to_response(signal)
    cross_module = CrossModuleService(db)
    context = cross_module.get_full_context(days=3)

    strategist = StrategistService()
    result = strategist.interpret_signal(signal_dict, context)

    # AI 해석 결과를 DB에 저장
    if result.get("interpretation"):
        signal.ai_interpretation = json.dumps(result, ensure_ascii=False)
        # confidence 조정 적용
        adj = result.get("confidence_adjustment", 0.0)
        if adj and signal.confidence:
            signal.confidence = max(0.0, min(1.0, signal.confidence + adj))
        db.commit()
        db.refresh(signal)

    return {
        "signal_id": signal.signal_id,
        "ai_result": result,
        "updated_confidence": signal.confidence,
    }


@router.get("/{signal_id}/gaps")
def analyze_signal_gaps(signal_id: int, db: Session = Depends(get_db)):
    """데이터 갭 분석 (Phase 2)"""
    signal = db.query(SignalModel).filter(SignalModel.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    signal_dict = _model_to_response(signal)
    cross_module = CrossModuleService(db)
    context = cross_module.get_full_context(days=3)

    analyzer = GapAnalyzer()
    result = analyzer.analyze(signal_dict, context)

    # 갭 결과를 DB에 저장
    signal.data_gaps = json.dumps(result.get("gaps", []), ensure_ascii=False)
    db.commit()

    return {
        "signal_id": signal.signal_id,
        "gaps": result,
    }


@router.post("/{signal_id}/accept", response_model=SignalAcceptResponse)
def accept_signal(signal_id: int, db: Session = Depends(get_db)):
    """시그널 채택 → Idea 자동 생성"""
    engine = SignalDetectionEngine(db)
    result = engine.accept_signal(signal_id)
    if not result:
        raise HTTPException(status_code=404, detail="Signal not found")
    return result
