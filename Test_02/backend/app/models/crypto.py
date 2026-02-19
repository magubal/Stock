"""Crypto Monitor DB Models — CryptoPrice, CryptoMetric, CollectorLog"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from ..database import Base


class CryptoPrice(Base):
    """일별 코인 가격 (CoinGecko top N)"""
    __tablename__ = "crypto_price"

    date = Column(String(10), primary_key=True)       # YYYY-MM-DD
    coin_id = Column(String(50), primary_key=True)     # coingecko id: bitcoin, ethereum, ...
    symbol = Column(String(20), nullable=False)         # BTC, ETH, ...
    price_usd = Column(Float)
    market_cap = Column(Float)
    volume_24h = Column(Float)
    change_24h = Column(Float)                          # 24h 변동률 (%)
    change_7d = Column(Float)                           # 7d 변동률 (%)


class CryptoMetric(Base):
    """일별 크립토 시장 지표"""
    __tablename__ = "crypto_metric"

    date = Column(String(10), primary_key=True)         # YYYY-MM-DD
    total_market_cap = Column(Float)
    total_volume_24h = Column(Float)
    btc_dominance = Column(Float)                       # %
    eth_btc_ratio = Column(Float)
    fear_greed_index = Column(Integer)                  # 0-100
    fear_greed_label = Column(String(30))               # Extreme Fear/Fear/Neutral/Greed/Extreme Greed
    defi_tvl = Column(Float)                            # DeFi 총 TVL (USD)
    stablecoin_mcap = Column(Float)                     # 스테이블코인 총 시가총액
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CollectorLog(Base):
    """데이터 수집 실행 이력"""
    __tablename__ = "collector_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False)           # YYYY-MM-DD
    collector = Column(String(30), nullable=False)      # liquidity, crypto, news
    status = Column(String(20), nullable=False)         # success, partial, failed
    duration = Column(Float)                            # 실행 시간 (초)
    details = Column(JSON)                              # 각 단계별 결과
    triggered_by = Column(String(30))                   # api, scheduler, manual-cli
    created_at = Column(DateTime(timezone=True), server_default=func.now())
