# PDCA 기반 개발 워크플로우 — AI 코딩 어시스턴트 통합 가이드

> **목적**: 이 문서는 AI 코딩 어시스턴트(Gemini, Claude, ChatGPT 등)가 PDCA 기반 개발 방법론을 즉시 이해하고 적용할 수 있도록 작성된 완전한 가이드입니다.
>
> **대상 프로젝트**: Stock Research ONE (한국어 주식 리서치 자동화)
>
> **핵심 원칙**: 모든 기능 개발은 반드시 PDCA(Plan→Design→Do→Check→Act) 사이클을 따르며, 추적 파일에 자동 등록되어야 한다.

---

## 1. PDCA란?

PDCA = Plan → Design → Do → Check (→ Act/Archive)

```
┌─── Plan ───┐    ┌── Design ──┐    ┌──── Do ────┐    ┌── Check ──┐    ┌── Archive ─┐
│ 목표/범위   │───▶│ 아키텍처   │───▶│ 코드 구현  │───▶│ Gap 분석  │───▶│ 완료 보고서│
│ 요구사항    │    │ 데이터모델 │    │ API/UI     │    │ 품질 검증 │    │ 교훈 정리  │
│ 성공기준    │    │ API 설계   │    │ 테스트     │    │ ≥90% PASS│    │ 아카이브   │
└────────────┘    └────────────┘    └────────────┘    └────────────┘    └────────────┘
```

### 각 Phase의 산출물

| Phase | 산출물 파일 | 내용 |
|-------|------------|------|
| **Plan** | `docs/01-plan/features/{name}.plan.md` | 목표, 요구사항, 범위, 성공기준 |
| **Design** | `docs/02-design/features/{name}.design.md` | 아키텍처, 데이터모델, API 설계, UI 와이어프레임 |
| **Do** | 실제 코드 파일들 | 백엔드, 프론트엔드, 스크립트 구현 |
| **Check** | `docs/03-analysis/features/{name}.analysis.md` | Gap 분석 (Design vs 구현 비교, Match Rate %) |
| **Report** | `docs/04-report/features/{name}.report.md` | 완료 보고서, PDCA 사이클 요약, 교훈 |

---

## 2. 프로젝트 구조

```
Stock/Test_02/
├── backend/app/
│   ├── main.py              # FastAPI 앱 (라우터 등록)
│   ├── models/              # SQLAlchemy DB 모델
│   ├── api/                 # FastAPI 라우터 (REST 엔드포인트)
│   ├── services/            # 비즈니스 로직
│   └── database.py          # DB 연결 설정
├── dashboard/               # 정적 HTML 대시보드 (CDN React+Babel)
│   ├── index.html           # 메인 대시보드
│   ├── project_status.html  # 프로젝트 현황 페이지
│   └── *.html               # 각 모듈별 페이지
├── scripts/                 # Python 배치/수집 스크립트
├── config/
│   └── pdca_id_map.json     # PDCA 기능 → 고정 ID 매핑 ★
├── docs/
│   ├── .pdca-status.json    # PDCA 상태 추적 ★
│   ├── 01-plan/features/    # Plan 문서들
│   ├── 02-design/features/  # Design 문서들
│   ├── 03-analysis/features/# Analysis 문서들
│   └── 04-report/features/  # Report 문서들
├── CLAUDE.md                # AI 에이전트 지침서
├── REQUESTS.md              # 요구사항 관리 (REQ-XXX)
└── TODO.md                  # 현재 작업 상태
```

---

## 3. 추적 시스템 (★ 핵심 — 반드시 이해)

### 3.1 두 가지 ID 체계

| 체계 | 형식 | 용도 | 관리 파일 |
|------|------|------|-----------|
| **REQ-XXX** | REQ-001 ~ | 사용자 요구사항 | `REQUESTS.md` |
| **PDCA-XXX** | PDCA-001 ~ | 개발된 기능 | `config/pdca_id_map.json` |

### 3.2 `config/pdca_id_map.json` — ID 레지스트리

```json
{
  "_comment": "PDCA feature -> fixed ID mapping. Never reuse deleted IDs.",
  "_nextId": 16,
  "map": {
    "stock-moat-estimator": 1,
    "evidence-based-moat": 2,
    "oracle-earnings-integration": 6,
    "news-intelligence-monitor": 8
  }
}
```

**규칙**:
- feature name은 **kebab-case** (예: `market-daily-digest`)
- ID는 순차 할당, **절대 재사용 금지**
- 새 기능 등록 시 `_nextId` 값을 사용하고 +1 증가

### 3.3 `docs/.pdca-status.json` — 상태 추적

```json
{
  "version": "2.0",
  "features": {
    "oracle-earnings-integration": {
      "phase": "check",
      "startedAt": "2026-02-15T12:00:00Z",
      "planPath": "docs/01-plan/features/oracle-earnings-integration.plan.md",
      "designPath": "docs/02-design/features/oracle-earnings-integration.design.md",
      "analysisPath": "docs/03-analysis/features/oracle-earnings-integration.analysis.md",
      "matchRate": 97.5,
      "iterationCount": 0
    }
  }
}
```

**중요**: `planPath`가 있어야 대시보드에 표시됨. `phaseNumber`/`timestamps` 필드가 있는 엔트리는 자동 생성된 노이즈이므로 무시.

### 3.4 대시보드 표시 조건

`project_status.py` API가 이 조건으로 필터링:
```python
# planPath 또는 archivedTo가 있는 항목만 표시
if not info.get("planPath") and not info.get("archivedTo"):
    continue  # 대시보드에 안 보임!
```

---

## 4. 개발 워크플로우 (Full Lifecycle)

### Phase 0: 브레인스토밍 (`/brain`)

새 기능 요청 시 반드시 브레인스토밍부터 시작:

**입력**: 사용자가 기능 아이디어 설명
**과정**:
1. 문제를 1문장으로 재정의 + 성공기준 정의
2. 제약/맥락 수집 (1~3개 질문)
3. 대안 2~4개 생성 (각각: 핵심/장점/단점/실패모드)
4. 비교표로 평가 (기준 4~6개)
5. 추천안 선정 + 리스크/완화 Top 3

**출력 형식**:
```markdown
# Brainstorm 결과: <기능명>

## 1) 목표 / 성공 기준(DoD)
## 2) 전제/제약
## 3) 대안 (2~4개, 각각 핵심/장점/단점/실패모드)
## 4) 비교표 (기준 4~6개)
## 5) 추천안 + 이유 + 뒤집히는 조건
## 6) 리스크/완화 (Top 3)
## 7) PDCA Handoff → 다음: Plan 작성
```

**규칙**: 브레인스토밍에서는 **코드를 작성하지 않는다**. 의사결정만.

### Phase 1: Plan

**파일**: `docs/01-plan/features/{feature-name}.plan.md`

**필수 섹션**:
```markdown
# Feature Plan: {Feature Name}

## 1. Overview
- Feature Name: {kebab-case-name}
- Level: Starter/Dynamic/Enterprise
- Priority: High/Medium/Low
- Estimated Scope: 한 줄 요약
- Brainstorm: 일자 + 선정 안

## 2. Background & Motivation
(왜 이 기능이 필요한가?)

## 3. Requirements
### 3.1 Functional Requirements
| ID | 요구사항 | 우선순위 |
|----|----------|----------|
| FR-01 | ... | Must/Should/Could |

### 3.2 Non-Functional Requirements
(성능, 보안, 호환성 등)

## 4. Success Criteria
- [ ] 검증 가능한 체크리스트

## 5. Out of Scope
(이번에 하지 않을 것)

## 6. Dependencies
(필요한 외부 리소스, 사전 조건)
```

**★ 등록 필수 작업** (Plan 생성 직후):
```
1. docs/01-plan/features/{name}.plan.md 파일 생성
2. docs/.pdca-status.json 에 엔트리 추가:
   {
     "phase": "plan",
     "startedAt": "{ISO timestamp}",
     "planPath": "docs/01-plan/features/{name}.plan.md"
   }
3. config/pdca_id_map.json 에 ID 할당:
   map에 "{name}": {_nextId} 추가, _nextId +1
4. REQUESTS.md 에 REQ-XXX 항목 추가 (PDCA-XXX 연결)
```

### Phase 2: Design

**파일**: `docs/02-design/features/{feature-name}.design.md`

**필수 섹션**:
```markdown
# Feature Design: {Feature Name}

> Plan 참조: `docs/01-plan/features/{name}.plan.md`

## 1. Architecture Overview
(ASCII 다이어그램 권장)

## 2. Data Models
(SQLAlchemy 모델, Pydantic 스키마)

## 3. API Design
| Method | Path | Request | Response | 설명 |
|--------|------|---------|----------|------|
| GET | /api/v1/... | - | {...} | ... |

## 4. UI/UX Design
(화면 구성, 컴포넌트 구조)

## 5. Error Handling
(에러 케이스 정의)

## 6. Migration/Compatibility
(기존 시스템과의 호환성)
```

**★ 등록 작업**:
```
1. docs/02-design/features/{name}.design.md 파일 생성
2. docs/.pdca-status.json 업데이트:
   - phase: "design"
   - designPath: "docs/02-design/features/{name}.design.md"
```

### Phase 3: Do (구현)

Design 문서를 참조하여 코드 구현:

**백엔드 체크리스트**:
- [ ] DB 모델 (`backend/app/models/`)
- [ ] `models/__init__.py`에 import 추가
- [ ] Service 레이어 (`backend/app/services/`)
- [ ] API Router (`backend/app/api/`)
- [ ] `main.py`에 router 등록
- [ ] 시드 데이터 (필요시, `source="DEMO"` 필수)

**프론트엔드 체크리스트**:
- [ ] 대시보드 HTML (`dashboard/{name}.html`)
- [ ] `dashboard/index.html`에 링크 추가
- [ ] API 연동 테스트

**★ 등록 작업**:
```
docs/.pdca-status.json 업데이트:
- phase: "do"
```

### Phase 4: Check (Gap 분석)

Design 문서 vs 실제 구현을 항목별로 비교:

**파일**: `docs/03-analysis/features/{feature-name}.analysis.md`

```markdown
# Gap Analysis: {feature-name}

> Design: `docs/02-design/features/{name}.design.md`
> Analysis Date: {YYYY-MM-DD}

## Overall Match Rate: **XX.X%**

## 1. Data Models
| Design Item | Status | Notes |
|-------------|--------|-------|
| Model A | MATCH | 정확히 일치 |
| Model B | MINOR GAP | 필드명 차이 있으나 기능 동일 |
| Model C | MISSING | 미구현 |

## 2. API Endpoints
| Design Item | Status | Notes |
|-------------|--------|-------|
| GET /api/... | MATCH | |

## 3. UI Components
...

## Summary
- Total items: XX
- MATCH: XX (XX%)
- MINOR GAP: XX (XX%)
- MISSING: XX (XX%)
```

**Status 코드**:
| Status | 의미 | Match Rate 반영 |
|--------|------|:---:|
| MATCH | 설계와 정확히 일치 | 100% |
| MINOR GAP | 사소한 차이, 기능 동일 | 90% |
| PARTIAL | 부분 구현 | 50% |
| MISSING | 미구현 | 0% |
| BONUS | 설계에 없는 추가 구현 | 가산 없음 |

**판정 기준**:
- **≥ 90%** → PASS → Report 작성 후 Archive
- **< 90%** → FAIL → 개선 후 재분석 (최대 5회 반복)

**★ 등록 작업**:
```
docs/.pdca-status.json 업데이트:
- phase: "check"
- analysisPath: "docs/03-analysis/features/{name}.analysis.md"
- matchRate: XX.X
- checkCompletedAt: "{ISO timestamp}"
```

### Phase 5: Report & Archive

**파일**: `docs/04-report/features/{feature-name}.report.md`

```markdown
# {feature-name} Completion Report

> Summary: 기능 한 줄 설명
> Date: {YYYY-MM-DD}
> Status: COMPLETE
> Match Rate: XX.X%

## 1. PDCA Cycle Summary
| Phase | Date | Duration | Deliverable |
|-------|------|----------|-------------|
| Plan | ... | ~XXmin | plan.md |
| Design | ... | ~XXmin | design.md |
| Do | ... | ~XXmin | N files |
| Check | ... | ~XXmin | analysis.md (XX.X%) |
| Report | ... | - | This document |

## 2. Feature Overview
## 3. Implementation Details
## 4. Key Decisions
## 5. Lessons Learned
## 6. Known Limitations
```

**★ 등록 작업**:
```
docs/.pdca-status.json 업데이트:
- phase: "archived"
- archivedAt: "{ISO timestamp}"
- archivedTo: "docs/archive/YYYY-MM/{name}/"
```

---

## 5. 핵심 규칙 (MANDATORY)

### 5.1 DEMO 데이터 규칙
```
모든 시드/테스트/더미 데이터는 반드시 source="DEMO"로 마킹
- DB: source 필드에 "DEMO"
- UI: isDemo(source) → 빨간 DEMO 배지 표시
- 실데이터와 혼재 금지
```

### 5.2 PDCA 등록 규칙 (★ 가장 중요)
```
기능 개발 시작 시 반드시:
1. Plan 문서 생성 → docs/01-plan/features/{name}.plan.md
2. .pdca-status.json에 planPath 포함한 엔트리 추가
3. pdca_id_map.json에 PDCA-XXX ID 할당
4. REQUESTS.md에 REQ-XXX 추가

이 4단계를 빠뜨리면 대시보드에 기능이 표시되지 않음!
```

### 5.3 Feature Name 규칙
```
- kebab-case 필수 (예: market-daily-digest)
- 최소 2단어 이상
- 블랙리스트 금지: backend, scripts, api, frontend, tests, schemas, parsers, dev
  (이들은 디렉토리명이며 기능명이 아님)
```

### 5.4 Windows 환경 주의
```
- PowerShell 미사용 (AhnLab V3 오탐 MDP.Powershell.M2514)
- bash && 대신 절대경로 사용
- 한국어 출력: sys.stdout.reconfigure(encoding='utf-8')
- pip 권한 오류: --no-cache-dir 옵션
```

---

## 6. 기술 스택 참조

### 백엔드
| 항목 | 기술 |
|------|------|
| Framework | FastAPI (Python 3.11+) |
| ORM | SQLAlchemy |
| DB | SQLite (개발) / PostgreSQL (운영) |
| API 문서 | http://localhost:8000/docs (Swagger) |

### 프론트엔드 (Dashboard)
| 항목 | 기술 |
|------|------|
| 방식 | CDN React 18 + Babel Standalone (정적 HTML) |
| 스타일 | Inline CSS (Dark OLED 테마) |
| 차트 | D3.js v7 |
| 아이콘 | Lucide Icons |
| 서버 | `python -m http.server 8080` |

> **주의**: `dashboard/*.html`은 React SPA가 아님! 각 파일이 독립적인 CDN React 앱.
> `frontend/`(Vite SPA)와 `dashboard/`(정적 HTML) 두 개의 프론트엔드가 공존.

### 서버 기동법
```bash
# 백엔드
cd backend && venv/Scripts/activate && uvicorn app.main:app --reload --port 8000

# 대시보드
cd dashboard && python -m http.server 8080

# 시드 데이터
python scripts/{module}/seed_data.py
```

---

## 7. 현재 개발 현황 (2026-02-20 기준)

### 등록된 기능 (pdca_id_map.json)

| PDCA-ID | Feature Name | Phase | Match Rate |
|---------|-------------|-------|:----------:|
| PDCA-001 | stock-moat-estimator | Archived | 98.4% |
| PDCA-002 | evidence-based-moat | Archived | 95.2% |
| PDCA-003 | stock-research-dashboard | Do | - |
| PDCA-004 | disclosure-monitoring | Archived | 96.4% |
| PDCA-005 | idea-ai-collaboration | Check | 93.8% |
| PDCA-006 | oracle-earnings-integration | Check | 97.5% |
| PDCA-007 | investment-intelligence-engine | Check | 98.5% |
| PDCA-008 | news-intelligence-monitor | Archived | 98.4% |
| PDCA-009 | data-source-footer | - | - |
| PDCA-010 | pdca-status-sync | Archived | 97.2% |
| PDCA-011 | disclosure-auto-collect | Archived | 97.9% |
| PDCA-012 | zombie-process-cleanup | Archived | 100% |
| PDCA-013 | pdca-auto-register | Archived | 100% |
| PDCA-014 | project-status-detail-enhance | Archived | 100% |
| PDCA-015 | pdca-auto-register-v2 | Do | - |

### 다음 ID: PDCA-016 (= `_nextId: 16`)

---

## 8. 실전 예시: 새 기능 "market-daily-digest" 개발

### Step 1: Brain (의사결정)
```
사용자: "시장 종합 정리 기능을 만들어줘"
AI: 브레인스토밍 실행 → 대안 비교 → 추천안 선정
AI: "market-daily-digest로 Plan을 작성하시겠습니까?"
```

### Step 2: Plan 생성
```
1. docs/01-plan/features/market-daily-digest.plan.md 작성
2. config/pdca_id_map.json 수정:
   - "market-daily-digest": 16
   - _nextId: 17
3. docs/.pdca-status.json 수정:
   - features["market-daily-digest"] = {
       "phase": "plan",
       "startedAt": "2026-02-20T...",
       "planPath": "docs/01-plan/features/market-daily-digest.plan.md"
     }
4. REQUESTS.md에 REQ-032 추가
```

### Step 3: Design 생성
```
1. docs/02-design/features/market-daily-digest.design.md 작성
2. .pdca-status.json: phase→"design", designPath 추가
```

### Step 4: Do (구현)
```
1. backend/app/models/daily_digest.py → DB 모델
2. backend/app/services/daily_digest_service.py → 서비스
3. backend/app/api/daily_digest.py → API 라우터
4. backend/app/main.py → 라우터 등록
5. dashboard/market_daily_digest.html → UI
6. dashboard/index.html → 링크 추가
7. .pdca-status.json: phase→"do"
```

### Step 5: Check (Gap 분석)
```
1. Design의 모든 항목 vs 구현 코드 대조
2. docs/03-analysis/features/market-daily-digest.analysis.md 작성
3. Match Rate 계산 → 97%이면 PASS
4. .pdca-status.json: phase→"check", matchRate, analysisPath 추가
```

### Step 6: Report & Archive
```
1. docs/04-report/features/market-daily-digest.report.md 작성
2. .pdca-status.json: phase→"archived", archivedAt 추가
```

---

## 9. Gemini 도입 시 체크리스트

### 9.1 세션 시작 시
```
1. CLAUDE.md 읽기 (프로젝트 컨텍스트)
2. TODO.md 읽기 (현재 작업 상태)
3. REQUESTS.md 읽기 (요구사항 현황)
4. docs/.pdca-status.json 읽기 (PDCA 진행 상태)
5. config/pdca_id_map.json 읽기 (ID 매핑)
```

### 9.2 기능 개발 시 (★ 필수 체크포인트)

```
□ Brain 완료 → 추천안 선정
□ Plan 문서 생성
□ ★ pdca_id_map.json에 PDCA-ID 할당
□ ★ .pdca-status.json에 planPath 포함 엔트리 생성
□ ★ REQUESTS.md에 REQ-XXX 추가
□ Design 문서 생성
□ ★ .pdca-status.json에 designPath 추가
□ 코드 구현
□ ★ .pdca-status.json phase→"do"
□ Gap 분석
□ ★ .pdca-status.json에 analysisPath, matchRate 추가
□ Report 작성
□ ★ .pdca-status.json phase→"archived"
```

★ 표시 항목이 누락되면 **대시보드에 기능이 표시되지 않는다**.

### 9.3 파일 수정 시 주의사항

**JSON 파일 수정 규칙**:
- `pdca_id_map.json`: ID는 순차 할당, `_nextId` 반드시 갱신
- `.pdca-status.json`: `planPath` 필드가 없으면 대시보드에서 보이지 않음
- `activeFeatures` 배열은 건드리지 않음 (bkit 자동 관리)
- `features` 딕셔너리에만 추가/수정

**REQUESTS.md 수정 규칙**:
- 요약 테이블 + 상세 섹션 모두 추가
- 상태: 기획/진행/검증/완료
- PDCA-XXX ID 연결 표기

---

## 10. 자주 하는 실수와 해결

| 실수 | 증상 | 해결 |
|------|------|------|
| Plan 파일만 만들고 .pdca-status.json 미갱신 | 대시보드에 안 보임 | .pdca-status.json에 planPath 추가 |
| pdca_id_map.json에 미등록 | PDCA-ID 없음 | map에 추가 + _nextId 증가 |
| feature name이 kebab-case 아님 | 일관성 깨짐 | 반드시 kebab-case 사용 |
| 새 API 라우터를 main.py에 안 넣음 | 404 에러 | main.py에 include_router 추가 |
| 새 모델을 __init__.py에 안 넣음 | 테이블 미생성 | models/__init__.py에 import 추가 |
| DEMO 데이터에 source="DEMO" 안 넣음 | 실데이터와 혼동 | 반드시 source="DEMO" |
| 세션 넘어가며 컨텍스트 유실 | 등록 누락 | 매 세션 시작 시 위 파일들 재확인 |

---

## 부록 A: 기존 API 엔드포인트 목록

```
# Daily Digest
GET  /api/v1/daily-digest/{date}    - 특정 날짜 종합정리
POST /api/v1/daily-digest           - 종합정리 저장
GET  /api/v1/daily-digest/history   - 히스토리 목록
POST /api/v1/daily-digest/ai-analyze - AI 총평 생성
GET  /api/v1/daily-digest/models    - AI 모델 목록

# Disclosures
GET  /api/v1/disclosures            - 공시 목록

# News Intelligence
GET  /api/v1/news-intel/articles    - 뉴스 기사
GET  /api/v1/news-intel/narrative   - 시장 내러티브
POST /api/v1/news-intel/fetch       - 뉴스 수집 실행

# Liquidity Stress
GET  /api/v1/liquidity-stress       - 스트레스 지수
GET  /api/v1/liquidity-stress/history - 히스토리

# Blog Review
GET  /api/v1/blog-review/posts      - 블로그 포스트
GET  /api/v1/blog-review/bloggers   - 블로거 목록

# Project Status
GET  /api/v1/project-status/pdca    - PDCA 현황
GET  /api/v1/project-status/req-docs - REQ 문서

# Cross Module
GET  /api/v1/cross-module/context   - 크로스 모듈 컨텍스트

# Crypto
GET  /api/v1/crypto/latest          - 최신 가격
GET  /api/v1/crypto/history         - 히스토리

# Moat Dashboard
GET  /api/v1/moat-dashboard         - 해자 대시보드
GET  /api/v1/moat-dashboard/stocks  - 종목 목록
```

---

## 부록 B: 빠른 참조 카드

```
┌──────────────────────────────────────────────────┐
│  PDCA 개발 빠른 참조                              │
├──────────────────────────────────────────────────┤
│                                                  │
│  1. Brain → 의사결정만 (코드 X)                   │
│  2. Plan  → .plan.md + pdca_id_map + status.json │
│  3. Design → .design.md + status.json 갱신       │
│  4. Do    → 코드 구현 + status.json phase=do     │
│  5. Check → .analysis.md + matchRate ≥90%        │
│  6. Report → .report.md + phase=archived         │
│                                                  │
│  ★ 매 단계마다 .pdca-status.json 갱신 필수!      │
│  ★ Plan 시 pdca_id_map.json ID 할당 필수!        │
│  ★ Plan 시 REQUESTS.md REQ-XXX 추가 필수!        │
│                                                  │
│  서버: backend=8000, dashboard=8080              │
│  DB: SQLite (stock_research.db)                  │
│  UI: CDN React + Babel (정적 HTML)               │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

*이 가이드는 2026-02-20 기준으로 작성되었습니다. 프로젝트 구조가 변경되면 이 문서도 함께 업데이트하세요.*
