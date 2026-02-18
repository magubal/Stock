"""
Yahoo Finance Price Fetcher
무료 Yahoo Finance CSV를 통해 ETF/지수 종가를 수집합니다.
Usage: python scripts/liquidity_monitor/price_fetch.py
"""
import sys
import json
import time
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError

sys.stdout.reconfigure(encoding='utf-8')

from config import PRICE_SYMBOLS, DB_PATH

from sqlalchemy import create_engine, Column, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
Base = declarative_base()


class LiquidityPrice(Base):
    __tablename__ = "liquidity_price"
    date = Column(String(10), primary_key=True)
    symbol = Column(String(20), primary_key=True)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)
    volume = Column(Float)


Base.metadata.create_all(bind=engine)


def fetch_yahoo_chart(symbol, days=7):
    """Yahoo Finance v8 chart API에서 히스토리컬 데이터를 가져옵니다."""
    end_ts = int(datetime.now().timestamp())
    start_ts = int((datetime.now() - timedelta(days=days)).timestamp())
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        f"?period1={start_ts}&period2={end_ts}&interval=1d"
    )

    try:
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            result = data.get("chart", {}).get("result", [])
            if not result:
                return []

            timestamps = result[0].get("timestamp", [])
            quote = result[0].get("indicators", {}).get("quote", [{}])[0]
            closes = quote.get("close", [])
            highs = quote.get("high", [])
            lows = quote.get("low", [])
            volumes = quote.get("volume", [])

            rows = []
            for i, ts in enumerate(timestamps):
                dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                rows.append({
                    "date": dt,
                    "close": round(closes[i], 4) if i < len(closes) and closes[i] is not None else None,
                    "high": round(highs[i], 4) if i < len(highs) and highs[i] is not None else None,
                    "low": round(lows[i], 4) if i < len(lows) and lows[i] is not None else None,
                    "volume": float(volumes[i]) if i < len(volumes) and volumes[i] is not None else None,
                })
            return rows
    except (URLError, json.JSONDecodeError, KeyError) as e:
        print(f"[ERROR] Yahoo {symbol} fetch 실패: {e}")
        return []


def run():
    """모든 심볼의 가격 데이터를 수집하여 DB에 저장합니다."""
    print("[PRICE] ETF/지수 가격 수집 시작...")

    session = Session()
    total = 0

    for symbol in PRICE_SYMBOLS:
        print(f"  Fetching {symbol}...")
        rows = fetch_yahoo_chart(symbol, days=7)

        for row in rows:
            date_str = row["date"]
            existing = session.query(LiquidityPrice).filter_by(
                date=date_str, symbol=symbol
            ).first()

            if existing:
                existing.close = row["close"]
                existing.high = row["high"]
                existing.low = row["low"]
                existing.volume = row["volume"]
            else:
                session.add(LiquidityPrice(
                    date=date_str, symbol=symbol,
                    close=row["close"], high=row["high"],
                    low=row["low"], volume=row["volume"],
                ))
            total += 1

        time.sleep(0.5)  # Rate limiting

    session.commit()
    session.close()
    print(f"[PRICE] {total}건 가격 데이터 저장 완료")


if __name__ == "__main__":
    run()
