from typing import List, Dict, Any
from datetime import datetime, timedelta
import asyncio
from .news import NewsCollector

class NewsCollectionManager:
    """뉴스 수집 매니저"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.collectors = {
            'news': NewsCollector(config)
        }
    
    async def run_all_collectors(self) -> Dict[str, Any]:
        """모든 뉴스 수집기 실행"""
        print("🚀 뉴스 수집 시작...")
        
        results = {}
        
        # 뉴스 수집 실행
        news_items = await self.collectors['news'].run()
        results['news'] = news_items
        
        # 통계 정보 생성
        stats = self.generate_collection_stats(results)
        
        print(f"✅ 총 {len(news_items)}개 뉴스 수집 완료")
        
        return {
            'news_items': news_items,
            'stats': stats,
            'collection_time': datetime.now().isoformat(),
            'total_count': len(news_items)
        }
    
    async def collect_by_source(self, source: str) -> List[Dict[str, Any]]:
        """특정 소스에서만 뉴스 수집"""
        if source not in ['yna', 'hankyung', 'maeil', 'edaily']:
            raise ValueError(f"지원되지 않는 뉴스 소스: {source}")
        
        collector = self.collectors['news']
        
        if source == 'yna':
            return await collector.collect_yna_news()
        elif source == 'hankyung':
            return await collector.collect_hankyung_news()
        elif source == 'maeil':
            return await collector.collect_maeil_news()
        elif source == 'edaily':
            return await collector.collect_edaily_news()
    
    def generate_collection_stats(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """수집 통계 정보 생성"""
        news_items = results.get('news', [])
        
        # 소스별 통계
        source_stats = {}
        for news in news_items:
            source = news.get('raw_source', 'unknown')
            if source not in source_stats:
                source_stats[source] = 0
            source_stats[source] += 1
        
        # 카테고리별 통계
        category_stats = {}
        for news in news_items:
            category = news.get('category', '일반뉴스')
            if category not in category_stats:
                category_stats[category] = 0
            category_stats[category] += 1
        
        # 감성 분석 통계
        sentiment_stats = {'positive': 0, 'negative': 0, 'neutral': 0}
        importance_stats = {'high': 0, 'medium': 0, 'low': 0}
        
        for news in news_items:
            # 감성 분석
            sentiment = news.get('sentiment_score', 0)
            if sentiment > 0.1:
                sentiment_stats['positive'] += 1
            elif sentiment < -0.1:
                sentiment_stats['negative'] += 1
            else:
                sentiment_stats['neutral'] += 1
            
            # 중요도 분석
            importance = news.get('importance_score', 0.5)
            if importance >= 0.7:
                importance_stats['high'] += 1
            elif importance >= 0.4:
                importance_stats['medium'] += 1
            else:
                importance_stats['low'] += 1
        
        # 종목 언급 통계
        stock_mentions = {}
        for news in news_items:
            stock_codes = news.get('stock_mentions', '')
            if stock_codes:
                codes = stock_codes.split(',')
                for code in codes:
                    code = code.strip()
                    if code:
                        stock_mentions[code] = stock_mentions.get(code, 0) + 1
        
        # 가장 많이 언급된 종목 상위 10개
        top_stocks = sorted(stock_mentions.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_news': len(news_items),
            'by_source': source_stats,
            'by_category': category_stats,
            'sentiment_distribution': sentiment_stats,
            'importance_distribution': importance_stats,
            'top_mentioned_stocks': top_stocks,
            'collection_sources': ['yna', 'hankyung', 'maeil', 'edaily']
        }
    
    async def run_scheduled_collection(self, interval_minutes: int = 60):
        """주기적인 뉴스 수집 실행"""
        while True:
            try:
                print(f"🕐 주기적 뉴스 수집 시작 ({interval_minutes}분 간격)")
                await self.run_all_collectors()
                
                # 다음 수집까지 대기
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                print(f"❌ 주기적 뉴스 수집 실패: {e}")
                # 5분 후 재시도
                await asyncio.sleep(300)
    
    def get_collection_summary(self) -> Dict[str, Any]:
        """수집 요약 정보"""
        return {
            'available_sources': ['yna', 'hankyung', 'maeil', 'edaily'],
            'source_names': {
                'yna': '연합뉴스',
                'hankyung': '한국경제',
                'maeil': '매일경제',
                'edaily': '이데일리'
            },
            'categories': [
                '시장동향', '실적공시', '기업공시', '금융정책', '산업동향', '해외증시', '일반뉴스'
            ],
            'supported_features': [
                '제목 및 내용 수집',
                '종목 코드 및 명 추출',
                '감성 분석',
                '중요도 평가',
                '카테고리 분류',
                '중복 제거'
            ]
        }

# 실행 예시
async def main():
    """테스트 실행"""
    config = {
        'request_delay': 1.0
    }
    
    manager = NewsCollectionManager(config)
    
    # 전체 뉴스 수집
    results = await manager.run_all_collectors()
    
    print("📊 뉴스 수집 결과:")
    print(f"  총 뉴스 수: {results['total_count']}개")
    
    stats = results['stats']
    print("  소스별:")
    for source, count in stats['by_source'].items():
        print(f"    {source}: {count}개")
    
    print("  카테고리별:")
    for category, count in stats['by_category'].items():
        print(f"    {category}: {count}개")
    
    print("  감성 분포:")
    for sentiment, count in stats['sentiment_distribution'].items():
        print(f"    {sentiment}: {count}개")
    
    print(f"  최상위 언급 종목: {stats['top_mentioned_stocks'][:5]}")

if __name__ == "__main__":
    asyncio.run(main())