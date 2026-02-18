# 일관성 모니터링 (Consistency Monitoring) Design

Date: 2026-02-15
Scope: Phase 1 (core paths only)

## 1. Goal
Build a shared consistency-monitoring guard that enforces requirement-plan-design consistency across core execution paths and blocks invalid progression until Codex reconfirmation is completed.

Target paths in phase 1:
- `backend/app/api/*`
- `scripts/idea_pipeline/*`
- `scripts/stock_moat/*`

## 2. Hard Rules (confirmed)
- Rule mode: hard-block for API and scripts.
- Batch scripts: do not stop full batch on one violation; isolate blocked item and continue next item.
- Reconfirmation approver: Codex.
- Incident queue storage: DB table.
- Phase 1 release: DB/API first. UI follows in phase 2.

## 3. Problem Statement
The project has multiple entry paths (API, MCP export/import, batch scripts). A single policy can be bypassed if one path does not normalize/validate the same way as others.

Observed example:
- Stock-evaluation packet misclassified as `SECTOR` in one path.
- Stock-only gate was not always applied without extra detection.

The guard must remove path-dependent behavior differences.

## 4. Architecture
Recommended approach: shared guard + centralized incident model.

### 4.1 Core components
- `MonitoringGuard` (shared service)
  - Evaluates context and rules.
  - Returns `pass` or `blocked` + structured reasons.
- `MonitoringIncidentRepository` (DB-backed)
  - Stores all blocked incidents and decisions.
- `MonitoringDecisionService`
  - Applies Codex approval/reject actions.
- `MonitoringEventLogger`
  - Stores trace events for pass/block attempts.

### 4.2 Flow
1. Entry point builds monitoring context.
2. Guard evaluates rules.
3. If pass: continue flow and write `pass` event.
4. If blocked:
   - Write incident row.
   - Write block event.
   - API: return blocking response.
   - Script: mark current item blocked and continue next item.
5. Reconfirm by Codex updates incident decision state.

## 5. Data Model (phase 1)
Proposed DB entities:
- `monitoring_incidents`
  - `id`, `occurred_at`, `source_path`, `entity_type`, `entity_id`, `rule_code`, `severity`, `status`, `payload_json`, `requires_reconfirm`, `approver`
- `monitoring_decisions`
  - `id`, `incident_id`, `decider`, `decision` (`approve/reject/resolve`), `note`, `decided_at`
- `monitoring_events`
  - `id`, `incident_id`, `event_type` (`pass/block/retry`), `source_path`, `entity_id`, `message`, `created_at`

Status lifecycle:
- `blocked_pending_codex` -> `approved` or `rejected` -> `resolved`

## 6. Rule Set (phase 1)
Rule codes:
- `classification_consistency`
  - Stock-like context but category/packet_type mismatch.
- `required_pipeline_execution`
  - Stock-like context but required pipeline not executed.
- `gate_bypass_attempt`
  - Create action attempted while required gate conditions are not met.
- `traceability_missing`
  - Required history/evidence metadata missing.
- `schema_contract_break`
  - Required contract fields absent or malformed.

## 7. API Behavior Contract
When blocked in API path:
- Return structured error with:
  - `blocked=true`
  - `incident_id`
  - `rule_code`
  - `reasons`
  - `reconfirm_required=true`
  - `approver=codex`

When pass:
- Continue normal response path.

## 8. Script Behavior Contract
When blocked in script path:
- Current record marked with:
  - `status=blocked`
  - `incident_id`
  - `rule_code`
- Continue processing remaining records.
- Batch summary includes `blocked_count`.

## 9. Reconfirmation Contract
Codex-only decision endpoints (phase 1):
- list pending incidents
- approve incident
- reject incident
- resolve incident

Guard checks must prevent progression for unresolved incidents.

## 10. Rollout Plan
Phase 1:
- Implement DB models + backend service + API integration in core paths.
- Add script integration for `idea_pipeline` and `stock_moat`.
- Add test coverage for API blocking and batch isolation.

Phase 2:
- Add monitoring dashboard UI.
- Add operational reports and trend analytics.

## 11. Risks and Mitigations
- Risk: false positives block too often.
  - Mitigation: rule-level payload details and Codex reconfirm queue.
- Risk: performance overhead in batch.
  - Mitigation: minimal context builder and cheap deterministic rules first.
- Risk: inconsistent integration across scripts.
  - Mitigation: shared guard adapter and one integration checklist.

## 12. Acceptance Criteria
- Core paths use one shared guard path (no duplicated ad-hoc checks).
- API blocks and emits incident when rule violation occurs.
- Batch keeps running while isolating blocked items.
- Codex decision updates incident state and unlocks progression.
- Regression tests cover all phase-1 rule families.
