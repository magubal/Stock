from typing import List, Dict, Any
from datetime import datetime
import asyncio
from ..collectors.news_manager import NewsCollectionManager

class NewsService:
    """뉴스 서비스"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.news_manager = NewsCollectionManager()
    
    async def collect_news(self, source: str = None) -> Dict[str, Any]:
        """뉴스 수집 실행"""
        try:
            if source:
                # 특정 소스만 수집
                news_items = await self.news_manager.collect_by_source(source)
                results = {
                    'news_items': news_items,
                    'total_count': len(news_items),
                    'source': source
                }
            else:
                # 전체 소스 수집
                results = await self.news_manager.run_all_collectors()
            
            # 데이터베이스에 저장
            saved_count = 0
            for news_data in results.get('news_items', []):
                if await self.save_news_to_db(news_data):
                    saved_count += 1
            
            return {
                'success': True,
                'total_collected': results.get('total_count', 0),
                'saved_to_db': saved_count,
                'collection_time': results.get('collection_time'),
                'stats': results.get('stats', {}),
                'source': source
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'collection_time': datetime.now().isoformat(),
                'source': source
            }
    
    async def save_news_to_db(self, news_data: Dict[str, Any]) -> bool:
        """뉴스를 데이터베이스에 저장"""
        try:
            # TODO: SQLAlchemy 모델 사용하여 저장
            # from ..models import News, DataSource
            # 
            # # 데이터 소스 확인 또는 생성
            # source_name = news_data.get('source_name', 'Unknown')
            # data_source = self.db.query(DataSource).filter(
            #     DataSource.name == source_name
            # ).first()
            # 
            # if not data_source:
            #     data_source = DataSource(
            #         name=source_name,
            #         type='news',
            #         url=news_data.get('url', ''),
            #         is_active=True
            #     )
            #     self.db.add(data_source)
            #     self.db.commit()
            #     self.db.refresh(data_source)
            # 
            # # 뉴스 기사 저장
            # news = News(
            #     source_id=data_source.id,
            #     title=news_data['title'],
            #     content=news_data['content'],
            #     url=news_data['url'],
            #     published_at=news_data['published_at'],
            #     author=news_data.get('author', ''),
            #     sentiment_score=news_data.get('sentiment_score'),
            #     importance_score=news_data.get('importance_score'),
            #     stock_mentions=news_data.get('stock_mentions')
            # )
            # 
            # self.db.add(news)
            # self.db.commit()
            
            print(f"💾 뉴스 저장: {news_data['title'][:30]}...")
            return True
            
        except Exception as e:
            print(f"❌ 뉴스 저장 실패: {e}")
            self.db.rollback()
            return False
    
    async def get_news_by_id(self, news_id: str) -> dict | None:
        """뉴스 ID로 단건 조회"""
        # TODO: DB 조회 구현
        # news = self.db.query(News).filter(News.id == int(news_id)).first()
        # return self._news_to_dict(news) if news else None
        return None

    async def get_recent_news(self, limit: int = 10, since: datetime = None) -> list:
        """최근 뉴스 조회 (since 이후)"""
        # TODO: DB 조회 구현
        # query = self.db.query(News)
        # if since:
        #     query = query.filter(News.published_at >= since)
        # return [self._news_to_dict(n) for n in query.order_by(News.published_at.desc()).limit(limit).all()]
        return []

    async def get_news(self,
                      source: str = None,
                      category: str = None,
                      limit: int = 50,
                      hours: int = 24) -> List[Dict[str, Any]]:
        """뉴스 목록 조회"""
        try:
            # TODO: 데이터베이스에서 뉴스 목록 조회
            # from ..models import News, DataSource
            # from sqlalchemy import and_, desc
            # 
            # # 시간 범위 설정
            # since = datetime.now() - timedelta(hours=hours)
            # 
            # query = self.db.query(News).join(DataSource).filter(
            #     News.published_at >= since
            # )
            # 
            # # 필터링
            # if source:
            #     query = query.filter(DataSource.name.like(f'%{source}%'))
            # if category:
            #     query = query.filter(News.category == category)
            # 
            # # 정렬 및 제한
            # news_items = query.order_by(desc(News.published_at)).limit(limit).all()
            # 
            # return [self._news_to_dict(news) for news in news_items]
            
            # 임시 데이터 반환
            return [
                {
                    'id': 1,
                    'title': '삼성전자, 4분기 실적 시장 기대 상회',
                    'content': '삼성전자가 4분기 실적 발표에서...',
                    'source_name': '연합뉴스',
                    'category': '실적공시',
                    'sentiment_score': 0.3,
                    'importance_score': 0.8,
                    'published_at': datetime.now(),
                    'url': 'https://example.com/news/1'
                }
            ]
            
        except Exception as e:
            print(f"❌ 뉴스 조회 실패: {e}")
            return []
    
    def _news_to_dict(self, news) -> Dict[str, Any]:
        """SQLAlchemy 모델을 딕셔너리로 변환"""
        return {
            'id': news.id,
            'source_id': news.source_id,
            'title': news.title,
            'content': news.content,
            'url': news.url,
            'published_at': news.published_at.isoformat(),
            'author': news.author,
            'sentiment_score': news.sentiment_score,
            'importance_score': news.importance_score,
            'stock_mentions': news.stock_mentions,
            'created_at': news.created_at.isoformat()
        }
    
    async def get_news_by_importance(self, hours: int = 24) -> List[Dict[str, Any]]:
        """중요도 높은 뉴스 조회"""
        return await self.get_news(
            limit=20,
            hours=hours
        )  # TODO: importance_score 기준 정렬 추가
    
    async def get_news_by_sentiment(self, sentiment: str = 'positive', hours: int = 24) -> List[Dict[str, Any]]:
        """감성별 뉴스 조회"""
        # TODO: 감성 필터링 로직 구현
        return await self.get_news(
            limit=20,
            hours=hours
        )
    
    async def get_news_by_stock(self, stock_code: str = None, hours: int = 24) -> List[Dict[str, Any]]:
        """종목 관련 뉴스 조회"""
        try:
            # TODO: 종목 코드로 뉴스 필터링
            # from ..models import News
            # from sqlalchemy import or_
            # 
            # since = datetime.now() - timedelta(hours=hours)
            # 
            # query = self.db.query(News).filter(
            #     and_(
            #         News.published_at >= since,
            #         or_(
            #             News.stock_mentions.like(f'%{stock_code}%'),
            #             News.title.like(f'%{stock_code}%'),
            #             News.content.like(f'%{stock_code}%')
            #         )
            #     )
            # )
            # 
            # news_items = query.order_by(News.importance_score.desc()).limit(20).all()
            # 
            # return [self._news_to_dict(news) for news in news_items]
            
            return await self.get_news(limit=20, hours=hours)
            
        except Exception as e:
            print(f"❌ 종목 관련 뉴스 조회 실패: {e}")
            return []
    
    async def get_news_stats(self, hours: int = 24) -> Dict[str, Any]:
        """뉴스 통계 정보"""
        try:
            # TODO: 데이터베이스에서 통계 정보 조회
            # from ..models import News, DataSource
            # from sqlalchemy import func, and_
            # 
            # since = datetime.now() - timedelta(hours=hours)
            # 
            # stats = {}
            # 
            # # 전체 뉴스 수
            # total_news = self.db.query(func.count(News.id)).filter(
            #     News.published_at >= since
            # ).scalar()
            # 
            # # 소스별 뉴스 수
            # source_stats = self.db.query(
            #     DataSource.name,
            #     func.count(News.id)
            # ).join(News).filter(
            #     News.published_at >= since
            # ).group_by(DataSource.name).all()
            # 
            # # 감성 분석 통계
            # sentiment_stats = self.db.query(
            #     func.avg(News.sentiment_score),
            #     func.count(News.id)
            # ).filter(News.published_at >= since).first()
            # 
            # # 중요도 통계
            # importance_stats = self.db.query(
            #     func.avg(News.importance_score),
            #     func.count(News.id)
            # ).filter(News.published_at >= since).first()
            # 
            # stats['total_news'] = total_news
            # stats['by_source'] = dict(source_stats)
            # stats['avg_sentiment'] = float(sentiment_stats[0]) if sentiment_stats[0] else 0.0
            # stats['avg_importance'] = float(importance_stats[0]) if importance_stats[0] else 0.0
            # 
            # # 최신 수집 시간
            # latest_collection = self.db.query(
            #     func.max(News.created_at)
            # ).scalar()
            # 
            # stats['latest_collection'] = latest_collection.isoformat() if latest_collection else None
            
            # 임시 통계
            stats = {
                'total_news': 0,
                'by_source': {
                    '연합뉴스': 0,
                    '한국경제': 0,
                    '매일경제': 0,
                    '이데일리': 0
                },
                'avg_sentiment': 0.0,
                'avg_importance': 0.0,
                'latest_collection': None,
                'time_range': f'{hours}시간'
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ 뉴스 통계 조회 실패: {e}")
            return {}
    
    async def search_news(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """뉴스 검색"""
        try:
            # TODO: 키워드로 뉴스 검색
            # from ..models import News
            # from sqlalchemy import or_
            # 
            # query = self.db.query(News).filter(
            #     or_(
            #         News.title.like(f'%{keyword}%'),
            #         News.content.like(f'%{keyword}%')
            #     )
            # )
            # 
            # news_items = query.order_by(News.published_at.desc()).limit(limit).all()
            # 
            # return [self._news_to_dict(news) for news in news_items]
            
            return []
            
        except Exception as e:
            print(f"❌ 뉴스 검색 실패: {e}")
            return []