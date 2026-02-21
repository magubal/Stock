#!/usr/bin/env python3
"""
네이버 블로그 데이터 자동 수집기
- 매일 최신 블로그 글을 수집하여 이미지와 함께 저장
- 일자별/블로거_순번 구조로 데이터 저장
- 중복 체크 및 자동 증분 저장 기능
"""

import os
import sys
import json
import hashlib
import requests

sys.stdout.reconfigure(encoding="utf-8")
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
from pathlib import Path
import re
from typing import List, Dict, Set

# 본문 캡처 모듈 import (세션 재사용)
from final_body_capture import BlogCaptureSession


def is_within_days(pub_date_str: str, days: int):
    """pub_date가 최근 N일 이내인지 확인.

    Returns:
        (result, reason)
        - (True, "within") : N일 이내
        - (True, "no_date") : pub_date 없음 → 수집 허용
        - (True, "parse_fail") : 파싱 실패 → 수집 허용
        - (False, "too_old") : N일 초과 → skip
    """
    if not pub_date_str or not pub_date_str.strip():
        return True, "no_date"
    try:
        pub_dt = parsedate_to_datetime(pub_date_str.strip())
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=days)
        if pub_dt >= cutoff:
            return True, "within"
        else:
            return False, "too_old"
    except Exception:
        return True, "parse_fail"


class NaverBlogCollector:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = Path(__file__).parent.parent / "data" / "naver_blog_data"
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 인덱스 폴더
        self.index_dir = self.base_dir / "index"
        self.index_dir.mkdir(exist_ok=True)
        
        # RSS 목록 파일
        self.rss_list_file = Path(__file__).parent.parent / "data" / "naver_blog_data" / "naver_bloger_rss_list.txt"
        
        # 저장된 게시물 추적 파일
        self.tracked_posts_file = self.index_dir / "tracked_posts.json"
        self.tracked_posts = self._load_tracked_posts()
        
        # 일자별 블로거 카운터
        self.daily_counter_file = self.index_dir / "daily_counter.json"
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
    
    def _download_image(self, img_url: str, save_path: Path) -> bool:
        """이미지 다운로드"""
        try:
            response = requests.get(img_url, timeout=10)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
        except Exception as e:
            print(f"이미지 다운로드 실패 {img_url}: {e}")
            return False
    
    def _extract_images_from_content(self, content: str) -> List[str]:
        """블로그 내용에서 이미지 URL 추출"""
        img_pattern = r'<img[^>]+src="([^"]+)"'
        matches = re.findall(img_pattern, content)
        return [url for url in matches if url.startswith('http')]
    
    def _extract_blog_content(self, blog_url: str) -> Dict:
        """네이버 블로그 본문 내용 추출"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(blog_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 간단한 내용 추출 (실제로는 더 복잡한 파싱 필요)
            title_match = re.search(r'<meta property="og:title" content="([^"]+)"', response.text)
            desc_match = re.search(r'<meta property="og:description" content="([^"]+)"', response.text)
            
            title = title_match.group(1) if title_match else ""
            description = desc_match.group(1) if desc_match else ""
            
            # 이미지 URL 추출
            images = self._extract_images_from_content(response.text)
            
            return {
                'title': title,
                'description': description,
                'content': response.text[:2000],  # 앞부분 2000자만 저장
                'images': images
            }
        except Exception as e:
            print(f"블로그 내용 추출 실패 {blog_url}: {e}")
            return {'title': '', 'description': '', 'content': '', 'images': []}
    
    def collect_blogger_posts(self, blogger_info: Dict, max_posts: int = 10, days: int = 3) -> List[Dict]:
        """개별 블로거의 최신 게시물 수집

        Args:
            blogger_info: {'url': rss_url, 'name': blogger_name}
            max_posts: RSS에서 가져올 최대 아이템 수
            days: pub_date 기준 최근 N일 이내만 수집 (0=필터 없음)
        """
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

                # pub_date 날짜 필터 (days=0이면 비활성)
                if days > 0:
                    within, reason = is_within_days(pub_date, days)
                    if not within:
                        print(f"    [SKIP-DATE] {title[:40]} (pub: {pub_date.strip()}, reason: {reason})")
                        continue
                    if reason in ("no_date", "parse_fail"):
                        print(f"    [WARN] pubDate {reason}: {title[:40]}")

                # 게시물 ID 생성 (URL 기준 - Stable Hash)
                post_id = hashlib.md5(link.encode('utf-8')).hexdigest()
                
                # 이미 저장된 게시물인지 확인
                if str(post_id) in self.tracked_posts:
                    continue
                
                # 블로그 내용 추출
                blog_content = self._extract_blog_content(link)
                
                post_data = {
                    'id': str(post_id),
                    'blogger': blogger_name,
                    'title': title,
                    'link': link,
                    'pub_date': pub_date,
                    'collected_date': datetime.now().isoformat(),
                    'content': blog_content['title'] + '\n\n' + blog_content['description'],
                    'images': blog_content['images']
                }
                
                collected_posts.append(post_data)
                self.tracked_posts.add(str(post_id))
            
            return collected_posts
            
        except Exception as e:
            print(f"RSS 수집 실패 {blogger_name} ({rss_url}): {e}")
            return []
    
    def save_post(self, post_data: Dict, capture_session):
        """게시물 저장 (브라우저 세션 재사용)"""
        blogger_name = post_data['blogger']
        blog_link = post_data['link']
        
        # 수집일자 기준 폴더 구조
        collected_date = datetime.fromisoformat(post_data['collected_date'])
        date_str = collected_date.strftime('%Y-%m-%d')
        
        # 본문 이미지 캡처 (세션 재사용)
        print(f"[캡처] {blogger_name}: {post_data['title'][:30]}...")
        capture_result = capture_session.capture(blog_link, blogger_name)
        
        if capture_result['success']:
            image_path = Path(capture_result['file_path'])
            metadata_path = image_path.with_suffix('.json')
            
            metadata = {
                'blogger': blogger_name,
                'title': post_data['title'],
                'link': blog_link,
                'pub_date': post_data['pub_date'],
                'collected_date': post_data['collected_date'],
                'image_file': image_path.name,
                'file_size_mb': capture_result['file_size_mb']
            }
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            self._update_daily_summary(date_str, image_path.stem, metadata)
            print(f"  → {image_path.name} ({capture_result['file_size_mb']}MB)")
        else:
            print(f"  → 실패: {capture_result['message']}")
    
    def collect_all(self, max_posts_per_blogger: int = 10, days: int = 3):
        """모든 블로거의 데이터 수집 (브라우저 재사용)

        Args:
            max_posts_per_blogger: 블로거당 RSS 최대 아이템 수
            days: pub_date 기준 최근 N일 이내만 수집 (0=필터 없음)
        """
        rss_list = self._load_rss_list()
        
        if not rss_list:
            print("RSS 목록이 비어있습니다.")
            return
        
        total_collected = 0
        all_posts = []
        
        # 1단계: 모든 블로거의 글 목록 수집 (빠름)
        for blogger_info in rss_list:
            print(f"\n[RSS] {blogger_info['name']} 목록 수집 중...")
            posts = self.collect_blogger_posts(blogger_info, max_posts_per_blogger, days=days)
            all_posts.extend(posts)
        
        if not all_posts:
            print("\n새로운 게시물이 없습니다.")
            return
        
        print(f"\n총 {len(all_posts)}개 글 캡처 시작...")
        
        # 2단계: 브라우저 한 번 열고 모든 글 캡처 (효율적)
        try:
            with BlogCaptureSession() as session:
                for post in all_posts:
                    self.save_post(post, session)
                    total_collected += 1
        except Exception as e:
            print(f"\n⚠️ 캡처 중 오류: {e}")
        finally:
            # 추적 게시물 목록 및 카운터 업데이트 (항상 저장)
            self._save_tracked_posts()
            self._save_daily_counters()
        
        print(f"\n✅ 총 {total_collected}개 게시물 수집 완료!")
        print(f"📁 저장 위치: {self.base_dir}")
    
    def _update_daily_summary(self, date_str: str, post_folder: str, metadata: Dict):
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
            'folder': post_folder,
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
    
    def get_recent_posts(self, days: int = 3) -> Dict:
        """최근 일자별 게시물 요약 가져오기"""
        summary_file = self.index_dir / "daily_summary.json"
        
        if not summary_file.exists():
            return {}
        
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary = json.load(f)
        
        # 최근 며칠치만 필터링
        recent_dates = []
        today = datetime.now().date()
        
        for i in range(days):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            if date_str in summary:
                recent_dates.append(date_str)
        
        return {date: summary[date] for date in sorted(recent_dates, reverse=True)}

def main():
    """메인 실행 함수"""
    import argparse
    parser = argparse.ArgumentParser(description="네이버 블로그 수집기")
    parser.add_argument("--days", type=int, default=3,
                        help="최근 N일 이내 발행 글만 수집 (0=필터없음, 기본=3)")
    parser.add_argument("--max-posts", type=int, default=10,
                        help="블로거당 RSS 최대 아이템 수 (기본=10)")
    args = parser.parse_args()

    collector = NaverBlogCollector()
    collector.collect_all(max_posts_per_blogger=args.max_posts, days=args.days)

if __name__ == "__main__":
    main()