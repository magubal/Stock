#!/usr/bin/env python3
"""
단일 블로그 이미지 테스트
- 전체 스크롤 포함 캡처 테스트
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
        
        # iframe 처리
        try:
            iframe = driver.find_element(By.ID, "mainFrame")
            driver.switch_to.frame(iframe)
            print("iframe 처리 완료")
        except Exception as e:
            print(f"iframe 처리 실패 또는 없음: {e}")
        
        # 페이지 높이 확인 및 전체 콘텐츠 로드
        print("전체 스크롤 시작...")
        
        # 여러 번 스크롤하며 모든 콘텐츠 로드
        for i in range(10):
            driver.execute_script("window.scrollBy(0, 1000)")
            time.sleep(0.5)
        
        # 맨 위로
        driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(1)
        
        # 페이지 전체 높이 가져오기
        total_height = driver.execute_script("return document.body.scrollHeight")
        viewport_height = driver.execute_script("return window.innerHeight")
        
        print(f"전체 페이지 높이: {total_height}px")
        print(f"뷰포트 높이: {viewport_height}px")
        
        # 여러 번 스크린샷 찍어서 이어 붙이기
        screenshots = []
        current_position = 0
        
        while current_position < total_height:
            driver.execute_script(f"window.scrollTo(0, {current_position})")
            time.sleep(0.5)
            
            # 현재 뷰포트 스크린샷
            temp_path = f"temp_{current_position}.png"
            driver.save_screenshot(temp_path)
            screenshots.append(temp_path)
            
            current_position += viewport_height - 50  # 약간 겹치게
            
            if current_position >= total_height:
                break
        
        # 스크린샷 합치기
        print("이미지 합치기...")
        images = [Image.open(path) for path in screenshots]
        
        # 총 높이 계산
        total_width = images[0].width
        total_stitch_height = 0
        
        # 마지막 이미지의 실제 높이 조정
        processed_images = []
        for i, img in enumerate(images):
            if i == len(images) - 1:
                # 마지막 이미지는 필요한 만큼만 잘라내기
                remaining = total_height - total_stitch_height
                if remaining < img.height:
                    img = img.crop((0, 0, total_width, remaining))
            processed_images.append(img)
            total_stitch_height += img.height
        
        # 최종 이미지 생성
        final_image = Image.new('RGB', (total_width, total_stitch_height))
        
        # 이미지 이어 붙이기
        y_position = 0
        for img in processed_images:
            final_image.paste(img, (0, y_position))
            y_position += img.height
        
        # JPG로 저장
        final_image.save(output_path, 'JPEG', quality=85, optimize=True)
        
        # 임시 파일 삭제
        for path in screenshots:
            os.remove(path)
        
        print(f"성공! 이미지 저장 완료: {output_path}")
        return True
        
    except Exception as e:
        print(f"실패: {e}")
        return False
    finally:
        driver.quit()

def main():
    test_url = "https://blog.naver.com/allsix6/224167698066"
    output_path = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02/data/test_full_capture.jpg"
    
    print("전체 스크롤 이미지 캡처 테스트 시작...")
    capture_full_blog_image(test_url, output_path)

if __name__ == "__main__":
    main()