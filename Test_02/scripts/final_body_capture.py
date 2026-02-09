#!/usr/bin/env python3
"""
최종 본문만 추출 캡처 (v3.0) - 브라우저 재사용 최적화
- 브라우저를 한 번 열고 여러 글 캡처
- 하트/댓글/관련링크 DOM 제거
- data/naver_blog_data/일자/블로거_순번.jpg 저장

작성자: Gemini (Antigravity)
업데이트: 2026-02-02
"""

import os
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Browser, BrowserContext
from PIL import Image
import time

# 제거할 DOM 요소 셀렉터
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
    '.se_oglink', '.og_container'
]

CONTENT_SELECTORS = [
    '.se-main-container',
    '#postViewArea', 
    '.blogview_content',
    '.se_component_wrap',
    'article.se_component'
]


class BlogCaptureSession:
    """브라우저를 재사용하는 캡처 세션"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        
    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context(
            viewport={"width": 1200, "height": 800},
            device_scale_factor=1.2,
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
        """단일 블로그 글 캡처"""
        result = {
            "success": False,
            "file_path": None,
            "file_size_mb": 0,
            "message": ""
        }
        
        try:
            # 일자별 폴더 생성
            today = datetime.now().strftime('%Y-%m-%d')
            base_path = Path("F:/PSJ/AntigravityWorkPlace/Stock/Test_02/data/naver_blog_data")
            save_dir = base_path / today
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 순번 확인
            existing_files = list(save_dir.glob(f"{blogger_id}_*.jpg"))
            sequence = len(existing_files) + 1
            
            filename = f"{blogger_id}_{sequence:03d}.jpg"
            final_path = save_dir / filename
            
            # 새 페이지 열기 (브라우저는 재사용)
            page = self.context.new_page()
            
            try:
                # 모바일 버전 접속
                mobile_url = blog_url.replace("blog.naver.com", "m.blog.naver.com")
                page.goto(mobile_url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(1500)
                
                # iframe 처리
                try:
                    iframe = page.query_selector("iframe#mainFrame")
                    if iframe:
                        src = iframe.get_attribute("src")
                        if src and src.startswith("http"):
                            page.goto(src, wait_until="domcontentloaded", timeout=15000)
                except:
                    pass
                
                page.wait_for_timeout(1000)
                
                # 빠른 스크롤 (이미지 로딩)
                for i in range(20):
                    page.evaluate("window.scrollBy(0, 1000)")
                    time.sleep(0.15)
                
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(0.5)
                
                # 본문 추출
                selectors_js = str(UNWANTED_SELECTORS).replace("'", '"')
                content_selectors_js = str(CONTENT_SELECTORS).replace("'", '"')
                
                page.evaluate(f"""
                    () => {{
                        const contentSelectors = {content_selectors_js};
                        const unwantedSelectors = {selectors_js};
                        
                        let contentElement = null;
                        for (let sel of contentSelectors) {{
                            const el = document.querySelector(sel);
                            if (el && el.offsetHeight > 200) {{
                                contentElement = el;
                                break;
                            }}
                        }}
                        
                        if (!contentElement) contentElement = document.body;
                        
                        const contentClone = contentElement.cloneNode(true);
                        
                        unwantedSelectors.forEach(selector => {{
                            contentClone.querySelectorAll(selector).forEach(el => el.remove());
                        }});
                        
                        document.body.innerHTML = '';
                        document.body.style.cssText = `
                            background-color: #ffffff;
                            margin: 0; padding: 30px;
                            font-family: 'Malgun Gothic', sans-serif;
                            font-size: 15px; line-height: 1.7;
                        `;
                        document.body.appendChild(contentClone);
                        
                        document.querySelectorAll('img').forEach(img => {{
                            img.style.maxWidth = '100%';
                            img.style.height = 'auto';
                        }});
                    }}
                """)
                
                page.wait_for_timeout(500)
                
                # 스크린샷
                final_height = page.evaluate("document.body.scrollHeight")
                page.set_viewport_size({"width": 1200, "height": min(final_height + 100, 32000)})
                
                temp_path = str(final_path).replace('.jpg', '.png')
                page.screenshot(path=temp_path, full_page=True)
                
                # JPG 변환
                img = Image.open(temp_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(final_path, 'JPEG', quality=75, optimize=True)
                
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
                file_size = os.path.getsize(final_path) / 1024 / 1024
                
                result["success"] = True
                result["file_path"] = str(final_path)
                result["file_size_mb"] = round(file_size, 2)
                result["message"] = "본문만 추출 완료"
                
            finally:
                page.close()  # 페이지만 닫기, 브라우저는 유지
                
            return result
            
        except Exception as e:
            result["message"] = f"에러: {str(e)}"
            return result


# 기존 호환성을 위한 함수 (단일 캡처용)
def extract_body_only_capture(blog_url: str, blogger_id: str = "unknown") -> dict:
    """단일 블로그 글 캡처 (기존 호환)"""
    with BlogCaptureSession() as session:
        return session.capture(blog_url, blogger_id)


def main():
    """테스트 - 3명 블로거"""
    print("=" * 60)
    print("본문 캡처 v3.0 - 브라우저 재사용 테스트")
    print("=" * 60)
    
    test_urls = [
        ("https://blog.naver.com/allsix6/224167698066", "daybyday"),
        # 다른 URL 추가 가능
    ]
    
    with BlogCaptureSession() as session:
        for url, blogger in test_urls:
            print(f"\n[캡처] {blogger}...")
            result = session.capture(url, blogger)
            print(f"  결과: {'✅' if result['success'] else '❌'} {result['file_path']}")
    
    print("\n완료!")


if __name__ == "__main__":
    main()