"""
Liquidity & Credit Stress Monitor - Seed Data Generator
30일간 데모 데이터를 생성하여 SQLite DB에 삽입합니다.
Usage: cd backend && python -m scripts.liquidity_monitor.seed_data
  또는: python scripts/liquidity_monitor/seed_data.py
"""

import os
import random
import math
from datetime import datetime, timedelta

from sqlalchemy import create_engine, Column, String, Float, Integer, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func

# DB 경로
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'stock_research.db')
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)

# 독립 모델 정의 (app.config 의존성 회피)
Base = declarative_base()

class LiquidityMacro(Base):
    __tablename__ = "liquidity_macro"
    date = Column(String(10), primary_key=True)
    hy_oas = Column(Float)
    ig_oas = Column(Float)
    sofr = Column(Float)
    rrp_balance = Column(Float)
    dgs2 = Column(Float)
    dgs10 = Column(Float)
    dgs30 = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LiquidityPrice(Base):
    __tablename__ = "liquidity_price"
    date = Column(String(10), primary_key=True)
    symbol = Column(String(20), primary_key=True)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)
    volume = Column(Float)

class LiquidityNews(Base):
    __tablename__ = "liquidity_news"
    date = Column(String(10), primary_key=True)
    keyword = Column(String(100), primary_key=True)
    count = Column(Integer, default=0)
    sample_titles = Column(Text)

class FedTone(Base):
    __tablename__ = "fed_tone"
    date = Column(String(10), primary_key=True)
    liquidity_score = Column(Float, default=0.0)
    credit_score = Column(Float, default=0.0)
    stability_score = Column(Float, default=0.0)

class StressIndex(Base):
    __tablename__ = "stress_index"
    date = Column(String(10), primary_key=True)
    vol_score = Column(Float)
    credit_score = Column(Float)
    funding_score = Column(Float)
    treasury_score = Column(Float)
    news_score = Column(Float)
    fed_tone_score = Column(Float)
    total_score = Column(Float)
    level = Column(String(20))

Base.metadata.create_all(bind=engine)


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def normalize(value, low, high):
    if value is None:
        return 0.0
    return clamp((value - low) / (high - low))


def score_to_level(score):
    if score < 0.25:
        return "normal"
    elif score < 0.40:
        return "watch"
    elif score < 0.55:
        return "caution"
    elif score < 0.75:
        return "stress"
    else:
        return "crisis"


def generate_seed_data(days=30):
    """30일간 시뮬레이션 데이터 생성"""
    session = Session()

    # 기존 데이터 삭제
    for model in [StressIndex, FedTone, LiquidityNews, LiquidityPrice, LiquidityMacro]:
        session.query(model).delete()
    session.commit()

    today = datetime.now().date()
    base_date = today - timedelta(days=days)

    # 시나리오: 서서히 스트레스가 올라가다가 중간에 안정, 최근 다시 상승
    for i in range(days):
        dt = base_date + timedelta(days=i)
        date_str = dt.isoformat()

        # 스트레스 곡선: 사인파 + 약간의 상승 트렌드
        t = i / days
        trend = 0.15 + 0.20 * t  # 서서히 상승
        wave = 0.08 * math.sin(2 * math.pi * t * 2.5)  # 파동
        noise = random.uniform(-0.05, 0.05)
        base_stress = clamp(trend + wave + noise, 0.05, 0.85)

        # ── 1. FRED Macro Data ──
        hy_oas = 3.0 + base_stress * 3.0 + random.uniform(-0.1, 0.1)
        ig_oas = 0.7 + base_stress * 0.5 + random.uniform(-0.05, 0.05)
        sofr = 4.30 + base_stress * 0.3 + random.uniform(-0.02, 0.02)
        rrp_balance = 150 - base_stress * 80 + random.uniform(-5, 5)
        dgs2 = 3.8 + base_stress * 0.5 + random.uniform(-0.05, 0.05)
        dgs10 = 4.0 + base_stress * 0.4 + random.uniform(-0.05, 0.05)
        dgs30 = 4.2 + base_stress * 0.3 + random.uniform(-0.05, 0.05)

        macro = LiquidityMacro(
            date=date_str, hy_oas=round(hy_oas, 2), ig_oas=round(ig_oas, 2),
            sofr=round(sofr, 2), rrp_balance=round(rrp_balance, 1),
            dgs2=round(dgs2, 2), dgs10=round(dgs10, 2), dgs30=round(dgs30, 2),
        )
        session.add(macro)

        # ── 2. Price Data (ETF/Index) ──
        symbols_base = {
            "^VIX": (15, 10 * base_stress),
            "HYG": (78, -5 * base_stress),
            "LQD": (105, -3 * base_stress),
            "TLT": (92, -8 * base_stress),
            "IEF": (95, -3 * base_stress),
            "SHV": (110, -0.5 * base_stress),
            "KRE": (48, -8 * base_stress),
            "VNQ": (82, -6 * base_stress),
        }
        vix_close = None
        for sym, (base_price, stress_delta) in symbols_base.items():
            close = base_price + stress_delta + random.uniform(-1, 1)
            high = close + random.uniform(0, 1.5)
            low = close - random.uniform(0, 1.5)
            vol = random.randint(1000000, 50000000)
            if sym == "^VIX":
                vix_close = close
            price = LiquidityPrice(
                date=date_str, symbol=sym,
                close=round(close, 2), high=round(high, 2),
                low=round(low, 2), volume=vol,
            )
            session.add(price)

        # ── 3. News Keywords ──
        keywords = [
            ("liquidity crisis", int(5 + base_stress * 40)),
            ("margin call", int(3 + base_stress * 30)),
            ("credit default", int(2 + base_stress * 25)),
            ("repo market", int(4 + base_stress * 20)),
            ("private credit", int(3 + base_stress * 15)),
            ("CRE default", int(1 + base_stress * 10)),
        ]
        total_news = 0
        for kw, cnt in keywords:
            cnt = max(0, cnt + random.randint(-2, 3))
            total_news += cnt
            news = LiquidityNews(
                date=date_str, keyword=kw, count=cnt,
                sample_titles=f"[DEMO] Sample {kw} headline for {date_str}",
            )
            session.add(news)

        # ── 4. Fed Tone ──
        fed = FedTone(
            date=date_str,
            liquidity_score=round(0.05 + base_stress * 0.3 + random.uniform(-0.02, 0.02), 3),
            credit_score=round(0.04 + base_stress * 0.2 + random.uniform(-0.02, 0.02), 3),
            stability_score=round(0.03 + base_stress * 0.15 + random.uniform(-0.01, 0.01), 3),
        )
        session.add(fed)

        # ── 5. Stress Index Calculation ──
        vol_score = normalize(vix_close or 15, 12, 35)
        credit_score = normalize(hy_oas, 2.5, 6.0)
        funding_score = normalize(sofr - 4.0, 0, 0.5)  # SOFR - 정책금리 근사
        treasury_score = normalize(abs((92 + (-8 * base_stress)) - 92), 0, 8)
        news_score = normalize(total_news, 0, 80)
        fed_tone_score = clamp(fed.liquidity_score + fed.credit_score + fed.stability_score)

        total = (
            0.25 * vol_score +
            0.25 * credit_score +
            0.20 * funding_score +
            0.15 * treasury_score +
            0.10 * news_score +
            0.05 * fed_tone_score
        )

        si = StressIndex(
            date=date_str,
            vol_score=round(vol_score, 3),
            credit_score=round(credit_score, 3),
            funding_score=round(funding_score, 3),
            treasury_score=round(treasury_score, 3),
            news_score=round(news_score, 3),
            fed_tone_score=round(fed_tone_score, 3),
            total_score=round(total, 3),
            level=score_to_level(total),
        )
        session.add(si)

    session.commit()
    session.close()
    print(f"[SEED] {days}일간 유동성 스트레스 데모 데이터 생성 완료!")


if __name__ == "__main__":
    generate_seed_data(30)
