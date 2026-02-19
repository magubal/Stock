"""
News Intelligence Monitor - Seed Data (DEMO)
DEMO 규칙 준수: source="DEMO", generated_by="DEMO"
"""
import sys
import os
import json
from datetime import datetime, timezone, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.stdout.reconfigure(encoding='utf-8')

from scripts.news_monitor.config import DB_PATH


def seed():
    from backend.app.models.news_article import NewsArticle, MarketNarrative
    from backend.app.database import Base

    engine = create_engine(f"sqlite:///{DB_PATH}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    today = datetime.now(timezone.utc)
    dates = [
        (today - timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(3)
    ]

    # ── DEMO Articles ──
    demo_articles = [
        # Market
        ("market", "Fed Signals Patience on Rate Cuts Amid Sticky Inflation", "Bloomberg", "https://demo.example.com/fed-patience"),
        ("market", "S&P 500 Extends Rally to Record High on Tech Earnings", "Reuters", "https://demo.example.com/sp500-rally"),
        ("market", "Treasury Yields Climb as Economic Data Beats Expectations", "CNBC", "https://demo.example.com/treasury-yields"),
        ("market", "Dollar Strengthens Against Major Currencies After Jobs Report", "WSJ", "https://demo.example.com/dollar-strength"),
        ("market", "Oil Prices Fall on China Demand Concerns", "Bloomberg", "https://demo.example.com/oil-prices"),
        # Market Pulse
        ("market_pulse", "VIX Drops Below 15 as Markets Calm After Earnings Season", "MarketWatch", "https://demo.example.com/vix-drops"),
        ("market_pulse", "Corporate Bond Spreads Tighten to Pre-Pandemic Levels", "FT", "https://demo.example.com/bond-spreads"),
        ("market_pulse", "IPO Market Shows Signs of Revival with Major Listings", "Reuters", "https://demo.example.com/ipo-revival"),
        ("market_pulse", "Retail Investor Sentiment Reaches 6-Month High", "CNBC", "https://demo.example.com/retail-sentiment"),
        # Stock
        ("stock", "NVIDIA Revenue Surges 265% on AI Chip Demand", "Bloomberg", "https://demo.example.com/nvidia-earnings"),
        ("stock", "Apple Announces $110B Buyback, Largest in History", "CNBC", "https://demo.example.com/apple-buyback"),
        ("stock", "Tesla Cuts Prices Amid EV Price War Intensification", "Reuters", "https://demo.example.com/tesla-prices"),
        ("stock", "Microsoft Cloud Revenue Grows 24% Beating Estimates", "WSJ", "https://demo.example.com/msft-cloud"),
        ("stock", "Amazon AWS Reports Record $25B Quarterly Revenue", "Bloomberg", "https://demo.example.com/aws-revenue"),
        # ETF
        ("etf", "Bitcoin ETF Inflows Surpass $50B Since Launch", "CoinDesk", "https://demo.example.com/btc-etf-inflows"),
        ("etf", "Emerging Market ETFs See Largest Outflows in 3 Months", "FT", "https://demo.example.com/em-outflows"),
        ("etf", "Gold ETF Holdings Rise on Geopolitical Uncertainty", "Reuters", "https://demo.example.com/gold-etf"),
        ("etf", "AI-Themed ETFs Attract Record $8B in Monthly Inflows", "Bloomberg", "https://demo.example.com/ai-etf"),
        # Crypto
        ("crypto", "Bitcoin Breaks $100K Barrier on Institutional Buying", "CoinDesk", "https://demo.example.com/btc-100k"),
        ("crypto", "Ethereum ETF Approval Speculation Drives 15% Rally", "The Block", "https://demo.example.com/eth-etf"),
        ("crypto", "Solana TVL Hits All-Time High as DeFi Activity Surges", "Decrypt", "https://demo.example.com/sol-tvl"),
        ("crypto", "SEC Commissioner Hints at More Crypto-Friendly Regulation", "Reuters", "https://demo.example.com/sec-crypto"),
    ]

    saved = 0
    for cat, title, publisher, url in demo_articles:
        for d_idx, d in enumerate(dates):
            unique_url = f"{url}-{d}"
            exists = db.query(NewsArticle).filter_by(source="DEMO", url=unique_url).first()
            if exists:
                continue
            hours = 9 + (hash(title) % 9)  # 09~17시
            mins = hash(url) % 60
            pub_dt = datetime.strptime(f"{d} {hours:02d}:{mins:02d}:00", "%Y-%m-%d %H:%M:%S")
            pub_dt = pub_dt.replace(tzinfo=timezone.utc)
            row = NewsArticle(
                source="DEMO",
                category=cat,
                title=f"[DEMO] {title}",
                url=unique_url,
                publisher=publisher,
                published_at=pub_dt,
            )
            db.add(row)
            saved += 1

    db.commit()
    print(f"[SEED] NewsArticles: {saved} rows inserted (DEMO)")

    # ── DEMO Narratives ──
    narratives_data = [
        {
            "key_issues": [
                {"title": "Fed 금리 동결 시사", "summary": "파월 의장이 인플레이션 둔화 속도에 만족하지 못하며 당분간 금리 동결을 시사했습니다. 시장은 6월 인하 기대를 후퇴시키고 있습니다.", "impact": "high", "category": "macro"},
                {"title": "AI 빅테크 실적 서프라이즈", "summary": "NVIDIA, Microsoft, Amazon 등 AI 관련 빅테크 기업들의 실적이 시장 기대를 크게 상회하며 기술주 랠리를 견인하고 있습니다.", "impact": "high", "category": "earnings"},
                {"title": "비트코인 $100K 돌파", "summary": "기관 투자자들의 지속적인 매수세와 ETF 유입 확대로 비트코인이 심리적 저항선인 10만 달러를 돌파했습니다.", "impact": "medium", "category": "crypto"},
            ],
            "narrative": "오늘 글로벌 시장은 Fed의 금리 정책 불확실성과 빅테크 실적 호조라는 상반된 시그널 사이에서 혼조세를 보이고 있습니다.\n\nFed의 금리 동결 시사에도 불구하고, AI 관련 기업들의 강력한 실적이 기술주 중심의 상승세를 유지시키고 있습니다. 특히 NVIDIA의 265% 매출 성장은 AI 투자 사이클이 여전히 초기 단계임을 시사합니다.\n\n크립토 시장에서는 비트코인의 10만 달러 돌파가 위험자산 선호 심리를 반영하며, 전반적으로 시장 참여자들은 거시적 리스크보다 성장 내러티브에 더 큰 비중을 두고 있는 것으로 판단됩니다.",
            "sector_impact": [
                {"sector": "Technology", "direction": "bullish", "confidence": 0.9, "reason": "AI 실적 서프라이즈로 강한 상승 모멘텀"},
                {"sector": "Financials", "direction": "neutral", "confidence": 0.5, "reason": "금리 동결 장기화 가능성으로 관망"},
                {"sector": "Energy", "direction": "bearish", "confidence": 0.6, "reason": "중국 수요 둔화 우려 지속"},
                {"sector": "Consumer", "direction": "neutral", "confidence": 0.4, "reason": "고금리 장기화에 따른 소비 둔화 리스크"},
                {"sector": "Crypto", "direction": "bullish", "confidence": 0.8, "reason": "기관 매수세 + ETF 유입 확대"},
                {"sector": "Real Estate", "direction": "bearish", "confidence": 0.7, "reason": "금리 인하 지연으로 부동산 시장 압박"},
            ],
            "sentiment_score": 0.25,
            "sentiment_label": "optimistic",
        },
    ]

    nar_saved = 0
    for d_idx, d in enumerate(dates):
        exists = db.query(MarketNarrative).filter_by(date=d).first()
        if exists:
            continue
        data = narratives_data[0]  # 동일 데이터 3일분
        # 날짜별 센티먼트 약간 변동
        score_offset = [-0.1, 0, 0.05][d_idx]
        row = MarketNarrative(
            date=d,
            key_issues=data["key_issues"],
            narrative=data["narrative"],
            sector_impact=data["sector_impact"],
            sentiment_score=round(data["sentiment_score"] + score_offset, 2),
            sentiment_label=data["sentiment_label"],
            article_count=len(demo_articles),
            generated_by="DEMO",
        )
        db.add(row)
        nar_saved += 1

    db.commit()
    db.close()
    print(f"[SEED] MarketNarratives: {nar_saved} rows inserted (DEMO)")
    print(f"[SEED] Complete.")


if __name__ == "__main__":
    seed()
