#!/usr/bin/env python3
"""Daily moat sync runner with change detection.

Runs Excel -> DB/JSON sync only when source workbook content changed.
Designed to be triggered by Windows Task Scheduler at 19:00 daily.
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.consistency.fail_closed_runtime import register_fail_closed_guard, mark_monitoring_called
from scripts.idea_pipeline.monitoring_adapter import enforce_monitoring

from scripts.moat_dashboard.extract_moat_data import XLSX_PATH, extract

STATE_PATH = ROOT / "data" / "runtime" / "moat_sync_state.json"
LOG_PATH = ROOT / "data" / "runtime" / "logs" / "moat_sync_task.log"


def _monitoring_context(entity_id: str) -> Dict:
    return {
        "req_id": "REQ-007",
        "enforce_requirement_contract": True,
        "consistency_monitoring_enabled": True,
        "source_path": "scripts.moat_dashboard.scheduled_moat_sync",
        "entity_type": "scheduler_job",
        "entity_id": entity_id,
        "requirement_refs": [
            "REQUESTS.md#REQ-007",
            "REQUESTS.md#REQ-008",
            "REQUESTS.md#REQ-009",
            "REQUESTS.md#REQ-015",
        ],
        "plan_refs": ["docs/plans/2026-02-15-global-monitoring-guard-implementation.md"],
        "design_refs": [
            "docs/plans/2026-02-15-global-monitoring-guard-design.md",
            "docs/plans/2026-02-15-global-monitoring-guard-implementation.md",
        ],
        "test_tags": ["monitoring_guard", "scheduler"],
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


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        while True:
            chunk = file.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def _fingerprint(path: Path) -> Dict:
    stat = path.stat()
    return {
        "sha256": _sha256(path),
        "size": stat.st_size,
        "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
    }


def _load_state(path: Path) -> Dict:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def _save_state(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def _append_log(message: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(message.rstrip() + "\n")


def run(force: bool = False, scheduled: bool = False) -> int:
    workbook_path = Path(XLSX_PATH)
    now = datetime.now().isoformat()
    entity_id = f"moat-sync:{now}"

    guard = enforce_monitoring(_monitoring_context(entity_id), hard_block=True)
    if guard.blocked:
        _append_log(
            f"[{now}] BLOCKED incident_id={guard.incident_id} rule={guard.rule_code} reasons={guard.reasons}"
        )
        print(
            f"[BLOCKED] incident_id={guard.incident_id} rule={guard.rule_code} reasons={guard.reasons}"
        )
        return 3

    if not workbook_path.exists():
        mark_monitoring_called()
        print(f"[ERROR] workbook not found: {workbook_path}")
        _append_log(f"[{now}] ERROR workbook_not_found path={workbook_path}")
        return 2

    current = _fingerprint(workbook_path)
    state = _load_state(STATE_PATH)
    previous = state.get("last_source", {})

    changed = (
        previous.get("sha256") != current.get("sha256")
        or previous.get("size") != current.get("size")
        or previous.get("mtime") != current.get("mtime")
    )

    if not force and not changed:
        state["last_checked_at"] = now
        state["last_result"] = "skipped_no_change"
        _save_state(STATE_PATH, state)
        msg = f"[{now}] SKIP no_change sha256={current['sha256'][:12]}"
        print(msg)
        _append_log(msg)
        return 0

    result = extract()
    synced_at = datetime.now().isoformat()
    state.update(
        {
            "last_checked_at": synced_at,
            "last_synced_at": synced_at,
            "last_result": "synced",
            "last_source": current,
            "last_sync": result.get("sync", {}),
            "mode": "scheduled" if scheduled else "manual",
        }
    )
    _save_state(STATE_PATH, state)

    sync_info = result.get("sync", {})
    msg = (
        f"[{synced_at}] SYNC run_id={sync_info.get('run_id')} "
        f"inserted={sync_info.get('inserted')} updated={sync_info.get('updated')} "
        f"unchanged={sync_info.get('unchanged')} deactivated={sync_info.get('deactivated')}"
    )
    print(msg)
    _append_log(msg)
    return 0


def main() -> int:
    # consistency-monitoring: runtime-exempt
    register_fail_closed_guard("scripts.moat_dashboard.scheduled_moat_sync")
    parser = argparse.ArgumentParser(description="Daily moat sync with change detection")
    parser.add_argument("--force", action="store_true", help="run sync even when source fingerprint unchanged")
    parser.add_argument("--scheduled", action="store_true", help="set when called by scheduler")
    args = parser.parse_args()
    return run(force=args.force, scheduled=args.scheduled)


if __name__ == "__main__":
    raise SystemExit(main())
