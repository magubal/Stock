# [Design] Stock Research Dashboard

> **Feature**: stock-research-dashboard
> **Phase**: Design
> **Created**: 2026-02-09
> **Plan Reference**: `docs/01-plan/features/stock-research-dashboard.plan.md`
> **Status**: In Progress

---

## 1. Component-to-API Mapping

### Overview

Each React component maps to specific backend API endpoints and database tables:

```
┌───────────────────────┐     ┌──────────────────────────┐     ┌──────────────────────┐
│   React Component     │     │   API Endpoint           │     │   Database Table      │
├───────────────────────┤     ├──────────────────────────┤     ├──────────────────────┤
│ PsychologyMetrics     │────▶│ GET /api/v1/psychology    │────▶│ investor_sentiment   │
│ TimingAnalysis        │────▶│ GET /api/v1/timing        │────▶│ investor_sentiment   │
│ PortfolioOverview     │────▶│ GET /api/v1/portfolio     │────▶│ market_data          │
│ CompanyEvaluation     │────▶│ GET /api/v1/evaluation    │────▶│ research_reports     │
│ ContextAnalyzer       │────▶│ GET /context-analysis/*   │────▶│ news + analysis      │
│ FlywheelStatus        │────▶│ GET /api/v1/flywheel      │────▶│ (new: flywheel_state)│
└───────────────────────┘     └──────────────────────────┘     └──────────────────────┘
```

---

## 2. API Endpoint Specifications

### 2.1 Psychology API (NEW)

**`GET /api/v1/psychology`**

Returns investor psychology metrics for the dashboard.

**Response Schema:**
```json
{
  "marketHeat": 35,
  "empathy": 72,
  "expectation": 58,
  "investorTypes": [
    {
      "type": "단기 투자자",
      "sentiment": "cautious",
      "label": "보수적"
    }
  ]
}
```

**Data Source:** `investor_sentiment` table
- `marketHeat` ← `market_heat` (latest record)
- `empathy` ← derived from `overall_score` + `fear_greed_index`
- `expectation` ← derived from `short_term_sentiment` + `long_term_sentiment`
- `investorTypes` ← derived from `ContextAnalyzer.predict_investor_behaviors()`

**Mapping Logic:**
```python
# investor_sentiment → PsychologyMetrics
marketHeat = latest_sentiment.market_heat * 100     # 0-1 → 0-100
empathy = (overall_score + 1) / 2 * 100             # -1~1 → 0-100
expectation = (short_term * 0.4 + long_term * 0.6 + 1) / 2 * 100

# investorTypes from ContextAnalyzer
investor_types = [
  { type: "단기 투자자",  sentiment: map_sentiment(short_term_sentiment) },
  { type: "중장기 투자자", sentiment: map_sentiment(long_term_sentiment) },
  { type: "보유자",       sentiment: map_sentiment(overall_score) },
  { type: "잠재 투자자",  sentiment: map_sentiment(fear_greed_index) }
]
```

---

### 2.2 Timing API (NEW)

**`GET /api/v1/timing`**

Returns investment timing analysis for 3/6/12 month periods.

**Response Schema:**
```json
[
  {
    "period": "3개월",
    "signal": "good",
    "label": "투자 적합",
    "reason": "기대요소 > 우려요소"
  }
]
```

**Data Source:** `investor_sentiment` + `market_data` tables
- Aggregates sentiment data over 3/6/12 month windows
- Compares positive vs negative sentiment trends
- References `investment-philosophy.md` timing criteria:
  - Is market sentiment NOT overheated?
  - Are concern factors significantly lower than expectation factors?
  - Is downside probability at its lowest?

**Mapping Logic:**
```python
# For each period (3m, 6m, 12m):
avg_sentiment = avg(investor_sentiment.overall_score) over period
avg_heat = avg(investor_sentiment.market_heat) over period
trend = calculate_trend(market_data.close_price) over period

signal = "good"    if avg_heat < 0.6 and avg_sentiment > 0
signal = "caution" if avg_heat >= 0.6 or avg_sentiment <= 0
signal = "danger"  if avg_heat >= 0.8 and avg_sentiment < -0.3
```

---

### 2.3 Portfolio API (NEW)

**`GET /api/v1/portfolio`**

Returns portfolio overview with holdings and alerts.

**Response Schema:**
```json
{
  "totalStocks": 12,
  "avgReturn": 24.8,
  "sellSignals": 3,
  "alerts": [
    {
      "type": "price-burden",
      "title": "가격부담 신호",
      "description": "2개 종목에서 감지됨"
    }
  ]
}
```

**Data Source:** `market_data` table + new `portfolio_holdings` table

**New Table Required: `portfolio_holdings`**
```python
class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(10), nullable=False)
    stock_name = Column(String(100), nullable=False)
    buy_price = Column(Float, nullable=False)
    buy_date = Column(DateTime(timezone=True), nullable=False)
    quantity = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**Alert Logic (from investment-philosophy.md):**
```python
# price-burden alert: RSI > 70 or price > MA60 * 1.3
# volatility alert: daily change > 3% for 3+ consecutive days
# sell signal: market_heat > 0.7 AND sentiment declining
```

---

### 2.4 Company Evaluation API (NEW)

**`GET /api/v1/evaluation`**

**Query Params:** `stock_code` (optional)

**Response Schema:**
```json
{
  "valueProposition": [
    { "checked": true, "label": "차별적 혜택 철학 보유" },
    { "checked": true, "label": "실질적 실행 증거 확인" },
    { "checked": false, "label": "경쟁력 상승 지속성" }
  ],
  "industryEvaluation": [
    { "name": "빅트렌드 부합도", "score": 85, "color": "positive" },
    { "name": "해자 요인", "score": 70, "color": "warning" },
    { "name": "성장 변수", "score": 60, "color": "warning" }
  ]
}
```

**Data Source:** `research_reports` table + analysis service

**Evaluation Criteria (from investment-philosophy.md):**
1. **고객가치제안 평가** (Customer Value Proposition):
   - 철학/미션: Does the company have a differentiated philosophy?
   - 실질적 행동: Are there concrete actions executing that philosophy?
   - 경쟁력 증거: Is there evidence of rising competitiveness?

2. **산업 평가** (Industry Evaluation):
   - 빅트렌드 부합도: Alignment with major trends
   - 해자요인: Moat factors (oligopoly, barriers to entry)
   - 성장 변수: Growth variables (fewer = less risk)

**Score Mapping:**
```python
color = "positive" if score >= 75
color = "warning"  if 50 <= score < 75
color = "danger"   if score < 50
```

---

### 2.5 Context Analysis API (EXISTS - extend)

**Existing endpoints to connect:**
- `GET /context-analysis/market-sentiment-summary`
- `GET /context-analysis/investor-behavior-analysis`
- `GET /context-analysis/recent-analyses`

**Response Mapping for ContextAnalyzer component:**
```json
{
  "flow": [
    { "icon": "Newspaper", "label": "뉴스/이슈" },
    { "icon": "Brain", "label": "투자심리" },
    { "icon": "Users", "label": "행동 예측" }
  ],
  "insights": [
    { "label": "최신 이슈", "value": "Fed 금리 동결" },
    { "label": "심리 영향", "value": "긍정적 (+68%)", "color": "positive" },
    { "label": "행동 가능성", "value": "매수 유도 (확률 72%)", "color": "positive" }
  ]
}
```

**Data Flow:**
```
GET /context-analysis/recent-analyses (limit=1)
  → latest analysis.title → insights[0].value (최신 이슈)
  → latest analysis.sentiment → insights[1].value (심리 영향)

GET /context-analysis/investor-behavior-analysis
  → top behavior.probability → insights[2].value (행동 가능성)
```

---

### 2.6 Flywheel API (NEW)

**`GET /api/v1/flywheel`**

Returns current flywheel execution status.

**Response Schema:**
```json
{
  "currentStep": 4,
  "totalSteps": 7,
  "currentPhase": "시나리오 작성 단계",
  "progress": [
    { "step": "데이터 수집", "status": "completed" },
    { "step": "맥락 분석", "status": "completed" },
    { "step": "중요도 평가", "status": "completed" },
    { "step": "시나리오 작성", "status": "current" },
    { "step": "실질 확인", "status": "pending" }
  ]
}
```

**New Table Required: `flywheel_state`**
```python
class FlywheelState(Base):
    __tablename__ = "flywheel_state"

    id = Column(Integer, primary_key=True)
    cycle_number = Column(Integer, nullable=False, default=1)
    current_step = Column(Integer, nullable=False, default=1)
    step_name = Column(String(100), nullable=False)
    status = Column(String(20), default="pending")  # pending, current, completed
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

---

## 3. Frontend Data Fetching Architecture

### 3.1 SWR Hook Pattern

```
frontend/src/
├── hooks/
│   ├── usePsychology.js      # SWR hook for psychology data
│   ├── useTiming.js           # SWR hook for timing data
│   ├── usePortfolio.js        # SWR hook for portfolio data
│   ├── useEvaluation.js       # SWR hook for evaluation data
│   ├── useContextAnalysis.js  # SWR hook for context analysis
│   └── useFlywheel.js         # SWR hook for flywheel status
├── lib/
│   └── fetcher.js             # Shared SWR fetcher with axios
└── components/
    └── Dashboard/
        ├── Dashboard.jsx      # Main dashboard (updated)
        └── Dashboard.css
```

### 3.2 SWR Fetcher Setup

```javascript
// lib/fetcher.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
});

export const fetcher = (url) => api.get(url).then(res => res.data);
```

### 3.3 Hook Implementation Pattern

```javascript
// hooks/usePsychology.js
import useSWR from 'swr';
import { fetcher } from '../lib/fetcher';

export function usePsychology() {
  const { data, error, isLoading, mutate } = useSWR(
    '/api/v1/psychology',
    fetcher,
    {
      refreshInterval: 60000,       // Refresh every 60 seconds
      revalidateOnFocus: true,
      dedupingInterval: 30000,
      errorRetryCount: 3
    }
  );

  return {
    psychology: data,
    isLoading,
    isError: error,
    refresh: mutate
  };
}
```

### 3.4 Dashboard Integration

```javascript
// Dashboard.jsx (updated data layer)
const Dashboard = () => {
  const { psychology, isLoading: psychLoading } = usePsychology();
  const { timing, isLoading: timingLoading } = useTiming();
  const { portfolio, isLoading: portfolioLoading } = usePortfolio();
  const { evaluation, isLoading: evalLoading } = useEvaluation();
  const { context, isLoading: contextLoading } = useContextAnalysis();
  const { flywheel, isLoading: flywheelLoading } = useFlywheel();

  // All 6 requests fire in parallel via SWR
  // SWR handles deduplication, caching, and revalidation

  return (
    <div className="dashboard">
      {/* Each card gets loading/error state */}
      <DashboardCard loading={psychLoading}>
        <PsychologyMetrics data={psychology} />
      </DashboardCard>
      {/* ... */}
    </div>
  );
};
```

---

## 4. Loading & Error States

### 4.1 Loading Component

```javascript
// components/shared/LoadingCard.jsx
const LoadingCard = () => (
  <div className="loading-spinner">
    <div className="spinner" />
  </div>
);
```

### 4.2 Error Boundary

```javascript
// components/shared/ErrorFallback.jsx
const ErrorFallback = ({ error, onRetry }) => (
  <div className="error-fallback">
    <AlertTriangle size={24} />
    <p>데이터를 불러올 수 없습니다</p>
    <button className="btn btn-secondary" onClick={onRetry}>
      다시 시도
    </button>
  </div>
);
```

### 4.3 DashboardCard Wrapper

```javascript
// components/shared/DashboardCard.jsx
const DashboardCard = ({ loading, error, onRetry, children, ...props }) => {
  if (loading) return <LoadingCard />;
  if (error) return <ErrorFallback error={error} onRetry={onRetry} />;
  return children;
};
```

---

## 5. Backend Implementation Order

### Step 1: Enable Existing API Routes

```python
# backend/app/main.py - uncomment and add routers
from .api import reports, news, context_analysis

app.include_router(news.router, prefix="/api/v1/news", tags=["News"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(context_analysis.router, tags=["Context Analysis"])
```

### Step 2: New Dashboard Router

```python
# backend/app/api/dashboard.py (NEW)
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/v1", tags=["Dashboard"])

@router.get("/psychology")
async def get_psychology(db: Session = Depends(get_db)):
    service = DashboardService(db)
    return await service.get_psychology_metrics()

@router.get("/timing")
async def get_timing(db: Session = Depends(get_db)):
    service = DashboardService(db)
    return await service.get_timing_analysis()

@router.get("/portfolio")
async def get_portfolio(db: Session = Depends(get_db)):
    service = DashboardService(db)
    return await service.get_portfolio_overview()

@router.get("/evaluation")
async def get_evaluation(
    stock_code: str = None,
    db: Session = Depends(get_db)
):
    service = DashboardService(db)
    return await service.get_company_evaluation(stock_code)

@router.get("/flywheel")
async def get_flywheel(db: Session = Depends(get_db)):
    service = DashboardService(db)
    return await service.get_flywheel_status()
```

### Step 3: Dashboard Service

```python
# backend/app/services/dashboard_service.py (NEW)
class DashboardService:
    def __init__(self, db_session):
        self.db = db_session
        self.context_analyzer = ContextAnalyzer()

    async def get_psychology_metrics(self) -> dict: ...
    async def get_timing_analysis(self) -> list: ...
    async def get_portfolio_overview(self) -> dict: ...
    async def get_company_evaluation(self, stock_code=None) -> dict: ...
    async def get_flywheel_status(self) -> dict: ...
```

### Step 4: New Database Models

Add `PortfolioHolding` and `FlywheelState` models (defined in Section 2).

### Step 5: Database Migration

```bash
cd backend
alembic revision --autogenerate -m "Add portfolio and flywheel tables"
alembic upgrade head
```

---

## 6. WebSocket Design (Phase 3)

### 6.1 Server-Side (FastAPI)

```python
# backend/app/api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            await connection.send_json(data)

manager = ConnectionManager()

@app.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle client messages (subscriptions, etc.)
    except WebSocketDisconnect:
        manager.active_connections.remove(websocket)
```

### 6.2 Event Types

| Event | Direction | Payload | Trigger |
|-------|-----------|---------|---------|
| `sentiment_update` | Server → Client | InvestorSentiment | New sentiment calculated |
| `news_alert` | Server → Client | News summary | High-importance news detected |
| `portfolio_alert` | Server → Client | Alert details | Sell signal or price burden |
| `flywheel_update` | Server → Client | FlywheelState | Step status changes |
| `market_data` | Server → Client | Price update | Every 30 seconds during market hours |

### 6.3 Client-Side Integration

```javascript
// hooks/useWebSocket.js
import { useEffect, useRef, useCallback } from 'react';

export function useDashboardSocket(onMessage) {
  const ws = useRef(null);

  useEffect(() => {
    ws.current = new WebSocket('ws://localhost:8000/ws/dashboard');

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    ws.current.onclose = () => {
      // Reconnect after 3 seconds
      setTimeout(() => {
        ws.current = new WebSocket('ws://localhost:8000/ws/dashboard');
      }, 3000);
    };

    return () => ws.current?.close();
  }, []);
}
```

---

## 7. State Management

### 7.1 Strategy

| Data Type | Management | Reason |
|-----------|-----------|--------|
| Server data (API) | SWR cache | Automatic revalidation, deduplication |
| Real-time updates | WebSocket + SWR mutate | Push updates trigger SWR cache refresh |
| UI state (filters, tabs) | React local state | Component-scoped, no sharing needed |
| Global state (user, theme) | Redux Toolkit | Cross-component shared state |

### 7.2 SWR + WebSocket Integration

```javascript
// When WebSocket receives update, invalidate SWR cache
useDashboardSocket((data) => {
  switch (data.type) {
    case 'sentiment_update':
      mutate('/api/v1/psychology');  // Triggers SWR refetch
      break;
    case 'portfolio_alert':
      mutate('/api/v1/portfolio');
      break;
  }
});
```

---

## 8. File Structure (New Files)

```
frontend/src/
├── hooks/                          # NEW
│   ├── usePsychology.js
│   ├── useTiming.js
│   ├── usePortfolio.js
│   ├── useEvaluation.js
│   ├── useContextAnalysis.js
│   ├── useFlywheel.js
│   └── useWebSocket.js
├── lib/                            # NEW
│   └── fetcher.js
├── components/
│   ├── shared/                     # NEW
│   │   ├── LoadingCard.jsx
│   │   ├── ErrorFallback.jsx
│   │   └── DashboardCard.jsx
│   └── Dashboard/
│       ├── Dashboard.jsx           # MODIFY (replace mock data with hooks)
│       └── Dashboard.css

backend/app/
├── api/
│   ├── dashboard.py                # NEW (psychology, timing, portfolio, etc.)
│   └── websocket.py                # NEW (Phase 3)
├── services/
│   └── dashboard_service.py        # NEW
├── models/
│   └── __init__.py                 # MODIFY (add PortfolioHolding, FlywheelState)
└── schemas/
    └── __init__.py                 # MODIFY (add dashboard response schemas)
```

---

## 9. Implementation Checklist

### Phase 2: API Integration

**Backend (in order):**
- [ ] 2.1: Add `PortfolioHolding` and `FlywheelState` models
- [ ] 2.2: Add dashboard Pydantic response schemas
- [ ] 2.3: Create `DashboardService` with 5 endpoint methods
- [ ] 2.4: Create `dashboard.py` API router
- [ ] 2.5: Enable all API routers in `main.py`
- [ ] 2.6: Run database migration (alembic)
- [ ] 2.7: Test all endpoints via `/docs`

**Frontend (in order):**
- [ ] 2.8: Install SWR (`npm install swr`)
- [ ] 2.9: Create `lib/fetcher.js`
- [ ] 2.10: Create 6 SWR hooks in `hooks/`
- [ ] 2.11: Create shared components (LoadingCard, ErrorFallback, DashboardCard)
- [ ] 2.12: Update `Dashboard.jsx` to use SWR hooks
- [ ] 2.13: Test full data flow (frontend → backend → database)

### Phase 3: Real-time Features
- [ ] 3.1: Create WebSocket connection manager
- [ ] 3.2: Add `/ws/dashboard` WebSocket endpoint
- [ ] 3.3: Create `useWebSocket` hook
- [ ] 3.4: Integrate WebSocket with SWR cache invalidation
- [ ] 3.5: Add reconnection logic

---

## 10. Error Handling Strategy

### Backend Error Responses

```python
# Standard error format
{
  "detail": "Error message",
  "error_code": "SENTIMENT_NOT_FOUND",
  "timestamp": "2026-02-09T12:00:00Z"
}
```

### HTTP Status Codes

| Code | Use Case |
|------|----------|
| 200 | Success |
| 404 | No data found for given parameters |
| 422 | Invalid query parameters |
| 500 | Internal server error |
| 503 | Database/Redis connection failure |

### Frontend Error Handling

```
API Error → SWR error state → ErrorFallback component → Retry button
                                                      → Show cached data if available
```

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 2026-02-09 | Claude Opus 4.6 | Initial design document created |
