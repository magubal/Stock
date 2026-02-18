# Global Change Guard (Mandatory)

## Purpose
- Prevent regressions in existing features when new requests are implemented.
- Enforce the same checklist across sessions and across different AI models.

## Scope
- Applies to **all source changes** under:
  - `backend/`
  - `frontend/`
  - `dashboard/`
  - `scripts/`
  - `config/`

## Required Checklist (Enforced)
1. `REQUESTS.md` must be updated when source files change.
2. `docs/development_log_YYYY-MM-DD.md` must be updated when source files change.
3. `dashboard/index.html` integrity check must pass.
4. If `dashboard/index.html` changed, Playwright runtime integrity check must pass.
5. If `dashboard/index.html` changed, structured Playwright suite must pass.
6. Changed Python files must pass `py_compile`.
7. Monitoring entrypoint guard must pass.

## Command
```bash
python scripts/ci/check_global_change_guard.py
```

Dashboard runtime check only:
```bash
python scripts/ci/check_dashboard_runtime_integrity.py
```

Structured Playwright suite only:
```bash
npm run test:dashboard --prefix tests/playwright
```

## CI Enforcement
- Workflow: `.github/workflows/consistency-monitoring-gate.yml`
- Step: `Global change guard checklist (mandatory)`

## Notes
- This guard is fail-closed: if required checklist evidence is missing, CI fails.
- For dashboard edits, malformed closing tags and missing monitoring links are blocked.
