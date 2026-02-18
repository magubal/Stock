"""
Moat Analysis Dashboard API Router
GET /api/v1/moat-dashboard          - KPIs + 분포 + 섹터
GET /api/v1/moat-dashboard/top      - 투자가치 ≥ N 종목
GET /api/v1/moat-dashboard/stocks   - 페이지네이션 + 필터
POST /api/v1/moat-dashboard/reload  - JSON 재로드
"""

from fastapi import APIRouter, Query
from typing import Optional

from ..services.moat_dashboard_service import MoatDashboardService

router = APIRouter(prefix="/api/v1", tags=["Moat Dashboard"])

_service = MoatDashboardService()


@router.get("/moat-dashboard")
async def get_summary():
    """KPI + 해자/투자가치 분포 + 섹터 분포"""
    return _service.get_summary()


@router.get("/moat-dashboard/top")
async def get_top_stocks(
    min_value: int = Query(4, ge=0, le=5, description="최소 투자가치"),
    sort_by: str = Query("investment_value", description="정렬 기준"),
    sort_desc: bool = Query(True, description="내림차순 여부"),
    limit: int = Query(50, ge=1, le=500, description="최대 건수"),
    sector: Optional[str] = Query(None, description="섹터 필터"),
):
    """투자가치 상위 종목 목록"""
    return _service.get_top_stocks(
        min_value=min_value,
        sort_by=sort_by,
        sort_desc=sort_desc,
        limit=limit,
        sector=sector,
    )


@router.get("/moat-dashboard/stocks")
async def get_stocks(
    min_moat: int = Query(0, ge=0, le=5, description="최소 해자 점수"),
    min_value: int = Query(0, ge=0, le=5, description="최소 투자가치"),
    sector: Optional[str] = Query(None, description="섹터 필터"),
    limit: int = Query(100, ge=1, le=500, description="페이지 크기"),
    offset: int = Query(0, ge=0, description="오프셋"),
):
    """전체 종목 목록 (페이지네이션 + 필터)"""
    return _service.get_stocks(
        min_moat=min_moat,
        min_value=min_value,
        sector=sector,
        limit=limit,
        offset=offset,
    )


@router.post("/moat-dashboard/reload")
async def reload_data():
    """JSON 데이터 재로드"""
    _service.reload()
    summary = _service.get_summary()
    return {
        "status": "reloaded",
        "total_stocks": summary["meta"]["total_stocks"],
        "evaluated_count": summary["meta"]["evaluated_count"],
    }
