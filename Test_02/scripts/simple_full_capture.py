#!/usr/bin/env python3
"""
간단한 전체 스크롤 캡처 테스트
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from PIL import Image
import os

def capture_full_blog_image(blog_url: str, output_path: str):
    """전체 블로그 글 캡처"""
    
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
        
        # 페이지 로딩 대기
        time.sleep(3)
        
        # iframe 처리 (모바일에는 없을 수 있음)
        try:
            iframe = driver.find_element(By.ID, "mainFrame")
            driver.switch_to.frame(iframe)
            print("iframe 처리 완료")
        except:
            print("iframe 없음 - 모바일 버전 직접 접근")
        
        # 전체 콘텐츠 로드를 위해 여러 번 스크롤
        print("전체 스크롤 시작...")
        for i in range(20):
            driver.execute_script("window.scrollBy(0, 1000)")
            time.sleep(0.5)
        
        # 맨 위로
        driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(1)
        
        # 전체 페이지 스크린샷 (Chrome의 기능 사용)
        print("전체 페이지 스크린샷...")
        
        # 전체 페이지 높이 계산
        total_height = driver.execute_script("return document.body.scrollHeight")
        print(f"전체 높이: {total_height}px")
        
        # 너무 크면 분할 캡처
        if total_height > 30000:
            print("페이지가 너무 길어서 분할 캡처합니다...")
            return capture_in_sections(driver, output_path, total_height)
        else:
            # 한 번에 캡처
            driver.set_window_size(1200, total_height + 100)
            time.sleep(2)
            
            temp_png = output_path.replace('.jpg', '.png')
            driver.save_screenshot(temp_png)
            
            # PNG를 JPG로 변환
            img = Image.open(temp_png)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(output_path, 'JPEG', quality=85)
            os.remove(temp_png)
            
            print(f"이미지 저장 완료: {output_path}")
            return True
        
    except Exception as e:
        print(f"실패: {e}")
        return False
    finally:
        driver.quit()

def capture_in_sections(driver, output_path, total_height):
    """분할하여 캡처"""
    try:
        viewport_height = 600
        screenshots = []
        
        current_position = 0
        while current_position < total_height:
            driver.execute_script(f"window.scrollTo(0, {current_position})")
            time.sleep(0.5)
            
            temp_file = f"temp_{len(screenshots)}.png"
            driver.save_screenshot(temp_file)
            screenshots.append(temp_file)
            
            current_position += viewport_height - 50
            if current_position >= total_height:
                break
        
        # 이미지 합치기
        images = [Image.open(path) for path in screenshots]
        total_width = images[0].width
        total_img_height = sum(img.height for img in images)
        
        final_image = Image.new('RGB', (total_width, total_img_height))
        y_pos = 0
        for img in images:
            final_image.paste(img, (0, y_pos))
            y_pos += img.height
        
        final_image.save(output_path, 'JPEG', quality=85)
        
        # 임시 파일 삭제
        for path in screenshots:
            os.remove(path)
        
        print(f"분할 캡처 완료: {output_path}")
        return True
        
    except Exception as e:
        print(f"분할 캡처 실패: {e}")
        return False

def main():
    test_url = "https://blog.naver.com/allsix6/224167698066"
    output_path = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02/data/test_full_capture.jpg"
    
    print("간단한 전체 스크롤 캡처 테스트 시작...")
    capture_full_blog_image(test_url, output_path)

if __name__ == "__main__":
    main()