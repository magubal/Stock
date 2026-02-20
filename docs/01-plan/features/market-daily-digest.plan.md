# Plan: Market Daily Digest (시장 종합정리)

> **Feature ID**: market-daily-digest
> **Created**: 2026-02-20
> **Phase**: Plan
> **Level**: Dynamic

---

## 1. Overview

### 1.1 Problem Statement
시장모니터링 7개 모듈(공시, 뉴스, 유동성, 크립토, 해자, Intelligence Board, 블로그)의 당일 데이터가 각각 분산되어 있어, 전체 시장 흐름을 한눈에 파악하고 종합적 판단을 내리기 어렵다.

### 1.2 Goal (1문장)
7개 모듈의 당일 핵심 데이터를 **Force-Directed 마인드맵**으로 종합 시각화하고, AI 기반 총평을 생성·저장하는 "종합정리" 페이지를 추가한다.

### 1.3 Success Criteria (DoD)
- [ ] 대시보드 시장모니터링 섹션에 "종합정리" 링크 추가, 클릭 시 신규 페이지 이동
- [ ] 당일 7개 모듈 데이터를 Force-Directed 마인드맵으로 시각화
- [ ] 마인드맵 노드 클릭 시 우측 패널에 해당 모듈 상세 데이터 표시
- [ ] AI Analyzer: AI 모델 선택(Claude/GPT/Gemini) + 총평 생성 버튼
- [ ] 사용자 확인 후 수동 저장 (Backend DB)
- [ ] 날짜 선택기로 히스토리 조회 가능
- [ ] AI API 미확보 시에도 수동 총평 작성·저장 가능

---

## 2. Context & Constraints

### 2.1 Existing System
| 항목 | 현재 상태 |
|------|----------|
| Dashboard | `dashboard/index.html` — CDN React+Babel 정적 HTML |
| 시장모니터링 | 7개 항목 (공시, 뉴스, 유동성, 크립토, 해자, Intelligence Board, 블로그) |
| Backend | FastAPI + SQLite (`backend/app/main.py`, 8+ routers) |
| 기존 API | 각 모듈별 REST API 엔드포인트 존재 |
| AI Analyzer 패턴 | `news_intelligence.html`에 Claude/GPT/Gemini 선택 + API 호출 구현 있음 |

### 2.2 Technical Constraints
- CDN 기반 정적 HTML (빌드 없음) — D3.js도 CDN 로드
- Backend: FastAPI + SQLite (기존 패턴 유지)
- AI API 키 미확보 시 graceful degradation 필수
- DEMO 데이터 규칙 준수 (`source="DEMO"`)

### 2.3 Dependencies
- D3.js v7 (CDN: `https://d3js.org/d3.v7.min.js`)
- 기존 7개 모듈 API 엔드포인트
- news_intelligence.html의 AI Analyzer UI 패턴

---

## 3. Data Sources (7 Modules)

| # | Module | API Endpoint | Key Data |
|---|--------|-------------|----------|
| 1 | 오늘의 공시 | `/api/v1/disclosures?date={date}` | 공시 건수, 주요 공시 목록, 심리 |
| 2 | 글로벌 뉴스 | `/api/v1/news/articles?date={date}` | 카테고리별 뉴스 건수, 핵심 이슈 |
| 3 | 유동성 스트레스 | `/api/v1/liquidity-stress/current` | 종합 스트레스 지수, 6대 모듈 점수 |
| 4 | 크립토 동향 | (Frontend-only, 외부 API 직접) | BTC/ETH 가격, Fear&Greed, DeFi TVL |
| 5 | 해자 분석 | `/api/v1/moat/summary` | 분석 종목 수, 평균 해자 점수 |
| 6 | Intelligence Board | `/api/v1/cross-module/context` | Cross-module signals, 이벤트 |
| 7 | 투자자 블로그 | `/api/v1/blog-review/posts?date={date}` | 수집 블로그 수, AI 요약 |

---

## 4. Feature Specification

### 4.1 Dashboard Link Addition
- `dashboard/index.html` 시장모니터링 섹션에 8번째 항목 추가
- **이름**: 종합정리
- **설명**: 전체 시장흐름 마인드맵 + AI 총평
- **테마 컬러**: Gold `#eab308`
- **링크**: `market_daily_digest.html`

### 4.2 Page Layout: Split View
```
┌──────────────────────────────────────────────────────────┐
│  [< 날짜]  2026-02-20 (목)  [날짜 >]    [AI Analyzer ▼] │
├─────────────────────────────────┬────────────────────────┤
│                                 │  📋 Module Detail      │
│   Force-Directed                │  ─────────────────     │
│   Mind Map                      │  [선택된 모듈 상세]     │
│   (D3.js)                       │  - KPI 카드들           │
│                                 │  - 핵심 데이터 목록     │
│   60%                           │  - 원본 페이지 링크     │
│                                 ├────────────────────────┤
│                                 │  💡 AI 총평             │
│                                 │  ─────────────────     │
│                                 │  [AI 생성 총평 텍스트]  │
│                                 │  [수동 편집 가능]       │
│                                 │  [💾 저장] [🤖 AI생성]  │
│                                 │  40%                   │
└─────────────────────────────────┴────────────────────────┘
```

### 4.3 Force-Directed Mind Map
- **중심 노드**: "2026-02-20 시장 종합" (크게, Gold 색상)
- **1차 노드 (7개)**: 각 모듈 (모듈별 테마 컬러)
  - 공시: `#ef4444` (Red)
  - 뉴스: `#f97316` (Orange)
  - 유동성: `#22c55e` (Green)
  - 크립토: `#a855f7` (Purple)
  - 해자: `#3b82f6` (Blue)
  - Intelligence: `#06b6d4` (Cyan)
  - 블로그: `#ec4899` (Pink)
- **2차 노드**: 각 모듈의 핵심 지표 (2~4개씩)
- **노드 크기**: 데이터 중요도/긴급도에 비례
- **링크 굵기**: 연관도 표현 (향후 확장)
- **인터랙션**:
  - 드래그: 노드 위치 이동
  - 클릭: 우측 패널에 상세 표시
  - 호버: 툴팁으로 요약 표시
  - 더블클릭: 해당 모듈 원본 페이지로 이동

### 4.4 AI Analyzer
- **UI 패턴**: news_intelligence.html의 AI Analyzer 재활용
- **AI 모델 선택**: Claude Sonnet / GPT-4o / Gemini Pro (드롭다운)
- **API Key 입력**: 모달 또는 설정 영역
- **프롬프트 구성**: 7개 모듈 요약 데이터를 컨텍스트로 포함
  - System: "당신은 시장 분석 전문가입니다. 아래 7개 모듈의 당일 데이터를 종합하여 시장 전체 흐름에 대한 핵심 인사이트와 총평을 작성하세요."
  - User: 각 모듈별 요약 데이터 JSON
- **Output**: 마크다운 형식 총평 텍스트
- **Fallback**: API 미확보 시 버튼 비활성 + "API 키를 설정하세요" 안내

### 4.5 Save (수동 저장)
- **저장 버튼**: 사용자가 총평 내용 확인 후 명시적 클릭
- **저장 대상**: AI 생성 총평 + 사용자 수정 내용 + 모듈별 요약 스냅샷
- **저장 확인**: 저장 성공 시 토스트 메시지
- **히스토리**: 날짜별 저장 기록 조회 가능

---

## 5. Backend Spec

### 5.1 DB Model: `DailyDigest`
| Column | Type | Description |
|--------|------|-------------|
| date | DATE (PK) | 날짜 |
| module_summaries | JSON | 7개 모듈 요약 스냅샷 |
| ai_summary | TEXT | AI 생성 총평 |
| user_summary | TEXT | 사용자 수정/추가 총평 |
| ai_model | VARCHAR(50) | 사용된 AI 모델명 |
| mindmap_data | JSON | 마인드맵 노드/링크 구조 (선택) |
| source | VARCHAR(20) | "DEMO" or "REAL" |
| created_at | DATETIME | 생성 시각 |
| updated_at | DATETIME | 수정 시각 |

### 5.2 API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/daily-digest/{date}` | 특정 날짜 종합정리 조회 |
| POST | `/api/v1/daily-digest` | 종합정리 저장 (upsert) |
| GET | `/api/v1/daily-digest/history` | 저장 히스토리 목록 (날짜 리스트) |
| POST | `/api/v1/daily-digest/ai-analyze` | AI 총평 생성 (Backend proxy) |

### 5.3 Service
- `backend/app/services/daily_digest_service.py`
- `backend/app/api/daily_digest.py`
- `backend/app/models/daily_digest.py`

---

## 6. Implementation Order

### Phase 1: Backend (DB + API)
1. DB Model 생성 (`DailyDigest`)
2. Service 레이어 구현
3. API Router 등록 (4개 엔드포인트)
4. main.py 라우터 등록
5. Seed data (DEMO 규칙 준수)

### Phase 2: Frontend — 기본 레이아웃
6. `dashboard/market_daily_digest.html` 생성 (Split 레이아웃)
7. 날짜 선택기 + 네비게이션
8. 7개 모듈 API 병렬 호출 + 데이터 매퍼

### Phase 3: Frontend — Force-Directed 마인드맵
9. D3.js Force Simulation 구현
10. 노드 렌더링 (중심 + 1차 + 2차)
11. 인터랙션 (드래그, 클릭, 호버, 더블클릭)
12. 노드 클릭 → 우측 패널 상세 연동

### Phase 4: AI Analyzer + 저장
13. AI Analyzer UI (모델 선택, 키 입력, 생성 버튼)
14. AI API 호출 (Backend proxy 또는 직접)
15. 총평 표시 + 편집 영역
16. 수동 저장 버튼 + API 연동
17. 히스토리 조회 기능

### Phase 5: 마무리
18. `dashboard/index.html` 시장모니터링에 링크 추가
19. DEMO 시드 데이터 생성
20. 반응형 레이아웃 (좁은 화면 → 상하 분할)

---

## 7. Risk & Mitigation

| # | Risk | Impact | Mitigation |
|---|------|--------|------------|
| R1 | 7개 API 동시 호출 지연/실패 | 마인드맵 불완전 | `Promise.allSettled` + 실패 모듈은 "데이터 없음" 노드 표시 + 프로그레스바 |
| R2 | Force-Directed 노드 텍스트 겹침 | UX 저하 | collision force + 텍스트 truncation + hover 시 전체 표시 |
| R3 | AI API 키 미확보 | 총평 기능 불가 | 수동 작성이 기본, AI는 보조. API 없으면 비활성 |
| R4 | 크립토 모듈은 Backend API 없음 | 데이터 수집 불일치 | Frontend에서 외부 API 직접 호출하여 통합 |
| R5 | Force 레이아웃 불안정 | 매번 다른 배치 | `forceCenter` + 초기 위치 preset + alpha decay 조정 |

---

## 8. Out of Scope (v1.0)
- 모듈 간 상관관계 자동 분석
- 알림/푸시 기능
- 멀티 유저 지원
- PDF 내보내기
- 30일 트렌드 차트

---

## 9. Estimation
| Phase | Items | Complexity |
|-------|-------|------------|
| Backend | Model + Service + API + Seed | Medium |
| Layout | Split view + 날짜 선택기 | Low |
| Mind Map | D3.js Force + 인터랙션 | High |
| AI Analyzer | 모델 선택 + API 호출 + 저장 | Medium |
| Integration | 대시보드 링크 + 반응형 | Low |
