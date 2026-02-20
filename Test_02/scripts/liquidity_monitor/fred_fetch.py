"""
FRED API Data Fetcher
무료 FRED API를 통해 매크로 지표를 수집합니다.
Usage: python scripts/liquidity_monitor/fred_fetch.py
"""
import os
import sys
import json
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError

sys.stdout.reconfigure(encoding='utf-8')

from config import FRED_API_KEY, FRED_SERIES, DB_PATH

from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func

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


Base.metadata.create_all(bind=engine)


def fetch_fred_series(series_id, days=7):
    """FRED API에서 최근 데이터를 가져옵니다."""
    if not FRED_API_KEY:
        print(f"[WARN] FRED_API_KEY가 설정되지 않았습니다. 환경변수를 설정하세요.")
        return {}

    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    url = (
        f"https://api.stlouisfed.org/fred/series/observations"
        f"?series_id={series_id}&api_key={FRED_API_KEY}"
        f"&file_type=json&observation_start={start}&observation_end={end}"
    )

    try:
        req = Request(url, headers={"User-Agent": "StockResearchONE/1.0"})
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            observations = data.get("observations", [])
            result = {}
            for obs in observations:
                if obs["value"] != ".":
                    result[obs["date"]] = float(obs["value"])
            return result
    except (URLError, json.JSONDecodeError) as e:
        print(f"[ERROR] FRED {series_id} fetch 실패: {e}")
        return {}


def run():
    """모든 FRED 시리즈를 수집하여 DB에 저장합니다."""
    print("[FRED] 매크로 지표 수집 시작...")

    all_data = {}
    for field, series_id in FRED_SERIES.items():
        print(f"  Fetching {field} ({series_id})...")
        obs = fetch_fred_series(series_id, days=7)
        for date_str, value in obs.items():
            if date_str not in all_data:
                all_data[date_str] = {}
            all_data[date_str][field] = value

    if not all_data:
        print("[FRED] 수집된 데이터 없음")
        return

    # Forward-fill: FRED 시리즈별 발표일이 다르므로 빈 필드는 직전 값으로 채움
    all_fields = list(FRED_SERIES.keys())
    sorted_dates = sorted(all_data.keys())

    session = Session()

    # DB에서 각 필드의 가장 최근 값을 seed로 가져옴
    prev_values = {}
    latest_macro = session.query(LiquidityMacro).filter(
        LiquidityMacro.hy_oas.isnot(None)
    ).order_by(LiquidityMacro.date.desc()).first()
    if latest_macro:
        for field in all_fields:
            val = getattr(latest_macro, field, None)
            if val is not None:
                prev_values[field] = val

    # 날짜순으로 forward-fill
    for date_str in sorted_dates:
        for field in all_fields:
            if field in all_data[date_str]:
                prev_values[field] = all_data[date_str][field]
            elif field in prev_values:
                all_data[date_str][field] = prev_values[field]

    count = 0
    for date_str, fields in sorted(all_data.items()):
        existing = session.query(LiquidityMacro).filter_by(date=date_str).first()
        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
        else:
            session.add(LiquidityMacro(date=date_str, **fields))
        count += 1

    session.commit()
    session.close()
    print(f"[FRED] {count}일간 매크로 데이터 저장 완료 (forward-fill 적용)")


if __name__ == "__main__":
    run()
