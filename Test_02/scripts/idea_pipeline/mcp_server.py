"""MCP Server for Stock Research ONE Idea Collaboration

Claude가 세션마다 자동으로 로드하여 아이디어 관리 + AI 협업을 수행.
"""
import os
import sys
import json
import hashlib
import uuid
import re
from datetime import datetime, date, timedelta

sys.stdout.reconfigure(encoding="utf-8")

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _project_root)

_db_path = os.path.join(_project_root, "backend", "stock_research.db")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_db_path}")
os.environ.setdefault("DEBUG", "false")

from mcp.server.fastmcp import FastMCP
try:
    from scripts.idea_pipeline.monitoring_adapter import enforce_monitoring
except Exception:  # pragma: no cover - fallback for direct script execution
    from monitoring_adapter import enforce_monitoring

mcp = FastMCP("idea-collab")
_STOCK_CODE_RE = re.compile(r"(?<!\d)(\d{6})(?!\d)")

# ─── helpers ───

def _get_db():
    from backend.app.database import SessionLocal, engine, Base
    import backend.app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def _json_serial(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def _collab_dir():
    d = os.path.join(_project_root, "data", "collab")
    os.makedirs(os.path.join(d, "packets"), exist_ok=True)
    return d


def _looks_like_stock_eval(topic: str, category: str, summary: str, key_claims: list, data_points: list) -> bool:
    text_parts = [
        str(topic or ""),
        str(category or ""),
        str(summary or ""),
        " ".join(str(item or "") for item in (key_claims or [])),
        " ".join(
            f"{str((point or {}).get('metric', ''))}:{str((point or {}).get('value', ''))}"
            for point in (data_points or [])
            if isinstance(point, dict)
        ),
    ]
    merged = " ".join(text_parts)
    if _STOCK_CODE_RE.search(merged):
        return True

    lowered = merged.lower()
    tokens = ["해자", "투자가치", "bm", "moat", "ttm", "op_multiple", "시가총액"]
    hit_count = sum(1 for token in tokens if token in lowered or token in merged)
    return hit_count >= 2


# ─── MCP Tools ───

@mcp.tool()
def get_active_ideas(status: str = "active", category: str = None, limit: int = 20) -> str:
    """활성 아이디어 목록 조회"""
    from backend.app.models.idea import Idea
    db = _get_db()
    try:
        q = db.query(Idea).filter(Idea.status == status)
        if category:
            q = q.filter(Idea.category == category)
        ideas = q.order_by(Idea.updated_at.desc()).limit(limit).all()
        result = []
        for i in ideas:
            result.append({
                "id": i.id,
                "title": i.title,
                "category": i.category,
                "thesis": i.thesis,
                "status": i.status,
                "priority": i.priority,
                "updated_at": i.updated_at,
            })
        return json.dumps(result, default=_json_serial, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def get_pending_packets(source_ai: str = None) -> str:
    """미처리 협업 패킷 조회 (pending 상태)"""
    from backend.app.models.collab import CollabPacket
    db = _get_db()
    try:
        q = db.query(CollabPacket).filter(CollabPacket.status == "pending")
        if source_ai:
            q = q.filter(CollabPacket.source_ai == source_ai)
        packets = q.order_by(CollabPacket.created_at.desc()).limit(10).all()
        result = []
        for p in packets:
            result.append({
                "packet_id": p.packet_id,
                "source_ai": p.source_ai,
                "topic": p.topic,
                "category": p.category,
                "request_action": p.request_action,
                "content": json.loads(p.content_json) if p.content_json else None,
                "created_at": p.created_at,
            })
        return json.dumps(result, default=_json_serial, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def export_packet(topic: str, category: str, summary: str, key_claims: list,
                  request_action: str = "validate", confidence: float = 0.7,
                  data_points: list = None, source_links: list = None) -> str:
    """현재 분석을 Context Packet으로 저장 (DB + 파일)"""
    from backend.app.models.collab import CollabPacket, CollabPacketHistory
    db = _get_db()
    try:
        packet_id = str(uuid.uuid4())
        normalized_category = category
        stock_context = _looks_like_stock_eval(topic, category, summary, key_claims, data_points or [])
        content = {
            "summary": summary,
            "key_claims": key_claims,
            "data_points": data_points or [],
            "confidence": confidence,
            "source_links": source_links or [],
        }
        if stock_context:
            normalized_category = "PORTFOLIO"
            content["packet_type"] = "종목"
        elif str(category or "").upper() == "SECTOR":
            content["packet_type"] = "섹터산업"

        monitor_result = enforce_monitoring(
            {
                "req_id": "REQ-007",
                "enforce_requirement_contract": True,
                "consistency_monitoring_enabled": True,
                "source_path": "scripts.idea_pipeline.mcp_server.export_packet",
                "entity_type": "collab_packet",
                "entity_id": packet_id,
                "requirement_refs": ["REQUESTS.md#REQ-007", "REQUESTS.md#REQ-008", "REQUESTS.md#REQ-009"],
                "plan_refs": ["docs/plans/2026-02-15-global-monitoring-guard-implementation.md"],
                "design_refs": [
                    "docs/plans/2026-02-15-global-monitoring-guard-design.md",
                    "docs/plans/2026-02-15-global-monitoring-guard-implementation.md",
                ],
                "test_tags": ["mcp_export", "monitoring_guard"],
                "category": normalized_category,
                "packet_type": content.get("packet_type"),
                "stock_context": stock_context,
                "run_stock_pipeline": False,
                "pipeline_executed": False,
                "pipeline_error": "",
                "create_idea": False,
                "idea_gate_should_create": False,
                "force_create_idea": False,
                "traceability_ok": bool(topic and summary and request_action),
                "ticker": "",
                "stock_name": "",
            },
            hard_block=True,
        )
        if monitor_result.blocked:
            return json.dumps(
                {
                    "status": "blocked",
                    "blocked": True,
                    "packet_id": packet_id,
                    "incident_id": monitor_result.incident_id,
                    "rule_code": monitor_result.rule_code,
                    "reasons": monitor_result.reasons or [],
                    "approver": "codex",
                },
                ensure_ascii=False,
            )

        packet_json = {
            "packet_id": packet_id,
            "source_ai": "claude",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "topic": topic,
            "category": normalized_category,
            "packet_type": content.get("packet_type"),
            "context": content,
            "request_action": request_action,
            "related_idea_id": None,
        }

        # DB 저장
        db_item = CollabPacket(
            packet_id=packet_id,
            source_ai="claude",
            topic=topic,
            category=normalized_category,
            content_json=json.dumps(content, ensure_ascii=False),
            request_action=request_action,
            status="pending",
        )
        db.add(db_item)
        db.add(
            CollabPacketHistory(
                packet_id=packet_id,
                event_type="created",
                action=request_action,
                packet_type=content.get("packet_type"),
                note=summary,
                work_date=date.today().isoformat(),
            )
        )
        db.commit()

        # 파일 저장
        file_path = os.path.join(_collab_dir(), "packets", f"{packet_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(packet_json, f, ensure_ascii=False, indent=2)

        return json.dumps({
            "status": "exported",
            "packet_id": packet_id,
            "category": normalized_category,
            "packet_type": content.get("packet_type"),
            "file": file_path,
            "instruction": "Copy the packet JSON above and paste to Gemini/ChatGPT for cross-verification.",
        }, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def import_packet(packet_json: str) -> str:
    """다른 AI의 응답 패킷을 DB + 파일에 저장"""
    from backend.app.models.collab import CollabPacket
    db = _get_db()
    try:
        data = json.loads(packet_json)
        packet_id = data.get("packet_id", str(uuid.uuid4()))
        source_ai = data.get("source_ai", "unknown")
        topic = data.get("topic", "")
        category = data.get("category", "")
        context = data.get("context", {})
        request_action = data.get("request_action", "validate")

        db_item = CollabPacket(
            packet_id=packet_id,
            source_ai=source_ai,
            topic=topic,
            category=category,
            content_json=json.dumps(context, ensure_ascii=False),
            request_action=request_action,
            status="received",
        )
        db.add(db_item)
        db.commit()

        file_path = os.path.join(_collab_dir(), "packets", f"{packet_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return json.dumps({
            "status": "imported",
            "packet_id": packet_id,
            "source_ai": source_ai,
            "topic": topic,
        }, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def get_collab_triggers() -> str:
    """협업 트리거 조건 목록 반환"""
    triggers = [
        {"condition": "major_investment_decision", "message": "이 분석은 중요한 투자 판단입니다. 교차검증을 위해 Context Packet을 생성하시겠습니까?"},
        {"condition": "one_sided_analysis", "message": "이 분석은 한 방향만 고려합니다. 반대 관점을 다른 AI에 요청하시겠습니까?"},
        {"condition": "stale_data", "message": "실시간 데이터 확인이 필요합니다. Gemini에서 최신 데이터를 확인하시겠습니까?"},
        {"condition": "hypothesis_testing", "message": "이 아이디어가 testing 단계로 진입합니다. 다른 AI에서 가설을 검증하시겠습니까?"},
    ]
    return json.dumps(triggers, ensure_ascii=False)


@mcp.tool()
def get_daily_work_summary(days: int = 7, category: str = None) -> str:
    """최근 일일작업 요약"""
    from backend.app.models.daily_work import DailyWork
    db = _get_db()
    try:
        since = date.today() - timedelta(days=days)
        q = db.query(DailyWork).filter(DailyWork.date >= since)
        if category:
            q = q.filter(DailyWork.category == category)
        items = q.order_by(DailyWork.date.desc()).all()
        result = []
        for w in items:
            result.append({
                "id": w.id,
                "date": w.date,
                "category": w.category,
                "description": w.description[:200] if w.description else "",
                "content_preview": w.content[:300] if w.content else "",
            })
        return json.dumps(result, default=_json_serial, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def create_idea_from_insights(title: str, thesis: str, category: str,
                               insight_ids: list = None) -> str:
    """인사이트 기반으로 아이디어 생성"""
    from backend.app.models.idea import Idea
    from backend.app.models.idea_evidence import IdeaEvidence
    db = _get_db()
    try:
        idea = Idea(
            title=title,
            content=thesis,
            thesis=thesis,
            category=category,
            status="draft",
            priority=3,
        )
        db.add(idea)
        db.flush()

        if insight_ids:
            for iid in insight_ids:
                ev = IdeaEvidence(
                    idea_id=idea.id,
                    insight_id=iid,
                    relation_type="supports",
                )
                db.add(ev)

        db.commit()
        return json.dumps({
            "status": "created",
            "idea_id": idea.id,
            "title": title,
            "linked_insights": len(insight_ids) if insight_ids else 0,
        }, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def get_cross_module_briefing(days: int = 3) -> str:
    """전체 모듈 데이터를 구조화된 시장 브리핑으로 반환.

    유동성 스트레스, 공시 요약, 일일작업 카테고리별 핵심,
    이벤트 캘린더, 섹터 모멘텀, 기존 아이디어 현황 포함.
    이 브리핑을 기반으로 투자 아이디어를 생성하세요.

    Args:
        days: 조회 기간 (기본 3일)

    Returns:
        JSON 형식의 크로스 모듈 브리핑
    """
    from backend.app.services.cross_module_service import CrossModuleService
    db = _get_db()
    try:
        service = CrossModuleService(db)
        ctx = service.get_full_context(days=days)
        return json.dumps(ctx, default=_json_serial, ensure_ascii=False)
    finally:
        db.close()


# ─── MCP Resources ───

@mcp.resource("collab://protocol")
def get_protocol() -> str:
    """COLLAB_PROTOCOL.md 내용"""
    path = os.path.join(_collab_dir(), "COLLAB_PROTOCOL.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "Protocol file not found."


@mcp.resource("collab://state")
def get_state() -> str:
    """현재 협업 상태"""
    from backend.app.models.idea import Idea
    from backend.app.models.collab import CollabPacket
    from backend.app.models.daily_work import DailyWork
    from sqlalchemy import func
    db = _get_db()
    try:
        state = {
            "active_ideas": db.query(Idea).filter(Idea.status.in_(["draft", "active", "testing"])).count(),
            "pending_packets": db.query(CollabPacket).filter(CollabPacket.status == "pending").count(),
            "total_daily_work": db.query(DailyWork).count(),
            "latest_work_date": str(db.query(func.max(DailyWork.date)).scalar() or "none"),
            "categories_with_data": [r[0] for r in db.query(DailyWork.category).distinct().all()],
        }
        return json.dumps(state, ensure_ascii=False)
    finally:
        db.close()


@mcp.resource("collab://packets/latest")
def get_latest_packets() -> str:
    """최근 패킷 5개"""
    from backend.app.models.collab import CollabPacket
    db = _get_db()
    try:
        packets = db.query(CollabPacket).order_by(CollabPacket.created_at.desc()).limit(5).all()
        result = []
        for p in packets:
            result.append({
                "packet_id": p.packet_id,
                "source_ai": p.source_ai,
                "topic": p.topic,
                "status": p.status,
                "created_at": p.created_at,
            })
        return json.dumps(result, default=_json_serial, ensure_ascii=False)
    finally:
        db.close()


@mcp.resource("collab://briefing/latest")
def get_latest_briefing() -> str:
    """최신 크로스 모듈 브리핑 (세션 시작 시 자동 로드)"""
    from backend.app.services.cross_module_service import CrossModuleService
    db = _get_db()
    try:
        service = CrossModuleService(db)
        ctx = service.get_full_context(days=3)
        return json.dumps(ctx, default=_json_serial, ensure_ascii=False)
    finally:
        db.close()


# ─── Signal Intelligence Tools ───

@mcp.tool()
def generate_signals(days: int = 3) -> str:
    """시그널 생성 실행 — Cross-Data 규칙 엔진으로 투자 시그널 탐지

    Args:
        days: 컨텍스트 수집 기간 (기본 3일)

    Returns:
        생성된 시그널 목록 (JSON)
    """
    from backend.app.services.signal_service import SignalDetectionEngine
    db = _get_db()
    try:
        engine = SignalDetectionEngine(db)
        signals = engine.generate_signals(days=days)
        return json.dumps({
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "count": len(signals),
            "signals": signals,
        }, default=_json_serial, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def get_signals(status: str = None, category: str = None, limit: int = 10) -> str:
    """시그널 목록 조회

    Args:
        status: 상태 필터 (new, reviewed, accepted, rejected)
        category: 카테고리 필터 (RISK, SECTOR, PORTFOLIO, THEME)
        limit: 조회 건수 (기본 10)

    Returns:
        시그널 목록 (JSON)
    """
    from backend.app.models.signal import Signal
    db = _get_db()
    try:
        q = db.query(Signal)
        if status:
            q = q.filter(Signal.status == status)
        if category:
            q = q.filter(Signal.category == category)
        signals = q.order_by(Signal.created_at.desc()).limit(limit).all()
        result = []
        for s in signals:
            result.append({
                "id": s.id,
                "signal_id": s.signal_id,
                "title": s.title,
                "category": s.category,
                "confidence": s.confidence,
                "status": s.status,
                "data_sources": json.loads(s.data_sources) if s.data_sources else [],
                "suggested_action": s.suggested_action,
                "created_at": s.created_at,
            })
        return json.dumps(result, default=_json_serial, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def interpret_signal(signal_id: int) -> str:
    """AI 전략가 해석 요청 — Claude API로 시그널의 투자적 의미 분석

    Args:
        signal_id: 시그널 DB ID

    Returns:
        AI 해석 결과 (JSON)
    """
    from backend.app.models.signal import Signal
    from backend.app.services.strategist_service import StrategistService
    from backend.app.services.cross_module_service import CrossModuleService
    db = _get_db()
    try:
        signal = db.query(Signal).filter(Signal.id == signal_id).first()
        if not signal:
            return json.dumps({"error": f"Signal {signal_id} not found"})

        signal_dict = {
            "title": signal.title,
            "category": signal.category,
            "confidence": signal.confidence,
            "evidence": json.loads(signal.evidence) if signal.evidence else [],
            "suggested_action": signal.suggested_action,
        }
        context = CrossModuleService(db).get_full_context(days=3)
        strategist = StrategistService()
        result = strategist.interpret_signal(signal_dict, context)

        if result.get("interpretation"):
            signal.ai_interpretation = json.dumps(result, ensure_ascii=False)
            db.commit()

        return json.dumps(result, default=_json_serial, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def analyze_data_gaps(signal_id: int = None) -> str:
    """데이터 갭 분석 — 부족한 데이터와 외부 소스 추천

    Args:
        signal_id: 특정 시그널 (없으면 전체 갭 분석)

    Returns:
        갭 분석 결과 + 외부 소스 추천 (JSON)
    """
    from backend.app.models.signal import Signal
    from backend.app.services.gap_analyzer import GapAnalyzer
    from backend.app.services.cross_module_service import CrossModuleService
    db = _get_db()
    try:
        context = CrossModuleService(db).get_full_context(days=3)
        analyzer = GapAnalyzer()

        if signal_id:
            signal = db.query(Signal).filter(Signal.id == signal_id).first()
            if not signal:
                return json.dumps({"error": f"Signal {signal_id} not found"})
            signal_dict = {
                "category": signal.category,
                "evidence": json.loads(signal.evidence) if signal.evidence else [],
            }
            result = analyzer.analyze(signal_dict, context)
        else:
            # 전체 갭 분석
            result = analyzer.analyze({"category": "ALL", "evidence": []}, context)

        return json.dumps(result, default=_json_serial, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def recommend_sources(category: str = None) -> str:
    """외부 소스 추천 — 미연동 데이터 소스 목록과 시너지 설명

    Args:
        category: 카테고리 필터 (RISK, SECTOR, PORTFOLIO, THEME)

    Returns:
        추천 외부 소스 목록 (JSON)
    """
    from backend.app.services.gap_analyzer import GapAnalyzer
    analyzer = GapAnalyzer()
    sources = analyzer.external_sources
    result = []
    for src in sources:
        if src.get("connected"):
            continue
        if category and src.get("category") not in (category, "ALL"):
            continue
        result.append({
            "id": src["id"],
            "name": src["name"],
            "category": src.get("category"),
            "synergy": src.get("synergy"),
            "confidence_boost": src.get("confidence_boost"),
            "url": src.get("url"),
            "api_required": src.get("api_required"),
        })
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def accept_signal(signal_id: int) -> str:
    """시그널 채택 → Idea 자동 생성

    Args:
        signal_id: 채택할 시그널 DB ID

    Returns:
        생성된 Idea 정보 (JSON)
    """
    from backend.app.services.signal_service import SignalDetectionEngine
    db = _get_db()
    try:
        engine = SignalDetectionEngine(db)
        result = engine.accept_signal(signal_id)
        if not result:
            return json.dumps({"error": f"Signal {signal_id} not found"})
        return json.dumps(result, default=_json_serial, ensure_ascii=False)
    finally:
        db.close()


# ─── Signal Resources ───

@mcp.resource("collab://signals/latest")
def get_latest_signals() -> str:
    """최근 시그널 5개"""
    from backend.app.models.signal import Signal
    db = _get_db()
    try:
        signals = db.query(Signal).order_by(Signal.created_at.desc()).limit(5).all()
        result = []
        for s in signals:
            result.append({
                "signal_id": s.signal_id,
                "title": s.title,
                "category": s.category,
                "confidence": s.confidence,
                "status": s.status,
                "created_at": s.created_at,
            })
        return json.dumps(result, default=_json_serial, ensure_ascii=False)
    finally:
        db.close()


@mcp.resource("collab://gaps/summary")
def get_gaps_summary() -> str:
    """현재 데이터 갭 요약"""
    from backend.app.services.gap_analyzer import GapAnalyzer
    from backend.app.services.cross_module_service import CrossModuleService
    db = _get_db()
    try:
        context = CrossModuleService(db).get_full_context(days=3)
        analyzer = GapAnalyzer()
        result = analyzer.analyze({"category": "ALL", "evidence": []}, context)
        return json.dumps(result, default=_json_serial, ensure_ascii=False)
    finally:
        db.close()


# ─── entry point ───

# consistency-monitoring: runtime-exempt (MCP host can start/stop without processing a tool call)
if __name__ == "__main__":
    mcp.run()
