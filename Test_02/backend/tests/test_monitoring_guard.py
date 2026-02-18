import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import backend.app.models  # noqa: F401
from backend.app.api import monitoring as monitoring_api
from backend.app.database import Base
from backend.app.models.monitoring import MonitoringEvent, MonitoringIncident
from backend.app.services.monitoring_guard_service import MonitoringBlockedError, MonitoringGuardService
from backend.app.services.monitoring_rules import evaluate_monitoring_rules


def _stock_context(**overrides):
    payload = {
        "source_path": "backend.app.api.collab.triage_packet",
        "entity_type": "collab_packet",
        "entity_id": "packet-test-001",
        "req_id": "REQ-007",
        "enforce_requirement_contract": True,
        "consistency_monitoring_enabled": True,
        "requirement_refs": ["REQUESTS.md#REQ-007", "REQUESTS.md#REQ-008", "REQUESTS.md#REQ-009"],
        "plan_refs": ["docs/plans/2026-02-15-global-monitoring-guard-implementation.md"],
        "design_refs": [
            "docs/plans/2026-02-15-global-monitoring-guard-design.md",
            "docs/plans/2026-02-15-global-monitoring-guard-implementation.md",
        ],
        "test_tags": ["monitoring_guard", "unit_test"],
        "category": "PORTFOLIO",
        "packet_type": "종목",
        "stock_context": True,
        "run_stock_pipeline": True,
        "pipeline_executed": True,
        "pipeline_error": "",
        "create_idea": False,
        "idea_gate_should_create": False,
        "force_create_idea": False,
        "traceability_ok": True,
        "ticker": "005930",
        "stock_name": "삼성전자",
    }
    payload.update(overrides)
    return payload


def _contract_context(**overrides):
    payload = _stock_context(
        req_id="REQ-007",
        enforce_requirement_contract=True,
        consistency_monitoring_enabled=True,
        requirement_refs=["REQUESTS.md#REQ-007", "REQUESTS.md#REQ-008", "REQUESTS.md#REQ-009"],
        plan_refs=["docs/plans/2026-02-15-global-monitoring-guard-implementation.md"],
        design_refs=[
            "docs/plans/2026-02-15-global-monitoring-guard-design.md",
            "docs/plans/2026-02-15-global-monitoring-guard-implementation.md",
        ],
        test_tags=["monitoring_guard", "unit_test"],
    )
    payload.update(overrides)
    return payload


class MonitoringRulesTests(unittest.TestCase):
    def test_schema_contract_break_when_required_fields_missing(self):
        violations = evaluate_monitoring_rules({})
        self.assertGreaterEqual(len(violations), 1)
        self.assertEqual(violations[0]["rule_code"], "schema_contract_break")

    def test_required_pipeline_execution_violation_for_stock_context(self):
        violations = evaluate_monitoring_rules(
            _stock_context(
                run_stock_pipeline=True,
                pipeline_executed=False,
                pipeline_error="stock_target_not_found",
            )
        )
        codes = {row["rule_code"] for row in violations}
        self.assertIn("required_pipeline_execution", codes)

    def test_requirement_contract_violation_when_req_id_missing(self):
        violations = evaluate_monitoring_rules(
            _contract_context(req_id="")
        )
        codes = {row["rule_code"] for row in violations}
        self.assertIn("requirement_contract_missing", codes)

    def test_requirement_contract_violation_when_design_ref_missing(self):
        violations = evaluate_monitoring_rules(
            _contract_context(design_refs=["docs/plans/other.md"])
        )
        codes = {row["rule_code"] for row in violations}
        self.assertIn("requirement_contract_mismatch", codes)

    def test_requirement_contract_violation_when_plan_ref_missing(self):
        violations = evaluate_monitoring_rules(
            _contract_context(plan_refs=["docs/plans/other.md"])
        )
        codes = {row["rule_code"] for row in violations}
        self.assertIn("requirement_contract_mismatch", codes)

    def test_requirement_contract_violation_when_requirement_ref_missing(self):
        violations = evaluate_monitoring_rules(
            _contract_context(requirement_refs=["REQUESTS.md#REQ-999"])
        )
        codes = {row["rule_code"] for row in violations}
        self.assertIn("requirement_contract_mismatch", codes)

    def test_requirement_contract_violation_when_consistency_disabled(self):
        violations = evaluate_monitoring_rules(
            _contract_context(consistency_monitoring_enabled=False)
        )
        codes = {row["rule_code"] for row in violations}
        self.assertIn("requirement_contract_mismatch", codes)

    def test_requirement_contract_passes_with_valid_context(self):
        violations = evaluate_monitoring_rules(_contract_context())
        codes = {row["rule_code"] for row in violations}
        self.assertNotIn("requirement_contract_missing", codes)
        self.assertNotIn("requirement_contract_mismatch", codes)


class MonitoringGuardServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def tearDown(self):
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def test_enforce_pass_records_monitoring_event(self):
        db = self.session_local()
        try:
            service = MonitoringGuardService(db)
            service.enforce(_stock_context(), hard_block=True)
            db.commit()
            events = db.query(MonitoringEvent).filter(MonitoringEvent.event_type == "pass").all()
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].entity_id, "packet-test-001")
        finally:
            db.close()

    def test_enforce_block_raises_and_records_incident(self):
        db = self.session_local()
        try:
            service = MonitoringGuardService(db)
            with self.assertRaises(MonitoringBlockedError) as err:
                service.enforce(
                    _stock_context(category="SECTOR", packet_type="섹터산업"),
                    hard_block=True,
                )
            db.commit()
            incident = (
                db.query(MonitoringIncident)
                .filter(MonitoringIncident.id == err.exception.incident_id)
                .first()
            )
            self.assertIsNotNone(incident)
            self.assertEqual(incident.status, "blocked_pending_codex")
            self.assertEqual(incident.rule_code, "classification_consistency")
        finally:
            db.close()


class MonitoringApiTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

        app = FastAPI()
        app.include_router(monitoring_api.router)

        def override_get_db():
            db = self.session_local()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[monitoring_api.get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def _seed_incident(self) -> int:
        db = self.session_local()
        try:
            service = MonitoringGuardService(db)
            incident = service.enforce(
                _stock_context(category="SECTOR", packet_type="섹터산업"),
                hard_block=False,
            )
            db.commit()
            return incident.id
        finally:
            db.close()

    def test_incident_list_and_approve(self):
        incident_id = self._seed_incident()
        list_resp = self.client.get("/api/v1/monitoring/incidents")
        self.assertEqual(list_resp.status_code, 200)
        ids = {row["id"] for row in list_resp.json()}
        self.assertIn(incident_id, ids)

        approve_resp = self.client.post(
            f"/api/v1/monitoring/incidents/{incident_id}/approve",
            json={"note": "confirmed"},
        )
        self.assertEqual(approve_resp.status_code, 200)
        self.assertEqual(approve_resp.json()["decision"], "approve")
        self.assertEqual(approve_resp.json()["decider"], "codex")

    def test_non_codex_decider_is_rejected(self):
        incident_id = self._seed_incident()
        resp = self.client.post(
            f"/api/v1/monitoring/incidents/{incident_id}/approve",
            json={"decider": "claude", "note": "invalid approver"},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json().get("detail"), "decider_must_be_codex")


if __name__ == "__main__":
    unittest.main()
