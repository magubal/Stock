# Gap Analysis: disclosure-auto-collect (v2.0 Re-Run)

> **Analysis Type**: Gap Analysis (Design v2.0 vs Implementation)
>
> **Project**: Stock Research ONE
> **Date**: 2026-02-19 (Re-Run)
> **Design Doc**: [disclosure-auto-collect.design.md](../../02-design/features/disclosure-auto-collect.design.md)
> **Previous Analysis**: v1.0 (2026-02-19) -- Match Rate 75.0%

---

## Summary

Re-run of gap analysis after design document v2.0 update and UI fix. The design document was updated to formally specify the async background thread + polling pattern that the implementation uses, and the frontend toast rendering was fixed to distinguish `partial` status. All 12 comparison items now match between design and implementation.

Match Rate improved from **75.0% to 97.9%**. All 6 previously-PARTIAL items are now resolved. One minor CHANGED item remains (run_all uses `_bg()` variant instead of wrapper -- intentional and correct).

---

## Overall Scores

| Category | Score | Status |
|----------|:-----:|:------:|
| Design Match | 97.9% | PASS |
| Architecture Compliance | 100% | PASS |
| Convention Compliance | 95% | PASS |
| Error Handling | 100% (4/4) | PASS |
| Cross-Consistency | 100% (7/7) | PASS |
| **Overall** | **97.9%** | **PASS** |

---

## Changes Since v1.0 Analysis

### Design Document Updates (v1.0 -> v2.0)

| Section | Change |
|---------|--------|
| 2.1 | Replaced synchronous function spec with `_run_disclosure_collector_bg()` background function + `_run_disclosure_collector()` thread wrapper pattern |
| 2.2 | Changed `POST /disclosure` response from full result to `{"status": "accepted"}`; added `GET /disclosure/progress` polling endpoint specification |
| 2.4 | Added `collectStep`, `collectElapsed`, `pollRef` states and polling-based `handleCollect` logic |
| 4 (Implementation Order) | Added Step 4 for progress endpoint; restructured steps 1-2 for bg/wrapper split |
| 6 | API Response Format now specifies `POST` returns `"accepted"`, `GET /progress` returns running/completed/idle states with full result |
| 7.2 | Toast messages now include `partial` status distinction: "수집 부분 완료" |
| 7.3 | Toast auto-hide changed from 5s to 8s to match implementation |

### Implementation Fix

| File | Line | Change |
|------|------|--------|
| `dashboard/monitor_disclosures.html` | 1157 | Added `collectResult.status === 'partial' ? '수집 부분 완료' : '수집 완료'` conditional |

---

## Detailed Comparison (12 Items)

### 1. Backend: `_run_disclosure_collector_bg()` background function

- **Design** (Section 2.1): Background function that runs collect -> analyze with step state management (`"collecting"` / `"analyzing"` / `"done"`). Stores result in `_disclosure_task`.
- **Implementation** (`backend/app/api/collector.py` lines 185-251):
  - KST date calculation: `utc_now + timedelta(hours=9)` -- match
  - Step 1: `collect_all_pages(today)` with `generate_sample_data()` fallback -- match
  - Step 2: `analyze(today)` with `save_result()` -- match
  - Step state updates via `_disclosure_lock` -- match
  - Status calculation: `ok_count == 2` for success, `>0` for partial -- match
  - `_log_collection()` call -- match
  - Final result dict: `{collector, status, duration, date, steps}` -- match
  - Result stored in `_disclosure_task["result"]` with `_disclosure_lock` -- match
- **Status**: **MATCH**

### 2. Backend: `_run_disclosure_collector()` thread wrapper

- **Design** (Section 2.1): Wrapper that checks `already_running`, starts daemon thread with `_run_disclosure_collector_bg`, returns `{"status": "accepted"}` immediately. Uses `_disclosure_task` dict and `_disclosure_lock`.
- **Implementation** (`backend/app/api/collector.py` lines 180-270):
  - `_disclosure_task` dict at line 181: `{"running": False, "result": None, "step": "", "started_at": None}` -- match
  - `_disclosure_lock` at line 182: `threading.Lock()` -- match
  - `already_running` check at line 260-261: returns `{"status": "already_running", "step": ...}` -- match
  - Sets `running=True`, `started_at=time.time()` -- match
  - `threading.Thread(target=_run_disclosure_collector_bg, daemon=True).start()` at line 267-268 -- match
  - Returns `{"status": "accepted", "message": "수집이 시작되었습니다"}` at line 270 -- match
- **Status**: **MATCH**

### 3. Backend: `POST /disclosure` endpoint

- **Design** (Section 2.2): `async def collect_disclosure()` calls `_run_disclosure_collector()` (no `asyncio.to_thread` needed since wrapper is non-blocking). Returns `{"status": "accepted"}` immediately. Error handling with `HTTPException(500)`.
- **Implementation** (`backend/app/api/collector.py` lines 318-325):
  - Route: `@router.post("/disclosure")` -- match
  - Function: `async def collect_disclosure()` -- match
  - Calls `_run_disclosure_collector()` directly (no `await asyncio.to_thread`) -- match
  - Returns result (which is `{"status": "accepted"}`) -- match
  - Error handling: `HTTPException(status_code=500, detail=str(e))` -- match
- **Status**: **MATCH**

### 4. Backend: `GET /disclosure/progress` polling endpoint

- **Design** (Section 2.2): Polling endpoint that returns:
  - Running: `{"status": "running", "step": "collecting", "elapsed": 5.2}`
  - Completed: `{"status": "completed", "result": {...}}` (1-time consumption)
  - Idle: `{"status": "idle"}`
- **Implementation** (`backend/app/api/collector.py` lines 328-344):
  - Route: `@router.get("/disclosure/progress")` -- match
  - Function: `async def get_disclosure_progress()` -- match
  - Uses `_disclosure_lock` for thread safety -- match
  - Completed branch: checks `not running and result`, returns `{"status": "completed", "result": result}`, sets `result = None` (1-time consumption) -- match
  - Running branch: returns `{"status": "running", "step": ..., "elapsed": round(elapsed, 1)}` -- match
  - Idle branch: returns `{"status": "idle"}` -- match
- **Status**: **MATCH**

### 5. Backend: `_run_all_collectors()` modification

- **Design** (Section 2.3): Sequential execution of `_run_liquidity_collector()`, `_run_crypto_collector()`, `_run_disclosure_collector()` with status aggregation (`all_ok` / `any_ok`).
- **Implementation** (`backend/app/api/collector.py` lines 273-295):
  - Sequential execution of all three collectors -- match
  - Uses `_run_disclosure_collector_bg()` instead of `_run_disclosure_collector()` -- **intentional change**: `run-all` itself runs inside `asyncio.to_thread` at the endpoint level (line 351), so the synchronous `_bg()` variant is correct; using the thread-spawning wrapper would create unnecessary indirection
  - Status aggregation: `all_ok = all(r["status"] == "success")`, `any_ok = any(r["status"] != "failed")` -- match
  - Return dict: `{status, total_duration, collectors}` -- match
- **Status**: **CHANGED** (Low impact -- function variant differs from design text but is the architecturally correct choice for synchronous context)

### 6. Frontend CSS: btn-collect, spin, toast styles

- **Design** (Section 2.5): `.btn-collect` green gradient, `.btn-collect:hover`, `.btn-collecting` gray, `.spin` animation, `.collect-toast`, `.toast-success` green, `.toast-error` red.
- **Implementation** (`dashboard/monitor_disclosures.html` lines 116-152):
  - `.btn-collect`: `background: linear-gradient(135deg, #22c55e, #10b981); color: white; border: none` -- exact match
  - `.btn-collect:hover`: `linear-gradient(135deg, #16a34a, #059669)` + `translateY(-1px)` -- exact match
  - `.btn-collecting`: `background: #1e293b; color: #94a3b8; border: 1px solid #334155; cursor: wait` -- exact match
  - `.spin`: `animation: spin 1s linear infinite` -- exact match
  - `.collect-toast`: max-width 1400px, margin, padding, border-radius 6px -- exact match. Additional `cursor: pointer` (supports click-to-dismiss)
  - `.toast-success` / `.toast-error`: colors and borders -- exact match
- **Status**: **MATCH**

### 7. Frontend Header: collect button + toast markup

- **Design** (Section 2.4): Button in `header-actions` with class toggle, disabled state, icon toggle, text toggle. Toast below header with result message and "15:30 이후 수집을 권장합니다".
- **Implementation** (`dashboard/monitor_disclosures.html` lines 1114-1163):
  - Header component signature: `({ date, onCollect, collecting, collectStep, collectElapsed, collectResult, onDismissToast })` -- design specifies these props
  - Button placement in `header-actions` after "메인 대시보드" link -- match
  - Button class: `collecting ? 'btn-collecting' : 'btn-collect'` -- match
  - `disabled={collecting}` -- match
  - Icon: `data-lucide={collecting ? "loader" : "download"}` with `className={collecting ? "spin" : ""}` -- match
  - Text: Idle = "데이터 수집" (match), collecting = `collectStep || '수집 중...'` (match with step enhancement)
  - Elapsed time display: `{collecting && collectElapsed > 0 && <span>...초</span>}` at line 1141-1145 -- matches design Section 2.4 `collectElapsed` spec
  - Toast: success shows duration + steps.collect (match), partial shows "수집 부분 완료" (match), failed shows error (match)
  - "15:30 이후 수집 권장" text at line 1158-1160 -- match
  - Toast click-to-dismiss: `onClick={onDismissToast}` -- design mentions this implicitly in Section 7.3
- **Status**: **MATCH**

### 8. Frontend DisclosureMonitor: collecting state + handleCollect

- **Design** (Section 2.4): States `collecting`, `collectStep`, `collectElapsed`, `collectResult`. `handleCollect` does POST, checks for `accepted`/`already_running`, starts 3-second polling. Data reload on completion.
- **Implementation** (`dashboard/monitor_disclosures.html` lines 835-836, 944-1017):
  - States: `collecting` (line 835), `collectResult` (line 836), `collectStep` (line 945), `collectElapsed` (line 946), `pollRef` (line 947) -- match
  - `STEP_LABELS` map at line 944: `starting/collecting/analyzing/done` -- matches design step flow
  - `startPolling()` / `stopPolling()` with 3-second `setInterval` at line 953-985 -- match
  - Polling callback: checks `running` -> update step/elapsed, `completed` -> stop polling + set result + reload data, `idle` -> stop polling -- match
  - `handleCollect` at line 989-1017: POST to disclosure endpoint, check `accepted`/`already_running` -> startPolling, check `failed` -> set error -- match
  - Data reload with cache-bust `?t=Date.now()` at line 971 -- match
  - Cleanup on unmount: `useEffect(() => stopPolling, [])` at line 987 -- match
- **Status**: **MATCH**

### 9. Batch file: `scripts/run_daily_collect.bat`

- **Design** (Section 2.6): curl POST to `run-all`, fallback to direct Python scripts, echo timestamps.
- **Implementation** (`scripts/run_daily_collect.bat` lines 1-22):
  - Header comments with purpose description -- matches design comment style
  - `curl -s -X POST http://localhost:8000/api/v1/collector/run-all` at line 11 -- match
  - Output redirect: `-o "%~dp0collector_log_daily.txt"` vs design's `> "%~dp0\..\scripts\collector_log_daily.txt"` -- minor output path difference (implementation writes to scripts/ directly vs one level up then back to scripts/). Functionally equivalent.
  - Fallback: `python scripts/collect_disclosures.py` and `python scripts/analyze_disclosures.py` at lines 16-17 -- match
  - Timestamp echo at lines 8, 14 -- match
  - ELSE branch with success log at lines 19-21 -- positive addition
- **Status**: **MATCH**

### 10. API Response Format (Section 6)

- **Design** (Section 6):
  - `POST /disclosure`: `{"status": "accepted"}` or `{"status": "already_running", "step": "collecting"}` -- match
  - `GET /progress` running: `{"status": "running", "step": "collecting", "elapsed": 5.2}` -- match
  - `GET /progress` completed: `{"status": "completed", "result": {collector, status, duration, date, steps}}` with 1-time consumption -- match
  - `GET /progress` idle: `{"status": "idle"}` -- match
- **Implementation** (`backend/app/api/collector.py` lines 318-344):
  - All response formats match design Section 6 specification exactly
- **Status**: **MATCH**

### 11. Toast Messages (Section 7.2)

| Result | Design | Implementation (line 1155-1157) | Match |
|--------|--------|--------------------------------|:-----:|
| success | Green, "수집 완료 (Xs) -- success: N items" | `'수집 완료' (${duration}초) -- ${steps.collect}` | Yes |
| partial | Green, "수집 부분 완료 (Xs) -- ..." | `collectResult.status === 'partial' ? '수집 부분 완료' : '수집 완료'` | Yes |
| failed | Red, "수집 실패: 서버 오류" | `'수집 실패: ${error}'` | Yes |

- **Status**: **MATCH** -- The `partial` distinction was added in the UI fix. Line 1157 now correctly distinguishes partial from success.

### 12. Toast Auto-hide (Section 7.3)

- **Design** (Section 7.3): Success = 8 second auto-hide. Failed = manual click only.
- **Implementation** (`dashboard/monitor_disclosures.html` line 974):
  - Success: `setTimeout(() => setCollectResult(null), 8000)` -- **8 seconds, exact match**
  - Failed: No auto-hide timer. Toast has `onClick={onDismissToast}` for manual dismiss -- match
- **Status**: **MATCH**

---

## Error Handling Verification (Section 5)

| # | Scenario | Design | Implementation | Match |
|---|----------|--------|----------------|:-----:|
| 1 | Backend server down | fetch fails, toast-error "서버에 연결할 수 없습니다" | `catch(err)` at line 1012-1013: `{status:'failed', error: err.message \|\| '서버에 연결할 수 없습니다'}` | Yes |
| 2 | KIND access failure | `generate_sample_data()` fallback, steps.collect = "sample_fallback" | `_run_disclosure_collector_bg()` line 205-207: `generate_sample_data(today)` with `"sample_fallback: N items"` | Yes |
| 3 | Analyze failure | Collect data preserved, toast shows "분석 실패" | Independent try/except blocks. `steps["analyze"] = "failed: {e}"` at line 230 | Yes |
| 4 | Already collecting | Button disabled, no duplicate calls | Frontend: `if (collecting) return` (line 990) + `disabled={collecting}` (line 1134). Backend: `already_running` guard (line 260-261) | Yes |

**Error Handling: 4/4 (100%)**

---

## Extra Implementations (Positive Additions)

| # | Item | Location | Description |
|---|------|----------|-------------|
| E1 | `STEP_LABELS` map | monitor_disclosures.html:944 | Human-readable Korean step labels (시작 중/KIND 공시 수집 중/분석 중/완료) |
| E2 | Elapsed time display | monitor_disclosures.html:1141-1145 | Seconds counter shown next to button during collection |
| E3 | Toast click-to-dismiss | monitor_disclosures.html:1153-1154 | `onClick={onDismissToast}` allows manual dismissal on any toast status |
| E4 | Cache-bust on reload | monitor_disclosures.html:971 | `?t=Date.now()` query param prevents stale JSON cache |
| E5 | Batch ELSE branch | run_daily_collect.bat:19-21 | Success message logged when API call succeeds |
| E6 | Non-blocking POST error detail | monitor_disclosures.html:998-1003 | Parses HTTP error body for detailed error message before setting failed state |
| E7 | Idle polling recovery | monitor_disclosures.html:977-981 | Handles unexpected `idle` status during polling gracefully |
| E8 | Lucide re-init on state change | monitor_disclosures.html:976, 981, 1015 | `lucide.createIcons()` called after collecting state changes to refresh icons |

All 8 extra implementations are positive enhancements that improve reliability, UX, or observability.

---

## Cross-Consistency Check

| # | Check | Result |
|---|-------|--------|
| 1 | Endpoint URL: frontend `${API_BASE}/api/v1/collector/disclosure` matches backend `@router.post("/disclosure")` under prefix `/api/v1/collector` | PASS |
| 2 | Progress URL: frontend `${API_BASE}/api/v1/collector/disclosure/progress` matches backend `@router.get("/disclosure/progress")` | PASS |
| 3 | Button CSS: `.btn-collect`, `.btn-collecting`, `.spin` classes in `<style>` block match JSX class references | PASS |
| 4 | Toast CSS: `.collect-toast`, `.toast-success`, `.toast-error` classes in `<style>` block match JSX class references | PASS |
| 5 | `_run_all_collectors` uses `_run_disclosure_collector_bg()` (synchronous variant) since endpoint wraps with `asyncio.to_thread` | PASS |
| 6 | Batch file URL `http://localhost:8000/api/v1/collector/run-all` matches backend `@router.post("/run-all")` | PASS |
| 7 | Fallback scripts in batch (`collect_disclosures.py`, `analyze_disclosures.py`) match scripts loaded in `_run_disclosure_collector_bg()` | PASS |

**Cross-Consistency: 7/7 (100%)**

---

## Score Calculation

| # | Item | Status | Score |
|---|------|--------|:-----:|
| 1 | `_run_disclosure_collector_bg()` background function | MATCH | 1.0 |
| 2 | `_run_disclosure_collector()` thread wrapper | MATCH | 1.0 |
| 3 | `POST /disclosure` endpoint | MATCH | 1.0 |
| 4 | `GET /disclosure/progress` endpoint | MATCH | 1.0 |
| 5 | `_run_all_collectors()` modification | CHANGED (Low) | 0.75 |
| 6 | CSS styles | MATCH | 1.0 |
| 7 | Header button + toast markup | MATCH | 1.0 |
| 8 | DisclosureMonitor handleCollect + polling | MATCH | 1.0 |
| 9 | `run_daily_collect.bat` | MATCH | 1.0 |
| 10 | API Response Format | MATCH | 1.0 |
| 11 | Toast messages (partial distinction) | MATCH | 1.0 |
| 12 | Toast auto-hide timing (8s) | MATCH | 1.0 |
| **Total** | **11 MATCH + 1 CHANGED** | | **11.75 / 12** |

**Match Rate: 97.9% (PASS)**

---

## v1.0 vs v2.0 Comparison

| Item | v1.0 Status | v2.0 Status | Resolution |
|------|-------------|-------------|------------|
| 1. `_run_disclosure_collector()` | PARTIAL (0.5) | MATCH (1.0) | Design updated to specify bg+wrapper pattern |
| 2. `POST /disclosure` response | PARTIAL (0.5) | MATCH (1.0) | Design updated to specify "accepted" response |
| 3. `_run_all_collectors()` | MATCH (1.0) | CHANGED (0.75) | Reclassified: design says wrapper, impl uses `_bg()` variant (correct for sync context) |
| 4. `GET /disclosure/progress` | (not checked) | MATCH (1.0) | New item: design now specifies this endpoint |
| 5. CSS styles | MATCH (1.0) | MATCH (1.0) | No change |
| 6. Header button + toast | MATCH (1.0) | MATCH (1.0) | No change |
| 7. DisclosureMonitor handleCollect | PARTIAL (0.5) | MATCH (1.0) | Design updated to specify polling pattern |
| 8. API Response Format | PARTIAL (0.5) | MATCH (1.0) | Design updated to specify accepted+progress format |
| 9. `run_daily_collect.bat` | MATCH (1.0) | MATCH (1.0) | No change |
| 10. Button states | MATCH (1.0) | (merged into #7) | Consolidated into header comparison |
| 11. Toast messages | PARTIAL (0.5) | MATCH (1.0) | UI fix: added `partial` conditional |
| 12. Toast auto-hide | PARTIAL (0.5) | MATCH (1.0) | Design updated to 8s |
| **Score** | **9.0/12 (75.0%)** | **11.75/12 (97.9%)** | **+22.9pp** |

---

## Remaining Gap

### CHANGED Items (1)

| # | Item | Design | Implementation | Impact |
|---|------|--------|----------------|--------|
| 5 | `_run_all_collectors()` disclosure call | `_run_disclosure_collector()` (wrapper) | `_run_disclosure_collector_bg()` (direct sync) | Low |

**Root Cause**: The design text in Section 2.3 shows `result_disclosure = _run_disclosure_collector()` but the implementation correctly uses the `_bg()` synchronous variant because `_run_all_collectors()` already executes inside `asyncio.to_thread` at the endpoint level (line 351). Using the wrapper would unnecessarily spawn a second thread. This is an intentional architectural optimization.

**Recommendation**: Update design Section 2.3 line to `_run_disclosure_collector_bg()` with a comment explaining that run-all uses the synchronous variant. Impact is Low -- no functional difference.

---

## Files Analyzed

| File | Lines | Purpose |
|------|------:|---------|
| `f:\PSJ\AntigravityWorkPlace\Stock\Test_02\backend\app\api\collector.py` | 417 | Backend API (all endpoints + collector logic) |
| `f:\PSJ\AntigravityWorkPlace\Stock\Test_02\dashboard\monitor_disclosures.html` | 1171 | Frontend (React CDN dashboard) |
| `f:\PSJ\AntigravityWorkPlace\Stock\Test_02\scripts\run_daily_collect.bat` | 22 | Windows batch scheduler |

---

## Conclusion

The design document v2.0 update successfully aligned the specification with the async background thread + polling implementation pattern. The UI fix added the missing `partial` toast distinction. Match rate improved from 75.0% to 97.9%, well above the 90% threshold.

The single remaining CHANGED item (run-all using `_bg()` instead of wrapper) is an intentional optimization with no functional impact. This feature is ready for `/pdca report disclosure-auto-collect`.

---

## Version History

| Version | Date | Changes | Analyst |
|---------|------|---------|---------|
| 1.0 | 2026-02-19 | Initial analysis -- 75.0% match rate, 6 PARTIAL items due to sync vs async pattern | gap-detector |
| 2.0 | 2026-02-19 | Re-run after design v2.0 update + UI fix -- 97.9% match rate, all gaps resolved | gap-detector |
