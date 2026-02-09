"""
Simple Context Analysis Test - Direct Import
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.context_analysis_service import ContextAnalyzer

def simple_test():
    """간단한 맥락 분석 테스트"""
    print("=== Context Analysis Engine Test ===")
    
    analyzer = ContextAnalyzer()
    
    # 테스트 뉴스
    test_news = {
        "id": "test_001",
        "title": "삼성전자, 4분기 실적 시장 예상 상회... 반도체 회복세 기대감상승",
        "content": "삼성전자가 4분기 실적이 시장 예상을 상회할 것이라는 전망이 나오고 있다. 반도체 업황의 점진적 회복세와 함께 메모리 반도체 가격 상승이 실적 개선에 기여할 것으로 보인다. 증권사들은 연이어 삼성전자의 목표가를 상향 조정하며 투자의견을 매수로 유지하고 있다."
    }
    
    # 분석 실행
    analysis = analyzer.analyze_content(
        news_id=test_news["id"],
        title=test_news["title"], 
        content=test_news["content"]
    )
    
    # 결과 출력
    print(f"News ID: {analysis.news_id}")
    print(f"Title: {analysis.title}")
    print(f"Sentiment: {analysis.sentiment_score.sentiment.value} (Score: {analysis.sentiment_score.score:.3f})")
    print(f"Market Impact: {analysis.market_impact.direction} ({analysis.market_impact.level.value})")
    print(f"Key Factors: {', '.join(analysis.key_factors)}")
    print(f"Related Stocks: {', '.join(analysis.related_stocks)}")
    print(f"Confidence Score: {analysis.confidence_score:.3f}")
    
    print("\nInvestor Behaviors:")
    for behavior in analysis.investor_behaviors:
        print(f"  - {behavior.investor_type.value}: {behavior.behavior_type} ({behavior.probability:.0%}) - {behavior.reasoning}")
    
    print("\n=== Test Completed ===")

if __name__ == "__main__":
    simple_test()