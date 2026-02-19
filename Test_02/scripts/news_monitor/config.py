"""
News Intelligence Monitor - Configuration
Finviz URL, 카테고리, DB 경로, Claude API 설정
"""
import os

# DB 경로 (기존 패턴)
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'stock_research.db')

# Finviz 설정
FINVIZ_URL = "https://finviz.com/news.ashx"
FINVIZ_SECTORS_URL = "https://finviz.com/groups.ashx?g=sector&v=110&o=name"
FINVIZ_CATEGORIES = ["market", "market_pulse", "stock", "etf", "crypto"]

# 요청 설정
REQUEST_DELAY = 2.0
REQUEST_TIMEOUT = 15
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

# Claude API 설정
def _load_anthropic_key():
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if key:
        return key
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith("ANTHROPIC_API_KEY="):
                    return line.split("=", 1)[1].strip()
    return ""

ANTHROPIC_API_KEY = _load_anthropic_key()
ANTHROPIC_MODEL = "claude-sonnet-4-5-20250929"
MAX_ARTICLES_FOR_ANALYSIS = 80

# Available AI models for narrative analysis
AVAILABLE_MODELS = {
    "claude-sonnet-4-5-20250929": {"label": "Sonnet 4.5", "tier": "balanced", "cost": "medium"},
    "claude-haiku-4-5-20251001": {"label": "Haiku 4.5", "tier": "fast", "cost": "low"},
    "claude-opus-4-6": {"label": "Opus 4.6", "tier": "advanced", "cost": "high"},
}
