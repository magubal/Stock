#!/usr/bin/env python3
"""
정보 완성도 중심 캡처
- 용량보다 정보 누락 방지 우선
- 확인용 최종 이미지 저장
"""

import os
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
from PIL import Image
import time

def complete_info_capture(blog_url: str, output_path: str) -> bool:
    """정보 완성도 100% 캡처"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                viewport={"width": 1200, "height": 600}, 
                device_scale_factor=1.2,
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
            
            # iframe 처리
            try:
                iframe = page.query_selector("iframe#mainFrame")
                if iframe:
                    src = iframe.get_attribute("src")
                    if src and src.startswith("http"):
                        page.goto(src, wait_until="networkidle")
                        print("iframe 처리 완료")
            except:
                print("iframe 없음 또는 처리 실패")
            
            page.wait_for_timeout(2000)
            
            # 매우 천천히 스크롤하며 모든 정보 확보
            print("완전 스크롤 시작 (정보 누락 방지)...")
            last_height = 0
            stable_count = 0
            
            for i in range(500):  # 최대 500번 스크롤
                current_height = page.evaluate("document.documentElement.scrollHeight")
                current_scroll = page.evaluate("window.scrollY")
                
                # 작게 스크롤
                page.evaluate("window.scrollBy(0, 200)")
                time.sleep(0.4)  # 충분한 대기
                
                new_scroll = page.evaluate("window.scrollY")
                new_height = page.evaluate("document.documentElement.scrollHeight")
                
                if i % 50 == 0:
                    print(f"스크롤 {i}: 위치={new_scroll}px, 문서높이={new_height}px")
                
                # 문서 높이가 변하지 않고 스크롤이 바닥에 닿으면
                if new_height == current_height and new_scroll + 600 >= new_height:
                    stable_count += 1
                    if stable_count >= 10:  # 10번 안정되면 종료
                        print(f"스크롤 완전 종료: {new_height}px")
                        break
                else:
                    stable_count = 0
            
            # 맨 위로
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(2000)
            
            # 최종 문서 높이
            final_height = page.evaluate("document.documentElement.scrollHeight")
            print(f"최종 문서 높이: {final_height}px")
            
            # 최소한의 불필요 영역만 제거
            print("필수 불필요 영역만 제거...")
            page.evaluate("""
                () => {
                    // 명시적으로 제거할 영역만 제거
                    const selectors = ['.u_likeit_list', '.comment_area', '#comment', '.recomm'];
                    selectors.forEach(sel => {
                        const elems = document.querySelectorAll(sel);
                        elems.forEach(el => el.remove());
                    });
                    
                    // 배경 정리
                    document.body.style.backgroundColor = '#ffffff';
                    document.body.style.margin = '0';
                    document.body.style.padding = '10px';
                }
            """)
            
            page.wait_for_timeout(1000)
            
            # 뷰포트 크기 조정
            page.set_viewport_size({"width": 1200, "height": final_height + 200})
            page.wait_for_timeout(2000)
            
            # 스크린샷 저장 (PNG -> JPG)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 일단 PNG로 저장
            png_path = output_path.replace('.jpg', '.png')
            page.screenshot(path=png_path, full_page=True)
            
            # JPG로 변환 (적당한 품질)
            img = Image.open(png_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 적당한 압축 (정보 완성도 우선)
            img.save(output_path, 'JPEG', quality=75, optimize=True)
            os.remove(png_path)
            
            browser.close()
            
            # 결과 확인
            file_size = os.path.getsize(output_path) / 1024 / 1024
            print(f"정보 완성 캡처 완료: {output_path}")
            print(f"파일 크기: {file_size:.2f} MB")
            
            return True
            
    except Exception as e:
        print(f"정보 완성 캡처 실패: {e}")
        return False

def main():
    test_url = "https://blog.naver.com/allsix6/224167698066"
    output_path = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02/data/complete_info_capture.jpg"
    
    print("정보 완성도 100% 캡처 테스트 시작...")
    complete_info_capture(test_url, output_path)
    
    print("\n=== 확인용 이미지 정보 ===")
    print(f"저장 위치: {output_path}")
    if os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / 1024 / 1024
        print(f"파일 크기: {size_mb:.2f} MB")
        print("이 이미지를 확인하여 정보 누락이 없는지 검증하세요.")

if __name__ == "__main__":
    main()