#!/usr/bin/env python3
"""
개선된 분할 캡처 테스트
- 겹침 방지
- 고압축
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from PIL import Image
import os

def capture_improved_full_blog(blog_url: str, output_path: str):
    """개선된 전체 블로그 캡처"""
    
    # Chrome 옵션 설정
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1200,800')
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
        
        # 전체 콘텐츠 로드
        print("전체 스크롤 시작...")
        for i in range(15):
            driver.execute_script("window.scrollBy(0, 1000)")
            time.sleep(0.5)
        
        driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(1)
        
        # 페이지 높이 확인
        total_height = driver.execute_script("return document.body.scrollHeight")
        print(f"전체 높이: {total_height}px")
        
        # 분할 캡처 시작
        viewport_height = 800
        screenshots = []
        current_position = 0
        section_number = 0
        
        while current_position < total_height:
            driver.execute_script(f"window.scrollTo(0, {current_position})")
            time.sleep(0.8)  # 안정적 로딩
            
            temp_file = f"temp_{section_number}.png"
            driver.save_screenshot(temp_file)
            screenshots.append(temp_file)
            section_number += 1
            
            # 겹침 없이 다음 섹션으로
            current_position += viewport_height
            if current_position >= total_height:
                break
        
        print(f"총 {len(screenshots)}개 섹션 캡처 완료")
        
        # 이미지 합치기 (겹침 방지)
        images = [Image.open(path) for path in screenshots]
        
        if not images:
            return False
        
        cropped_images = []
        total_width = images[0].width
        
        for i, img in enumerate(images):
            if i == 0:
                cropped_img = img
            else:
                # 상단 50px 잘라내기 (겹침 방지)
                cropped_img = img.crop((0, 50, total_width, img.height))
            
            if cropped_img.height > 0:
                cropped_images.append(cropped_img)
        
        # 최종 이미지 합치기
        total_img_height = sum(img.height for img in cropped_images)
        final_image = Image.new('RGB', (total_width, total_img_height))
        
        y_pos = 0
        for img in cropped_images:
            final_image.paste(img, (0, y_pos))
            y_pos += img.height
        
        # 고압축 JPG 저장
        final_image.save(output_path, 'JPEG', quality=60, optimize=True, progressive=True)
        
        # 임시 파일 삭제
        for path in screenshots:
            os.remove(path)
        
        # 파일 크기 확인
        file_size = os.path.getsize(output_path) / 1024 / 1024  # MB
        print(f"개선된 캡처 완료: {output_path}")
        print(f"파일 크기: {file_size:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"실패: {e}")
        return False
    finally:
        driver.quit()

def main():
    test_url = "https://blog.naver.com/allsix6/224167698066"
    output_path = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02/data/improved_capture.jpg"
    
    print("개선된 분할 캡처 테스트 시작...")
    capture_improved_full_blog(test_url, output_path)

if __name__ == "__main__":
    main()