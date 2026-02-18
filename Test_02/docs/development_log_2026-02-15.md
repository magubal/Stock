# Development Log - 2026-02-15

## Session Goal
- Stabilize Idea Board text/encoding behavior and remove masking policy.
- Enforce "raw data visibility first" for `???`-like strings.
- Validate API/UI flow with a real sample registration.
- Leave handoff notes so next model (including Claude) can continue immediately.

## Key Decisions (Policy)
1. Raw information must not be hidden in UI/API, even if text looks broken.
2. Root-cause fixing is preferred over symptom masking.
3. Work scope remains `Test_02` only.

## Completed Changes
1. Raw-text policy applied to backend API
- File: `backend/app/api/collab.py`
- Updated action/packet-type Korean labels.
- Removed masking behavior that replaced/suppressed `???`-like values.
- Kept safe mojibake repair attempt, but preserve original when not repairable.
- Added inline policy comment for future maintainers.

2. Raw-text policy applied to frontend display
- File: `frontend/src/pages/IdeaBoard.jsx`
- Removed fallback masking for suspicious text patterns.
- Display now preserves raw strings (including `???`) for traceability.
- Added inline policy comment.

3. Test expectation aligned with policy
- File: `backend/tests/test_collab_triage.py`
- Renamed/updated test to verify garbled packet type is preserved (not auto-fallback).

4. Backend startup stability fix
- File: `backend/app/config.py`
- Added `model_config = SettingsConfigDict(env_file=".env", extra="ignore")`
- Prevents crash when unrelated `.env` keys (e.g., `ORACLE_*`) exist.

5. Handoff policy note updated
- File: `docs/handoffs/2026-02-15-codex-fix-summary.md`
- Appended explicit policy update section.

## Runtime Verification
1. Backend compile
- `python -m py_compile backend/app/api/collab.py backend/app/config.py`
- Result: PASS

2. Frontend build
- `npx vite build` (in `frontend`)
- Result: PASS

3. API tests
- `backend\\venv\\Scripts\\python.exe -m unittest discover -s backend/tests -p "test_collab_triage.py" -v`
- Result: PASS (5 tests)

4. Live API smoke (port 8001)
- Created packet with `packet_type="???"`, `request_ask="timeline ??? ??"`.
- Confirmed inbox/history API returns raw values without masking.

## Data Registration (User Request)
Request: register ECOPro BM/moat/investment-value idea + industry packet.

Final valid records:
- Idea ID: `5`
- Idea title: `Ecopro BM (247540) BM/moat/investment-value check` (Korean title in DB for this row)
- Packet ID: `pkt-ecoprobm-20260215-183233-k`
- Packet topic: `Ecopro BM industry outlook idea packet` (Korean topic in DB for this row)
- Related idea: `5`
- Packet status: `pending`

Note:
- Earlier attempt produced corrupted values due terminal input encoding:
  - Idea ID: `4`
  - Packet ID: `pkt-ecoprobm-20260215-183140`
- Kept as-is per raw-data policy unless user requests cleanup.

## Ops Notes For Next Session
1. Active backend expected at `http://127.0.0.1:8001`.
2. If text appears stale in browser, hard refresh (`Ctrl+F5`).
3. If backend fails after `.env` changes, check `backend/app/config.py` extra-ignore setting first.

## Safety / Scope Record
- All changes made under `f:\PSJ\AntigravityWorkPlace\Stock\Test_02`.
- No destructive commands used (`del /s`, `Remove-Item -Recurse -Force`, `git reset --hard` not used).

## Session Update (Collab x Stock Pipeline Integration)
1. Added stock-pipeline bridge in triage API
- File: `backend/app/api/collab.py`
- `triage` now can run stock analysis (`analyze_with_evidence`) for stock packets and map result fields into triage payload.
- Added stock target resolver (`ticker/name`) from request + packet text.

2. Added idea auto-registration gate for stock packets
- File: `backend/app/api/collab.py`
- Stock packets no longer auto-create ideas unconditionally.
- Gate checks industry outlook / summary-evidence / confidence-or-consensus / final comment.
- Added `force_create_idea` override and `idea_gate_blocked` history event.

3. Extended collab schema for bridge/gate
- File: `backend/app/schemas/collab.py`
- New request fields:
  - `run_stock_pipeline`, `stock_ticker`, `stock_name`, `stock_year`
  - `force_create_idea`
- New response field:
  - `idea_gate` (`should_create`, `reasons`)

4. Updated frontend triage payload support
- File: `frontend/src/pages/IdeaBoard.jsx`
- Sends bridge/gate fields to triage API.
- Shows packet error message when idea creation is blocked by gate.

5. Added regression tests
- File: `backend/tests/test_collab_triage.py`
- Added tests for:
  - stock pipeline enrichment path
  - stock idea gate block path
  - force override path
  - stock pipeline attempt history event (`stock_pipeline_attempted`)

## Verification (Collab x Stock)
1. Targeted new tests
- Command:
  - `backend\\venv\\Scripts\\python.exe -m unittest backend.tests.test_collab_triage.CollabTriageApiTests.test_stock_packet_triage_enriches_from_stock_pipeline_and_creates_idea backend.tests.test_collab_triage.CollabTriageApiTests.test_stock_packet_idea_registration_is_blocked_without_industry_outlook backend.tests.test_collab_triage.CollabTriageApiTests.test_stock_packet_force_create_idea_overrides_gate -v`
- Result: PASS

2. Full collab triage tests
- Command:
  - `backend\\venv\\Scripts\\python.exe -m unittest discover -s backend/tests -p "test_collab_triage.py" -v`
- Result: PASS (8 tests)

## Traceability Update (Claude attempt check)
- Added packet history event `stock_pipeline_attempted` during triage when stock pipeline run is requested/auto-detected.
- Event note stores JSON fields for post-check:
  - `source_ai`, `requested`, `executed`, `ticker`, `name`, `error`
- This allows explicit verification whether Claude-requested packet attempted stock pipeline execution.
- IdeaBoard history UI now labels and formats this event for quick reading:
  - `stock_pipeline_attempted` -> `파이프라인시도`
  - note preview example: `source:claude | requested:Y | executed:Y | 삼성전자(005930)`

## Consistency Fix (Stock packet misclassified as SECTOR)
- Observed issue:
  - Claude-exported stock evaluation packet used `category=SECTOR` (example packet: `93977025-8a5b-443e-8b60-bc08a2b1420b`), which could bypass stock-specific gate if only category/packet_type were trusted.
  - MCP `export_packet` path writes DB directly, so API normalization/history behavior was partially skipped.
- Fixes:
  1. `backend/app/api/collab.py`
     - Added stock-like context detector (`ticker + stock-eval keywords`) so stock gate/pipeline still applies even if category is mislabeled.
     - Added regression test scenario for stock-like `SECTOR` packet.
  2. `scripts/idea_pipeline/mcp_server.py`
     - `export_packet` now auto-normalizes stock-like packet to `PORTFOLIO` + `packet_type=종목`.
     - Added history row on export (`event_type=created`) for traceability.
     - Export response now returns normalized `category` and `packet_type`.
- Verification:
  - `backend/tests/test_collab_triage.py` PASS (9 tests)
  - `python -m py_compile backend/app/api/collab.py scripts/idea_pipeline/mcp_server.py backend/app/schemas/collab.py` PASS

## Planning Update (Global Monitoring Guard)
- User confirmed project-level expansion (not collab-only) for consistency monitoring.
- Confirmed policy:
  - hard-block on violation
  - batch continues by isolating violating item
  - reconfirm approver fixed to Codex
  - incident queue stored in DB
  - phase-1: DB/API first, UI later
- Added design + implementation plan docs:
  - `docs/plans/2026-02-15-global-monitoring-guard-design.md`
  - `docs/plans/2026-02-15-global-monitoring-guard-implementation.md`
- REQUESTS updated with `REQ-007`.

3. Python compile check
- Command:
  - `python -m py_compile backend/app/api/collab.py backend/app/schemas/collab.py`
- Result: PASS

4. Frontend build
- Command:
  - `npm run build` (in `frontend`)
- Result: FAIL (existing TypeScript/tsconfig invocation issue in this environment; not introduced by this change)

## Session Update (Monitoring Guard Stabilization)
- Scope: finalize global monitoring hard-block path and script bridge consistency.

### Code changes
1. `scripts/idea_pipeline/mcp_server.py`
- Fixed runtime import mismatch (`CollabPacketHistory` now imported where used).
- Added `monitoring_adapter.enforce_monitoring(...)` call in `export_packet`.
- Export now returns explicit `status=blocked` payload with `incident_id/rule_code/reasons` when monitor guard blocks.

2. `backend/app/api/monitoring.py`
- Enforced approver policy at API layer: `decider` must be `codex`.
- Non-codex decider now returns HTTP 400 (`decider_must_be_codex`).

3. `scripts/stock_moat/batch_moat_value.py`
- Integrated monitor guard call per-row.
- On monitor block, row is isolated and marked `MONITOR_BLOCK` and batch continues (no whole-batch stop).

4. Tests
- Updated `backend/tests/test_collab_triage.py` for hard-block behavior (409 expected in gate-bypass/misclassification scenarios).
- Added `backend/tests/test_monitoring_guard.py` covering:
  - rule evaluation,
  - service block/pass recording,
  - monitoring API incident list/approve,
  - non-codex decider rejection.

### Verification
- Compile:
  - `python -m py_compile scripts/idea_pipeline/mcp_server.py scripts/idea_pipeline/monitoring_adapter.py scripts/stock_moat/batch_moat_value.py backend/app/api/monitoring.py backend/tests/test_collab_triage.py backend/tests/test_monitoring_guard.py` -> PASS
- Tests:
  - `backend\\venv\\Scripts\\python.exe -m unittest discover -s backend/tests -p "test_collab_triage.py" -v` -> PASS (9 tests)
  - `backend\\venv\\Scripts\\python.exe -m unittest discover -s backend/tests -p "test_monitoring_guard.py" -v` -> PASS (6 tests)
- Runtime spot-check:
  - `mcp_server.export_packet(...)` verified with mocked `FastMCP` in venv -> `status=exported`, `category=PORTFOLIO`, `packet_type=종목`.

## Session Update (REQ Contract Enforcement)
- User request: monitoring should control requirement references during new-program development, not only runtime stock rules.

### Implemented
1. Added machine-readable requirement contract schema
- `config/requirement_contracts.json`
- Contract key `REQ-007` with required fields:
  - req_id, source_path, entity_type, entity_id, design_refs, test_tags
  - traceability_ok must be truthy
  - allowed source prefixes and required design refs/test tag

2. Added requirement contract validator service
- `backend/app/services/requirement_contract_service.py`
- Supports:
  - contract file load
  - req_id lookup
  - contract mismatch evaluation
  - violation outputs: `requirement_contract_missing` / `requirement_contract_mismatch`

3. Integrated contract check into monitoring rule engine
- `backend/app/services/monitoring_rules.py`
- New context flag: `enforce_requirement_contract`
- When enabled, contract violations are appended to blocking violations.

4. Applied context injection on current critical paths
- `backend/app/api/collab.py` (triage monitor ctx)
- `scripts/idea_pipeline/mcp_server.py` (export_packet monitor ctx)
- `scripts/stock_moat/batch_moat_value.py` (per-row monitor ctx)
- Added `req_id=REQ-007`, design refs, test tags, and contract enforcement flag.

5. Strengthened default adapter behavior for future programs
- `scripts/idea_pipeline/monitoring_adapter.py`
- Default-injects:
  - req_id=REQ-007
  - enforce_requirement_contract=True
  - design_refs/test_tags defaults

6. Tests
- Extended `backend/tests/test_monitoring_guard.py` with contract-specific cases:
  - missing req_id -> violation
  - missing design refs -> mismatch
  - valid contract context -> pass

### Verification
- `python -m py_compile ...` PASS
- `backend\\venv\\Scripts\\python.exe -m unittest discover -s backend/tests -p "test_monitoring_guard.py" -v` PASS (9)
- `backend\\venv\\Scripts\\python.exe -m unittest discover -s backend/tests -p "test_collab_triage.py" -v` PASS (9)

## Session Update (일관성 모니터링 명칭 고정 + 누락 강제)
- User confirmed official program name: `일관성 모니터링`.
- Core mission fixed: enforce consistency across requirements -> plan -> design -> implementation -> verification.

### Enforcement upgrades
1. Contract schema 강화 (`config/requirement_contracts.json`)
- Added mandatory context fields:
  - `requirement_refs`, `plan_refs`, `design_refs`
  - `consistency_monitoring_enabled` (truthy required)
- Added required reference sets:
  - `required_requirement_refs`
  - `required_plan_refs`
  - existing `required_design_refs`

2. Contract evaluator 강화 (`backend/app/services/requirement_contract_service.py`)
- Added explicit mismatch reasons:
  - `requirement_ref_missing:*`
  - `plan_ref_missing:*`
  - existing `design_ref_missing:*`

3. Rule default hardening (`backend/app/services/monitoring_rules.py`)
- `enforce_requirement_contract` default changed to `True`.
- Meaning: monitoring contract is enforced by default unless explicitly disabled (discouraged).

4. Core path context hardening
- `backend/app/api/collab.py`
- `scripts/idea_pipeline/mcp_server.py`
- `scripts/stock_moat/batch_moat_value.py`
- Added:
  - `consistency_monitoring_enabled=True`
  - `requirement_refs`, `plan_refs`, `design_refs`

5. Adapter defaults hardening (`scripts/idea_pipeline/monitoring_adapter.py`)
- Auto-injects default consistency contract fields so new scripts do not miss required context.

### Validation
- `backend\\venv\\Scripts\\python.exe -m unittest discover -s backend/tests -p "test_monitoring_guard.py" -v` -> PASS (12)
- `backend\\venv\\Scripts\\python.exe -m unittest discover -s backend/tests -p "test_collab_triage.py" -v` -> PASS (9)
- Follow-up hardening: `required_requirement_refs` now includes `REQUESTS.md#REQ-009` and all core contexts/adapter defaults include REQ-009 reference.
- Re-verified after hardening:
  - `backend\\venv\\Scripts\\python.exe -m unittest discover -s backend/tests -p "test_monitoring_guard.py" -v` PASS (12)
  - `backend\\venv\\Scripts\\python.exe -m unittest discover -s backend/tests -p "test_collab_triage.py" -v` PASS (9)

## Session Update (3-Layer Enforcement for Consistency Monitoring)
- Implemented requested triple enforcement:
  1) Branch/CI gate, 2) static new-entrypoint check, 3) runtime fail-closed.

### 1) CI gate
- Added workflow: `.github/workflows/consistency-monitoring-gate.yml`
- Runs on PR to master/main:
  - `scripts/ci/check_entrypoint_monitoring.py --scope changed`
  - `backend/tests/test_monitoring_guard.py`
  - `backend/tests/test_collab_triage.py`

### 2) Static new-entrypoint check
- Added: `scripts/ci/check_entrypoint_monitoring.py`
- Behavior:
  - scans added entrypoint files (A/R) + modified files that add new entrypoint markers
  - fails when monitoring call token is missing
  - for script `__main__`, requires runtime fail-closed token unless runtime-exempt marker exists

### 3) Runtime fail-closed
- Added: `scripts/consistency/fail_closed_runtime.py`
- `register_fail_closed_guard(entrypoint)` + `mark_monitoring_called()`
- if process exits without monitoring mark, forced exit code 97.
- integrated with:
  - `scripts/idea_pipeline/monitoring_adapter.py` (auto marks on enforce call)
  - `scripts/stock_moat/batch_moat_value.py` (register + no-target/header-missing safe mark)
  - `scripts/idea_pipeline/mcp_server.py` marked runtime-exempt comment for MCP host lifecycle.

### Branch protection automation
- Added: `scripts/ci/apply_branch_protection.py`
- Added runbook: `docs/ops/consistency-monitoring-branch-protection.md`
- required check context: `consistency-monitoring-gate / consistency-monitoring-gate`

### Verification
- Compile PASS:
  - `python -m py_compile ...` (new/changed gate files)
- Tests PASS:
  - `backend\\venv\\Scripts\\python.exe -m unittest discover -s backend/tests -p "test_monitoring_guard.py" -v` (12)
  - `backend\\venv\\Scripts\\python.exe -m unittest discover -s backend/tests -p "test_collab_triage.py" -v` (9)
- Static gate script PASS:
  - `python scripts/ci/check_entrypoint_monitoring.py --scope changed --base-ref HEAD~1`
- Runtime fail-closed behavior verified:
  - no mark => exit 97
  - mark present => exit 0

## Session Update (Mini Consistency Batch Demo Execution)
- Implemented and executed a simple demo project for consistency-monitoring validation.

### Added
1. Demo runner
- `scripts/demo/mini_consistency_batch.py`
- reads CSV rows, builds monitoring context per row, runs `enforce_monitoring`, and writes `OK/BLOCKED` output.
- includes runtime fail-closed registration.

2. Demo data
- `data/demo/mini_input.csv` (6 rows)
- scenarios: `ok`, `missing_requirement_refs`, `missing_plan_refs`, `missing_req_id`, `consistency_off`, `ok`

3. Demo test
- `backend/tests/test_mini_consistency_batch.py`
- validates: total 6, OK 2, BLOCKED 4, blocked rows carry incident/rule fields.

4. Ops scenario doc
- `docs/ops/mini-consistency-batch-scenario.md`

### Adjustment
- Updated contract allowed source prefixes to include `scripts.demo` for demo entrypoint path.

### Execution Result
- Command: `backend\\venv\\Scripts\\python.exe scripts/demo/mini_consistency_batch.py`
- Result: `total=6 success=2 blocked=4`
- Output: `data/demo/mini_output.csv`

### Verification
- `backend\\venv\\Scripts\\python.exe -m unittest discover -s backend/tests -p "test_mini_consistency_batch.py" -v` PASS (1)
- `backend\\venv\\Scripts\\python.exe -m unittest discover -s backend/tests -p "test_monitoring_guard.py" -v` PASS (12)
- `backend\\venv\\Scripts\\python.exe -m unittest discover -s backend/tests -p "test_collab_triage.py" -v` PASS (9)
- Static entrypoint check for new demo path: `_check_path('scripts/demo/mini_consistency_batch.py') -> []`

## Session Update (Windows Dev Server Start/Stop Shortcuts)
- Added PowerShell shortcuts to reduce manual two-terminal restarts.

### Added
1. `scripts/dev/start_servers.ps1`
- Starts API + Dashboard using backend venv python.
- If port is already in use, skips that service safely.
- Writes runtime state to `data/runtime/dev_servers_state.json`.
- Writes logs to `data/runtime/logs/*`.

2. `scripts/dev/stop_servers.ps1`
- Stops only processes started by the script (safe default).
- Optional `-KillByPort` mode to force-stop by given ports.

3. `docs/ops/dev-server-shortcuts.md`
- documents start/stop commands and options.

### Fixes during validation
- Resolved PowerShell automatic variable collisions (`$Args`, `$PID`) by renaming parameters/locals.
- Added stop fallback to check/stop by recorded port for started services.

### Verification
- start script execution validated.
- state file creation/removal validated.
- dashboard force-stop by port validated (`-KillByPort -ApiPort 9999 -DashboardPort 8080`).
- final environment check: port 8000 active (pre-existing), port 8080 free.
