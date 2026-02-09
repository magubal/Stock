# 간단한 테스트 버전
print("Stock Research ONE - Backend Test")
print("=" * 40)

# 간단한 API 응답 테스트
from fastapi import FastAPI

app = FastAPI(title="Stock Research ONE - Test")

@app.get("/")
async def root():
    return {
        "message": "Stock Research ONE API - Test Version",
        "status": "running",
        "features": [
            "뉴스 수집 준비",
            "리포트 수집 준비", 
            "대시보드 API 준비"
        ]
    }

@app.get("/test/dashboard")
async def test_dashboard():
    return {
        "psychology": {
            "market_heat": 35,
            "empathy": 72,
            "expectation": 58
        },
        "portfolio": {
            "total_stocks": 12,
            "avg_return": 24.8,
            "sell_signals": 3
        },
        "timing": [
            {"period": "3개월", "signal": "good", "reason": "기대요소 > 우려요소"},
            {"period": "6개월", "signal": "good", "reason": "구조적 성장 기대"},
            {"period": "1년", "signal": "caution", "reason": "변동성 증가 예상"}
        ]
    }

@app.get("/test/news-stats")
async def test_news_stats():
    return {
        "total_news": 87,
        "by_source": {
            "연합뉴스": 25,
            "한국경제": 22,
            "매일경제": 20,
            "이데일리": 20
        },
        "avg_sentiment": 0.3,
        "avg_importance": 0.8,
        "collection_sources": ["yna", "hankyung", "maeil", "edaily"]
    }

@app.get("/test/reports-stats")
async def test_reports_stats():
    return {
        "total_reports": 45,
        "by_brokerage": {
            "키움증권": 12,
            "미래에셋증권": 15,
            "KB증권": 10,
            "NH투자증권": 8
        },
        "latest_collection": "2026-01-31T21:00:00"
    }

# Context Analysis Test Integration
@app.get("/test/context-analysis")
async def test_context_analysis():
    """Context Analysis Engine 테스트"""
    try:
        # Import context analyzer
        from app.services.context_analysis_service import ContextAnalyzer
        
        analyzer = ContextAnalyzer()
        
        # 테스트 뉴스 데이터
        test_news = {
            "id": "test_001",
            "title": "삼성전자, 4분기 실적 시장 예상 상회... 반도체 회복세 기대감상승",
            "content": "삼성전자가 4분기 실적이 시장 예상을 상회할 것이라는 전망이 나오고 있다. 반도체 업황의 점진적 회복세와 함께 메모리 반도체 가격 상승이 실적 개선에 기여할 것으로 보인다. 증권사들은 연이어 삼성전자의 목표가를 상향 조정하며 투자의견을 매수로 유지하고 있다."
        }
        
        # 맥락 분석 실행
        analysis = analyzer.analyze_content(
            news_id=test_news["id"],
            title=test_news["title"], 
            content=test_news["content"]
        )
        
        return {
            "success": True,
            "message": "Context Analysis Engine 테스트 성공",
            "data": {
                "news_id": analysis.news_id,
                "sentiment": {
                    "type": analysis.sentiment_score.sentiment.value,
                    "score": analysis.sentiment_score.score,
                    "confidence": analysis.sentiment_score.confidence
                },
                "market_impact": {
                    "direction": analysis.market_impact.direction,
                    "level": analysis.market_impact.level.value,
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
        return {
            "success": False,
            "message": f"Context Analysis 테스트 실패: {str(e)}",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 테스트 서버 시작: http://localhost:8000")
    print("📚 API 문서: http://localhost:8000/docs")
    print("📊 테스트 엔드포인트:")
    print("  - GET /")
    print("  - GET /test/dashboard")
    print("  - GET /test/news-stats") 
    print("  - GET /test/reports-stats")
    print("🔄 서버 실행 중... (Ctrl+C 종료)")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)