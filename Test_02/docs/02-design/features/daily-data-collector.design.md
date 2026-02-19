# daily-data-collector Design Document

> **Summary**: 유동성/크립토 데이터 자동 수집 + 수동 트리거 + Windows Task Scheduler 스케줄링
>
> **Project**: Stock Research ONE
> **Author**: Claude + User
> **Date**: 2026-02-19
> **Status**: Draft
> **Planning Doc**: [daily-data-collector.plan.md](../../01-plan/features/daily-data-collector.plan.md)

---

## 1. Overview

### 1.1 Design Goals

1. 크립토 데이터를 백엔드 수집 스크립트로 전환하여 히스토리 축적
2. 유동성/크립토 수집을 API 엔드포인트로 트리거 (대시보드 버튼 + 스케줄러 공용)
3. Windows Task Scheduler로 매일 자동 실행 (뉴스 수집 전 완료 보장)
4. 개별 수집기 실패 격리 (하나 실패해도 나머지 계속)

### 1.2 Design Principles

- 기존 `run_eod.py` 패턴 재사용 (try/except + [SKIP] 로그)
- API 엔드포인트와 CLI 스크립트 동일 코드 경로
- UPSERT로 중복 방지 (date + coin/metric PK)

---

## 2. Data Model

### 2.1 New Tables

#### CryptoPrice (일별 코인 가격)

```sql
CREATE TABLE crypto_price (
    date       TEXT NOT NULL,          -- YYYY-MM-DD
    coin_id    TEXT NOT NULL,          -- coingecko id: bitcoin, ethereum, ...
    symbol     TEXT NOT NULL,          -- BTC, ETH, ...
    price_usd  REAL,                   -- USD 가격
    market_cap REAL,                   -- 시가총액 (USD)
    volume_24h REAL,                   -- 24h 거래량
    change_24h REAL,                   -- 24h 변동률 (%)
    change_7d  REAL,                   -- 7d 변동률 (%)
    PRIMARY KEY (date, coin_id)
);
```

#### CryptoMetric (일별 시장 지표)

```sql
CREATE TABLE crypto_metric (
    date              TEXT PRIMARY KEY,  -- YYYY-MM-DD
    total_market_cap  REAL,              -- 전체 시가총액
    total_volume_24h  REAL,              -- 전체 24h 거래량
    btc_dominance     REAL,              -- BTC 도미넌스 (%)
    eth_btc_ratio     REAL,              -- ETH/BTC 비율
    fear_greed_index  INTEGER,           -- Fear & Greed (0-100)
    fear_greed_label  TEXT,              -- Extreme Fear/Fear/Neutral/Greed/Extreme Greed
    defi_tvl          REAL,              -- DeFi 총 TVL (USD)
    stablecoin_mcap   REAL,             -- 스테이블코인 총 시가총액
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### CollectorLog (수집 실행 이력)

```sql
CREATE TABLE collector_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    date       TEXT NOT NULL,          -- YYYY-MM-DD
    collector  TEXT NOT NULL,          -- liquidity, crypto, news
    status     TEXT NOT NULL,          -- success, partial, failed
    duration   REAL,                   -- 실행 시간 (초)
    details    TEXT,                   -- JSON: 각 단계별 결과
    triggered_by TEXT,                 -- api, scheduler, manual-cli
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 SQLAlchemy Models

파일: `backend/app/models/crypto.py`

```python
class CryptoPrice(Base):
    __tablename__ = "crypto_price"
    date = Column(String(10), primary_key=True)
    coin_id = Column(String(50), primary_key=True)
    symbol = Column(String(20), nullable=False)
    price_usd = Column(Float)
    market_cap = Column(Float)
    volume_24h = Column(Float)
    change_24h = Column(Float)
    change_7d = Column(Float)

class CryptoMetric(Base):
    __tablename__ = "crypto_metric"
    date = Column(String(10), primary_key=True)
    total_market_cap = Column(Float)
    total_volume_24h = Column(Float)
    btc_dominance = Column(Float)
    eth_btc_ratio = Column(Float)
    fear_greed_index = Column(Integer)
    fear_greed_label = Column(String(30))
    defi_tvl = Column(Float)
    stablecoin_mcap = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CollectorLog(Base):
    __tablename__ = "collector_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False)
    collector = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False)
    duration = Column(Float)
    details = Column(JSON)
    triggered_by = Column(String(30))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

파일: `backend/app/models/__init__.py` 에 import 추가

---

## 3. API Specification

### 3.1 Collector Router

파일: `backend/app/api/collector.py`
Prefix: `/api/v1/collector`

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| POST | `/liquidity` | 유동성 데이터 수집 트리거 | `{status, duration, steps}` |
| POST | `/crypto` | 크립토 데이터 수집 트리거 | `{status, duration, steps}` |
| POST | `/run-all` | 전체 순차 수집 (유동성→크립토) | `{status, collectors[]}` |
| GET | `/status` | 최근 수집 상태/이력 조회 | `{collectors: {liquidity, crypto, news}}` |

### 3.2 Endpoint Details

#### POST /api/v1/collector/liquidity

```python
@router.post("/liquidity")
async def collect_liquidity():
    """유동성 스트레스 데이터 수집 (run_eod.py 래핑)"""
    result = await asyncio.to_thread(_run_liquidity_collector)
    return result
    # Response: {
    #   "collector": "liquidity",
    #   "status": "success" | "partial" | "failed",
    #   "duration": 12.3,
    #   "date": "2026-02-19",
    #   "steps": {
    #     "fred": "success" | "skipped",
    #     "price": "success",
    #     "news": "success",
    #     "fed_tone": "success",
    #     "stress_calc": "success"
    #   }
    # }
```

#### POST /api/v1/collector/crypto

```python
@router.post("/crypto")
async def collect_crypto():
    """크립토 데이터 수집 (CoinGecko + DefiLlama + Fear&Greed)"""
    result = await asyncio.to_thread(_run_crypto_collector)
    return result
    # Response: {
    #   "collector": "crypto",
    #   "status": "success",
    #   "duration": 8.5,
    #   "date": "2026-02-19",
    #   "steps": {
    #     "coingecko_prices": "success (20 coins)",
    #     "coingecko_global": "success",
    #     "defillama_tvl": "success",
    #     "fear_greed": "success"
    #   }
    # }
```

#### POST /api/v1/collector/run-all

```python
@router.post("/run-all")
async def collect_all():
    """전체 순차 수집: 유동성 → 크립토"""
    result = await asyncio.to_thread(_run_all_collectors)
    return result
    # Response: {
    #   "status": "success",
    #   "total_duration": 25.1,
    #   "collectors": [
    #     {"collector": "liquidity", "status": "success", "duration": 12.3},
    #     {"collector": "crypto", "status": "success", "duration": 8.5}
    #   ]
    # }
```

#### GET /api/v1/collector/status

```python
@router.get("/status")
async def get_collector_status():
    """각 수집기 최근 실행 상태 조회"""
    # collector_log 테이블에서 각 collector별 최신 1건
    # Response: {
    #   "collectors": {
    #     "liquidity": {"date": "2026-02-19", "status": "success", "duration": 12.3, "triggered_by": "api"},
    #     "crypto": {"date": "2026-02-19", "status": "success", "duration": 8.5, "triggered_by": "scheduler"},
    #     "news": {"date": "2026-02-19", "status": "success", "duration": 45.2, "triggered_by": "api"}
    #   }
    # }
```

### 3.3 Crypto Data API (대시보드 연동용)

파일: `backend/app/api/crypto_data.py`
Prefix: `/api/v1/crypto`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/latest` | 최신 코인 가격 + 시장 지표 |
| GET | `/history?days=30` | 최근 N일 히스토리 |

#### GET /api/v1/crypto/latest

```python
# Response: {
#   "date": "2026-02-19",
#   "metrics": {
#     "total_market_cap": 3.2e12,
#     "btc_dominance": 54.2,
#     "fear_greed_index": 65,
#     "fear_greed_label": "Greed",
#     "eth_btc_ratio": 0.041,
#     "defi_tvl": 95.2e9,
#     "stablecoin_mcap": 215.3e9
#   },
#   "prices": [
#     {"coin_id": "bitcoin", "symbol": "BTC", "price_usd": 97500, "change_24h": 2.1, "market_cap": 1.93e12},
#     {"coin_id": "ethereum", "symbol": "ETH", "price_usd": 3200, "change_24h": -0.5, "market_cap": 385e9},
#     ...
#   ]
# }
```

---

## 4. Scripts Design

### 4.1 Crypto Monitor Scripts

#### `scripts/crypto_monitor/config.py`

```python
COINGECKO_TOP_COINS_URL = "https://api.coingecko.com/api/v3/coins/markets"
COINGECKO_GLOBAL_URL = "https://api.coingecko.com/api/v3/global"
COINGECKO_ETH_BTC_URL = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=btc"
DEFILLAMA_TVL_URL = "https://api.llama.fi/v2/protocols"
DEFILLAMA_STABLECOINS_URL = "https://stablecoins.llama.fi/stablecoins?includePrices=false"
FEAR_GREED_URL = "https://api.alternative.me/fng/?limit=1"

TOP_N_COINS = 20
REQUEST_DELAY = 2.0  # CoinGecko rate limit 대응
DB_PATH = "backend/stock_research.db"  # 상대경로 (project root 기준)
```

#### `scripts/crypto_monitor/coingecko_fetch.py`

```python
def run(target_date=None) -> dict:
    """CoinGecko top 20 coins 가격 수집 → crypto_price 테이블"""
    # 1. GET /coins/markets?vs_currency=usd&order=market_cap_desc&per_page=20
    # 2. UPSERT into crypto_price (date, coin_id)
    # 3. GET /global → total_market_cap, btc_dominance
    # 4. GET /simple/price?ids=ethereum&vs_currencies=btc → eth_btc_ratio
    # 5. Return: {"coins_saved": 20, "global_saved": True}
```

#### `scripts/crypto_monitor/defi_fetch.py`

```python
def run(target_date=None) -> dict:
    """DefiLlama TVL + 스테이블코인 데이터 수집"""
    # 1. GET /v2/protocols → sum(tvl) for total DeFi TVL
    # 2. GET /stablecoins → sum(circulating.peggedUSD) for stablecoin mcap
    # 3. Return: {"defi_tvl": 95.2e9, "stablecoin_mcap": 215.3e9}
```

#### `scripts/crypto_monitor/fear_greed_fetch.py`

```python
def run(target_date=None) -> dict:
    """Fear & Greed Index 수집"""
    # 1. GET https://api.alternative.me/fng/?limit=1
    # 2. Return: {"index": 65, "label": "Greed"}
```

#### `scripts/crypto_monitor/run_crypto.py`

```python
def run(target_date=None) -> dict:
    """통합 배치 러너: CoinGecko → DefiLlama → Fear&Greed → DB 저장"""
    # Pattern: run_eod.py와 동일
    # Step 1: coingecko_fetch.run() → crypto_price + partial crypto_metric
    # Step 2: defi_fetch.run() → crypto_metric.defi_tvl, stablecoin_mcap
    # Step 3: fear_greed_fetch.run() → crypto_metric.fear_greed_*
    # Step 4: UPSERT crypto_metric (all fields merged)
    # 각 단계 try/except + [SKIP] on failure
```

### 4.2 Collector API Internal Functions

파일: `backend/app/api/collector.py`

```python
def _run_liquidity_collector() -> dict:
    """run_eod.py 호출 래핑"""
    # sys.path에 scripts/liquidity_monitor 추가
    # run_eod.run() 호출
    # 결과를 collector_log에 기록
    # return structured result

def _run_crypto_collector() -> dict:
    """run_crypto.py 호출 래핑"""
    # sys.path에 scripts/crypto_monitor 추가
    # run_crypto.run() 호출
    # 결과를 collector_log에 기록

def _run_all_collectors() -> dict:
    """순차: 유동성 → 크립토"""
    result_liq = _run_liquidity_collector()
    result_crypto = _run_crypto_collector()
    return {"collectors": [result_liq, result_crypto], ...}
```

---

## 5. Windows Task Scheduler

### 5.1 스케줄 구성

| Task Name | Time (KST) | Command | Purpose |
|-----------|------------|---------|---------|
| `Stock_DataCollect_0600` | 06:00 | `curl -X POST http://localhost:8000/api/v1/collector/run-all` | 유동성+크립토 |
| `Stock_NewsFetch_0630` | 06:30 | `curl -X POST http://localhost:8000/api/v1/news-intel/fetch` | 뉴스 수집 |

### 5.2 Registration Script

파일: `scripts/dev/register_daily_collector.ps1`

```powershell
# 패턴: register_moat_sync_task.ps1와 동일
param(
    [string]$CollectorTaskName = "Stock_DataCollect_0600",
    [string]$CollectorTime = "06:00",
    [string]$NewsTaskName = "Stock_NewsFetch_0630",
    [string]$NewsTime = "06:30"
)

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$collectorCmd = Join-Path $root "scripts\dev\run_daily_collector.cmd"
$newsCmd = Join-Path $root "scripts\dev\run_news_fetch.cmd"

# schtasks /Create /F /SC DAILY /ST $CollectorTime /TN $CollectorTaskName /TR $collectorCmd
# schtasks /Create /F /SC DAILY /ST $NewsTime /TN $NewsTaskName /TR $newsCmd
```

### 5.3 CMD Runner Files

`scripts/dev/run_daily_collector.cmd`:
```cmd
@echo off
curl -s -X POST http://localhost:8000/api/v1/collector/run-all >> "%~dp0..\..\data\runtime\logs\collector_stdout.log" 2>&1
```

`scripts/dev/run_news_fetch.cmd`:
```cmd
@echo off
curl -s -X POST http://localhost:8000/api/v1/news-intel/fetch >> "%~dp0..\..\data\runtime\logs\news_fetch_stdout.log" 2>&1
```

---

## 6. Dashboard UI Changes

### 6.1 유동성 모니터 수동 수집 버튼

파일: `dashboard/liquidity_stress.html`

```jsx
// 헤더 영역에 "데이터 수집" 버튼 추가
<button onClick={handleCollectLiquidity}>
    유동성 데이터 수집
</button>

// handleCollectLiquidity:
const handleCollectLiquidity = async () => {
    setCollecting(true);
    const res = await fetch(`${API_BASE}/api/v1/collector/liquidity`, {method: 'POST'});
    const data = await res.json();
    // 성공 시 페이지 데이터 리로드
    setCollecting(false);
};
```

### 6.2 크립토 모니터 수동 수집 버튼

파일: `dashboard/crypto_trends.html`

```jsx
// 기존 브라우저 직접 API 호출 유지 + "DB에서 수집" 버튼 추가
<button onClick={handleCollectCrypto}>
    크립토 데이터 수집 (DB 저장)
</button>

// Phase 1: 수동 수집 버튼으로 DB 저장 트리거
// Phase 2 (향후): 브라우저 직접 호출을 DB 데이터로 완전 전환
```

### 6.3 수집 상태 표시

각 모니터 페이지 헤더에:
```
마지막 수집: 2026-02-19 06:01 (자동) | 상태: 성공
```

`GET /api/v1/collector/status` 응답으로 렌더링.

---

## 7. Implementation Order

| # | Task | Files | Priority |
|---|------|-------|----------|
| 1 | DB 모델 추가 (CryptoPrice, CryptoMetric, CollectorLog) | `backend/app/models/crypto.py`, `__init__.py` | High |
| 2 | 크립토 수집 스크립트 (config, coingecko, defi, fear_greed, run_crypto) | `scripts/crypto_monitor/*.py` | High |
| 3 | Collector API 라우터 | `backend/app/api/collector.py`, `main.py` | High |
| 4 | Crypto Data API 라우터 | `backend/app/api/crypto_data.py`, `main.py` | High |
| 5 | 유동성 모니터 수동 수집 버튼 | `dashboard/liquidity_stress.html` | Medium |
| 6 | 크립토 모니터 수동 수집 버튼 | `dashboard/crypto_trends.html` | Medium |
| 7 | 수집 상태 표시 (마지막 수집 시간) | 각 dashboard HTML | Medium |
| 8 | Windows Task Scheduler 등록 스크립트 | `scripts/dev/register_daily_collector.ps1` 등 | Medium |

---

## 8. Error Handling

| Scenario | Handling |
|----------|----------|
| CoinGecko 429 Rate Limit | 2초 sleep + 1회 재시도 → [SKIP] |
| Yahoo Finance 429 | DB 캐시 fallback (기존 구현) |
| FRED API key 미설정 | SKIP (기존 동작) |
| DefiLlama 서버 다운 | [SKIP], crypto_metric에 null 저장 |
| 서버 미기동 시 스케줄 호출 | curl 실패 → 로그에 기록 |
| 중복 수집 (같은 날 2번) | UPSERT로 덮어쓰기 |

---

## 9. Test Plan

| Test | Method | Expected |
|------|--------|----------|
| 크립토 수집 스크립트 단독 실행 | `python scripts/crypto_monitor/run_crypto.py` | DB에 20 coins + 1 metric 저장 |
| Collector API liquidity | `curl -X POST .../collector/liquidity` | 5 steps 실행, collector_log 기록 |
| Collector API crypto | `curl -X POST .../collector/crypto` | 4 steps 실행, collector_log 기록 |
| Collector API run-all | `curl -X POST .../collector/run-all` | 순차 실행, 총 시간 반환 |
| Collector status | `GET .../collector/status` | 각 collector 최신 상태 |
| 대시보드 수동 버튼 | 브라우저에서 클릭 | 데이터 갱신 확인 |
| 스케줄러 등록 | `register_daily_collector.ps1` | schtasks에 2개 태스크 등록 |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-19 | Initial design from plan document | Claude + User |
