# Feature Plan: Liquidity & Credit Stress Monitor

## 1. Overview
- **Feature Name**: liquidity-stress-monitor (유동성 및 신용 스트레스 모니터)
- **Level**: Dynamic (BaaS 불필요, API + DB + 단일 대시보드)
- **Priority**: High
- **Estimated Scope**: Backend API + Data Fetcher + Frontend Page + Dashboard 연동

## 2. Background & Motivation
ChatGPT 대화에서 설계된 "MGB Liquidity & Credit Stress Monitor" 컨셉을
Stock Research ONE 대시보드에 통합한다.

핵심 아이디어:
- 무료 API(FRED, Yahoo Finance, Google News RSS)로 유동성/크레딧 지표를 수집
- 6개 모듈(변동성, 크레딧 스프레드, 단기자금, 국채유동성, 뉴스, Fed 톤)을 종합
- MGB Liquidity Stress Index(0.0~1.0) 산출
- 대시보드 "시장 모니터링" 섹션에 링크 추가

## 3. Requirements

### 3.1 Functional Requirements
| ID | 요구사항 | 우선순위 |
|----|----------|----------|
| FR-01 | FRED API로 HY OAS, IG OAS, SOFR, 역리포잔고, 국채금리(2Y/10Y/30Y) 일별 수집 | Must |
| FR-02 | Yahoo Finance(requests+CSV)로 VIX, 주요 ETF(HYG, LQD, TLT, KRE, VNQ, SHV) 종가 수집 | Must |
| FR-03 | Google News RSS로 위기 키워드(margin call, liquidity crisis 등) 뉴스 카운트 수집 | Must |
| FR-04 | Fed 스피치 페이지에서 키워드 톤 분석 (liquidity, credit, stability 빈도) | Should |
| FR-05 | 6개 모듈 점수를 가중 평균하여 종합 Stress Index(0.0~1.0) 산출 | Must |
| FR-06 | `/api/v1/liquidity-stress` GET 엔드포인트: 최신 스트레스 데이터 반환 | Must |
| FR-07 | `/api/v1/liquidity-stress/history` GET 엔드포인트: 30일 히스토리 반환 | Must |
| FR-08 | `dashboard/liquidity_stress.html` 전용 모니터 페이지 구현 | Must |
| FR-09 | `dashboard/index.html` 시장모니터링 섹션에 "유동성 및 신용 스트레스" 링크 추가 | Must |
| FR-10 | 스트레스 등급별 색상: Normal(녹색), Watch(노란), Caution(주황), Stress(빨강), Crisis(진빨강) | Must |
| FR-11 | 시드 데이터 생성 스크립트로 데모 데이터 삽입 | Must |
| FR-12 | 모듈 바 및 KPI 카드 클릭 시 상세 팝업(DetailModal) 표시 | Must |
| FR-13 | 상세 팝업에 모듈별 30일 추이 미니 차트 표시 | Must |
| FR-14 | 상세 팝업 하단에 데이터 출처 참조 링크(FRED, Yahoo, Google News, Fed) 표시 | Must |
| FR-15 | 실제 데이터 수집: Yahoo Finance v8 chart API, Google News RSS, Fed RSS로 자동 수집 | Must |
| FR-16 | FRED API key 없이도 Yahoo/News/Fed 데이터로 부분 동작 | Should |

### 3.2 Non-Functional Requirements
- FRED API 키 미설정 시에도 시드 데이터로 화면 표시 가능
- 데이터 수집은 `scripts/` 하위에 독립 스크립트로 구현 (수동/스케줄러 실행)
- 기존 대시보드 코드에 최소 영향
- SQLite 호환 유지

## 4. Technical Approach

### 4.1 Backend
- **New DB Models**: `LiquidityMacro`, `LiquidityPrice`, `LiquidityNews`, `FedTone`, `StressIndex`
- **New API Router**: `backend/app/api/liquidity_stress.py`
- **New Service**: `backend/app/services/liquidity_stress_service.py`
- **Data Scripts**: `scripts/liquidity_monitor/` 하위에 수집 스크립트

### 4.2 Frontend
- **New Page**: `dashboard/liquidity_stress.html` (기존 `monitor_disclosures.html` 패턴 따름)
- **Dashboard Link**: `dashboard/index.html`의 시장 모니터링 섹션에 새 항목 추가
- **시각화**: Chart.js로 스트레스 인덱스 추이, 게이지 차트, 지표별 바 차트

### 4.3 Data Flow
```
FRED API / Yahoo Finance / Google News RSS / Fed Website
    ↓ (scripts/liquidity_monitor/*.py - 수동 또는 스케줄러)
SQLite DB (5 new tables)
    ↓ (FastAPI endpoints)
dashboard/liquidity_stress.html (Chart.js 시각화)
```

## 5. Success Criteria
- [x] 5개 DB 테이블 생성 및 시드 데이터 삽입
- [x] 2개 API 엔드포인트 정상 응답 (200 OK)
- [x] 스트레스 모니터 페이지에서 게이지 + 히스토리 차트 표시
- [x] 대시보드 시장 모니터링에서 링크 클릭 시 모니터 페이지 이동
- [x] 스트레스 등급(5단계) 색상 정상 표시
- [x] 모듈/KPI 클릭 시 DetailModal 팝업 표시
- [x] DetailModal에 30일 추이 미니 차트 + 데이터 출처 참조 링크
- [x] 실제 데이터 수집 (Yahoo v8 API, Google News RSS, Fed RSS)
- [ ] FRED API key 설정 후 전체 모듈 실제 데이터 검증

## 6. Out of Scope (이번 릴리스)
- 실시간 장중(intraday) 모니터링 (EOD 배치만 구현)
- 알람/Slack/Telegram 통지
- WebSocket 실시간 업데이트
- Power BI 연동
