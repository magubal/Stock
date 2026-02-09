#!/usr/bin/env python3
"""
최종 정밀 캡처 테스트
"""

import os
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
from PIL import Image
import time

def final_precise_capture(blog_url: str, output_path: str) -> bool:
    """최종 정밀 캡처"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                viewport={"width": 1200, "height": 600}, 
                device_scale_factor=1.2,  # 적절한 해상도
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            page = ctx.new_page()
            
            # 모바일 버전으로 접속
            mobile_url = blog_url.replace("blog.naver.com", "m.blog.naver.com")
            print(f"접속: {mobile_url}")
            
            # 페이지 로드
            try:
                page.goto(mobile_url, wait_until="networkidle", timeout=30000)
            except TimeoutError:
                page.goto(mobile_url, wait_until="domcontentloaded", timeout=30000)
            
            page.wait_for_timeout(3000)
            
            # 자동 스크롤로 모든 콘텐츠 로드
            print("전체 스크롤...")
            last_position = 0
            
            for i in range(100):
                current_pos = page.evaluate("window.scrollY")
                page.evaluate("window.scrollBy(0, 500)")
                time.sleep(0.2)
                
                new_pos = page.evaluate("window.scrollY")
                
                if i % 20 == 0:
                    print(f"스크롤: {new_pos}px")
                
                if new_pos == current_pos and new_pos != 0:
                    break  # 스크롤 멈춤
                
                last_position = new_pos
            
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(2000)
            
            # 본문 영역만 남기기 (단순화)
            print("본문 정리...")
            try:
                # 간단한 본문 정리 스크립트
                page.evaluate("""
                    () => {
                        // 하트, 댓글 등 제거
                        const unwanted = ['.u_likeit_list', '.comment_area', '#comment', '.recomm', '.social'];
                        unwanted.forEach(sel => {
                            const elems = document.querySelectorAll(sel);
                            elems.forEach(el => el.remove());
                        });
                        
                        // 헤더/푸터 제거
                        const header_footer = ['header', 'footer', '.header', '.footer'];
                        header_footer.forEach(sel => {
                            const elems = document.querySelectorAll(sel);
                            elems.forEach(el => el.remove());
                        });
                        
                        // 배경 정리
                        document.body.style.backgroundColor = '#ffffff';
                        document.body.style.margin = '0';
                        document.body.style.padding = '20px';
                    }
                """)
                print("본문 정리 성공")
            except Exception as e:
                print(f"본문 정리 실패: {e}")
            
            page.wait_for_timeout(1000)
            
            # 최종 높이 확인 및 스크린샷
            final_height = page.evaluate("document.body.scrollHeight")
            print(f"최종 높이: {final_height}px")
            
            page.set_viewport_size({"width": 1200, "height": final_height + 100})
            page.wait_for_timeout(1000)
            
            # 스크린샷
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            page.screenshot(path=output_path, full_page=True)
            
            browser.close()
            
            # PNG를 JPG로 변환 (중간 품질)
            try:
                img = Image.open(output_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                temp_png = output_path.replace('.jpg', '.png')
                os.rename(output_path, temp_png)
                
                img.save(output_path, 'JPEG', quality=65, optimize=True)
                os.remove(temp_png)
                
                file_size = os.path.getsize(output_path) / 1024 / 1024
                print(f"최종 캡처 완료: {output_path}")
                print(f"파일 크기: {file_size:.2f} MB")
                
                return True
            except Exception as e:
                print(f"JPG 변환 실패: {e}")
                return False
                
    except Exception as e:
        print(f"최종 캡처 실패: {e}")
        return False

def main():
    test_url = "https://blog.naver.com/allsix6/224167698066"
    output_path = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02/data/final_capture.jpg"
    
    print("최종 정밀 캡처 테스트 시작...")
    final_precise_capture(test_url, output_path)

if __name__ == "__main__":
    main()