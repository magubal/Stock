#!/usr/bin/env python3
"""
리포트 수집 테스트 스크립트
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.collectors.report_manager import ReportCollectorManager

async def test_report_collection():
    """리포트 수집 테스트"""
    print("🚀 증권사 리포트 수집 테스트 시작...")
    
    # 수집기 매니저 초기화
    config = {
        'extract_pdf_content': False,  # PDF 내용 추적은 비활성화
        'request_delay': 1.0
    }
    
    manager = ReportCollectorManager(config)
    
    try:
        # 리포트 수집 실행
        results = await manager.run_all_collectors()
        
        print(f"\n📊 수집 결과 요약:")
        print(f"  총 수집된 리포트: {results['total_count']}개")
        print(f"  수집 시간: {results['collection_time']}")
        
        # 증권사별 수집 결과
        brokerage_stats = {}
        for report in results['reports']:
            brokerage = report.get('brokerage', '알 수 없음')
            brokerage_stats[brokerage] = brokerage_stats.get(brokerage, 0) + 1
        
        print(f"\n🏢 증권사별 수집 결과:")
        for brokerage, count in brokerage_stats.items():
            print(f"  {brokerage}: {count}개")
        
        # 샘플 리포트 정보 출력
        print(f"\n📋 수집된 리포트 샘플:")
        for i, report in enumerate(results['reports'][:3]):
            print(f"  {i+1}. [{report.get('brokerage')}] {report.get('title', '')[:50]}...")
        
        return results
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return None

async def test_individual_collectors():
    """개별 수집기 테스트"""
    print("\n🔍 개별 수집기 테스트 시작...")
    
    from backend.app.collectors.research_report import ResearchReportCollector
    
    collector = ResearchReportCollector()
    
    # 키움증권만 테스트
    print("  키움증권 리포트 수집 테스트...")
    kiwoom_reports = await collector.collect_kiwoom_reports()
    print(f"  ✅ 키움증권: {len(kiwoom_reports)}개 수집됨")
    
    if kiwoom_reports:
        print(f"  📄 샘플: {kiwoom_reports[0].get('title', '')[:50]}...")

if __name__ == "__main__":
    # 간단한 테스트 실행
    print("Stock Research ONE - 리포트 수집기 테스트")
    print("=" * 50)
    
    # 개별 수집기 테스트
    asyncio.run(test_individual_collectors())
    
    # 전체 수집기 테스트
    asyncio.run(test_report_collection())
    
    print("\n✅ 테스트 완료!")