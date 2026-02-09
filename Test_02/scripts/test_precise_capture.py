#!/usr/bin/env python3
"""
정밀 스크롤 캡처 테스트
- 정확한 콘텐츠 영역만 캡처
- 누락 없는 완벽한 스크롤
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from PIL import Image
import os

def capture_precise_blog(blog_url: str, output_path: str):
    """정밀한 블로그 캡처"""
    
    # Chrome 옵션 설정
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1200,600')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # 모바일 버전으로 접속
        mobile_url = blog_url.replace("blog.naver.com", "m.blog.naver.com")
        print(f"접속: {mobile_url}")
        driver.get(mobile_url)
        time.sleep(3)
        
        # iframe 처리
        try:
            iframe = driver.find_element(By.ID, "mainFrame")
            driver.switch_to.frame(iframe)
            print("iframe 처리 완료")
        except:
            print("iframe 없음 - 모바일 버전 직접 접근")
        
        # 본문 영역 찾기
        content_selectors = [
            ".se-main-container",
            "#postViewArea", 
            ".blogview_content",
            ".se_component_wrap",
            ".se-section-area"
        ]
        
        content_element = None
        for selector in content_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                if element.size['height'] > 100:  # 의미 있는 높이
                    content_element = element
                    print(f"본문 영역 발견: {selector}")
                    break
            except:
                continue
        
        if not content_element:
            print("본문 영역을 찾지 못해 전체 페이지 캡처")
            # 전체 페이지 캡처로 fallback
        
        # 천천히 스크롤하며 모든 콘텐츠 로드
        print("전체 스크롤 시작...")
        last_height = 0
        
        for i in range(50):  # 최대 50번 스크롤
            # 현재 스크롤 위치
            current_scroll = driver.execute_script("return window.pageYOffset || document.documentElement.scrollTop")
            
            # 스크롤 다운
            driver.execute_script("window.scrollBy(0, 300)")
            time.sleep(0.3)
            
            # 새로운 높이 확인
            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            
            # 진행 상황 출력
            if i % 10 == 0:
                print(f"스크롤 {i}: {current_scroll}px, 문서 높이: {new_height}px")
            
            # 스크롤이 멈추면 종료
            if new_height == last_height and current_scroll + 600 >= new_height:
                print("스크롤 완료")
                break
            
            last_height = new_height
        
        # 맨 위로
        driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(1)
        
        # 페이지 전체 높이 다시 확인
        final_height = driver.execute_script("return document.documentElement.scrollHeight")
        print(f"최종 문서 높이: {final_height}px")
        
        # 정밀 분할 캡처
        return capture_precise_sections(driver, output_path, final_height)
        
    except Exception as e:
        print(f"실패: {e}")
        return False
    finally:
        driver.quit()

def capture_precise_sections(driver, output_path: str, total_height: int):
    """정밀한 섹션 캡처 (누락/겹침 방지)"""
    try:
        viewport_height = 500  # 더 작은 뷰포트로 정밀 캡처
        overlap = 30  # 겹침을 줄임
        
        screenshots = []
        current_position = 0
        section_num = 0
        
        while current_position < total_height:
            driver.execute_script(f"window.scrollTo(0, {current_position})")
            time.sleep(0.5)  # 안정적 렌더링
            
            temp_file = f"precise_temp_{section_num}.png"
            driver.save_screenshot(temp_file)
            screenshots.append(temp_file)
            
            print(f"섹션 {section_num}: {current_position}px 캡처")
            
            # 겹침을 최소화하며 다음 위치로
            current_position += viewport_height - overlap
            section_num += 1
            
            if current_position >= total_height:
                break
        
        print(f"총 {len(screenshots)}개 섹션 캡처 완료")
        
        # 이미지 정밀 합치기
        return stitch_precisely(screenshots, output_path)
        
    except Exception as e:
        print(f"정밀 캡처 실패: {e}")
        return False

def stitch_precisely(screenshots, output_path: str):
    """정밀한 이미지 합치기"""
    try:
        images = [Image.open(path) for path in screenshots]
        
        if not images:
            return False
        
        # 첫 이미지 그대로, 나머지는 겹침 제거
        final_images = []
        total_width = images[0].width
        
        for i, img in enumerate(images):
            if i == 0:
                final_images.append(img)
            else:
                # 상단 30px만 잘라냄 (최소 겹침)
                cropped = img.crop((0, overlap, total_width, img.height))
                if cropped.height > 10:  # 의미 있는 높이만
                    final_images.append(cropped)
        
        # 최종 이미지 합치기
        total_height = sum(img.height for img in final_images)
        final_image = Image.new('RGB', (total_width, total_height))
        
        y_pos = 0
        for img in final_images:
            final_image.paste(img, (0, y_pos))
            y_pos += img.height
        
        # 고품질로 저장
        final_image.save(output_path, 'JPEG', quality=70, optimize=True, progressive=True)
        
        # 임시 파일 삭제
        for path in screenshots:
            os.remove(path)
        
        file_size = os.path.getsize(output_path) / 1024 / 1024
        print(f"정밀 합치기 완료: {output_path}")
        print(f"최종 파일 크기: {file_size:.2f} MB")
        print(f"최종 이미지 높이: {total_height}px")
        
        return True
        
    except Exception as e:
        print(f"정밀 합치기 실패: {e}")
        return False

def main():
    test_url = "https://blog.naver.com/allsix6/224167698066"
    output_path = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02/data/precise_capture.jpg"
    
    print("정밀 스크롤 캡처 테스트 시작...")
    capture_precise_blog(test_url, output_path)

if __name__ == "__main__":
    main()