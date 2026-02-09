#!/usr/bin/env python3
"""
네이버 블로그 이미지 수집기 테스트
- 단일 게시물 이미지 캡처 테스트
"""

import os
import json
import time
from datetime import datetime
from urllib.parse import urlunparse
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

# 본문 후보 셀렉터(모바일/PC 겸용)
ARTICLE_SELECTORS = [
    ".se-main-container",          # 최신 스마트에디터
    "#postViewArea",               # 구버전
    "article.se_component",        # 일부 테마
    "article[data-role='post']",
    ".se-viewer",                  # 뷰어 래퍼
]

def to_mobile(url: str) -> str:
    """모바일 URL로 변환"""
    from urllib.parse import urlparse
    p = urlparse(url)
    if p.netloc.startswith("blog.naver.com"):
        p = p._replace(netloc="m.blog.naver.com")
    return urlunparse(p)

def open_iframe_or_self(page, url):
    """iframe 처리 후 페이지 로드"""
    try:
        page.goto(url, wait_until="networkidle", timeout=60000)
    except TimeoutError:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
    
    # 네이버 블로그 iframe 처리
    f = page.query_selector("iframe#mainFrame")
    if f:
        src = f.get_attribute("src")
        if src and src.startswith("http"):
            page.goto(src, wait_until="networkidle")

def auto_scroll(page, step=1500, pause=0.12, loops=400):
    """자동 스크롤로 전체 콘텐츠 로드"""
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
    """본문 셀렉터 감지"""
    for sel in ARTICLE_SELECTORS:
        try:
            if page.locator(sel).count() > 0 and page.locator(sel).first.is_visible():
                return sel
        except:
            pass
    return None

# 본문 외 모두 제거(광고/피드 재로딩 차단)
PRUNE_JS = """
(sel) => {
  const el = document.querySelector(sel);
  if (!el) return false;
  // 이미지 지연로딩 해제
  document.querySelectorAll('img[data-src]').forEach(img => { img.src = img.getAttribute('data-src'); });
  // 본문만 남기기
  document.body.style.margin = '0';
  document.body.style.padding = '0';
  document.body.style.backgroundColor = '#ffffff';
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
  el.style.padding = '20px';
  el.style.backgroundColor = '#ffffff';
  el.style.color = '#000000';
  window.scrollTo(0,0);
  return true;
}
"""

def capture_blog_image(blog_url: str, output_path: Path) -> bool:
    """블로그 글을 이미지로 캡처"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                viewport={"width": 1200, "height": 2000}, 
                device_scale_factor=2,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            page = ctx.new_page()
            
            # 모바일 버전이 더 깔끔함
            mobile_url = blog_url.replace("blog.naver.com", "m.blog.naver.com")
            
            print(f"접속 시도: {mobile_url}")
            open_iframe_or_self(page, mobile_url)
            page.wait_for_timeout(3000)  # 로딩 대기
            
            # 자동 스크롤로 전체 콘텐츠 로드
            print("스크롤 중...")
            auto_scroll(page)
            page.wait_for_timeout(2000)
            
            # 본문 셀렉터 감지
            sel = detect_article_selector(page)
            if not sel:
                sel = "body"  # 최후 수단
                print("본문 셀렉터를 찾지 못해 body 사용")
            else:
                print(f"본문 셀렉터 발견: {sel}")
            
            # 본문만 남기기
            print("본문 외 요소 제거 중...")
            ok = page.evaluate(PRUNE_JS, sel)
            if not ok:
                print("본문 정리 실패 - 전체 페이지 캡처")
                page.evaluate("window.scrollTo(0,0)")
            
            page.wait_for_timeout(2000)
            
            # 전체 페이지 스크린샷
            print(f"이미지 저장: {output_path}")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=output_path, full_page=True)
            
            browser.close()
            return True
            
    except Exception as e:
        print(f"이미지 캡처 실패 {blog_url}: {e}")
        return False

def main():
    """테스트 메인 함수"""
    # 테스트용 블로그 URL
    test_url = "https://blog.naver.com/allsix6/224167698066"
    
    # 출력 경로
    output_dir = Path("F:/PSJ/AntigravityWorkPlace/Stock/Test_02/data/test_capture")
    output_path = output_dir / f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    
    print(f"테스트 시작: {test_url}")
    
    if capture_blog_image(test_url, output_path):
        print(f"✅ 성공! 이미지 저장: {output_path}")
        
        # 파일 정보 출력
        if output_path.exists():
            file_size = output_path.stat().st_size / 1024 / 1024  # MB
            print(f"파일 크기: {file_size:.2f} MB")
        else:
            print("⚠️ 파일이 생성되지 않았습니다")
    else:
        print("❌ 실패!")

if __name__ == "__main__":
    main()