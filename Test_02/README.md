# Stock Research ONE - 전체 프로젝트

> 🛑 **[AI 모델 필수 지침]**
> 작업을 시작하기 전에 반드시 **`TODO.md`**를 가장 먼저 읽으십시오.
> `TODO.md` 상단에 **세션 시작 체크리스트**와 **업무 연속성 정책**이 정의되어 있습니다.
> `TODO.md` 상단에 **세션 시작 체크리스트**와 **업무 연속성 정책**이 정의되어 있습니다.
> 이를 따르지 않을 경우 작업 컨텍스트가 손실될 수 있습니다.
> **[필수] 터미널 명령어(Git, 빌드 등) 실행 후에는 반드시 `.agent/skills/terminal-best-practices/SKILL.md`를 참고하여 `command_status`로 결과를 검증하십시오.**

---


## 🎯 프로젝트 목표
AI 기반 주식 리서치 자동화 솔루션으로, 7단계 플라이휠 시스템을 구현하여 체계적인 투자 의사결정을 지원

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   데이터 소스    │    │   데이터 수집    │    │   분석 엔진     │
│                │    │                 │    │                │
│ • 뉴스 사이트    │───▶│ • Scrapy       │───▶│ • NLP 분석      │
│ • 증권사 리포트  │    │ • Selenium     │    │ • 심리 분석     │
│ • 텔레그램 채널  │    │ • API 연동      │    │ • 시나리오 생성  │
│ • 시장 데이터    │    │                 │    │                │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   프론트엔드     │    │   백엔드 API    │    │   데이터베이스   │
│                │    │                 │    │                │
│ • React 대시보드│◀───│ • FastAPI       │◀───│ • PostgreSQL    │
│ • 실시간 차트    │    │ • WebSocket     │    │ • Redis 캐시    │
│ • 알림 시스템    │    │ • 배치 작업      │    │ • Time-series   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📊 7단계 플라이휠 구현

1. **데이터 수집** - 뉴스, 보고서, 소셜 미디어 자동 수집
2. **맥락 분석** - 투자자 심리와 데이터 연결
3. **중요도 평가** - 영향력 및 우선순위 자동 결정
4. **시나리오 작성** - 행동 계획 및 리스크 관리
5. **실질 확인** - 시세 및 실제 행동 모니터링
6. **결과 복기** - 성과 분석 및 개선점 도출
7. **트렌드 정리** - 인사이트 축적 및 지식 베이스

## 🛠️ 기술 스택

### 백엔드
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + Redis
- **Queue**: Celery + Redis
- **ML/AI**: transformers, KoNLPy, scikit-learn

### 프론트엔드
- **Framework**: React 18 + TypeScript
- **State**: Redux Toolkit
- **UI**: Tailwind CSS + Chart.js
- **Real-time**: Socket.io

### 인프라
- **Containerization**: Docker + Docker Compose
- **Deployment**: Nginx + Gunicorn
- **Monitoring**: Prometheus + Grafana

## 📁 프로젝트 구조

```
stock-research-one/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── collectors/      # 데이터 수집기
│   │   ├── analyzers/       # 분석 엔진
│   │   ├── api/            # API 라우터
│   │   └── models/         # 데이터 모델
│   └── tests/              # 백엔드 테스트
├── frontend/               # React 프론트엔드
│   ├── src/
│   │   ├── components/     # 컴포넌트
│   │   ├── pages/         # 페이지
│   │   └── store/         # 상태 관리
│   └── public/            # 정적 리소스
├── docs/                  # 문서
├── scripts/               # 배치 스크립트
└── docker-compose.yml     # 개발 환경 설정
```

## 🚀 시작하기

### 개발 환경 설정
```bash
# 클론 후
cd stock-research-one

# 백엔드 설정
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 프론트엔드 설정
cd ../frontend
npm install
npm run dev
```

### Docker로 시작
```bash
docker-compose up -d
```

## 📋 현재 상태 (2026-02-01 업데이트)

### ✅ 완료된 작업
- **홍보 랜딩페이지** (`stock-research-one/`)
  - `index.html` - 메인 페이지 (Hero, Features, Dashboard, Flywheel, Philosophy, Pricing, CTA, Footer)
  - `styles.css` - Dark Mode OLED 테마, IBM Plex Sans 폰트
- **투자자 심리 분석 대시보드** 섹션 추가
  - 투자자 심리 지표 (시장 과열도, 공감도, 기대감)
  - 투자 타이밍 분석 (3개월/6개월/1년)
  - 기업 평가 워크스페이스 (고객가치제안, 산업 평가)
  - 중장기 포트폴리오 (보유종목, 수익률, 매도 신호)
  - 맥락 연결 분석기 (뉴스→심리→행동 흐름)
  - 플라이휠 실행 현황 (7단계 진행 상태)
- **프로젝트 컨텍스트** 설정
  - `AGENTS.md` - AI 에이전트 컨텍스트
  - `docs/investment-philosophy.md` - 투자 운용철학
  - `.agent/workflows/` - 7단계 플라이휠 워크플로우

### 🔄 진행 중
- 데이터 수집 모듈 개발

### ⏳ 예정
- 백엔드 API 설계
- 프론트엔드 대시보드 (React 구현)
- AI 분석 엔진 통합

---

## 🖥️ 로컬 서버 실행

```bash
# 홍보 페이지 미리보기
cd stock-research-one
npx serve -l 3000
# http://localhost:3000 에서 확인
```

---

## 📝 다음 작업 가이드

다음에 작업을 이어서 할 때:
1. `stock-research-one/index.html` 열기
2. 현재 대시보드 섹션 확인
3. 필요한 기능 추가/수정

**마지막 수정 파일**: `index.html`, `styles.css` (대시보드 섹션 추가)