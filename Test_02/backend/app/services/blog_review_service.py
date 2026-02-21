"""
Blog Review Service - 투자자 블로그 정리 비즈니스 로직
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func

from ..models.blog_post import BlogPost, BlogSummary

_BASE = Path(__file__).resolve().parent.parent.parent.parent  # project root


def get_posts_by_date(db: Session, date_str: str, blogger: str = None):
    """날짜별 블로그 글 리스트 조회."""
    # date_str -> 해당 날짜 범위
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return []

    # SQLite stores naive datetime strings — use naive comparison
    start = dt.replace(hour=0, minute=0, second=0)
    end = dt.replace(hour=23, minute=59, second=59)

    q = db.query(BlogPost).filter(
        BlogPost.collected_at >= start,
        BlogPost.collected_at <= end,
    )
    if blogger:
        q = q.filter(BlogPost.blogger == blogger)

    posts = q.order_by(BlogPost.blogger, BlogPost.pub_date.desc()).all()

    result = []
    for p in posts:
        latest = (
            db.query(BlogSummary)
            .filter(BlogSummary.post_id == p.id)
            .order_by(BlogSummary.created_at.desc())
            .first()
        )
        result.append({
            "id": p.id,
            "blogger": p.blogger,
            "title": p.title,
            "link": p.link,
            "pub_date": p.pub_date.isoformat() if p.pub_date else None,
            "has_summary": latest is not None,
            "is_edited": latest.is_edited if latest else False,
            "image_size_kb": p.image_size_kb,
            "source": p.source,
        })
    return result


def get_post_detail(db: Session, post_id: int):
    """글 상세 + 최신 요약 조회."""
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        return None

    latest = (
        db.query(BlogSummary)
        .filter(BlogSummary.post_id == post_id)
        .order_by(BlogSummary.created_at.desc())
        .first()
    )

    return {
        "id": post.id,
        "blogger": post.blogger,
        "title": post.title,
        "link": post.link,
        "pub_date": post.pub_date.isoformat() if post.pub_date else None,
        "text_content": post.text_content,
        "image_path": post.image_path,
        "image_size_kb": post.image_size_kb,
        "collected_at": post.collected_at.isoformat() if post.collected_at else None,
        "source": post.source,
        "summary": {
            "id": latest.id,
            "summary": latest.summary,
            "viewpoint": latest.viewpoint,
            "implications": latest.implications,
            "is_edited": latest.is_edited,
            "edited_at": latest.edited_at.isoformat() if latest.edited_at else None,
            "ai_model": latest.ai_model,
            "created_at": latest.created_at.isoformat() if latest.created_at else None,
        } if latest else None,
    }


def update_summary(db: Session, post_id: int, data: dict):
    """요약 수정/저장."""
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        return None

    latest = (
        db.query(BlogSummary)
        .filter(BlogSummary.post_id == post_id)
        .order_by(BlogSummary.created_at.desc())
        .first()
    )

    now = datetime.now(timezone(timedelta(hours=9)))

    if latest:
        latest.summary = data.get("summary", latest.summary)
        latest.viewpoint = data.get("viewpoint", latest.viewpoint)
        latest.implications = data.get("implications", latest.implications)
        latest.is_edited = True
        latest.edited_at = now
    else:
        latest = BlogSummary(
            post_id=post_id,
            summary=data.get("summary", ""),
            viewpoint=data.get("viewpoint", ""),
            implications=data.get("implications", ""),
            is_edited=True,
            edited_at=now,
            ai_model="manual",
        )
        db.add(latest)

    db.commit()
    db.refresh(latest)

    return {
        "id": latest.id,
        "post_id": post_id,
        "is_edited": latest.is_edited,
        "edited_at": latest.edited_at.isoformat() if latest.edited_at else None,
    }


def run_ai_analysis(db: Session, post_id: int, detail: dict):
    """AI 분석 실행 후 결과를 DB에 저장."""
    import sys
    sys.path.insert(0, str(_BASE / "scripts" / "blog_monitor"))
    try:
        from blog_analyzer import analyze_post
    except ImportError as e:
        return {"error": f"blog_analyzer import failed: {e}"}

    result = analyze_post(
        blogger=detail.get("blogger", ""),
        title=detail.get("title", ""),
        text_content=detail.get("text_content"),
        image_path=detail.get("image_path"),
    )

    if "error" in result:
        return result

    now = datetime.now(timezone(timedelta(hours=9)))
    summary_obj = BlogSummary(
        post_id=post_id,
        summary=result.get("summary", ""),
        viewpoint=result.get("viewpoint", ""),
        implications=result.get("implications", ""),
        is_edited=False,
        ai_model=result.get("ai_model", "claude-text"),
        created_at=now,
    )
    db.add(summary_obj)
    db.commit()
    db.refresh(summary_obj)

    return {
        "post_id": post_id,
        "summary": {
            "id": summary_obj.id,
            "summary": summary_obj.summary,
            "viewpoint": summary_obj.viewpoint,
            "implications": summary_obj.implications,
            "ai_model": summary_obj.ai_model,
        },
    }


def get_bloggers(db: Session):
    """블로거 목록 + 글 수."""
    rows = (
        db.query(BlogPost.blogger, sa_func.count(BlogPost.id))
        .group_by(BlogPost.blogger)
        .order_by(BlogPost.blogger)
        .all()
    )
    return [{"name": r[0], "count": r[1]} for r in rows]


def get_available_dates(db: Session, limit: int = 30):
    """수집된 날짜 목록 (최근 N일)."""
    rows = (
        db.query(sa_func.date(BlogPost.collected_at))
        .distinct()
        .order_by(sa_func.date(BlogPost.collected_at).desc())
        .limit(limit)
        .all()
    )
    return [str(r[0]) for r in rows if r[0]]


def get_today_count(db: Session, date_str: str) -> int:
    """오늘 수집된 블로그 글 수."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return 0
    start = dt.replace(hour=0, minute=0, second=0)
    end = dt.replace(hour=23, minute=59, second=59)
    return db.query(sa_func.count(BlogPost.id)).filter(
        BlogPost.collected_at >= start,
        BlogPost.collected_at <= end,
    ).scalar() or 0


def resolve_image_path(image_path: str) -> Path:
    """이미지 경로를 안전하게 resolve."""
    if not image_path:
        return None

    normalized = image_path.replace("\\", "/")
    if ".." in normalized:
        return None

    full = _BASE / normalized
    try:
        full.resolve().relative_to(_BASE.resolve())
    except ValueError:
        return None

    if not full.exists() or not full.is_file():
        return None

    if full.suffix.lower() not in (".pdf", ".jpg", ".jpeg", ".png", ".webp"):
        return None

    return full
