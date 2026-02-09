#!/usr/bin/env python3
"""
네이버 블로그 이미지 수집기
- Playwright로 블로그 글 전체를 이미지로 캡처
- 일자별/블로거_순번.jpg 구조로 저장
"""

import os
import json
import requests
import xml.etree.ElementTree as ET
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse, urlunparse
from pathlib import Path
import re
from typing import List, Dict, Set
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
import tempfile

# 본문 후보 셀렉터(모바일/PC 겸용)
ARTICLE_SELECTORS = [
    ".se-main-container",          # 최신 스마트에디터
    "#postViewArea",               # 구버전
    "article.se_component",        # 일부 테마
    "article[data-role='post']",
    ".se-viewer",                  # 뷰어 래퍼
]

class NaverBlogImageCollector:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = Path(__file__).parent.parent / "data" / "naver_blog_data"
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 인덱스 폴더
        self.index_dir = self.base_dir / "index"
        self.index_dir.mkdir(exist_ok=True)
        
        # RSS 목록 파일
        self.rss_list_file = Path(__file__).parent.parent.parent / "test_data" / "naver_bloger_rss_list.txt"
        
        # 저장된 게시물 추적 파일
        self.tracked_posts_file = self.index_dir / "tracked_posts.json"
        self.tracked_posts = self._load_tracked_posts()
        
        # 일자별 블로거 카운터
        self.daily_counter_file = self.index_dir / "daily_counter.json"
        self.daily_counters = self._load_daily_counters()
        
        # Playwright 상태 파일 (로그인 필요 시)
        self.state_file = self.index_dir / "playwright_state.json"
    
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
    
    def to_mobile(self, url: str) -> str:
        """모바일 URL로 변환"""
        p = urlparse(url)
        if p.netloc.startswith("blog.naver.com"):
            p = p._replace(netloc="m.blog.naver.com")
        return urlunparse(p)
    
    def open_iframe_or_self(self, page, url):
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
    
    def auto_scroll(self, page, step=1500, pause=0.12, loops=400):
        """자동 스크롤로 전체 콘텐츠 로드"""
        last = -1
        for _ in range(loops):
            page.evaluate(f"window.scrollBy(0,{step})")
            time.sleep(pause)
            cur = page.evaluate("window.scrollY")
            if cur == last:
                break
            last = cur
        page.evaluate("window.scrollTo(0,0)")  # 맨 위로
    
    def detect_article_selector(self, page):
        """본문 셀렉터 감지"""
        for sel in ARTICLE_SELECTORS:
            try:
                if page.locator(sel).count() > 0 and page.locator(sel).first.is_visible():
                    return sel
            except:
                pass
        return None
    
    # 본문 외 모두 제거(광고/피드 재로딩 차단)
    PRUNE_JS = """
    (sel) => {
      const el = document.querySelector(sel);
      if (!el) return false;
      // 이미지 지연로딩 해제
      document.querySelectorAll('img[data-src]').forEach(img => { img.src = img.getAttribute('data-src'); });
      // 본문만 남기기
      document.body.style.margin = '0';
      document.body.style.padding = '0';
      document.body.style.backgroundColor = '#ffffff';
      Array.from(document.body.children).forEach(c => { if (!el.contains(c) && c !== el) c.remove(); });
      // 본문을 body의 유일한 자식으로 이동
      if (el.parentElement !== document.body) {
        el.remove();
        document.body.innerHTML = "";
        document.body.appendChild(el);
      }
      // 폭 고정 및 글자색 보존
      el.style.maxWidth = '100%';
      el.style.margin = '0';
      el.style.padding = '20px';
      el.style.backgroundColor = '#ffffff';
      el.style.color = '#000000';
      window.scrollTo(0,0);
      return true;
    }
    """
    
    def capture_blog_image(self, blog_url: str, output_path: Path) -> bool:
        """블로그 글을 이미지로 캡처"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                ctx = browser.new_context(
                    viewport={"width": 1200, "height": 2000}, 
                    device_scale_factor=2,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                
                # 상태 파일이 있으면 로드
                if self.state_file.exists():
                    ctx.add_cookies(json.loads(self.state_file.read_text()))
                
                page = ctx.new_page()
                
                # 모바일 버전이 더 깔끔함
                mobile_url = blog_url.replace("blog.naver.com", "m.blog.naver.com")
                
                self.open_iframe_or_self(page, mobile_url)
                page.wait_for_timeout(2000)  # 로딩 대기
                
                # 자동 스크롤로 전체 콘텐츠 로드
                self.auto_scroll(page)
                page.wait_for_timeout(1000)
                
                # 본문 셀렉터 감지
                sel = self.detect_article_selector(page)
                if not sel:
                    sel = "body"  # 최후 수단
                
                # 본문만 남기기
                page.evaluate(self.PRUNE_JS, sel)
                page.wait_for_timeout(1000)
                
                # 전체 페이지 스크린샷
                output_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=output_path, full_page=True)
                
                browser.close()
                return True
                
        except Exception as e:
            print(f"이미지 캡처 실패 {blog_url}: {e}")
            return False
    
    def collect_blogger_posts(self, blogger_info: Dict, max_posts: int = 10) -> List[Dict]:
        """개별 블로거의 최신 게시물 수집"""
        rss_url = blogger_info['url']
        blogger_name = blogger_info['name']
        
        try:
            # .xml 확장자 추가
            if not rss_url.endswith('.xml'):
                rss_url += '.xml'
            
            response = requests.get(rss_url, timeout=10)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            items = root.find("channel").findall("item")[:max_posts]
            
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
            if self.capture_blog_image(post_data['link'], image_path):
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
                
                # 일자별 요약 업데이트
                self._update_daily_summary(date_str, metadata)
                
                print(f"이미지 저장 완료: {date_str}/{filename} - {post_data['title'][:50]}...")
                return True
            else:
                print(f"이미지 캡처 실패: {post_data['link']}")
                return False
        except Exception as e:
            print(f"이미지 저장 중 오류: {e}")
            return False
    
    def _update_daily_summary(self, date_str: str, metadata: Dict):
        """일자별 요약 업데이트"""
        summary_file = self.index_dir / "daily_summary.json"
        
        # 기존 요약 로드
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary = json.load(f)
        else:
            summary = {}
        
        # 날짜별 요약 업데이트
        if date_str not in summary:
            summary[date_str] = {
                'date': date_str,
                'total_posts': 0,
                'bloggers': {},
                'posts': []
            }
        
        summary[date_str]['total_posts'] += 1
        summary[date_str]['posts'].append({
            'filename': metadata['filename'],
            'blogger': metadata['blogger'],
            'title': metadata['title'],
            'link': metadata['link'],
            'collected_time': metadata['collected_date']
        })
        
        # 블로거별 카운트
        blogger = metadata['blogger']
        if blogger not in summary[date_str]['bloggers']:
            summary[date_str]['bloggers'][blogger] = 0
        summary[date_str]['bloggers'][blogger] += 1
        
        # 요약 저장
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
    
    def collect_all(self, max_posts_per_blogger: int = 10):
        """모든 블로거의 데이터 수집"""
        rss_list = self._load_rss_list()
        
        if not rss_list:
            print("RSS 목록이 비어있습니다.")
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
    
    # 처음 실행 시 최근 10개만 수집
    collector.collect_all(max_posts_per_blogger=10)

if __name__ == "__main__":
    main()