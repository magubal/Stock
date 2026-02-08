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

## Key Conventions

- **Quality over file size**: Prioritize information completeness over reducing output size
- **Playwright over Selenium**: Use Playwright for browser automation (stability)
- **Blog data structure**: `data/naver_blog_data/YYYY-MM-DD/blogger_sequencenum.jpg`
- **Request tracking**: New feature requests must be registered in `REQUESTS.md` using the REQ-XXX format
- **Continuous improvement**: When no TODOs remain, reference `docs/investment-philosophy.md` to identify system gaps

## Environment Variables

Required keys (see `.env.example`):
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string
- `OPENAI_API_KEY` — OpenAI API access
- `ALPHA_VANTAGE_API_KEY` — Market data
- `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` — Celery/Redis config
- `SECRET_KEY` — Application secret
