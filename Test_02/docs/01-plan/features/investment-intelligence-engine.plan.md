# Feature Plan: Investment Intelligence Engine (투자 인텔리전스 엔진)

## 1. Overview
- **Feature Name**: investment-intelligence-engine
- **Level**: Enterprise (Multi-module orchestration + AI agent + Dashboard redesign)
- **Priority**: High
- **Estimated Scope**: Signal Engine + AI Strategist Agent + Data Gap Analyzer + Dashboard Redesign
- **Predecessor**: idea-ai-collaboration (Phase 2 Intelligence Layer 완료, 96.2% match)
- **Brainstorm Source**: `/brainstorm-bkit` 세션 2026-02-15

## 2. Background & Motivation

### 2.1 문제 인식

기존 `idea-ai-collaboration` 시스템은 **개발자 관점의 정보 관리 도구**로 구현되었다:
- DB CRUD, API 엔드포인트, 파이프라인 — 데이터를 **저장하고 조회**하는 도구
- 투자 전략가가 실제로 원하는 것: 데이터를 **조합하고 해석**하여 투자 기회를 **발견**하는 도구

### 2.2 핵심 갭

| 현재 (정보 관리) | 목표 (인텔리전스) |
|-----------------|------------------|
| 데이터 저장/조회 | 데이터 교차 분석 → 시그널 발견 |
| 수동 인사이트 등록 | AI가 자동으로 투자 가설 제안 |
| 단일 모듈 데이터 표시 | 모듈 간 시너지 탐지 |
| 기존 데이터만 활용 | 부족한 데이터 식별 + 외부 소스 추천 |
| 개발자용 그리드 UI | 투자 전략가의 의사결정 데스크 |

### 2.3 핵심 가치 제안

**"내 데이터들을 조합하면 어떤 투자 기회가 보이는가?"**

1. **Cross-Data Signal**: 유동성 + 섹터 + 공시 + 크립토 + 일일작업 데이터를 교차 분석하여 투자 시그널 자동 생성
2. **AI Strategist**: 시그널을 투자전략가 관점으로 해석하고 가설/행동을 제안
3. **Data Gap Awareness**: "이 결론을 강화하려면 X 데이터가 필요하다" → 외부 소스 추천 + 연동 시너지 설명
4. **Human-in-the-Loop**: 사용자가 AI 제안을 검토/수정/채택하는 반복 루프

## 3. Requirements

### 3.1 Functional Requirements

| ID | 요구사항 | 우선순위 | Phase |
|----|----------|----------|-------|
| FR-01 | Cross-Data Signal Generator: 기존 모듈 데이터 교차 분석 → 시그널 자동 생성 | Must | 1 |
| FR-02 | Signal 구조: type, title, description, data_sources[], confidence, evidence[], suggested_action | Must | 1 |
| FR-03 | Signal Detection Rules: 모듈 간 교차 조건 정의 (규칙 기반) | Must | 1 |
| FR-04 | `signals` DB 테이블: 생성된 시그널 저장 및 이력 관리 | Must | 1 |
| FR-05 | Signal API: GET /api/v1/signals (필터: type, confidence, date) | Must | 1 |
| FR-06 | AI Strategist Agent: 시그널을 받아 투자 관점 해석 + 가설 제안 (Claude API) | Must | 2 |
| FR-07 | Data Gap Analyzer: 분석 시 부족한 데이터 식별 | Must | 2 |
| FR-08 | External Source Recommender: 갭에 맞는 외부 데이터 소스 추천 + 시너지 설명 | Must | 2 |
| FR-09 | `data_gaps` DB 테이블: 식별된 데이터 갭 및 추천 소스 저장 | Should | 2 |
| FR-10 | External Source Registry: `data/external_sources.json` (FRED, Yahoo, DART, News 등) | Must | 2 |
| FR-11 | idea_board.html 대폭 리디자인: 투자 전략가 데스크 | Must | 3 |
| FR-12 | Signal Feed UI: 시간순 시그널 카드, confidence 게이지, 근거 데이터 링크 | Must | 3 |
| FR-13 | Hypothesis Card UI: AI 제안 가설 표시, 사용자 승인/수정/거부 버튼 | Should | 3 |
| FR-14 | Data Source Map UI: 어떤 모듈이 어떤 시그널에 기여했는지 시각화 | Should | 3 |
| FR-15 | Signal → Idea 자동 변환: 사용자 승인 시 시그널이 Idea로 등록 | Should | 2 |
| FR-16 | MCP Tool 확장: generate_signals(), analyze_gap(), recommend_sources() | Must | 2 |
| FR-17 | 외부 데이터 자동 수집 연동 (FRED, Yahoo 등 기존 수집기 활용) | Could | 3 |

### 3.2 Non-Functional Requirements

- 기존 인프라 최대 활용: CrossModuleService, MCP Server, FastAPI, SQLite
- LLM API 미설정 시에도 규칙 기반 시그널은 동작 (FR-01~05)
- 시그널 생성 시 반드시 근거 데이터 출처(evidence) 첨부 — 할루시네이션 방지
- Confidence scoring: 교차 모듈 수 × 데이터 신선도 × (AI 확신도)
- 모든 데이터 로컬 저장 유지
- 한국어 UI 우선

## 4. Technical Approach

### 4.1 Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                  Investment Intelligence Engine                    │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  Layer 1: Cross-Data Signal Generator (규칙 기반)           │   │
│  │                                                             │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │   │
│  │  │Liquidity │ │ Sector   │ │Disclosure│ │ Crypto   │ ...   │   │
│  │  │Stress    │ │Momentum  │ │Monitor   │ │Trends    │      │   │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │   │
│  │       └─────────────┴────────────┴────────────┘             │   │
│  │                      ↓ cross-check                          │   │
│  │              Signal Detection Rules                          │   │
│  │              ↓ matched signals                               │   │
│  │         signals DB table                                     │   │
│  └─────────────────────────┬──────────────────────────────────┘   │
│                             ↓                                      │
│  ┌─────────────────────────┴──────────────────────────────────┐   │
│  │  Layer 2: AI Strategist Agent (LLM 기반)                     │   │
│  │                                                             │   │
│  │  Signal → [Claude API] → 투자 해석 + 가설 + 행동 제안        │   │
│  │                                                             │   │
│  │  Data Gap Analyzer → 부족 데이터 식별                        │   │
│  │  External Source Recommender → 보완 소스 추천 + 시너지 설명   │   │
│  └─────────────────────────┬──────────────────────────────────┘   │
│                             ↓                                      │
│  ┌─────────────────────────┴──────────────────────────────────┐   │
│  │  Layer 3: Intelligence Dashboard (UI)                        │   │
│  │                                                             │   │
│  │  [Signal Feed] [Hypothesis Cards] [Data Source Map]          │   │
│  │  사용자: 승인 → Idea 등록 / 수정 → 재분석 / 거부 → 아카이브  │   │
│  └────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Signal Detection Rules (예시)

```python
SIGNAL_RULES = [
    {
        "id": "SIG-CASH-UP",
        "name": "현금비중 확대 시그널",
        "conditions": {
            "liquidity_stress": {"score": ">70"},  # 스트레스 높음
            "sector_momentum": {"defensive": "상승", "growth": "하락"},  # 방어주 전환
        },
        "min_modules": 2,  # 최소 2개 모듈 교차 확인
        "confidence_base": 0.7,
        "suggested_action": "현금비중 20%→30% 확대 검토",
        "category": "RISK"
    },
    {
        "id": "SIG-SECTOR-ROT",
        "name": "섹터 로테이션 전환 시그널",
        "conditions": {
            "sector_momentum": {"rotation_detected": True},
            "daily_work": {"category": "SECTOR", "recent": True},
            "us_market": {"narrative_shift": True}  # optional
        },
        "min_modules": 2,
        "confidence_base": 0.65,
        "suggested_action": "포트폴리오 섹터 비중 재조정 검토",
        "category": "SECTOR"
    },
    {
        "id": "SIG-CRYPTO-DIVERGE",
        "name": "크립토-전통시장 디커플링 시그널",
        "conditions": {
            "crypto_trends": {"btc_trend": "상승"},
            "liquidity_stress": {"score": ">60"},  # 전통시장 스트레스
        },
        "min_modules": 2,
        "confidence_base": 0.5,
        "suggested_action": "크립토 비중 확대 vs 리스크 평가",
        "category": "PORTFOLIO"
    }
]
```

### 4.3 Data Gap Analyzer 설계

```python
class DataGapAnalyzer:
    """시그널 분석 시 부족한 데이터를 식별하고 외부 소스를 추천"""

    def analyze(self, signal, available_modules):
        gaps = []
        # 1) 시그널 조건 중 데이터 없는 모듈 식별
        for module, condition in signal["conditions"].items():
            if module not in available_modules or available_modules[module] is None:
                gaps.append({
                    "module": module,
                    "reason": f"{module} 데이터 없음 또는 오래됨",
                    "impact": "시그널 confidence 저하"
                })
        # 2) 시그널을 강화할 수 있는 추가 데이터 추천
        enrichments = self.recommend_enrichments(signal, available_modules)
        return {"gaps": gaps, "enrichments": enrichments}

    def recommend_enrichments(self, signal, available_data):
        """외부 데이터로 시그널을 강화할 수 있는 경우 추천"""
        # external_sources.json에서 관련 소스 매칭
        ...
```

### 4.4 External Source Registry

```json
// data/external_sources.json
{
  "sources": [
    {
      "id": "fred-credit-spread",
      "name": "FRED 신용스프레드",
      "url": "https://fred.stlouisfed.org/series/BAMLC0A0CM",
      "category": "RISK",
      "data_type": "time_series",
      "update_frequency": "daily",
      "integration": "scripts/liquidity_monitor/fred_fetch.py",
      "synergy": "유동성 스트레스 모듈과 결합 시 신용 리스크 조기 감지 가능",
      "api_required": "FRED_API_KEY"
    },
    {
      "id": "yahoo-vix",
      "name": "Yahoo VIX Index",
      "url": "https://finance.yahoo.com/quote/%5EVIX",
      "category": "RISK",
      "data_type": "real_time",
      "update_frequency": "real_time",
      "integration": "scripts/liquidity_monitor/price_fetch.py",
      "synergy": "VIX 급등 + 섹터 방어주 전환 = 강력한 현금비중 확대 시그널"
    },
    {
      "id": "dart-disclosures",
      "name": "DART 전자공시",
      "url": "https://opendart.fss.or.kr",
      "category": "PORTFOLIO",
      "data_type": "event",
      "update_frequency": "real_time",
      "integration": "scripts/collect_disclosures.py",
      "synergy": "보유종목 공시 + 섹터 모멘텀 = 종목별 리스크/기회 조기 감지"
    }
  ]
}
```

### 4.5 Signal DB Model

```python
# backend/app/models/signal.py
class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(String(20), nullable=False, unique=True)  # SIG-CASH-UP-20260215
    rule_id = Column(String(50), nullable=False)  # SIG-CASH-UP
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, default=0.5)
    data_sources = Column(Text, default="[]")  # JSON: ["liquidity_stress", "sector_momentum"]
    evidence = Column(Text, default="[]")  # JSON: [{module, key, value, timestamp}]
    suggested_action = Column(Text)
    ai_interpretation = Column(Text)  # AI 전략가 해석 (Phase 2)
    status = Column(String(20), default="new")  # new, reviewed, accepted, rejected, expired
    related_idea_id = Column(Integer, ForeignKey("ideas.id"), nullable=True)
    data_gaps = Column(Text, default="[]")  # JSON: [{module, reason, recommended_source}]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
```

### 4.6 Dashboard Redesign Concept

```
┌──────────────────────────────────────────────────────────────┐
│  Intelligence Board — Stock Research ONE          [Refresh]   │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─── Signal Feed (좌측 40%) ─────────────────────────────┐  │
│  │  🔴 HIGH  현금비중 확대 시그널           conf: 82%      │  │
│  │  유동성 스트레스 72 + 방어주 전환 감지                   │  │
│  │  [근거 보기] [AI 해석] [채택] [거부]                     │  │
│  │  ─────────────────────────────────────────             │  │
│  │  🟡 MED   섹터 로테이션 전환              conf: 65%      │  │
│  │  ...                                                    │  │
│  │  ─────────────────────────────────────────             │  │
│  │  ⚪ LOW   크립토-전통시장 디커플링         conf: 45%      │  │
│  │  ...                                                    │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─── Detail Panel (우측 60%) ─────────────────────────────┐  │
│  │  📊 현금비중 확대 시그널 상세                             │  │
│  │                                                         │  │
│  │  ■ 근거 데이터                                          │  │
│  │  ├ [유동성 스트레스] 종합 72점 (2026-02-15)             │  │
│  │  ├ [섹터 모멘텀] XLU +2.3%, XLK -1.8% (방어주 전환)     │  │
│  │  └ [일일 작업] RISK 카테고리 최근 3건 관련               │  │
│  │                                                         │  │
│  │  ■ AI 전략가 해석                                       │  │
│  │  "유동성 스트레스가 70을 넘어서면서 섹터 로테이션이        │  │
│  │   방어주로 전환되고 있습니다. 과거 유사 패턴에서는..."     │  │
│  │                                                         │  │
│  │  ■ 제안 행동                                            │  │
│  │  → 현금비중 20%→30% 확대 검토                           │  │
│  │  → 성장주 비중 축소, 방어주/배당주 확대                   │  │
│  │                                                         │  │
│  │  ■ 데이터 갭 & 보완 추천                                │  │
│  │  ⚠ FRED 신용스프레드 미연동 (API key 필요)               │  │
│  │    → 연동 시: 신용 리스크 조기 감지로 confidence +15%     │  │
│  │  ⚠ 크립토 Fear&Greed 24시간 이상 경과                   │  │
│  │    → 갱신 시: 전통/크립토 상관관계 분석 가능              │  │
│  │                                                         │  │
│  │  [✅ 채택 → Idea로 등록] [✏ 수정] [❌ 거부]              │  │
│  └─────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## 5. Implementation Order

### Phase 1: Cross-Data Signal Engine (규칙 기반) — ~3-5일

| # | 작업 | 파일 | 의존성 |
|---|------|------|--------|
| 1-1 | Signal DB 모델 | `backend/app/models/signal.py` | - |
| 1-2 | Signal 스키마 | `backend/app/schemas/signal.py` | - |
| 1-3 | Signal Detection Rules 정의 | `data/signal_rules.json` | - |
| 1-4 | CrossDataSignalService: 규칙 엔진 | `backend/app/services/signal_service.py` | 1-1, 1-3 |
| 1-5 | Signal API 라우터 | `backend/app/api/signals.py` | 1-1, 1-2, 1-4 |
| 1-6 | main.py 라우터 등록 | `backend/app/main.py` | 1-5 |
| 1-7 | CrossModuleService 확장: 시그널 엔진 연동 | `backend/app/services/cross_module_service.py` | 1-4 |
| 1-8 | External Source Registry | `data/external_sources.json` | - |
| 1-9 | 시그널 생성 배치 스크립트 | `scripts/intelligence/generate_signals.py` | 1-4 |

### Phase 2: AI Strategist + Data Gap — ~3-5일

| # | 작업 | 파일 | 의존성 |
|---|------|------|--------|
| 2-1 | AI Strategist Service (Claude API) | `backend/app/services/strategist_service.py` | Phase 1 |
| 2-2 | Data Gap Analyzer | `backend/app/services/gap_analyzer.py` | 1-8 |
| 2-3 | External Source Recommender | `backend/app/services/source_recommender.py` | 1-8, 2-2 |
| 2-4 | Signal API 확장: AI 해석 + 갭 분석 엔드포인트 | `backend/app/api/signals.py` | 2-1, 2-2 |
| 2-5 | Signal → Idea 변환 로직 | `backend/app/services/signal_service.py` | 1-4 |
| 2-6 | MCP Tool 확장: generate_signals, analyze_gap, recommend_sources | `scripts/idea_pipeline/mcp_server.py` | 2-1, 2-2, 2-3 |

### Phase 3: Intelligence Dashboard Redesign — ~3-5일

| # | 작업 | 파일 | 의존성 |
|---|------|------|--------|
| 3-1 | idea_board.html 대폭 리디자인 | `dashboard/idea_board.html` | Phase 1+2 |
| 3-2 | Signal Feed 컴포넌트 (좌측 패널) | 위 파일 내 | 1-5 |
| 3-3 | Detail Panel: 근거 + AI 해석 + 제안 + 갭 | 위 파일 내 | 2-1, 2-2 |
| 3-4 | 채택/수정/거부 인터랙션 | 위 파일 내 | 2-5 |
| 3-5 | dashboard/index.html 링크 업데이트 | `dashboard/index.html` | 3-1 |
| 3-6 | 외부 데이터 자동 수집 연동 (기존 스크립트 활용) | `scripts/intelligence/` | 1-8 |

## 6. Success Criteria

- [ ] 기존 모듈 데이터 교차 분석 → 시그널 최소 3종 자동 생성
- [ ] 각 시그널에 근거 데이터(evidence) 링크 첨부
- [ ] Confidence scoring 동작 (교차 모듈 수 기반)
- [ ] AI 전략가가 시그널을 투자 관점으로 해석 (Claude API)
- [ ] 데이터 갭 식별 + 외부 소스 추천 + 시너지 설명
- [ ] 사용자가 시그널 검토 후 승인 → Idea로 자동 등록
- [ ] Intelligence Dashboard 리디자인: Signal Feed + Detail Panel + Data Gap
- [ ] LLM API 없어도 규칙 기반 시그널은 정상 동작

## 7. Out of Scope (이번 릴리스)

- 실시간 WebSocket 업데이트 (polling 방식)
- 외부 데이터 자동 구매/유료 API 연동
- 도메인 전문 에이전트 7개 (요구사항의 FR-AGENT-01~07) — 향후 Phase
- 아이디어 연결 그래프 시각화 (idea_connections)
- 대화형 워크스페이스 (B안) — 다음 PDCA 사이클
- 모바일 UI

## 8. Dependencies & Risks

| 항목 | 설명 | 완화 방안 |
|------|------|----------|
| 기존 모듈 데이터 충분성 | 유동성/크립토/공시 데이터가 없으면 교차 분석 불가 | DEMO 시드 데이터 + 실제 수집 스크립트 병행 |
| LLM API 비용 | AI 해석마다 API 호출 | 시그널 생성은 규칙 기반(무료), AI 해석은 선택적 |
| 규칙 설계 품질 | 노이즈 시그널 과다 | min_modules=2 교차 확인 필수, confidence 임계값 |
| CrossModuleService 의존 | 기존 서비스 확장 시 기존 기능 영향 | 별도 SignalService로 분리, CrossModule은 데이터 소스로만 활용 |
| Data Gap 추천 정확도 | 무의미한 외부 소스 추천 | 카테고리 매칭 + 검증된 소스만 레지스트리에 등록 |

## 9. Relationship to Previous Features

| Feature | 관계 | 활용 방식 |
|---------|------|----------|
| `liquidity-stress-monitor` | 데이터 소스 | StressIndex, LiquidityPrice → 시그널 조건 |
| `crypto-trends-monitor` | 데이터 소스 | BTC/ETH 트렌드, Fear&Greed → 시그널 조건 |
| `idea-ai-collaboration` | 확장 | CrossModuleService → SignalService, MCP 확장, Idea 모델 활용 |
| `disclosure-monitoring` | 데이터 소스 | 공시 데이터 → 종목별 시그널 |
| `stock-research-dashboard` | UI 패턴 | 기존 대시보드 디자인 참고 |
