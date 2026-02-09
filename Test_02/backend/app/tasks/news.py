from celery import current_app
from ..database import SessionLocal
from ..services.news_service import NewsService
from ..collectors.news_manager import NewsCollectionManager

@current_app.task(bind=True, max_retries=3)
def collect_all_news(self):
    """모든 뉴스 수집 태스크"""
    try:
        # 데이터베이스 세션 생성
        db = SessionLocal()
        
        try:
            # 서비스 초기화
            service = NewsService(db)
            
            # 뉴스 수집 실행
            result = service.collect_news()
            
            return {
                'status': 'success',
                'total_collected': result.get('total_collected', 0),
                'saved_to_db': result.get('saved_to_db', 0),
                'stats': result.get('stats', {}),
                'task_id': self.request.id
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        # 재시도 로직
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {
            'status': 'failed',
            'error': str(exc),
            'task_id': self.request.id,
            'retries': self.request.retries
        }

@current_app.task(bind=True, max_retries=3)
def collect_specific_news_source(self, source: str):
    """특정 뉴스 소스 수집 태스크"""
    try:
        db = SessionLocal()
        
        try:
            service = NewsService(db)
            manager = NewsCollectionManager()
            
            # 특정 소스만 수집
            if source not in ['yna', 'hankyung', 'maeil', 'edaily']:
                raise ValueError(f"지원되지 않는 뉴스 소스: {source}")
            
            # 개별 소스 수집
            news_items = await manager.collect_by_source(source)
            
            # 데이터베이스 저장
            saved_count = 0
            for news_data in news_items:
                if await service.save_news_to_db(news_data):
                    saved_count += 1
            
            return {
                'status': 'success',
                'source': source,
                'total_collected': len(news_items),
                'saved_to_db': saved_count,
                'task_id': self.request.id
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {
            'status': 'failed',
            'source': source,
            'error': str(exc),
            'task_id': self.request.id,
            'retries': self.request.retries
        }

@current_app.task
def analyze_news_sentiment(news_id: int):
    """뉴스 감성 분석 태스크"""
    try:
        db = SessionLocal()
        
        try:
            # TODO: 뉴스 감성 분석 로직
            # from ..models import News
            # from ..analyzers.sentiment_analyzer import SentimentAnalyzer
            # 
            # news = db.query(News).filter(News.id == news_id).first()
            # if not news:
            #     raise ValueError(f"뉴스를 찾을 수 없습니다: {news_id}")
            # 
            # analyzer = SentimentAnalyzer()
            # sentiment_result = analyzer.analyze(news.content)
            # 
            # # 분석 결과 저장
            # news.sentiment_score = sentiment_result.get('score')
            # news.importance_score = sentiment_result.get('importance')
            # db.commit()
            
            return {
                'status': 'success',
                'news_id': news_id,
                'sentiment_score': 0.3,  # 임시 값
                'importance_score': 0.7
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        return {
            'status': 'failed',
            'news_id': news_id,
            'error': str(exc)
        }

@current_app.task
def extract_news_entities(news_id: int):
    """뉴스 개체명 추출 태스크"""
    try:
        db = SessionLocal()
        
        try:
            # TODO: 개체명 추출 로직
            # from ..models import News
            # from ..analyzers.entity_extractor import EntityExtractor
            # 
            # news = db.query(News).filter(News.id == news_id).first()
            # if not news:
            #     raise ValueError(f"뉴스를 찾을 수 없습니다: {news_id}")
            # 
            # extractor = EntityExtractor()
            # entities = extractor.extract(f"{news.title} {news.content}")
            # 
            # # 추출 결과 저장
            # news.stock_mentions = ','.join(entities.get('stock_codes', []))
            # db.commit()
            
            return {
                'status': 'success',
                'news_id': news_id,
                'entities': {
                    'stock_codes': ['005930', '000660'],  # 임시 값
                    'companies': ['삼성전자', 'SK하이닉스'],
                    'people': [],
                    'locations': []
                }
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        return {
            'status': 'failed',
            'news_id': news_id,
            'error': str(exc)
        }