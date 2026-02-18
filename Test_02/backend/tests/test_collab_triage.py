import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.api import collab as collab_api
from backend.app.database import Base
from backend.app.models.collab import CollabPacket
from backend.app.models.idea import Idea


class CollabTriageApiTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

        app = FastAPI()
        app.include_router(collab_api.router)

        def override_get_db():
            db = self.session_local()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[collab_api.get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def test_triage_endpoint_creates_linked_idea_and_saves_triage_meta(self):
        packet_payload = {
            "packet_id": "packet-001",
            "source_ai": "claude",
            "topic": "AI CAPEX Bubble Risk",
            "category": "RISK",
            "content_json": json.dumps({"summary": "Valuation risk rising", "packet_type": "시장우려"}),
            "request_action": "validate",
            "request_ask": "Need challenge scenario",
            "related_idea_id": None,
        }
        create_resp = self.client.post("/api/v1/collab/packets", json=packet_payload)
        self.assertEqual(create_resp.status_code, 200)

        due = datetime.now(timezone.utc) + timedelta(days=2)
        triage_payload = {
            "action": "extend",
            "assignee_ai": "Agent-Research",
            "due_at": due.isoformat(),
            "note": "expand assumptions",
            "create_idea": True,
            "idea_priority": 2,
            "packet_type": "이슈전망",
        }
        triage_resp = self.client.put("/api/v1/collab/packets/packet-001/triage", json=triage_payload)
        self.assertEqual(triage_resp.status_code, 200)

        body = triage_resp.json()
        self.assertEqual(body["packet"]["request_action"], "extend")
        self.assertIsNotNone(body["packet"]["related_idea_id"])
        self.assertIsNotNone(body["idea"])
        self.assertEqual(body["idea"]["priority"], 2)

        db = self.session_local()
        try:
            packet = db.query(CollabPacket).filter(CollabPacket.packet_id == "packet-001").first()
            self.assertIsNotNone(packet)
            payload = json.loads(packet.content_json)
            self.assertEqual(payload.get("_triage", {}).get("assignee_ai"), "Agent-Research")
            self.assertEqual(payload.get("_triage", {}).get("action"), "extend")
            self.assertEqual(payload.get("_triage", {}).get("packet_type"), "이슈전망")
            self.assertEqual(payload.get("packet_type"), "이슈전망")

            idea = db.query(Idea).filter(Idea.id == packet.related_idea_id).first()
            self.assertIsNotNone(idea)
            self.assertEqual(idea.title, "AI CAPEX Bubble Risk")
            self.assertEqual(idea.status, "active")
        finally:
            db.close()

    def test_inbox_endpoint_returns_triage_fields_and_overdue_flag(self):
        packet_payload = {
            "packet_id": "packet-002",
            "source_ai": "gemini",
            "topic": "Sector Rotation to Value",
            "category": "SECTOR",
            "content_json": json.dumps({"summary": "rates higher for longer", "packet_type": "시장기대"}),
            "request_action": "validate",
            "request_ask": "quick check",
            "related_idea_id": None,
        }
        create_resp = self.client.post("/api/v1/collab/packets", json=packet_payload)
        self.assertEqual(create_resp.status_code, 200)

        overdue_due = datetime.now(timezone.utc) - timedelta(hours=3)
        triage_payload = {
            "action": "challenge",
            "assignee_ai": "Agent-Risk",
            "due_at": overdue_due.isoformat(),
            "note": "needs downside case",
            "create_idea": False,
        }
        triage_resp = self.client.put("/api/v1/collab/packets/packet-002/triage", json=triage_payload)
        self.assertEqual(triage_resp.status_code, 200)

        inbox_resp = self.client.get("/api/v1/collab/inbox", params={"status": "reviewed"})
        self.assertEqual(inbox_resp.status_code, 200)
        items = inbox_resp.json()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["packet_id"], "packet-002")
        self.assertEqual(items[0]["triage_action"], "challenge")
        self.assertEqual(items[0]["assignee_ai"], "Agent-Risk")
        self.assertEqual(items[0]["packet_type"], "시장기대")
        self.assertRegex(items[0]["work_date"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertTrue(items[0]["overdue"])

    def test_triage_persists_structured_result_payload_and_reflects_on_idea_content(self):
        packet_payload = {
            "packet_id": "packet-005",
            "source_ai": "gemini",
            "topic": "Semiconductor demand check",
            "category": "SECTOR",
            "content_json": json.dumps({"summary": "demand may improve"}),
            "request_action": "validate",
            "request_ask": "verify channel checks",
            "related_idea_id": None,
        }
        create_resp = self.client.post("/api/v1/collab/packets", json=packet_payload)
        self.assertEqual(create_resp.status_code, 200)

        triage_payload = {
            "action": "validate",
            "assignee_ai": "Agent-Research",
            "note": "completed first-pass review",
            "result_summary": "Demand normalization likely in 2H.",
            "result_evidence": "Distributor inventory declined for 2 quarters.",
            "result_risks": "PC end-demand remains weak.",
            "result_next_step": "Validate with earnings call transcript.",
            "result_confidence": 72,
            "create_idea": True,
            "idea_priority": 2,
        }
        triage_resp = self.client.put("/api/v1/collab/packets/packet-005/triage", json=triage_payload)
        self.assertEqual(triage_resp.status_code, 200)

        db = self.session_local()
        try:
            packet = db.query(CollabPacket).filter(CollabPacket.packet_id == "packet-005").first()
            self.assertIsNotNone(packet)
            payload = json.loads(packet.content_json)
            result = payload.get("_triage", {}).get("result", {})
            self.assertEqual(result.get("summary"), "Demand normalization likely in 2H.")
            self.assertEqual(result.get("evidence"), "Distributor inventory declined for 2 quarters.")
            self.assertEqual(result.get("risks"), "PC end-demand remains weak.")
            self.assertEqual(result.get("next_step"), "Validate with earnings call transcript.")
            self.assertEqual(result.get("confidence"), 72)

            idea = db.query(Idea).filter(Idea.id == packet.related_idea_id).first()
            self.assertIsNotNone(idea)
            self.assertIn("Result summary:", idea.content)
            self.assertIn("Demand normalization likely in 2H.", idea.content)
        finally:
            db.close()

    def test_packet_history_endpoint_tracks_created_and_triaged_events(self):
        packet_payload = {
            "packet_id": "packet-003",
            "source_ai": "chatgpt",
            "topic": "Macro positioning",
            "category": "US_MARKET",
            "content_json": json.dumps({"summary": "positioning risk", "packet_type": "트랜드"}),
            "request_action": "infer",
            "request_ask": "map scenarios",
            "related_idea_id": None,
        }
        create_resp = self.client.post("/api/v1/collab/packets", json=packet_payload)
        self.assertEqual(create_resp.status_code, 200)

        triage_payload = {
            "action": "infer",
            "assignee_ai": "Agent-Inference",
            "note": "scenario tree",
            "create_idea": False,
            "packet_type": "이슈전망",
        }
        triage_resp = self.client.put("/api/v1/collab/packets/packet-003/triage", json=triage_payload)
        self.assertEqual(triage_resp.status_code, 200)

        history_resp = self.client.get("/api/v1/collab/packets/packet-003/history")
        self.assertEqual(history_resp.status_code, 200)
        rows = history_resp.json()
        self.assertGreaterEqual(len(rows), 2)
        self.assertEqual(rows[0]["packet_id"], "packet-003")
        self.assertRegex(rows[0]["work_date"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertIn(rows[0]["event_type"], ["created", "triaged", "status_updated"])
        self.assertTrue(any(row["event_type"] == "created" for row in rows))
        self.assertTrue(any(row["event_type"] == "triaged" for row in rows))

    def test_garbled_packet_type_is_preserved(self):
        packet_payload = {
            "packet_id": "packet-004",
            "source_ai": "demo",
            "topic": "encoding check",
            "category": "THEME",
            "content_json": json.dumps({"summary": "demo", "packet_type": "???"}),
            "request_action": "validate",
            "request_ask": "timeline ??? ??",
            "related_idea_id": None,
        }
        create_resp = self.client.post("/api/v1/collab/packets", json=packet_payload)
        self.assertEqual(create_resp.status_code, 200)

        inbox_resp = self.client.get("/api/v1/collab/inbox", params={"status": "pending"})
        self.assertEqual(inbox_resp.status_code, 200)
        items = inbox_resp.json()
        item = next(row for row in items if row["packet_id"] == "packet-004")
        self.assertEqual(item["packet_type"], "???")
        self.assertEqual(item["request_ask"], "timeline ??? ??")

        history_resp = self.client.get("/api/v1/collab/packets/packet-004/history")
        self.assertEqual(history_resp.status_code, 200)
        rows = history_resp.json()
        self.assertGreaterEqual(len(rows), 1)
        self.assertEqual(rows[0]["packet_type"], "???")
        self.assertEqual(rows[0]["note"], "timeline ??? ??")

    def test_stock_packet_triage_enriches_from_stock_pipeline_and_creates_idea(self):
        packet_payload = {
            "packet_id": "packet-006",
            "source_ai": "claude",
            "topic": "삼성전자 (005930) 해자 점검",
            "category": "PORTFOLIO",
            "content_json": json.dumps({"summary": "stock check", "packet_type": "종목"}),
            "request_action": "validate",
            "request_ask": "종목 업황+해자+투자가치 분석",
            "related_idea_id": None,
        }
        create_resp = self.client.post("/api/v1/collab/packets", json=packet_payload)
        self.assertEqual(create_resp.status_code, 200)

        mocked_analysis = {
            "name": "삼성전자",
            "ticker": "005930",
            "core_desc": "삼성전자 | 메모리 중심",
            "bm_summary": "메모리/파운드리 중심 BM",
            "evidence_summary": "증거 7건 quality 14.0",
            "투자가치": 4,
            "해자강도": 4,
            "investment_value": 4,
            "industry_outlook": {
                "summary": "메모리 업황은 재고 정상화 이후 회복 국면으로 진입.",
            },
            "consensus_2026": {
                "revenue_est": 320.0,
                "op_income_est": 48.0,
                "unit": "조원",
            },
            "forecast_scenarios": [
                {"scenario": "bear", "op_income_est": 35.0},
                {"scenario": "base", "op_income_est": 48.0},
                {"scenario": "bull", "op_income_est": 58.0},
            ],
            "investment_comment": "업황 회복과 고부가 믹스 개선이 동반되는 구간.",
        }

        triage_payload = {
            "action": "validate",
            "packet_type": "종목",
            "run_stock_pipeline": True,
            "stock_ticker": "005930",
            "stock_name": "삼성전자",
            "create_idea": True,
            "idea_priority": 2,
        }

        with patch.object(collab_api, "_run_stock_moat_analysis", return_value=mocked_analysis) as mocked_runner:
            triage_resp = self.client.put("/api/v1/collab/packets/packet-006/triage", json=triage_payload)
            self.assertEqual(triage_resp.status_code, 200)
            mocked_runner.assert_called_once()

        body = triage_resp.json()
        self.assertIsNotNone(body.get("idea"))
        self.assertIn("idea_gate", body)
        self.assertTrue(body["idea_gate"]["should_create"])

        db = self.session_local()
        try:
            packet = db.query(CollabPacket).filter(CollabPacket.packet_id == "packet-006").first()
            self.assertIsNotNone(packet)
            payload = json.loads(packet.content_json)
            result = payload.get("_triage", {}).get("result", {})
            self.assertIn("industry_outlook", result)
            self.assertIn("메모리 업황", result.get("industry_outlook", ""))
            self.assertEqual(result.get("consensus_unit"), "조원")
            self.assertEqual(result.get("scenario_base"), "48.0")
            self.assertIsNotNone(packet.related_idea_id)
        finally:
            db.close()

        history_resp = self.client.get("/api/v1/collab/packets/packet-006/history")
        self.assertEqual(history_resp.status_code, 200)
        history_rows = history_resp.json()
        pipeline_event = next((row for row in history_rows if row.get("event_type") == "stock_pipeline_attempted"), None)
        self.assertIsNotNone(pipeline_event)
        self.assertIn('"source_ai": "claude"', pipeline_event.get("note", ""))
        self.assertIn('"requested": true', pipeline_event.get("note", ""))

    def test_stock_packet_idea_registration_is_blocked_without_industry_outlook(self):
        packet_payload = {
            "packet_id": "packet-007",
            "source_ai": "claude",
            "topic": "테스트 종목 (123456)",
            "category": "PORTFOLIO",
            "content_json": json.dumps({"summary": "stock check", "packet_type": "종목"}),
            "request_action": "validate",
            "request_ask": "아이디어 등록 조건 테스트",
            "related_idea_id": None,
        }
        create_resp = self.client.post("/api/v1/collab/packets", json=packet_payload)
        self.assertEqual(create_resp.status_code, 200)

        triage_payload = {
            "action": "validate",
            "packet_type": "종목",
            "create_idea": True,
            "result_summary": "정량 점수는 양호",
            "result_evidence": "증거 존재",
            "result_confidence": 78,
            # result_industry_outlook intentionally omitted
        }
        triage_resp = self.client.put("/api/v1/collab/packets/packet-007/triage", json=triage_payload)
        self.assertEqual(triage_resp.status_code, 409)
        detail = triage_resp.json().get("detail", {})
        self.assertTrue(detail.get("blocked"))
        self.assertEqual(detail.get("rule_code"), "gate_bypass_attempt")
        self.assertIn("create_idea_requested_but_gate_denied", detail.get("reasons", []))

        db = self.session_local()
        try:
            packet = db.query(CollabPacket).filter(CollabPacket.packet_id == "packet-007").first()
            self.assertIsNotNone(packet)
            self.assertIsNone(packet.related_idea_id)
        finally:
            db.close()

    def test_stock_like_sector_packet_still_applies_stock_gate(self):
        packet_payload = {
            "packet_id": "packet-009",
            "source_ai": "claude",
            "topic": "삼성전자(005930) BM/해자/투자가치 점검",
            "category": "SECTOR",
            "content_json": json.dumps({"summary": "삼성전자 BM 해자 평가"}),
            "request_action": "validate",
            "request_ask": "종목 평가 요청",
            "related_idea_id": None,
        }
        create_resp = self.client.post("/api/v1/collab/packets", json=packet_payload)
        self.assertEqual(create_resp.status_code, 200)

        triage_payload = {
            "action": "validate",
            "create_idea": True,
            "result_summary": "정량 점검 완료",
            "result_confidence": 80,
        }
        with patch.object(collab_api, "_run_stock_moat_analysis", return_value={"status": "failed"}):
            triage_resp = self.client.put("/api/v1/collab/packets/packet-009/triage", json=triage_payload)

        self.assertEqual(triage_resp.status_code, 409)
        detail = triage_resp.json().get("detail", {})
        self.assertTrue(detail.get("blocked"))
        self.assertIn(
            detail.get("rule_code"),
            {"classification_consistency", "required_pipeline_execution"},
        )

    def test_stock_packet_force_create_idea_overrides_gate(self):
        packet_payload = {
            "packet_id": "packet-008",
            "source_ai": "claude",
            "topic": "강제 등록 종목 (654321)",
            "category": "PORTFOLIO",
            "content_json": json.dumps({"summary": "stock check", "packet_type": "종목"}),
            "request_action": "validate",
            "request_ask": "강제 아이디어 등록 테스트",
            "related_idea_id": None,
        }
        create_resp = self.client.post("/api/v1/collab/packets", json=packet_payload)
        self.assertEqual(create_resp.status_code, 200)

        triage_payload = {
            "action": "validate",
            "packet_type": "종목",
            "create_idea": True,
            "force_create_idea": True,
            "result_summary": "요약만 있는 상태",
        }
        triage_resp = self.client.put("/api/v1/collab/packets/packet-008/triage", json=triage_payload)
        self.assertEqual(triage_resp.status_code, 200)
        body = triage_resp.json()
        self.assertIsNotNone(body.get("idea"))
        self.assertIn("idea_gate", body)
        self.assertTrue(body["idea_gate"]["should_create"])


if __name__ == "__main__":
    unittest.main()
