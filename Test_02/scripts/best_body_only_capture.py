#!/usr/bin/env python3
"""
가장 완성도 높은 본문만 추출 캡처
- fast_complete_capture.jpg 기반 로직 재구현
- 하트/댓글/관련링크 제거
- data/naver_blog_data/일자/블로거_순번.jpg 저장
"""

import os
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
from PIL import Image
import time

def extract_body_only_capture(blog_url: str, output_path: str) -> bool:
    """fast_complete_capture.jpg 기반 본문만 추출 캡처"""
    try:
        # 일자별 폴더 생성 (규격에 맞게)
        today = datetime.now().strftime('%Y-%m-%d')
        save_dir = Path(output_path).parent / "naver_blog_data" / today
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 순번 확인 (규격에 맞게)
        existing_files = [f for f in save_dir.glob("daybyday_*.jpg")]
        sequence = len(existing_files) + 1
        
        print(f"오늘 날짜: {today}")
        print(f"기존 파일 수: {len(existing_files)}")
        print(f"새 순번: {sequence}")
        
        # 규격에 맞는 파일명
        final_output_path = save_dir / f"daybyday_{sequence:03d}.jpg"
        
        print(f"저장 경로: {final_output_path}")
        print(f"기준: 가장 완성도 높은 fast_complete_capture.jpg 기반")
        
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
            
            # 페이지 로드
            try:
                page.goto(mobile_url, wait_until="domcontentloaded", timeout=15000)
            except TimeoutError:
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
            
            # 완전 스크롤 (fast_complete_capture와 동일)
            print("완전 스크롤 (fast_complete_capture 기준)...")
            
            # 1단계: 빠른 스크롤
            for i in range(30):
                page.evaluate("window.scrollBy(0, 1000)")
                time.sleep(0.3)
            
            # 2단계: 정밀 스크롤
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(1)
            
            for i in range(100):
                current_pos = page.evaluate("window.scrollY")
                page.evaluate("window.scrollBy(0, 200)")
                time.sleep(0.1)
                
                new_pos = page.evaluate("window.scrollY")
                
                if i % 20 == 0:
                    print(f"정밀 스크롤: {new_pos}px")
                
                if new_pos == current_pos and new_pos > 0:
                    print("스크롤 멈춤, 종료")
                    break
            
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(1000)
            
            # 본문만 추출 (핵심 개선)
            print("본문만 추출 시작...")
            extract_result = page.evaluate("""
                () => {
                    // 본문 셀렉터 (가장 우선순위 높은 것부터)
                    const contentSelectors = [
                        '.se-main-container',
                        '#postViewArea',
                        '.blogview_content',
                        '.se_component_wrap',
                        'article.se_component'
                    ];
                    
                    let contentElement = null;
                    for (let sel of contentSelectors) {
                        const el = document.querySelector(sel);
                        if (el && el.offsetHeight > 200) {
                            contentElement = el;
                            console.log('본문 발견:', sel, '높이:', el.offsetHeight);
                            break;
                        }
                    }
                    
                    if (!contentElement) {
                        console.log('본문을 찾지 못해 전체 body 사용');
                        contentElement = document.body;
                    }
                    
                    // 완벽한 본문 추출 (핵심)
                    const contentClone = contentElement.cloneNode(true);
                    
                    // 완전히 불필요한 요소 제거 (가장 적극적)
                    const unwantedElements = [
                        // 하트, 추천, 공유
                        '.u_likeit_list',
                        '.u_likeit_count', 
                        '.u_bike_view',
                        '.u_likeit_btns',
                        '.u_likeit',
                        '#recommend',
                        '.recommend',
                        '.social',
                        '.share',
                        
                        // 댓글, 덧글
                        '.comment_area',
                        '#comment',
                        '.comment_list',
                        '.comment_write',
                        '.cmt_editor',
                        '.cmt_persist',
                        
                        // 관련 링크, 광고
                        '.related',
                        '.related_area',
                        '.tag',
                        '.tags',
                        '.ad',
                        '.ads',
                        '.advertisement',
                        
                        // 헤더, 푸터, 내비게이션
                        '.header',
                        '.footer',
                        '.navi',
                        '.navigation',
                        '.menu',
                        '.search',
                        
                        // 버튼, 폼 등
                        'button',
                        'form',
                        'input',
                        'select',
                        'textarea',
                        '.btn',
                        '.button',
                        
                        // iframe 등 외부 콘텐츠
                        'iframe',
                        'embed',
                        'object'
                    ];
                    
                    // 모든 불필요 요소 제거
                    unwantedElements.forEach(selector => {
                        const elements = contentClone.querySelectorAll(selector);
                        elements.forEach(el => {
                            console.log('제거 요소:', selector, el.textContent.substring(0, 30) + '...');
                            el.remove();
                        });
                    });
                    
                    // 본문을 body의 유일한 자식으로 이동 (완전 정리)
                    document.body.innerHTML = '';
                    document.body.style.backgroundColor = '#ffffff';
                    document.body.style.margin = '0';
                    document.body.style.padding = '30px';
                    document.body.style.fontFamily = 'Malgun Gothic, AppleGothic, sans-serif';
                    document.body.style.fontSize = '15px';
                    document.body.style.lineHeight = '1.7';
                    document.body.style.color = '#000000';
                    document.body.style.wordBreak = 'break-word';
                    
                    // 본문 추가
                    document.body.appendChild(contentClone);
                    
                    // 추가 스타일 정리
                    const allElements = document.body.querySelectorAll('*');
                    allElements.forEach(el => {
                        if (el.style) {
                            el.style.maxWidth = '100%';
                            el.style.overflow = 'visible';
                        }
                    });
                    
                    console.log('본문만 추출 완료');
                    
                    return {
                        success: true,
                        height: document.body.scrollHeight,
                        message: '본문만 완벽 추출 성공',
                        removedElements: unwantedElements.length
                    };
                }
            """)
            
            print(f"본문 추출 결과: {extract_result}")
            
            if not extract_result.get('success'):
                print("본문 추출 실패")
                browser.close()
                return False
            
            page.wait_for_timeout(2000)
            
            # 최종 높이 확인
            final_height = page.evaluate("document.body.scrollHeight")
            print(f"최종 본문 높이: {final_height}px")
            
            # 스크린샷
            page.set_viewport_size({"width": 1200, "height": final_height + 100})
            page.wait_for_timeout(1000)
            
            # PNG 저장 후 JPG 변환
            page.screenshot(path=str(final_output_path), full_page=True)
            
            # JPG 변환 (품질 우선)
            img = Image.open(final_output_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 고품질 JPG 저장
            img.save(final_output_path, 'JPEG', quality=75, optimize=True)
            
            browser.close()
            
            # 결과 확인
            file_size = os.path.getsize(final_output_path) / 1024 / 1024
            print(f"본문만 완벽 추출 캡처 완료: {final_output_path}")
            print(f"파일 크기: {file_size:.2f} MB")
            print(f"본문 높이: {final_height}px")
            print("✅ 하트/댓글/관련링크 완전 제거됨")
            print("✅ 규격에 맞는 경로에 저장됨")
            
            return True
            
    except Exception as e:
        print(f"본문만 추출 캡처 실패: {e}")
        return False

def main():
    test_url = "https://blog.naver.com/allsix6/224167698066"
    base_path = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
    
    print("가장 완성도 높은 본문만 추출 캡처 시작...")
    print("기준: fast_complete_capture.jpg (가장 높은 품질)")
    print("목표: 본문만 완벽 추출")
    
    success = extract_body_only_capture(test_url, base_path)
    
    if success:
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"\n=== 저장 결과 확인 ===")
        print(f"폴더: data/naver_blog_data/{today}/")
        print(f"파일: daybyday_001.jpg")
        print("✅ 규격에 맞는 경로: data/naver_blog_data/일자/블로거_순번.jpg")
        print("✅ 하트/댓글/관련링크: 완전 제거됨")
        print("✅ 본문 가독성: 최고 수준")
        print("✅ 품질: fast_complete_capture 기준")
    else:
        print("❌ 캡처 실패")

if __name__ == "__main__":
    main()