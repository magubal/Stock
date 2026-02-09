#!/usr/bin/env python3
"""
네이버 블로그 이미지 수집기 (간단 버전)
- RSS 피드 수집 후 링크 목록만 저장
- 수동으로 이미지 캡처 가능
"""

import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urlparse
from pathlib import Path
import re
from typing import List, Dict, Set

class NaverBlogSimpleCollector:
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
    
    def _load_tracked_posts(self) -> Set[str]:
        """이미 저장된 게시물 목록 로드"""
        if self.tracked_posts_file.exists():
            with open(self.tracked_posts_file, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        return set()
    
    def _save_tracked_posts(self):
        """저장된 게시물 목록 업데이트"""
        with open(self.tracked_posts_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.tracked_posts), f, ensure_ascii=False, indent=2)
    
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
    
    def save_post_info(self, post_data: Dict):
        """게시물 정보 저장 (일자별/블로거_순번.txt)"""
        blogger_name = post_data['blogger']
        
        # 수집일자 기준 폴더 구조
        collected_date = datetime.fromisoformat(post_data['collected_date'])
        date_str = collected_date.strftime('%Y-%m-%d')
        
        # 일자별 폴더 생성
        date_dir = self.base_dir / date_str
        date_dir.mkdir(exist_ok=True)
        
        # 파일명 (블로거_순번.txt)
        # 순번은 파일 개수로 계산
        existing_files = list(date_dir.glob(f"{self._sanitize_filename(blogger_name)}_*.txt"))
        sequence = len(existing_files) + 1
        
        filename = f"{self._sanitize_filename(blogger_name)}_{sequence:03d}.txt"
        file_path = date_dir / filename
        
        # 게시물 정보 저장
        content = f"""제목: {post_data['title']}
블로거: {post_data['blogger']}
링크: {post_data['link']}
게시일: {post_data['pub_date']}
수집일: {post_data['collected_date']}

--------------------
이 링크를 이미지로 캡처해주세요:
{post_data['link']}
--------------------
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"정보 저장 완료: {date_str}/{filename} - {post_data['title'][:50]}...")
        return True
    
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
                if self.save_post_info(post):
                    total_collected += 1
        
        # 추적 게시물 목록 업데이트
        self._save_tracked_posts()
        
        print(f"\n총 {total_collected}개의 새로운 게시물 정보를 수집했습니다.")
        print(f"데이터 저장 위치: {self.base_dir}")
        print("\n참고: 저장된 파일들은 링크 정보만 포함합니다.")
        print("실제 이미지 캡처는 full_capture.py를 사용하세요.")

def main():
    """메인 실행 함수"""
    collector = NaverBlogSimpleCollector()
    
    # 처음 실행 시 최근 10개만 수집
    collector.collect_all(max_posts_per_blogger=10)

if __name__ == "__main__":
    main()