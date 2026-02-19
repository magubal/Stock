"""
Finviz Industry → Stock Screener 배치 수집기
인더스트리별 개별 종목의 당일 변화율 + 1Y 퍼포먼스를 수집하여 DB 저장.
차단 방지를 위해 인더스트리 간 딜레이를 두고 점진적으로 수집.
"""
import sys, os, json, time, random, sqlite3
from datetime import datetime, timezone, timedelta

sys.stdout.reconfigure(encoding="utf-8")

import requests
from bs4 import BeautifulSoup

# ── Config ──
_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.abspath(os.path.join(_dir, "..", ".."))
DB_PATH = os.path.join(_root, "backend", "stock_research.db")
SLUG_PATH = os.path.join(_root, "data", "finviz_industry_slugs.json")
SECTOR_MAP_PATH = os.path.join(_root, "data", "finviz_sector_industry_map.json")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0",
]

DELAY_MIN = 4.0   # 인더스트리 간 최소 딜레이 (초)
DELAY_MAX = 8.0   # 인더스트리 간 최대 딜레이 (초)
REQUEST_TIMEOUT = 15


def _headers():
    return {"User-Agent": random.choice(USER_AGENTS)}


def _load_slugs() -> dict:
    """인더스트리 이름 → Finviz slug 매핑 로드."""
    if not os.path.exists(SLUG_PATH):
        print(f"  [WARN] Slug file not found: {SLUG_PATH}")
        return {}
    with open(SLUG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_sector_map() -> dict:
    """인더스트리 → 섹터 역매핑."""
    if not os.path.exists(SECTOR_MAP_PATH):
        return {}
    with open(SECTOR_MAP_PATH, "r", encoding="utf-8") as f:
        sector_map = json.load(f)
    inv = {}
    for sector, industries in sector_map.items():
        for ind in industries:
            inv[ind] = sector
    return inv


def _parse_pct(text: str) -> float | None:
    """'4.87%' -> 4.87, '-' -> None"""
    if not text or text == "-":
        return None
    try:
        return float(text.replace("%", "").replace(",", ""))
    except (ValueError, AttributeError):
        return None


def _parse_float(text: str) -> float | None:
    if not text or text == "-":
        return None
    try:
        return float(text.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def _parse_screener_table(soup: BeautifulSoup) -> list[dict]:
    """screener_table 클래스 테이블을 파싱하여 dict 리스트 반환."""
    table = soup.find("table", class_="screener_table")
    if not table:
        return []
    rows = table.find_all("tr")
    if len(rows) < 2:
        return []
    headers = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])]
    results = []
    for row in rows[1:]:
        cells = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cells) == len(headers):
            results.append(dict(zip(headers, cells)))
    return results


def fetch_industry_stocks(slug: str, industry: str) -> list[dict]:
    """
    Finviz screener에서 특정 인더스트리의 종목 데이터를 수집.
    Overview(v=111) + Performance(v=141) 2회 요청으로 통합 데이터 생성.
    """
    stocks = {}

    # 1) Overview: Company, Market Cap, P/E, Price, Change, Volume
    try:
        url = f"https://finviz.com/screener.ashx?f={slug}&v=111"
        resp = requests.get(url, headers=_headers(), timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for row in _parse_screener_table(soup):
            ticker = row.get("Ticker", "")
            if not ticker:
                continue
            stocks[ticker] = {
                "ticker": ticker,
                "company": row.get("Company", ""),
                "market_cap": row.get("Market Cap", ""),
                "pe_ratio": _parse_float(row.get("P/E", "")),
                "price": _parse_float(row.get("Price", "")),
                "change_pct": _parse_pct(row.get("Change", "")),
                "volume": row.get("Volume", ""),
            }
    except requests.RequestException as e:
        print(f"  [WARN] Overview fetch failed for {industry}: {e}")
        return []

    if not stocks:
        return []

    # 짧은 딜레이 (같은 인더스트리 2번째 요청)
    time.sleep(random.uniform(1.0, 2.0))

    # 2) Performance: Perf Week/Month/Quarter/Half/YTD/Year
    try:
        url = f"https://finviz.com/screener.ashx?f={slug}&v=141"
        resp = requests.get(url, headers=_headers(), timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for row in _parse_screener_table(soup):
            ticker = row.get("Ticker", "")
            if ticker in stocks:
                stocks[ticker]["perf_week"] = _parse_pct(row.get("Perf Week", ""))
                stocks[ticker]["perf_month"] = _parse_pct(row.get("Perf Month", ""))
                stocks[ticker]["perf_quarter"] = _parse_pct(row.get("Perf Quart", ""))
                stocks[ticker]["perf_half"] = _parse_pct(row.get("Perf Half", ""))
                stocks[ticker]["perf_ytd"] = _parse_pct(row.get("Perf YTD", ""))
                stocks[ticker]["perf_year"] = _parse_pct(row.get("Perf Year", ""))
    except requests.RequestException as e:
        print(f"  [WARN] Performance fetch failed for {industry}: {e}")
        # Overview 데이터만이라도 반환

    return list(stocks.values())


def save_industry_stocks(industry: str, sector: str, stocks: list[dict], target_date: str = None):
    """인더스트리 종목 데이터를 DB에 UPSERT 저장."""
    if not target_date:
        kst = datetime.now(timezone.utc) + timedelta(hours=9)
        target_date = kst.strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_PATH)
    now = datetime.now(timezone.utc).isoformat()
    saved = 0

    for s in stocks:
        existing = conn.execute(
            "SELECT id FROM industry_stocks WHERE date=? AND ticker=?",
            (target_date, s["ticker"]),
        ).fetchone()

        if existing:
            conn.execute(
                """UPDATE industry_stocks SET
                    industry=?, sector=?, company=?, price=?, change_pct=?,
                    perf_week=?, perf_month=?, perf_quarter=?, perf_half=?,
                    perf_ytd=?, perf_year=?, market_cap=?, pe_ratio=?,
                    volume=?, fetched_at=?
                WHERE date=? AND ticker=?""",
                (
                    industry, sector, s.get("company"), s.get("price"), s.get("change_pct"),
                    s.get("perf_week"), s.get("perf_month"), s.get("perf_quarter"),
                    s.get("perf_half"), s.get("perf_ytd"), s.get("perf_year"),
                    s.get("market_cap"), s.get("pe_ratio"), s.get("volume"), now,
                    target_date, s["ticker"],
                ),
            )
        else:
            conn.execute(
                """INSERT INTO industry_stocks
                (date, industry, sector, ticker, company, price, change_pct,
                 perf_week, perf_month, perf_quarter, perf_half, perf_ytd, perf_year,
                 market_cap, pe_ratio, volume, source, fetched_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    target_date, industry, sector, s["ticker"], s.get("company"),
                    s.get("price"), s.get("change_pct"),
                    s.get("perf_week"), s.get("perf_month"), s.get("perf_quarter"),
                    s.get("perf_half"), s.get("perf_ytd"), s.get("perf_year"),
                    s.get("market_cap"), s.get("pe_ratio"), s.get("volume"),
                    "finviz", now,
                ),
            )
        saved += 1

    conn.commit()
    conn.close()
    return saved


def ensure_table():
    """industry_stocks 테이블이 없으면 생성."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS industry_stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            industry TEXT NOT NULL,
            sector TEXT NOT NULL,
            ticker TEXT NOT NULL,
            company TEXT,
            price REAL,
            change_pct REAL,
            perf_week REAL,
            perf_month REAL,
            perf_quarter REAL,
            perf_half REAL,
            perf_ytd REAL,
            perf_year REAL,
            market_cap TEXT,
            pe_ratio REAL,
            volume TEXT,
            source TEXT DEFAULT 'finviz',
            fetched_at TEXT
        )
    """)
    # Unique constraint + indexes
    try:
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_stock_date_ticker ON industry_stocks(date, ticker)")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stocks_industry ON industry_stocks(date, industry)")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stocks_sector ON industry_stocks(date, sector)")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


def run_batch(target_date: str = None, max_industries: int = 0):
    """
    전체 인더스트리 배치 수집.
    각 인더스트리 수집 후 DB 저장 → 딜레이 → 다음 인더스트리.
    max_industries=0 이면 전체 수집.
    """
    ensure_table()
    slugs = _load_slugs()
    sector_map = _load_sector_map()

    if not slugs:
        print("[ERROR] No industry slugs loaded")
        return

    if not target_date:
        kst = datetime.now(timezone.utc) + timedelta(hours=9)
        target_date = kst.strftime("%Y-%m-%d")

    industries = list(slugs.items())
    if max_industries > 0:
        industries = industries[:max_industries]

    total_stocks = 0
    total_industries = 0
    start_time = time.time()

    print(f"[BATCH] Starting stock collection for {len(industries)} industries (date={target_date})")
    print(f"[BATCH] Delay: {DELAY_MIN}~{DELAY_MAX}s between industries")

    for i, (industry, slug) in enumerate(industries, 1):
        sector = sector_map.get(industry, "Unknown")
        print(f"  [{i:3d}/{len(industries)}] {industry}...", end=" ", flush=True)

        stocks = fetch_industry_stocks(slug, industry)
        if stocks:
            saved = save_industry_stocks(industry, sector, stocks, target_date)
            total_stocks += saved
            total_industries += 1
            print(f"{saved} stocks saved")
        else:
            print("0 stocks (skipped)")

        # 딜레이 (마지막 인더스트리는 제외)
        if i < len(industries):
            delay = random.uniform(DELAY_MIN, DELAY_MAX)
            time.sleep(delay)

    elapsed = time.time() - start_time
    print(f"\n[BATCH] Done: {total_industries} industries, {total_stocks} stocks in {elapsed:.0f}s")
    return {"industries": total_industries, "stocks": total_stocks, "elapsed": elapsed}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Finviz Industry Stock Batch Collector")
    parser.add_argument("--date", help="Target date (YYYY-MM-DD)")
    parser.add_argument("--max", type=int, default=0, help="Max industries to fetch (0=all)")
    parser.add_argument("--test", action="store_true", help="Test mode: fetch 3 industries only")
    args = parser.parse_args()

    if args.test:
        args.max = 3

    run_batch(target_date=args.date, max_industries=args.max)
