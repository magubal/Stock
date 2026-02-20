#!/usr/bin/env python3
"""
기존 blog_posts의 JPG를 PDF로 재캡처.
URL 재방문 → PDF 생성 → DB image_path 업데이트.

Usage:
    python backfill_pdf.py                    # 전체 (limit 50)
    python backfill_pdf.py --date 2026-02-18  # 특정 날짜만
    python backfill_pdf.py --id 93            # 특정 ID만
    python backfill_pdf.py --limit 100        # 최대 N건
    python backfill_pdf.py --all              # JPG인 포스트 전부
"""
import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "backend" / "stock_research.db"
DATA_DIR = ROOT / "data" / "naver_blog_data"

# final_body_capture.py의 함수들을 직접 import
sys.path.insert(0, str(ROOT / "scripts"))
from final_body_capture import (
    strip_rss_params,
    open_iframe_or_self,
    auto_scroll,
    detect_article_selector,
    extract_text,
    PRUNE_JS,
)


def capture_pdf(page, url, out_path):
    """단일 URL → PDF 캡처 + 텍스트 추출."""
    clean_url = strip_rss_params(url)
    open_iframe_or_self(page, clean_url)
    auto_scroll(page, step=1500, pause=0.12, loops=400)
    time.sleep(2.0)

    text_content = extract_text(page)

    sel = detect_article_selector(page)
    ok = page.evaluate(PRUNE_JS, sel or "body")
    if not ok:
        page.evaluate("window.scrollTo(0,0)")
    time.sleep(0.8)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    page.emulate_media(media="print")
    page.pdf(
        path=str(out_path),
        print_background=True,
        format="A4",
        margin={"top": "12mm", "right": "10mm",
                "bottom": "12mm", "left": "10mm"},
        prefer_css_page_size=True,
        scale=1.0,
    )

    file_size_kb = int(os.path.getsize(out_path) / 1024)
    return text_content, file_size_kb


def backfill(date_filter=None, id_filter=None, limit=50, do_all=False):
    """image_path가 .jpg/.png인 포스트를 PDF로 재캡처."""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    query = """SELECT id, blogger, title, link, image_path
               FROM blog_posts WHERE link IS NOT NULL"""
    params = []

    if id_filter:
        query += " AND id = ?"
        params.append(id_filter)
    elif date_filter:
        query += " AND (date(collected_at) = ? OR date(pub_date) = ?)"
        params.extend([date_filter, date_filter])
    else:
        # image_path가 .jpg/.png이거나 NULL인 건
        query += " AND (image_path LIKE '%.jpg' OR image_path LIKE '%.png' OR image_path IS NULL)"

    query += " ORDER BY id"
    if not do_all:
        query += " LIMIT ?"
        params.append(limit)

    rows = cur.execute(query, params).fetchall()

    if not rows:
        print("[BACKFILL-PDF] No posts need PDF backfill.")
        conn.close()
        return

    print(f"[BACKFILL-PDF] Found {len(rows)} posts to re-capture as PDF")

    from playwright.sync_api import sync_playwright

    success_count = 0
    fail_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 2000},
            device_scale_factor=2,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )
        page = context.new_page()

        for row in rows:
            post_id, blogger, title, link, old_path = row
            print(f"\n  [{post_id}] {blogger} - {title[:50]}")

            # PDF 저장 경로 결정
            if old_path:
                # 기존 이미지 경로 기반: 확장자만 .pdf로
                old_full = ROOT / old_path.replace("\\", "/")
                pdf_path = old_full.with_suffix(".pdf")
            else:
                # image_path가 NULL인 경우: 날짜 폴더에 저장
                cur2 = conn.cursor()
                row2 = cur2.execute(
                    "SELECT date(collected_at) FROM blog_posts WHERE id = ?",
                    (post_id,),
                ).fetchone()
                date_str = row2[0] if row2 and row2[0] else "unknown"
                save_dir = DATA_DIR / date_str
                save_dir.mkdir(parents=True, exist_ok=True)
                # 순번
                existing = list(save_dir.glob(f"{blogger}_*.pdf"))
                seq = len(existing) + 1
                pdf_path = save_dir / f"{blogger}_{seq:03d}.pdf"

            try:
                text, size_kb = capture_pdf(page, link, pdf_path)

                rel_path = str(pdf_path.relative_to(ROOT)).replace("\\", "/")

                updates = ["image_path = ?", "image_size_kb = ?"]
                values = [rel_path, size_kb]

                if text:
                    updates.append("text_content = ?")
                    values.append(text)

                values.append(post_id)
                cur.execute(
                    f"UPDATE blog_posts SET {', '.join(updates)} WHERE id = ?",
                    values,
                )
                conn.commit()
                success_count += 1
                print(f"    OK: {pdf_path.name} ({size_kb}KB)")
                if text:
                    print(f"    Text: {len(text)} chars")

            except Exception as e:
                fail_count += 1
                print(f"    FAIL: {e}")

        page.close()
        context.close()
        browser.close()

    conn.close()
    print(f"\n[DONE] Success: {success_count}, Failed: {fail_count}, Total: {len(rows)}")


def main():
    parser = argparse.ArgumentParser(description="Blog PDF backfill")
    parser.add_argument("--date", type=str, help="Filter by date (YYYY-MM-DD)")
    parser.add_argument("--id", type=int, help="Filter by post ID")
    parser.add_argument("--limit", type=int, default=50, help="Max posts to process")
    parser.add_argument("--all", action="store_true", help="Process all matching posts")
    args = parser.parse_args()

    backfill(
        date_filter=args.date,
        id_filter=args.id,
        limit=args.limit,
        do_all=args.all,
    )


if __name__ == "__main__":
    main()
