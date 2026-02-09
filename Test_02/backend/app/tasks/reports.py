from celery import current_app
from ..database import SessionLocal
from ..services.report_service import ReportCollectionService
from ..collectors.report_manager import ReportCollectorManager

@current_app.task(bind=True, max_retries=3)
def collect_all_reports(self, extract_pdf: bool = False):
    """모든 리포트 수집 태스크"""
    try:
        # 데이터베이스 세션 생성
        db = SessionLocal()
        
        try:
            # 서비스 초기화
            service = ReportCollectionService(db)
            
            # 리포트 수집 실행
            result = service.collect_reports(extract_pdf=extract_pdf)
            
            return {
                'status': 'success',
                'total_collected': result.get('total_collected', 0),
                'saved_to_db': result.get('saved_to_db', 0),
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
def collect_specific_brokerage_reports(self, brokerage: str):
    """특정 증권사 리포트 수집 태스크"""
    try:
        db = SessionLocal()
        
        try:
            service = ReportCollectionService(db)
            manager = ReportCollectorManager()
            
            # 특정 증권사만 수집
            if brokerage == 'kiwoom':
                reports = await manager.collect_kiwoom_reports()
            elif brokerage == 'miraeasset':
                reports = await manager.collect_miraeasset_reports()
            elif brokerage == 'kbsec':
                reports = await manager.collect_kbsec_reports()
            elif brokerage == 'nhqv':
                reports = await manager.collect_nhqv_reports()
            else:
                raise ValueError(f"지원되지 않는 증권사: {brokerage}")
            
            # 데이터베이스 저장
            saved_count = 0
            for report_data in reports:
                if await service.save_report_to_db(report_data):
                    saved_count += 1
            
            return {
                'status': 'success',
                'brokerage': brokerage,
                'total_collected': len(reports),
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
            'brokerage': brokerage,
            'error': str(exc),
            'task_id': self.request.id,
            'retries': self.request.retries
        }

@current_app.task
def analyze_report_content(report_id: int):
    """리포트 내용 분석 태스크"""
    try:
        db = SessionLocal()
        
        try:
            # TODO: 리포트 내용 분석 로직
            # from ..models import ResearchReport
            # from ..analyzers.content_analyzer import ContentAnalyzer
            # 
            # report = db.query(ResearchReport).filter(ResearchReport.id == report_id).first()
            # if not report:
            #     raise ValueError(f"리포트를 찾을 수 없습니다: {report_id}")
            # 
            # analyzer = ContentAnalyzer()
            # analysis_result = analyzer.analyze(report.content)
            # 
            # # 분석 결과 저장
            # report.sentiment_score = analysis_result.get('sentiment_score')
            # report.importance_score = analysis_result.get('importance_score')
            # report.stock_mentions = analysis_result.get('stock_mentions', [])
            # db.commit()
            
            return {
                'status': 'success',
                'report_id': report_id,
                'sentiment_score': 0.5,  # 임시 값
                'importance_score': 0.8,
                'stock_mentions': ['005930']  # 임시 값
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        return {
            'status': 'failed',
            'report_id': report_id,
            'error': str(exc)
        }