#!/usr/bin/env python3
"""
뉴스 수집 테스트 스크립트
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.collectors.news_manager import NewsCollectionManager

async def test_news_collection():
    """뉴스 수집 테스트"""
    print("🚀 뉴스 수집 테스트 시작...")
    
    # 수집기 매니저 초기화
    config = {
        'request_delay': 1.0
    }
    
    manager = NewsCollectionManager(config)
    
    try:
        # 뉴스 수집 실행
        results = await manager.run_all_collectors()
        
        print(f"\n📊 수집 결과 요약:")
        print(f"  총 수집된 뉴스: {results['total_count']}개")
        print(f"  수집 시간: {results['collection_time']}")
        
        # 통계 정보
        stats = results['stats']
        
        print(f"\n🏢 소스별 수집 결과:")
        for source, count in stats['by_source'].items():
            print(f"  {source}: {count}개")
        
        print(f"\n📂 카테고리별 분포:")
        for category, count in stats['by_category'].items():
            print(f"  {category}: {count}개")
        
        print(f"\n😊 감성 분석 결과:")
        for sentiment, count in stats['sentiment_distribution'].items():
            print(f"  {sentiment}: {count}개")
        
        print(f"\n🎯 중요도 분석 결과:")
        for importance, count in stats['importance_distribution'].items():
            print(f"  {importance}: {count}개")
        
        print(f"\n📈 가장 많이 언급된 종목 (상위 5개):")
        for stock_code, count in stats['top_mentioned_stocks'][:5]:
            print(f"  {stock_code}: {count}회")
        
        # 샘플 뉴스 정보 출력
        print(f"\n📰 수집된 뉴스 샘플:")
        for i, news in enumerate(results['news_items'][:3]):
            print(f"  {i+1}. [{news.get('source_name')}] {news.get('title', '')[:60]}...")
            print(f"     감성: {news.get('sentiment_score', 0):.2f}, 중요도: {news.get('importance_score', 0):.2f}")
            print(f"     종목: {news.get('stock_mentions', '없음')}")
        
        return results
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return None

async def test_individual_sources():
    """개별 소스 테스트"""
    print("\n🔍 개별 뉴스 소스 테스트 시작...")
    
    from backend.app.collectors.news import NewsCollector
    
    collector = NewsCollector()
    
    # 연합뉴스만 테스트
    print("  연합뉴스 수집 테스트...")
    yna_news = await collector.collect_yna_news()
    print(f"  ✅ 연합뉴스: {len(yna_news)}개 수집됨")
    
    if yna_news:
        sample = yna_news[0]
        print(f"  📄 샘플: {sample.get('title', '')[:50]}...")
        print(f"  🕐 발행시간: {sample.get('published_at')}")
        print(f"  📊 내용 길이: {len(sample.get('content', ''))}자")

async def test_specific_source():
    """특정 소스 테스트"""
    print("\n🎯 특정 소스 수집 테스트...")
    
    manager = NewsCollectionManager()
    
    for source in ['yna', 'hankyung']:
        print(f"  {source} 소스 수집 테스트...")
        try:
            news_items = await manager.collect_by_source(source)
            print(f"  ✅ {source}: {len(news_items)}개 수집됨")
        except Exception as e:
            print(f"  ❌ {source}: 실패 - {e}")

if __name__ == "__main__":
    # 간단한 테스트 실행
    print("Stock Research ONE - 뉴스 수집기 테스트")
    print("=" * 50)
    
    # 개별 소스 테스트
    asyncio.run(test_individual_sources())
    
    # 특정 소스 테스트
    asyncio.run(test_specific_source())
    
    # 전체 수집기 테스트
    asyncio.run(test_news_collection())
    
    print("\n✅ 테스트 완료!")
    
    # 수집 정보 요약
    print("\n📋 수집기 정보:")
    summary = NewsCollectionManager().get_collection_summary()
    print(f"  지원 소스: {summary['available_sources']}")
    print(f"  카테고리 수: {len(summary['categories'])}")
    print(f"  지원 기능: {', '.join(summary['supported_features'])}")