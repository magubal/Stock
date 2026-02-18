import json
import os
from pathlib import Path
from typing import Dict, List, Optional


ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_CONTRACT_PATH = ROOT_DIR / "config" / "requirement_contracts.json"


def _to_list(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return []
        return [v]
    return [str(value)]


def _contract_path() -> Path:
    raw = os.environ.get("REQUIREMENT_CONTRACTS_PATH", "").strip()
    return Path(raw) if raw else DEFAULT_CONTRACT_PATH


def _load_contract_doc() -> Dict:
    path = _contract_path()
    if not path.exists():
        raise FileNotFoundError(f"requirement_contract_file_missing:{path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_requirement_contract(req_id: str) -> Optional[Dict]:
    req_key = str(req_id or "").strip()
    if not req_key:
        return None
    doc = _load_contract_doc()
    for contract in doc.get("contracts", []):
        if str(contract.get("req_id", "")).strip() == req_key:
            return contract
    return None


def evaluate_requirement_contract(context: Dict) -> Optional[Dict]:
    req_id = str(context.get("req_id") or "").strip()
    if not req_id:
        return {
            "rule_code": "requirement_contract_missing",
            "reasons": ["req_id_missing"],
            "severity": "high",
        }

    try:
        contract = get_requirement_contract(req_id)
    except Exception as e:
        return {
            "rule_code": "requirement_contract_missing",
            "reasons": [f"contract_load_failed:{e}"],
            "severity": "high",
        }

    if not contract:
        return {
            "rule_code": "requirement_contract_missing",
            "reasons": [f"req_contract_not_found:{req_id}"],
            "severity": "high",
        }

    reasons: List[str] = []
    source_path = str(context.get("source_path") or "")

    for field in _to_list(contract.get("required_context_fields")):
        value = context.get(field)
        if value is None:
            reasons.append(f"context_field_missing:{field}")
            continue
        if isinstance(value, str) and not value.strip():
            reasons.append(f"context_field_empty:{field}")
            continue
        if isinstance(value, (list, dict)) and not value:
            reasons.append(f"context_field_empty:{field}")

    for field in _to_list(contract.get("required_truthy_fields")):
        if not bool(context.get(field)):
            reasons.append(f"context_field_not_truthy:{field}")

    allowed_prefixes = _to_list(contract.get("allowed_source_prefixes"))
    if allowed_prefixes and not any(source_path.startswith(prefix) for prefix in allowed_prefixes):
        reasons.append(f"source_path_not_allowed:{source_path}")

    provided_design_refs = set(_to_list(context.get("design_refs")))
    for ref in _to_list(contract.get("required_design_refs")):
        if ref not in provided_design_refs:
            reasons.append(f"design_ref_missing:{ref}")

    provided_requirement_refs = set(_to_list(context.get("requirement_refs")))
    for ref in _to_list(contract.get("required_requirement_refs")):
        if ref not in provided_requirement_refs:
            reasons.append(f"requirement_ref_missing:{ref}")

    provided_plan_refs = set(_to_list(context.get("plan_refs")))
    for ref in _to_list(contract.get("required_plan_refs")):
        if ref not in provided_plan_refs:
            reasons.append(f"plan_ref_missing:{ref}")

    provided_test_tags = set(_to_list(context.get("test_tags")))
    for tag in _to_list(contract.get("required_test_tags")):
        if tag not in provided_test_tags:
            reasons.append(f"test_tag_missing:{tag}")

    if reasons:
        return {
            "rule_code": "requirement_contract_mismatch",
            "reasons": reasons,
            "severity": "high",
        }
    return None
