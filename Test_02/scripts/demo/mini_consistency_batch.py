#!/usr/bin/env python3
"""Mini consistency-monitoring demo batch.

Reads a small CSV and validates each row against consistency-monitoring
contract context. Blocked rows are isolated and remaining rows continue.
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.consistency.fail_closed_runtime import register_fail_closed_guard, mark_monitoring_called
from scripts.idea_pipeline.monitoring_adapter import enforce_monitoring


DEFAULT_INPUT = ROOT / "data" / "demo" / "mini_input.csv"
DEFAULT_OUTPUT = ROOT / "data" / "demo" / "mini_output.csv"
REQUIRED_COLUMNS = ["row_id", "name", "text", "scenario"]


def _base_context(entity_id: str) -> Dict:
    return {
        "req_id": "REQ-007",
        "enforce_requirement_contract": True,
        "consistency_monitoring_enabled": True,
        "source_path": "scripts.demo.mini_consistency_batch",
        "entity_type": "demo_record",
        "entity_id": entity_id,
        "requirement_refs": ["REQUESTS.md#REQ-007", "REQUESTS.md#REQ-008", "REQUESTS.md#REQ-009", "REQUESTS.md#REQ-010"],
        "plan_refs": ["docs/plans/2026-02-15-global-monitoring-guard-implementation.md"],
        "design_refs": [
            "docs/plans/2026-02-15-global-monitoring-guard-design.md",
            "docs/plans/2026-02-15-global-monitoring-guard-implementation.md",
        ],
        "test_tags": ["monitoring_guard", "mini_demo"],
        "traceability_ok": True,
        "stock_context": False,
        "run_stock_pipeline": False,
        "pipeline_executed": False,
        "pipeline_error": "",
        "create_idea": False,
        "idea_gate_should_create": False,
        "force_create_idea": False,
        "category": "CROSS",
        "packet_type": "이슈전망",
        "ticker": "",
        "stock_name": "",
    }


def _apply_scenario(context: Dict, scenario: str) -> Dict:
    payload = dict(context)
    key = str(scenario or "").strip().lower()

    if key == "missing_requirement_refs":
        payload["requirement_refs"] = ["REQUESTS.md#REQ-999"]
    elif key == "missing_plan_refs":
        payload["plan_refs"] = []
    elif key == "missing_req_id":
        payload["req_id"] = ""
    elif key == "consistency_off":
        payload["consistency_monitoring_enabled"] = False
    return payload


def _score_text(text: str) -> int:
    return len((text or "").strip())


def run_batch(input_path: Path, output_path: Path) -> Dict:
    rows: List[Dict] = []
    with input_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        columns = list(reader.fieldnames or [])
        missing = [col for col in REQUIRED_COLUMNS if col not in columns]
        if missing:
            mark_monitoring_called()
            raise ValueError(f"missing_required_columns:{','.join(missing)}")
        rows = list(reader)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "row_id",
        "name",
        "scenario",
        "status",
        "score",
        "incident_id",
        "rule_code",
        "reasons",
    ]

    success = 0
    blocked = 0
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        if not rows:
            mark_monitoring_called()
            return {"total": 0, "success": 0, "blocked": 0, "output": str(output_path)}

        for row in rows:
            row_id = str(row.get("row_id") or "").strip()
            name = str(row.get("name") or "").strip()
            text = str(row.get("text") or "")
            scenario = str(row.get("scenario") or "ok").strip()
            entity_id = f"mini:{row_id or 'unknown'}"

            context = _base_context(entity_id)
            context = _apply_scenario(context, scenario)
            result = enforce_monitoring(context, hard_block=True)

            if result.blocked:
                blocked += 1
                writer.writerow(
                    {
                        "row_id": row_id,
                        "name": name,
                        "scenario": scenario,
                        "status": "BLOCKED",
                        "score": 0,
                        "incident_id": result.incident_id,
                        "rule_code": result.rule_code,
                        "reasons": "|".join(result.reasons or []),
                    }
                )
                continue

            success += 1
            writer.writerow(
                {
                    "row_id": row_id,
                    "name": name,
                    "scenario": scenario,
                    "status": "OK",
                    "score": _score_text(text),
                    "incident_id": "",
                    "rule_code": "",
                    "reasons": "",
                }
            )

    return {"total": len(rows), "success": success, "blocked": blocked, "output": str(output_path)}


def main() -> int:
    register_fail_closed_guard("scripts.demo.mini_consistency_batch")
    parser = argparse.ArgumentParser(description="Mini consistency-monitoring demo batch")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="input csv path")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="output csv path")
    args = parser.parse_args()

    if not args.input.exists():
        mark_monitoring_called()
        print(f"[ERROR] input file not found: {args.input}")
        return 2

    summary = run_batch(args.input, args.output)
    print(
        "[DONE] total={total} success={success} blocked={blocked} output={output}".format(
            **summary
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
