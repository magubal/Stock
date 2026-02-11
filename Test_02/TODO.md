# TODO - Stock Research ONE

> ⚠️ **[세션 시작 전 필수]**
> 1. `AGENTS.md` (업무 연속성 정책) 필독
> 2. `docs/development_log_YYYY-MM-DD.md` (최신 로그) 확인
> 3. `REQUESTS.md` (요청 현황) 확인

> 마지막 업데이트: 2026-02-09 22:00 by Claude Sonnet 4.5

---

## 🔴 우선순위 높음 (Critical/High)

### Stock Research Dashboard - Phase 2: API Integration (PDCA Do Phase)

**상태**: Do 진행 중 | **PDCA**: `/pdca do stock-research-dashboard`
**설계**: `docs/02-design/features/stock-research-dashboard.design.md`

**Frontend (완료):**
- [x] SWR 설치 (`swr@^2.4.0`)
- [x] `lib/fetcher.js` (axios + SWR fetcher)
- [x] 6개 SWR hooks (`usePsychology`, `useTiming`, `usePortfolio`, `useEvaluation`, `useContextAnalysis`, `useFlywheel`)
- [x] Shared components (`DashboardCard`, `ErrorFallback`, `LoadingCard`)
- [x] `Dashboard.jsx` SWR 연동

**Backend (구현 완료 — 2026-02-11):**
- [x] Task 1: DB 모델 추가 — `PortfolioHolding`, `FlywheelState` (`backend/app/models/__init__.py`)
- [x] Task 2: Pydantic 스키마 추가 — Dashboard 전용 (`backend/app/schemas/__init__.py`)
- [x] Task 3: `DashboardService` 생성 (`backend/app/services/dashboard_service.py`)
  - `get_psychology_metrics()` — investor_sentiment 기반
  - `get_timing_analysis()` — sentiment + market_data 기반
  - `get_portfolio_overview()` — portfolio_holdings 기반
  - `get_company_evaluation()` — research_reports 기반
  - `get_flywheel_status()` — flywheel_state 기반
- [x] Task 4: Dashboard API 라우터 (`backend/app/api/dashboard.py`)
  - `GET /api/v1/psychology`
  - `GET /api/v1/timing`
  - `GET /api/v1/portfolio`
  - `GET /api/v1/evaluation`
  - `GET /api/v1/flywheel`
- [x] Task 5: `main.py` 라우터 활성화 (news + reports + dashboard + context_analysis)
- [x] Task 6: DB auto-create via `Base.metadata.create_all`
- [x] Task 7: Frontend ↔ Backend URL 매핑 검증 완료
- [ ] Task 8: Docker 기동 후 통합 테스트 (DB 연결 필요)

**참고:** `context_analysis` 라우터 임포트 수정 완료 및 활성화됨 (2026-02-11)

---

## 🟡 우선순위 중간

### 시스템 통합
- [ ] 자동화 스케줄러 테스트
- [ ] 텔레그램 Bot Token 설정
- [ ] 채널 ID 목록 설정

### 홍보 페이지
- [ ] 실시간 채팅 상담 버튼 완성
- [ ] 로그인/회원가입 모달 구현
- [ ] Demo 영상 섹션 추가
- [ ] 최종 QA 및 브라우저 테스트

---

## 🟢 우선순위 낮음

### 코드 정리
- [x] 임시 파일 정리 (temp_*.png, precise_temp_*.png)
- [ ] 스크립트 버전 통합 (중복 파일 정리)

---

## ✅ 완료됨

### 2026-02-11
- [x] Dashboard Backend: DB 모델 추가 (PortfolioHolding, FlywheelState)
- [x] Dashboard Backend: Pydantic 스키마 추가 (7개 응답 스키마)
- [x] Dashboard Backend: DashboardService 5개 메서드 구현
- [x] Dashboard Backend: API 라우터 5개 엔드포인트 구현
- [x] Dashboard Backend: main.py 라우터 활성화 (news, reports, dashboard)

### 2026-02-09
- [x] Evidence-Based Moat v2.0 완료 (PDCA archived, 95.2% match rate)
- [x] Stock Moat Estimator v1.0 완료 (PDCA archived, 98.4% match rate)
- [x] Dashboard Phase 1: Performance Optimization (React.memo, CSS 최적화)
- [x] Dashboard Frontend: SWR hooks + shared components 구현

### 2026-02-02
- [x] 전체 캡처 기능 구현
- [x] Playwright 기반 스크린샷
- [x] 일자별 폴더 자동 생성
- [x] 순번 자동 부여

### 2026-02-01
- [x] 홍보 랜딩페이지 (Hero, Features, Dashboard, Flywheel, Philosophy, Pricing, FAQ, CTA, Footer)
- [x] 텔레그램 데이터 수집 기능 구현

---

## 📝 다음 모델을 위한 노트

### 핵심 파일 위치
| 용도 | 파일 |
|------|------|
| Dashboard Plan | `docs/01-plan/features/stock-research-dashboard.plan.md` |
| Dashboard Design | `docs/02-design/features/stock-research-dashboard.design.md` |
| Frontend Dashboard | `frontend/src/components/Dashboard/Dashboard.jsx` |
| Frontend Hooks | `frontend/src/hooks/use*.js` (6개) |
| Backend Main | `backend/app/main.py` (라우터 주석 처리 상태) |
| Backend Models | `backend/app/models/__init__.py` |
| Backend Services | `backend/app/services/` |
| Backend API | `backend/app/api/` |
| 투자 철학 | `docs/investment-philosophy.md` |
| 아카이브 | `docs/archive/2026-02/` (moat v1, v2) |

### 현재 상태 요약
- **Frontend**: 준비 완료 (SWR hooks → Backend API 연동)
- **Backend**: Dashboard API 5개 엔드포인트 구현 완료, 라우터 활성화
- **다음 작업**: Docker 기동 후 통합 테스트 또는 Gap Analysis

### 결정 사항
- **품질 > 용량**: 정보 누락 방지 우선
- **Playwright 사용**: Selenium 대비 안정성
- **파일 구조**: `data/naver_blog_data/YYYY-MM-DD/블로거_순번.jpg`
