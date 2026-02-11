"""
Dashboard API Router - 투자 대시보드 엔드포인트
GET /api/v1/psychology, timing, portfolio, evaluation, flywheel
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/v1", tags=["Dashboard"])


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    return DashboardService(db)


def _raise_with_code(status_code: int, detail: str, error_code: str):
    """설계 문서 규격에 맞는 에러 응답 생성"""
    raise HTTPException(
        status_code=status_code,
        detail={
            "detail": detail,
            "error_code": error_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@router.get("/psychology")
async def get_psychology(service: DashboardService = Depends(get_dashboard_service)):
    """투자자 심리 지표 조회"""
    try:
        return await service.get_psychology_metrics()
    except HTTPException:
        raise
    except Exception as e:
        _raise_with_code(500, f"심리 지표 조회 실패: {str(e)}", "PSYCHOLOGY_FETCH_ERROR")


@router.get("/timing")
async def get_timing(service: DashboardService = Depends(get_dashboard_service)):
    """투자 타이밍 분석 (3/6/12개월)"""
    try:
        return await service.get_timing_analysis()
    except HTTPException:
        raise
    except Exception as e:
        _raise_with_code(500, f"타이밍 분석 실패: {str(e)}", "TIMING_FETCH_ERROR")


@router.get("/portfolio")
async def get_portfolio(service: DashboardService = Depends(get_dashboard_service)):
    """포트폴리오 현황 조회"""
    try:
        return await service.get_portfolio_overview()
    except HTTPException:
        raise
    except Exception as e:
        _raise_with_code(500, f"포트폴리오 조회 실패: {str(e)}", "PORTFOLIO_FETCH_ERROR")


@router.get("/evaluation")
async def get_evaluation(
    stock_code: Optional[str] = Query(None, description="종목 코드 (선택)"),
    service: DashboardService = Depends(get_dashboard_service),
):
    """기업 평가 조회"""
    try:
        return await service.get_company_evaluation(stock_code)
    except HTTPException:
        raise
    except Exception as e:
        _raise_with_code(500, f"기업 평가 조회 실패: {str(e)}", "EVALUATION_FETCH_ERROR")


@router.get("/flywheel")
async def get_flywheel(service: DashboardService = Depends(get_dashboard_service)):
    """플라이휠 진행 상태 조회"""
    try:
        return await service.get_flywheel_status()
    except HTTPException:
        raise
    except Exception as e:
        _raise_with_code(500, f"플라이휠 상태 조회 실패: {str(e)}", "FLYWHEEL_FETCH_ERROR")
