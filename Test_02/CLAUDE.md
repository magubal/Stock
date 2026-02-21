# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Stock Research ONE** — AI-based stock research automation platform implementing a 7-step flywheel investment decision system. The project is primarily in Korean.

## Session Startup (Required)

Before starting any work, read these files in order:
1. `TODO.md` — current task status and priorities
2. `AGENTS.md` — business continuity policy and agent context
3. `REQUESTS.md` — active feature requests
4. Latest `docs/development_log_YYYY-MM-DD.md` — most recent dev log

Previous technical decisions must not be rolled back without explicit user approval.

## Preservation Rule (기존 요건 보존 — 필수)

코드 수정/추가/변경 시 **반드시** 아래를 지킬 것:
1. **참조 프로그램 확인**: 동일/유사 기능의 기존 프로그램이 있으면 핵심 로직(필터, 검증, 기본값)을 먼저 파악
2. **기존 요건 보존**: 기존 필터/검증/기본값은 명시적 요청 없이 제거·변경 금지
3. **영향 범위 최소화**: 요청받은 변경 외의 코드는 건드리지 않음
4. **변경 내역 보고**: 변경 파일·내용을 명확하게 정리하여 보고

## Commands

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
API docs at http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev                    # Vite dev server
npm run build                  # tsc && vite build
npm run lint                   # ESLint
npm run lint:fix
```

### Docker (full stack)
```bash
docker-compose up -d
```
Starts: PostgreSQL (5432), Redis (6379), FastAPI (8000), Celery worker + beat, React (3000), Nginx (80/443)

### Data Collection Scripts
```bash
python scripts/naver_blog_collector.py       # Naver blog collector
python scripts/final_body_capture.py         # Blog body-only capture (Playwright)
python scripts/naver_blog_scheduler.py       # Daily scheduler
python scripts/continuity_check.py           # Business continuity check
python scripts/master_plan_analyzer.py       # Plan status analysis
scripts/run_collector.bat                    # Windows batch runner
```

### Tests
```bash
pytest backend/app/test_main.py
```

## Architecture

### Stack
- **Backend**: FastAPI (Python 3.11+), SQLAlchemy ORM, PostgreSQL, Redis, Celery
- **Frontend**: React 18 + TypeScript + Vite, Redux Toolkit, Tailwind CSS, Chart.js, Socket.io
- **Data collection**: Scrapy, Playwright (preferred over Selenium), BeautifulSoup
- **AI/NLP**: transformers, KoNLPy, scikit-learn, OpenAI API

### Backend Structure (`backend/app/`)
- `main.py` — FastAPI app entry point, CORS configured for localhost:3000
- `config.py` — Pydantic settings from environment variables
- `database.py` — SQLAlchemy engine and session setup
- `models/` — SQLAlchemy ORM models
- `schemas/` — Pydantic request/response schemas
- `api/` — FastAPI routers (news, reports, context_analysis). Currently commented out in main.py.
- `services/` — Business logic layer (news, reports, context analysis)
- `collectors/` — Data collection modules with abstract `BaseCollector`
- `tasks/` — Celery background tasks

### Frontend Structure (`frontend/src/`)
- `components/Dashboard/` — Main dashboard (Dashboard.jsx + Dashboard.css)
- `pages/` — Page-level components
- `store/` — Redux state management
- `index.js` — React entry point

### Other Key Directories
- `stock-research-one/` — Marketing landing page (static HTML/CSS)
- `scripts/` — Python automation and collection scripts
- `data/naver_blog_data/YYYY-MM-DD/` — Collected blog data organized by date
- `.agent/workflows/` — 7-step flywheel workflow definitions (01 through 07)
- `.agent/skills/` — Agent skill definitions (ui-ux-pro-max, data-collection, analysis, decision, research, brain)
- `docs/investment-philosophy.md` — Core investment philosophy document

## Custom Commands

- **`/brain <주제>`** — 브레인스토밍 워크플로우 실행
  - 사용자가 `/brain`, `brain`, `브레인스토밍` 뒤에 주제를 입력하면 `.agent/skills/brain/SKILL.md` 프로토콜을 실행한다.
  - 흐름: 문제 정의 → 제약 수집(1~3개 질문) → 대안 생성(2~4개) → 비교표 → 추천안 → Design Brief 출력 → `/pdca plan` handoff
  - 코드 작성 금지. 의사결정만 한다.
- **`/kill-port [ports]`** — 좀비 프로세스 포트 정리
  - 기본: 8000만 정리 (uvicorn 좀비가 주 원인) / `all`=8000+8080+3000
  - Python 기반 (`scripts/kill_port.py`) — AhnLab V3 오탐 회피
  - "port already in use" 에러 발생 시 사용

### Port Cleanup (Zombie Process)
```bash
python scripts/kill_port.py              # 기본: 8000만 (백엔드)
python scripts/kill_port.py all          # 전체: 8000+8080+3000
python scripts/kill_port.py 8000 3000    # 복수 포트 지정
```
VS Code: `Ctrl+Shift+P` → `Tasks: Run Task` → `kill-ports-all`

## Key Conventions

- **Implementation Guardian (MANDATORY)**: Always use `/00-implementation-guardian` to verify alignment with `*.plan.md` before requesting review.
  - Required for: finishing a phase, major code changes, refactoring.
  - Ensures: Implementation matches the approved design and success criteria.
- **Vercel React Best Practices (MANDATORY)**: Always use `/vercel-react-best-practices` skill for all React/Next.js code
  - Required for: writing new components, refactoring, code review, performance optimization
  - Ensures: React.memo usage, stable keys, CSS optimization, bundle size optimization
  - Apply proactively without being asked
- **Quality over file size**: Prioritize information completeness over reducing output size
- **Playwright over Selenium**: Use Playwright for browser automation (stability)
- **Blog data structure**: `data/naver_blog_data/YYYY-MM-DD/blogger_sequencenum.jpg`
- **Request tracking**: New feature requests must be registered in `REQUESTS.md` using the REQ-XXX format
- **Continuous improvement**: When no TODOs remain, reference `docs/investment-philosophy.md` to identify system gaps
- **DEMO Data Convention (MANDATORY)**: All seed/test/demo data must be clearly distinguishable from real data.
  - DB records: `source` field must be `"DEMO"` (not "Manual", "Test", etc.)
  - Collab packets: `source_ai` field must be `"DEMO"`
  - News headlines: prefix with `[DEMO]`
  - UI auto-detection: dashboards check `source==="DEMO"` and render red DEMO badge
  - Seed scripts: print `[SEED]` prefix in console output
  - Never mix demo and real data without clear distinction in the UI
- **PDCA Feature Registration (MANDATORY)**:
  - AI가 규칙을 skip해도 강제 등록 가능: `python scripts/pdca_auto_register.py`
  - 스크립트가 `.pdca-status.json`에서 planPath 없는 피처를 감지하여:
    1. 경량 Plan 자동 생성 (`docs/01-plan/features/PDCA-XXX_feature-name.plan.md`)
    2. `.pdca-status.json`에 planPath 등록
    3. `config/pdca_id_map.json`에 PDCA-XXX ID 할당
  - **REQUESTS.md는 대상이 아님** (REQ-XXX는 별도 체계, 다른 AI 인스턴스가 관리)
  - 사전 확인: `python scripts/pdca_auto_register.py --dry-run`
  - `project_status.py`가 `planPath` 기준으로 필터링하므로 planPath 누락 시 대시보드에서 보이지 않음
- **PDCA Document Naming Convention (MANDATORY)**:
  - 모든 PDCA 기획/설계/검증 문서를 새로 생성할 때는 **반드시** 파일명에 `PDCA-XXX_` 접두사를 붙여야 합니다. (예: `PDCA-026_resilient-blog-collector.plan.md`)
  - XXX 숫자 할당은 `config/pdca_id_map.json`을 확인하여 다음 숫자를 사용하고 업데이트합니다.

## Environment Variables

Required keys (see `.env.example`):
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string
- `OPENAI_API_KEY` — OpenAI API access
- `ALPHA_VANTAGE_API_KEY` — Market data
- `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` — Celery/Redis config
- `SECRET_KEY` — Application secret
