#!/usr/bin/env python3
"""
원본 방식 기반 캡처 테스트
- full_capture.py의 안정적인 방식 사용
"""

import os
import time
from urllib.parse import urlparse, urlunparse
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

def auto_scroll(page, step=800, pause=0.2, loops=300):
    """자동 스크롤로 전체 콘텐츠 로드 (더 정밀하게)"""
    last_position = -1
    scroll_count = 0
    
    for i in range(loops):
        current_position = page.evaluate("window.scrollY")
        
        # 스크롤
        page.evaluate(f"window.scrollBy(0,{step})")
        time.sleep(pause)
        
        new_position = page.evaluate("window.scrollY")
        
        # 진행 상황 출력
        if i % 30 == 0:
            print(f"스크롤 진행: {new_position}px (step {i})")
        
        # 스크롤이 멈추면 종료
        if new_position == last_position and new_position != 0:
            scroll_count += 1
            if scroll_count >= 3:  # 3번 연속으로 멈추면 종료
                print(f"스크롤 멈춤: {new_position}px")
                break
        else:
            scroll_count = 0
        
        last_position = new_position
        
        # 페이지 끝에 도달
        if page.evaluate("window.innerHeight + window.scrollY >= document.body.scrollHeight"):
            print("페이지 끝 도달")
            break
    
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
  document.querySelectorAll('img[data-src]').forEach(img => { 
    img.src = img.getAttribute('data-src'); 
  });
  
  // 본문만 남기기
  document.body.style.margin = '0';
  document.body.style.padding = '0';
  document.body.style.backgroundColor = '#ffffff';
  
  // 본문 외 요소 제거
  Array.from(document.body.children).forEach(c => { 
    if (!el.contains(c) && c !== el) c.remove(); 
  });
  
  // 본문을 body의 유일한 자식으로 이동
  if (el.parentElement !== document.body) {
    el.remove();
    document.body.innerHTML = "";
    document.body.appendChild(el);
  }
  
  // 스타일 정리
  el.style.maxWidth = '100%';
  el.style.margin = '0';
  el.style.padding = '20px';
  el.style.backgroundColor = '#ffffff';
  el.style.color = '#000000';
  
  window.scrollTo(0,0);
  return true;
}
"""

def capture_with_playwright(blog_url: str, output_path: str) -> bool:
    """Playwright로 정밀 캡처"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                viewport={"width": 1200, "height": 800}, 
                device_scale_factor=1.5,  # 더 선명하게
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            page = ctx.new_page()
            
            # 모바일 버전으로 접속
            mobile_url = to_mobile(blog_url)
            print(f"접속: {mobile_url}")
            
            open_iframe_or_self(page, mobile_url)
            page.wait_for_timeout(3000)  # 로딩 대기
            
            # 자동 스크롤로 전체 콘텐츠 로드
            print("전체 스크롤 시작...")
            auto_scroll(page)
            page.wait_for_timeout(2000)  # 추가 렌더링 대기
            
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
            if ok:
                print("본문 정리 성공")
            else:
                print("본문 정리 실패 - 전체 페이지 캡처")
            
            page.wait_for_timeout(2000)  # 적용 대기
            
            # 페이지 최종 높이 확인
            final_height = page.evaluate("document.body.scrollHeight")
            print(f"최종 콘텐츠 높이: {final_height}px")
            
            # 뷰포트 크기 조정 및 스크린샷
            page.set_viewport_size({"width": 1200, "height": final_height + 100})
            page.wait_for_timeout(1000)
            
            # 스크린샷 저장
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            page.screenshot(path=output_path, full_page=True)
            
            browser.close()
            
            # 파일 크기 확인
            file_size = os.path.getsize(output_path) / 1024 / 1024
            print(f"캡처 완료: {output_path}")
            print(f"파일 크기: {file_size:.2f} MB")
            
            return True
            
    except Exception as e:
        print(f"Playwright 캡처 실패: {e}")
        return False

def main():
    test_url = "https://blog.naver.com/allsix6/224167698066"
    output_path = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02/data/playwright_capture.jpg"
    
    print("Playwright 기반 정밀 캡처 테스트 시작...")
    capture_with_playwright(test_url, output_path)

if __name__ == "__main__":
    main()