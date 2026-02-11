"""
Context Analysis API Router
2단계: 맥락연결/영향분석 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from ..database import get_db
from ..services.context_analysis_service import ContextAnalyzer, ContextAnalysis
from ..models import News
from ..services.news_service import NewsService

router = APIRouter(prefix="/context-analysis", tags=["context-analysis"])

# ContextAnalyzer는 DB 불필요 (순수 분석 엔진)
analyzer = ContextAnalyzer()


def get_news_service(db: Session = Depends(get_db)) -> NewsService:
    return NewsService(db)

@router.post("/analyze/{news_id}")
async def analyze_news_context(
    news_id: str,
    service: NewsService = Depends(get_news_service)
):
    """특정 뉴스 기사에 대한 맥락 분석 수행"""
    try:
        # 뉴스 데이터 조회
        news = await service.get_news_by_id(news_id)
        if not news:
            raise HTTPException(status_code=404, detail="News not found")

        # 맥락 분석 수행
        analysis = analyzer.analyze_content(
            news_id=news["id"],
            title=news["title"],
            content=news["content"]
        )
        
        return {
            "success": True,
            "data": {
                "news_id": analysis.news_id,
                "title": analysis.title,
                "content_summary": analysis.content_summary,
                "sentiment": {
                    "type": analysis.sentiment_score.sentiment.value,
                    "score": analysis.sentiment_score.score,
                    "confidence": analysis.sentiment_score.confidence,
                    "keywords": analysis.sentiment_score.keywords
                },
                "market_impact": {
                    "level": analysis.market_impact.level.value,
                    "scope": analysis.market_impact.market_scope,
                    "direction": analysis.market_impact.direction,
                    "duration": analysis.market_impact.duration_estimate,
                    "confidence": analysis.market_impact.confidence
                },
                "investor_behaviors": [
                    {
                        "investor_type": behavior.investor_type.value,
                        "behavior_type": behavior.behavior_type,
                        "probability": behavior.probability,
                        "reasoning": behavior.reasoning,
                        "timing": behavior.timing_expectation
                    }
                    for behavior in analysis.investor_behaviors
                ],
                "key_factors": analysis.key_factors,
                "related_stocks": analysis.related_stocks,
                "analysis_timestamp": analysis.analysis_timestamp.isoformat(),
                "confidence_score": analysis.confidence_score
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/recent-analyses")
async def get_recent_analyses(
    limit: int = Query(10, ge=1, le=100),
    hours: int = Query(24, ge=1, le=168),
    service: NewsService = Depends(get_news_service)
):
    """최근 맥락 분석 결과 조회"""
    try:
        # 최근 뉴스 목록 조회
        since = datetime.now() - timedelta(hours=hours)
        recent_news = await service.get_recent_news(limit=limit, since=since)

        analyses = []
        for news in recent_news:
            # 각 뉴스에 대해 맥락 분석 수행
            analysis = analyzer.analyze_content(
                news_id=news["id"],
                title=news["title"],
                content=news["content"]
            )
            
            analyses.append({
                "news_id": analysis.news_id,
                "title": analysis.title,
                "sentiment_type": analysis.sentiment_score.sentiment.value,
                "sentiment_score": analysis.sentiment_score.score,
                "market_direction": analysis.market_impact.direction,
                "impact_level": analysis.market_impact.level.value,
                "key_factors": analysis.key_factors[:3],  # 상위 3개 요인만
                "related_stocks": analysis.related_stocks,
                "analysis_timestamp": analysis.analysis_timestamp.isoformat()
            })
        
        return {
            "success": True,
            "count": len(analyses),
            "data": analyses
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent analyses: {str(e)}")

@router.get("/market-sentiment-summary")
async def get_market_sentiment_summary(
    hours: int = Query(24, ge=1, le=168),
    service: NewsService = Depends(get_news_service)
):
    """시장 심리 요약 (최근 N시간 기준)"""
    try:
        # 최근 뉴스 조회
        since = datetime.now() - timedelta(hours=hours)
        recent_news = await service.get_recent_news(limit=50, since=since)
        
        if not recent_news:
            return {
                "success": True,
                "data": {
                    "overall_sentiment": "neutral",
                    "sentiment_distribution": {},
                    "market_direction": "보합",
                    "key_themes": [],
                    "trending_stocks": [],
                    "analysis_count": 0,
                    "period_hours": hours
                }
            }
        
        # 모든 뉴스에 대해 맥락 분석
        analyses = []
        for news in recent_news:
            analysis = analyzer.analyze_content(
                news_id=news["id"],
                title=news["title"],
                content=news["content"]
            )
            analyses.append(analysis)

        # 종합 감성 분석
        sentiment_counts = {}
        total_sentiment_score = 0
        
        for analysis in analyses:
            sentiment_type = analysis.sentiment_score.sentiment.value
            sentiment_counts[sentiment_type] = sentiment_counts.get(sentiment_type, 0) + 1
            total_sentiment_score += analysis.sentiment_score.score
        
        # 전체 감성 결정
        avg_sentiment = total_sentiment_score / len(analyses)
        if avg_sentiment > 0.2:
            overall_sentiment = "positive"
        elif avg_sentiment < -0.2:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"
        
        # 시장 방향성 결정
        positive_count = sentiment_counts.get("positive", 0) + sentiment_counts.get("very_positive", 0)
        negative_count = sentiment_counts.get("negative", 0) + sentiment_counts.get("very_negative", 0)
        
        if positive_count > negative_count * 1.2:
            market_direction = "상승"
        elif negative_count > positive_count * 1.2:
            market_direction = "하락"
        else:
            market_direction = "보합"
        
        # 주요 테마 추출
        all_factors = []
        for analysis in analyses:
            all_factors.extend(analysis.key_factors)
        
        # 가장 많이 언급된 요인 상위 10개
        from collections import Counter
        factor_counter = Counter(all_factors)
        key_themes = [factor for factor, count in factor_counter.most_common(10)]
        
        # 트렌딩 종목 추출
        all_stocks = []
        for analysis in analyses:
            all_stocks.extend(analysis.related_stocks)
        
        stock_counter = Counter(all_stocks)
        trending_stocks = [stock for stock, count in stock_counter.most_common(10)]
        
        return {
            "success": True,
            "data": {
                "overall_sentiment": overall_sentiment,
                "sentiment_distribution": sentiment_counts,
                "market_direction": market_direction,
                "key_themes": key_themes,
                "trending_stocks": trending_stocks,
                "analysis_count": len(analyses),
                "period_hours": hours,
                "average_sentiment_score": round(avg_sentiment, 3)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate market summary: {str(e)}")

@router.get("/investor-behavior-analysis")
async def get_investor_behavior_analysis(
    investor_type: Optional[str] = Query(None, description="투자자 유형 필터링"),
    hours: int = Query(24, ge=1, le=168),
    service: NewsService = Depends(get_news_service)
):
    """투자자별 행동 분석"""
    try:
        # 최근 뉴스 조회
        since = datetime.now() - timedelta(hours=hours)
        recent_news = await service.get_recent_news(limit=50, since=since)
        
        if not recent_news:
            return {
                "success": True,
                "data": {
                    "behaviors": {},
                    "summary": {},
                    "analysis_count": 0
                }
            }
        
        # 모든 뉴스 분석
        all_behaviors = {}
        for news in recent_news:
            analysis = analyzer.analyze_content(
                news_id=news["id"],
                title=news["title"],
                content=news["content"]
            )
            
            for behavior in analysis.investor_behaviors:
                investor_type_key = behavior.investor_type.value
                
                if investor_type and investor_type_key != investor_type:
                    continue
                
                if investor_type_key not in all_behaviors:
                    all_behaviors[investor_type_key] = []
                
                all_behaviors[investor_type_key].append({
                    "behavior_type": behavior.behavior_type,
                    "probability": behavior.probability,
                    "reasoning": behavior.reasoning,
                    "timing": behavior.timing_expectation,
                    "news_title": news.title
                })
        
        # 각 투자자 유형별 요약
        summary = {}
        for investor_type_key, behaviors in all_behaviors.items():
            behavior_counts = {}
            total_probability = 0
            
            for behavior in behaviors:
                behavior_type = behavior["behavior_type"]
                behavior_counts[behavior_type] = behavior_counts.get(behavior_type, 0) + 1
                total_probability += behavior["probability"]
            
            # 가장 가능성 높은 행동
            dominant_behavior = max(behavior_counts.keys(), key=lambda x: behavior_counts[x])
            
            summary[investor_type_key] = {
                "dominant_behavior": dominant_behavior,
                "behavior_distribution": behavior_counts,
                "average_probability": total_probability / len(behaviors) if behaviors else 0,
                "total_analyses": len(behaviors)
            }
        
        return {
            "success": True,
            "data": {
                "behaviors": all_behaviors,
                "summary": summary,
                "analysis_count": len(recent_news)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze investor behaviors: {str(e)}")

@router.get("/test/analysis")
async def test_context_analysis():
    """맥락 분석 테스트 엔드포인트"""
    try:
        # 테스트용 뉴스 데이터
        test_news = {
            "id": "test_001",
            "title": "삼성전자, 4분기 실적 시장 예상 상회... 반도체 회복세 기대감↑",
            "content": "삼성전자가 4분기 실적이 시장 예상을 상회할 것이라는 전망이 나오고 있다. 반도체 업황의 점진적 회복세와 함께 메모리 반도체 가격 상승이 실적 개선에 기여할 것으로 보인다. 증권사들은 연이어 삼성전자의 목표가를 상향 조정하며 투자의견을 '매수'로 유지하고 있다. 다만, 세계 경제 둔화 우려로 단기적인 변동성은 불가피할 것으로 전망된다."
        }
        
        # 맥락 분석 수행
        analysis = analyzer.analyze_content(
            news_id=test_news["id"],
            title=test_news["title"],
            content=test_news["content"]
        )
        
        return {
            "success": True,
            "message": "Context analysis test completed successfully",
            "data": {
                "news_id": analysis.news_id,
                "title": analysis.title,
                "sentiment": {
                    "type": analysis.sentiment_score.sentiment.value,
                    "score": analysis.sentiment_score.score,
                    "confidence": analysis.sentiment_score.confidence
                },
                "market_impact": {
                    "level": analysis.market_impact.level.value,
                    "direction": analysis.market_impact.direction,
                    "scope": analysis.market_impact.market_scope
                },
                "investor_behaviors": [
                    {
                        "investor_type": behavior.investor_type.value,
                        "behavior_type": behavior.behavior_type,
                        "probability": behavior.probability,
                        "reasoning": behavior.reasoning
                    }
                    for behavior in analysis.investor_behaviors
                ],
                "key_factors": analysis.key_factors,
                "related_stocks": analysis.related_stocks,
                "confidence_score": analysis.confidence_score
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")