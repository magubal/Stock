"""
News Intelligence Monitor API Router
GET  /api/v1/news-intel/articles    - 뉴스 기사 목록
GET  /api/v1/news-intel/narrative   - AI 분석 내러티브
GET  /api/v1/news-intel/industries  - 섹터→인더스트리 퍼포먼스
GET  /api/v1/news-intel/stocks      - 인더스트리별 개별 종목
POST /api/v1/news-intel/fetch       - 실시간 Finviz 파싱
"""
import sys, os, asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.news_intelligence_service import NewsIntelligenceService

# scripts 경로를 sys.path에 추가 (finviz_fetch 임포트용)
_scripts_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _scripts_root not in sys.path:
    sys.path.insert(0, _scripts_root)

router = APIRouter(prefix="/api/v1/news-intel", tags=["News Intelligence"])


def get_service(db: Session = Depends(get_db)) -> NewsIntelligenceService:
    return NewsIntelligenceService(db)


@router.get("/articles")
async def get_articles(
    category: str = Query(None, description="카테고리 필터"),
    date: str = Query(None, description="날짜 (YYYY-MM-DD)"),
    source: str = Query(None, description="소스 필터"),
    limit: int = Query(500, ge=1, le=1000, description="최대 건수"),
    service: NewsIntelligenceService = Depends(get_service),
):
    """뉴스 기사 목록 조회"""
    try:
        return await service.get_articles(category=category, date=date, source=source, limit=limit)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": f"기사 조회 실패: {str(e)}", "error_code": "ARTICLES_FETCH_ERROR"},
        )


@router.get("/narrative")
async def get_narrative(
    date: str = Query(None, description="날짜 (YYYY-MM-DD)"),
    service: NewsIntelligenceService = Depends(get_service),
):
    """AI 분석 내러티브 조회"""
    try:
        return await service.get_narrative(date=date)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": f"내러티브 조회 실패: {str(e)}", "error_code": "NARRATIVE_FETCH_ERROR"},
        )


@router.get("/industries")
async def get_industries(
    sector: str = Query(None, description="섹터 필터 (e.g. Technology)"),
    date: str = Query(None, description="날짜 (YYYY-MM-DD)"),
    service: NewsIntelligenceService = Depends(get_service),
):
    """섹터→인더스트리 퍼포먼스 조회"""
    try:
        return await service.get_industries(sector=sector, date=date)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": f"인더스트리 조회 실패: {str(e)}", "error_code": "INDUSTRIES_FETCH_ERROR"},
        )


@router.get("/stocks")
async def get_stocks(
    industry: str = Query(None, description="인더스트리 필터 (e.g. Silver)"),
    sector: str = Query(None, description="섹터 필터 (e.g. Basic Materials)"),
    date: str = Query(None, description="날짜 (YYYY-MM-DD)"),
    service: NewsIntelligenceService = Depends(get_service),
):
    """인더스트리별 개별 종목 퍼포먼스 조회"""
    try:
        return await service.get_stocks(industry=industry, sector=sector, date=date)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": f"종목 조회 실패: {str(e)}", "error_code": "STOCKS_FETCH_ERROR"},
        )


@router.get("/stocks/coverage")
async def get_stock_coverage(
    date: str = Query(None, description="날짜 (YYYY-MM-DD)"),
    service: NewsIntelligenceService = Depends(get_service),
):
    """종목 수집 진척률 조회 (수집된 인더스트리 / 전체 144개)"""
    try:
        return await service.get_stock_coverage(date=date)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": f"진척률 조회 실패: {str(e)}", "error_code": "COVERAGE_ERROR"},
        )


@router.get("/models")
async def get_available_models():
    """사용 가능한 AI 모델 목록 조회"""
    from scripts.news_monitor.config import AVAILABLE_MODELS
    return {
        "models": [
            {"id": mid, **info}
            for mid, info in AVAILABLE_MODELS.items()
        ],
        "default": "claude-sonnet-4-5-20250929",
    }


@router.post("/analyze")
async def run_analysis(
    date: str = Query(None, description="날짜 (YYYY-MM-DD)"),
    model: str = Query(None, description="AI 모델 (sonnet/haiku/opus)"),
):
    """AI 내러티브 분석 실행 (모델 선택 가능). US 지수 + 섹터 + 뉴스 통합 분석."""
    try:
        from scripts.news_monitor.narrative_analyzer import analyze_today_news
        from datetime import timedelta

        utc_now = datetime.now(timezone.utc)
        kst_now = utc_now + timedelta(hours=9)
        target_date = date or kst_now.strftime("%Y-%m-%d")

        result = await asyncio.to_thread(analyze_today_news, target_date, model)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail={"detail": "분석 불가 (기사 없음 또는 API 키 미설정)", "error_code": "ANALYSIS_UNAVAILABLE"},
            )

        return {
            "status": "ok",
            "date": target_date,
            "model": model or "default",
            "key_issues": len(result.get("key_issues", [])),
            "sentiment": result.get("sentiment_label", "unknown"),
            "has_market_summary": bool(result.get("market_summary")),
            "has_timeline": bool(result.get("sentiment_timeline")),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": f"분석 실패: {str(e)}", "error_code": "ANALYSIS_ERROR"},
        )


@router.post("/fetch")
async def fetch_news(
    include_stocks: bool = Query(False, description="Stock 배치 수집 포함 (느림, ~20분)"),
    max_stocks: int = Query(0, ge=0, le=144, description="Stock 수집 인더스트리 수 (0=전체)"),
):
    """
    실시간 Finviz 데이터 수집 (통합 파이프라인).
    수집 순서: 뉴스 → Stock(옵션) → Sector Matrix → AI 내러티브
    Stock 수집은 Sector Matrix 직전에 실행 (종목 데이터 → 섹터 집계 일관성)
    """
    try:
        from scripts.news_monitor.finviz_fetch import fetch_all_categories, save_sector_industry_performance
        from scripts.news_monitor.narrative_analyzer import generate_from_sector_data
        from datetime import timedelta

        # KST(UTC+9)와 UTC 양쪽 날짜 → 타임존 무관하게 대응
        utc_now = datetime.now(timezone.utc)
        kst_now = utc_now + timedelta(hours=9)
        dates_to_update = list(set([
            utc_now.strftime("%Y-%m-%d"),
            kst_now.strftime("%Y-%m-%d"),
        ]))

        # Step 1: 뉴스 수집
        results = await asyncio.to_thread(fetch_all_categories)
        total_fetched = sum(r["fetched"] for r in results.values())
        total_saved = sum(r["saved"] for r in results.values())
        total_skipped = sum(r["skipped"] for r in results.values())

        # Step 2: Stock 배치 수집 (Sector Matrix 직전, 옵션)
        stock_result = None
        if include_stocks:
            from scripts.news_monitor.stock_fetch import run_batch
            stock_result = await asyncio.to_thread(
                run_batch,
                target_date=kst_now.strftime("%Y-%m-%d"),
                max_industries=max_stocks,
            )

        # Step 3: Sector + Industry 퍼포먼스 DB 저장
        perf_result = await asyncio.to_thread(save_sector_industry_performance)

        # Step 4: 섹터 퍼포먼스 기반 AI 내러티브 갱신 (AI 없이 실제 데이터)
        for d in dates_to_update:
            await asyncio.to_thread(generate_from_sector_data, d)

        return {
            "status": "ok",
            "pipeline": "news → stocks → sector_matrix → narrative",
            "total_fetched": total_fetched,
            "total_saved": total_saved,
            "total_skipped": total_skipped,
            "by_category": results,
            "performance": perf_result,
            "stocks": stock_result,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": f"뉴스 파싱 실패: {str(e)}", "error_code": "FETCH_ERROR"},
        )
