#!/usr/bin/env python3
"""
본문만 완벽 추출 캡처
- 하트, 댓글, 관련 링크 완전 제거
- 일자별 폴더에 명확한 이름으로 저장
"""

import os
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
from PIL import Image
import time

def body_only_capture(blog_url: str, output_dir: str) -> bool:
    """본문만 완벽 추출하여 캡처"""
    try:
        # 일자별 폴더 생성
        today = datetime.now().strftime('%Y-%m-%d')
        save_dir = os.path.join(output_dir, today)
        os.makedirs(save_dir, exist_ok=True)
        
        # 파일명 (규약에 맞게: 블로거_순번)
        # 순번은 해당 일자의 기존 파일 개수 + 1
        existing_files = [f for f in os.listdir(save_dir) if f.startswith('daybyday_') and f.endswith('.jpg')]
        sequence = len(existing_files) + 1
        output_path = os.path.join(save_dir, f"daybyday_{sequence:03d}.jpg")
        
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
            
            # 본문만 완벽 추출 JavaScript
            print("본문만 완벽 추출 중...")
            body_content = page.evaluate("""
                () => {
                    // 본문 셀렉터 우선순위
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
                        if (el && el.offsetHeight > 100) {
                            contentElement = el;
                            console.log('본문 발견:', sel);
                            break;
                        }
                    }
                    
                    if (!contentElement) {
                        // 최후 수단: body에서 본문 추정
                        const allElems = document.body.querySelectorAll('p, div, span');
                        for (let el of allElems) {
                            if (el.textContent && el.textContent.length > 200) {
                                contentElement = el;
                                break;
                            }
                        }
                        console.log('body에서 본문 추정');
                    }
                    
                    // 완벽한 본문 추출
                    if (contentElement) {
                        // 본문 내용 복사
                        const contentClone = contentElement.cloneNode(true);
                        
                        // 불필요 요소 제거
                        const unwantedSelectors = [
                            '.u_likeit_list',
                            '.comment_area',
                            '#comment',
                            '.recomm',
                            '.social',
                            '.share',
                            '.tag',
                            '.related',
                            '.footer',
                            '.header',
                            'button',
                            'iframe',
                            '.ad',
                            '.ads'
                        ];
                        
                        unwantedSelectors.forEach(sel => {
                            const elems = contentClone.querySelectorAll(sel);
                            elems.forEach(el => el.remove());
                        });
                        
                        // body 완전 교체
                        document.body.innerHTML = '';
                        document.body.style.backgroundColor = '#ffffff';
                        document.body.style.margin = '0';
                        document.body.style.padding = '30px';
                        document.body.style.fontFamily = 'Arial, sans-serif';
                        document.body.style.fontSize = '14px';
                        document.body.style.lineHeight = '1.6';
                        document.body.style.color = '#000000';
                        
                        document.body.appendChild(contentClone);
                        
                        return {
                            success: true,
                            height: document.body.scrollHeight,
                            message: '본문만 완벽 추출 성공'
                        };
                    } else {
                        return {
                            success: false,
                            height: 0,
                            message: '본문을 찾을 수 없음'
                        };
                    }
                }
            """)
            
            print(f"본문 추출 결과: {body_content}")
            
            if not body_content['success']:
                print("본문 추출 실패")
                browser.close()
                return False
            
            page.wait_for_timeout(2000)
            
            # 전체 스크롤로 모든 내용 로드
            print("본문 전체 스크롤...")
            for i in range(50):
                current_pos = page.evaluate("window.scrollY")
                page.evaluate("window.scrollBy(0, 300)")
                time.sleep(0.2)
                
                new_pos = page.evaluate("window.scrollY")
                if new_pos == current_pos and new_pos > 0:
                    break
            
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(1000)
            
            # 최종 높이
            final_height = page.evaluate("document.body.scrollHeight")
            print(f"최종 본문 높이: {final_height}px")
            
            # 스크린샷
            page.set_viewport_size({"width": 1200, "height": final_height + 100})
            page.wait_for_timeout(1000)
            
            page.screenshot(path=output_path, full_page=True)
            
            # PNG -> JPG 변환 (적당한 품질)
            img = Image.open(output_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # JPG 저장 (본문 가독성 중심)
            img.save(output_path, 'JPEG', quality=75, optimize=True)
            
            browser.close()
            
            # 결과 확인
            file_size = os.path.getsize(output_path) / 1024 / 1024
            print(f"본문만 캡처 완료: {output_path}")
            print(f"파일 크기: {file_size:.2f} MB")
            print(f"본문 높이: {final_height}px")
            
            return True
            
    except Exception as e:
        print(f"본문만 캡처 실패: {e}")
        return False

def main():
    test_url = "https://blog.naver.com/allsix6/224167698066"
    output_dir = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02/data"
    
    print("본문만 완벽 추출 캡처 테스트 시작...")
    success = body_only_capture(test_url, output_dir)
    
    if success:
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"\n=== 저장 위치 확인 ===")
        print(f"폴더: {output_dir}/{today}")
        print("daybyday_001.jpg 파일을 확인하세요!")
        print("하트, 댓글, 관련 링크가 제거된 본문만 보일 것입니다.")

if __name__ == "__main__":
    main()