"""DefiLlama data fetcher — DeFi TVL + Stablecoin market cap."""
import sys
import json
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import HTTPError

sys.stdout.reconfigure(encoding='utf-8')

from config import DEFILLAMA_PROTOCOLS_URL, DEFILLAMA_STABLECOINS_URL, REQUEST_TIMEOUT, DB_PATH


def _fetch_json(url, label=""):
    """URL에서 JSON 가져오기."""
    try:
        req = Request(url, headers={"Accept": "application/json", "User-Agent": "StockResearchONE/1.0"})
        resp = urlopen(req, timeout=REQUEST_TIMEOUT)
        return json.loads(resp.read())
    except HTTPError as e:
        print(f"  [WARN] HTTP {e.code} for {label}")
        raise


def run(target_date=None):
    """DefiLlama TVL + 스테이블코인 시가총액 수집 → DB 저장."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[2]))
    from backend.app.models.crypto import CryptoMetric

    today = target_date or datetime.now().strftime("%Y-%m-%d")
    engine = create_engine(f'sqlite:///{DB_PATH}')
    CryptoMetric.__table__.create(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    db = Session()

    result = {"defi_tvl": None, "stablecoin_mcap": None}

    # Ensure metric row exists
    metric = db.query(CryptoMetric).filter_by(date=today).first()
    if not metric:
        metric = CryptoMetric(date=today)
        db.add(metric)
        db.commit()

    # 1. DeFi TVL (sum of all protocols)
    try:
        protocols = _fetch_json(DEFILLAMA_PROTOCOLS_URL, "protocols")
        total_tvl = sum(p.get("tvl", 0) or 0 for p in protocols if isinstance(p, dict))
        metric.defi_tvl = total_tvl
        db.commit()
        result["defi_tvl"] = total_tvl
        print(f"  [OK] DeFi TVL: ${total_tvl/1e9:.1f}B ({len(protocols)} protocols)")
    except Exception as e:
        print(f"  [SKIP] DefiLlama protocols: {e}")

    # 2. Stablecoin total market cap
    try:
        stables = _fetch_json(DEFILLAMA_STABLECOINS_URL, "stablecoins")
        pegged_list = stables.get("peggedAssets", [])
        total_mcap = sum(
            (s.get("circulating", {}).get("peggedUSD", 0) or 0)
            for s in pegged_list
            if isinstance(s, dict)
        )
        metric.stablecoin_mcap = total_mcap
        db.commit()
        result["stablecoin_mcap"] = total_mcap
        print(f"  [OK] Stablecoin mcap: ${total_mcap/1e9:.1f}B ({len(pegged_list)} assets)")
    except Exception as e:
        print(f"  [SKIP] DefiLlama stablecoins: {e}")

    db.close()
    return result


if __name__ == "__main__":
    run()
