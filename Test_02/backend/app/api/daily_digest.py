"""
Market Daily Digest API Router
GET  /api/v1/daily-digest/{date}   - 특정 날짜 종합정리 조회
POST /api/v1/daily-digest          - 종합정리 저장 (upsert)
GET  /api/v1/daily-digest/history  - 저장 히스토리 목록
POST /api/v1/daily-digest/ai-analyze - AI 총평 생성
GET  /api/v1/daily-digest/models   - 사용 가능한 AI 모델 목록
"""
import sys, os
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.daily_digest_service import DailyDigestService

_scripts_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _scripts_root not in sys.path:
    sys.path.insert(0, _scripts_root)

router = APIRouter(prefix="/api/v1/daily-digest", tags=["Daily Digest"])


def get_service(db: Session = Depends(get_db)) -> DailyDigestService:
    return DailyDigestService(db)


@router.get("/models")
async def get_available_models():
    """사용 가능한 AI 모델 목록"""
    from scripts.news_monitor.config import AVAILABLE_MODELS
    return {
        "models": [{"id": mid, **info} for mid, info in AVAILABLE_MODELS.items()],
        "default": "claude-sonnet-4-5-20250929",
    }


@router.get("/history")
async def get_history(
    limit: int = Query(30, ge=1, le=100, description="최대 건수"),
    service: DailyDigestService = Depends(get_service),
):
    """저장된 종합정리 히스토리 목록"""
    try:
        return await service.get_history(limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": f"히스토리 조회 실패: {str(e)}", "error_code": "HISTORY_ERROR"},
        )


@router.get("/{date}")
async def get_digest(
    date: str,
    service: DailyDigestService = Depends(get_service),
):
    """특정 날짜 종합정리 조회"""
    try:
        return await service.get_digest(date=date)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": f"종합정리 조회 실패: {str(e)}", "error_code": "DIGEST_FETCH_ERROR"},
        )


@router.post("")
async def save_digest(
    data: dict = Body(...),
    service: DailyDigestService = Depends(get_service),
):
    """종합정리 저장 (upsert by date)"""
    try:
        return await service.save_digest(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": f"저장 실패: {str(e)}", "error_code": "SAVE_ERROR"},
        )


@router.post("/ai-analyze")
async def ai_analyze(
    data: dict = Body(...),
):
    """AI 총평 생성 (Claude/GPT/Gemini proxy)"""
    try:
        from ..services.daily_digest_service import DailyDigestService
        from ..database import get_db

        db = next(get_db())
        try:
            service = DailyDigestService(db)
            return await service.ai_analyze(
                date=data.get("date", ""),
                module_summaries=data.get("module_summaries", {}),
                model=data.get("model"),
            )
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": f"AI 분석 실패: {str(e)}", "error_code": "AI_ERROR"},
        )
