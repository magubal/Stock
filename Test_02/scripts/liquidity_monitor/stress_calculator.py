"""
Stress Index Calculator
수집된 데이터를 기반으로 종합 스트레스 인덱스를 계산합니다.
Usage: python scripts/liquidity_monitor/stress_calculator.py
"""
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

from config import DB_PATH, WEIGHTS, NORMALIZE_RANGES

from sqlalchemy import create_engine, Column, String, Float, Integer, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func
from sqlalchemy import desc

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
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


def calculate(target_date=None):
    """특정 날짜의 스트레스 인덱스를 계산합니다."""
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    session = Session()

    # 1. VIX
    vix_row = session.query(LiquidityPrice).filter_by(
        date=target_date, symbol="^VIX"
    ).first()
    vix = vix_row.close if vix_row else None
    vix_lo, vix_hi = NORMALIZE_RANGES["vix"]
    vol_score = normalize(vix, vix_lo, vix_hi)

    # 2. Credit (HY OAS) — exact date first, then fallback to latest with real data
    macro = session.query(LiquidityMacro).filter_by(date=target_date).first()
    if not macro or macro.hy_oas is None:
        better = session.query(LiquidityMacro).filter(
            LiquidityMacro.date <= target_date, LiquidityMacro.hy_oas.isnot(None)
        ).order_by(desc(LiquidityMacro.date)).first()
        if better:
            print(f"  [INFO] macro fallback: {target_date} → {better.date} (hy_oas={better.hy_oas})")
            macro = better
    hy_oas = macro.hy_oas if macro else None
    hy_lo, hy_hi = NORMALIZE_RANGES["hy_oas"]
    credit_score = normalize(hy_oas, hy_lo, hy_hi)

    # 3. Funding (SOFR spread)
    sofr = macro.sofr if macro else None
    spread = (sofr - 4.0) if sofr else 0
    sp_lo, sp_hi = NORMALIZE_RANGES["sofr_spread"]
    funding_score = normalize(spread, sp_lo, sp_hi)

    # 4. Treasury (TLT 5일 변동성 대리: 당일 high-low range)
    tlt_row = session.query(LiquidityPrice).filter_by(
        date=target_date, symbol="TLT"
    ).first()
    if tlt_row and tlt_row.high and tlt_row.low and tlt_row.close:
        tlt_range_pct = ((tlt_row.high - tlt_row.low) / tlt_row.close) * 100
    else:
        tlt_range_pct = 0
    tlt_lo, tlt_hi = NORMALIZE_RANGES["tlt_vol"]
    treasury_score = normalize(tlt_range_pct, tlt_lo, tlt_hi)

    # 5. News
    news_rows = session.query(LiquidityNews).filter_by(date=target_date).all()
    total_news = sum(n.count for n in news_rows)
    ns_lo, ns_hi = NORMALIZE_RANGES["news_count"]
    news_score = normalize(total_news, ns_lo, ns_hi)

    # 6. Fed Tone
    fed = session.query(FedTone).filter_by(date=target_date).first()
    if fed:
        fed_sum = (fed.liquidity_score or 0) + (fed.credit_score or 0) + (fed.stability_score or 0)
    else:
        fed_sum = 0
    ft_lo, ft_hi = NORMALIZE_RANGES["fed_tone"]
    fed_tone_score = normalize(fed_sum, ft_lo, ft_hi)

    # Weighted total
    total = (
        WEIGHTS["vol"] * vol_score +
        WEIGHTS["credit"] * credit_score +
        WEIGHTS["funding"] * funding_score +
        WEIGHTS["treasury"] * treasury_score +
        WEIGHTS["news"] * news_score +
        WEIGHTS["fed_tone"] * fed_tone_score
    )

    level = score_to_level(total)

    # Save
    existing = session.query(StressIndex).filter_by(date=target_date).first()
    if existing:
        existing.vol_score = round(vol_score, 3)
        existing.credit_score = round(credit_score, 3)
        existing.funding_score = round(funding_score, 3)
        existing.treasury_score = round(treasury_score, 3)
        existing.news_score = round(news_score, 3)
        existing.fed_tone_score = round(fed_tone_score, 3)
        existing.total_score = round(total, 3)
        existing.level = level
    else:
        session.add(StressIndex(
            date=target_date,
            vol_score=round(vol_score, 3),
            credit_score=round(credit_score, 3),
            funding_score=round(funding_score, 3),
            treasury_score=round(treasury_score, 3),
            news_score=round(news_score, 3),
            fed_tone_score=round(fed_tone_score, 3),
            total_score=round(total, 3),
            level=level,
        ))

    session.commit()
    session.close()

    print(f"[CALC] {target_date}: total={total:.3f} level={level}")
    print(f"  vol={vol_score:.3f} credit={credit_score:.3f} funding={funding_score:.3f}")
    print(f"  treasury={treasury_score:.3f} news={news_score:.3f} fed={fed_tone_score:.3f}")

    return total, level


if __name__ == "__main__":
    calculate()
