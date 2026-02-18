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
- `.agent/skills/` — Agent skill definitions (ui-ux-pro-max, data-collection, analysis, decision, research)
- `docs/investment-philosophy.md` — Core investment philosophy document

## Custom Commands

- **`/brain <주제>`** — 브레인스토밍 워크플로우 실행
  - 사용자가 `/brain`, `brain`, `브레인스토밍` 뒤에 주제를 입력하면 `.agent/skills/brainstorm-bkit/SKILL.md` 프로토콜을 실행한다.
  - 흐름: 문제 정의 → 제약 수집(1~3개 질문) → 대안 생성(2~4개) → 비교표 → 추천안 → Design Brief 출력 → `/pdca plan` handoff
  - 코드 작성 금지. 의사결정만 한다.

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

## Environment Variables

Required keys (see `.env.example`):
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string
- `OPENAI_API_KEY` — OpenAI API access
- `ALPHA_VANTAGE_API_KEY` — Market data
- `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` — Celery/Redis config
- `SECRET_KEY` — Application secret
