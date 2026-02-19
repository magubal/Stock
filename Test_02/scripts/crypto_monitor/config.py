"""Crypto Monitor - Configuration"""
import os

# CoinGecko API
COINGECKO_MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"
COINGECKO_GLOBAL_URL = "https://api.coingecko.com/api/v3/global"
COINGECKO_ETH_BTC_URL = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=btc"

# DefiLlama API
DEFILLAMA_PROTOCOLS_URL = "https://api.llama.fi/v2/protocols"
DEFILLAMA_STABLECOINS_URL = "https://stablecoins.llama.fi/stablecoins?includePrices=false"

# Fear & Greed Index
FEAR_GREED_URL = "https://api.alternative.me/fng/?limit=1"

# Settings
TOP_N_COINS = 20
REQUEST_DELAY = 2.0  # seconds between CoinGecko requests (rate limit)
REQUEST_TIMEOUT = 30  # seconds

# DB
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'stock_research.db')
