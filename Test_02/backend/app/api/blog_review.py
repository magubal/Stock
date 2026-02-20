"""
Blog Review API - 투자자 블로그 정리 대시보드 엔드포인트
GET  /posts          - 날짜별 글 리스트
GET  /posts/{id}     - 글 상세 + 요약
PUT  /posts/{id}/summary - 요약 수정/저장
GET  /posts/{id}/image   - 캡처 이미지 서빙
GET  /bloggers       - 블로거 목록
GET  /dates          - 수집된 날짜 목록
"""

import subprocess
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from pathlib import Path

from ..database import get_db
from ..services import blog_review_service as svc

router = APIRouter(prefix="/api/v1/blog-review", tags=["blog-review"])

LOCK_FILE = Path("data/collection.lock")
LOG_FILE = Path("data/blog_collection.log")

class SummaryUpdate(BaseModel):
    summary: Optional[str] = None
    viewpoint: Optional[str] = None
    implications: Optional[str] = None


import time

def run_collection_process():
    """Background task to run the python script and manage the lock."""
    # Ensure data dir exists
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Create absolute paths
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    scripts_dir = base_dir / "scripts"
    script_path = scripts_dir / "naver_blog_collector.py"
    
    # Write PID into lock file
    with open(LOCK_FILE, "w") as f:
        f.write("running")

    try:
        with open(base_dir / LOG_FILE, "w", encoding="utf-8") as out_file:
            process = subprocess.Popen(
                ["python", str(script_path)],
                stdout=out_file,
                stderr=subprocess.STDOUT,
                cwd=str(base_dir)
            )
            process.communicate() # wait for finish
    finally:
        # Guarantee lock is removed
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()


@router.post("/collect")
async def trigger_collection(background_tasks: BackgroundTasks):
    """수동으로 네이버 블로그 수집기 실행 (Lock 방어)"""
    if LOCK_FILE.exists():
        # Check if lock is stale (older than 30 mins)
        mtime = LOCK_FILE.stat().st_mtime
        if time.time() - mtime > 1800:
            LOCK_FILE.unlink()
        else:
            raise HTTPException(status_code=409, detail="A collection process is already running.")
            
    background_tasks.add_task(run_collection_process)
    return {"message": "Collection started"}


@router.get("/collect/status")
async def get_collection_status():
    """현재 블로그 수집 프로세스의 파싱 상태 반환"""
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    log_file_path = base_dir / LOG_FILE
    
    if not LOCK_FILE.exists():
        return {"status": "idle", "message": "대기 중"}
        
    status_msg = "수집 진행 중..."
    if log_file_path.exists():
        try:
            with open(log_file_path, "r", encoding="utf-8") as f:
                # Read last 10 lines
                lines = f.readlines()
                if lines:
                    last_lines = lines[-10:]
                    # Find a meaningful last line
                    for line in reversed(last_lines):
                        line = line.strip()
                        if line:
                            status_msg = line
                            break
        except Exception:
            pass
            
    return {"status": "running", "message": status_msg}


@router.get("/posts")
async def get_posts(
    date: str = Query(None, description="YYYY-MM-DD"),
    blogger: str = Query(None, description="블로거명 필터"),
    db: Session = Depends(get_db),
):
    """날짜별 블로그 글 리스트."""
    if not date:
        kst = timezone(timedelta(hours=9))
        date = datetime.now(kst).strftime("%Y-%m-%d")

    posts = svc.get_posts_by_date(db, date, blogger)
    return {"date": date, "total": len(posts), "posts": posts}


@router.get("/posts/{post_id}")
async def get_post_detail(post_id: int, db: Session = Depends(get_db)):
    """글 상세 + 최신 요약."""
    result = svc.get_post_detail(db, post_id)
    if not result:
        raise HTTPException(status_code=404, detail="Post not found")
    return result


@router.put("/posts/{post_id}/summary")
async def update_summary(
    post_id: int, body: SummaryUpdate, db: Session = Depends(get_db)
):
    """요약 수정/저장."""
    result = svc.update_summary(db, post_id, body.dict(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="Post not found")
    return result


@router.get("/posts/{post_id}/image")
async def get_post_image(post_id: int, db: Session = Depends(get_db)):
    """캡처 이미지 서빙."""
    detail = svc.get_post_detail(db, post_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Post not found")

    image_path = detail.get("image_path")
    if not image_path:
        raise HTTPException(status_code=404, detail="No image")

    resolved = svc.resolve_image_path(image_path)
    if not resolved:
        raise HTTPException(status_code=404, detail="Image not found")

    suffix = resolved.suffix.lower()
    if suffix == ".pdf":
        media = "application/pdf"
    elif suffix in (".jpg", ".jpeg"):
        media = "image/jpeg"
    elif suffix == ".png":
        media = "image/png"
    else:
        media = "application/octet-stream"
    return FileResponse(str(resolved), media_type=media)


@router.post("/posts/{post_id}/analyze")
async def analyze_post(post_id: int, db: Session = Depends(get_db)):
    """AI 재분석 (Claude text/vision)."""
    detail = svc.get_post_detail(db, post_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Post not found")

    result = svc.run_ai_analysis(db, post_id, detail)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/bloggers")
async def get_bloggers(db: Session = Depends(get_db)):
    """블로거 목록 + 글 수."""
    return svc.get_bloggers(db)


@router.get("/dates")
async def get_dates(
    limit: int = Query(30, description="최근 N일"),
    db: Session = Depends(get_db),
):
    """수집된 날짜 목록."""
    return svc.get_available_dates(db, limit)
