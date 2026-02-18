"""
Sector ETF Momentum Snapshot
Yahoo Finance v8 chart API를 사용하여 주요 섹터 ETF 모멘텀을 수집합니다.
Usage: python scripts/idea_pipeline/sector_momentum.py
"""
import sys
import json
import os
import time
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError

sys.stdout.reconfigure(encoding="utf-8")

SECTOR_ETFS = {
    "XLK": "Technology",
    "XLF": "Financals",
    "XLE": "Energy",
    "XLV": "Healthcare",
    "SOXX": "Semiconductors",
    "XLI": "Industrials",
    "XLY": "Consumer Discretionary",
    "XLP": "Consumer Staples",
    "XLRE": "Real Estate",
    "SPY": "S&P 500",
    "QQQ": "Nasdaq 100",
    "EWY": "Korea (MSCI)",
}

CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "sector_momentum.json")


def fetch_yahoo_chart(symbol, days=30):
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
            rows = []
            for i, ts in enumerate(timestamps):
                c = closes[i] if i < len(closes) else None
                if c is not None:
                    rows.append({"date": datetime.fromtimestamp(ts).strftime("%Y-%m-%d"), "close": round(c, 4)})
            return rows
    except (URLError, json.JSONDecodeError, KeyError) as e:
        print(f"[ERROR] Yahoo {symbol}: {e}")
        return []


def calc_momentum(prices):
    """5일/20일 수익률 계산"""
    if not prices:
        return {"latest": None, "ret_5d": None, "ret_20d": None, "trend": "unknown"}
    latest = prices[-1]["close"]
    ret_5d = None
    ret_20d = None
    if len(prices) >= 6:
        p5 = prices[-6]["close"]
        ret_5d = round(((latest - p5) / p5) * 100, 2) if p5 else None
    if len(prices) >= 21:
        p20 = prices[-21]["close"]
        ret_20d = round(((latest - p20) / p20) * 100, 2) if p20 else None
    trend = "unknown"
    if ret_5d is not None and ret_20d is not None:
        if ret_5d > 1 and ret_20d > 2:
            trend = "strong_up"
        elif ret_5d > 0 and ret_20d > 0:
            trend = "up"
        elif ret_5d < -1 and ret_20d < -2:
            trend = "strong_down"
        elif ret_5d < 0 and ret_20d < 0:
            trend = "down"
        else:
            trend = "mixed"
    return {"latest": latest, "ret_5d": ret_5d, "ret_20d": ret_20d, "trend": trend}


def run():
    """모든 섹터 ETF 모멘텀을 수집하고 캐시 파일에 저장합니다."""
    print("[MOMENTUM] 섹터 ETF 모멘텀 수집 시작...")
    results = {}
    for symbol, name in SECTOR_ETFS.items():
        print(f"  Fetching {symbol} ({name})...")
        prices = fetch_yahoo_chart(symbol, days=30)
        momentum = calc_momentum(prices)
        results[symbol] = {
            "name": name,
            "latest": momentum["latest"],
            "ret_5d": momentum["ret_5d"],
            "ret_20d": momentum["ret_20d"],
            "trend": momentum["trend"],
        }
        time.sleep(0.5)

    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "sectors": results,
    }
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[MOMENTUM] {len(results)}개 섹터 저장 → {CACHE_PATH}")
    return output


def load_cached():
    """캐시된 모멘텀 데이터 로드. 없으면 빈 dict."""
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"generated_at": None, "sectors": {}}


if __name__ == "__main__":
    run()
