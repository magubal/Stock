import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "backend" / "stock_research.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{DB_PATH}")
os.environ.setdefault("DEBUG", "false")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.database import Base, SessionLocal, engine  # noqa: E402
import backend.app.models  # noqa: E402,F401
from backend.app.services.monitoring_guard_service import MonitoringBlockedError, MonitoringGuardService  # noqa: E402
from scripts.consistency.fail_closed_runtime import mark_monitoring_called  # noqa: E402


@dataclass
class GuardResult:
    blocked: bool
    incident_id: int = 0
    rule_code: str = ""
    reasons: list = None


_DEFAULT_DESIGN_REFS = [
    "docs/plans/2026-02-15-global-monitoring-guard-design.md",
    "docs/plans/2026-02-15-global-monitoring-guard-implementation.md",
]
_DEFAULT_REQUIREMENT_REFS = [
    "REQUESTS.md#REQ-007",
    "REQUESTS.md#REQ-008",
    "REQUESTS.md#REQ-009",
]
_DEFAULT_PLAN_REFS = [
    "docs/plans/2026-02-15-global-monitoring-guard-implementation.md",
]


def _normalize_context(context: Dict) -> Dict:
    payload = dict(context or {})
    payload.setdefault("req_id", "REQ-007")
    payload.setdefault("enforce_requirement_contract", True)
    payload.setdefault("consistency_monitoring_enabled", True)
    payload.setdefault("requirement_refs", list(_DEFAULT_REQUIREMENT_REFS))
    payload.setdefault("plan_refs", list(_DEFAULT_PLAN_REFS))
    payload.setdefault("design_refs", list(_DEFAULT_DESIGN_REFS))
    payload.setdefault("test_tags", ["monitoring_guard"])
    return payload


def enforce_monitoring(context: Dict, hard_block: bool = True) -> GuardResult:
    mark_monitoring_called()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        service = MonitoringGuardService(db)
        normalized = _normalize_context(context)
        try:
            service.enforce(normalized, hard_block=hard_block)
            db.commit()
            return GuardResult(blocked=False, reasons=[])
        except MonitoringBlockedError as e:
            db.commit()
            return GuardResult(
                blocked=True,
                incident_id=e.incident_id,
                rule_code=e.rule_code,
                reasons=e.reasons,
            )
    finally:
        db.close()
