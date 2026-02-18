# Development Log - 2026-02-18

## 작업: 엑셀 기준 소스 + DB 갱신 이력 반영 (REQ-015)

### 배경
- `data/국내상장종목 해자 투자가치.xlsx`를 정식 기준 소스로 유지.
- 대시보드는 기존 JSON 기반이었고, 종목 데이터 변경 이력이 DB에 남지 않던 상태.

### 변경 사항
1. DB 모델 추가
- `backend/app/models/moat_data.py`
  - `moat_stock_snapshot`: 종목 최신 스냅샷
  - `moat_stock_history`: 종목 변경 이력(INSERT/UPDATE/DEACTIVATE/REACTIVATE)
  - `moat_stock_sync_runs`: 동기화 실행 이력/집계

2. 대시보드 서비스 DB 우선화
- `backend/app/services/moat_dashboard_service.py`
  - DB(`moat_stock_snapshot`) 우선 조회
  - 데이터 없을 때 `data/moat_analysis_summary.json` fallback

3. 엑셀 동기화 스크립트 확장
- `scripts/moat_dashboard/extract_moat_data.py`
  - Excel 파싱 유지
  - DB 스냅샷 upsert + 이력 기록 + 비활성 처리
  - 기존 JSON 산출 유지(호환)

4. 회귀 테스트 추가
- `scripts/moat_dashboard/tests/test_moat_db_sync.py`
  - 최초 insert 시 스냅샷/히스토리 생성 검증
  - 재동기화 시 update/deactivate 이력 검증

### 메모
- 엑셀은 기준 소스, DB는 최신 상태 + 히스토리 저장소로 동작.
- 후속으로 배치 실행 시 sync run 카운트/이력으로 변경 추적 가능.

## 작업: 매일 19:00 변경감지 기반 자동 갱신 (REQ-016)

### 변경 사항
1. 변경감지 실행기 추가
- `scripts/moat_dashboard/scheduled_moat_sync.py`
  - 엑셀 파일 SHA-256/크기/mtime fingerprint 비교
  - 변경 없으면 skip, 변경 시 `extract_moat_data.extract()` 실행
  - 실행 상태를 `data/runtime/moat_sync_state.json`에 저장
  - 로그를 `data/runtime/logs/moat_sync_task.log`에 누적

2. 작업 스케줄러 등록/해제 스크립트 추가
- `scripts/dev/register_moat_sync_task.ps1`
- `scripts/dev/unregister_moat_sync_task.ps1`

3. 운영 문서 추가
- `docs/ops/moat-sync-scheduler.md`

4. 테스트 추가
- `scripts/moat_dashboard/tests/test_scheduled_moat_sync.py`
  - no-change skip
  - changed sync
  - monitoring blocked

5. 모니터링 계약 허용 prefix 확장
- `config/requirement_contracts.json`
  - `scripts.moat_dashboard` 추가

### 운영 적용 확인 (2026-02-19 00:15)
- Scheduled Task 등록 완료: `\Stock_Moat_DailySync_1900`
- Next Run Time: `2026-02-19 19:00:00`
- 수동 트리거 검증: `schtasks /Run` 후 `Last Result: 0` 확인
- 로그 경로
  - 상태 로그: `data/runtime/logs/moat_sync_task.log`
  - 표준출력 로그: `data/runtime/logs/moat_sync_stdout.log`

### 비고 파서/복구 조치 (2026-02-19 00:40)
- `parse_bigo`를 고정 2줄 방식에서 가변 줄(2/3/10+ lines) 파서로 교체.
- `moat_stock_snapshot`에 `bigo_raw` 컬럼 추가 및 자동 스키마 보정(ALTER TABLE) 적용.
- 전체 재동기화 실행: `run_id=5`, `updated=2507`, `unchanged=6`.
- 손실 케이스(효성중공업 298040) details 복구 확인 완료.
- 신규 종목 insert 시 Naver WICS 확인 로직 추가 (cache 우선, miss 시 fetch).
- WICS 확인값이 있으면 BM을 WICS로 정규화하여 스냅샷/히스토리에 저장.

## 작업: 메인 대시보드 프로젝트 현황 카드 + 클릭형 체크리스트 (REQ-017)

### 변경 사항
1. `dashboard/index.html`
- 우측 빈 영역을 채우는 `프로젝트 현황` 카드 추가.
- `PROJECT_STATUS_ITEMS` 데이터셋 기반으로 완료/진행중/예정 KPI 표시.
- 체크리스트 항목 클릭 시 세부 진행 체크, 다음 단계, 근거 파일 경로 표시.

2. 스타일/반응형
- 프로젝트 현황 패널 전용 스타일(`project-status-*`) 추가.
- 모바일에서 summary 2열, 상세 패널 1열로 자동 전환.

3. 요구사항 정합성 반영
- 카드 항목에 REQ-015/REQ-016/REQ-017과 QA 도구 계획 항목을 연결.
- 각 항목별 근거 경로를 명시해 진행 여부를 UI에서 확인 가능하도록 구성.

## Task: Dashboard black screen recovery (REQ-018)

### Root cause evidence
- Playwright pageerror at `http://localhost:8080/index.html`:
  - `Missing semicolon. (80:17)` caused by comment+code merged line: `// ... const apiService = {`
  - `Expected corresponding JSX closing tag for <span>. (109:20)` due to malformed closers like `/span>`
  - `Missing initializer in destructuring declaration. (445:17)` caused by comment+code merged line before `setTimeout`

### Fixes applied
1. Split merged comment/code lines into separate lines:
   - `const apiService = { ... }`
   - `setTimeout(() => { ... })`
   - `ReactDOM.render(...)`
2. Normalized malformed JSX closing tags (`/span>`, `/div>`, etc.) to proper `</...>`.
3. Re-verified with Playwright:
   - `status=200`, `pageerror_count=0`, `root_text_len=1826` (rendered)

### Residual note
- React 18 warning remains for `ReactDOM.render` deprecation, but it does not block rendering.

## Task: Global change guard enforcement (REQ-019)

### What was added
1. Unified guard script: `scripts/ci/check_global_change_guard.py`
- Detects changed files (CI PR base-aware + local fallback).
- Enforces mandatory docs update for source changes:
  - `REQUESTS.md`
  - `docs/development_log_YYYY-MM-DD.md`
- Executes dashboard integrity guard.
- Compiles changed Python files (`py_compile`).
- Executes monitoring entrypoint guard.

2. CI fail-closed integration
- `.github/workflows/consistency-monitoring-gate.yml`
- Added step: `Global change guard checklist (mandatory)`

3. Operations and local usage
- `docs/ops/global-change-guard.md`
- `scripts/dev/run_global_change_guard.ps1`

### Intent
- Make non-regression checklist mandatory for all modifications across sessions/models.
- Prevent accidental breakage of existing behavior before merge.

### Follow-up: runtime integrity mandatory for dashboard edits
- Added `scripts/ci/check_dashboard_runtime_integrity.py`.
- Wired into `scripts/ci/check_global_change_guard.py` (triggered when `dashboard/index.html` changes).
- Updated workflow to install Playwright Chromium and execute global guard in CI.
- Verified local pass:
  - `python scripts/ci/check_dashboard_runtime_integrity.py` -> PASS
  - `python scripts/ci/check_global_change_guard.py` -> PASS
## Task: REQ-017 dashboard project-status checklist panel reapply (2026-02-19)

### What was implemented
1. dashboard/index.html
- Added 프로젝트 현황 dashboard card.
- Added clickable sub-checklist panel with REQ-015/REQ-016/REQ-017 items.
- Clicking each item updates detail panel: current stage, checklist done/pending, next action.

2. 	ests/playwright/tests/dashboard-core.spec.ts
- Added regression assertions for:
  - 프로젝트 현황 text presence
  - card count threshold update
  - interactive click behavior (project-checklist-REQ-017, project-checklist-REQ-015)
  - detail panel text switching

3. scripts/ci/check_dashboard_runtime_integrity.py
- Added 프로젝트 현황 required text.
- Raised minimum dashboard card count from 7 to 8.

### Verification
- 
pm run test:dashboard --prefix tests/playwright -> PASS
- python scripts/ci/check_dashboard_runtime_integrity.py -> PASS
- python scripts/ci/check_global_change_guard.py -> PASS