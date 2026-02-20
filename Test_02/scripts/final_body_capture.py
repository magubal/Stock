#!/usr/bin/env python3
"""
블로그 본문 PDF 캡처 (v4.0) - A4 다페이지 PDF 출력
- 데스크톱 iframe 접근 → DOM pruning → page.pdf()
- 텍스트 추출은 pruning 전 수행 (block-aware)
- data/naver_blog_data/YYYY-MM-DD/blogger_NNN.pdf 저장

작성자: PSJ + Claude
업데이트: 2026-02-20
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

# 본문 컨테이너 셀렉터 (우선순위 순)
ARTICLE_SELECTORS = [
    ".se-main-container",
    "#postViewArea",
    "article.se_component",
    "article[data-role='post']",
    ".se-viewer",
    ".blogview_content",
    ".se_component_wrap",
]

# 텍스트 추출 시 제거할 요소
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

# DOM pruning JS (참조코드 기반)
PRUNE_JS = """
(sel) => {
  const el = document.querySelector(sel);
  if (!el) return false;

  // 이미지 지연로딩 해제
  document.querySelectorAll('img[data-src]').forEach(img => {
    img.src = img.getAttribute('data-src');
  });

  // body 자체가 선택된 경우 pruning 스킵 (스타일만 정리)
  if (el === document.body) {
    document.body.style.margin = '0';
    document.body.style.padding = '0';
    const css = `@media print { html, body { margin:0!important; padding:0!important; background:#fff!important; } img { max-width:100%!important; height:auto!important; } }`;
    const s = document.createElement('style');
    s.textContent = css;
    document.head.appendChild(s);
    window.scrollTo(0,0);
    return true;
  }

  // body 정리
  document.body.style.margin = '0';
  document.body.style.padding = '0';

  // 본문만 남기기
  Array.from(document.body.children).forEach(c => {
    if (!el.contains(c) && c !== el) c.remove();
  });

  // 본문을 body의 유일한 자식으로 이동
  if (el.parentElement !== document.body) {
    el.remove();
    document.body.innerHTML = "";
    document.body.appendChild(el);
  }

  // 폭/여백 정리
  el.style.maxWidth = '100%';
  el.style.margin = '0';
  el.style.padding = '0';

  // print용 CSS
  const css = `
    @media print {
      html, body { margin:0 !important; padding:0 !important; background:#fff !important; }
      * { visibility: visible !important; }
      a { color: inherit; text-decoration: none; }
      img { max-width: 100% !important; height: auto !important; }
    }`;
  const s = document.createElement('style');
  s.textContent = css;
  document.head.appendChild(s);

  window.scrollTo(0,0);
  return true;
}
"""


def strip_rss_params(url):
    """RSS 트래킹 파라미터 제거."""
    return url.split("?fromRss")[0] if "?fromRss" in url else url


def open_iframe_or_self(page, url):
    """데스크톱 네이버 블로그 접속 + iframe 내부 진입."""
    try:
        page.goto(url, wait_until="networkidle", timeout=60000)
    except PWTimeoutError:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)

    iframe = page.query_selector("iframe#mainFrame")
    if iframe:
        src = iframe.get_attribute("src")
        if src:
            # 상대 경로 → 절대 경로 변환
            if src.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(url)
                src = f"{parsed.scheme}://{parsed.netloc}{src}"
            if src.startswith("http"):
                try:
                    page.goto(src, wait_until="networkidle", timeout=60000)
                except PWTimeoutError:
                    page.goto(src, wait_until="domcontentloaded", timeout=60000)


def auto_scroll(page, step=1500, pause=0.12, loops=400):
    """스크롤하여 lazy-load 트리거. scrollY 변화 없으면 중단."""
    last = -1
    for _ in range(loops):
        page.evaluate(f"window.scrollBy(0,{step})")
        time.sleep(pause)
        cur = page.evaluate("window.scrollY")
        if cur == last:
            break
        last = cur
    page.evaluate("window.scrollTo(0,0)")


def detect_article_selector(page):
    """본문 컨테이너 셀렉터 자동 감지."""
    for sel in ARTICLE_SELECTORS:
        try:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                return sel
        except Exception:
            pass
    return None


def extract_text(page):
    """DOM pruning 전에 본문 텍스트를 block-aware로 추출."""
    content_selectors_js = json.dumps(ARTICLE_SELECTORS)
    unwanted_selectors_js = json.dumps(UNWANTED_SELECTORS)

    text_content = page.evaluate(f"""
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
            // normalize: collapse 2+ newlines, trim each line, remove zero-width spaces
            text = text.split('\\n')
                .map(line => line.replace(/\\u200B/g, '').trim())
                .filter((line, i, arr) => line !== '' || (i > 0 && arr[i-1] !== ''))
                .join('\\n')
                .replace(/\\n{{3,}}/g, '\\n\\n')
                .trim();
            return text.substring(0, 50000);
        }}
    """)
    return text_content if text_content and len(text_content) > 30 else None


class BlogCaptureSession:
    """브라우저를 재사용하는 캡처 세션 (PDF 버전)"""

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None

    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 2000},
            device_scale_factor=2,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def capture(self, blog_url: str, blogger_id: str) -> dict:
        """단일 블로그 글 캡처 → PDF + 텍스트"""
        result = {
            "success": False,
            "file_path": None,
            "file_size_mb": 0,
            "text_content": None,
            "message": ""
        }

        try:
            # 일자별 폴더 생성
            today = datetime.now().strftime('%Y-%m-%d')
            base_path = Path(__file__).resolve().parent.parent / "data" / "naver_blog_data"
            save_dir = base_path / today
            save_dir.mkdir(parents=True, exist_ok=True)

            # 순번 확인 (PDF + JPG 모두 카운트)
            existing_files = list(save_dir.glob(f"{blogger_id}_*.pdf")) + \
                             list(save_dir.glob(f"{blogger_id}_*.jpg"))
            sequence = len(existing_files) + 1

            filename = f"{blogger_id}_{sequence:03d}.pdf"
            final_path = save_dir / filename

            page = self.context.new_page()

            try:
                # Step 1: URL 정리 + 데스크톱 접속
                clean_url = strip_rss_params(blog_url)
                open_iframe_or_self(page, clean_url)

                # Step 2: auto_scroll (lazy-load 트리거, break 조건)
                auto_scroll(page, step=1500, pause=0.12, loops=400)
                time.sleep(2.0)

                # Step 3: 텍스트 추출 (pruning 전!)
                text_content = extract_text(page)
                result["text_content"] = text_content

                # Step 4: DOM pruning (PRUNE_JS)
                sel = detect_article_selector(page)
                ok = page.evaluate(PRUNE_JS, sel or "body")
                if not ok:
                    page.evaluate("window.scrollTo(0,0)")
                time.sleep(0.8)

                # Step 5: PDF 생성
                page.emulate_media(media="print")
                page.pdf(
                    path=str(final_path),
                    print_background=True,
                    format="A4",
                    margin={"top": "12mm", "right": "10mm",
                            "bottom": "12mm", "left": "10mm"},
                    prefer_css_page_size=True,
                    scale=1.0,
                )

                file_size = os.path.getsize(final_path) / 1024 / 1024

                result["success"] = True
                result["file_path"] = str(final_path)
                result["file_size_mb"] = round(file_size, 2)
                result["message"] = "PDF 캡처 완료"

            finally:
                page.close()

            return result

        except Exception as e:
            result["message"] = f"에러: {str(e)}"
            return result


# 기존 호환성을 위한 함수 (단일 캡처용)
def extract_body_only_capture(blog_url: str, blogger_id: str = "unknown") -> dict:
    """단일 블로그 글 캡처 (기존 호환)."""
    with BlogCaptureSession() as session:
        return session.capture(blog_url, blogger_id)


def main():
    """테스트 - 단건 PDF 캡처"""
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 60)
    print("블로그 본문 PDF 캡처 v4.0")
    print("=" * 60)

    test_urls = [
        ("https://blog.naver.com/allsix6/224167698066", "daybyday"),
    ]

    with BlogCaptureSession() as session:
        for url, blogger in test_urls:
            print(f"\n[캡처] {blogger}...")
            result = session.capture(url, blogger)
            if result["success"]:
                print(f"  PDF: {result['file_path']}")
                print(f"  크기: {result['file_size_mb']}MB")
                if result["text_content"]:
                    print(f"  텍스트: {len(result['text_content'])} chars")
            else:
                print(f"  실패: {result['message']}")

    print("\n완료!")


if __name__ == "__main__":
    main()
