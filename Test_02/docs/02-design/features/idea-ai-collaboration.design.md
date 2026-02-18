# Feature Design: Idea Management & AI Collaboration System

> **Feature**: idea-ai-collaboration
> **Plan**: `docs/01-plan/features/idea-ai-collaboration.plan.md`
> **Requirements**: `docs/requirements/idea-ai-collaboration-system.requirements.md`

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Stock Research ONE                          │
│                                                                  │
│  ┌─────────────┐  ┌───────────────┐  ┌───────────────────────┐  │
│  │ Data Parsers │  │ MCP Server    │  │ FastAPI Backend        │  │
│  │ (Excel,CSV,  │  │ (Claude 전용)  │  │ /api/v1/daily-work    │  │
│  │  Text,JSON)  │  │ get_ideas()   │  │ /api/v1/insights      │  │
│  └──────┬───────┘  │ export/import │  │ /api/v1/ideas         │  │
│         │          │ get_triggers  │  │ /api/v1/collab        │  │
│         ▼          └───────┬───────┘  └───────────┬───────────┘  │
│  ┌──────────────────────────┴─────────────────────┴───────────┐  │
│  │                    SQLite Database                          │  │
│  │  daily_work │ insights │ ideas │ idea_evidence             │  │
│  │  collab_packets │ collab_sessions                          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  data/collab/                                             │   │
│  │  ├── packets/          (Context Packet JSON 파일)         │   │
│  │  ├── COLLAB_PROTOCOL.md (공통 프로토콜 문서)               │   │
│  │  └── state.json        (현재 활성 상태)                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │ dashboard/      │  │ Gemini Gem     │  │ ChatGPT GPT    │    │
│  │ idea_board.html │  │ (프로토콜 내장) │  │ (프로토콜 내장) │    │
│  └────────────────┘  └────────────────┘  └────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Database Schema

### 2.1 daily_work (원본 데이터)

```sql
CREATE TABLE daily_work (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        DATE NOT NULL,
    category    VARCHAR(50) NOT NULL,   -- SECTOR, US_MARKET, THEME, RISK, NEXT_DAY, PORTFOLIO, AI_RESEARCH
    description TEXT,                   -- 설명/목적
    content     TEXT NOT NULL,          -- 상세내용
    source_link VARCHAR(500),           -- ChatGPT 세션 링크 등
    source_type VARCHAR(50) DEFAULT 'excel',  -- excel, csv, text, manual
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, category, source_type)
);
```

### 2.2 insights (추출 인사이트)

```sql
CREATE TABLE insights (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id     INTEGER REFERENCES daily_work(id) ON DELETE SET NULL,
    type        VARCHAR(20) NOT NULL,   -- claim, prediction, pattern
    text        TEXT NOT NULL,           -- 인사이트 내용
    confidence  REAL DEFAULT 0.5,       -- 0.0 ~ 1.0
    keywords    TEXT DEFAULT '[]',      -- JSON array (SQLite TEXT)
    source_ai   VARCHAR(20),            -- claude, gemini, chatgpt, manual
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2.3 ideas (기존 확장)

Gemini가 만든 `ideas` 테이블을 확장:

```python
# 추가 컬럼
category    = Column(String(50), nullable=True)   # 7개 카테고리 또는 CROSS_CATEGORY
thesis      = Column(Text, nullable=True)         # 투자 가설
status      변경: NEW → draft, IN_PROGRESS → active, REVIEW → testing,
                  DONE → validated/invalidated, ARCHIVED → archived
```

### 2.4 idea_evidence (아이디어↔인사이트 연결)

```sql
CREATE TABLE idea_evidence (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    idea_id       INTEGER NOT NULL REFERENCES ideas(id) ON DELETE CASCADE,
    insight_id    INTEGER NOT NULL REFERENCES insights(id) ON DELETE CASCADE,
    relation_type VARCHAR(20) DEFAULT 'supports',  -- supports, primary, reference
    UNIQUE(idea_id, insight_id)
);
```

### 2.5 collab_packets (AI 협업 패킷)

```sql
CREATE TABLE collab_packets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    packet_id       VARCHAR(36) NOT NULL UNIQUE,  -- UUID
    source_ai       VARCHAR(20) NOT NULL,          -- claude, gemini, chatgpt
    topic           VARCHAR(200) NOT NULL,
    category        VARCHAR(50),
    content_json    TEXT NOT NULL,                  -- 전체 Context Packet JSON
    request_action  VARCHAR(20),                   -- validate, extend, challenge, synthesize
    request_ask     TEXT,
    status          VARCHAR(20) DEFAULT 'pending', -- pending, reviewed, synthesized
    related_idea_id INTEGER REFERENCES ideas(id),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2.6 collab_sessions (AI 세션 레지스트리)

```sql
CREATE TABLE collab_sessions (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    ai_type           VARCHAR(20) NOT NULL,
    session_link      VARCHAR(500),
    assigned_task     TEXT,
    status            VARCHAR(20) DEFAULT 'active', -- active, completed, abandoned
    last_exchange_at  DATETIME,
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. API Design

### 3.1 Daily Work API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/daily-work` | 원본 데이터 등록 |
| GET | `/api/v1/daily-work` | 목록 조회 (필터: date, category) |
| GET | `/api/v1/daily-work/{id}` | 단건 조회 |
| GET | `/api/v1/daily-work/stats` | 카테고리별 통계 |
| DELETE | `/api/v1/daily-work/{id}` | 삭제 |

### 3.2 Insights API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/insights` | 인사이트 등록 (수동) |
| POST | `/api/v1/insights/extract` | LLM으로 인사이트 자동 추출 (work_id 기반) |
| GET | `/api/v1/insights` | 목록 조회 (필터: type, keyword, work_id) |
| GET | `/api/v1/insights/{id}` | 단건 조회 |
| DELETE | `/api/v1/insights/{id}` | 삭제 |

### 3.3 Ideas API (기존 확장)

| Method | Path | Description |
|--------|------|-------------|
| (기존) | `/ideas/*` | Gemini 구현 CRUD 유지 |
| GET | `/ideas/stats` | 카테고리별·상태별 통계 (신규) |
| POST | `/ideas/{id}/evidence` | 아이디어에 인사이트 연결 (신규) |
| GET | `/ideas/{id}/evidence` | 아이디어의 근거 인사이트 조회 (신규) |

### 3.4 Collab API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/collab/packets` | 패킷 저장 |
| GET | `/api/v1/collab/packets` | 패킷 목록 (필터: status, source_ai) |
| GET | `/api/v1/collab/packets/{id}` | 패킷 단건 조회 |
| PUT | `/api/v1/collab/packets/{id}/status` | 패킷 상태 변경 (reviewed, synthesized) |
| GET | `/api/v1/collab/state` | 현재 협업 상태 (활성 아이디어, 미처리 패킷) |

---

## 4. Context Packet Schema

```json
{
  "packet_version": "1.0",
  "packet_id": "uuid-v4",
  "source_ai": "claude | gemini | chatgpt",
  "timestamp": "ISO-8601",
  "topic": "분석 주제",
  "category": "SECTOR | US_MARKET | THEME | RISK | NEXT_DAY | PORTFOLIO | AI_RESEARCH | CROSS",
  "context": {
    "background": "현재 시장 상황 요약",
    "analysis": "분석 내용",
    "conclusions": ["결론 1", "결론 2"],
    "open_questions": ["미해결 질문"],
    "data_references": ["참조 데이터"]
  },
  "request_to_next_ai": {
    "action": "validate | extend | challenge | synthesize",
    "specific_ask": "구체적 요청 사항",
    "priority": "high | medium | low"
  },
  "metadata": {
    "related_ideas": ["IDEA-001"],
    "confidence": 0.7,
    "tags": ["키워드1", "키워드2"]
  }
}
```

---

## 5. MCP Server Design (Claude 전용)

### 5.1 파일 위치

```
scripts/idea_pipeline/mcp_server.py
```

### 5.2 MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_active_ideas` | 활성 아이디어 목록 조회 | `status?`, `category?`, `limit?` |
| `get_pending_packets` | 미처리 협업 패킷 조회 | `source_ai?` |
| `export_packet` | 현재 분석을 Context Packet으로 저장 | `topic`, `category`, `context`, `request` |
| `import_packet` | 패킷 가져와서 DB+파일 저장 | `packet_json` |
| `get_collab_triggers` | 협업 트리거 조건 조회 | - |
| `get_daily_work_summary` | 최근 일일작업 요약 | `days?`, `category?` |
| `create_idea_from_insights` | 인사이트 → 아이디어 생성 | `title`, `thesis`, `insight_ids[]` |

### 5.3 MCP Resources

| URI | Description |
|-----|-------------|
| `collab://protocol` | COLLAB_PROTOCOL.md 내용 |
| `collab://state` | 현재 협업 상태 JSON |
| `collab://packets/latest` | 최근 패킷 5개 |

### 5.4 Claude 등록

```json
// .claude/settings.json
{
  "mcpServers": {
    "idea-collab": {
      "command": "python",
      "args": ["scripts/idea_pipeline/mcp_server.py"],
      "env": {
        "DATABASE_URL": "sqlite:///backend/stock_research.db"
      }
    }
  }
}
```

---

## 6. Parser Pipeline Design

### 6.1 Base Parser Interface

```python
# scripts/idea_pipeline/parsers/base_parser.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
from datetime import date

@dataclass
class DailyWorkRow:
    date: date
    category: str          # SECTOR, US_MARKET, etc.
    description: str
    content: str
    source_link: str = ''
    source_type: str = ''  # excel, csv, text, manual

class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> List[DailyWorkRow]:
        """파일을 파싱하여 DailyWorkRow 리스트 반환"""
        pass

    @abstractmethod
    def supports(self, file_path: str) -> bool:
        """이 파서가 해당 파일을 처리할 수 있는지 판별"""
        pass
```

### 6.2 Excel Parser

```python
# scripts/idea_pipeline/parsers/excel_parser.py
class ExcelParser(BaseParser):
    # 7개 카테고리 매핑
    CATEGORY_MAP = {
        '시장섹터선호변화': 'SECTOR',
        '미국시장이슈및동향': 'US_MARKET',
        '시장테마흐름': 'THEME',
        '주식시장리스크': 'RISK',
        '익일시장추정': 'NEXT_DAY',
        '투자시장': 'PORTFOLIO',
        'AI 리서치': 'AI_RESEARCH',
    }

    def supports(self, file_path):
        return file_path.endswith(('.xlsx', '.xls'))

    def parse(self, file_path) -> List[DailyWorkRow]:
        # openpyxl로 읽기 → 카테고리 매핑 → DailyWorkRow 리스트
        ...
```

### 6.3 수집 CLI

```bash
# 사용법
python scripts/idea_pipeline/ingest.py data/ask/some_file.xlsx
python scripts/idea_pipeline/ingest.py data/notes/memo.txt
python scripts/idea_pipeline/ingest.py data/market/data.csv

# 자동 파서 선택: 확장자 기반
# --extract 옵션: LLM 인사이트 추출도 함께 실행
python scripts/idea_pipeline/ingest.py data/ask/file.xlsx --extract
```

---

## 7. Insight Extractor Design

### 7.1 LLM 기반 추출

```python
# backend/app/services/insight_extractor.py
class InsightExtractor:
    def __init__(self, api_key: str = None):
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None

    def extract(self, content: str, category: str) -> List[InsightResult]:
        """content에서 인사이트 추출"""
        if not self.client:
            return []  # API 키 없으면 빈 결과 (수동 입력 모드)

        prompt = f"""다음 투자 분석 내용에서 핵심 인사이트를 추출하세요.
카테고리: {category}

내용:
{content}

각 인사이트를 JSON으로 출력:
- type: "claim" (주장), "prediction" (예측), "pattern" (패턴)
- text: 인사이트 내용 (1~2문장)
- confidence: 확신도 (0.0~1.0)
- keywords: 관련 키워드 배열
"""
        # Anthropic API 호출 → JSON 파싱 → InsightResult 리스트
        ...
```

### 7.2 Fallback: 수동 입력

API 키 미설정 시 수동 입력 모드로 동작:
- API를 통해 직접 insight 등록 (POST `/api/v1/insights`)
- 또는 MCP Tool `create_idea_from_insights`로 직접 생성

---

## 8. Collaboration Protocol Document

### 8.1 파일 위치

```
data/collab/COLLAB_PROTOCOL.md
```

### 8.2 내용 구조

```markdown
# Stock Research ONE — AI 협업 프로토콜 v1.0

## 당신의 역할
당신은 Stock Research ONE 프로젝트의 투자 분석 협업 AI입니다.
다른 AI(Claude/Gemini/ChatGPT)와 Context Packet을 교환하여 분석을 교차검증합니다.

## Context Packet 형식
[JSON 스키마 포함]

## 협업 트리거 조건
1. 중요 투자 판단 시 → "교차검증을 위해 Context Packet을 생성하시겠습니까?"
2. 단방향 분석 시 → "반대 관점을 다른 AI에 요청하시겠습니까?"
3. 최신 데이터 필요 시 → "Gemini에서 실시간 데이터를 확인하시겠습니까?"
4. 아이디어 testing 진입 시 → "다른 AI에서 이 가설을 검증하시겠습니까?"

## 패킷 수신 시 행동
1. 패킷의 source_ai, topic, request_action 확인
2. request_action에 따라:
   - validate: 분석의 논리적 타당성 검증
   - extend: 추가 관점이나 데이터로 분석 확장
   - challenge: 의도적으로 반론 제시
   - synthesize: 여러 분석을 종합
3. 결과를 동일한 Context Packet 형식으로 출력

## 7개 분석 카테고리
[SECTOR, US_MARKET, THEME, RISK, NEXT_DAY, PORTFOLIO, AI_RESEARCH 설명]
```

### 8.3 AI별 주입 방법

| AI | 방법 | 자동화 |
|----|------|--------|
| Claude | MCP Resource `collab://protocol` 자동 로드 | 완전 자동 |
| Gemini | Gem 시스템 지시에 프로토콜 삽입 (1회) | 영구 자동 |
| ChatGPT | Custom GPT Instructions에 삽입 (1회) | 영구 자동 |

---

## 9. Gemini Idea 모델 확장 전략

### 기존 유지 (변경 없음)
- `backend/app/models/idea.py` — 컬럼 구조
- `backend/app/schemas/idea.py` — Pydantic 스키마
- `backend/app/api/ideas.py` — CRUD 5개 엔드포인트

### 확장 (추가)
- `idea.py` 모델에 `category`, `thesis` 컬럼 추가
- `idea.py` 스키마에 `IdeaStatus` enum 값 변경 (NEW→draft 등)
- `ideas.py` API에 `/stats`, `/{id}/evidence` 엔드포인트 추가
- `main.py`에는 이미 `ideas.router` 등록되어 있으므로 변경 불필요

---

## 10. Dashboard Design

### 10.1 idea_board.html

- 위치: `dashboard/idea_board.html`
- 패턴: 기존 `liquidity_stress.html`과 동일 (Static HTML + CDN React 18)
- 주요 컴포넌트:
  - **KanbanBoard**: 상태별 칸반 (draft / active / testing / validated)
  - **IdeaCard**: 제목, 카테고리 배지, 우선순위, 인사이트 수
  - **CategoryStats**: 카테고리별 아이디어 수 차트
  - **CollabStatus**: 미처리 패킷 알림

### 10.2 dashboard/index.html 링크 추가

시장 모니터링 섹션(또는 새 "아이디어" 섹션)에 추가:
```html
<a href="idea_board.html">아이디어 보드</a>
```

---

## 11. Implementation Order (상세)

### Phase 1: 핵심 기반 (MVP)

| # | 작업 | 파일 | 의존성 |
|---|------|------|--------|
| 1-1 | daily_work 모델 | `backend/app/models/daily_work.py` | - |
| 1-2 | insights 모델 | `backend/app/models/insight.py` | - |
| 1-3 | idea_evidence 모델 | `backend/app/models/idea_evidence.py` | - |
| 1-4 | ideas 모델 확장 | `backend/app/models/idea.py` (수정) | - |
| 1-5 | models/__init__.py에 등록 | `backend/app/models/__init__.py` (수정) | 1-1~1-4 |
| 1-6 | Pydantic 스키마 | `backend/app/schemas/daily_work.py`, `insight.py` (수정) | - |
| 1-7 | daily_work API | `backend/app/api/daily_work.py` | 1-1, 1-6 |
| 1-8 | insights API | `backend/app/api/insights.py` | 1-2, 1-6 |
| 1-9 | ideas API 확장 | `backend/app/api/ideas.py` (수정) | 1-3, 1-4 |
| 1-10 | main.py 라우터 등록 | `backend/app/main.py` (수정) | 1-7, 1-8 |
| 1-11 | Base Parser + Excel Parser | `scripts/idea_pipeline/parsers/` | - |
| 1-12 | 수집 CLI | `scripts/idea_pipeline/ingest.py` | 1-11 |
| 1-13 | Insight Extractor 서비스 | `backend/app/services/insight_extractor.py` | - |
| 1-14 | Excel 데이터 실제 수집 테스트 | - | 1-12, 1-7 |

### Phase 2: AI 협업

| # | 작업 | 파일 | 의존성 |
|---|------|------|--------|
| 2-1 | collab_packets, collab_sessions 모델 | `backend/app/models/collab.py` | - |
| 2-2 | Collab 스키마 | `backend/app/schemas/collab.py` | - |
| 2-3 | Collab API | `backend/app/api/collab.py` | 2-1, 2-2 |
| 2-4 | COLLAB_PROTOCOL.md | `data/collab/COLLAB_PROTOCOL.md` | - |
| 2-5 | MCP Server | `scripts/idea_pipeline/mcp_server.py` | 2-1, 2-4 |
| 2-6 | .claude/settings.json MCP 등록 | `.claude/settings.json` (수정) | 2-5 |
| 2-7 | Gemini Gem 생성 가이드 | `data/collab/GEMINI_GEM_SETUP.md` | 2-4 |
| 2-8 | ChatGPT GPT 생성 가이드 | `data/collab/CHATGPT_GPT_SETUP.md` | 2-4 |

### Phase 3: UI + 고급 기능

| # | 작업 | 파일 | 의존성 |
|---|------|------|--------|
| 3-1 | idea_board.html | `dashboard/idea_board.html` | Phase 1 완료 |
| 3-2 | index.html 링크 추가 | `dashboard/index.html` (수정) | 3-1 |
| 3-3 | idea_connections 모델 | `backend/app/models/idea_connection.py` | - |
| 3-4 | idea_outcomes 모델 | `backend/app/models/idea_outcome.py` | - |

---

## 12. File Map

| 파일 | 상태 | 설명 |
|------|------|------|
| `backend/app/models/daily_work.py` | 신규 | 원본 데이터 모델 |
| `backend/app/models/insight.py` | 신규 | 인사이트 모델 |
| `backend/app/models/idea_evidence.py` | 신규 | 연결 모델 |
| `backend/app/models/idea.py` | 수정 | category, thesis 추가 |
| `backend/app/models/collab.py` | 신규 | 협업 패킷/세션 모델 |
| `backend/app/models/__init__.py` | 수정 | 모델 등록 |
| `backend/app/schemas/daily_work.py` | 신규 | 스키마 |
| `backend/app/schemas/insight.py` | 신규 | 스키마 |
| `backend/app/schemas/idea.py` | 수정 | status enum 변경 |
| `backend/app/schemas/collab.py` | 신규 | 스키마 |
| `backend/app/api/daily_work.py` | 신규 | API 라우터 |
| `backend/app/api/insights.py` | 신규 | API 라우터 |
| `backend/app/api/ideas.py` | 수정 | 엔드포인트 추가 |
| `backend/app/api/collab.py` | 신규 | API 라우터 |
| `backend/app/main.py` | 수정 | 라우터 등록 |
| `backend/app/services/insight_extractor.py` | 신규 | LLM 추출 |
| `scripts/idea_pipeline/parsers/base_parser.py` | 신규 | 파서 인터페이스 |
| `scripts/idea_pipeline/parsers/excel_parser.py` | 신규 | Excel 파서 |
| `scripts/idea_pipeline/parsers/text_parser.py` | 신규 | Text 파서 |
| `scripts/idea_pipeline/ingest.py` | 신규 | 수집 CLI |
| `scripts/idea_pipeline/mcp_server.py` | 신규 | MCP Server |
| `data/collab/COLLAB_PROTOCOL.md` | 신규 | 협업 프로토콜 |
| `data/collab/GEMINI_GEM_SETUP.md` | 신규 | Gem 설정 가이드 |
| `data/collab/CHATGPT_GPT_SETUP.md` | 신규 | GPT 설정 가이드 |
| `dashboard/idea_board.html` | 신규 | 아이디어 보드 |
| `dashboard/index.html` | 수정 | 링크 추가 |
