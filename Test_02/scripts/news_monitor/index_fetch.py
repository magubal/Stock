"""
News Intelligence Monitor - US Market Index Fetcher
DOW(^DJI), NASDAQ(^IXIC), S&P500(^GSPC) 장중 시세 데이터를 Yahoo Finance v8 API로 수집
"""
import sys
import os
import json
import time
import random
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.stdout.reconfigure(encoding='utf-8')

from scripts.news_monitor.config import USER_AGENTS

# US 주요 지수
INDEX_SYMBOLS = {
    "^DJI": {"name": "DOW", "full_name": "Dow Jones Industrial Average"},
    "^IXIC": {"name": "NASDAQ", "full_name": "NASDAQ Composite"},
    "^GSPC": {"name": "S&P500", "full_name": "S&P 500"},
    "^VIX": {"name": "VIX", "full_name": "CBOE Volatility Index"},
}


def fetch_index_data(symbol: str, range_str: str = "1d", interval: str = "5m", max_retries: int = 3) -> dict | None:
    """Yahoo Finance v8 API로 지수 데이터 수집 (retry with backoff).

    Args:
        symbol: Yahoo Finance ticker (e.g. ^DJI)
        range_str: 조회 기간 (1d, 5d, 1mo)
        interval: 봉 간격 (1m, 5m, 15m, 1h, 1d)
        max_retries: 최대 재시도 횟수

    Returns:
        dict with timestamps, opens, closes, highs, lows, volumes
    """
    # query1 / query2 교대 사용
    hosts = ["query1.finance.yahoo.com", "query2.finance.yahoo.com"]

    for attempt in range(max_retries):
        host = hosts[attempt % len(hosts)]
        url = (
            f"https://{host}/v8/finance/chart/{symbol}"
            f"?range={range_str}&interval={interval}&includePrePost=false"
        )
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/json",
        }

        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))

            result = data["chart"]["result"][0]
            meta = result["meta"]
            timestamps = result.get("timestamp", [])
            quotes = result["indicators"]["quote"][0]

            return {
                "symbol": symbol,
                "name": INDEX_SYMBOLS.get(symbol, {}).get("name", symbol),
                "full_name": INDEX_SYMBOLS.get(symbol, {}).get("full_name", symbol),
                "currency": meta.get("currency", "USD"),
                "exchange_timezone": meta.get("exchangeTimezoneName", ""),
                "regular_market_price": meta.get("regularMarketPrice"),
                "previous_close": meta.get("chartPreviousClose") or meta.get("previousClose"),
                "timestamps": timestamps,
                "opens": quotes.get("open", []),
                "closes": quotes.get("close", []),
                "highs": quotes.get("high", []),
                "lows": quotes.get("low", []),
                "volumes": quotes.get("volume", []),
            }
        except HTTPError as e:
            if e.code == 429 and attempt < max_retries - 1:
                wait = (attempt + 1) * 2 + random.uniform(0, 1)
                print(f"  [WARN] Rate limited for {symbol}, retry {attempt+1}/{max_retries} in {wait:.1f}s...")
                time.sleep(wait)
                continue
            print(f"  [WARN] Index fetch failed for {symbol}: HTTP {e.code}")
            return None
        except Exception as e:
            print(f"  [WARN] Index fetch error for {symbol}: {e}")
            return None

    return None


def fetch_all_indices(range_str: str = "1d", interval: str = "5m") -> list[dict]:
    """모든 주요 지수 데이터를 수집."""
    results = []
    for i, symbol in enumerate(INDEX_SYMBOLS):
        if i > 0:
            time.sleep(1.5 + random.uniform(0, 1))
        data = fetch_index_data(symbol, range_str=range_str, interval=interval)
        if data:
            results.append(data)
            print(f"  [INDEX] {data['name']}: {data['regular_market_price']}")
    return results


def summarize_index_data(indices: list[dict]) -> list[dict]:
    """지수 데이터를 요약 (프롬프트 + DB 저장용).

    Returns:
        list of dicts with name, current, prev_close, change, change_pct,
        day_high, day_low, intraday_moves (key timestamp → price snapshots)
    """
    summaries = []
    for idx in indices:
        if not idx or not idx.get("timestamps"):
            continue

        current = idx["regular_market_price"]
        prev_close = idx["previous_close"]
        closes = [c for c in idx["closes"] if c is not None]
        highs = [h for h in idx["highs"] if h is not None]
        lows = [l for l in idx["lows"] if l is not None]

        if not closes or not prev_close:
            continue

        change = current - prev_close
        change_pct = (change / prev_close) * 100 if prev_close else 0

        day_high = max(highs) if highs else current
        day_low = min(lows) if lows else current

        # Intraday key moments: open, mid-morning, lunch, mid-afternoon, current
        ts_list = idx["timestamps"]
        n = len(ts_list)
        key_points = []
        if n > 0:
            checkpoints = [0, n // 4, n // 2, 3 * n // 4, n - 1]
            seen = set()
            for ci in checkpoints:
                if ci < n and ci not in seen:
                    seen.add(ci)
                    t = ts_list[ci]
                    c = closes[ci] if ci < len(closes) else None
                    if c is not None:
                        dt = datetime.fromtimestamp(t, tz=timezone(timedelta(hours=-5)))
                        key_points.append({
                            "time": dt.strftime("%H:%M ET"),
                            "price": round(c, 2),
                            "change_from_open": round(c - (closes[0] if closes else c), 2),
                        })

        summaries.append({
            "name": idx["name"],
            "full_name": idx["full_name"],
            "current": round(current, 2),
            "previous_close": round(prev_close, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "day_high": round(day_high, 2),
            "day_low": round(day_low, 2),
            "intraday_points": key_points,
        })

    return summaries


def build_index_prompt_text(summaries: list[dict]) -> str:
    """지수 요약을 프롬프트용 텍스트로 변환."""
    if not summaries:
        return "(US index data unavailable)"

    lines = ["| Index | Current | Change | Day Range | Key Intraday Moves |",
             "|-------|---------|--------|-----------|-------------------|"]

    for s in summaries:
        sign = "+" if s["change"] >= 0 else ""
        range_str = f"{s['day_low']:,.2f} - {s['day_high']:,.2f}"

        # Key intraday moves as compact text
        moves = []
        for p in s.get("intraday_points", []):
            sign_p = "+" if p["change_from_open"] >= 0 else ""
            moves.append(f"{p['time']}={p['price']:,.2f}({sign_p}{p['change_from_open']:,.2f})")
        moves_text = " → ".join(moves) if moves else "N/A"

        lines.append(
            f"| {s['name']} | {s['current']:,.2f} | "
            f"{sign}{s['change']:,.2f} ({sign}{s['change_pct']:.2f}%) | "
            f"{range_str} | {moves_text} |"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    print("[INDEX] Fetching US market indices...")
    raw = fetch_all_indices()
    summaries = summarize_index_data(raw)
    print("\n" + build_index_prompt_text(summaries))
    print(f"\n[INDEX] Done. {len(summaries)} indices fetched.")
