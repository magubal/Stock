from typing import List, Dict, Any
from datetime import datetime, timedelta
import asyncio
from .research_report import ResearchReportCollector
from .pdf_extractor import PDFReportCollector

class ReportCollectorManager:
    """리포트 수집 매니저"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.collectors = {
            'research_reports': ResearchReportCollector(config),
            'pdf_content': PDFReportCollector(config)
        }
    
    async def run_all_collectors(self) -> Dict[str, List[Dict[str, Any]]]:
        """모든 리포트 수집기 실행"""
        print("🚀 리포트 수집 시작...")
        
        results = {}
        
        # 1단계: 기본 리포트 목록 수집
        print("📋 리포트 목록 수집 중...")
        research_reports = await self.collectors['research_reports'].run()
        results['research_reports'] = research_reports
        
        # 2단계: PDF 상세 내용 수집 (필요시)
        if self.config.get('extract_pdf_content', False):
            print("📄 PDF 상세 내용 수집 중...")
            pdf_contents = await self.collectors['pdf_content'].run()
            results['pdf_contents'] = pdf_contents
        
        # 3단계: 결과 병합 및 정리
        merged_reports = self.merge_reports(
            results.get('research_reports', []),
            results.get('pdf_contents', [])
        )
        
        print(f"✅ 총 {len(merged_reports)}개 리포트 수집 완료")
        
        return {
            'reports': merged_reports,
            'raw_results': results,
            'collection_time': datetime.now().isoformat(),
            'total_count': len(merged_reports)
        }
    
    def merge_reports(self, basic_reports: List[Dict], pdf_contents: List[Dict]) -> List[Dict]:
        """기본 리포트와 PDF 내용 병합"""
        merged = []
        
        # PDF 내용을 맵으로 변환
        pdf_map = {content.get('pdf_url'): content for content in pdf_contents}
        
        for report in basic_reports:
            pdf_url = report.get('pdf_url')
            pdf_content = pdf_map.get(pdf_url) if pdf_url else None
            
            merged_report = {
                **report,
                'detailed_content': pdf_content.get('content') if pdf_content else '',
                'summary': pdf_content.get('summary') if pdf_content else '',
                'content_extracted': pdf_content is not None
            }
            
            merged.append(merged_report)
        
        return merged
    
    async def run_scheduled_collection(self, interval_hours: int = 6):
        """주기적인 리포트 수집 실행"""
        while True:
            try:
                print(f"🕐 주기적 리포트 수집 시작 ({interval_hours}시간 간격)")
                await self.run_all_collectors()
                
                # 다음 수집까지 대기
                await asyncio.sleep(interval_hours * 3600)
                
            except Exception as e:
                print(f"❌ 주기적 수집 실패: {e}")
                # 1시간 후 재시도
                await asyncio.sleep(3600)
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """수집 통계 정보"""
        return {
            'available_collectors': list(self.collectors.keys()),
            'last_collection': None,  # TODO: DB에서 마지막 수집 시간 조회
            'total_reports_collected': 0,  # TODO: DB에서 총 리포트 수 조회
            'supported_brokerages': [
                '키움증권', '미래에셋증권', 'KB증권', 'NH투자증권'
            ]
        }

# 실행 예시
async def main():
    """테스트 실행"""
    config = {
        'extract_pdf_content': False,  # 초기에는 비활성화
        'request_delay': 1.0
    }
    
    manager = ReportCollectorManager(config)
    
    # 단일 실행
    results = await manager.run_all_collectors()
    
    print("📊 수집 결과:")
    for brokerage, reports in {
        '키움증권': [],
        '미래에셋증권': [],
        'KB증권': [],
        'NH투자증권': []
    }.items():
        count = len([r for r in results['reports'] if r.get('brokerage') == brokerage])
        print(f"  {brokerage}: {count}개")
    
    print(f"  총계: {results['total_count']}개")

if __name__ == "__main__":
    asyncio.run(main())