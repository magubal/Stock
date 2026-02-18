"""
Liquidity & Credit Stress Monitor API Router
GET /api/v1/liquidity-stress         - 최신 스트레스 데이터
GET /api/v1/liquidity-stress/history - 30일 히스토리
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.liquidity_stress_service import LiquidityStressService

router = APIRouter(prefix="/api/v1", tags=["Liquidity Stress"])


def get_service(db: Session = Depends(get_db)) -> LiquidityStressService:
    return LiquidityStressService(db)


def _raise_with_code(status_code: int, detail: str, error_code: str):
    raise HTTPException(
        status_code=status_code,
        detail={
            "detail": detail,
            "error_code": error_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@router.get("/liquidity-stress")
async def get_latest_stress(service: LiquidityStressService = Depends(get_service)):
    """최신 유동성·크레딧 스트레스 데이터 조회"""
    try:
        return await service.get_latest_stress()
    except HTTPException:
        raise
    except Exception as e:
        _raise_with_code(500, f"스트레스 데이터 조회 실패: {str(e)}", "STRESS_FETCH_ERROR")


@router.get("/liquidity-stress/history")
async def get_stress_history(
    days: int = Query(30, ge=1, le=365, description="조회 일수"),
    service: LiquidityStressService = Depends(get_service),
):
    """유동성·크레딧 스트레스 히스토리 조회"""
    try:
        return await service.get_stress_history(days)
    except HTTPException:
        raise
    except Exception as e:
        _raise_with_code(500, f"스트레스 히스토리 조회 실패: {str(e)}", "STRESS_HISTORY_ERROR")
