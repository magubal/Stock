# Codex Fix Summary (2026-02-15)

## Scope
- Workspace scope fixed to `Test_02` only.
- This patch focuses on Oracle/DART TTM integration stability, compatibility, and regression fixes.

## What Was Fixed

1. AIVerifier compatibility and stability
- File: `.agent/skills/stock-moat/utils/ai_verifier.py`
- Rebuilt verifier module to remove syntax/encoding breakage.
- Added legacy positional-call coercion for old `verify(...)` call pattern.
- Kept new signature support for `analyze_with_evidence.py`.
- Changed init behavior:
  - `api_key=None` is disabled by default (test-deterministic).
  - Optional env loading via `load_from_env=True`.

2. As-of-date consistency wiring
- File: `scripts/stock_moat/analyze_with_evidence.py`
- Introduced `analysis_as_of_date` and threaded into:
  - `FinancialsResolver.resolve_ttm(..., as_of_date=...)`
  - `FinancialsResolver.resolve_trend(..., as_of_date=...)`
- Replaced `year="auto"` direct DART call with derived `financial_year`.
- Fixed segment query year to use resolved `financial_year`.

3. Fallback resolver correctness
- File: `.agent/skills/stock-moat/utils/financials_resolver.py`
- Rebuilt resolver to ensure clean, executable fallback layers:
  - Layer 1: Oracle TTM
  - Layer 2: DART quarterly reconstruction
  - Layer 3: DART annual fallback
- Added `as_of_date`-based year anchoring (`_base_year`).
- Multi-year trend query years now derived from `as_of_date`.

4. Data quality metadata completion
- File: `.agent/skills/stock-moat/utils/data_quality.py`
- Rebuilt models cleanly.
- Added `DataQuality.__post_init__` for freshness/warning derivation from `AsOfDate`.
- Ensured `freshness_days` + warnings are materialized and serializable.

5. Op multiple serialization bug
- File: `scripts/stock_moat/analyze_with_evidence.py`
- Fixed:
  - from: `round(op_multiple, 1) if op_multiple else None`
  - to:   `round(op_multiple, 1) if op_multiple is not None else None`

6. MoatEvaluator reason logging bug
- File: `.agent/skills/stock-moat/utils/moat_evaluator_v2.py`
- Fixed ROE gatekeeper reason append condition (previous branch was unreachable).

7. Legacy caller fixes for evaluator signature
- Files:
  - `scripts/stock_moat/reanalyze_with_evidence.py`
  - `scripts/stock_moat/update_master_excel_v2.py`
- Updated `evaluator.evaluate(...)` to pass `classification` in correct slot and `financials` as named arg.

8. Path fallback portability
- File: `.agent/skills/stock-moat/utils/config.py`
- Replaced hardcoded fallback root with path-derived fallback from current file location.

## Verification Run

1. Syntax compile
```bash
python -m py_compile scripts/stock_moat/analyze_with_evidence.py .agent/skills/stock-moat/utils/ai_verifier.py .agent/skills/stock-moat/utils/financials_resolver.py .agent/skills/stock-moat/utils/data_quality.py .agent/skills/stock-moat/utils/moat_evaluator_v2.py scripts/stock_moat/reanalyze_with_evidence.py scripts/stock_moat/update_master_excel_v2.py .agent/skills/stock-moat/utils/config.py
```
- Result: PASS

2. Regression tests
```bash
pytest scripts/stock_moat/tests/test_evidence_moat.py -q
```
- Result: `30 passed`

## Notes for Claude

1. `as_of_date` is now consistently threaded through resolver and valuation date fields, but DART report fetch itself is still “latest report” logic.
2. Metric naming remains `op_multiple` (market cap / TTM operating income), not PER.
3. If you want strict “single temporal baseline” for report retrieval too, next step is to constrain report search by explicit `as_of_date` cutoff.

## 2026-02-15 Policy Update (Codex)

- Raw information must not be hidden in UI/API, even when strings look broken (e.g. `???`).
- Fix root causes (encoding/write path) first; do not mask symptoms with fallback placeholders.
- Idea Board/COLLAB display path updated to preserve raw text for debugging and data-quality tracking.
