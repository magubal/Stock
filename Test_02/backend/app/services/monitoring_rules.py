import re
from typing import Dict, List

from .requirement_contract_service import evaluate_requirement_contract


_TICKER_RE = re.compile(r"^\d{6}$")


def evaluate_monitoring_rules(context: Dict) -> List[Dict]:
    violations: List[Dict] = []

    source_path = str(context.get("source_path") or "")
    entity_id = str(context.get("entity_id") or "")
    entity_type = str(context.get("entity_type") or "")
    stock_context = bool(context.get("stock_context"))
    category = str(context.get("category") or "")
    packet_type = str(context.get("packet_type") or "")
    run_stock_pipeline = bool(context.get("run_stock_pipeline"))
    pipeline_executed = bool(context.get("pipeline_executed"))
    pipeline_error = str(context.get("pipeline_error") or "")
    create_idea = bool(context.get("create_idea"))
    idea_gate_should_create = bool(context.get("idea_gate_should_create"))
    force_create_idea = bool(context.get("force_create_idea"))
    traceability_ok = bool(context.get("traceability_ok", True))
    ticker = str(context.get("ticker") or "")
    stock_name = str(context.get("stock_name") or "")
    enforce_requirement_contract = bool(context.get("enforce_requirement_contract", True))

    if not source_path or not entity_type or not entity_id:
        violations.append(
            {
                "rule_code": "schema_contract_break",
                "reasons": ["missing_required_context_fields"],
                "severity": "high",
            }
        )
        return violations

    if stock_context:
        if category.upper() != "PORTFOLIO" or packet_type not in {"종목", "PORTFOLIO"}:
            violations.append(
                {
                    "rule_code": "classification_consistency",
                    "reasons": ["stock_context_category_or_packet_type_mismatch"],
                    "severity": "high",
                }
            )

        if run_stock_pipeline and (not pipeline_executed):
            reasons = ["stock_pipeline_not_executed"]
            if pipeline_error:
                reasons.append(f"pipeline_error:{pipeline_error}")
            violations.append(
                {
                    "rule_code": "required_pipeline_execution",
                    "reasons": reasons,
                    "severity": "high",
                }
            )

        if create_idea and not idea_gate_should_create and not force_create_idea:
            violations.append(
                {
                    "rule_code": "gate_bypass_attempt",
                    "reasons": ["create_idea_requested_but_gate_denied"],
                    "severity": "high",
                }
            )

    if not traceability_ok:
        violations.append(
            {
                "rule_code": "traceability_missing",
                "reasons": ["required_traceability_data_missing"],
                "severity": "high",
            }
        )

    if enforce_requirement_contract:
        req_violation = evaluate_requirement_contract(context)
        if req_violation:
            violations.append(req_violation)

    if source_path.startswith("scripts.stock_moat"):
        if not _TICKER_RE.match(ticker) or not stock_name:
            violations.append(
                {
                    "rule_code": "schema_contract_break",
                    "reasons": ["stock_moat_requires_6digit_ticker_and_name"],
                    "severity": "high",
                }
            )

    return violations
