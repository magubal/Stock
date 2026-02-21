#!/usr/bin/env python3
"""
블로그 수집 배치 스크립트 (22:00 스케줄러용).
1) RSS 파싱 → 새 글 감지
2) Playwright 캡처 (이미지 + 텍스트 추출)
3) DB blog_posts INSERT
4) (옵션) Claude AI 요약 생성 → blog_summaries INSERT

Usage:
    python run_blog.py                 # 수집 + AI 분석
    python run_blog.py --skip-ai       # 수집만 (AI 분석 건너뜀)
"""
import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_PATH = ROOT / "backend" / "stock_research.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Session = sessionmaker(bind=engine)

from app.models.blog_post import BlogPost, BlogSummary

BLOG_DATA_DIR = ROOT / "data" / "naver_blog_data"
RSS_LIST_FILE = BLOG_DATA_DIR / "naver_bloger_rss_list.txt"
KST = timezone(timedelta(hours=9))
DEFAULT_DAYS = 3  # naver_blog_collector.py와 동일


def is_after_cutoff(pub_date_str: str, cutoff_dt: datetime):
    """pub_date가 cutoff_dt 이후인지 확인.

    Returns:
        (result, reason)
        - (True, "within") : N일 이내 (또는 DB 최신글 이후)
        - (True, "no_date") : pub_date 없음 → 수집 허용
        - (True, "parse_fail") : 파싱 실패 → 수집 허용
        - (False, "too_old") : 기준일 초과 → skip
    """
    if not pub_date_str or not pub_date_str.strip():
        return True, "no_date"
    try:
        from email.utils import parsedate_to_datetime
        pub_dt = parsedate_to_datetime(pub_date_str.strip())
        if pub_dt >= cutoff_dt:
            return True, "within"
        else:
            return False, "too_old"
    except Exception:
        return True, "parse_fail"


def load_bloggers():
    """RSS 목록에서 블로거 정보 로드.

    지원 포맷:
      1) URL # display_name   (기존 naver_bloger_rss_list.txt)
      2) naver_id,display_name,rss_url   (CSV)
    """
    bloggers = []
    if not RSS_LIST_FILE.exists():
        print(f"[WARN] RSS list not found: {RSS_LIST_FILE}")
        return bloggers

    for line in RSS_LIST_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if "," in line:
            # CSV: naver_id,display_name,rss_url
            parts = line.split(",")
            if len(parts) >= 3:
                bloggers.append({
                    "naver_id": parts[0].strip(),
                    "display_name": parts[1].strip(),
                    "rss_url": parts[2].strip(),
                })
        else:
            # URL # display_name
            parts = line.split("#")
            rss_url = parts[0].strip()
            display_name = parts[1].strip() if len(parts) > 1 else "unknown"
            # naver_id 추출: https://rss.blog.naver.com/{naver_id}
            naver_id = rss_url.rstrip("/").split("/")[-1] if rss_url else display_name
            bloggers.append({
                "naver_id": naver_id,
                "display_name": display_name,
                "rss_url": rss_url,
            })
    return bloggers


def collect_and_capture(skip_ai=False, days=DEFAULT_DAYS):
    """RSS → 캡처 → DB 저장 → (옵션) AI 분석.

    2-phase 구조:
      Phase 1: RSS 스캔 + 날짜필터 + dedup → 신규 목록 확정 (빠름)
      Phase 2: 캡처 + DB 저장 → [PROGRESS] 마커 출력 (느림)
    """
    bloggers = load_bloggers()
    if not bloggers:
        print("[ERROR] No bloggers configured")
        return

    session = Session()
    now = datetime.now(KST)
    today = now.strftime("%Y-%m-%d")

    print(f"[BLOG] Collecting for {today} ({len(bloggers)} bloggers)")

    # RSS parser (self-contained)
    def parse_rss_feed(rss_url):
        """RSS 피드 파싱 → [{title, link, published}, ...]"""
        import requests
        import xml.etree.ElementTree as ET
        feed_url = rss_url if rss_url.endswith(".xml") else rss_url + ".xml"
        resp = requests.get(feed_url, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        entries = []
        for item in root.find("channel").findall("item"):
            entries.append({
                "title": (item.findtext("title") or "").strip(),
                "link": (item.findtext("link") or "").strip(),
                "published": (item.findtext("pubDate") or "").strip(),
            })
        return entries

    # ── Phase 1: RSS 스캔 + dedup (캡처 없이 빠르게) ──
    from sqlalchemy import func
    pending_items = []  # [(blogger_dict, entry_dict), ...]
    now_utc = datetime.now(timezone.utc)

    for b in bloggers:
        print(f"\n  [{b['display_name']}] RSS 스캔 중...")
        
        # 블로거별 최신발행일 조회하여 동적 필터링 적용
        max_pub = session.query(func.max(BlogPost.pub_date)).filter(BlogPost.blogger == b["display_name"]).scalar()
        base_cutoff = now_utc - timedelta(days=days)
        if max_pub:
            if max_pub.tzinfo is None:
                max_pub = max_pub.replace(tzinfo=timezone.utc)
            cutoff_dt = max(base_cutoff, max_pub)
        else:
            cutoff_dt = base_cutoff

        try:
            entries = parse_rss_feed(b["rss_url"])
        except Exception as e:
            print(f"    [SKIP] RSS error: {e}")
            continue

        for entry in entries:
            link = entry.get("link", "")
            if not link:
                continue

            # 동적 날짜 필터 적용
            pub_date_str = entry.get("published", "")
            within, reason = is_after_cutoff(pub_date_str, cutoff_dt)
            if not within:
                continue
            if reason in ("no_date", "parse_fail"):
                print(f"    [WARN] pubDate {reason}: {entry.get('title', '')[:40]}")

            existing = session.query(BlogPost).filter(BlogPost.link == link).first()
            if existing:
                continue
            pending_items.append((b, entry))

    total_to_capture = len(pending_items)
    print(f"\n[PROGRESS] 0/{total_to_capture}")
    sys.stdout.flush()

    if total_to_capture == 0:
        print("\n[DONE] New: 0, AI analyzed: 0")
        session.close()
        return

    # ── Phase 2: 캡처 + DB 저장 ──
    # Import capture session
    try:
        from final_body_capture import BlogCaptureSession
    except ImportError:
        print("[WARN] final_body_capture not importable. Skipping capture.")
        BlogCaptureSession = None

    total_new = 0
    total_analyzed = 0

    capture_session = None
    if BlogCaptureSession:
        capture_session = BlogCaptureSession()
        capture_session.__enter__()

    last_blogger_name = None
    try:
        for b, entry in pending_items:
            try:
                last_blogger_name = b["display_name"]
                link = entry.get("link", "")
                title = entry.get("title", "제목 없음")
                pub_date = None
                raw_date = entry.get("published", "")
                if raw_date:
                    try:
                        from email.utils import parsedate_to_datetime
                        pub_date = parsedate_to_datetime(raw_date)
                    except Exception:
                        pass

                text_content = None
                image_path = None
                image_size_kb = 0

                # Capture
                if capture_session:
                    try:
                        cap = capture_session.capture(link, b["display_name"])
                        if cap.get("success"):
                            image_path = str(Path(cap["file_path"]).relative_to(ROOT)).replace("\\", "/")
                            image_size_kb = int(cap.get("file_size_mb", 0) * 1024)
                            text_content = cap.get("text_content")
                    except Exception as e:
                        print(f"    [WARN] Capture error: {e}")

                post = BlogPost(
                    blogger=b["display_name"],
                    title=title,
                    link=link,
                    pub_date=pub_date,
                    text_content=text_content,
                    image_path=image_path,
                    image_size_kb=image_size_kb,
                    collected_at=now,
                    source="COLLECTOR",
                )
                session.add(post)
                session.flush()

                # AI analysis
                if not skip_ai and (text_content or image_path):
                    try:
                        from blog_analyzer import analyze_post
                        result = analyze_post(
                            blogger=b["display_name"],
                            title=title,
                            text_content=text_content,
                            image_path=image_path,
                        )
                        if "error" not in result:
                            summary_obj = BlogSummary(
                                post_id=post.id,
                                summary=result.get("summary", ""),
                                viewpoint=result.get("viewpoint", ""),
                                implications=result.get("implications", ""),
                                ai_model=result.get("ai_model", "claude-text"),
                            )
                            session.add(summary_obj)
                            total_analyzed += 1
                            print(f"      AI: {result.get('ai_model', 'unknown')}")
                        else:
                            print(f"      AI skip: {result['error']}")
                    except Exception as e:
                        print(f"      AI error: {e}")
                
                # 개별 단위 성공 시 바로 커밋 (Resilience 확보)
                session.commit()
                
                total_new += 1
                print(f"[PROGRESS] {total_new}/{total_to_capture}")
                print(f"    + {title[:50]}")
                sys.stdout.flush()

            except Exception as inner_e:
                session.rollback()
                print(f"    [ERROR] Failed to process post '{entry.get('title', '')}': {inner_e}")
                sys.stdout.flush()
                continue

    finally:
        if capture_session:
            capture_session.__exit__(None, None, None)

    session.close()
    print(f"\n[DONE] New: {total_new}, AI analyzed: {total_analyzed}")


def main():
    parser = argparse.ArgumentParser(description="Blog Monitor Batch")
    parser.add_argument("--skip-ai", action="store_true", help="Skip AI analysis")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS,
                        help=f"최근 N일 이내 발행 글만 수집 (0=필터없음, 기본={DEFAULT_DAYS})")
    args = parser.parse_args()

    collect_and_capture(skip_ai=args.skip_ai, days=args.days)


if __name__ == "__main__":
    main()
