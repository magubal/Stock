# News Intelligence Monitor Design Document

> **Summary**: Finviz 뉴스 파싱 + Claude AI 기반 핵심이슈/내러티브/섹터 영향도 분석 모니터
>
> **Project**: Stock Research ONE
> **Author**: Claude
> **Created**: 2026-02-19
> **Last Modified**: 2026-02-19
> **Status**: Draft

---

## 1. Architecture Overview

### 1.1 Data Flow

```
[Finviz HTML]                    [Future Sources]
     │                                │
     ▼                                ▼
finviz_fetch.py              (yahoo_fetch.py, ...)
     │                                │
     └──────────┬─────────────────────┘
                ▼
        news_articles (DB)
                │
                ▼
     narrative_analyzer.py  ── Claude Sonnet API
                │
                ▼
      market_narratives (DB)
                │
                ▼
     FastAPI Router (2 endpoints)
                │
                ▼
     news_intelligence.html (Dashboard)
```

### 1.2 File Structure

```
scripts/news_monitor/
├── __init__.py
├── config.py                 # 소스별 설정, DB 경로, 상수
├── finviz_fetch.py           # Finviz HTML 파서 + DB 저장
├── narrative_analyzer.py     # Claude API 분석기
├── run_news.py               # 배치 실행 CLI (파싱 → 저장 → 분석)
└── seed_data.py              # DEMO 시드 데이터 생성

backend/app/
├── models/
│   └── news_article.py       # NewsArticle, MarketNarrative 모델
├── api/
│   └── news_intelligence.py  # GET articles, GET narrative
└── services/
    └── news_intelligence_service.py  # 비즈니스 로직

dashboard/
└── news_intelligence.html    # 뉴스 인텔리전스 대시보드 페이지
```

---

## 2. Data Model

### 2.1 NewsArticle (news_articles)

```python
class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False, index=True)       # "finviz", "yahoo", ...
    category = Column(String(50), nullable=False, index=True)     # "market", "market_pulse", "stock", "etf", "crypto"
    title = Column(String(500), nullable=False)
    url = Column(String(500), nullable=False)
    publisher = Column(String(100))                               # "Bloomberg", "CNBC", ...
    published_at = Column(DateTime(timezone=True), index=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    summary = Column(Text)                                        # AI 생성 요약 (선택)

    __table_args__ = (
        UniqueConstraint('source', 'url', name='uq_source_url'),
    )
```

### 2.2 MarketNarrative (market_narratives)

```python
class MarketNarrative(Base):
    __tablename__ = "market_narratives"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), unique=True, nullable=False, index=True)  # "YYYY-MM-DD"
    key_issues = Column(JSON)           # [{title, summary, impact, category}]
    narrative = Column(Text)            # 시장 내러티브 요약 (2~3문단)
    sector_impact = Column(JSON)        # [{sector, direction, confidence, reason}]
    sentiment_score = Column(Float)     # -1.0 ~ 1.0
    sentiment_label = Column(String(20))# fear/cautious/neutral/optimistic/greed
    article_count = Column(Integer)
    generated_by = Column(String(50))   # "claude-sonnet", "DEMO"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 2.3 JSON Schema Details

**key_issues** (배열, 최대 3개):
```json
[
  {
    "title": "Fed 금리 동결 시사",
    "summary": "파월 의장이 당분간 금리 동결을 시사하며...",
    "impact": "high",
    "category": "macro"
  }
]
```

**sector_impact** (배열):
```json
[
  {
    "sector": "Technology",
    "direction": "bullish",
    "confidence": 0.8,
    "reason": "AI 투자 확대 뉴스 다수"
  },
  {
    "sector": "Banking",
    "direction": "bearish",
    "confidence": 0.6,
    "reason": "CRE 손실 우려 보도"
  }
]
```

**sentiment_label 매핑**:
| Range | Label |
|-------|-------|
| -1.0 ~ -0.6 | fear |
| -0.6 ~ -0.2 | cautious |
| -0.2 ~ 0.2 | neutral |
| 0.2 ~ 0.6 | optimistic |
| 0.6 ~ 1.0 | greed |

---

## 3. Scripts Design

### 3.1 config.py

```python
# DB 경로 (기존 패턴 따름)
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'stock_research.db')

# Finviz 설정
FINVIZ_URL = "https://finviz.com/news.ashx"
FINVIZ_CATEGORIES = ["market", "market_pulse", "stock", "etf", "crypto"]

# 요청 설정
REQUEST_DELAY = 2.0           # 카테고리 간 딜레이 (초)
USER_AGENTS = [...]           # User-Agent 로테이션 리스트 (3~5개)
REQUEST_TIMEOUT = 15          # 타임아웃 (초)

# Claude API 설정
ANTHROPIC_MODEL = "claude-sonnet-4-5-20250929"
MAX_ARTICLES_FOR_ANALYSIS = 80  # 분석에 사용할 최대 기사 수
```

### 3.2 finviz_fetch.py

**핵심 함수**:

```python
def fetch_finviz_news(category: str) -> list[dict]:
    """
    Finviz HTML에서 특정 카테고리 뉴스 파싱.
    Returns: [{title, url, publisher, published_at, category}]
    """

def save_articles(articles: list[dict], source: str = "finviz") -> tuple[int, int]:
    """
    DB에 저장 (중복 무시).
    Returns: (saved_count, skipped_count)
    """

def fetch_all_categories() -> dict:
    """
    5개 카테고리 순차 수집 (딜레이 포함).
    Returns: {category: {saved, skipped}}
    """
```

**파싱 전략**:
- `requests.get()` + `BeautifulSoup` (기존 프로젝트 패턴)
- Finviz 뉴스 테이블에서 `<tr>` 단위로 제목/URL/매체/시간 추출
- `published_at`: Finviz 상대시간("10:30AM") → `datetime` 변환
- 실패 시 해당 카테고리만 스킵, 나머지 계속 진행

### 3.3 narrative_analyzer.py

**핵심 함수**:

```python
def analyze_today_news(target_date: str = None) -> dict:
    """
    당일 뉴스를 Claude API로 분석.
    1. DB에서 당일 기사 조회 (최대 MAX_ARTICLES_FOR_ANALYSIS)
    2. Claude API 호출 (구조화 JSON 응답 강제)
    3. market_narratives 테이블에 저장 (UPSERT)
    Returns: {key_issues, narrative, sector_impact, sentiment_score, sentiment_label}
    """
```

**Claude API 프롬프트 구조**:

```
System: You are a financial market analyst. Analyze today's news headlines and provide investment intelligence.

User:
## Today's News ({article_count} articles, {date})
{category별 기사 제목 리스트}

## Required Output (JSON):
{
  "key_issues": [최대 3개 핵심이슈],
  "narrative": "2~3문단 시장 내러티브",
  "sector_impact": [섹터별 영향도],
  "sentiment_score": -1.0~1.0,
  "sentiment_label": "fear|cautious|neutral|optimistic|greed"
}
```

**동일 날짜 재분석 방지**: `date` 유니크 제약으로 UPSERT (기존 있으면 UPDATE)

### 3.4 run_news.py

```python
def main():
    """
    배치 실행 엔트리포인트.
    1. fetch_all_categories() → 뉴스 수집
    2. analyze_today_news() → AI 분석 (--skip-analysis 옵션으로 스킵 가능)
    3. 결과 요약 출력
    """

# CLI: python scripts/news_monitor/run_news.py [--skip-analysis] [--date YYYY-MM-DD]
```

### 3.5 seed_data.py

DEMO 데이터 규칙 준수:
- `NewsArticle`: `source="DEMO"`, 20~30건 (카테고리별 4~6건)
- `MarketNarrative`: `generated_by="DEMO"`, 3일분
- 콘솔 출력: `[SEED]` 프리픽스

---

## 4. API Specification

### 4.1 GET /api/v1/news-intel/articles

뉴스 기사 목록 조회.

**Query Parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| category | string | (all) | 카테고리 필터 (market, market_pulse, stock, etf, crypto) |
| date | string | today | 날짜 필터 (YYYY-MM-DD) |
| source | string | (all) | 소스 필터 (finviz, yahoo, ...) |
| limit | int | 50 | 최대 건수 (1~200) |

**Response** (200):
```json
{
  "date": "2026-02-19",
  "total": 47,
  "articles": [
    {
      "id": 1,
      "source": "finviz",
      "category": "market",
      "title": "Fed Signals Pause on Rate Cuts",
      "url": "https://...",
      "publisher": "Bloomberg",
      "published_at": "2026-02-19T14:30:00Z",
      "fetched_at": "2026-02-19T15:00:00Z"
    }
  ]
}
```

### 4.2 GET /api/v1/news-intel/narrative

당일 AI 분석 내러티브 조회.

**Query Parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| date | string | today | 날짜 (YYYY-MM-DD) |

**Response** (200):
```json
{
  "date": "2026-02-19",
  "key_issues": [
    {
      "title": "Fed 금리 동결 시사",
      "summary": "파월 의장이 당분간 금리 동결을...",
      "impact": "high",
      "category": "macro"
    }
  ],
  "narrative": "오늘 시장은 Fed의 금리 정책 시그널에...",
  "sector_impact": [
    {
      "sector": "Technology",
      "direction": "bullish",
      "confidence": 0.8,
      "reason": "AI 투자 확대 뉴스"
    }
  ],
  "sentiment": {
    "score": 0.15,
    "label": "neutral"
  },
  "article_count": 47,
  "generated_by": "claude-sonnet"
}
```

**Response** (404 - 분석 결과 없음):
```json
{
  "detail": "해당 날짜의 분석 결과가 없습니다",
  "error_code": "NARRATIVE_NOT_FOUND"
}
```

---

## 5. Service Layer

### 5.1 NewsIntelligenceService

```python
class NewsIntelligenceService:
    def __init__(self, db: Session):
        self.db = db

    async def get_articles(
        self, category: str = None, date: str = None,
        source: str = None, limit: int = 50
    ) -> dict:
        """기사 목록 조회"""

    async def get_narrative(self, date: str = None) -> dict:
        """내러티브 조회 (없으면 404)"""
```

---

## 6. Dashboard UI Design

### 6.1 Page Layout (news_intelligence.html)

기존 모니터 페이지 패턴 (`crypto_trends.html`, `liquidity_stress.html`) 따름.

**전체 구조**:
```
┌──────────────────────────────────────────────┐
│ Header: News Intelligence + 날짜 + 새로고침   │
├──────────────────────────────────────────────┤
│ [AI Briefing Panel]                           │
│ ┌──────────────────────────────────────────┐ │
│ │ 핵심이슈 3개 카드 (제목+요약+임팩트)      │ │
│ │ 시장 내러티브 (2~3문단)                    │ │
│ │ 센티먼트 게이지 (fear ← → greed)          │ │
│ └──────────────────────────────────────────┘ │
├──────────────────────────────────────────────┤
│ [Sector Impact Matrix]                        │
│ ┌──────────────────────────────────────────┐ │
│ │ Tech ▲ | Banking ▼ | Energy ─ | ...     │ │
│ │ (direction + confidence bar + reason)     │ │
│ └──────────────────────────────────────────┘ │
├──────────────────────────────────────────────┤
│ [Category Tabs] All | Market | Pulse | ...    │
├──────────────────────────────────────────────┤
│ [News List]                                   │
│ ┌──────────────────────────────────────────┐ │
│ │ 10:30 │ Bloomberg │ Fed Signals Pause...  │ │
│ │ 10:15 │ CNBC      │ S&P 500 hits new...  │ │
│ │ ...                                       │ │
│ └──────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

### 6.2 Color Scheme

기존 다크 테마 일관성 유지 + 뉴스 특화 액센트:
| Element | Color | Usage |
|---------|-------|-------|
| 배경 | `#0a0a0a` → `#1a1a2e` gradient | 기존 패턴 |
| 뉴스 액센트 | `#f97316` (Orange) | 로고, 액센트, 링크 배지 |
| Bullish | `#22c55e` | 섹터 영향도 긍정 |
| Bearish | `#ef4444` | 섹터 영향도 부정 |
| Neutral | `#94a3b8` | 중립 |
| 센티먼트 바 | `#ef4444` → `#eab308` → `#22c55e` | Fear → Greed 그래디언트 |
| 카테고리 탭 | `#f97316` active, `#334155` inactive | 필터 탭 |

### 6.3 Component Specs

**AI Briefing Panel**:
- 핵심이슈 카드: 최대 3개, `impact` 레벨별 테두리 색상 (high=red, medium=yellow, low=green)
- 내러티브: 텍스트 블록, 최대 3문단
- 센티먼트: 수평 게이지바 (`-1.0 ~ 1.0`), 라벨 표시

**Sector Impact Matrix**:
- 그리드 레이아웃 (2~3열)
- 각 섹터: 이름 + 방향 아이콘(▲▼─) + confidence 바 + 이유 텍스트
- `direction`: bullish=green, bearish=red, neutral=gray

**Category Filter Tabs**:
- 6개 탭: All, Market, Market Pulse, Stock, ETF, Crypto
- 각 탭에 기사 수 표시
- 클릭 시 뉴스 리스트 필터링 (API 재호출 없이 클라이언트 필터)

**News List**:
- 시간순 정렬 (최신 먼저)
- 각 행: 시간 | 매체명 | 제목 (외부 링크)
- DEMO 데이터: 빨간 `DEMO` 배지 표시

### 6.4 DEMO Data Display

```javascript
const isDemo = (source) => source === 'DEMO';
// 또는 generated_by === 'DEMO' (내러티브)

// 상단 경고 배너 (DEMO 데이터 존재 시)
if (demoCount > 0) {
    renderBanner(`DEMO 데이터 ${demoCount}건 포함`);
}
```

---

## 7. Main Dashboard Link

[dashboard/index.html](../../../dashboard/index.html) 시장모니터링 섹션에 추가:

```jsx
<a href="news_intelligence.html" className="monitoring-link">
    <span className="monitoring-name">글로벌 뉴스 인텔리전스</span>
    <span className="monitoring-desc">AI 기반 핵심이슈/내러티브/영향도</span>
</a>
```

위치: 기존 5개 링크 중 "오늘의 공시" 바로 아래 (뉴스 성격 유사).

---

## 8. Playwright Test

### 8.1 dashboard-core.spec.ts 업데이트

```typescript
// REQUIRED_LINKS에 추가
const REQUIRED_LINKS = [
    'monitor_disclosures.html',
    'news_intelligence.html',      // NEW
    'liquidity_stress.html',
    'crypto_trends.html',
    'moat_analysis.html',
    'idea_board.html',
];
```

### 8.2 news-intelligence.spec.ts (신규)

```typescript
test.describe('news_intelligence.html core', () => {
    test('renders AI briefing and news list', async ({ page }) => {
        // 1. API mock (articles + narrative)
        // 2. 페이지 로드
        // 3. AI Briefing 패널 존재 확인
        // 4. 카테고리 탭 6개 존재 확인
        // 5. 뉴스 리스트 렌더링 확인
        // 6. 콘솔 에러 없음 확인
    });
});
```

---

## 9. Error Handling

| Scenario | Handling |
|----------|----------|
| Finviz 403/차단 | `fetch_finviz_news()` → 빈 리스트 반환 + 로그 경고 |
| Finviz HTML 구조 변경 | 파싱 실패 시 해당 카테고리 스킵 + 경고 |
| Claude API 실패 | `narrative_analyzer.py` → 예외 로그 + `run_news.py`에서 catch |
| Claude API 응답 파싱 실패 | JSON 파싱 실패 → 원본 텍스트 `narrative`에 저장 |
| DB 중복 저장 | `(source, url)` unique → INSERT OR IGNORE |
| API 엔드포인트 - 데이터 없음 | articles → 빈 배열, narrative → 404 |
| 대시보드 - API 실패 | "데이터를 불러올 수 없습니다" 메시지 표시 |

---

## 10. Implementation Order

| Step | Task | File | Est. Lines |
|------|------|------|-----------|
| 1 | DB 모델 정의 | `backend/app/models/news_article.py` | ~45 |
| 2 | 모델 등록 | `backend/app/models/__init__.py` | ~3 |
| 3 | 수집 설정 | `scripts/news_monitor/config.py` | ~50 |
| 4 | Finviz 파서 | `scripts/news_monitor/finviz_fetch.py` | ~130 |
| 5 | AI 분석기 | `scripts/news_monitor/narrative_analyzer.py` | ~120 |
| 6 | 배치 스크립트 | `scripts/news_monitor/run_news.py` | ~70 |
| 7 | API 서비스 | `backend/app/services/news_intelligence_service.py` | ~70 |
| 8 | API 라우터 | `backend/app/api/news_intelligence.py` | ~55 |
| 9 | main.py 등록 | `backend/app/main.py` | ~2 |
| 10 | 대시보드 페이지 | `dashboard/news_intelligence.html` | ~650 |
| 11 | 메인 대시보드 링크 | `dashboard/index.html` | ~5 |
| 12 | 시드 데이터 | `scripts/news_monitor/seed_data.py` | ~90 |
| 13 | Playwright 테스트 | `tests/playwright/tests/` | ~10 |

---

## 11. Verification Criteria (Gap Analysis)

| ID | 검증 항목 | 확인 방법 |
|----|-----------|-----------|
| V-01 | `news_articles` 테이블 존재 + 스키마 일치 | DB 확인 |
| V-02 | `(source, url)` 유니크 제약 | 중복 INSERT 테스트 |
| V-03 | `market_narratives` 테이블 존재 + `date` 유니크 | DB 확인 |
| V-04 | `finviz_fetch.py` 5개 카테고리 파싱 함수 | 코드 확인 |
| V-05 | `narrative_analyzer.py` Claude API 호출 + JSON 파싱 | 코드 확인 |
| V-06 | `run_news.py` CLI 실행 가능 | 코드 확인 |
| V-07 | GET `/api/v1/news-intel/articles` 응답 | curl/httpie |
| V-08 | GET `/api/v1/news-intel/narrative` 응답 | curl/httpie |
| V-09 | `main.py`에 라우터 등록 | 코드 확인 |
| V-10 | 대시보드: 카테고리 필터 탭 6개 | 브라우저 확인 |
| V-11 | 대시보드: AI 브리핑 패널 (핵심이슈 + 내러티브 + 센티먼트) | 브라우저 확인 |
| V-12 | 대시보드: 섹터 영향도 매트릭스 | 브라우저 확인 |
| V-13 | 대시보드: 뉴스 리스트 시간순 | 브라우저 확인 |
| V-14 | 메인 대시보드 시장모니터링 링크 존재 | index.html 확인 |
| V-15 | Playwright `REQUIRED_LINKS`에 `news_intelligence.html` | 테스트 확인 |
| V-16 | 다크 테마 일관성 (기존 모니터 색상) | 시각 확인 |
| V-17 | DEMO 데이터 규칙 준수 (source="DEMO", 배지, 배너) | 코드+브라우저 확인 |
| V-18 | 외부 라이브러리 추가 없음 | HTML `<script>` 확인 |
| V-19 | 시드 데이터 존재 (articles 20건+, narratives 3일분) | DB 확인 |

---

## 12. Related Documents

- Plan: [news-intelligence-monitor.plan.md](../../01-plan/features/news-intelligence-monitor.plan.md)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-19 | Initial design | Claude |
