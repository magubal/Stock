# Stock Research ONE - 대시보드

## 🎯 개요
Stock Research ONE의 데이터 수집 및 분석 결과를 시각화하는 대시보드

## 🚀 빠른 시작

### 자동 실행 (권장)
```bash
python scripts/run_dashboard.py
```

### 수동 실행

#### 1. 백엔드 시작
```bash
cd backend

# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 서버 시작
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. 프론트엔드 시작
```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 시작
npm start
```

## 🌐 접속 정보

- **대시보드**: http://localhost:3000
- **API 서버**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

## 📊 대시보드 기능

### 1. 투자자 심리 분석
- 시장 과열도 (35%)
- 투자자 공감도 (72%)
- 기대감 레벨 (58%)
- 투자자 유형별 심리 현황

### 2. 투자 타이밍 분석
- 3개월/6개월/1년별 투자 적합성 평가
- 기대요소 vs 우려요소 분석

### 3. 중장기 포트폴리오
- 보유 종목: 12개
- 평균 수익률: +24.8%
- 매도 신호: 3개
- 가격부담/변동성 알림

### 4. 기업 평가 워크스페이스
- 고객가치제안 평가 체크리스트
- 산업 평가 (빅트렌드 부합도 85%)

### 5. 맥락 연결 분석기
- 뉴스 → 투자심리 → 행동 예측 흐름
- 최신 이슈 및 영향 분석

### 6. 플라이휘 실행 현황
- 7단계 진행 상황 (4/7단계 진행 중)
- 각 단계별 완료 상태

## 🛠️ 기술 스택

### Frontend
- **React 18** - 컴포넌트 기반 UI
- **Lucide React** - 아이콘 라이브러리
- **CSS Grid** - 반응형 레이아웃
- **CSS Variables** - 테마 시스템

### Backend
- **FastAPI** - API 서버
- **PostgreSQL** - 데이터 저장소
- **Celery** - 백그라운드 작업

## 🎨 디자인 시스템

### 컬러 팔레트
- **Primary**: #22c55e (연두색)
- **Background**: #0a0a0a (다크 모드)
- **Surface**: #1a1a2e (카드 배경)
- **Text**: #ffffff (주 텍스트)
- **Muted**: #94a3b8 (보조 텍스트)

### 컴포넌트 구조
```
Dashboard/
├── Dashboard.jsx           # 메인 대시보드
├── Dashboard.css           # 스타일링
├── PsychologyMetrics.jsx   # 투자자 심리
├── TimingAnalysis.jsx     # 투자 타이밍
├── PortfolioOverview.jsx  # 포트폴리오
├── CompanyEvaluation.jsx  # 기업 평가
├── ContextAnalyzer.jsx    # 맥락 분석
└── FlywheelStatus.jsx     # 플라이휘 현황
```

## 📱 반응형 디자인

- **Desktop**: 2열 그리드 레이아웃
- **Tablet**: 1열 레이아웃
- **Mobile**: 단일 컬럼 레이아웃

## 🔧 API 연동

대시보드는 다음 API 엔드포인트와 연동됩니다:

```javascript
// 뉴스 데이터
GET /api/v1/news/dashboard/summary

// 리포트 데이터  
GET /api/v1/reports/dashboard/summary

// 데이터 수집 트리거
POST /api/v1/news/collect
POST /api/v1/reports/collect
```

## 📈 데이터 흐름

1. **데이터 수집**: 뉴스/리포트 → 데이터베이스
2. **데이터 처리**: 감성분석/중요도평가 → 저장
3. **데이터 시각화**: API → React 컴포넌트 → 차트/지표

## 🔄 실시간 업데이트

- **WebSocket**: 준비 중 (실시간 알림)
- **주기적 새로고침**: 1분 간격 자동 데이터 갱신
- **수동 새로고침**: 버튼 클릭으로 즉시 업데이트

## 🎯 다음 단계

1. **WebSocket 실시간 연동**
2. **차트 라이브러리 통합** (Chart.js)
3. **사용자 인증 시스템**
4. **개인화 대시보드**
5. **모바일 앱 버전**