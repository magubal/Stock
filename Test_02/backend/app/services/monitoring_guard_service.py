import json
from dataclasses import dataclass
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from ..models.monitoring import MonitoringDecision, MonitoringEvent, MonitoringIncident
from .monitoring_rules import evaluate_monitoring_rules


@dataclass
class MonitoringBlockedError(Exception):
    incident_id: int
    rule_code: str
    reasons: List[str]


class MonitoringGuardService:
    """Consistency Monitoring guard.

    Core responsibility: block workflows when requirement-plan-design
    consistency contracts are violated.
    """

    def __init__(self, db: Session):
        self.db = db

    def record_pass(self, context: Dict, message: str = "guard_pass") -> MonitoringEvent:
        event = MonitoringEvent(
            incident_id=None,
            event_type="pass",
            source_path=str(context.get("source_path") or "unknown"),
            entity_id=str(context.get("entity_id") or "unknown"),
            message=message,
        )
        self.db.add(event)
        self.db.flush()
        return event

    def record_block(self, context: Dict, violations: List[Dict]) -> MonitoringIncident:
        first = violations[0]
        incident = MonitoringIncident(
            source_path=str(context.get("source_path") or "unknown"),
            entity_type=str(context.get("entity_type") or "unknown"),
            entity_id=str(context.get("entity_id") or "unknown"),
            rule_code=str(first.get("rule_code") or "unknown"),
            severity=str(first.get("severity") or "high"),
            status="blocked_pending_codex",
            payload_json=json.dumps(
                {
                    "context": context,
                    "violations": violations,
                },
                ensure_ascii=False,
            ),
            requires_reconfirm=True,
            approver="codex",
        )
        self.db.add(incident)
        self.db.flush()

        block_event = MonitoringEvent(
            incident_id=incident.id,
            event_type="block",
            source_path=incident.source_path,
            entity_id=incident.entity_id,
            message=json.dumps(
                {
                    "rule_code": incident.rule_code,
                    "reasons": first.get("reasons", []),
                },
                ensure_ascii=False,
            ),
        )
        self.db.add(block_event)
        self.db.flush()
        return incident

    def enforce(self, context: Dict, hard_block: bool = True) -> Optional[MonitoringIncident]:
        violations = evaluate_monitoring_rules(context)
        if not violations:
            self.record_pass(context)
            return None

        incident = self.record_block(context, violations)
        if hard_block:
            reasons = list(violations[0].get("reasons", []))
            raise MonitoringBlockedError(
                incident_id=incident.id,
                rule_code=incident.rule_code,
                reasons=reasons,
            )
        return incident

    def list_pending(self, limit: int = 100) -> List[MonitoringIncident]:
        return (
            self.db.query(MonitoringIncident)
            .filter(MonitoringIncident.status == "blocked_pending_codex")
            .order_by(MonitoringIncident.id.desc())
            .limit(limit)
            .all()
        )

    def _change_status(self, incident_id: int, decision: str, note: Optional[str], decider: str) -> MonitoringDecision:
        incident = self.db.query(MonitoringIncident).filter(MonitoringIncident.id == incident_id).first()
        if not incident:
            raise ValueError("incident_not_found")

        mapping = {
            "approve": "approved",
            "reject": "rejected",
            "resolve": "resolved",
        }
        target_status = mapping.get(decision)
        if not target_status:
            raise ValueError("invalid_decision")

        if decision in {"approve", "reject"} and incident.status != "blocked_pending_codex":
            raise ValueError("invalid_status_transition")

        incident.status = target_status
        entry = MonitoringDecision(
            incident_id=incident.id,
            decider=decider or "codex",
            decision=decision,
            note=note,
        )
        self.db.add(entry)
        self.db.flush()

        self.db.add(
            MonitoringEvent(
                incident_id=incident.id,
                event_type=decision,
                source_path=incident.source_path,
                entity_id=incident.entity_id,
                message=note or "",
            )
        )
        self.db.flush()
        return entry

    def approve_incident(self, incident_id: int, note: Optional[str], decider: str = "codex") -> MonitoringDecision:
        return self._change_status(incident_id, "approve", note, decider)

    def reject_incident(self, incident_id: int, note: Optional[str], decider: str = "codex") -> MonitoringDecision:
        return self._change_status(incident_id, "reject", note, decider)

    def resolve_incident(self, incident_id: int, note: Optional[str], decider: str = "codex") -> MonitoringDecision:
        return self._change_status(incident_id, "resolve", note, decider)
