#!/usr/bin/env python3
"""
기존 블로그 수집 데이터 재캡처(JPG→PDF) + DB sync 통합 스크립트

Usage:
    python scripts/recapture_and_sync.py                # 전체 실행 (재캡처 + DB sync)
    python scripts/recapture_and_sync.py --sync-only    # DB sync만 (재캡처 skip)
    python scripts/recapture_and_sync.py --dry-run      # 실제 실행 없이 대상 목록만 출력
    python scripts/recapture_and_sync.py --date 2026-02-10  # 특정 날짜만
"""

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "backend" / "stock_research.db"
DATA_DIR = ROOT / "data" / "naver_blog_data"

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


def scan_sidecar_files(date_filter=None):
    """JSON sidecar 파일 스캔 → 재캡처/sync 대상 목록 반환."""
    targets = []

    for folder in sorted(DATA_DIR.iterdir()):
        if not folder.is_dir():
            continue
        folder_name = folder.name
        # YYYY-MM-DD 형식만
        if not (len(folder_name) == 10 and folder_name[4] == '-' and folder_name[7] == '-'):
            continue
        # backup 폴더 제외
        if 'backup' in folder_name:
            continue
        # 날짜 필터
        if date_filter and folder_name != date_filter:
            continue

        for json_file in sorted(folder.glob("*.json")):
            # daily_summary.json 등 제외
            if json_file.stem.startswith("daily_"):
                continue

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

            link = meta.get("link", "")
            if not link:
                continue

            # 현재 이미지 파일 확인
            image_file = meta.get("image_file", "")
            base_name = json_file.stem  # e.g., "daybyday_001"

            has_pdf = (folder / f"{base_name}.pdf").exists()
            has_jpg = (folder / f"{base_name}.jpg").exists()

            targets.append({
                "date_folder": folder_name,
                "folder_path": folder,
                "json_file": json_file,
                "base_name": base_name,
                "meta": meta,
                "link": link,
                "has_pdf": has_pdf,
                "has_jpg": has_jpg,
                "needs_recapture": not has_pdf,
            })

    return targets


def recapture_jpgs(targets, dry_run=False):
    """JPG만 있는 항목을 PDF로 재캡처."""
    needs = [t for t in targets if t["needs_recapture"]]
    if not needs:
        print("[RECAPTURE] 재캡처 대상 없음 (모두 PDF 보유)")
        return

    print(f"[RECAPTURE] {len(needs)}건 PDF 재캡처 대상")

    if dry_run:
        for t in needs:
            print(f"  {t['date_folder']}/{t['base_name']}: {t['meta'].get('title', '')[:40]}")
        return

    from playwright.sync_api import sync_playwright

    success = 0
    fail = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 2000},
            device_scale_factor=2,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )
        page = context.new_page()

        for i, t in enumerate(needs, 1):
            pdf_path = t["folder_path"] / f"{t['base_name']}.pdf"
            title = t['meta'].get('title', 'N/A')[:40]
            print(f"\n  [{i}/{len(needs)}] {t['date_folder']}/{t['base_name']} - {title}")

            try:
                text, size_kb = capture_pdf(page, t["link"], pdf_path)

                # JSON sidecar 업데이트
                t["meta"]["image_file"] = f"{t['base_name']}.pdf"
                t["meta"]["file_size_mb"] = round(size_kb / 1024, 2)
                with open(t["json_file"], 'w', encoding='utf-8') as f:
                    json.dump(t["meta"], f, ensure_ascii=False, indent=2)

                t["has_pdf"] = True
                t["text_content"] = text
                t["size_kb"] = size_kb
                success += 1
                print(f"    OK: {pdf_path.name} ({size_kb}KB)")

            except Exception as e:
                fail += 1
                print(f"    FAIL: {e}")

        page.close()
        context.close()
        browser.close()

    print(f"\n[RECAPTURE DONE] Success: {success}, Failed: {fail}")


def sync_to_db(targets, dry_run=False):
    """JSON sidecar → blog_posts DB sync (최신 수집 날짜 기준 dedup)."""
    # 같은 link가 여러 날짜 폴더에 존재 → 최신 date_folder의 것만 유지
    dedup = {}
    for t in targets:
        link = t["meta"].get("link", "")
        if not link:
            continue
        existing = dedup.get(link)
        if existing is None or t["date_folder"] > existing["date_folder"]:
            dedup[link] = t

    unique_targets = list(dedup.values())
    print(f"\n[DB SYNC] 전체 {len(targets)}건 → dedup {len(unique_targets)}건 (중복 {len(targets) - len(unique_targets)}건 제거)")

    if dry_run:
        for t in unique_targets:
            print(f"  {t['date_folder']}/{t['base_name']}: {t['meta'].get('title', '')[:40]}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # 기존 blog_posts 전부 삭제 (run_blog.py가 만든 잘못된 데이터)
    cur.execute("DELETE FROM blog_posts")
    # blog_summaries도 정리 (외래키 참조)
    cur.execute("DELETE FROM blog_summaries")
    conn.commit()
    print("[DB SYNC] 기존 blog_posts/blog_summaries 클리어")

    inserted = 0
    for t in unique_targets:
        meta = t["meta"]
        blogger = meta.get("blogger", "")
        title = meta.get("title", "")
        link = meta.get("link", "")
        pub_date = meta.get("pub_date", "")
        collected_date = meta.get("collected_date", "")

        # 이미지 경로 결정
        if t["has_pdf"]:
            image_file = f"{t['base_name']}.pdf"
        elif t["has_jpg"]:
            image_file = f"{t['base_name']}.jpg"
        else:
            image_file = None

        image_path = None
        image_size_kb = 0
        if image_file:
            full_image = t["folder_path"] / image_file
            if full_image.exists():
                image_path = str(full_image.relative_to(ROOT)).replace("\\", "/")
                image_size_kb = int(full_image.stat().st_size / 1024)

        # text_content (재캡처에서 추출된 것 또는 None)
        text_content = t.get("text_content")

        # pub_date 파싱
        pub_dt = None
        if pub_date:
            try:
                from email.utils import parsedate_to_datetime
                pub_dt = parsedate_to_datetime(pub_date).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pub_dt = None

        # collected_at 파싱 (SQLAlchemy는 공백 구분자 사용 → T 대신 공백)
        collected_at = collected_date if collected_date else f"{t['date_folder']} 09:00:00"
        collected_at = collected_at.replace("T", " ")

        cur.execute("""
            INSERT INTO blog_posts (blogger, title, link, pub_date, collected_at,
                                    image_path, image_size_kb, text_content, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            blogger, title, link,
            pub_dt, collected_at,
            image_path, image_size_kb,
            text_content, "COLLECTOR"
        ))
        inserted += 1

    conn.commit()
    conn.close()
    print(f"[DB SYNC DONE] {inserted}건 등록 완료")


def main():
    parser = argparse.ArgumentParser(description="블로그 데이터 재캡처 + DB sync")
    parser.add_argument("--sync-only", action="store_true", help="DB sync만 (재캡처 skip)")
    parser.add_argument("--dry-run", action="store_true", help="실제 실행 없이 대상만 출력")
    parser.add_argument("--date", type=str, help="특정 날짜만 (YYYY-MM-DD)")
    args = parser.parse_args()

    print("=" * 60)
    print("블로그 데이터 재캡처 + DB sync")
    print("=" * 60)

    # 1) 스캔
    targets = scan_sidecar_files(date_filter=args.date)
    print(f"\n[SCAN] JSON sidecar {len(targets)}건 발견")

    pdf_count = sum(1 for t in targets if t["has_pdf"])
    jpg_only = sum(1 for t in targets if not t["has_pdf"] and t["has_jpg"])
    print(f"  PDF 보유: {pdf_count}건")
    print(f"  JPG만 (재캡처 필요): {jpg_only}건")

    # 2) 재캡처 (JPG → PDF)
    if not args.sync_only:
        recapture_jpgs(targets, dry_run=args.dry_run)

    # 3) DB sync
    sync_to_db(targets, dry_run=args.dry_run)

    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
