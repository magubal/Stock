#!/usr/bin/env python3
"""
네이버 블로그 데이터 수집 스케줄러
- 매일 자동 실행을 위한 스케줄러
"""

import schedule
import time
from datetime import datetime
from naver_blog_collector import NaverBlogCollector
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('naver_blog_scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def run_daily_collection():
    """매일 데이터 수집 실행"""
    logging.info("=== 네이버 블로그 데이터 수집 시작 ===")
    
    try:
        collector = NaverBlogCollector()
        collector.collect_all(max_posts_per_blogger=5)  # 매일은 5개만 수집
        logging.info("데이터 수집 완료")
    except Exception as e:
        logging.error(f"데이터 수집 중 오류 발생: {e}")

def main():
    """메인 스케줄러"""
    logging.info("네이버 블로그 수집 스케줄러 시작")
    
    # 매일 오전 9시에 실행
    schedule.every().day.at("09:00").do(run_daily_collection)
    
    # 테스트를 위한 즉시 실행 (주석 처리 가능)
    # run_daily_collection()
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # 1분마다 체크

if __name__ == "__main__":
    main()