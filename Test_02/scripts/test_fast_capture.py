#!/usr/bin/env python3
"""
빠른 정보 완성도 캡처
- 30초 안에 완료
- 최소한의 요소만 제거
"""

import os
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
from PIL import Image
import time

def fast_complete_capture(blog_url: str, output_path: str) -> bool:
    """빠른 정보 완성도 캡처"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                viewport={"width": 1200, "height": 800}, 
                device_scale_factor=1.2,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            page = ctx.new_page()
            
            # 모바일 버전으로 접속
            mobile_url = blog_url.replace("blog.naver.com", "m.blog.naver.com")
            print(f"접속: {mobile_url}")
            
            # 빠른 페이지 로드
            page.goto(mobile_url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(2000)
            
            # iframe 처리
            try:
                iframe = page.query_selector("iframe#mainFrame")
                if iframe:
                    src = iframe.get_attribute("src")
                    if src and src.startswith("http"):
                        page.goto(src, wait_until="domcontentloaded", timeout=15000)
                        print("iframe 처리 완료")
            except:
                pass
            
            page.wait_for_timeout(2000)
            
            # 빠르고 완전한 스크롤
            print("빠른 완전 스크롤...")
            
            # 페이지 높이 확보
            for i in range(30):
                page.evaluate("window.scrollBy(0, 1000)")
                time.sleep(0.3)
            
            # 다시 천천히 스크롤
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(1)
            
            # 200px 단위로 정밀 스크롤
            for i in range(100):
                current_pos = page.evaluate("window.scrollY")
                page.evaluate("window.scrollBy(0, 200)")
                time.sleep(0.1)
                
                new_pos = page.evaluate("window.scrollY")
                
                if i % 20 == 0:
                    print(f"정밀 스크롤: {new_pos}px")
                
                # 스크롤이 멈추면 종료
                if new_pos == current_pos and new_pos > 0:
                    print("스크롤 멈춤, 종료")
                    break
            
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(1000)
            
            # 최소한의 요소만 제거 (속도 중시)
            print("핵심 요소만 제거...")
            page.evaluate("""
                () => {
                    // 가장 방해되는 요소만 제거
                    const selectors = ['.u_likeit_list', '.comment_area'];
                    selectors.forEach(sel => {
                        const elems = document.querySelectorAll(sel);
                        elems.forEach(el => el.remove());
                    });
                    
                    // 간단한 스타일 정리
                    document.body.style.backgroundColor = '#ffffff';
                    document.body.style.margin = '0';
                    document.body.style.padding = '15px';
                }
            """)
            
            page.wait_for_timeout(500)
            
            # 최종 높이
            final_height = page.evaluate("document.documentElement.scrollHeight")
            print(f"최종 높이: {final_height}px")
            
            # 스크린샷
            page.set_viewport_size({"width": 1200, "height": final_height + 100})
            page.wait_for_timeout(1000)
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            page.screenshot(path=output_path, full_page=True)
            
            # PNG->JPG 변환 (적당한 품질)
            img = Image.open(output_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # JPG 덮어쓰기 저장 (정보 완성도 중시)
            img.save(output_path, 'JPEG', quality=70, optimize=True)
            
            browser.close()
            
            # 결과
            file_size = os.path.getsize(output_path) / 1024 / 1024
            print(f"빠른 완전 캡처 완료: {output_path}")
            print(f"파일 크기: {file_size:.2f} MB")
            
            return True
            
    except Exception as e:
        print(f"빠른 캡처 실패: {e}")
        return False

def main():
    test_url = "https://blog.naver.com/allsix6/224167698066"
    output_path = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02/data/fast_complete_capture.jpg"
    
    print("빠른 정보 완성도 캡처 테스트 시작...")
    success = fast_complete_capture(test_url, output_path)
    
    if success and os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / 1024 / 1024
        print(f"\n=== 확인용 최종 이미지 ===")
        print(f"파일: {output_path}")
        print(f"크기: {size_mb:.2f} MB")
        print("\n22:15 데이터 다음에 2/5일 데이터가 연속적으로 있는지 확인하세요!")
    else:
        print("캡처 실패")

if __name__ == "__main__":
    main()