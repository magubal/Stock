from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..services.news_service import NewsService
from ..schemas import News, NewsCreate

router = APIRouter(prefix="/api/v1/news", tags=["news"])

# 의존성 주입
def get_news_service(db: Session = Depends(get_db)) -> NewsService:
    return NewsService(db)

@router.get("/", response_model=List[News])
async def get_news(
    source: Optional[str] = Query(None, description="뉴스 소스 필터링"),
    category: Optional[str] = Query(None, description="카테고리 필터링"),
    limit: int = Query(50, ge=1, le=1000, description="최대 개수"),
    hours: int = Query(24, ge=1, le=168, description="시간 범위(시간)"),
    service: NewsService = Depends(get_news_service)
):
    """뉴스 목록 조회"""
    try:
        news = await service.get_news(
            source=source,
            category=category,
            limit=limit,
            hours=hours
        )
        return news
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"뉴스 조회 실패: {str(e)}")

@router.get("/stats")
async def get_news_stats(
    hours: int = Query(24, ge=1, le=168, description="시간 범위(시간)"),
    service: NewsService = Depends(get_news_service)
):
    """뉴스 통계 정보"""
    try:
        stats = await service.get_news_stats(hours=hours)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")

@router.post("/collect")
async def trigger_news_collection(
    source: Optional[str] = Query(None, description="특정 소스만 수집"),
    service: NewsService = Depends(get_news_service)
):
    """뉴스 수집 트리거"""
    try:
        result = await service.collect_news(source=source)
        
        if result['success']:
            return {
                "message": "뉴스 수집 완료",
                "total_collected": result['total_collected'],
                "saved_to_db": result['saved_to_db'],
                "collection_time": result['collection_time'],
                "source": result.get('source'),
                "stats": result.get('stats', {})
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"뉴스 수집 실패: {result['error']}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"수집 실패: {str(e)}")

@router.get("/important")
async def get_important_news(
    hours: int = Query(24, ge=1, le=168, description="시간 범위(시간)"),
    service: NewsService = Depends(get_news_service)
):
    """중요도 높은 뉴스 조회"""
    try:
        news = await service.get_news_by_importance(hours=hours)
        return {
            "news": news,
            "time_range": f"{hours}시간",
            "count": len(news)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"중요 뉴스 조회 실패: {str(e)}")

@router.get("/sentiment/{sentiment}")
async def get_news_by_sentiment(
    sentiment: str = Query(..., regex="^(positive|negative|neutral)$", description="감성 타입"),
    hours: int = Query(24, ge=1, le=168, description="시간 범위(시간)"),
    service: NewsService = Depends(get_news_service)
):
    """감성별 뉴스 조회"""
    try:
        news = await service.get_news_by_sentiment(sentiment=sentiment, hours=hours)
        return {
            "news": news,
            "sentiment": sentiment,
            "time_range": f"{hours}시간",
            "count": len(news)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"감성 뉴스 조회 실패: {str(e)}")

@router.get("/stock/{stock_code}")
async def get_news_by_stock(
    stock_code: str = Query(..., description="종목 코드"),
    hours: int = Query(24, ge=1, le=168, description="시간 범위(시간)"),
    service: NewsService = Depends(get_news_service)
):
    """종목 관련 뉴스 조회"""
    try:
        news = await service.get_news_by_stock(stock_code=stock_code, hours=hours)
        return {
            "news": news,
            "stock_code": stock_code,
            "time_range": f"{hours}시간",
            "count": len(news)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"종목 뉴스 조회 실패: {str(e)}")

@router.get("/search")
async def search_news(
    keyword: str = Query(..., min_length=2, description="검색 키워드"),
    limit: int = Query(20, ge=1, le=100, description="최대 개수"),
    service: NewsService = Depends(get_news_service)
):
    """뉴스 검색"""
    try:
        news = await service.search_news(keyword=keyword, limit=limit)
        return {
            "news": news,
            "keyword": keyword,
            "count": len(news)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"뉴스 검색 실패: {str(e)}")

@router.get("/sources/list")
async def get_supported_news_sources():
    """지원되는 뉴스 소스 목록"""
    return {
        "sources": [
            {
                "code": "yna",
                "name": "연합뉴스",
                "supported": True,
                "url": "https://www.yna.co.kr/economy",
                "description": "국내 최대 뉴스통신사"
            },
            {
                "code": "hankyung",
                "name": "한국경제",
                "supported": True,
                "url": "https://www.hankyung.com/economy",
                "description": "대표 경제 전문지"
            },
            {
                "code": "maeil",
                "name": "매일경제",
                "supported": True,
                "url": "https://www.mk.co.kr/news/economy/",
                "description": "경제 전문 일간지"
            },
            {
                "code": "edaily",
                "name": "이데일리",
                "supported": True,
                "url": "https://www.edaily.co.kr",
                "description": "경제/금융 전문지"
            }
        ]
    }

@router.get("/categories/list")
async def get_news_categories():
    """뉴스 카테고리 목록"""
    return {
        "categories": [
            {
                "code": "시장동향",
                "name": "시장동향",
                "description": "코스피/코스닥 시장 전반 동향"
            },
            {
                "code": "실적공시",
                "name": "실적공시",
                "description": "기업 실적 발표 및 관련 정보"
            },
            {
                "code": "기업공시",
                "name": "기업공시",
                "description": "M&A, 인수합병 등 기업 공시"
            },
            {
                "code": "금융정책",
                "name": "금융정책",
                "description": "금리, 환율 등 금융 정책 관련"
            },
            {
                "code": "산업동향",
                "name": "산업동향",
                "description": "주요 산업 및 섹터 동향"
            },
            {
                "code": "해외증시",
                "name": "해외증시",
                "description": "미국, 중국 등 해외 증시 동향"
            }
        ]
    }

@router.get("/dashboard/summary")
async def get_news_dashboard(
    hours: int = Query(24, ge=1, le=168, description="시간 범위(시간)"),
    service: NewsService = Depends(get_news_service)
):
    """뉴스 대시보드 요약 정보"""
    try:
        stats = await service.get_news_stats(hours=hours)
        recent_news = await service.get_news(limit=5, hours=hours)
        important_news = await service.get_news_by_importance(hours=hours)
        
        return {
            "total_news": stats.get('total_news', 0),
            "by_source": stats.get('by_source', {}),
            "avg_sentiment": stats.get('avg_sentiment', 0.0),
            "avg_importance": stats.get('avg_importance', 0.0),
            "latest_collection": stats.get('latest_collection'),
            "recent_news": recent_news[:3],
            "important_news": important_news[:3],
            "time_range": f"{hours}시간",
            "summary": {
                "sentiment_trend": "stable",  # TODO: 감성 트렌드 분석
                "importance_trend": "rising", # TODO: 중요도 트렌드 분석
                "most_active_source": max(stats.get('by_source', {}).items(), key=lambda x: x[1])[0] if stats.get('by_source') else None
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대시보드 정보 조회 실패: {str(e)}")