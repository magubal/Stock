#!/usr/bin/env python3
"""
블로그 포스트 텍스트 백필 스크립트.
text_content가 NULL인 기존 포스트를 재방문하여 텍스트 추출.

Usage:
    python backfill_text.py                    # 전체 NULL 포스트
    python backfill_text.py --date 2026-02-18  # 특정 날짜만
    python backfill_text.py --id 93            # 특정 ID만
    python backfill_text.py --limit 10         # 최대 N건
"""
import argparse
import sqlite3
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "backend" / "stock_research.db"

# Playwright text extraction (same logic as final_body_capture.py)
CONTENT_SELECTORS = [
    '.se-main-container',
    '#postViewArea',
    '.blogview_content',
    '.se_component_wrap',
    'article.se_component',
]

UNWANTED_SELECTORS = [
    '.u_likeit_list', '.u_likeit_count', '.u_bike_view',
    '.u_likeit_btns', '.u_likeit', '#recommend', '.recommend',
    '.social', '.share', '.sympathy_area',
    '.comment_area', '#comment', '.comment_list',
    '.comment_write', '.cmt_editor', '.cmt_persist',
    '.related', '.related_area', '.tag', '.tags',
    '.ad', '.ads', '.advertisement', '.adsbygoogle',
    '.header', '.footer', '.navi', '.navigation',
    '.menu', '.search', '.blog_category',
    'button', 'form', 'input', 'select', 'textarea',
    '.btn', '.button',
    'iframe', 'embed', 'object',
    '.se_oglink', '.og_container',
]


def extract_text_from_url(page, url):
    """Playwright page로 URL 방문하여 본문 텍스트 추출.

    전략: 데스크톱 네이버 블로그 → iframe#mainFrame 내부 진입 → 본문 텍스트 추출.
    모바일 버전보다 데스크톱 iframe이 전체 텍스트를 더 안정적으로 포함함.
    """
    try:
        # RSS 트래킹 파라미터 제거
        clean_url = url.split("?fromRss")[0] if "?fromRss" in url else url

        # 데스크톱 버전 접속 (모바일보다 본문 텍스트 완전성이 높음)
        page.goto(clean_url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2000)

        # 네이버 블로그 데스크톱: iframe#mainFrame 안에 본문 존재
        content_frame = None
        try:
            iframe_el = page.query_selector("iframe#mainFrame")
            if iframe_el:
                content_frame = iframe_el.content_frame()
                if content_frame:
                    content_frame.wait_for_load_state("domcontentloaded", timeout=10000)
                    page.wait_for_timeout(1500)
        except Exception as e:
            print(f"    [WARN] iframe access: {e}")

        target = content_frame if content_frame else page

        # 충분한 스크롤 (lazy-load 이미지/텍스트 트리거, 긴 포스트 대비 30회)
        for _ in range(30):
            target.evaluate("window.scrollBy(0, 1000)")
            time.sleep(0.1)
        target.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.5)

        # DOM 정리 후 텍스트 추출
        content_selectors_js = str(CONTENT_SELECTORS).replace("'", '"')
        unwanted_selectors_js = str(UNWANTED_SELECTORS).replace("'", '"')

        text_content = target.evaluate(f"""
            () => {{
                const contentSelectors = {content_selectors_js};
                const unwantedSelectors = {unwanted_selectors_js};

                let contentElement = null;
                for (let sel of contentSelectors) {{
                    const el = document.querySelector(sel);
                    if (el && el.offsetHeight > 50) {{
                        contentElement = el;
                        break;
                    }}
                }}

                if (!contentElement) contentElement = document.body;

                const clone = contentElement.cloneNode(true);
                unwantedSelectors.forEach(sel => {{
                    clone.querySelectorAll(sel).forEach(el => el.remove());
                }});

                // br → newline
                clone.querySelectorAll('br').forEach(br => {{
                    br.replaceWith('\\n');
                }});

                // block elements → newline before text
                const blocks = 'div,p,h1,h2,h3,h4,h5,h6,li,tr,blockquote,section,article,.se_component';
                clone.querySelectorAll(blocks).forEach(el => {{
                    el.insertAdjacentText('beforebegin', '\\n');
                }});

                let text = clone.textContent || '';
                // normalize: collapse 2+ newlines → single, trim each line
                text = text.split('\\n')
                    .map(line => line.replace(/\\u200B/g, '').trim())
                    .filter((line, i, arr) => line !== '' || (i > 0 && arr[i-1] !== ''))
                    .join('\\n')
                    .replace(/\\n{{3,}}/g, '\\n\\n')
                    .trim();
                return text.substring(0, 50000);
            }}
        """)

        if text_content and len(text_content) > 30:
            return text_content
        return None

    except Exception as e:
        print(f"    [ERROR] {e}")
        return None


def backfill(date_filter=None, id_filter=None, limit=50):
    """text_content가 NULL인 포스트를 재방문하여 텍스트 추출."""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    query = "SELECT id, blogger, title, link FROM blog_posts WHERE text_content IS NULL"
    params = []

    if id_filter:
        query += " AND id = ?"
        params.append(id_filter)
    elif date_filter:
        query += " AND (date(collected_at) = ? OR date(pub_date) = ?)"
        params.extend([date_filter, date_filter])

    query += " ORDER BY id LIMIT ?"
    params.append(limit)

    rows = cur.execute(query, params).fetchall()

    if not rows:
        print("[BACKFILL] No posts need text backfill.")
        conn.close()
        return

    print(f"[BACKFILL] Found {len(rows)} posts without text_content")

    from playwright.sync_api import sync_playwright

    updated = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1200, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )
        page = context.new_page()

        for row in rows:
            post_id, blogger, title, link = row
            print(f"\n  [{post_id}] {blogger} - {title[:50]}")
            print(f"    URL: {link}")

            text = extract_text_from_url(page, link)

            if text:
                cur.execute(
                    "UPDATE blog_posts SET text_content = ? WHERE id = ?",
                    (text, post_id),
                )
                conn.commit()
                updated += 1
                print(f"    OK: {len(text)} chars extracted")
                print(f"    Preview: {text[:100]}...")
            else:
                print(f"    SKIP: No text extracted")

        page.close()
        context.close()
        browser.close()

    conn.close()
    print(f"\n[DONE] Updated {updated}/{len(rows)} posts with text_content")


def main():
    parser = argparse.ArgumentParser(description="Blog text backfill")
    parser.add_argument("--date", type=str, help="Filter by date (YYYY-MM-DD)")
    parser.add_argument("--id", type=int, help="Filter by post ID")
    parser.add_argument("--limit", type=int, default=50, help="Max posts to process")
    args = parser.parse_args()

    backfill(date_filter=args.date, id_filter=args.id, limit=args.limit)


if __name__ == "__main__":
    main()
