# Feature Design: Investment Intelligence Engine

> **Feature**: investment-intelligence-engine
> **Plan**: `docs/01-plan/features/investment-intelligence-engine.plan.md`
> **Predecessor**: idea-ai-collaboration (96.2%)

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Investment Intelligence Engine                       │
│                                                                       │
│  ┌── Layer 1: Cross-Data Signal Engine (규칙 기반) ───────────────┐  │
│  │                                                                 │  │
│  │  Data Sources (기존 모듈)                                       │  │
│  │  ┌───────────┐ ┌──────────┐ ┌───────────┐ ┌──────────┐        │  │
│  │  │ Liquidity │ │ Sector   │ │ Disclosure│ │ Crypto   │        │  │
│  │  │ Stress    │ │ Momentum │ │ Monitor   │ │ Trends   │        │  │
│  │  │ (DB)      │ │ (file)   │ │ (file)    │ │ (file)   │        │  │
│  │  └─────┬─────┘ └─────┬────┘ └─────┬─────┘ └─────┬────┘        │  │
│  │        │              │            │             │              │  │
│  │  ┌─────┴──┐ ┌────────┴─┐  ┌──────┴───┐  ┌─────┴────┐         │  │
│  │  │DailyWrk│ │ Ideas    │  │ Events   │  │ Custom   │         │  │
│  │  │(DB)    │ │ (DB)     │  │ (json)   │  │ Sources  │         │  │
│  │  └────┬───┘ └────┬─────┘  └────┬─────┘  └────┬─────┘         │  │
│  │       └───────────┴─────────────┴─────────────┘                │  │
│  │                         ↓                                       │  │
│  │              CrossModuleService.get_full_context()               │  │
│  │                         ↓                                       │  │
│  │              SignalDetectionEngine (signal_rules.json)           │  │
│  │                         ↓ matched signals                       │  │
│  │              signals DB table                                    │  │
│  └─────────────────────────┬───────────────────────────────────────┘  │
│                             ↓                                          │
│  ┌─────────────────────────┴───────────────────────────────────────┐  │
│  │  Layer 2: AI Strategist + Data Gap (LLM 기반)                    │  │
│  │                                                                   │  │
│  │  ┌──────────────────┐  ┌────────────────┐  ┌────────────────┐   │  │
│  │  │ StrategistService│  │ GapAnalyzer    │  │ SourceRecom-   │   │  │
│  │  │ Claude API       │  │ 부족 데이터 식별│  │ mender         │   │  │
│  │  │ → 투자 해석       │  │ → 갭 리스트     │  │ → 외부소스 추천 │   │  │
│  │  │ → 가설 제안       │  │                │  │ → 시너지 설명   │   │  │
│  │  └──────────────────┘  └────────────────┘  └────────────────┘   │  │
│  └─────────────────────────┬───────────────────────────────────────┘  │
│                             ↓                                          │
│  ┌─────────────────────────┴───────────────────────────────────────┐  │
│  │  Layer 3: Intelligence Dashboard                                  │  │
│  │  dashboard/idea_board.html (complete redesign)                    │  │
│  │                                                                   │  │
│  │  ┌──────────────┐  ┌─────────────────────────────────────────┐  │  │
│  │  │ Signal Feed  │  │ Detail Panel                             │  │  │
│  │  │ (좌측 35%)    │  │ (우측 65%)                               │  │  │
│  │  │              │  │ ┌─ 근거 데이터 ──────────────────────┐   │  │  │
│  │  │ ● HIGH       │  │ │ [모듈명] 수치 (날짜)              │   │  │  │
│  │  │ ● MED        │  │ └────────────────────────────────────┘   │  │  │
│  │  │ ● LOW        │  │ ┌─ AI 전략가 해석 ─────────────────┐   │  │  │
│  │  │              │  │ │ "유동성 스트레스가..."             │   │  │  │
│  │  │              │  │ └────────────────────────────────────┘   │  │  │
│  │  │ [filter]     │  │ ┌─ 데이터 갭 & 외부소스 추천 ──────┐   │  │  │
│  │  │ [sort]       │  │ │ ⚠ FRED 미연동 → +15% conf        │   │  │  │
│  │  │              │  │ └────────────────────────────────────┘   │  │  │
│  │  │              │  │ [✅ 채택] [✏ 수정] [❌ 거부]           │  │  │
│  │  └──────────────┘  └─────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Database Schema

### 2.1 signals (신규)

```sql
CREATE TABLE signals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id       VARCHAR(50) NOT NULL UNIQUE,  -- SIG-CASH-UP-20260215-001
    rule_id         VARCHAR(50) NOT NULL,          -- SIG-CASH-UP
    title           VARCHAR(200) NOT NULL,
    description     TEXT,
    category        VARCHAR(50) NOT NULL,          -- RISK, SECTOR, PORTFOLIO, THEME, ...
    signal_type     VARCHAR(20) DEFAULT 'cross',   -- cross(교차), single(단일), ai(AI생성)
    confidence      REAL DEFAULT 0.5,              -- 0.0 ~ 1.0
    data_sources    TEXT DEFAULT '[]',             -- JSON: ["liquidity_stress","sector_momentum"]
    evidence        TEXT DEFAULT '[]',             -- JSON: [{module,key,value,timestamp}]
    suggested_action TEXT,
    ai_interpretation TEXT,                         -- AI 전략가 해석 (Phase 2)
    data_gaps       TEXT DEFAULT '[]',             -- JSON: [{module,reason,recommended_source}]
    status          VARCHAR(20) DEFAULT 'new',     -- new, reviewed, accepted, rejected, expired
    related_idea_id INTEGER REFERENCES ideas(id) ON DELETE SET NULL,
    expires_at      DATETIME,                      -- 시그널 유효기간
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    reviewed_at     DATETIME
);
CREATE INDEX idx_signals_status ON signals(status);
CREATE INDEX idx_signals_category ON signals(category);
CREATE INDEX idx_signals_created ON signals(created_at);
```

### 2.2 기존 모델 — 변경 없음

| 모델 | 파일 | 역할 | 변경 |
|------|------|------|------|
| Idea | `backend/app/models/idea.py` | 시그널 → Idea 변환 대상 | 없음 |
| DailyWork | `backend/app/models/daily_work.py` | 데이터 소스 | 없음 |
| Insight | `backend/app/models/insight.py` | 데이터 소스 | 없음 |
| StressIndex | `backend/app/models/__init__.py` | 데이터 소스 | 없음 |
| LiquidityPrice | `backend/app/models/__init__.py` | 데이터 소스 | 없음 |
| CollabPacket | `backend/app/models/collab.py` | 데이터 소스 | 없음 |

---

## 3. Signal Detection Rules

### 3.1 Rules Schema (`data/signal_rules.json`)

```json
{
  "version": "1.0",
  "rules": [
    {
      "id": "SIG-CASH-UP",
      "title": "현금비중 확대 시그널",
      "description": "유동성 스트레스 상승 + 방어주 전환 감지 시 현금비중 확대 추천",
      "category": "RISK",
      "conditions": [
        {
          "module": "liquidity_stress",
          "field": "total_score",
          "operator": ">",
          "value": 65,
          "label": "유동성 스트레스"
        },
        {
          "module": "sector_momentum",
          "field": "defensive_trend",
          "operator": "==",
          "value": "up",
          "label": "방어주 모멘텀"
        }
      ],
      "min_conditions": 2,
      "confidence_base": 0.7,
      "confidence_boost_per_extra": 0.1,
      "suggested_action": "현금비중 확대 검토 (20%→30%)",
      "expires_hours": 72
    },
    {
      "id": "SIG-SECTOR-ROT",
      "title": "섹터 로테이션 전환",
      "description": "섹터 모멘텀 전환 + 일일작업 SECTOR 데이터 존재 시",
      "category": "SECTOR",
      "conditions": [
        {
          "module": "sector_momentum",
          "field": "rotation_signal",
          "operator": "!=",
          "value": null,
          "label": "섹터 로테이션"
        },
        {
          "module": "daily_work",
          "field": "has_recent",
          "operator": "==",
          "value": true,
          "category_filter": "SECTOR",
          "label": "SECTOR 분석 데이터"
        }
      ],
      "min_conditions": 2,
      "confidence_base": 0.6,
      "confidence_boost_per_extra": 0.1,
      "suggested_action": "포트폴리오 섹터 비중 재조정 검토",
      "expires_hours": 48
    },
    {
      "id": "SIG-CRYPTO-DIVERGE",
      "title": "크립토-전통시장 디커플링",
      "description": "크립토 상승 + 전통시장 스트레스 동시 발생",
      "category": "PORTFOLIO",
      "conditions": [
        {
          "module": "crypto_trends",
          "field": "btc_7d_change",
          "operator": ">",
          "value": 5,
          "label": "BTC 7일 상승률"
        },
        {
          "module": "liquidity_stress",
          "field": "total_score",
          "operator": ">",
          "value": 55,
          "label": "전통시장 스트레스"
        }
      ],
      "min_conditions": 2,
      "confidence_base": 0.5,
      "confidence_boost_per_extra": 0.1,
      "suggested_action": "크립토 비중 유지/확대 vs 전통자산 축소 평가",
      "expires_hours": 48
    },
    {
      "id": "SIG-DISCLOSURE-RISK",
      "title": "보유종목 공시 리스크",
      "description": "최근 공시에서 리스크 키워드 감지 + 해당 종목 보유",
      "category": "PORTFOLIO",
      "conditions": [
        {
          "module": "disclosures",
          "field": "risk_count",
          "operator": ">",
          "value": 0,
          "label": "리스크 공시"
        },
        {
          "module": "ideas_status",
          "field": "active_portfolio_ideas",
          "operator": ">",
          "value": 0,
          "label": "활성 포트폴리오 아이디어"
        }
      ],
      "min_conditions": 2,
      "confidence_base": 0.65,
      "confidence_boost_per_extra": 0.15,
      "suggested_action": "관련 종목 리스크 재평가 및 비중 조정 검토",
      "expires_hours": 24
    },
    {
      "id": "SIG-THEME-ACCEL",
      "title": "테마 가속 시그널",
      "description": "일일작업 THEME + 섹터 모멘텀 특정 ETF 상승 동시",
      "category": "THEME",
      "conditions": [
        {
          "module": "daily_work",
          "field": "has_recent",
          "operator": "==",
          "value": true,
          "category_filter": "THEME",
          "label": "THEME 분석 데이터"
        },
        {
          "module": "sector_momentum",
          "field": "top_performer_pct",
          "operator": ">",
          "value": 3,
          "label": "섹터 ETF 강세"
        }
      ],
      "min_conditions": 2,
      "confidence_base": 0.55,
      "confidence_boost_per_extra": 0.1,
      "suggested_action": "해당 테마 관련 종목 추가 매수 검토",
      "expires_hours": 48
    }
  ]
}
```

### 3.2 Module Data Extractors

SignalDetectionEngine이 CrossModuleService의 데이터를 규칙 엔진이 이해하는 flat key-value로 변환:

```python
MODULE_EXTRACTORS = {
    "liquidity_stress": lambda ctx: {
        "total_score": ctx.get("liquidity_stress", {}).get("latest_score"),
        "level": ctx.get("liquidity_stress", {}).get("level"),
        "vix": ctx.get("liquidity_stress", {}).get("vix"),
        "change_1d": ctx.get("liquidity_stress", {}).get("score_change"),
    },
    "sector_momentum": lambda ctx: {
        "defensive_trend": _calc_defensive_trend(ctx.get("sector_momentum", {})),
        "rotation_signal": _calc_rotation(ctx.get("sector_momentum", {})),
        "top_performer_pct": _calc_top_pct(ctx.get("sector_momentum", {})),
    },
    "daily_work": lambda ctx: {
        "has_recent": len(ctx.get("daily_work", {}).get("recent", [])) > 0,
        "categories": [w["category"] for w in ctx.get("daily_work", {}).get("recent", [])],
        "count": ctx.get("daily_work", {}).get("total_count", 0),
    },
    "crypto_trends": lambda ctx: {
        "btc_7d_change": ctx.get("crypto_trends", {}).get("btc_7d_change"),
        "fear_greed": ctx.get("crypto_trends", {}).get("fear_greed_value"),
    },
    "disclosures": lambda ctx: {
        "risk_count": ctx.get("disclosures", {}).get("risk_disclosure_count", 0),
        "total_count": ctx.get("disclosures", {}).get("total_count", 0),
    },
    "ideas_status": lambda ctx: {
        "active_portfolio_ideas": _count_portfolio_ideas(ctx.get("ideas_status", {})),
        "active_count": ctx.get("ideas_status", {}).get("active_count", 0),
    },
    "events": lambda ctx: {
        "upcoming_high_impact": _count_high_impact(ctx.get("events", {})),
        "next_event_days": _days_to_next(ctx.get("events", {})),
    },
}
```

---

## 4. Backend Services

### 4.1 SignalDetectionEngine (`backend/app/services/signal_service.py`)

```python
class SignalDetectionEngine:
    """규칙 기반 시그널 탐지 엔진"""

    def __init__(self, db: Session):
        self.db = db
        self.rules = self._load_rules()
        self.cross_module = CrossModuleService(db)

    def _load_rules(self) -> list:
        """data/signal_rules.json 로드"""
        ...

    def generate_signals(self, days: int = 3) -> list[dict]:
        """
        1) CrossModuleService에서 전체 컨텍스트 수집
        2) MODULE_EXTRACTORS로 flat data 변환
        3) 각 규칙의 conditions 평가
        4) min_conditions 이상 매치되면 Signal 생성
        5) DB 저장 + 결과 반환
        """
        context = self.cross_module.get_full_context(days)
        extracted = self._extract_module_data(context)
        signals = []

        for rule in self.rules:
            matched_conditions = []
            evidence_items = []

            for cond in rule["conditions"]:
                module_data = extracted.get(cond["module"], {})
                if self._evaluate_condition(cond, module_data):
                    matched_conditions.append(cond)
                    evidence_items.append({
                        "module": cond["module"],
                        "field": cond["field"],
                        "value": module_data.get(cond["field"]),
                        "label": cond["label"],
                        "timestamp": context.get("generated_at"),
                    })

            if len(matched_conditions) >= rule["min_conditions"]:
                confidence = min(1.0,
                    rule["confidence_base"]
                    + (len(matched_conditions) - rule["min_conditions"])
                    * rule.get("confidence_boost_per_extra", 0.1)
                )
                signal = self._create_signal(rule, confidence, evidence_items)
                signals.append(signal)

        return signals

    def _evaluate_condition(self, cond: dict, module_data: dict) -> bool:
        """단일 조건 평가 (>, <, ==, !=, in, contains)"""
        value = module_data.get(cond["field"])
        if value is None:
            return False
        op = cond["operator"]
        target = cond["value"]
        if op == ">": return value > target
        if op == "<": return value < target
        if op == "==": return value == target
        if op == "!=": return value != target
        if op == ">=": return value >= target
        if op == "in": return value in target
        return False

    def _create_signal(self, rule, confidence, evidence) -> dict:
        """Signal 레코드 생성 + DB 저장"""
        ...
```

### 4.2 StrategistService (`backend/app/services/strategist_service.py`)

```python
class StrategistService:
    """AI 투자전략가: 시그널을 투자 관점으로 해석"""

    def __init__(self, api_key: str = None):
        self.client = None
        if api_key:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)

    def interpret_signal(self, signal: dict, context: dict) -> dict:
        """
        시그널 + 컨텍스트 → AI 투자 해석
        Returns: {interpretation, hypothesis, actions[], risk_factors[]}
        """
        if not self.client:
            return {"interpretation": None, "reason": "API key not configured"}

        prompt = f"""당신은 한국 주식시장 전문 투자전략가입니다.

다음 투자 시그널을 분석하고 투자 관점에서 해석해주세요.

## 시그널
- 제목: {signal['title']}
- 카테고리: {signal['category']}
- 신뢰도: {signal['confidence']:.0%}
- 근거 데이터: {json.dumps(signal['evidence'], ensure_ascii=False)}
- 제안 행동: {signal['suggested_action']}

## 현재 시장 컨텍스트 요약
{self._summarize_context(context)}

다음 형식으로 JSON 응답해주세요:
{{
  "interpretation": "시그널의 투자적 의미 해석 (2-3문장)",
  "hypothesis": "이 시그널이 맞다면 예상되는 시장 시나리오",
  "actions": ["구체적 행동 1", "구체적 행동 2"],
  "risk_factors": ["리스크 1", "리스크 2"],
  "confidence_adjustment": 0.0  // -0.2 ~ +0.2 범위로 AI가 confidence 조정
}}"""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return self._parse_response(response)
```

### 4.3 GapAnalyzer (`backend/app/services/gap_analyzer.py`)

```python
class GapAnalyzer:
    """데이터 갭 분석 + 외부 소스 추천"""

    def __init__(self):
        self.external_sources = self._load_external_sources()

    def _load_external_sources(self) -> list:
        """data/external_sources.json 로드"""
        ...

    def analyze(self, signal: dict, context: dict) -> dict:
        """
        Returns: {
            gaps: [{module, reason, impact, staleness_hours}],
            recommendations: [{source_id, name, synergy, confidence_boost, integration}]
        }
        """
        gaps = []
        recommendations = []

        # 1) 시그널 조건 중 데이터 없는/오래된 모듈 탐지
        for evidence in signal.get("evidence", []):
            module = evidence["module"]
            module_data = context.get(module, {})

            if not module_data or module_data.get("available") is False:
                gaps.append({
                    "module": module,
                    "reason": f"{module} 데이터 없음",
                    "impact": "시그널 신뢰도 저하",
                    "staleness_hours": None,
                })
            elif ts := module_data.get("last_updated"):
                hours_old = self._hours_since(ts)
                if hours_old > 24:
                    gaps.append({
                        "module": module,
                        "reason": f"{module} 데이터 {hours_old:.0f}시간 경과",
                        "impact": "최신 상황 미반영 가능",
                        "staleness_hours": hours_old,
                    })

        # 2) 시그널 카테고리에 맞는 외부 소스 추천
        for source in self.external_sources:
            if source["category"] == signal["category"] or source["category"] == "ALL":
                is_connected = self._check_integration(source)
                if not is_connected:
                    recommendations.append({
                        "source_id": source["id"],
                        "name": source["name"],
                        "synergy": source["synergy"],
                        "confidence_boost": source.get("confidence_boost", "+10%"),
                        "integration": source.get("integration", "manual"),
                        "url": source.get("url"),
                    })

        # 3) 시그널을 강화할 추가 데이터 소스 (연동 여부 무관)
        enrichments = self._find_enrichment_sources(signal, context)

        return {
            "gaps": gaps,
            "recommendations": recommendations,
            "enrichments": enrichments,
        }
```

---

## 5. API Design

### 5.1 Signal API (`backend/app/api/signals.py`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/signals/generate` | 시그널 생성 실행 (규칙 엔진 트리거) |
| GET | `/api/v1/signals` | 시그널 목록 (필터: status, category, min_confidence) |
| GET | `/api/v1/signals/{id}` | 시그널 상세 (근거+AI해석+갭 포함) |
| PUT | `/api/v1/signals/{id}/status` | 시그널 상태 변경 (reviewed/accepted/rejected) |
| POST | `/api/v1/signals/{id}/interpret` | AI 전략가 해석 요청 (Phase 2) |
| GET | `/api/v1/signals/{id}/gaps` | 데이터 갭 분석 (Phase 2) |
| POST | `/api/v1/signals/{id}/accept` | 시그널 채택 → Idea 자동 생성 |

### 5.2 Request/Response Examples

**POST `/api/v1/signals/generate`**
```json
// Request
{ "days": 3 }

// Response
{
  "generated_at": "2026-02-15T10:00:00Z",
  "signals_count": 3,
  "signals": [
    {
      "id": 1,
      "signal_id": "SIG-CASH-UP-20260215-001",
      "title": "현금비중 확대 시그널",
      "category": "RISK",
      "confidence": 0.8,
      "status": "new",
      "data_sources": ["liquidity_stress", "sector_momentum"],
      "evidence": [
        {"module": "liquidity_stress", "field": "total_score", "value": 72, "label": "유동성 스트레스"},
        {"module": "sector_momentum", "field": "defensive_trend", "value": "up", "label": "방어주 모멘텀"}
      ],
      "suggested_action": "현금비중 확대 검토 (20%→30%)"
    }
  ]
}
```

**POST `/api/v1/signals/{id}/accept`**
```json
// Response
{
  "signal_id": "SIG-CASH-UP-20260215-001",
  "status": "accepted",
  "idea": {
    "id": 15,
    "title": "현금비중 확대 — 유동성 스트레스 72 + 방어주 전환",
    "category": "RISK",
    "status": "draft",
    "source": "Signal:SIG-CASH-UP-20260215-001"
  }
}
```

---

## 6. External Source Registry

### 6.1 파일 위치

```
data/external_sources.json
```

### 6.2 Schema

```json
{
  "version": "1.0",
  "sources": [
    {
      "id": "fred-credit-spread",
      "name": "FRED 신용스프레드 (BAA-AAA)",
      "category": "RISK",
      "url": "https://fred.stlouisfed.org/series/BAMLC0A0CM",
      "data_type": "time_series",
      "update_frequency": "daily",
      "api_required": "FRED_API_KEY",
      "integration_script": "scripts/liquidity_monitor/fred_fetch.py",
      "connected": false,
      "synergy": "유동성 스트레스 모듈과 결합 시 신용 리스크 조기 감지, confidence +15%",
      "confidence_boost": "+15%"
    },
    {
      "id": "yahoo-vix",
      "name": "CBOE VIX Index",
      "category": "RISK",
      "url": "https://finance.yahoo.com/quote/%5EVIX",
      "data_type": "real_time",
      "update_frequency": "intraday",
      "api_required": null,
      "integration_script": "scripts/liquidity_monitor/price_fetch.py",
      "connected": true,
      "synergy": "VIX 급등 + 섹터 방어주 전환 = 현금비중 확대 강력 시그널"
    },
    {
      "id": "dart-disclosure",
      "name": "DART 전자공시",
      "category": "PORTFOLIO",
      "url": "https://opendart.fss.or.kr",
      "data_type": "event",
      "update_frequency": "real_time",
      "api_required": "DART_API_KEY",
      "integration_script": "scripts/collect_disclosures.py",
      "connected": false,
      "synergy": "보유종목 공시 + 섹터 모멘텀 = 종목별 리스크/기회 조기 감지"
    },
    {
      "id": "google-news-kr",
      "name": "Google News (한국 금융)",
      "category": "ALL",
      "url": "https://news.google.com/topics/CAAqJQgKIh9DQkFTRVFvSUwyMHZNRFp0Y1RjU0JXdHZMVXRTSWdBUEFR",
      "data_type": "text",
      "update_frequency": "real_time",
      "api_required": null,
      "integration_script": "scripts/liquidity_monitor/news_fetch.py",
      "connected": true,
      "synergy": "뉴스 센티먼트 + 유동성 지표 = 시장 공포/탐욕 복합 분석"
    },
    {
      "id": "coingecko-market",
      "name": "CoinGecko 시장 데이터",
      "category": "PORTFOLIO",
      "url": "https://api.coingecko.com/api/v3",
      "data_type": "real_time",
      "update_frequency": "5min",
      "api_required": null,
      "integration_script": null,
      "connected": false,
      "synergy": "크립토 상세 데이터 + Fear&Greed = 크립토 비중 결정 정밀화"
    },
    {
      "id": "fed-calendar",
      "name": "연준 일정/발언",
      "category": "RISK",
      "url": "https://www.federalreserve.gov/newsevents.htm",
      "data_type": "event",
      "update_frequency": "weekly",
      "api_required": null,
      "integration_script": "scripts/liquidity_monitor/fed_speech_fetch.py",
      "connected": true,
      "synergy": "Fed 톤 변화 + 유동성 지표 = 금리/유동성 정책 전환 조기 감지"
    }
  ]
}
```

---

## 7. MCP Server Extension

### 7.1 신규 MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `generate_signals` | 시그널 생성 실행 | `days?` (default 3) |
| `get_signals` | 시그널 목록 조회 | `status?`, `category?`, `limit?` |
| `interpret_signal` | AI 전략가 해석 요청 | `signal_id` |
| `analyze_data_gaps` | 데이터 갭 분석 | `signal_id?` (없으면 전체) |
| `recommend_sources` | 외부 소스 추천 | `category?` |
| `accept_signal` | 시그널 채택 → Idea 변환 | `signal_id` |

### 7.2 MCP Resources (신규)

| URI | Description |
|-----|-------------|
| `collab://signals/latest` | 최근 시그널 5개 |
| `collab://gaps/summary` | 현재 데이터 갭 요약 |

---

## 8. Dashboard Redesign

### 8.1 idea_board.html 완전 재작성

| Component | 위치 | 설명 |
|-----------|------|------|
| Header | 상단 | "Intelligence Board" + 새로고침 + 필터 |
| SignalFeed | 좌측 35% | 시그널 카드 리스트 (confidence 게이지, 카테고리 배지) |
| DetailPanel | 우측 65% | 선택된 시그널 상세 (4 섹션) |
| DetailPanel.Evidence | 상단 | 근거 데이터 (모듈별 수치 + 타임스탬프) |
| DetailPanel.AI | 중단 | AI 전략가 해석 + 가설 + 행동 제안 |
| DetailPanel.Gaps | 하단 | 데이터 갭 + 외부소스 추천 (시너지 설명) |
| DetailPanel.Actions | 최하단 | [채택→Idea] [수정] [거부] 버튼 |

### 8.2 Signal Card Design

```
┌─────────────────────────────────────┐
│ 🔴 82%  현금비중 확대 시그널         │  ← confidence color + 제목
│ RISK   liquidity + sector           │  ← 카테고리 배지 + 소스 모듈
│ 현금비중 20%→30% 확대 검토          │  ← suggested_action
│ 2시간 전  ⚠ 데이터 갭 2건           │  ← 시간 + 갭 카운트
└─────────────────────────────────────┘
```

### 8.3 Confidence Color Scheme

| Range | Color | Label |
|-------|-------|-------|
| 0.8 ~ 1.0 | `#ef4444` (red) | HIGH |
| 0.6 ~ 0.79 | `#f59e0b` (amber) | MEDIUM |
| 0.4 ~ 0.59 | `#94a3b8` (gray) | LOW |
| 0.0 ~ 0.39 | `#64748b` (dark gray) | WEAK |

### 8.4 API Endpoints Used by Dashboard

```javascript
const API = 'http://localhost:8000';

// 1. 시그널 목록
fetch(`${API}/api/v1/signals?status=new,reviewed&min_confidence=0.4`)

// 2. 시그널 상세 (클릭 시)
fetch(`${API}/api/v1/signals/${signalId}`)

// 3. AI 해석 요청 (버튼 클릭)
fetch(`${API}/api/v1/signals/${signalId}/interpret`, { method: 'POST' })

// 4. 데이터 갭
fetch(`${API}/api/v1/signals/${signalId}/gaps`)

// 5. 시그널 채택
fetch(`${API}/api/v1/signals/${signalId}/accept`, { method: 'POST' })

// 6. 시그널 거부
fetch(`${API}/api/v1/signals/${signalId}/status`, {
  method: 'PUT',
  body: JSON.stringify({ status: 'rejected' })
})
```

---

## 9. Implementation Order (상세)

### Phase 1: Cross-Data Signal Engine (~3-5일)

| # | 작업 | 파일 | 의존성 |
|---|------|------|--------|
| 1-1 | Signal DB 모델 | `backend/app/models/signal.py` | - |
| 1-2 | models/__init__.py 등록 | `backend/app/models/__init__.py` | 1-1 |
| 1-3 | Signal Pydantic 스키마 | `backend/app/schemas/signal.py` | - |
| 1-4 | signal_rules.json (5개 규칙) | `data/signal_rules.json` | - |
| 1-5 | external_sources.json (6개 소스) | `data/external_sources.json` | - |
| 1-6 | SignalDetectionEngine 서비스 | `backend/app/services/signal_service.py` | 1-1, 1-4 |
| 1-7 | Signal API 라우터 (generate, list, detail, status) | `backend/app/api/signals.py` | 1-1, 1-3, 1-6 |
| 1-8 | main.py 라우터 등록 | `backend/app/main.py` | 1-7 |
| 1-9 | 시그널 생성 배치 스크립트 | `scripts/intelligence/generate_signals.py` | 1-6 |

### Phase 2: AI Strategist + Data Gap (~3-5일)

| # | 작업 | 파일 | 의존성 |
|---|------|------|--------|
| 2-1 | StrategistService | `backend/app/services/strategist_service.py` | Phase 1 |
| 2-2 | GapAnalyzer | `backend/app/services/gap_analyzer.py` | 1-5 |
| 2-3 | Signal API 확장 (interpret, gaps, accept) | `backend/app/api/signals.py` | 2-1, 2-2 |
| 2-4 | Signal→Idea 변환 로직 | `backend/app/services/signal_service.py` | 1-6 |
| 2-5 | MCP Server 확장 (6 tools + 2 resources) | `scripts/idea_pipeline/mcp_server.py` | 2-1, 2-2 |

### Phase 3: Intelligence Dashboard (~3-5일)

| # | 작업 | 파일 | 의존성 |
|---|------|------|--------|
| 3-1 | idea_board.html 완전 재작성 | `dashboard/idea_board.html` | Phase 1+2 |
| 3-2 | dashboard/index.html 링크 업데이트 | `dashboard/index.html` | 3-1 |

---

## 10. File Map

| 파일 | 상태 | 설명 |
|------|------|------|
| `backend/app/models/signal.py` | **신규** | Signal DB 모델 |
| `backend/app/models/__init__.py` | **수정** | Signal import 추가 |
| `backend/app/schemas/signal.py` | **신규** | Pydantic 스키마 |
| `backend/app/services/signal_service.py` | **신규** | 시그널 탐지 엔진 |
| `backend/app/services/strategist_service.py` | **신규** | AI 투자전략가 |
| `backend/app/services/gap_analyzer.py` | **신규** | 데이터 갭 분석 |
| `backend/app/api/signals.py` | **신규** | Signal API 라우터 |
| `backend/app/main.py` | **수정** | signals 라우터 등록 |
| `data/signal_rules.json` | **신규** | 시그널 탐지 규칙 5개 |
| `data/external_sources.json` | **신규** | 외부 데이터 소스 레지스트리 |
| `scripts/intelligence/generate_signals.py` | **신규** | 배치 시그널 생성 |
| `scripts/idea_pipeline/mcp_server.py` | **수정** | MCP 도구 6개 추가 |
| `dashboard/idea_board.html` | **재작성** | Intelligence Dashboard |
| `dashboard/index.html` | **수정** | 링크 텍스트 업데이트 |
