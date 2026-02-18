# 일관성 모니터링 (Consistency Monitoring) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enforce consistent hard-block monitoring across core paths with DB-backed incident queue and Codex reconfirm decisions.

**Architecture:** Introduce a shared consistency-monitoring service and apply it to API and script entry points. Violations create standardized incidents in DB. API requests are blocked immediately. Batch scripts isolate blocked records and continue processing other records.

**Tech Stack:** FastAPI, SQLAlchemy, SQLite, Python unittest, existing project scripts (`idea_pipeline`, `stock_moat`).

---

### Task 1: Add Monitoring Models

**Files:**
- Create: `backend/app/models/monitoring.py`
- Modify: `backend/app/models/__init__.py`
- Test: `backend/tests/test_monitoring_guard_models.py`

**Step 1: Write the failing test**
- Add model tests for table creation and required columns:
  - `monitoring_incidents`
  - `monitoring_decisions`
  - `monitoring_events`

**Step 2: Run test to verify it fails**
- Run: `backend\\venv\\Scripts\\python.exe -m unittest backend.tests.test_monitoring_guard_models -v`
- Expected: FAIL due to missing model/table.

**Step 3: Write minimal implementation**
- Implement SQLAlchemy models with status fields and timestamps.
- Register model imports in `backend/app/models/__init__.py`.

**Step 4: Run test to verify it passes**
- Same command as Step 2.

### Task 2: Add Monitoring Schemas and Repository Service

**Files:**
- Create: `backend/app/schemas/monitoring.py`
- Create: `backend/app/services/monitoring_guard_service.py`
- Test: `backend/tests/test_monitoring_guard_service.py`

**Step 1: Write the failing test**
- Add tests for:
  - incident create
  - event create
  - decision transitions (`blocked_pending_codex -> approved/rejected/resolved`)

**Step 2: Run test to verify it fails**
- Run: `backend\\venv\\Scripts\\python.exe -m unittest backend.tests.test_monitoring_guard_service -v`

**Step 3: Write minimal implementation**
- Add dataclasses/typed schema contracts.
- Add repository-like service methods:
  - `record_pass`
  - `record_block`
  - `approve_incident`
  - `reject_incident`
  - `resolve_incident`

**Step 4: Run test to verify it passes**
- Same command as Step 2.

### Task 3: Implement Shared Rule Engine

**Files:**
- Create: `backend/app/services/monitoring_rules.py`
- Modify: `backend/app/services/monitoring_guard_service.py`
- Test: `backend/tests/test_monitoring_rules.py`

**Step 1: Write the failing test**
- Add rule tests for:
  - `classification_consistency`
  - `required_pipeline_execution`
  - `gate_bypass_attempt`
  - `traceability_missing`
  - `schema_contract_break`

**Step 2: Run test to verify it fails**
- Run: `backend\\venv\\Scripts\\python.exe -m unittest backend.tests.test_monitoring_rules -v`

**Step 3: Write minimal implementation**
- Implement deterministic rule functions and consolidated evaluator.

**Step 4: Run test to verify it passes**
- Same command as Step 2.

### Task 4: Integrate Guard into Collab API Path

**Files:**
- Modify: `backend/app/api/collab.py`
- Create: `backend/app/api/monitoring.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_collab_monitoring_integration.py`

**Step 1: Write the failing test**
- Add tests that assert:
  - rule violation returns block response
  - incident row is created
  - reconfirm-required fields present

**Step 2: Run test to verify it fails**
- Run: `backend\\venv\\Scripts\\python.exe -m unittest backend.tests.test_collab_monitoring_integration -v`

**Step 3: Write minimal implementation**
- Call guard at collab triage boundaries.
- Add monitoring API endpoints for Codex decisions.

**Step 4: Run test to verify it passes**
- Same command as Step 2.

### Task 5: Integrate Guard into Idea Pipeline Scripts

**Files:**
- Modify: `scripts/idea_pipeline/mcp_server.py`
- Create: `scripts/idea_pipeline/monitoring_adapter.py`
- Test: `backend/tests/test_idea_pipeline_monitoring_integration.py`

**Step 1: Write the failing test**
- Validate export/import path writes incidents for violations and blocks progression for violating call.

**Step 2: Run test to verify it fails**
- Run: `backend\\venv\\Scripts\\python.exe -m unittest backend.tests.test_idea_pipeline_monitoring_integration -v`

**Step 3: Write minimal implementation**
- Use shared guard adapter from scripts.

**Step 4: Run test to verify it passes**
- Same command as Step 2.

### Task 6: Integrate Guard into Stock Moat Batch Scripts

**Files:**
- Modify: `scripts/stock_moat/batch_moat_value.py`
- Modify: `scripts/stock_moat/manager_distributed_batch.py`
- Create: `scripts/stock_moat/monitoring_adapter.py`
- Test: `backend/tests/test_stock_moat_batch_monitoring.py`

**Step 1: Write the failing test**
- Ensure one violating row is marked blocked with incident id while the next row is still processed.

**Step 2: Run test to verify it fails**
- Run: `backend\\venv\\Scripts\\python.exe -m unittest backend.tests.test_stock_moat_batch_monitoring -v`

**Step 3: Write minimal implementation**
- Add per-row guard check and blocked-row summary counters.

**Step 4: Run test to verify it passes**
- Same command as Step 2.

### Task 7: Add Codex Reconfirmation Endpoints Tests

**Files:**
- Modify: `backend/app/api/monitoring.py`
- Test: `backend/tests/test_monitoring_api.py`

**Step 1: Write the failing test**
- Endpoints:
  - list pending incidents
  - approve/reject/resolve
- Assert state transition correctness and invalid transition handling.

**Step 2: Run test to verify it fails**
- Run: `backend\\venv\\Scripts\\python.exe -m unittest backend.tests.test_monitoring_api -v`

**Step 3: Write minimal implementation**
- Add endpoint handlers and service wiring.

**Step 4: Run test to verify it passes**
- Same command as Step 2.

### Task 8: Final Verification and Documentation

**Files:**
- Modify: `REQUESTS.md`
- Modify: `docs/development_log_2026-02-15.md`

**Step 1: Run all monitoring-related tests**
- Run:
  - `backend\\venv\\Scripts\\python.exe -m unittest discover -s backend/tests -p "test_monitoring*.py" -v`
  - `backend\\venv\\Scripts\\python.exe -m unittest discover -s backend/tests -p "test_collab*.py" -v`

**Step 2: Run compile checks**
- Run:
  - `python -m py_compile backend/app/api/collab.py backend/app/api/monitoring.py backend/app/services/monitoring_guard_service.py backend/app/services/monitoring_rules.py scripts/idea_pipeline/mcp_server.py scripts/stock_moat/batch_moat_value.py`

**Step 3: Update continuity docs**
- Add phase-1 scope, decisions, and verification outputs.

**Step 4: Confirm completion checklist**
- Shared guard integrated in all phase-1 target paths.
- Hard-block behavior validated.
- Batch isolation behavior validated.
- Codex reconfirmation flow validated.
