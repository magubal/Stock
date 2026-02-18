# Feature Design: Liquidity & Credit Stress Monitor

## 1. DB Schema

### 1.1 liquidity_macro (일별 FRED 매크로 지표)
| Column | Type | Description |
|--------|------|-------------|
| date | TEXT PK | 날짜 (YYYY-MM-DD) |
| hy_oas | REAL | High Yield OAS (%) |
| ig_oas | REAL | Investment Grade OAS (%) |
| sofr | REAL | SOFR 금리 (%) |
| rrp_balance | REAL | 역리포 잔고 (십억달러) |
| dgs2 | REAL | 2년 국채 금리 |
| dgs10 | REAL | 10년 국채 금리 |
| dgs30 | REAL | 30년 국채 금리 |
| created_at | TEXT | 생성 시각 |

### 1.2 liquidity_price (일별 ETF/지수 종가)
| Column | Type | Description |
|--------|------|-------------|
| date | TEXT | 날짜 |
| symbol | TEXT | 티커 (^VIX, HYG, TLT 등) |
| close | REAL | 종가 |
| high | REAL | 고가 |
| low | REAL | 저가 |
| volume | REAL | 거래량 |
| PK: (date, symbol) |

### 1.3 liquidity_news (일별 뉴스 키워드 카운트)
| Column | Type | Description |
|--------|------|-------------|
| date | TEXT | 날짜 |
| keyword | TEXT | 검색 키워드 |
| count | INTEGER | 기사 수 |
| sample_titles | TEXT | 대표 기사 제목 (최대 5건) |
| PK: (date, keyword) |

### 1.4 fed_tone (Fed 스피치 톤 분석)
| Column | Type | Description |
|--------|------|-------------|
| date | TEXT PK | 날짜 |
| liquidity_score | REAL | 유동성 관련 키워드 비중 |
| credit_score | REAL | 크레딧 관련 키워드 비중 |
| stability_score | REAL | 금융안정 관련 키워드 비중 |

### 1.5 stress_index (종합 스트레스 인덱스)
| Column | Type | Description |
|--------|------|-------------|
| date | TEXT PK | 날짜 |
| vol_score | REAL | 변동성 점수 (0~1) |
| credit_score | REAL | 크레딧 점수 (0~1) |
| funding_score | REAL | 자금시장 점수 (0~1) |
| treasury_score | REAL | 국채 유동성 점수 (0~1) |
| news_score | REAL | 뉴스 위기 점수 (0~1) |
| fed_tone_score | REAL | Fed 톤 점수 (0~1) |
| total_score | REAL | 종합 스트레스 (0~1) |
| level | TEXT | 등급 (normal/watch/caution/stress/crisis) |

## 2. API Endpoints

### 2.1 GET /api/v1/liquidity-stress
최신 스트레스 데이터 반환.

**Response:**
```json
{
  "date": "2026-02-14",
  "totalScore": 0.32,
  "level": "watch",
  "levelLabel": "관심",
  "modules": {
    "volatility": { "score": 0.28, "vix": 18.5, "vixChange": -2.3 },
    "credit": { "score": 0.35, "hyOas": 3.45, "igOas": 0.92 },
    "funding": { "score": 0.22, "sofr": 4.32, "rrpBalance": 120.5 },
    "treasury": { "score": 0.40, "dgs10": 4.15, "tltClose": 88.2 },
    "news": { "score": 0.30, "totalCount": 25, "topKeyword": "liquidity crisis" },
    "fedTone": { "score": 0.15, "liquidityFocus": 0.12, "stabilityFocus": 0.08 }
  },
  "macro": {
    "dgs2": 3.95, "dgs10": 4.15, "dgs30": 4.35,
    "hyOas": 3.45, "igOas": 0.92, "sofr": 4.32
  }
}
```

### 2.2 GET /api/v1/liquidity-stress/history?days=30
히스토리 반환.

**Response:**
```json
{
  "history": [
    { "date": "2026-01-15", "totalScore": 0.28, "level": "normal", ... },
    { "date": "2026-01-16", "totalScore": 0.31, "level": "watch", ... },
    ...
  ]
}
```

## 3. Stress Index Calculation

### 3.1 Module Scoring (각 0.0~1.0 정규화)
| Module | Input | Low (0.0) | High (1.0) |
|--------|-------|-----------|------------|
| Volatility | VIX | 12 | 35 |
| Credit | HY OAS | 2.5% | 6.0% |
| Funding | SOFR - 정책금리 | 0 bp | 50 bp |
| Treasury | TLT 변동성(5일) | 0.5% | 5.0% |
| News | 총 키워드 카운트 | 0 | 80 |
| Fed Tone | 키워드 비중 합계 | 0 | 0.5 |

### 3.2 Weighted Average
```
total = 0.25 * vol + 0.25 * credit + 0.20 * funding
      + 0.15 * treasury + 0.10 * news + 0.05 * fedTone
```

### 3.3 Level Mapping
| Score Range | Level | Label | Color |
|-------------|-------|-------|-------|
| 0.00 ~ 0.25 | normal | 안정 | #22c55e (green) |
| 0.25 ~ 0.40 | watch | 관심 | #eab308 (yellow) |
| 0.40 ~ 0.55 | caution | 주의 | #f97316 (orange) |
| 0.55 ~ 0.75 | stress | 경계 | #ef4444 (red) |
| 0.75 ~ 1.00 | crisis | 위기 | #dc2626 (dark red) |

## 4. Frontend Page Layout

### 4.1 liquidity_stress.html 레이아웃
```
+--------------------------------------------------+
| Header: "유동성 & 신용 스트레스 모니터"  [← 돌아가기] |
+--------------------------------------------------+
| [게이지 차트]       | 종합 스트레스: 0.32         |
| 등급: 관심 (Watch)  | 날짜: 2026-02-14          |
+--------------------------------------------------+
| 모듈별 점수 (6개 수평 바 차트)                      |
| ■ 변동성 0.28  ■ 크레딧 0.35  ■ 자금시장 0.22    |
| ■ 국채유동성 0.40  ■ 뉴스 0.30  ■ Fed톤 0.15     |
+--------------------------------------------------+
| 핵심 지표 카드 (4열 그리드)                          |
| VIX: 18.5 | HY OAS: 3.45% | SOFR: 4.32% | 10Y: 4.15% |
+--------------------------------------------------+
| 30일 히스토리 라인 차트 (Chart.js)                  |
| (x축: 날짜, y축: totalScore, 배경 색상으로 등급 표시) |
+--------------------------------------------------+
| 최근 위기 뉴스 키워드 Top 5                         |
+--------------------------------------------------+
```

### 4.2 dashboard/index.html 수정
시장 모니터링 섹션의 "새 항목 추가 예정" placeholder를 실제 링크로 교체:
```
오늘의 공시          → monitor_disclosures.html
유동성 및 신용 스트레스 → liquidity_stress.html  (NEW)
```

## 4.3 DetailModal (상세 팝업)

모듈 바 또는 KPI 카드를 클릭하면 DetailModal이 표시된다.

### 구성요소
1. **제목**: 모듈명 (예: "변동성 (VIX)")
2. **세부 지표 그리드**: 모듈별 주요 수치 (2~6개 항목)
3. **30일 추이 미니 차트**: 해당 모듈의 히스토리 라인 차트
4. **설명**: 해당 모듈의 측정 방법 및 의미 설명
5. **참조 링크**: 데이터 출처 URL 목록

### MODULE_SOURCES 매핑
| Module | 참조 출처 |
|--------|-----------|
| volatility | Yahoo Finance VIX, CBOE VIX Index |
| credit | FRED HY OAS (BAMLH0A0HYM2), FRED IG OAS (BAMLC0A0CM) |
| funding | FRED SOFR, FRED RRP (RRPONTSYD) |
| treasury | FRED DGS10, DGS2, DGS30, Yahoo Finance TLT |
| news | Google News RSS (liquidity crisis, credit crunch, margin call) |
| fedTone | Fed 보도자료 페이지, Fed RSS Feed |

### 모듈별 detailItems
- **volatility**: VIX 현재, VIX 전일비, 모듈 점수, 가중치
- **credit**: HY OAS, IG OAS, 모듈 점수, 가중치
- **funding**: SOFR, 역리포 잔고, 모듈 점수, 가중치
- **treasury**: 10Y 금리, 2Y 금리, 30Y 금리, TLT 종가, 모듈 점수, 가중치
- **news**: Top 키워드, 총 뉴스 수, 모듈 점수, 가중치
- **fedTone**: 유동성 키워드, 안정성 키워드, 모듈 점수, 가중치

## 4.4 데이터 수집 스크립트

### Yahoo Finance (price_fetch.py)
- v8 chart API 사용 (`/v8/finance/chart/{symbol}`)
- JSON 응답에서 timestamp, close, high, low, volume 추출
- 심볼: ^VIX, HYG, LQD, TLT, IEF, SHV, KRE, VNQ

### Google News (news_fetch.py)
- RSS 엔드포인트: `news.google.com/rss/search?q={keyword}`
- 6개 키워드: liquidity crisis, margin call, credit default, repo market, private credit, CRE default
- 카운트 + 대표 제목 5건 저장

### Fed Tone (fed_speech_fetch.py)
- RSS: `federalreserve.gov/feeds/press_all.xml`
- 최근 20건 Atom/RSS 항목에서 liquidity/credit/stability 키워드 비중 분석

### FRED (fred_fetch.py)
- 환경변수 `FRED_API_KEY` 필요 (무료 발급)
- 미설정 시 SKIP (다른 수집기는 정상 동작)

## 5. File Structure
```
backend/app/
├── api/liquidity_stress.py          # New router
├── services/liquidity_stress_service.py  # New service
├── models/__init__.py               # Add 5 new models

scripts/liquidity_monitor/
├── __init__.py
├── config.py                        # FRED API key, symbols
├── fred_fetch.py                    # FRED data fetcher
├── price_fetch.py                   # Yahoo Finance CSV fetcher
├── news_fetch.py                    # Google News RSS fetcher
├── fed_speech_fetch.py              # Fed speech tone analyzer
├── stress_calculator.py             # Stress index calculator
├── run_eod.py                       # EOD batch runner
└── seed_data.py                     # Demo data generator

dashboard/
├── index.html                       # Modified: add link
└── liquidity_stress.html            # New: monitor page
```

## 6. Implementation Order
1. DB Models (5 tables) + migration ✅
2. Seed data script ✅
3. Backend Service (liquidity_stress_service.py) ✅
4. Backend API endpoints (2 routes) ✅
5. main.py router 등록 + CORS ✅
6. Dashboard link in index.html ✅
7. Liquidity stress monitor page (게이지, 모듈바, KPI, 히스토리) ✅
8. DetailModal (클릭 상세 팝업 + 미니 차트) ✅
9. 소스 참조 링크 (MODULE_SOURCES) ✅
10. Data fetching scripts (Yahoo v8 API, News RSS, Fed RSS) ✅
11. FRED API 연동 (API key 설정 후)
