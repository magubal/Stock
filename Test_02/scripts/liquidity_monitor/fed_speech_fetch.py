"""
Fed Speech Tone Analyzer
Fed 홈페이지 RSS에서 스피치/성명 키워드 비중을 분석합니다.
Usage: python scripts/liquidity_monitor/fed_speech_fetch.py
"""
import sys
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

sys.stdout.reconfigure(encoding='utf-8')

from config import DB_PATH

from sqlalchemy import create_engine, Column, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
Base = declarative_base()


class FedTone(Base):
    __tablename__ = "fed_tone"
    date = Column(String(10), primary_key=True)
    liquidity_score = Column(Float, default=0.0)
    credit_score = Column(Float, default=0.0)
    stability_score = Column(Float, default=0.0)


Base.metadata.create_all(bind=engine)

# 키워드 사전
LIQUIDITY_KEYWORDS = [
    "liquidity", "funding", "repo", "reverse repo", "money market",
    "cash flow", "balance sheet", "reserves",
]
CREDIT_KEYWORDS = [
    "credit", "lending", "loan", "default", "delinquency",
    "bankruptcy", "nonperforming", "charge-off",
]
STABILITY_KEYWORDS = [
    "financial stability", "systemic risk", "stress test",
    "macroprudential", "contagion", "too big to fail",
]


def fetch_fed_rss():
    """Fed 보도자료 RSS를 가져옵니다."""
    url = "https://www.federalreserve.gov/feeds/press_all.xml"
    try:
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urlopen(req, timeout=15) as resp:
            xml_text = resp.read().decode("utf-8")
            root = ET.fromstring(xml_text)
            items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
            if not items:
                items = root.findall(".//item")
            return items
    except (URLError, ET.ParseError) as e:
        print(f"[ERROR] Fed RSS fetch 실패: {e}")
        return []


def count_keywords(text, keywords):
    """텍스트에서 키워드 출현 횟수를 센다."""
    text_lower = text.lower()
    return sum(len(re.findall(re.escape(kw), text_lower)) for kw in keywords)


def analyze_tone(items):
    """최근 항목들의 키워드 비중을 분석합니다."""
    if not items:
        return 0.0, 0.0, 0.0

    total_words = 0
    liq_count = 0
    cred_count = 0
    stab_count = 0

    for item in items[:20]:  # 최근 20개
        title = ""
        summary = ""

        # Atom format
        title_el = item.find("{http://www.w3.org/2005/Atom}title")
        if title_el is not None and title_el.text:
            title = title_el.text
        summary_el = item.find("{http://www.w3.org/2005/Atom}summary")
        if summary_el is not None and summary_el.text:
            summary = summary_el.text

        # RSS format fallback
        if not title:
            title_el = item.find("title")
            if title_el is not None and title_el.text:
                title = title_el.text
        if not summary:
            desc_el = item.find("description")
            if desc_el is not None and desc_el.text:
                summary = desc_el.text

        text = f"{title} {summary}"
        words = len(text.split())
        total_words += max(words, 1)

        liq_count += count_keywords(text, LIQUIDITY_KEYWORDS)
        cred_count += count_keywords(text, CREDIT_KEYWORDS)
        stab_count += count_keywords(text, STABILITY_KEYWORDS)

    if total_words == 0:
        return 0.0, 0.0, 0.0

    return (
        round(liq_count / total_words, 4),
        round(cred_count / total_words, 4),
        round(stab_count / total_words, 4),
    )


def run():
    """Fed 톤 분석을 실행하여 DB에 저장합니다."""
    print("[FED] Fed 스피치 톤 분석 시작...")

    items = fetch_fed_rss()
    if not items:
        print("[FED] RSS 항목 없음")
        return

    liq, cred, stab = analyze_tone(items)
    today = datetime.now().strftime("%Y-%m-%d")

    session = Session()
    existing = session.query(FedTone).filter_by(date=today).first()
    if existing:
        existing.liquidity_score = liq
        existing.credit_score = cred
        existing.stability_score = stab
    else:
        session.add(FedTone(
            date=today,
            liquidity_score=liq,
            credit_score=cred,
            stability_score=stab,
        ))

    session.commit()
    session.close()
    print(f"[FED] {today} 톤 분석 저장: liquidity={liq}, credit={cred}, stability={stab}")


if __name__ == "__main__":
    run()
