import json
import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.collab import CollabPacket as PacketModel, CollabSession as SessionModel, CollabPacketHistory as HistoryModel
from ..models.idea import Idea as IdeaModel
from ..services.monitoring_guard_service import MonitoringBlockedError, MonitoringGuardService
from ..schemas.collab import (
    CollabInboxItem,
    CollabIdeaGate,
    CollabIdeaSummary,
    CollabPacket,
    CollabPacketCreate,
    CollabPacketHistoryItem,
    CollabPacketStatusUpdate,
    CollabPacketTriageRequest,
    CollabPacketTriageResponse,
    CollabSession,
    CollabSessionCreate,
    CollabState,
)

router = APIRouter(
    prefix="/api/v1/collab",
    tags=["collab"],
)

# Raw text policy:
# Do not hide suspicious strings like "???" at API layer.
# Preserve original values for root-cause tracing and upstream fixes.
ACTION_TO_IDEA_STATUS = {
    "validate": "testing",
    "extend": "active",
    "challenge": "testing",
    "infer": "testing",
    "synthesize": "validated",
}
ACTION_LABELS = {
    "validate": "검증",
    "extend": "확장",
    "challenge": "반박",
    "infer": "추정(추론)",
    "synthesize": "종합",
}

VALID_IDEA_STATUSES = {"draft", "active", "testing", "validated", "invalidated", "archived"}
PACKET_TYPE_TERMS = {
    "시장기대",
    "시장우려",
    "섹터산업",
    "종목",
    "트랜드",
    "주요일정",
    "이슈전망",
}
CATEGORY_TO_PACKET_TYPE = {
    "SECTOR": "섹터산업",
    "US_MARKET": "시장기대",
    "RISK": "시장우려",
    "THEME": "트랜드",
    "NEXT_DAY": "주요일정",
    "PORTFOLIO": "종목",
    "AI_RESEARCH": "이슈전망",
    "CROSS": "이슈전망",
}
_STOCK_CODE_RE = re.compile(r"(?<!\d)(\d{6})(?!\d)")
_STOCK_PIPELINE_INSTANCE = None


def _parse_content_json(raw_value: Optional[str]) -> dict:
    if not raw_value:
        return {}
    if isinstance(raw_value, dict):
        return raw_value
    try:
        parsed = json.loads(raw_value)
    except Exception:
        return {"raw_text": raw_value}
    if isinstance(parsed, dict):
        return parsed
    return {"raw_data": parsed}


def _normalize_packet_type(raw_value: Optional[str]) -> Optional[str]:
    if raw_value is None:
        return None
    value = str(raw_value).strip()
    if not value:
        return None
    if value in PACKET_TYPE_TERMS:
        return value
    mapped = CATEGORY_TO_PACKET_TYPE.get(value.upper())
    if mapped:
        return mapped
    try:
        repaired = value.encode("latin1").decode("utf-8")
        if repaired in PACKET_TYPE_TERMS:
            return repaired
        mapped_repaired = CATEGORY_TO_PACKET_TYPE.get(repaired.upper())
        if mapped_repaired:
            return mapped_repaired
        return repaired
    except Exception:
        return value


def _repair_mojibake(value: str) -> str:
    try:
        repaired = value.encode("latin1").decode("utf-8")
        return repaired
    except Exception:
        return value


def _clean_text(value: Optional[str], fallback: str = "-") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    if not text:
        return fallback
    text = _repair_mojibake(text)
    text = " ".join(text.split())
    return text if text else fallback


def _extract_packet_type(payload: dict, fallback: Optional[str] = None) -> Optional[str]:
    return _normalize_packet_type(payload.get("packet_type")) or _normalize_packet_type(fallback)


def _today_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _record_history(
    db: Session,
    packet_id: str,
    event_type: str,
    *,
    action: Optional[str] = None,
    packet_type: Optional[str] = None,
    assignee_ai: Optional[str] = None,
    due_at: Optional[datetime] = None,
    note: Optional[str] = None,
):
    entry = HistoryModel(
        packet_id=packet_id,
        event_type=event_type,
        action=action,
        packet_type=_normalize_packet_type(packet_type),
        assignee_ai=(assignee_ai or "").strip() or None,
        due_at=due_at,
        note=note,
        work_date=_today_utc(),
    )
    db.add(entry)


def _safe_parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            return None
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except Exception:
            return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _resolve_idea_status(action: str, explicit_status: Optional[str]) -> str:
    if explicit_status:
        normalized = explicit_status.strip().lower()
        if normalized in VALID_IDEA_STATUSES:
            return normalized
    return ACTION_TO_IDEA_STATUS.get(action, "active")


def _merge_tags(existing_tags, category: Optional[str], action: str):
    merged = list(existing_tags or [])
    for value in [action, (category or "").lower()]:
        if value and value not in merged:
            merged.append(value)
    return merged


def _build_idea_content(packet: PacketModel, payload: dict, note: Optional[str]) -> str:
    summary = payload.get("summary")
    triage_meta = payload.get("_triage") if isinstance(payload.get("_triage"), dict) else {}
    result = triage_meta.get("result") if isinstance(triage_meta.get("result"), dict) else {}
    details = []
    if summary:
        details.append(f"Summary: {summary}")
    if packet.request_ask:
        details.append(f"Ask: {packet.request_ask}")
    if note:
        details.append(f"Triage note: {note}")
    if result.get("summary"):
        details.append(f"Result summary: {result.get('summary')}")
    if result.get("evidence"):
        details.append(f"Key evidence: {result.get('evidence')}")
    if result.get("risks"):
        details.append(f"Key risks: {result.get('risks')}")
    if result.get("next_step"):
        details.append(f"Next step: {result.get('next_step')}")
    if result.get("confidence") is not None:
        details.append(f"Confidence: {result.get('confidence')}/100")
    if result.get("industry_outlook"):
        details.append(f"Industry outlook: {result.get('industry_outlook')}")
    if result.get("consensus_revenue") is not None or result.get("consensus_op_income") is not None:
        unit = result.get("consensus_unit") or "억원"
        details.append(
            f"Consensus: revenue {result.get('consensus_revenue')} {unit}, "
            f"op_income {result.get('consensus_op_income')} {unit}"
        )
    scenario_parts = []
    if result.get("scenario_bear"):
        scenario_parts.append(f"bear={result.get('scenario_bear')}")
    if result.get("scenario_base"):
        scenario_parts.append(f"base={result.get('scenario_base')}")
    if result.get("scenario_bull"):
        scenario_parts.append(f"bull={result.get('scenario_bull')}")
    if scenario_parts:
        details.append(f"Scenario: {' | '.join(scenario_parts)}")
    if result.get("final_comment"):
        details.append(f"Investment comment: {result.get('final_comment')}")
    body = "\n".join(details).strip()
    return body or str(payload.get("raw_text") or packet.topic or "No detail")


def _build_final_comment(result_payload: dict, action: str, packet_type: Optional[str]) -> Optional[str]:
    if result_payload.get("final_comment"):
        return result_payload.get("final_comment")

    parts = []
    summary = result_payload.get("summary")
    if summary:
        parts.append(f"결론: {summary}")

    outlook = result_payload.get("industry_outlook")
    if outlook:
        parts.append(f"업황: {outlook}")

    rev = result_payload.get("consensus_revenue")
    opi = result_payload.get("consensus_op_income")
    if rev is not None or opi is not None:
        unit = result_payload.get("consensus_unit") or "억원"
        parts.append(f"2026E 컨센서스 매출 {rev} {unit}, 영업이익 {opi} {unit}")

    scenario_tokens = []
    if result_payload.get("scenario_bear"):
        scenario_tokens.append(f"bear={result_payload.get('scenario_bear')}")
    if result_payload.get("scenario_base"):
        scenario_tokens.append(f"base={result_payload.get('scenario_base')}")
    if result_payload.get("scenario_bull"):
        scenario_tokens.append(f"bull={result_payload.get('scenario_bull')}")
    if scenario_tokens:
        parts.append(f"시나리오: {' / '.join(scenario_tokens)}")

    action_label = ACTION_LABELS.get(action, action)
    if action_label:
        parts.append(f"현재 단계: {action_label}")
    if packet_type:
        parts.append(f"유형: {packet_type}")

    if not parts:
        return None
    return " | ".join(parts)


def _is_stock_packet(packet_type: Optional[str], category: Optional[str]) -> bool:
    if (category or "").upper() == "PORTFOLIO":
        return True
    stock_packet_type = CATEGORY_TO_PACKET_TYPE.get("PORTFOLIO")
    return bool(stock_packet_type and packet_type == stock_packet_type)


def _looks_like_stock_context(packet: PacketModel, payload: dict, result_payload: Optional[dict] = None) -> bool:
    texts = [
        str(packet.topic or ""),
        str(packet.request_ask or ""),
        str(payload.get("summary") or ""),
        str(payload.get("request_ask") or ""),
        str(payload.get("topic") or ""),
    ]
    if isinstance(result_payload, dict):
        texts.extend(
            [
                str(result_payload.get("summary") or ""),
                str(result_payload.get("evidence") or ""),
                str(result_payload.get("next_step") or ""),
                str(result_payload.get("final_comment") or ""),
            ]
        )

    combined = " ".join(texts)
    has_ticker = bool(_STOCK_CODE_RE.search(combined))
    stock_keywords = [
        "해자",
        "투자가치",
        "bm",
        "moat",
        "op_multiple",
        "ttm",
        "기업가치",
    ]
    lowered = combined.lower()
    keyword_hits = sum(1 for token in stock_keywords if token in lowered or token in combined)
    return has_ticker or keyword_hits >= 2


def _extract_stock_target(req: CollabPacketTriageRequest, packet: PacketModel, payload: dict) -> tuple[Optional[str], Optional[str]]:
    ticker = (req.stock_ticker or "").strip()
    name = (req.stock_name or "").strip()

    if not ticker:
        for key in ["stock_ticker", "ticker", "stock_code", "code"]:
            value = payload.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if _STOCK_CODE_RE.fullmatch(text):
                ticker = text
                break

    if not ticker:
        candidates = [
            packet.topic,
            packet.request_ask,
            payload.get("topic"),
            payload.get("request_ask"),
            payload.get("summary"),
        ]
        for value in candidates:
            match = _STOCK_CODE_RE.search(str(value or ""))
            if match:
                ticker = match.group(1)
                break

    if ticker:
        ticker = ticker.zfill(6)

    if not name:
        for key in ["stock_name", "company_name", "name"]:
            value = payload.get(key)
            if value:
                name = str(value).strip()
                if name:
                    break

    if not name and packet.topic:
        topic = str(packet.topic).strip()
        if ticker:
            topic = topic.replace(ticker, " ")
        topic = topic.replace("(", " ").replace(")", " ").replace("[", " ").replace("]", " ")
        topic = " ".join(topic.split())
        if topic:
            name = topic

    return ticker or None, name or None


def _confidence_to_score(*values) -> int:
    scale = {"high": 85, "medium": 70, "low": 55}
    for value in values:
        if value is None:
            continue
        if isinstance(value, (int, float)):
            return int(value)
        normalized = str(value).strip().lower()
        if normalized in scale:
            return scale[normalized]
    return 65


def _scenario_value(scenarios: list, scenario_name: str, key: str) -> Optional[str]:
    for item in scenarios or []:
        if str(item.get("scenario", "")).lower() != scenario_name:
            continue
        value = item.get(key)
        if value is None:
            return None
        return str(value)
    return None


def _merge_stock_analysis_result(result_payload: dict, analysis_result: Optional[dict]) -> dict:
    if not isinstance(analysis_result, dict):
        return dict(result_payload)
    if analysis_result.get("status") == "failed":
        return dict(result_payload)

    merged = dict(result_payload)
    moat_strength = analysis_result.get("해자강도", analysis_result.get("?댁옄媛뺣룄"))
    investment_value = analysis_result.get("investment_value")
    core_desc = analysis_result.get("core_desc")
    bm_summary = analysis_result.get("bm_summary")
    evidence_summary = analysis_result.get("evidence_summary")
    investment_comment = analysis_result.get("investment_comment")

    industry = analysis_result.get("industry_outlook") or {}
    consensus = analysis_result.get("consensus_2026") or {}
    scenarios = analysis_result.get("forecast_scenarios") or []

    if not merged.get("summary"):
        summary_parts = []
        if core_desc:
            summary_parts.append(str(core_desc))
        if moat_strength is not None:
            summary_parts.append(f"Moat {moat_strength}/5")
        if investment_value is not None:
            summary_parts.append(f"Value {investment_value}/5")
        if summary_parts:
            merged["summary"] = " | ".join(summary_parts)

    if not merged.get("evidence") and evidence_summary:
        merged["evidence"] = str(evidence_summary)
    if not merged.get("industry_outlook") and industry.get("summary"):
        merged["industry_outlook"] = str(industry.get("summary"))

    if merged.get("consensus_revenue") is None and consensus.get("revenue_est") is not None:
        merged["consensus_revenue"] = consensus.get("revenue_est")
    if merged.get("consensus_op_income") is None and consensus.get("op_income_est") is not None:
        merged["consensus_op_income"] = consensus.get("op_income_est")
    if not merged.get("consensus_unit") and consensus.get("unit"):
        merged["consensus_unit"] = consensus.get("unit")

    if not merged.get("scenario_bear"):
        value = _scenario_value(scenarios, "bear", "op_income_est")
        if value is not None:
            merged["scenario_bear"] = value
    if not merged.get("scenario_base"):
        value = _scenario_value(scenarios, "base", "op_income_est")
        if value is not None:
            merged["scenario_base"] = value
    if not merged.get("scenario_bull"):
        value = _scenario_value(scenarios, "bull", "op_income_est")
        if value is not None:
            merged["scenario_bull"] = value

    if not merged.get("final_comment") and investment_comment:
        merged["final_comment"] = str(investment_comment)
    if not merged.get("next_step") and bm_summary:
        merged["next_step"] = f"BM: {bm_summary}"

    if merged.get("confidence") is None:
        merged["confidence"] = _confidence_to_score(consensus.get("confidence"), industry.get("confidence"))

    return {k: v for k, v in merged.items() if v is not None}


def _run_stock_moat_analysis(ticker: str, name: str, year: str = "auto") -> Optional[dict]:
    if not ticker or not name:
        return None

    global _STOCK_PIPELINE_INSTANCE

    from pathlib import Path
    import sys

    project_root = Path(__file__).resolve().parents[3]
    utils_dir = str(project_root / ".agent/skills/stock-moat/utils")
    scripts_dir = str(project_root / "scripts/stock_moat")

    if utils_dir not in sys.path:
        sys.path.insert(0, utils_dir)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    from analyze_with_evidence import EvidenceBasedMoatPipeline

    if _STOCK_PIPELINE_INSTANCE is None:
        _STOCK_PIPELINE_INSTANCE = EvidenceBasedMoatPipeline()

    result = _STOCK_PIPELINE_INSTANCE.analyze_stock(ticker, name, year or "auto")
    return result if isinstance(result, dict) else None


def _evaluate_idea_gate(
    *,
    create_idea: bool,
    force_create_idea: bool,
    is_stock_context: bool,
    packet_type: Optional[str],
    category: Optional[str],
    result_payload: dict,
) -> dict:
    if not create_idea:
        return {"should_create": False, "reasons": ["create_idea_disabled"]}

    if force_create_idea:
        return {"should_create": True, "reasons": ["force_create_idea"]}

    if not is_stock_context:
        return {"should_create": True, "reasons": ["non_stock_packet"]}

    reasons = []
    outlook = str(result_payload.get("industry_outlook") or "").strip()
    summary = str(result_payload.get("summary") or "").strip()
    evidence = str(result_payload.get("evidence") or "").strip()
    final_comment = str(result_payload.get("final_comment") or "").strip()
    confidence = result_payload.get("confidence")

    has_consensus = (
        result_payload.get("consensus_revenue") is not None
        or result_payload.get("consensus_op_income") is not None
    )

    if len(outlook) < 12:
        reasons.append("industry_outlook_missing")
    if len(summary) < 8 and len(evidence) < 8:
        reasons.append("summary_or_evidence_insufficient")
    try:
        confidence_score = float(confidence) if confidence is not None else None
    except Exception:
        confidence_score = None
    if (confidence_score is None or confidence_score < 60) and not has_consensus:
        reasons.append("confidence_or_consensus_insufficient")
    if not final_comment:
        reasons.append("final_comment_missing")

    if reasons:
        return {"should_create": False, "reasons": reasons}
    return {"should_create": True, "reasons": ["stock_gate_passed"]}


def _build_consistency_alerts(
    *,
    packet: PacketModel,
    packet_type: Optional[str],
    stock_context: bool,
    run_stock_pipeline: bool,
    stock_pipeline_meta: dict,
) -> List[str]:
    alerts: List[str] = []
    stock_packet_type = CATEGORY_TO_PACKET_TYPE.get("PORTFOLIO")

    if not stock_context:
        return alerts

    if (packet.category or "").upper() != "PORTFOLIO":
        alerts.append("stock_context_category_mismatch")
    if stock_packet_type and packet_type != stock_packet_type:
        alerts.append("stock_context_packet_type_mismatch")
    if run_stock_pipeline and not stock_pipeline_meta.get("executed"):
        alerts.append("stock_pipeline_execution_failed")
    if stock_pipeline_meta.get("error"):
        alerts.append("stock_pipeline_error_present")

    return alerts


def _ensure_monitor_reconfirm_packet(db: Session, packet: PacketModel, alerts: List[str]) -> Optional[str]:
    if not alerts:
        return None

    monitor_topic = f"[Consistency Alert] {packet.packet_id}"
    exists = (
        db.query(PacketModel)
        .filter(
            PacketModel.source_ai == "consistency-monitor",
            PacketModel.topic == monitor_topic,
        )
        .first()
    )
    if exists:
        return exists.packet_id

    new_packet_id = str(uuid.uuid4())
    payload = {
        "monitor_for_packet_id": packet.packet_id,
        "source_ai": packet.source_ai,
        "alerts": alerts,
    }
    monitor_packet = PacketModel(
        packet_id=new_packet_id,
        source_ai="consistency-monitor",
        topic=monitor_topic,
        category="AI_RESEARCH",
        content_json=json.dumps(payload, ensure_ascii=False),
        request_action="validate",
        request_ask=f"Codex 재확인 필요: {packet.packet_id} ({', '.join(alerts)})",
        status="pending",
        related_idea_id=packet.related_idea_id,
    )
    db.add(monitor_packet)
    _record_history(
        db,
        new_packet_id,
        "created",
        action="validate",
        packet_type=_extract_packet_type(payload, monitor_packet.category),
        note=monitor_packet.request_ask,
    )
    return new_packet_id


@router.post("/packets", response_model=CollabPacket)
def create_packet(item: CollabPacketCreate, db: Session = Depends(get_db)):
    payload = _parse_content_json(item.content_json)
    packet_type = _extract_packet_type(payload, item.packet_type or item.category)
    if packet_type:
        payload["packet_type"] = packet_type

    data = item.model_dump(exclude={"packet_type"})
    data["content_json"] = json.dumps(payload, ensure_ascii=False)
    db_item = PacketModel(**data)
    db.add(db_item)
    _record_history(
        db,
        db_item.packet_id,
        "created",
        action=db_item.request_action,
        packet_type=packet_type,
        note=db_item.request_ask,
    )
    db.commit()
    db.refresh(db_item)
    return db_item


@router.get("/packets", response_model=List[CollabPacket])
def list_packets(
    status: Optional[str] = None,
    source_ai: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(PacketModel)
    if status:
        query = query.filter(PacketModel.status == status)
    if source_ai:
        query = query.filter(PacketModel.source_ai == source_ai)
    packets = query.order_by(PacketModel.created_at.desc()).limit(limit).all()
    for packet in packets:
        packet.topic = _clean_text(packet.topic, "Untitled packet")
        packet.request_ask = _clean_text(packet.request_ask, None) if packet.request_ask else None
    return packets


@router.get("/inbox", response_model=List[CollabInboxItem])
def list_inbox(
    status: Optional[str] = "pending",
    source_ai: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(PacketModel)
    if status:
        query = query.filter(PacketModel.status == status)
    if source_ai:
        query = query.filter(PacketModel.source_ai == source_ai)

    packets = query.order_by(PacketModel.created_at.desc()).limit(limit).all()
    now_utc = datetime.now(timezone.utc)
    items: List[CollabInboxItem] = []
    for packet in packets:
        payload = _parse_content_json(packet.content_json)
        triage = payload.get("_triage") if isinstance(payload.get("_triage"), dict) else {}
        due_at = _safe_parse_dt(triage.get("due_at"))
        overdue = bool(due_at and due_at < now_utc and packet.status in {"pending", "reviewed"})
        packet_type = _extract_packet_type(payload, packet.category)
        if triage.get("packet_type"):
            packet_type = _normalize_packet_type(triage.get("packet_type")) or packet_type
        work_date = triage.get("work_date") or (packet.created_at.date().isoformat() if packet.created_at else None)

        items.append(
            CollabInboxItem(
                packet_id=packet.packet_id,
                source_ai=packet.source_ai,
                topic=_clean_text(packet.topic, "Untitled packet"),
                category=packet.category,
                packet_type=packet_type,
                work_date=work_date,
                status=packet.status,
                request_action=packet.request_action,
                request_ask=_clean_text(packet.request_ask, "요청 질문 없음"),
                related_idea_id=packet.related_idea_id,
                created_at=packet.created_at,
                assignee_ai=triage.get("assignee_ai"),
                due_at=due_at,
                triage_action=triage.get("action"),
                triage_note=triage.get("note"),
                overdue=overdue,
            )
        )
    return items


@router.get("/packets/{packet_id}", response_model=CollabPacket)
def get_packet(packet_id: str, db: Session = Depends(get_db)):
    item = db.query(PacketModel).filter(PacketModel.packet_id == packet_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Packet not found")
    item.topic = _clean_text(item.topic, "Untitled packet")
    item.request_ask = _clean_text(item.request_ask, None) if item.request_ask else None
    return item


@router.put("/packets/{packet_id}/status", response_model=CollabPacket)
def update_packet_status(packet_id: str, update: CollabPacketStatusUpdate, db: Session = Depends(get_db)):
    item = db.query(PacketModel).filter(PacketModel.packet_id == packet_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Packet not found")
    item.status = update.status
    payload = _parse_content_json(item.content_json)
    _record_history(
        db,
        item.packet_id,
        "status_updated",
        action=update.status,
        packet_type=_extract_packet_type(payload, item.category),
    )
    db.commit()
    db.refresh(item)
    return item


@router.put("/packets/{packet_id}/triage", response_model=CollabPacketTriageResponse)
def triage_packet(packet_id: str, req: CollabPacketTriageRequest, db: Session = Depends(get_db)):
    packet = db.query(PacketModel).filter(PacketModel.packet_id == packet_id).first()
    if not packet:
        raise HTTPException(status_code=404, detail="Packet not found")

    action = req.action.value
    payload = _parse_content_json(packet.content_json)
    packet_type = _normalize_packet_type(req.packet_type) or _extract_packet_type(payload, packet.category)
    result_payload = {
        "summary": (req.result_summary or "").strip() or None,
        "evidence": (req.result_evidence or "").strip() or None,
        "risks": (req.result_risks or "").strip() or None,
        "next_step": (req.result_next_step or "").strip() or None,
        "confidence": req.result_confidence,
        "industry_outlook": (req.result_industry_outlook or "").strip() or None,
        "consensus_revenue": req.result_consensus_revenue,
        "consensus_op_income": req.result_consensus_op_income,
        "consensus_unit": (req.result_consensus_unit or "").strip() or None,
        "scenario_bear": (req.result_scenario_bear or "").strip() or None,
        "scenario_base": (req.result_scenario_base or "").strip() or None,
        "scenario_bull": (req.result_scenario_bull or "").strip() or None,
        "final_comment": (req.result_final_comment or "").strip() or None,
    }
    result_payload = {key: value for key, value in result_payload.items() if value is not None}

    stock_context = _is_stock_packet(packet_type, packet.category) or _looks_like_stock_context(packet, payload)

    stock_pipeline_meta = {
        "requested": bool(req.run_stock_pipeline),
        "executed": False,
        "ticker": None,
        "name": None,
        "error": None,
    }
    run_stock_pipeline = req.run_stock_pipeline or stock_context
    if run_stock_pipeline:
        stock_pipeline_meta["requested"] = True
        ticker, stock_name = _extract_stock_target(req, packet, payload)
        stock_pipeline_meta["ticker"] = ticker
        stock_pipeline_meta["name"] = stock_name
        if ticker and stock_name:
            try:
                stock_result = _run_stock_moat_analysis(ticker, stock_name, req.stock_year or "auto")
                result_payload = _merge_stock_analysis_result(result_payload, stock_result)
                stock_pipeline_meta["executed"] = bool(stock_result)
            except Exception as e:
                stock_pipeline_meta["error"] = str(e)
        else:
            stock_pipeline_meta["error"] = "stock_target_not_found"

    auto_final_comment = _build_final_comment(result_payload, action, packet_type)
    if auto_final_comment:
        result_payload["final_comment"] = auto_final_comment

    idea_gate = _evaluate_idea_gate(
        create_idea=req.create_idea,
        force_create_idea=req.force_create_idea,
        is_stock_context=stock_context,
        packet_type=packet_type,
        category=packet.category,
        result_payload=result_payload,
    )

    monitor_ctx = {
        "req_id": "REQ-007",
        "enforce_requirement_contract": True,
        "consistency_monitoring_enabled": True,
        "source_path": "backend.app.api.collab.triage_packet",
        "entity_type": "collab_packet",
        "entity_id": packet.packet_id,
        "requirement_refs": ["REQUESTS.md#REQ-007", "REQUESTS.md#REQ-008", "REQUESTS.md#REQ-009"],
        "plan_refs": ["docs/plans/2026-02-15-global-monitoring-guard-implementation.md"],
        "design_refs": [
            "docs/plans/2026-02-15-global-monitoring-guard-design.md",
            "docs/plans/2026-02-15-global-monitoring-guard-implementation.md",
        ],
        "test_tags": ["collab_triage", "monitoring_guard"],
        "category": packet.category,
        "packet_type": packet_type,
        "stock_context": stock_context,
        "run_stock_pipeline": run_stock_pipeline,
        "pipeline_executed": bool(stock_pipeline_meta.get("executed")),
        "pipeline_error": stock_pipeline_meta.get("error"),
        "create_idea": req.create_idea,
        "idea_gate_should_create": bool(idea_gate.get("should_create")),
        "force_create_idea": req.force_create_idea,
        "traceability_ok": True,
        "ticker": stock_pipeline_meta.get("ticker"),
        "stock_name": stock_pipeline_meta.get("name"),
    }
    guard_service = MonitoringGuardService(db)
    try:
        guard_service.enforce(monitor_ctx, hard_block=True)
    except MonitoringBlockedError as blocked:
        _record_history(
            db,
            packet.packet_id,
            "monitor_blocked",
            action=action,
            packet_type=packet_type,
            assignee_ai=(req.assignee_ai or "").strip() or None,
            note=json.dumps(
                {
                    "incident_id": blocked.incident_id,
                    "rule_code": blocked.rule_code,
                    "reasons": blocked.reasons,
                },
                ensure_ascii=False,
            ),
        )
        db.commit()
        raise HTTPException(
            status_code=409,
            detail={
                "blocked": True,
                "incident_id": blocked.incident_id,
                "rule_code": blocked.rule_code,
                "reasons": blocked.reasons,
                "reconfirm_required": True,
                "approver": "codex",
            },
        )

    triage_meta = {
        "action": action,
        "packet_type": packet_type,
        "assignee_ai": (req.assignee_ai or "").strip() or None,
        "due_at": req.due_at.isoformat() if req.due_at else None,
        "note": (req.note or "").strip() or None,
        "work_date": _today_utc(),
        "triaged_at": datetime.now(timezone.utc).isoformat(),
        "idea_gate": idea_gate,
        "stock_pipeline": stock_pipeline_meta,
    }
    if result_payload:
        triage_meta["result"] = result_payload

    payload["_triage"] = triage_meta
    if packet_type:
        payload["packet_type"] = packet_type
    packet.content_json = json.dumps(payload, ensure_ascii=False)
    packet.request_action = action
    packet.status = "synthesized" if action == "synthesize" else "reviewed"
    _record_history(
        db,
        packet.packet_id,
        "triaged",
        action=action,
        packet_type=packet_type,
        assignee_ai=triage_meta.get("assignee_ai"),
        due_at=req.due_at,
        note=triage_meta.get("note") or result_payload.get("summary"),
    )
    if run_stock_pipeline:
        _record_history(
            db,
            packet.packet_id,
            "stock_pipeline_attempted",
            action=action,
            packet_type=packet_type,
            assignee_ai=triage_meta.get("assignee_ai"),
            note=json.dumps(
                {
                    "source_ai": packet.source_ai,
                    "requested": bool(stock_pipeline_meta.get("requested")),
                    "executed": bool(stock_pipeline_meta.get("executed")),
                    "ticker": stock_pipeline_meta.get("ticker"),
                    "name": stock_pipeline_meta.get("name"),
                    "error": stock_pipeline_meta.get("error"),
                },
                ensure_ascii=False,
            ),
        )
    if req.create_idea and not idea_gate.get("should_create"):
        _record_history(
            db,
            packet.packet_id,
            "idea_gate_blocked",
            action=action,
            packet_type=packet_type,
            assignee_ai=triage_meta.get("assignee_ai"),
            note=", ".join(idea_gate.get("reasons", [])),
        )

    consistency_alerts = _build_consistency_alerts(
        packet=packet,
        packet_type=packet_type,
        stock_context=stock_context,
        run_stock_pipeline=run_stock_pipeline,
        stock_pipeline_meta=stock_pipeline_meta,
    )
    monitor_packet_id = None
    if consistency_alerts:
        alert_note = json.dumps(
            {
                "packet_id": packet.packet_id,
                "source_ai": packet.source_ai,
                "alerts": consistency_alerts,
                "reconfirm_with": "codex",
            },
            ensure_ascii=False,
        )
        _record_history(
            db,
            packet.packet_id,
            "consistency_alert",
            action=action,
            packet_type=packet_type,
            assignee_ai=triage_meta.get("assignee_ai"),
            note=alert_note,
        )
        monitor_packet_id = _ensure_monitor_reconfirm_packet(db, packet, consistency_alerts)
        triage_meta["consistency_alerts"] = consistency_alerts
        triage_meta["reconfirm_with"] = "codex"
        triage_meta["monitor_packet_id"] = monitor_packet_id
        payload["_triage"] = triage_meta
        packet.content_json = json.dumps(payload, ensure_ascii=False)

    idea = None
    if req.create_idea and idea_gate.get("should_create"):
        target_status = _resolve_idea_status(action, req.idea_status)
        if packet.related_idea_id:
            idea = db.query(IdeaModel).filter(IdeaModel.id == packet.related_idea_id).first()

        if idea is None:
            idea = IdeaModel(
                title=packet.topic,
                content=_build_idea_content(packet, payload, triage_meta.get("note")),
                source=f"COLLAB:{packet.source_ai}",
                category=packet.category,
                status=target_status,
                priority=req.idea_priority,
                tags=_merge_tags([], packet.category, action),
                author=triage_meta.get("assignee_ai") or packet.source_ai,
                action_item_id=packet.packet_id,
            )
            db.add(idea)
            db.flush()
            packet.related_idea_id = idea.id
        else:
            idea.title = packet.topic or idea.title
            idea.content = _build_idea_content(packet, payload, triage_meta.get("note"))
            idea.category = packet.category
            idea.status = target_status
            idea.priority = req.idea_priority
            idea.tags = _merge_tags(idea.tags, packet.category, action)
            if triage_meta.get("assignee_ai"):
                idea.author = triage_meta["assignee_ai"]
            if not idea.source:
                idea.source = f"COLLAB:{packet.source_ai}"
            if not idea.action_item_id:
                idea.action_item_id = packet.packet_id

    db.commit()
    db.refresh(packet)
    if idea:
        db.refresh(idea)

    summary = None
    if idea:
        summary = CollabIdeaSummary(
            id=idea.id,
            title=idea.title,
            status=idea.status,
            category=idea.category,
            priority=idea.priority,
        )

    gate_summary = CollabIdeaGate(
        should_create=bool(idea_gate.get("should_create")),
        reasons=[str(reason) for reason in idea_gate.get("reasons", [])],
    )
    return CollabPacketTriageResponse(packet=packet, idea=summary, idea_gate=gate_summary)


@router.get("/packets/{packet_id}/history", response_model=List[CollabPacketHistoryItem])
def list_packet_history(packet_id: str, db: Session = Depends(get_db)):
    packet = db.query(PacketModel).filter(PacketModel.packet_id == packet_id).first()
    if not packet:
        raise HTTPException(status_code=404, detail="Packet not found")

    rows = (
        db.query(HistoryModel)
        .filter(HistoryModel.packet_id == packet_id)
        .order_by(HistoryModel.created_at.desc(), HistoryModel.id.desc())
        .all()
    )
    payload = _parse_content_json(packet.content_json)
    fallback_packet_type = _extract_packet_type(payload, packet.category)
    items: List[CollabPacketHistoryItem] = []
    for row in rows:
        note = _clean_text(row.note, None) if row.note else None
        items.append(
            CollabPacketHistoryItem(
                id=row.id,
                packet_id=row.packet_id,
                event_type=row.event_type,
                action=row.action,
                packet_type=_normalize_packet_type(row.packet_type) or fallback_packet_type,
                assignee_ai=row.assignee_ai,
                due_at=row.due_at,
                note=note,
                work_date=row.work_date,
                created_at=row.created_at,
            )
        )
    return items


@router.post("/sessions", response_model=CollabSession)
def create_session(item: CollabSessionCreate, db: Session = Depends(get_db)):
    db_item = SessionModel(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.get("/sessions", response_model=List[CollabSession])
def list_sessions(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(SessionModel)
    if status:
        query = query.filter(SessionModel.status == status)
    return query.order_by(SessionModel.created_at.desc()).all()


@router.get("/state", response_model=CollabState)
def get_collab_state(db: Session = Depends(get_db)):
    active_ideas = db.query(IdeaModel).filter(IdeaModel.status.in_(["draft", "active", "testing"])).count()
    pending_packets = db.query(PacketModel).filter(PacketModel.status == "pending").count()
    active_sessions = db.query(SessionModel).filter(SessionModel.status == "active").count()
    return CollabState(
        active_ideas_count=active_ideas,
        pending_packets_count=pending_packets,
        active_sessions_count=active_sessions,
    )
