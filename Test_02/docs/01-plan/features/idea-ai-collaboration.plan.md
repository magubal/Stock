# Feature Plan: Idea Management & AI Collaboration System

## 1. Overview
- **Feature Name**: idea-ai-collaboration (아이디어 매니징 & AI 협업 시스템)
- **Level**: Dynamic (FastAPI + SQLite + Static Dashboard + Python Scripts)
- **Priority**: High
- **Estimated Scope**: DB Models + Backend API + Ingestion Pipeline + Collaboration Skill + Dashboard Page
- **Requirements Doc**: `docs/requirements/idea-ai-collaboration-system.requirements.md`

## 2. Background & Motivation

투자자는 매일 7개 카테고리의 시장 분석 작업을 수행하며 아이디어를 축적한다.
현재 이 작업들은 ChatGPT, Claude, Gemini 등 여러 AI 세션에 분산되어 있어
아이디어 유실, 맥락 단절, 크로스-AI 시너지 부재 문제가 있다.

핵심 아이디어:
- 일일 작업 데이터(Excel 등)에서 인사이트를 자동 추출하여 투자 아이디어로 발전
- Context Packet 표준을 통해 Claude↔Gemini↔ChatGPT 간 분석 결과 공유
- 3단계 분리(원본→인사이트→아이디어)로 어떤 데이터 소스든 동일 모델로 처리
- Gemini가 기 구현한 기본 CRUD(Idea 모델, API, 스키마)를 확장하여 구축

## 3. Requirements

### 3.1 Functional Requirements

| ID | 요구사항 | 우선순위 | Phase |
|----|----------|----------|-------|
| FR-01 | `daily_work` 테이블: 원본 데이터 저장 (날짜, 카테고리, 내용, 소스링크) | Must | 1 |
| FR-02 | `insights` 테이블: 인사이트 저장 (type, text, confidence, keywords) | Must | 1 |
| FR-03 | `idea_evidence` 테이블: 아이디어↔인사이트 연결 | Must | 1 |
| FR-04 | `idea_connections` 테이블: 아이디어 간 관계 (supports, contradicts, extends) | Should | 3 |
| FR-05 | `idea_outcomes` 테이블: 아이디어 검증 결과 (predicted vs actual) | Should | 3 |
| FR-06 | Excel 파싱 스크립트: 7개 카테고리 자동 분류 + DB 저장 | Must | 1 |
| FR-07 | 범용 파서 인터페이스: Excel/CSV/Text/JSON 등 다양한 소스 지원 | Must | 1 |
| FR-08 | LLM 기반 인사이트 자동 추출 (핵심 주장, 예측, 패턴 식별) | Must | 1 |
| FR-09 | 기존 Gemini `Idea` 모델 확장: status 흐름 변경 (draft→active→testing→validated/invalidated→archived) | Must | 1 |
| FR-10 | `/api/v1/daily-work` CRUD 엔드포인트 | Must | 1 |
| FR-11 | `/api/v1/insights` CRUD 엔드포인트 | Must | 1 |
| FR-12 | `/api/v1/ideas` 확장: 검색, 필터, 카테고리별 통계 | Must | 1 |
| FR-13 | `collab_packets` 테이블: AI 협업 Context Packet 저장 | Must | 2 |
| FR-14 | `collab_sessions` 테이블: AI 세션 레지스트리 | Should | 2 |
| FR-15 | Context Packet JSON 표준 포맷 정의 및 생성/파싱 | Must | 2 |
| FR-16 | `/collab export` 커맨드: 현재 분석 맥락을 Context Packet으로 내보내기 | Must | 2 |
| FR-17 | `/collab import` 커맨드: 다른 AI의 Context Packet 가져오기 | Must | 2 |
| FR-18 | `/collab synthesize` 커맨드: 여러 AI 분석을 종합 | Should | 2 |
| FR-19 | `dashboard/idea_board.html` 아이디어 보드 페이지 | Should | 3 |
| FR-20 | `dashboard/index.html`에 아이디어 보드 링크 추가 | Must | 3 |

### 3.2 Non-Functional Requirements
- 기존 Gemini 구현물(`backend/app/models/idea.py`, `schemas/idea.py`, `api/ideas.py`) 최대한 활용·확장
- 3단계 분리 아키텍처: raw data(`daily_work`) → insights → ideas
- 새 데이터 소스 추가 시 Parser만 구현하면 나머지 파이프라인 재사용
- SQLite 호환 유지 (JSON 컬럼은 TEXT 저장)
- LLM API 미설정 시에도 수동 인사이트 입력으로 동작
- 모든 데이터 로컬 저장 (클라우드 전송 없음)

## 4. Technical Approach

### 4.1 데이터 모델 (기존 확장 + 신규)

**기존 확장** (Gemini 구현):
- `ideas` 테이블: status 흐름 변경, `category` 컬럼 추가, priority 범위 P1~P5

**신규 테이블**:
```
daily_work (원본 데이터)
├── id, date, category, description, content, source_link, source_type
├── created_at
└── UNIQUE(date, category, source_type)

insights (추출 인사이트)
├── id, work_id(FK→daily_work), type(claim/prediction/pattern)
├── text, confidence, keywords(JSON)
└── created_at

idea_evidence (아이디어↔인사이트)
├── idea_id(FK→ideas), insight_id(FK→insights)
└── relation_type(supports/primary/reference)

idea_connections (아이디어↔아이디어)
├── idea_a_id(FK), idea_b_id(FK)
└── relation_type(supports/contradicts/extends/depends_on)

idea_outcomes (검증 결과)
├── id, idea_id(FK), predicted, actual
└── evaluated_at, accuracy_score

collab_packets (AI 협업 패킷)
├── id, source_ai, session_id, topic, category
├── content_json(TEXT), request_action, request_ask
└── created_at

collab_sessions (AI 세션 레지스트리)
├── id, ai_type, session_link, assigned_task, status
└── last_exchange_at
```

### 4.2 Backend

- **Models**: `backend/app/models/daily_work.py`, `insight.py` 신규 + `idea.py` 확장
- **Schemas**: `backend/app/schemas/daily_work.py`, `insight.py` 신규 + `idea.py` 확장
- **API Routers**:
  - `backend/app/api/daily_work.py` — 원본 데이터 CRUD + 카테고리별 통계
  - `backend/app/api/insights.py` — 인사이트 CRUD + 키워드 검색
  - `backend/app/api/ideas.py` — 기존 확장 (필터, 연결, 통계)
  - `backend/app/api/collab.py` — 협업 패킷 CRUD
- **Services**:
  - `backend/app/services/insight_extractor.py` — LLM 기반 인사이트 추출
  - `backend/app/services/collab_service.py` — Context Packet 생성/파싱

### 4.3 수집 파이프라인 (Scripts)

```
scripts/idea_pipeline/
├── parsers/
│   ├── base_parser.py      # 추상 Parser 인터페이스
│   ├── excel_parser.py     # Excel 7카테고리 파싱
│   ├── text_parser.py      # 텍스트 파일 파싱
│   └── csv_parser.py       # CSV 파싱
├── extractors/
│   └── insight_extractor.py # LLM 인사이트 추출
├── ingest.py               # 통합 수집 CLI (파서 자동 선택)
└── collab/
    ├── export_packet.py    # Context Packet 내보내기
    └── import_packet.py    # Context Packet 가져오기
```

### 4.4 AI 협업 인지 전략 (A안: Claude MCP + Gem/GPT 1회 설정)

**원칙**: 각 AI가 협업 프로토콜을 영구 인지하되, 패킷 교환은 사용자가 복사/붙여넣기로 중개

#### Claude: MCP Server (완전 자동)
- 로컬 MCP 서버(`scripts/idea_pipeline/mcp_server.py`)를 `.claude/settings.json`에 등록
- 매 세션 자동으로 활성 아이디어, 미처리 패킷, 트리거 조건 로드
- MCP Tools: `get_active_ideas()`, `get_pending_packets()`, `export_packet()`, `import_packet()`

#### Gemini: Gem 1회 생성 (프로토콜 자동 인지)
- "투자 아이디어 협업 분석가" Gem 생성 시 프로토콜 시스템 지시 삽입
- 분석 완료 시 자동으로 "Context Packet으로 내보내시겠습니까?" 제안
- 패킷 교환은 사용자 복사/붙여넣기

#### ChatGPT: Custom GPT 1회 생성 (프로토콜 자동 인지)
- Gemini와 동일 방식으로 Custom GPT Instructions에 프로토콜 삽입

#### 협업 트리거 조건 (공통)
- 투자 판단 관련 분석 완료 시 → 교차검증 제안
- 한 방향 분석만 진행 시 → 반론 관점 제안
- 아이디어 상태 active→testing 전환 시 → 다른 AI 검증 제안

#### 실제 흐름
```
[Claude] 분석 → MCP로 자동 패킷 저장 → data/collab/packets/에 JSON 생성
    ↓ (사용자가 JSON 복사)
[Gemini Gem] 패킷 붙여넣기 → Gem이 프로토콜 인지하여 자동 검토 → 결과 JSON 출력
    ↓ (사용자가 결과 복사)
[Claude] "/collab import" 또는 MCP가 자동 감지 → 종합 → 아이디어 업데이트
```

### 4.5 Frontend

- **New Page**: `dashboard/idea_board.html` (기존 정적 HTML + CDN React 패턴)
- **Dashboard Link**: `dashboard/index.html`에 새 섹션 추가
- **시각화**: 칸반 보드 (draft→active→testing→validated), 카테고리별 통계 차트

## 5. Implementation Order

### Phase 1: 핵심 기반 (MVP)
1. DB 모델 생성 (daily_work, insights, idea_evidence + ideas 확장)
2. 범용 Parser 인터페이스 + Excel 파서
3. 수집 CLI (`scripts/idea_pipeline/ingest.py`)
4. API 엔드포인트 (daily_work, insights, ideas 확장)
5. LLM 인사이트 추출 서비스 (Anthropic API 활용)

### Phase 2: AI 협업
6. Context Packet 스키마 정의
7. collab_packets, collab_sessions DB 모델
8. `/collab` export/import 스크립트
9. 협업 API 엔드포인트

### Phase 3: UI + 고급 기능
10. idea_connections, idea_outcomes 모델
11. `dashboard/idea_board.html` 페이지
12. `dashboard/index.html` 링크 추가
13. 아이디어 연결 그래프 시각화

## 6. Success Criteria

- [ ] Excel 일일작업 데이터 파싱 → daily_work 테이블 저장 (7개 카테고리)
- [ ] 인사이트 자동 추출 (LLM) → insights 테이블 저장
- [ ] 인사이트 → 아이디어 생성 → 상태 관리 (5단계)
- [ ] 다른 파일 포맷(CSV, Text)도 동일 파이프라인으로 수집 가능
- [ ] Context Packet 생성 → JSON 파일 저장 → 다른 AI에서 활용 가능
- [ ] Context Packet 가져오기 → 기존 분석과 종합
- [ ] API 엔드포인트 정상 응답 (daily-work, insights, ideas, collab)
- [ ] 아이디어 보드 대시보드 페이지 표시

## 7. Out of Scope (이번 릴리스)
- AI 간 직접 통신 (자동 API 호출) — 사용자 중개 방식만
- 실시간 WebSocket 업데이트
- 도메인 전문 에이전트 7개 (SECTOR, US_MARKET 등) — Phase 2+ 이후
- 아이디어 검증 자동화 (시장 결과 자동 비교)
- 모바일 UI

## 8. Dependencies & Risks

| 항목 | 설명 | 완화 방안 |
|------|------|----------|
| Gemini 기존 코드 | `Idea` 모델/API가 이미 존재, 충돌 방지 필요 | 기존 코드 확장 방식으로 접근 |
| LLM API 키 | 인사이트 추출에 Anthropic/OpenAI API 필요 | API 키 없으면 수동 입력 모드 |
| JSON 컬럼 (SQLite) | JSON 쿼리 제한 | Python 레벨 필터링 + TEXT 저장 |
| Context 윈도우 | 대량 데이터 AI 전달 한계 | 요약 + 핵심만 전달하는 패킷 설계 |
