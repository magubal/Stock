"""CoinGecko data fetcher — top coins + global metrics."""
import sys
import time
import json
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import HTTPError

sys.stdout.reconfigure(encoding='utf-8')

from config import (
    COINGECKO_MARKETS_URL, COINGECKO_GLOBAL_URL, COINGECKO_ETH_BTC_URL,
    TOP_N_COINS, REQUEST_DELAY, REQUEST_TIMEOUT, DB_PATH,
)


def _fetch_json(url, label=""):
    """URL에서 JSON 가져오기 (rate limit 대응 1회 재시도)."""
    for attempt in range(2):
        try:
            req = Request(url, headers={"Accept": "application/json", "User-Agent": "StockResearchONE/1.0"})
            resp = urlopen(req, timeout=REQUEST_TIMEOUT)
            return json.loads(resp.read())
        except HTTPError as e:
            if e.code == 429 and attempt == 0:
                print(f"  [WARN] Rate limited for {label}, retry in {REQUEST_DELAY * 2}s...")
                time.sleep(REQUEST_DELAY * 2)
                continue
            raise
    return None


def run(target_date=None):
    """CoinGecko top coins 가격 + global 데이터 수집 → DB 저장."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Lazy import to avoid circular deps when called from project root
    sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[2]))
    from backend.app.models.crypto import CryptoPrice, CryptoMetric

    today = target_date or datetime.now().strftime("%Y-%m-%d")
    engine = create_engine(f'sqlite:///{DB_PATH}')
    CryptoPrice.__table__.create(engine, checkfirst=True)
    CryptoMetric.__table__.create(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    db = Session()

    result = {"coins_saved": 0, "global_saved": False, "eth_btc": None}

    # 1. Top N coins
    try:
        url = f"{COINGECKO_MARKETS_URL}?vs_currency=usd&order=market_cap_desc&per_page={TOP_N_COINS}&page=1&sparkline=false&price_change_percentage=7d"
        coins = _fetch_json(url, "markets")
        for c in coins:
            existing = db.query(CryptoPrice).filter_by(date=today, coin_id=c["id"]).first()
            if existing:
                existing.symbol = (c.get("symbol") or "").upper()
                existing.price_usd = c.get("current_price")
                existing.market_cap = c.get("market_cap")
                existing.volume_24h = c.get("total_volume")
                existing.change_24h = c.get("price_change_percentage_24h")
                existing.change_7d = c.get("price_change_percentage_7d_in_currency")
            else:
                db.add(CryptoPrice(
                    date=today,
                    coin_id=c["id"],
                    symbol=(c.get("symbol") or "").upper(),
                    price_usd=c.get("current_price"),
                    market_cap=c.get("market_cap"),
                    volume_24h=c.get("total_volume"),
                    change_24h=c.get("price_change_percentage_24h"),
                    change_7d=c.get("price_change_percentage_7d_in_currency"),
                ))
        db.commit()
        result["coins_saved"] = len(coins)
        print(f"  [OK] Top {len(coins)} coins saved")
    except Exception as e:
        print(f"  [SKIP] CoinGecko markets: {e}")

    time.sleep(REQUEST_DELAY)

    # 2. Global data
    try:
        g = _fetch_json(COINGECKO_GLOBAL_URL, "global")
        gd = g.get("data", {})
        metric = db.query(CryptoMetric).filter_by(date=today).first()
        if not metric:
            metric = CryptoMetric(date=today)
            db.add(metric)
        metric.total_market_cap = gd.get("total_market_cap", {}).get("usd")
        metric.total_volume_24h = gd.get("total_volume", {}).get("usd")
        metric.btc_dominance = gd.get("market_cap_percentage", {}).get("btc")
        db.commit()
        result["global_saved"] = True
        print(f"  [OK] Global metrics saved (BTC dom: {metric.btc_dominance:.1f}%)")
    except Exception as e:
        print(f"  [SKIP] CoinGecko global: {e}")

    time.sleep(REQUEST_DELAY)

    # 3. ETH/BTC ratio
    try:
        eth = _fetch_json(COINGECKO_ETH_BTC_URL, "eth_btc")
        ratio = eth.get("ethereum", {}).get("btc")
        if ratio:
            metric = db.query(CryptoMetric).filter_by(date=today).first()
            if metric:
                metric.eth_btc_ratio = ratio
                db.commit()
                result["eth_btc"] = ratio
                print(f"  [OK] ETH/BTC ratio: {ratio}")
    except Exception as e:
        print(f"  [SKIP] ETH/BTC: {e}")

    db.close()
    return result


if __name__ == "__main__":
    run()
