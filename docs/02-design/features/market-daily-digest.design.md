# Design: Market Daily Digest (시장 종합정리)

> **Feature ID**: market-daily-digest
> **Plan Reference**: `docs/01-plan/features/market-daily-digest.plan.md`
> **Created**: 2026-02-20
> **Phase**: Design

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  dashboard/market_daily_digest.html (CDN React + D3.js)     │
│  ┌────────────────────────┬────────────────────────────┐    │
│  │  Force-Directed        │  Detail Panel              │    │
│  │  Mind Map (D3.js)      │  ┌──────────────────────┐  │    │
│  │                        │  │ Module Detail View    │  │    │
│  │  7 module nodes        │  │ (KPI + Data + Links)  │  │    │
│  │  + sub-indicator nodes │  └──────────────────────┘  │    │
│  │                        │  ┌──────────────────────┐  │    │
│  │                        │  │ AI Summary / Editor   │  │    │
│  │                        │  │ [Save] [AI Generate]  │  │    │
│  │                        │  └──────────────────────┘  │    │
│  └────────────────────────┴────────────────────────────┘    │
└───────────┬──────────┬──────────┬──────────────────────────┘
            │          │          │
   7 Module APIs    POST/GET    AI Analyze
            │      daily-digest   (proxy)
            ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Backend                                            │
│  ┌─────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │ Existing     │  │ daily_digest.py  │  │ AI Proxy      │  │
│  │ Module APIs  │  │ (Router+Service) │  │ (Claude/GPT)  │  │
│  └──────┬──────┘  └────────┬─────────┘  └───────┬───────┘  │
│         │                  │                     │          │
│         ▼                  ▼                     ▼          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  SQLite: DailyDigest table                           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. DB Model

### 2.1 DailyDigest

**File**: `backend/app/models/daily_digest.py`

```python
from sqlalchemy import Column, String, DateTime, Text, JSON, Float
from sqlalchemy.sql import func
from ..database import Base

class DailyDigest(Base):
    __tablename__ = "daily_digests"

    date = Column(String(10), primary_key=True, index=True)       # "2026-02-20"
    module_summaries = Column(JSON, nullable=True)                  # 7개 모듈 요약 스냅샷
    mindmap_data = Column(JSON, nullable=True)                      # 마인드맵 노드/링크 구조
    ai_summary = Column(Text, nullable=True)                        # AI 생성 총평
    user_summary = Column(Text, nullable=True)                      # 사용자 수정/추가 총평
    ai_model = Column(String(50), nullable=True)                    # 사용된 AI 모델명
    sentiment_score = Column(Float, nullable=True)                  # 시장 심리 점수 (-1.0~1.0)
    sentiment_label = Column(String(20), nullable=True)             # "Bullish"/"Bearish"/"Neutral"
    source = Column(String(20), default="REAL")                     # "DEMO" or "REAL"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 2.2 module_summaries JSON Schema

```json
{
  "disclosures": {
    "status": "ok",
    "total_count": 42,
    "key_items": ["삼성전자 임시주총 소집", "LG에너지 유상증자"],
    "sentiment": "neutral"
  },
  "news": {
    "status": "ok",
    "total_count": 156,
    "categories": {"Market": 45, "Tech": 32, "Crypto": 28, "Economy": 30, "World": 21},
    "top_issues": ["Fed 금리 동결 시사", "AI 반도체 수요 급증"]
  },
  "liquidity_stress": {
    "status": "ok",
    "stress_index": 42.5,
    "stress_label": "Moderate",
    "modules": {"credit": 55, "funding": 38, "treasury": 30, "equity_vol": 45, "news_sentiment": 50, "fed_tone": 35}
  },
  "crypto": {
    "status": "ok",
    "btc_price": 98500,
    "btc_change_24h": 2.3,
    "eth_price": 3420,
    "fear_greed": 72,
    "fear_greed_label": "Greed",
    "defi_tvl": 185000000000
  },
  "moat": {
    "status": "ok",
    "analyzed_count": 2534,
    "avg_moat_score": 3.2,
    "top_moat_stocks": ["005930", "000660", "035420"]
  },
  "intelligence": {
    "status": "ok",
    "active_signals": 5,
    "upcoming_events": 3,
    "key_insight": "유동성 완화 + AI 모멘텀 → 기술주 우선"
  },
  "blog": {
    "status": "ok",
    "post_count": 12,
    "key_themes": ["반도체 사이클 회복", "배당주 선호"]
  }
}
```

---

## 3. API Endpoints

### 3.1 Router: `backend/app/api/daily_digest.py`

**Prefix**: `/api/v1/daily-digest`

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| GET | `/{date}` | 특정 날짜 종합정리 조회 | path: date (YYYY-MM-DD) | `DailyDigestResponse` |
| POST | `/` | 종합정리 저장 (upsert) | body: `DailyDigestSaveRequest` | `{status, date}` |
| GET | `/history` | 저장 히스토리 목록 | query: limit(20) | `{dates: [...]}` |
| POST | `/ai-analyze` | AI 총평 생성 | body: `AIAnalyzeRequest` | `AIAnalyzeResponse` |

### 3.2 Request/Response Schemas

```python
# POST / — Save
class DailyDigestSaveRequest:
    date: str                    # "2026-02-20"
    module_summaries: dict       # 7개 모듈 요약
    ai_summary: str | None       # AI 총평
    user_summary: str | None     # 사용자 총평
    ai_model: str | None         # 모델명
    sentiment_score: float | None
    sentiment_label: str | None

# POST /ai-analyze — AI Analysis
class AIAnalyzeRequest:
    date: str
    module_summaries: dict       # 컨텍스트로 전달할 모듈 데이터
    model: str | None            # "claude-sonnet-4-5-20250929" 등

# Response
class AIAnalyzeResponse:
    status: str                  # "ok"
    summary: str                 # AI 생성 총평 텍스트 (markdown)
    sentiment_score: float
    sentiment_label: str
    model_used: str
```

---

## 4. Service Layer

### 4.1 `backend/app/services/daily_digest_service.py`

```python
class DailyDigestService:
    def __init__(self, db: Session):
        self.db = db

    async def get_digest(self, date: str) -> dict:
        """특정 날짜 종합정리 조회"""

    async def save_digest(self, data: dict) -> dict:
        """종합정리 upsert (date 기준)"""

    async def get_history(self, limit: int = 20) -> dict:
        """저장된 날짜 목록 (최신순)"""

    async def ai_analyze(self, date: str, module_summaries: dict, model: str = None) -> dict:
        """AI 총평 생성 — Claude/GPT/Gemini 프록시"""
```

### 4.2 AI Analyze 로직

```python
async def ai_analyze(self, date, module_summaries, model=None):
    # 1. 모델 결정 (기본: claude-sonnet-4-5-20250929)
    model = model or "claude-sonnet-4-5-20250929"

    # 2. 프롬프트 구성
    system_prompt = """당신은 한국 시장 전문 애널리스트입니다.
    아래 7개 시장 모니터링 모듈의 당일 데이터를 종합하여:
    1. 시장 전체 흐름 요약 (3줄)
    2. 핵심 인사이트 3~5개 (bullet)
    3. 리스크 요인 2~3개
    4. 총평 (투자 관점, 2~3문장)
    5. 시장 심리 평가 (Bullish/Neutral/Bearish + 점수 -1.0~1.0)
    마크다운 형식으로 작성하세요."""

    user_content = json.dumps(module_summaries, ensure_ascii=False, indent=2)

    # 3. AI API 호출 (anthropic / openai / google SDK)
    # 4. 응답 파싱 → summary, sentiment_score, sentiment_label 추출
    # 5. Return
```

### 4.3 AI 모델 설정

기존 `scripts/news_monitor/config.py`의 `AVAILABLE_MODELS` 패턴 재활용:

```python
AVAILABLE_MODELS = {
    "claude-sonnet-4-5-20250929": {"label": "Claude Sonnet 4.5", "tier": "recommended", "provider": "anthropic"},
    "gpt-4o": {"label": "GPT-4o", "tier": "premium", "provider": "openai"},
    "gemini-2.0-flash": {"label": "Gemini 2.0 Flash", "tier": "standard", "provider": "google"},
}
```

---

## 5. Frontend Design

### 5.1 Page: `dashboard/market_daily_digest.html`

**CDN Dependencies**:
```html
<script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
<script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script src="https://unpkg.com/lucide@latest"></script>
```

### 5.2 Page Layout Structure

```
┌─────────────────────────────────────────────────────────────────┐
│ HEADER: "시장 종합정리" title + date nav + AI model selector    │
│ [◀ Prev] [2026-02-20 (목)] [Next ▶]   [Model ▼] [AI 총평 생성] │
├──────────────────────────────────┬──────────────────────────────┤
│                                  │  DETAIL PANEL (right 40%)    │
│  MINDMAP AREA (left 60%)         │  ┌────────────────────────┐  │
│                                  │  │ Module Detail Tab      │  │
│  ┌─ D3.js SVG ───────────────┐  │  │ (노드 클릭 시 표시)     │  │
│  │                            │  │  │ - Module Name + Icon   │  │
│  │   [crypto]  [news]         │  │  │ - KPI Cards (2~4)     │  │
│  │      \       /             │  │  │ - Key Data List       │  │
│  │  [moat]─[CENTER]─[liquid]  │  │  │ - [원본 페이지 열기 →] │  │
│  │      /       \             │  │  └────────────────────────┘  │
│  │  [blog] [intel] [disc]     │  │  ┌────────────────────────┐  │
│  │                            │  │  │ Summary Tab            │  │
│  └────────────────────────────┘  │  │ [AI 총평 / 수동 총평]   │  │
│                                  │  │ - Markdown Rendered     │  │
│  [Zoom +/-] [Reset]             │  │ - Edit Mode Toggle      │  │
│                                  │  │ - [💾 저장] [📋 복사]   │  │
│                                  │  └────────────────────────┘  │
├──────────────────────────────────┴──────────────────────────────┤
│ FOOTER: 데이터 시각 + 히스토리 저장 목록 (날짜 chips)            │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Responsive (< 1024px)

좁은 화면에서는 상하 분할:
```
┌──────────────────────────┐
│ HEADER (날짜 + AI 선택)   │
├──────────────────────────┤
│ MINDMAP (상단 50vh)       │
├──────────────────────────┤
│ DETAIL PANEL (하단)       │
│ - Module Detail          │
│ - Summary                │
└──────────────────────────┘
```

### 5.4 Color Theme

| 요소 | 색상 | 용도 |
|------|------|------|
| Primary | `#eab308` (Gold) | 헤더 액센트, 중심 노드, 버튼 |
| Background | `#0f172a` | 페이지 배경 (기존 패턴 동일) |
| Card BG | `rgba(15,23,42,0.8)` | 패널 배경 |
| Border | `#334155` | 카드 테두리 |
| Hover | `#eab308` glow | 노드/버튼 hover |

### 5.5 Module Node Colors

| Module | Color | Icon |
|--------|-------|------|
| 중심 노드 | `#eab308` (Gold) | `activity` |
| 공시 | `#ef4444` (Red) | `file-text` |
| 뉴스 | `#f97316` (Orange) | `newspaper` |
| 유동성 | `#22c55e` (Green) | `trending-up` |
| 크립토 | `#a855f7` (Purple) | `bitcoin` |
| 해자 | `#3b82f6` (Blue) | `shield` |
| Intelligence | `#06b6d4` (Cyan) | `brain` |
| 블로그 | `#ec4899` (Pink) | `bookmark` |

---

## 6. D3.js Force-Directed Mind Map

### 6.1 Data Structure

```javascript
// nodes array
const nodes = [
  // Center
  { id: "center", label: "2026-02-20\n시장 종합", group: "center", radius: 45, color: "#eab308" },

  // Level 1: Modules
  { id: "disclosures", label: "공시", group: "module", radius: 30, color: "#ef4444",
    parent: "center", summary: { count: 42, key: "삼성전자 임시주총" } },
  { id: "news", label: "뉴스", group: "module", radius: 30, color: "#f97316",
    parent: "center", summary: { count: 156, key: "Fed 금리 동결 시사" } },
  // ... 5 more modules

  // Level 2: Sub-indicators (per module)
  { id: "news_market", label: "Market\n45건", group: "sub", radius: 16, color: "#f97316",
    parent: "news" },
  { id: "news_tech", label: "Tech\n32건", group: "sub", radius: 16, color: "#f97316",
    parent: "news" },
  // ... more sub-indicators
];

// links array
const links = [
  { source: "center", target: "disclosures" },
  { source: "center", target: "news" },
  // ... center → modules
  { source: "news", target: "news_market" },
  { source: "news", target: "news_tech" },
  // ... modules → sub-indicators
];
```

### 6.2 Force Simulation Config

```javascript
const simulation = d3.forceSimulation(nodes)
  .force("link", d3.forceLink(links).id(d => d.id)
    .distance(d => {
      if (d.source.group === "center") return 150;  // center → module
      return 80;                                       // module → sub
    })
    .strength(0.8))
  .force("charge", d3.forceManyBody()
    .strength(d => d.group === "center" ? -500 : d.group === "module" ? -300 : -100))
  .force("center", d3.forceCenter(width / 2, height / 2))
  .force("collision", d3.forceCollide()
    .radius(d => d.radius + 15)   // 노드 겹침 방지
    .strength(0.8))
  .alphaDecay(0.02)               // 안정화 속도
  .velocityDecay(0.4);            // 드래그 감쇠
```

### 6.3 Node Rendering

```javascript
// 각 노드: circle + text
const nodeGroup = svg.selectAll(".node")
  .data(nodes)
  .join("g")
  .attr("class", "node")
  .call(drag(simulation));

// Circle
nodeGroup.append("circle")
  .attr("r", d => d.radius)
  .attr("fill", d => d.color + "33")       // 20% opacity fill
  .attr("stroke", d => d.color)
  .attr("stroke-width", d => d.group === "center" ? 3 : 2);

// Label
nodeGroup.append("text")
  .text(d => d.label)
  .attr("text-anchor", "middle")
  .attr("fill", "#e2e8f0")
  .attr("font-size", d => d.group === "center" ? 14 : d.group === "module" ? 12 : 10);

// Hover tooltip
nodeGroup.on("mouseenter", showTooltip)
         .on("mouseleave", hideTooltip);

// Click → update detail panel
nodeGroup.on("click", (event, d) => {
  if (d.group === "module" || d.group === "center") {
    setSelectedModule(d.id);              // React state update
  }
});

// Double-click → open module page
nodeGroup.on("dblclick", (event, d) => {
  const urls = { disclosures: "monitor_disclosures.html", news: "news_intelligence.html", ... };
  if (urls[d.id]) window.open(urls[d.id], "_blank");
});
```

### 6.4 Drag Behavior

```javascript
function drag(simulation) {
  return d3.drag()
    .on("start", (event, d) => {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x; d.fy = d.y;
    })
    .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
    .on("end", (event, d) => {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null; d.fy = null;    // 놓으면 자유 이동
    });
}
```

### 6.5 Zoom & Pan

```javascript
const zoom = d3.zoom()
  .scaleExtent([0.3, 3])
  .on("zoom", (event) => container.attr("transform", event.transform));
svg.call(zoom);

// Reset 버튼
function resetZoom() {
  svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity);
}
```

---

## 7. React Component Structure

```
MarketDailyDigest (root)
├── Header
│   ├── DateNavigator         — [◀] date [▶] + date picker
│   ├── ModelSelector         — AI model dropdown
│   └── AnalyzeButton         — AI 총평 생성 버튼
├── SplitLayout
│   ├── MindMapPanel (left 60%)
│   │   ├── D3ForceGraph      — SVG force-directed 마인드맵
│   │   └── ZoomControls      — [+] [-] [Reset]
│   └── DetailPanel (right 40%)
│       ├── TabBar             — [모듈 상세] [총평]
│       ├── ModuleDetailView   — 선택된 모듈 KPI + 데이터
│       │   ├── ModuleHeader   — icon + name + status badge
│       │   ├── KPICards       — 핵심 지표 카드 (2~4개)
│       │   ├── DataList       — 상세 데이터 목록
│       │   └── OriginalLink   — 원본 페이지 바로가기
│       └── SummaryView        — AI 총평 + 사용자 총평
│           ├── MarkdownRender — 총평 텍스트 렌더링
│           ├── EditToggle     — 보기/편집 모드 전환
│           ├── TextEditor     — textarea (편집 모드)
│           └── ActionButtons  — [💾 저장] [📋 복사]
└── Footer
    ├── DataTimestamp          — "마지막 업데이트: 14:30"
    └── HistoryChips           — 저장된 날짜 chip 목록
```

---

## 8. Data Flow

### 8.1 Page Load Sequence

```
1. Load date (default: today)
2. Fetch saved digest → GET /api/v1/daily-digest/{date}
   ├── If exists → populate mindmap + summary from saved data
   └── If 404 → fetch live data from 7 module APIs
3. Fetch 7 module APIs (parallel)
   ├── Promise.allSettled([
   │   fetch("/api/v1/disclosures?date=..."),
   │   fetch("/api/v1/news-intel/articles?date=..."),
   │   fetch("/api/v1/liquidity-stress/current"),
   │   fetchCryptoExternal(),                          // CoinGecko 등 직접
   │   fetch("/api/v1/moat/summary"),
   │   fetch("/api/v1/cross-module/context"),
   │   fetch("/api/v1/blog-review/posts?date=..."),
   │ ])
   └── Map responses → module_summaries + mindmap nodes
4. Render Force-Directed Mind Map
5. Fetch AI models → GET /api/v1/daily-digest/models
6. Display saved summary (if any) or placeholder
```

### 8.2 AI Analyze Flow

```
1. User clicks "AI 총평 생성"
2. Confirm dialog: "AI 총평을 생성하시겠습니까?"
3. POST /api/v1/daily-digest/ai-analyze
   body: { date, module_summaries, model }
4. Backend calls AI API (Claude/GPT/Gemini)
5. Response → display in SummaryView (markdown)
6. User reviews + optionally edits
7. User clicks "저장" → POST /api/v1/daily-digest
```

### 8.3 Manual Save Flow

```
1. User edits summary in textarea
2. User clicks "💾 저장"
3. POST /api/v1/daily-digest
   body: { date, module_summaries, ai_summary, user_summary, ai_model, ... }
4. Backend upsert (date PK)
5. Toast: "저장 완료"
6. HistoryChips 갱신
```

---

## 9. Module Data Mapper

각 모듈 API 응답을 마인드맵 노드로 변환하는 매퍼 함수:

```javascript
const MODULE_CONFIG = {
  disclosures: {
    label: "공시",
    color: "#ef4444",
    icon: "file-text",
    url: "monitor_disclosures.html",
    apiUrl: "/api/v1/disclosures",
    mapToNodes: (data) => ({
      summary: { count: data.total || 0, key: data.items?.[0]?.title || "데이터 없음" },
      children: [
        { id: "disc_count", label: `${data.total || 0}건`, value: data.total },
        { id: "disc_key", label: data.items?.[0]?.title?.slice(0, 15) || "-" },
      ]
    })
  },
  news: {
    label: "뉴스",
    color: "#f97316",
    icon: "newspaper",
    url: "news_intelligence.html",
    apiUrl: "/api/v1/news-intel/articles",
    mapToNodes: (data) => ({
      summary: { count: data.total || 0, key: data.articles?.[0]?.title || "데이터 없음" },
      children: Object.entries(data.by_category || {}).map(([cat, cnt]) => ({
        id: `news_${cat.toLowerCase()}`, label: `${cat}\n${cnt}건`, value: cnt
      }))
    })
  },
  liquidity_stress: {
    label: "유동성",
    color: "#22c55e",
    icon: "trending-up",
    url: "liquidity_stress.html",
    apiUrl: "/api/v1/liquidity-stress/current",
    mapToNodes: (data) => ({
      summary: { stress_index: data.stress_index, label: data.stress_label },
      children: Object.entries(data.modules || {}).map(([mod, score]) => ({
        id: `liq_${mod}`, label: `${mod}\n${score}`, value: score
      }))
    })
  },
  crypto: {
    label: "크립토",
    color: "#a855f7",
    icon: "bitcoin",
    url: "crypto_trends.html",
    apiUrl: null,  // external API (CoinGecko)
    mapToNodes: (data) => ({
      summary: { btc: data.btc_price, fear_greed: data.fear_greed },
      children: [
        { id: "crypto_btc", label: `BTC\n$${(data.btc_price/1000).toFixed(1)}k`, value: data.btc_price },
        { id: "crypto_eth", label: `ETH\n$${data.eth_price}`, value: data.eth_price },
        { id: "crypto_fg", label: `F&G\n${data.fear_greed}`, value: data.fear_greed },
      ]
    })
  },
  moat: {
    label: "해자",
    color: "#3b82f6",
    icon: "shield",
    url: "moat_analysis.html",
    apiUrl: "/api/v1/moat/summary",
    mapToNodes: (data) => ({
      summary: { count: data.analyzed_count, avg: data.avg_moat_score },
      children: [
        { id: "moat_count", label: `${data.analyzed_count}종목`, value: data.analyzed_count },
        { id: "moat_avg", label: `평균 ${data.avg_moat_score}/5`, value: data.avg_moat_score },
      ]
    })
  },
  intelligence: {
    label: "Intelligence",
    color: "#06b6d4",
    icon: "brain",
    url: "idea_board.html",
    apiUrl: "/api/v1/cross-module/context",
    mapToNodes: (data) => ({
      summary: { signals: data.active_signals, events: data.upcoming_events },
      children: [
        { id: "intel_signals", label: `시그널\n${data.active_signals || 0}`, value: data.active_signals },
        { id: "intel_events", label: `이벤트\n${data.upcoming_events || 0}`, value: data.upcoming_events },
      ]
    })
  },
  blog: {
    label: "블로그",
    color: "#ec4899",
    icon: "bookmark",
    url: "blog_review.html",
    apiUrl: "/api/v1/blog-review/posts",
    mapToNodes: (data) => ({
      summary: { count: data.total || 0, key: data.posts?.[0]?.title || "데이터 없음" },
      children: [
        { id: "blog_count", label: `${data.total || 0}건`, value: data.total },
      ]
    })
  },
};
```

---

## 10. Error Handling

| Scenario | Handling |
|----------|----------|
| 모듈 API 실패 | `Promise.allSettled` — 실패 모듈은 `status: "error"` + 노드 회색 처리 + "데이터 없음" 텍스트 |
| AI API 키 미설정 | "AI 총평 생성" 버튼 비활성 + tooltip "Backend에 API 키를 설정하세요" |
| AI API 호출 실패 | 에러 토스트 + 수동 편집으로 fallback |
| 저장 실패 | 에러 토스트 + retry 안내 |
| 날짜 데이터 없음 | "이 날짜의 데이터가 없습니다" placeholder + 모듈 API 호출 시도 |

---

## 11. Dashboard Link

### `dashboard/index.html` 시장모니터링 섹션 추가

```html
<!-- 8번째 항목: 종합정리 -->
<a href="market_daily_digest.html" className="monitoring-link">
    <span className="monitoring-name">종합정리</span>
    <span className="monitoring-desc">전체 시장흐름 마인드맵 + AI 총평</span>
</a>
```

**위치**: 시장모니터링 카드의 **최상단** (가장 중요한 종합 뷰이므로)

---

## 12. Seed Data (DEMO)

`scripts/daily_digest/seed_data.py`:

```python
seed = DailyDigest(
    date="2026-02-20",
    module_summaries={...},            # 7개 모듈 예시 데이터
    ai_summary="## 시장 종합 총평\n...",
    user_summary=None,
    ai_model="DEMO",
    sentiment_score=0.15,
    sentiment_label="Slightly Bullish",
    source="DEMO",                      # MANDATORY
)
```

---

## 13. Implementation Checklist

### Phase 1: Backend
- [ ] `backend/app/models/daily_digest.py` — DailyDigest 모델
- [ ] `backend/app/models/__init__.py` — import 추가
- [ ] `backend/app/services/daily_digest_service.py` — 4개 메서드
- [ ] `backend/app/api/daily_digest.py` — 4개 엔드포인트
- [ ] `backend/app/main.py` — 라우터 등록
- [ ] `scripts/daily_digest/seed_data.py` — DEMO 시드

### Phase 2: Frontend Layout
- [ ] `dashboard/market_daily_digest.html` — 기본 HTML/CSS
- [ ] Header: 날짜 네비게이션 + AI 모델 선택
- [ ] Split layout: 좌 60% / 우 40%
- [ ] Detail Panel: TabBar + ModuleDetail + Summary
- [ ] Footer: 히스토리 chips

### Phase 3: D3.js Mind Map
- [ ] Force simulation setup
- [ ] Node rendering (center + module + sub)
- [ ] Link rendering (curved lines)
- [ ] Drag behavior
- [ ] Click → detail panel 연동
- [ ] Double-click → 원본 페이지
- [ ] Hover tooltip
- [ ] Zoom & pan + reset

### Phase 4: AI + Save
- [ ] AI model list API 연동
- [ ] AI 총평 생성 버튼 + API 호출
- [ ] Summary 편집 모드 (view/edit toggle)
- [ ] 저장 버튼 + POST API 연동
- [ ] 히스토리 조회 + chip 네비게이션

### Phase 5: Polish
- [ ] `dashboard/index.html` 링크 추가 (최상단)
- [ ] Responsive layout (< 1024px)
- [ ] 로딩 프로그레스바 (7개 모듈 로딩 시)
- [ ] DEMO 배지 + 배너
- [ ] 에러 노드 회색 처리
