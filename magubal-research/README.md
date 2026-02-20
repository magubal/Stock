# Magubal Research Platform

마구티어 플라이휠 기반 Stock Research 플랫폼

## Quick Start

```bash
# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python run.py
```

브라우저에서 `http://localhost:5000` 접속

## Architecture

```
magubal-research/
├── app/
│   ├── __init__.py       # Flask App Factory
│   ├── config.py         # Configuration
│   ├── models/           # Data Models
│   ├── services/         # Skill-based Services
│   │   ├── data_collection.py
│   │   ├── analysis.py
│   │   ├── decision.py
│   │   └── research.py
│   └── api/              # REST API
│       ├── stock.py
│       ├── news.py
│       └── flywheel.py
├── static/               # Frontend Assets
├── templates/            # HTML Templates
└── run.py               # Entry Point
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check |
| `GET /api/flywheel/stages` | Flywheel 7 stages |
| `GET /api/stock/<symbol>` | Stock price data |
| `GET /api/data/news/<symbol>` | Stock news |
| `GET /api/data/market-issues` | Market issues |
| `POST /api/decision/scenario` | Create scenarios |
| `GET /api/research/company/<symbol>` | Company analysis |
