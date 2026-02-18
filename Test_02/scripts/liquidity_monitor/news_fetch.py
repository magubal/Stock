"""
Google News RSS Fetcher
무료 Google News RSS로 위기 키워드 뉴스를 수집합니다.
Usage: python scripts/liquidity_monitor/news_fetch.py
"""
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import quote

sys.stdout.reconfigure(encoding='utf-8')

from config import NEWS_KEYWORDS, DB_PATH

from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
Base = declarative_base()


class LiquidityNews(Base):
    __tablename__ = "liquidity_news"
    date = Column(String(10), primary_key=True)
    keyword = Column(String(100), primary_key=True)
    count = Column(Integer, default=0)
    sample_titles = Column(Text)


Base.metadata.create_all(bind=engine)


def fetch_google_news_rss(keyword, max_titles=5):
    """Google News RSS에서 키워드 검색 결과를 가져옵니다."""
    encoded = quote(keyword)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"

    try:
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urlopen(req, timeout=15) as resp:
            xml_text = resp.read().decode("utf-8")
            root = ET.fromstring(xml_text)
            items = root.findall(".//item")
            titles = []
            for item in items[:max_titles]:
                title_el = item.find("title")
                if title_el is not None and title_el.text:
                    titles.append(title_el.text)
            return len(items), titles
    except (URLError, ET.ParseError) as e:
        print(f"[ERROR] Google News '{keyword}' fetch 실패: {e}")
        return 0, []


def run():
    """모든 키워드에 대해 뉴스 카운트를 수집하여 DB에 저장합니다."""
    print("[NEWS] 위기 키워드 뉴스 수집 시작...")

    session = Session()
    today = datetime.now().strftime("%Y-%m-%d")
    total = 0

    for keyword in NEWS_KEYWORDS:
        print(f"  Searching '{keyword}'...")
        count, titles = fetch_google_news_rss(keyword)
        sample = " | ".join(titles) if titles else ""

        existing = session.query(LiquidityNews).filter_by(
            date=today, keyword=keyword
        ).first()

        if existing:
            existing.count = count
            existing.sample_titles = sample
        else:
            session.add(LiquidityNews(
                date=today, keyword=keyword,
                count=count, sample_titles=sample,
            ))
        total += count
        time.sleep(1)  # Rate limiting

    session.commit()
    session.close()
    print(f"[NEWS] {today} 총 {total}건 뉴스 키워드 저장 완료")


if __name__ == "__main__":
    run()
