"""
Test Context Analysis Script
2단계: 맥락연결/영향분석 기능 테스트
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.context_analysis_service import ContextAnalyzer

def test_context_analysis():
    """맥락 분석 기능 테스트"""
    print("Context Analysis Engine 테스트 시작...")
    
    analyzer = ContextAnalyzer()
    
    # 테스트 케이스 1: 긍정적 뉴스
    print("\n테스트 케이스 1: 긍정적 뉴스")
    news_1 = {
        "id": "test_001",
        "title": "삼성전자, 4분기 실적 시장 예상 상회... 반도체 회복세 기대감↑",
        "content": "삼성전자가 4분기 실적이 시장 예상을 상회할 것이라는 전망이 나오고 있다. 반도체 업황의 점진적 회복세와 함께 메모리 반도체 가격 상승이 실적 개선에 기여할 것으로 보인다. 증권사들은 연이어 삼성전자의 목표가를 상향 조정하며 투자의견을 '매수'로 유지하고 있다."
    }
    
    analysis_1 = analyzer.analyze_content(
        news_1["id"], 
        news_1["title"], 
        news_1["content"]
    )
    
    print(f"감성: {analysis_1.sentiment_score.sentiment.value} (점수: {analysis_1.sentiment_score.score:.2f})")
    print(f"시장영향: {analysis_1.market_impact.direction} ({analysis_1.market_impact.level.value})")
    print(f"핵심요인: {', '.join(analysis_1.key_factors[:3])}")
    print(f"관련종목: {', '.join(analysis_1.related_stocks)}")
    
    # 테스트 케이스 2: 부정적 뉴스
    print("\n테스트 케이스 2: 부정적 뉴스")
    news_2 = {
        "id": "test_002", 
        "title": "코스피 급락... 금리인상 우려에 투자심리 위축",
        "content": "미국 연준의 공격적인 금리인상 가능성에 코스피가 큰 폭으로 하락했다. 투자자들의 위험회피 성향이 강해지며 코스닥 시장도 동반 하락했다. 증권가들은 당분간 시장 변동성이 확대될 것으로 예상하며 투자자들에게 신중한 접근을 당부하고 있다."
    }
    
    analysis_2 = analyzer.analyze_content(
        news_2["id"],
        news_2["title"], 
        news_2["content"]
    )
    
    print(f"감성: {analysis_2.sentiment_score.sentiment.value} (점수: {analysis_2.sentiment_score.score:.2f})")
    print(f"시장영향: {analysis_2.market_impact.direction} ({analysis_2.market_impact.level.value})")
    print(f"핵심요인: {', '.join(analysis_2.key_factors[:3])}")
    print(f"관련종목: {', '.join(analysis_2.related_stocks)}")
    
    # 테스트 케이스 3: 중립적 뉴스
    print("\n테스트 케이스 3: 중립적 뉴스")
    news_3 = {
        "id": "test_003",
        "title": "금융당국, 외환시장 안정화 방안 논의",
        "content": "금융당국이 최근 원/달러 환율 변동성 확대에 대응하기 위해 관계 부처와 협의 중이다. 현재로서는 구체적인 대책 발표 시점은 정해지지 않았으나, 시장 참여자들의 과도한 투기 심리를 경계하고 있다. 전문가들은 정부의 적절한 시장 개입이 필요하다고 입을 모으고 있다."
    }
    
    analysis_3 = analyzer.analyze_content(
        news_3["id"],
        news_3["title"],
        news_3["content"]
    )
    
    print(f"감성: {analysis_3.sentiment_score.sentiment.value} (점수: {analysis_3.sentiment_score.score:.2f})")
    print(f"시장영향: {analysis_3.market_impact.direction} ({analysis_3.market_impact.level.value})")
    print(f"핵심요인: {', '.join(analysis_3.key_factors[:3])}")
    print(f"관련종목: {', '.join(analysis_3.related_stocks)}")
    
    # 투자자 행동 예측 요약
    print("\n투자자 행동 예측 비교:")
    print("뉴스 1 (긍정적):")
    for behavior in analysis_1.investor_behaviors:
        print(f"  - {behavior.investor_type.value}: {behavior.behavior_type} ({behavior.probability:.0%})")
    
    print("뉴스 2 (부정적):")
    for behavior in analysis_2.investor_behaviors:
        print(f"  - {behavior.investor_type.value}: {behavior.behavior_type} ({behavior.probability:.0%})")
    
    print("뉴스 3 (중립적):")
    for behavior in analysis_3.investor_behaviors:
        print(f"  - {behavior.investor_type.value}: {behavior.behavior_type} ({behavior.probability:.0%})")
    
    print("\nContext Analysis 테스트 완료!")

def test_sentiment_analysis():
    """감성 분석 기능만 별도 테스트"""
    print("\n감성 분석 상세 테스트")
    
    analyzer = ContextAnalyzer()
    
    test_texts = [
        "삼성전자 주가 급등! 목표가 대폭 상향 조정",
        "LG화학 실적 악화로 주가 급락 전망", 
        "SK하이닉스 반도체 업황 개선 기대감",
        "현대차 노사 갈등 심화... 생산 차질 우려",
        "카카오 규제 리스크로 투자의견 하향 조정"
    ]
    
    for i, text in enumerate(test_texts, 1):
        result = analyzer.analyze_sentiment(text)
        print(f"{i}. '{text}'")
        print(f"   감성: {result.sentiment.value} (점수: {result.score:.2f}, 신뢰도: {result.confidence:.2f})")
        print(f"   키워드: {result.keywords}")
        print()

if __name__ == "__main__":
    test_context_analysis()
    test_sentiment_analysis()