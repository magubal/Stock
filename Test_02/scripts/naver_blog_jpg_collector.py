#!/usr/bin/env python3
"""
네이버 블로그 이미지 수집기 (간단 버전)
- selenium으로 이미지 캡처
- 일자별/블로거_순번.jpg 구조
"""

import os
import json
import requests
import xml.etree.ElementTree as ET
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse
from pathlib import Path
import re
from typing import List, Dict, Set

# playwright 및 selenium 임포트
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class NaverBlogImageCollector:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = Path(__file__).parent.parent / "data" / "naver_blog_data"
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # RSS 목록 파일
        self.rss_list_file = Path(__file__).parent.parent.parent / "test_data" / "naver_bloger_rss_list.txt"
        
        # 저장된 게시물 추적 파일
        self.tracked_posts_file = self.base_dir / "tracked_posts.json"
        self.tracked_posts = self._load_tracked_posts()
        
        # 일자별 블로거 카운터
        self.daily_counter_file = self.base_dir / "daily_counter.json"
        self.daily_counters = self._load_daily_counters()
    
    def _load_tracked_posts(self) -> Set[str]:
        """이미 저장된 게시물 목록 로드"""
        if self.tracked_posts_file.exists():
            with open(self.tracked_posts_file, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        return set()
    
    def _load_daily_counters(self) -> Dict[str, Dict[str, int]]:
        """일자별 블로거 카운터 로드"""
        if self.daily_counter_file.exists():
            with open(self.daily_counter_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_tracked_posts(self):
        """저장된 게시물 목록 업데이트"""
        with open(self.tracked_posts_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.tracked_posts), f, ensure_ascii=False, indent=2)
    
    def _save_daily_counters(self):
        """일자별 블로거 카운터 저장"""
        with open(self.daily_counter_file, 'w', encoding='utf-8') as f:
            json.dump(self.daily_counters, f, ensure_ascii=False, indent=2)
    
    def _get_next_sequence(self, date_str: str, blogger_name: str) -> int:
        """일자별 블로거 다음 순번 가져오기"""
        if date_str not in self.daily_counters:
            self.daily_counters[date_str] = {}
        
        if blogger_name not in self.daily_counters[date_str]:
            self.daily_counters[date_str][blogger_name] = 0
        
        self.daily_counters[date_str][blogger_name] += 1
        return self.daily_counters[date_str][blogger_name]
    
    def _load_rss_list(self) -> List[Dict[str, str]]:
        """RSS 피드 목록 로드"""
        rss_list = []
        if not self.rss_list_file.exists():
            print(f"RSS 목록 파일을 찾을 수 없습니다: {self.rss_list_file}")
            return rss_list
            
        with open(self.rss_list_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split('#')
                    rss_url = parts[0].strip()
                    blogger_name = parts[1].strip() if len(parts) > 1 else "미정"
                    rss_list.append({
                        'url': rss_url,
                        'name': blogger_name
                    })
        return rss_list
    
    def _sanitize_filename(self, filename: str) -> str:
        """파일명에서 사용 불가능한 문자 제거"""
        return re.sub(r'[<>:"/\\|?*]', '_', filename)[:100]
    
    def capture_blog_image_playwright(self, blog_url: str, output_path: Path) -> bool:
        """Playwright로 정밀한 블로그 글 이미지 캡처"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                ctx = browser.new_context(
                    viewport={"width": 1200, "height": 800}, 
                    device_scale_factor=1.5,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                
                page = ctx.new_page()
                
                # 모바일 버전으로 접속
                mobile_url = blog_url.replace("blog.naver.com", "m.blog.naver.com")
                print(f"접속: {mobile_url}")
                
                # iframe 처리 후 페이지 로드
                self._open_iframe_or_self(page, mobile_url)
                page.wait_for_timeout(3000)
                
                # 자동 스크롤로 전체 콘텐츠 로드
                print("전체 스크롤 시작...")
                self._auto_scroll_precise(page)
                page.wait_for_timeout(2000)
                
                # 본문 셀렉터 감지
                sel = self._detect_article_selector(page)
                if not sel:
                    sel = "body"
                    print("본문 셀렉터를 찾지 못해 body 사용")
                else:
                    print(f"본문 셀렉터 발견: {sel}")
                
                # 본문만 남기기
                print("본문 외 요소 제거 중...")
                ok = page.evaluate(self._PRUNE_JS, sel)
                if ok:
                    print("본문 정리 성공")
                else:
                    print("본문 정리 실패 - 전체 페이지 캡처")
                
                page.wait_for_timeout(2000)
                
                # 페이지 최종 높이 확인
                final_height = page.evaluate("document.body.scrollHeight")
                print(f"최종 콘텐츠 높이: {final_height}px")
                
                # 뷰포트 크기 조정 및 스크린샷
                page.set_viewport_size({"width": 1200, "height": final_height + 100})
                page.wait_for_timeout(1000)
                
                # 스크린샷 저장
                output_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(output_path), full_page=True)
                
                # PNG를 JPG로 변환 (고압축)
                try:
                    img = Image.open(output_path)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # 고압축 JPG 저장
                    temp_png = output_path.with_suffix('.png')
                    output_path.rename(temp_png)
                    
                    img.save(output_path, 'JPEG', quality=60, optimize=True, progressive=True)
                    temp_png.unlink()
                    
                    file_size = output_path.stat().st_size / 1024 / 1024
                    print(f"JPG 변환 완료: {output_path} ({file_size:.2f} MB)")
                    
                except Exception as e:
                    print(f"JPG 변환 실패: {e}")
                
                browser.close()
                return True
                
        except Exception as e:
            print(f"Playwright 캡처 실패: {e}")
            return False
    
    def _open_iframe_or_self(self, page, url):
        """iframe 처리 후 페이지 로드"""
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
        except TimeoutError:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # 네이버 블로그 iframe 처리
        f = page.query_selector("iframe#mainFrame")
        if f:
            src = f.get_attribute("src")
            if src and src.startswith("http"):
                page.goto(src, wait_until="networkidle")
    
    def _auto_scroll_precise(self, page, step=800, pause=0.2, loops=300):
        """정밀한 자동 스크롤"""
        last_position = -1
        scroll_count = 0
        
        for i in range(loops):
            current_position = page.evaluate("window.scrollY")
            
            # 스크롤
            page.evaluate(f"window.scrollBy(0,{step})")
            time.sleep(pause)
            
            new_position = page.evaluate("window.scrollY")
            
            # 진행 상황 출력
            if i % 30 == 0:
                print(f"스크롤 진행: {new_position}px")
            
            # 스크롤이 멈추면 종료
            if new_position == last_position and new_position != 0:
                scroll_count += 1
                if scroll_count >= 3:
                    print(f"스크롤 멈춤: {new_position}px")
                    break
            else:
                scroll_count = 0
            
            last_position = new_position
            
            # 페이지 끝에 도달
            if page.evaluate("window.innerHeight + window.scrollY >= document.body.scrollHeight"):
                print("페이지 끝 도달")
                break
        
        page.evaluate("window.scrollTo(0,0)")
    
    def _detect_article_selector(self, page):
        """본문 셀렉터 감지"""
        ARTICLE_SELECTORS = [
            ".se-main-container",
            "#postViewArea",
            "article.se_component",
            "article[data-role='post']",
            ".se-viewer",
        ]
        
        for sel in ARTICLE_SELECTORS:
            try:
                if page.locator(sel).count() > 0 and page.locator(sel).first.is_visible():
                    return sel
            except:
                pass
        return None
    
    # 본문 외 모두 제거 JavaScript
    _PRUNE_JS = """
    (sel) => {
      const el = document.querySelector(sel);
      if (!el) return false;
      
      // 이미지 지연로딩 해제
      document.querySelectorAll('img[data-src]').forEach(img => { 
        img.src = img.getAttribute('data-src'); 
      });
      
      // 본문만 남기기
      document.body.style.margin = '0';
      document.body.style.padding = '0';
      document.body.style.backgroundColor = '#ffffff';
      
      // 본문 외 요소 제거
      Array.from(document.body.children).forEach(c => { 
        if (!el.contains(c) && c !== el) c.remove(); 
      });
      
      // 본문을 body의 유일한 자식으로 이동
      if (el.parentElement !== document.body) {
        el.remove();
        document.body.innerHTML = "";
        document.body.appendChild(el);
      }
      
      // 스타일 정리
      el.style.maxWidth = '100%';
      el.style.margin = '0';
      el.style.padding = '20px';
      el.style.backgroundColor = '#ffffff';
      el.style.color = '#000000';
      
      window.scrollTo(0,0);
      return true;
    }
    """
    
    def _capture_in_sections(self, driver, output_path: Path, total_height: int) -> bool:
        """분할하여 캡처 (겹침 방지 + 압축)"""
        try:
            viewport_height = 800  # 더 큰 뷰포트
            screenshots = []
            
            current_position = 0
            section_number = 0
            
            while current_position < total_height:
                driver.execute_script(f"window.scrollTo(0, {current_position})")
                time.sleep(0.8)  # 안정적인 로딩을 위해 더 대기
                
                temp_file = f"temp_{section_number}.png"
                driver.save_screenshot(temp_file)
                screenshots.append(temp_file)
                section_number += 1
                
                # 겹침 없이 다음 섹션으로 이동
                current_position += viewport_height
                if current_position >= total_height:
                    break
            
            # 이미지 합치기 (겹침 방지 로직)
            images = [Image.open(path) for path in screenshots]
            
            if not images:
                return False
            
            # 각 이미지에서 실제 콘텐츠 영역만 잘라내기
            cropped_images = []
            total_width = images[0].width
            
            for i, img in enumerate(images):
                # 첫 이미지는 그대로, 나머지는 상단 일부 잘라냄 (겹침 방지)
                if i == 0:
                    cropped_img = img
                else:
                    # 상단 50px 잘라내기 (이전 이미지와 겹치는 부분 제거)
                    cropped_img = img.crop((0, 50, total_width, img.height))
                
                if cropped_img.height > 0:  # 빈 이미지가 아닌 경우만 추가
                    cropped_images.append(cropped_img)
            
            # 최종 이미지 합치기
            total_img_height = sum(img.height for img in cropped_images)
            final_image = Image.new('RGB', (total_width, total_img_height))
            
            y_pos = 0
            for img in cropped_images:
                final_image.paste(img, (0, y_pos))
                y_pos += img.height
            
            # 고압축 JPG로 저장
            final_image.save(output_path, 'JPEG', quality=70, optimize=True, progressive=True)
            
            # 임시 파일 삭제
            for path in screenshots:
                os.remove(path)
            
            print(f"분할 캡처 완료 (압축): {output_path}")
            return True
            
        except Exception as e:
            print(f"분할 캡처 실패: {e}")
            return False
    
    def collect_blogger_posts(self, blogger_info: Dict, max_posts: int = 3) -> List[Dict]:
        """개별 블로거의 최신 게시물 수집 (소량만 테스트)"""
        rss_url = blogger_info['url']
        blogger_name = blogger_info['name']
        
        try:
            # .xml 확장자 추가
            if not rss_url.endswith('.xml'):
                rss_url += '.xml'
            
            response = requests.get(rss_url, timeout=10)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            channel = root.find("channel")
            if channel is None:
                print(f"RSS 채널을 찾을 수 없음: {rss_url}")
                return []
                
            items = channel.findall("item")[:max_posts]
            
            collected_posts = []
            
            for item in items:
                title = item.findtext("title", "").strip()
                link = item.findtext("link", "").strip()
                pub_date = item.findtext("pubDate", "")
                
                if not link:
                    continue
                
                # 게시물 ID 생성 (URL 기준)
                post_id = str(hash(link))
                
                # 이미 저장된 게시물인지 확인
                if post_id in self.tracked_posts:
                    continue
                
                post_data = {
                    'id': post_id,
                    'blogger': blogger_name,
                    'title': title,
                    'link': link,
                    'pub_date': pub_date,
                    'collected_date': datetime.now().isoformat()
                }
                
                collected_posts.append(post_data)
                self.tracked_posts.add(post_id)
            
            return collected_posts
            
        except Exception as e:
            print(f"RSS 수집 실패 {blogger_name} ({rss_url}): {e}")
            return []
    
    def save_post_as_image(self, post_data: Dict):
        """게시물을 이미지로 저장"""
        blogger_name = post_data['blogger']
        
        # 수집일자 기준 폴더 구조
        collected_date = datetime.fromisoformat(post_data['collected_date'])
        date_str = collected_date.strftime('%Y-%m-%d')
        
        # 다음 순번 가져오기
        sequence = self._get_next_sequence(date_str, blogger_name)
        
        # 일자별 폴더 생성
        date_dir = self.base_dir / date_str
        date_dir.mkdir(exist_ok=True)
        
        # 이미지 파일명 (블로거_순번.jpg)
        filename = f"{self._sanitize_filename(blogger_name)}_{sequence:03d}.jpg"
        image_path = date_dir / filename
        
        # 블로그 글 이미지 캡처
        try:
            if self.capture_blog_image_playwright(post_data['link'], image_path):
                # 메타데이터 저장
                metadata = {
                    **post_data,
                    'date_folder': date_str,
                    'filename': filename,
                    'sequence': sequence,
                    'image_path': str(image_path.relative_to(self.base_dir))
                }
                
                # 이미지 메타데이터 파일 저장
                metadata_path = image_path.with_suffix('.json')
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                
                print(f"✅ 이미지 저장 완료: {date_str}/{filename} - {post_data['title'][:50]}...")
                return True
            else:
                print(f"❌ 이미지 캡처 실패: {post_data['link']}")
                return False
        except Exception as e:
            print(f"이미지 저장 중 오류: {e}")
            return False
    
    def collect_all(self, max_posts_per_blogger: int = 3):
        """모든 블로거의 데이터 수집 (소량만 테스트)"""
        rss_list = self._load_rss_list()
        
        if not rss_list:
            print("RSS 목록이 비어있습니다.")
            return
        
        if not SELENIUM_AVAILABLE:
            print("Selenium이 설치되지 않아 이미지 캡처를 할 수 없습니다.")
            print("설치 명령: pip install selenium")
            return
        
        total_collected = 0
        
        for blogger_info in rss_list:
            print(f"\n{blogger_info['name']} 블로거 데이터 수집 중...")
            posts = self.collect_blogger_posts(blogger_info, max_posts_per_blogger)
            
            for post in posts:
                if self.save_post_as_image(post):
                    total_collected += 1
        
        # 추적 게시물 목록 및 카운터 업데이트
        self._save_tracked_posts()
        self._save_daily_counters()
        
        print(f"\n총 {total_collected}개의 새로운 게시물을 수집했습니다.")
        print(f"데이터 저장 위치: {self.base_dir}")

def main():
    """메인 실행 함수"""
    collector = NaverBlogImageCollector()
    
    # 테스트용으로 소량만 수집
    collector.collect_all(max_posts_per_blogger=2)

if __name__ == "__main__":
    main()