# save_post_pdf_only_article.py
import os, sys, time, argparse, tempfile
from urllib.parse import urlparse, urlunparse
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

#==================== 실행명령어 ======================================================
# python full_capture.py --url "https://blog.naver.com/findingst1/224165482603" --mobile
# 로그인 필요한 글은 --login 옵션 추가.
# 종료가 안되니...Ctrl+C하고, 다시 적용할 필요.
#=====================================================================================

# 본문 후보 셀렉터(모바일/PC 겸용)
ARTICLE_SELECTORS = [
    ".se-main-container",          # 최신 스마트에디터
    "#postViewArea",               # 구버전
    "article.se_component",        # 일부 테마
    "article[data-role='post']",
    ".se-viewer",                  # 뷰어 래퍼
]

OUTPUT_PATH = r"C:\Users\calm_\Downloads\blog_page.pdf"

def to_mobile(u: str) -> str:
    p = urlparse(u)
    if p.netloc.startswith("blog.naver.com"):
        p = p._replace(netloc="m.blog.naver.com")
    return urlunparse(p)

def open_iframe_or_self(page, url):
    try:
        page.goto(url, wait_until="networkidle", timeout=60000)
    except TimeoutError:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
    f = page.query_selector("iframe#mainFrame")
    if f:
        src = f.get_attribute("src")
        if src and src.startswith("http"):
            page.goto(src, wait_until="networkidle")

def auto_scroll(page, step=1500, pause=0.12, loops=400):
    last = -1
    for _ in range(loops):
        page.evaluate(f"window.scrollBy(0,{step})")
        time.sleep(pause)
        cur = page.evaluate("window.scrollY")
        if cur == last:
            break
        last = cur
    page.evaluate("window.scrollTo(0,0)")  # 맨 위로

def detect_article_selector(page):
    for sel in ARTICLE_SELECTORS:
        try:
            if page.locator(sel).count() > 0 and page.locator(sel).first.is_visible():
                return sel
        except:
            pass
    return None

# 핵심: 본문 외 모두 제거(광고/피드 재로딩 차단)
PRUNE_JS = """
(sel) => {
  const el = document.querySelector(sel);
  if (!el) return false;
  // 이미지 지연로딩 해제
  document.querySelectorAll('img[data-src]').forEach(img => { img.src = img.getAttribute('data-src'); });
  // 본문만 남기기
  document.body.style.margin = '0';
  document.body.style.padding = '0';
  Array.from(document.body.children).forEach(c => { if (!el.contains(c) && c !== el) c.remove(); });
  // 본문을 body의 유일한 자식으로 이동
  if (el.parentElement !== document.body) {
    el.remove();
    document.body.innerHTML = "";
    document.body.appendChild(el);
  }
  // 폭 고정 및 글자색 보존
  el.style.maxWidth = '100%';
  el.style.margin = '0';
  el.style.padding = '0';
  // 인쇄 모드 적용
  const css = `
    @media print {
      html, body { margin:0 !important; padding:0 !important; background:#fff !important; }
      * { visibility: visible !important; }
    }`;
  const s = document.createElement('style');
  s.textContent = css;
  document.head.appendChild(s);
  window.scrollTo(0,0);
  return true;
}
"""

def login_and_dump_state(p, url):
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context(viewport={"width":1280,"height":900}, device_scale_factor=1.5)
    page = ctx.new_page()
    open_iframe_or_self(page, url)
    print("필요하면 로그인 후 Enter:", flush=True)
    input()
    f = tempfile.mktemp(suffix=".json")
    ctx.storage_state(path=f)
    try: page.close(); ctx.close(); browser.close()
    except: pass
    return f

def render_pdf(p, url, state=None):
    browser = p.chromium.launch(headless=True)  # PDF는 headless 필수
    ctx_kwargs = {"viewport":{"width":1280,"height":2000}, "device_scale_factor":2}
    if state: ctx_kwargs["storage_state"] = state
    ctx = browser.new_context(**ctx_kwargs)
    page = ctx.new_page()

    open_iframe_or_self(page, url)
    auto_scroll(page)          # 전체 로드 유도
    time.sleep(2.0)            # 지연 렌더 대기

    sel = detect_article_selector(page)
    if not sel:
        sel = "body"           # 최후 수단

    ok = page.evaluate(PRUNE_JS, sel)  # 본문만 남김
    if not ok:
        # 실패 시에도 전체를 인쇄하되 광고 최소화 위해 맨 위로
        page.evaluate("window.scrollTo(0,0)")

    time.sleep(0.8)            # 적용 대기
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    page.emulate_media(media="print")
    page.pdf(path=OUTPUT_PATH, print_background=True, scale=1.0)
    print(f"PDF 저장 완료 : {OUTPUT_PATH}", flush=True)

    try: page.close(); ctx.close(); browser.close()
    except: pass

def main():
    ap = argparse.ArgumentParser(description="네이버 블로그 본문만 PDF 저장")
    ap.add_argument("--url", required=True)
    ap.add_argument("--mobile", action="store_true")
    ap.add_argument("--login", action="store_true")
    args = ap.parse_args()

    url = to_mobile(args.url) if args.mobile else args.url

    p = sync_playwright().start()
    try:
        state = login_and_dump_state(p, url) if args.login else None
        render_pdf(p, url, state)
    finally:
        try: p.stop()
        except: pass
        os._exit(0)  # 종료 보장

if __name__ == "__main__":
    main()
