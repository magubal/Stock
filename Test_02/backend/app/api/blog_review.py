"""
Blog Review API - 투자자 블로그 정리 대시보드 엔드포인트
GET  /posts          - 날짜별 글 리스트
GET  /posts/{id}     - 글 상세 + 요약
PUT  /posts/{id}/summary - 요약 수정/저장
GET  /posts/{id}/image   - 캡처 이미지 서빙
GET  /bloggers       - 블로거 목록
GET  /dates          - 수집된 날짜 목록
"""

import os
import shutil
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, UploadFile, File
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
    """Background task: RSS수집 → 캡처 → DB저장 (run_blog.py 사용)."""
    # Ensure data dir exists
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Create absolute paths
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    script_path = base_dir / "scripts" / "blog_monitor" / "run_blog.py"
    # venv Python 사용 (시스템 Python에는 sqlalchemy 없음)
    venv_python = base_dir / "backend" / "venv" / "Scripts" / "python.exe"
    python_cmd = str(venv_python) if venv_python.exists() else sys.executable

    # Write PID into lock file
    with open(LOCK_FILE, "w") as f:
        f.write("running")

    try:
        with open(base_dir / LOG_FILE, "w", encoding="utf-8") as out_file:
            process = subprocess.Popen(
                [python_cmd, str(script_path), "--skip-ai"],
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
async def get_collection_status(db: Session = Depends(get_db)):
    """현재 블로그 수집 프로세스의 파싱 상태 반환 + idle 시 오늘 수집 건수"""
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    log_file_path = base_dir / LOG_FILE

    if not LOCK_FILE.exists():
        # 오늘 수집 건수 조회
        kst = timezone(timedelta(hours=9))
        today = datetime.now(kst).strftime("%Y-%m-%d")
        today_count = svc.get_today_count(db, today)
        if today_count > 0:
            message = f"오늘 {today_count}건 수집완료"
        else:
            message = "수집 대기"
        return {"status": "idle", "message": message, "today_count": today_count}

    status_msg = "수집 진행 중..."
    current = 0
    total = 0
    if log_file_path.exists():
        try:
            with open(log_file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # [PROGRESS] 마커에서 진행률 파싱 (마지막 것 사용)
                for line in reversed(lines[-30:]):
                    stripped = line.strip()
                    m = re.match(r"\[PROGRESS]\s+(\d+)/(\d+)", stripped)
                    if m:
                        current = int(m.group(1))
                        total = int(m.group(2))
                        if total == 0:
                            status_msg = "RSS 스캔 중..."
                        elif current >= total:
                            status_msg = f"수집 완료 처리 중... ({current}/{total})"
                        else:
                            status_msg = f"수집 중 ({current}/{total})"
                        break
        except Exception:
            pass

    result = {"status": "running", "message": status_msg}
    if total > 0:
        result["current"] = current
        result["total"] = total
    return result


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


def _get_attachment_dir(post_id: int, detail: dict) -> Path:
    """첨부 파일 저장 대상 OS 폴더 추출 헬퍼"""
    date_str = None
    
    # 1. image_path에서 YYYY-MM-DD 추출 시도 (예: "data/naver_blog_data/2026-02-21/블로거_글/...")
    if detail.get("image_path"):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", detail["image_path"])
        if m:
            date_str = m.group(1)
            
    # 2. image_path에 없으면 collected_at에서 추출
    if not date_str and detail.get("collected_at"):
        date_str = detail["collected_at"][:10]
        
    # 3. 최후의 보루: 오늘 날짜
    if not date_str:
        date_str = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
        
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    return base_dir / "data" / "naver_blog_data" / date_str / f"{post_id}_첨부"

@router.get("/posts/{post_id}/attachments")
async def get_attachments(post_id: int, db: Session = Depends(get_db)):
    """첨부 파일 목록 동적 스캔 반환"""
    detail = svc.get_post_detail(db, post_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Post not found")
        
    target_dir = _get_attachment_dir(post_id, detail)
    files = []
    if target_dir.exists() and target_dir.is_dir():
        for filename in os.listdir(target_dir):
            if os.path.isfile(target_dir / filename):
                files.append({
                    "name": filename,
                    "url": f"/api/v1/blog-review/posts/{post_id}/attachments/{filename}"
                })
                
    return {"attachments": files}


@router.post("/posts/{post_id}/attachments")
async def upload_attachment(post_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """새로운 첨부 파일 업로드"""
    detail = svc.get_post_detail(db, post_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Post not found")
        
    target_dir = _get_attachment_dir(post_id, detail)
    target_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = target_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"message": "success", "filename": file.filename}


@router.get("/posts/{post_id}/attachments/{filename}")
async def download_attachment(post_id: int, filename: str, db: Session = Depends(get_db)):
    """첨부 파일 다운로드/서빙"""
    detail = svc.get_post_detail(db, post_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Post not found")
        
    target_dir = _get_attachment_dir(post_id, detail)
    file_path = target_dir / filename
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
        
    # Content-Disposition 헤더 세팅을 위해 FileResponse 대신 직접 파일 리턴 (미디어타입 추론)
    return FileResponse(str(file_path), filename=filename)


@router.delete("/posts/{post_id}/attachments/{filename}")
async def delete_attachment(post_id: int, filename: str, db: Session = Depends(get_db)):
    """첨부 파일 삭제"""
    detail = svc.get_post_detail(db, post_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Post not found")
        
    target_dir = _get_attachment_dir(post_id, detail)
    file_path = target_dir / filename
    
    if file_path.exists() and file_path.is_file():
        os.remove(file_path)
        return {"message": "deleted"}
    else:
        raise HTTPException(status_code=404, detail="File not found")
