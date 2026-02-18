"""
Liquidity Stress Monitor - Configuration
FRED API key, symbols, DB path 등 설정
"""
import os

# .env 파일에서 FRED_API_KEY 로드 (환경변수 우선)
def _load_env_key():
    key = os.getenv("FRED_API_KEY", "")
    if key:
        return key
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith("FRED_API_KEY="):
                    return line.split("=", 1)[1].strip()
    return ""

FRED_API_KEY = _load_env_key()

# DB 경로
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'stock_research.db')

# FRED 시리즈 ID
FRED_SERIES = {
    "hy_oas": "BAMLH0A0HYM2",   # ICE BofA US High Yield OAS
    "ig_oas": "BAMLC0A0CM",      # ICE BofA US Corp Master OAS
    "sofr": "SOFR",              # Secured Overnight Financing Rate
    "rrp_balance": "RRPONTSYD",  # Overnight Reverse Repurchase Agreements
    "dgs2": "DGS2",              # 2-Year Treasury
    "dgs10": "DGS10",            # 10-Year Treasury
    "dgs30": "DGS30",            # 30-Year Treasury
}

# Yahoo Finance 심볼
PRICE_SYMBOLS = ["^VIX", "HYG", "LQD", "TLT", "IEF", "SHV", "KRE", "VNQ"]

# 뉴스 검색 키워드
NEWS_KEYWORDS = [
    "liquidity crisis",
    "margin call",
    "credit default",
    "repo market",
    "private credit",
    "CRE default",
]

# 스트레스 인덱스 가중치
WEIGHTS = {
    "vol": 0.25,
    "credit": 0.25,
    "funding": 0.20,
    "treasury": 0.15,
    "news": 0.10,
    "fed_tone": 0.05,
}

# 정규화 범위
NORMALIZE_RANGES = {
    "vix": (12, 35),
    "hy_oas": (2.5, 6.0),
    "sofr_spread": (0, 0.5),
    "tlt_vol": (0.5, 5.0),
    "news_count": (0, 80),
    "fed_tone": (0, 0.5),
}
