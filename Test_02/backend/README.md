# Stock Research ONE - 백엔드

## 프로젝트 개요
AI 기반 주식 리서치 자동화 솔루션의 백엔드 서비스

## 기술 스택
- **Framework**: FastAPI
- **Database**: PostgreSQL + Redis (캐시)
- **Message Queue**: Celery + Redis
- **Web Scraping**: Scrapy, Selenium, BeautifulSoup4
- **Financial Data**: Yahoo Finance, Alpha Vantage, Naver Finance API
- **NLP**: KoNLPy, transformers, OpenAI API
- **WebSocket**: FastAPI WebSocket

## 프로젝트 구조
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 앱 엔트리포인트
│   ├── config.py              # 환경 설정
│   ├── database.py            # 데이터베이스 연결
│   ├── models/                # SQLAlchemy 모델
│   ├── schemas/               # Pydantic 스키마
│   ├── api/                   # API 라우터
│   ├── services/              # 비즈니스 로직
│   ├── collectors/            # 데이터 수집기
│   ├── analyzers/             # 분석 엔진
│   └── utils/                 # 유틸리티 함수
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## 데이터 수집 소스
1. **뉴스**: 연합뉴스, 이데일리, 한국경제, 매일경제
2. **증권사 리포트**: 각 증권사 PDF/HTML 리포트
3. **텔레그램**: 주식 관련 채널 메시지
4. **블로그/커뮤니티**: 네이버 블로그, 티스토리
5. **시장 데이터**: 코스피/코스닥 실시간 시세