from typing import List, Dict, Any
from datetime import datetime
import asyncio
from ..collectors.report_manager import ReportCollectorManager

class ReportCollectionService:
    """리포트 수집 서비스"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.collector_manager = ReportCollectorManager()
    
    async def collect_reports(self, extract_pdf: bool = False) -> Dict[str, Any]:
        """리포트 수집 실행"""
        try:
            # 수집기 실행
            config = {'extract_pdf_content': extract_pdf}
            self.collector_manager.config.update(config)
            
            results = await self.collector_manager.run_all_collectors()
            
            # 데이터베이스에 저장
            saved_count = 0
            for report_data in results['reports']:
                if await self.save_report_to_db(report_data):
                    saved_count += 1
            
            return {
                'success': True,
                'total_collected': results['total_count'],
                'saved_to_db': saved_count,
                'collection_time': results['collection_time']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'collection_time': datetime.now().isoformat()
            }
    
    async def save_report_to_db(self, report_data: Dict[str, Any]) -> bool:
        """리포트를 데이터베이스에 저장"""
        try:
            # TODO: SQLAlchemy 모델 사용하여 저장
            # from ..models import ResearchReport
            # 
            # report = ResearchReport(
            #     title=report_data['title'],
            #     content=report_data['content'],
            #     pdf_url=report_data['pdf_url'],
            #     brokerage=report_data['brokerage'],
            #     target_price=report_data['target_price'],
            #     recommendation=report_data['recommendation'],
            #     published_at=report_data['published_at'],
            #     stock_code=report_data['stock_code'],
            #     stock_name=report_data['stock_name']
            # )
            # 
            # self.db.add(report)
            # self.db.commit()
            
            print(f"💾 리포트 저장: {report_data['title'][:30]}...")
            return True
            
        except Exception as e:
            print(f"❌ 리포트 저장 실패: {e}")
            self.db.rollback()
            return False
    
    async def get_reports(self, brokerage: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """리포트 목록 조회"""
        try:
            # TODO: 데이터베이스에서 리포트 목록 조회
            # from ..models import ResearchReport
            # 
            # query = self.db.query(ResearchReport)
            # if brokerage:
            #     query = query.filter(ResearchReport.brokerage == brokerage)
            # 
            # reports = query.order_by(ResearchReport.published_at.desc()).limit(limit).all()
            # 
            # return [self._report_to_dict(report) for report in reports]
            
            # 임시 데이터 반환
            return [
                {
                    'id': 1,
                    'title': '삼성전자 투자의견 상향',
                    'brokerage': '키움증권',
                    'recommendation': 'buy',
                    'target_price': 85000,
                    'published_at': datetime.now()
                }
            ]
            
        except Exception as e:
            print(f"❌ 리포트 조회 실패: {e}")
            return []
    
    def _report_to_dict(self, report) -> Dict[str, Any]:
        """SQLAlchemy 모델을 딕셔너리로 변환"""
        return {
            'id': report.id,
            'title': report.title,
            'content': report.content,
            'pdf_url': report.pdf_url,
            'brokerage': report.brokerage,
            'author': report.author,
            'target_price': report.target_price,
            'recommendation': report.recommendation,
            'published_at': report.published_at.isoformat(),
            'stock_code': report.stock_code,
            'stock_name': report.stock_name,
            'created_at': report.created_at.isoformat()
        }
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """수집 통계 정보"""
        try:
            # TODO: 데이터베이스에서 통계 정보 조회
            # from ..models import ResearchReport
            # from sqlalchemy import func
            # 
            # stats = {}
            # 
            # # 전체 리포트 수
            # total_count = self.db.query(func.count(ResearchReport.id)).scalar()
            # 
            # # 증권사별 리포트 수
            # brokerage_stats = self.db.query(
            #     ResearchReport.brokerage,
            #     func.count(ResearchReport.id)
            # ).group_by(ResearchReport.brokerage).all()
            # 
            # # 최신 수집 시간
            # latest_collection = self.db.query(
            #     func.max(ResearchReport.created_at)
            # ).scalar()
            # 
            # stats['total_reports'] = total_count
            # stats['by_brokerage'] = dict(brokerage_stats)
            # stats['latest_collection'] = latest_collection.isoformat() if latest_collection else None
            
            # 임시 통계
            stats = {
                'total_reports': 0,
                'by_brokerage': {
                    '키움증권': 0,
                    '미래에셋증권': 0,
                    'KB증권': 0,
                    'NH투자증권': 0
                },
                'latest_collection': None
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ 통계 조회 실패: {e}")
            return {}