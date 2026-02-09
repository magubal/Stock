from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..services.report_service import ReportCollectionService
from ..schemas import ResearchReport, ResearchReportCreate

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

# 의존성 주입
def get_report_service(db: Session = Depends(get_db)) -> ReportCollectionService:
    return ReportCollectionService(db)

@router.get("/", response_model=List[ResearchReport])
async def get_reports(
    brokerage: Optional[str] = Query(None, description="증권사 필터링"),
    limit: int = Query(50, ge=1, le=1000, description="최대 개수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    service: ReportCollectionService = Depends(get_report_service)
):
    """리포트 목록 조회"""
    try:
        reports = await service.get_reports(brokerage=brokerage, limit=limit)
        return reports
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"리포트 조회 실패: {str(e)}")

@router.get("/stats")
async def get_collection_stats(
    service: ReportCollectionService = Depends(get_report_service)
):
    """수집 통계 정보"""
    try:
        stats = await service.get_collection_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")

@router.post("/collect")
async def trigger_collection(
    extract_pdf: bool = Query(False, description="PDF 상세 내용 추출 여부"),
    service: ReportCollectionService = Depends(get_report_service)
):
    """리포트 수집 트리거"""
    try:
        result = await service.collect_reports(extract_pdf=extract_pdf)
        
        if result['success']:
            return {
                "message": "리포트 수집 완료",
                "total_collected": result['total_collected'],
                "saved_to_db": result['saved_to_db'],
                "collection_time": result['collection_time']
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"리포트 수집 실패: {result['error']}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"수집 실패: {str(e)}")

@router.get("/{report_id}", response_model=ResearchReport)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db)
):
    """특정 리포트 상세 조회"""
    try:
        # TODO: 데이터베이스에서 특정 리포트 조회
        # from ..models import ResearchReport
        # report = db.query(ResearchReport).filter(ResearchReport.id == report_id).first()
        # 
        # if not report:
        #     raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다")
        # 
        # return report
        
        # 임시 응답
        raise HTTPException(status_code=501, detail="아직 구현되지 않았습니다")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")

@router.delete("/{report_id}")
async def delete_report(
    report_id: int,
    db: Session = Depends(get_db)
):
    """리포트 삭제"""
    try:
        # TODO: 데이터베이스에서 리포트 삭제
        # from ..models import ResearchReport
        # report = db.query(ResearchReport).filter(ResearchReport.id == report_id).first()
        # 
        # if not report:
        #     raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다")
        # 
        # db.delete(report)
        # db.commit()
        # 
        # return {"message": "리포트가 삭제되었습니다"}
        
        raise HTTPException(status_code=501, detail="아직 구현되지 않았습니다")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"삭제 실패: {str(e)}")

@router.get("/brokerages/list")
async def get_supported_brokerages():
    """지원되는 증권사 목록"""
    return {
        "brokerages": [
            {
                "code": "kiwoom",
                "name": "키움증권",
                "supported": True,
                "collection_url": "https://www.kiwoom.com/h/invest/research/report/recommend.jspx"
            },
            {
                "code": "miraeasset",
                "name": "미래에셋증권", 
                "supported": True,
                "collection_url": "https://www.miraeasset.com/contents/research/researchList.jsp"
            },
            {
                "code": "kbsec",
                "name": "KB증권",
                "supported": True,
                "collection_url": "https://securities.kbfg.com/research/report/reportList.do"
            },
            {
                "code": "nhqv",
                "name": "NH투자증권",
                "supported": True,
                "collection_url": "https://www.nhqv.com/research/researchList.do"
            }
        ]
    }

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    service: ReportCollectionService = Depends(get_report_service)
):
    """대시보드 요약 정보"""
    try:
        stats = await service.get_collection_stats()
        latest_reports = await service.get_reports(limit=5)
        
        return {
            "total_reports": stats.get('total_reports', 0),
            "by_brokerage": stats.get('by_brokerage', {}),
            "latest_collection": stats.get('latest_collection'),
            "recent_reports": latest_reports,
            "summary": {
                "today_collected": 0,  # TODO: 오늘 수집된 리포트 수
                "weekly_avg": 0,       # TODO: 주평균 수집량
                "most_active": None     # TODO: 가장 활동적인 증권사
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대시보드 정보 조회 실패: {str(e)}")