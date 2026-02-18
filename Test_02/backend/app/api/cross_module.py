"""
Cross-Module Context API
모든 모듈 데이터를 통합 브리핑으로 제공합니다.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.cross_module_service import CrossModuleService

router = APIRouter(prefix="/api/v1/cross-module", tags=["cross-module"])


@router.get("/context")
async def get_cross_module_context(
    days: int = Query(default=3, ge=1, le=30, description="조회 기간 (일)"),
    db: Session = Depends(get_db),
):
    """전체 모듈 데이터를 통합 브리핑으로 반환"""
    service = CrossModuleService(db)
    return service.get_full_context(days=days)
