"""
News Intelligence Monitor - Finviz HTML Parser
5개 카테고리(market, market_pulse, stock, etf, crypto) 뉴스 수집
"""
import sys
import os
import random
import time
import re
from datetime import datetime, timezone, timedelta

import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from scripts.news_monitor.config import (
    DB_PATH, FINVIZ_URL, FINVIZ_SECTORS_URL, FINVIZ_CATEGORIES,
    REQUEST_DELAY, REQUEST_TIMEOUT, USER_AGENTS,
)

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Finviz 카테고리 → URL 매핑 (v= parameter)
CATEGORY_PARAM = {
    "market": "1",
    "market_pulse": "2",
    "stock": "3",
    "etf": "4",
    "crypto": "5",
}


def _get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }


def _parse_finviz_time(time_str: str) -> datetime:
    """Finviz 시간 문자열을 datetime으로 변환.
    형식: 'Feb-19-26 10:30AM' 또는 '10:30AM' (당일)
    """
    time_str = time_str.strip()
    now = datetime.now(timezone.utc)

    # 'Mon-DD-YY HH:MMAM/PM' 형식
    match = re.match(r'([A-Z][a-z]{2})-(\d{2})-(\d{2})\s+(\d{1,2}:\d{2}(?:AM|PM))', time_str)
    if match:
        month_str, day, year, t = match.groups()
        try:
            dt = datetime.strptime(f"{month_str}-{day}-20{year} {t}", "%b-%d-%Y %I:%M%p")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    # 'HH:MMAM/PM' 형식 (당일)
    match = re.match(r'(\d{1,2}:\d{2}(?:AM|PM))', time_str)
    if match:
        try:
            t = datetime.strptime(match.group(1), "%I:%M%p")
            return now.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
        except ValueError:
            pass

    # 'Today HH:MMAM/PM'
    match = re.match(r'Today\s+(\d{1,2}:\d{2}(?:AM|PM))', time_str)
    if match:
        try:
            t = datetime.strptime(match.group(1), "%I:%M%p")
            return now.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
        except ValueError:
            pass

    return now


def fetch_finviz_news(category: str) -> list[dict]:
    """Finviz HTML에서 특정 카테고리 뉴스 파싱."""
    param = CATEGORY_PARAM.get(category)
    if not param:
        print(f"  [WARN] Unknown category: {category}")
        return []

    url = f"{FINVIZ_URL}?v={param}"
    try:
        resp = requests.get(url, headers=_get_headers(), timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [WARN] Finviz fetch failed ({category}): {e}")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    articles = []

    # Finviz 뉴스 테이블 파싱
    news_table = soup.find('table', class_='styled-table-new')
    if not news_table:
        # fallback: id="news" 테이블
        news_table = soup.find('table', id='news')
    if not news_table:
        # fallback: 모든 뉴스 링크 수집
        for link in soup.select('a.nn-tab-link, a[class*="news"]'):
            href = link.get('href', '')
            title = link.get_text(strip=True)
            if href and title and href.startswith('http'):
                articles.append({
                    'title': title[:500],
                    'url': href[:500],
                    'publisher': '',
                    'published_at': datetime.now(timezone.utc),
                    'category': category,
                })
        if not articles:
            # 최종 fallback: 외부 링크 수집
            for row in soup.select('tr'):
                link = row.find('a', href=True)
                if not link:
                    continue
                href = link.get('href', '')
                if not href.startswith('http') or 'finviz.com' in href:
                    continue
                title = link.get_text(strip=True)
                if not title or len(title) < 10:
                    continue
                # 시간 추출
                td_time = row.find('td', class_='news_date-cell') or row.find('td', class_='nn-date') or row.find('td')
                time_text = td_time.get_text(strip=True) if td_time else ''
                published = _parse_finviz_time(time_text) if time_text else datetime.now(timezone.utc)
                # 매체명 추출
                small = row.find('small') or row.find('span', class_='nn-label')
                publisher = small.get_text(strip=True) if small else ''
                articles.append({
                    'title': title[:500],
                    'url': href[:500],
                    'publisher': publisher[:100],
                    'published_at': published,
                    'category': category,
                })
        return articles

    for row in news_table.find_all('tr'):
        link = row.find('a', href=True)
        if not link:
            continue
        href = link.get('href', '')
        title = link.get_text(strip=True)
        if not href.startswith('http') or not title:
            continue

        # 시간 (Finviz: td.news_date-cell)
        td_time = (
            row.find('td', class_='news_date-cell')
            or row.find('td', class_='nn-date')
        )
        time_text = td_time.get_text(strip=True) if td_time else ''
        published = _parse_finviz_time(time_text) if time_text else datetime.now(timezone.utc)

        # 매체 (Finviz: span inside news_link-cell)
        td_link = row.find('td', class_='news_link-cell')
        small = None
        if td_link:
            small = td_link.find('span') or td_link.find('small')
        if not small:
            small = row.find('small') or row.find('span', class_='nn-label')
        publisher = small.get_text(strip=True) if small else ''

        articles.append({
            'title': title[:500],
            'url': href[:500],
            'publisher': publisher[:100],
            'published_at': published,
            'category': category,
        })

    return articles


def save_articles(articles: list[dict], source: str = "finviz") -> tuple[int, int]:
    """DB에 저장 (중복 무시)."""
    from backend.app.models.news_article import NewsArticle

    engine = create_engine(f"sqlite:///{DB_PATH}")
    Session = sessionmaker(bind=engine)
    db = Session()

    saved, skipped = 0, 0
    for art in articles:
        exists = db.query(NewsArticle).filter_by(source=source, url=art['url']).first()
        if exists:
            skipped += 1
            continue
        row = NewsArticle(
            source=source,
            category=art['category'],
            title=art['title'],
            url=art['url'],
            publisher=art.get('publisher', ''),
            published_at=art['published_at'],
        )
        db.add(row)
        saved += 1

    db.commit()
    db.close()
    return saved, skipped


def fetch_all_categories() -> dict:
    """5개 카테고리 순차 수집 (딜레이 포함)."""
    results = {}
    for i, cat in enumerate(FINVIZ_CATEGORIES):
        print(f"  [{cat}] Fetching...")
        articles = fetch_finviz_news(cat)
        if articles:
            saved, skipped = save_articles(articles)
            results[cat] = {"fetched": len(articles), "saved": saved, "skipped": skipped}
            print(f"  [{cat}] {len(articles)} fetched, {saved} saved, {skipped} skipped")
        else:
            results[cat] = {"fetched": 0, "saved": 0, "skipped": 0}
            print(f"  [{cat}] No articles found")
        if i < len(FINVIZ_CATEGORIES) - 1:
            time.sleep(REQUEST_DELAY)
    return results


def fetch_sector_performance() -> list[dict]:
    """
    Finviz Groups 페이지에서 실제 섹터 1일 퍼포먼스를 스크래핑.
    Returns: [{name, change_pct, market_cap, stocks, pe, fwd_pe, dividend}]
    """
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        resp = requests.get(FINVIZ_SECTORS_URL, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [WARN] Sector fetch failed: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    sectors = []

    # Overview table: header uses <th>, data uses <td>
    # Columns: No. | Name | Stocks | MarketCap | ... | Change | Volume
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 5:
            continue
        header_cells = rows[0].find_all("th")
        if not header_cells:
            continue
        header_text = rows[0].get_text(strip=True)
        if "Name" not in header_text or "Change" not in header_text:
            continue

        # Find Change column index from <th> header
        change_idx = None
        for idx, cell in enumerate(header_cells):
            if cell.get_text(strip=True) == "Change":
                change_idx = idx
                break
        if change_idx is None:
            continue

        for row in rows[1:]:
            cells = row.find_all("td")
            if len(cells) <= change_idx:
                continue
            name = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            change_text = cells[change_idx].get_text(strip=True)
            if not name or not change_text:
                continue
            try:
                change_pct = float(change_text.replace("%", ""))
            except ValueError:
                change_pct = 0.0

            sectors.append({
                "name": name,
                "change_pct": change_pct,
            })
        break  # first matching table only

    print(f"  [SECTOR] {len(sectors)} sectors fetched")
    return sectors


def _parse_groups_table(url: str, label: str) -> list[dict]:
    """Finviz Groups 테이블 공통 파서 (sector/industry 공용)."""
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [WARN] {label} fetch failed: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 5:
            continue
        header_cells = rows[0].find_all("th")
        if not header_cells:
            continue
        header_text = rows[0].get_text(strip=True)
        if "Name" not in header_text or "Change" not in header_text:
            continue

        # Build column index map from <th> headers
        col_map = {}
        for idx, cell in enumerate(header_cells):
            col_map[cell.get_text(strip=True)] = idx

        change_idx = col_map.get("Change")
        mktcap_idx = col_map.get("Market Cap")
        pe_idx = col_map.get("P/E")
        vol_idx = col_map.get("Volume")
        if change_idx is None:
            continue

        for row in rows[1:]:
            cells = row.find_all("td")
            if len(cells) <= change_idx:
                continue
            name = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            change_text = cells[change_idx].get_text(strip=True)
            if not name or not change_text:
                continue
            try:
                change_pct = float(change_text.replace("%", "").replace(",", ""))
            except ValueError:
                change_pct = 0.0

            item = {"name": name, "change_pct": change_pct}
            if mktcap_idx and len(cells) > mktcap_idx:
                item["market_cap"] = cells[mktcap_idx].get_text(strip=True)
            if pe_idx and len(cells) > pe_idx:
                pe_text = cells[pe_idx].get_text(strip=True)
                try:
                    item["pe_ratio"] = float(pe_text.replace(",", ""))
                except (ValueError, AttributeError):
                    pass
            if vol_idx and len(cells) > vol_idx:
                item["volume"] = cells[vol_idx].get_text(strip=True)
            results.append(item)
        break

    print(f"  [{label}] {len(results)} items fetched")
    return results


FINVIZ_INDUSTRY_URL = "https://finviz.com/groups.ashx?g=industry&v=110&o=name"


def fetch_industry_performance() -> list[dict]:
    """Finviz Groups 페이지에서 인더스트리 1일 퍼포먼스를 스크래핑."""
    return _parse_groups_table(FINVIZ_INDUSTRY_URL, "INDUSTRY")


def _load_sector_industry_map() -> dict:
    """data/finviz_sector_industry_map.json에서 매핑 로드 → {industry: sector}"""
    import json
    map_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'finviz_sector_industry_map.json')
    if not os.path.exists(map_path):
        print(f"  [WARN] Sector-industry map not found: {map_path}")
        return {}
    with open(map_path, 'r', encoding='utf-8') as f:
        sector_map = json.load(f)
    # Invert: {industry_name: sector_name}
    inv = {}
    for sector, industries in sector_map.items():
        for ind in industries:
            inv[ind] = sector
    return inv


def save_sector_industry_performance(target_date: str = None) -> dict:
    """섹터 + 인더스트리 퍼포먼스를 DB에 저장."""
    from backend.app.models.news_article import SectorPerformance, IndustryPerformance

    if not target_date:
        target_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    engine = create_engine(f"sqlite:///{DB_PATH}")
    Session = sessionmaker(bind=engine)
    # Ensure tables exist
    from backend.app.models.news_article import Base as NewsBase
    NewsBase.metadata.create_all(engine)

    db = Session()
    result = {"sectors": 0, "industries": 0}

    # 1. Sectors
    sectors = fetch_sector_performance()
    for s in sectors:
        existing = db.query(SectorPerformance).filter_by(date=target_date, sector=s["name"]).first()
        if existing:
            existing.change_pct = s["change_pct"]
            existing.market_cap = s.get("market_cap")
            existing.pe_ratio = s.get("pe_ratio")
            existing.volume = s.get("volume")
        else:
            db.add(SectorPerformance(
                date=target_date, sector=s["name"], change_pct=s["change_pct"],
                market_cap=s.get("market_cap"), pe_ratio=s.get("pe_ratio"),
                volume=s.get("volume"),
            ))
        result["sectors"] += 1

    time.sleep(REQUEST_DELAY)

    # 2. Industries
    industries = fetch_industry_performance()
    inv_map = _load_sector_industry_map()
    for ind in industries:
        sector = inv_map.get(ind["name"], "Unknown")
        existing = db.query(IndustryPerformance).filter_by(date=target_date, industry=ind["name"]).first()
        if existing:
            existing.change_pct = ind["change_pct"]
            existing.sector = sector
            existing.market_cap = ind.get("market_cap")
            existing.pe_ratio = ind.get("pe_ratio")
            existing.volume = ind.get("volume")
        else:
            db.add(IndustryPerformance(
                date=target_date, industry=ind["name"], sector=sector,
                change_pct=ind["change_pct"], market_cap=ind.get("market_cap"),
                pe_ratio=ind.get("pe_ratio"), volume=ind.get("volume"),
            ))
        result["industries"] += 1

    db.commit()
    db.close()
    print(f"  [SAVE] {result['sectors']} sectors, {result['industries']} industries saved for {target_date}")
    return result


if __name__ == "__main__":
    print("[NEWS] Finviz fetch starting...")
    results = fetch_all_categories()
    total = sum(r["saved"] for r in results.values())
    print(f"[NEWS] Done. Total saved: {total}")
