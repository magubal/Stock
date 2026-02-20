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
    python run_blog.py --date 2026-02-18  # 특정 날짜 폴더 데이터 DB 등록
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


def collect_and_capture(skip_ai=False):
    """RSS → 캡처 → DB 저장 → (옵션) AI 분석."""
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

    try:
        for b in bloggers:
            print(f"\n  [{b['display_name']}] Fetching RSS...")
            try:
                entries = parse_rss_feed(b["rss_url"])
            except Exception as e:
                print(f"    [SKIP] RSS error: {e}")
                continue

            for entry in entries:
                link = entry.get("link", "")
                if not link:
                    continue

                # 중복 체크
                existing = session.query(BlogPost).filter(BlogPost.link == link).first()
                if existing:
                    continue

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
                total_new += 1
                print(f"    + {title[:50]}")

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

            session.commit()
    finally:
        if capture_session:
            capture_session.__exit__(None, None, None)

    session.close()
    print(f"\n[DONE] New: {total_new}, AI analyzed: {total_analyzed}")


def register_from_files(session, date_str):
    """기존 파일 데이터를 DB에 등록 (fallback)."""
    date_dir = BLOG_DATA_DIR / date_str
    if not date_dir.exists():
        print(f"[WARN] No data dir: {date_dir}")
        return

    inserted = 0
    for json_file in sorted(date_dir.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        link = data.get("link", "")
        if not link:
            continue

        existing = session.query(BlogPost).filter(BlogPost.link == link).first()
        if existing:
            continue

        stem = json_file.stem
        image_path = None
        image_size_kb = 0
        for ext in (".pdf", ".jpg", ".jpeg", ".png"):
            candidate = date_dir / f"{stem}{ext}"
            if candidate.exists():
                image_path = str(candidate.relative_to(ROOT)).replace("\\", "/")
                image_size_kb = int(candidate.stat().st_size / 1024)
                break

        pub_date = None
        raw_date = data.get("pub_date", "")
        if raw_date:
            try:
                from email.utils import parsedate_to_datetime
                pub_date = parsedate_to_datetime(raw_date)
            except Exception:
                pass

        collected_at = None
        raw_collected = data.get("collected_date", "")
        if raw_collected:
            try:
                collected_at = datetime.fromisoformat(raw_collected)
            except Exception:
                pass

        post = BlogPost(
            blogger=data.get("blogger", "unknown"),
            title=data.get("title", stem),
            link=link,
            pub_date=pub_date,
            text_content=None,
            image_path=image_path,
            image_size_kb=image_size_kb,
            collected_at=collected_at,
            source="COLLECTOR",
        )
        session.add(post)
        inserted += 1

    session.commit()
    print(f"[FILE] Registered {inserted} posts from {date_dir.name}")


def main():
    parser = argparse.ArgumentParser(description="Blog Monitor Batch")
    parser.add_argument("--skip-ai", action="store_true", help="Skip AI analysis")
    parser.add_argument("--date", type=str, help="Register file data for specific date (YYYY-MM-DD)")
    args = parser.parse_args()

    if args.date:
        session = Session()
        register_from_files(session, args.date)
        session.close()
    else:
        collect_and_capture(skip_ai=args.skip_ai)


if __name__ == "__main__":
    main()
