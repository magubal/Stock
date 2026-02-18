#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[2]
TARGET_PREFIXES = ("scripts/", "backend/app/api/")
EXCLUDED_PREFIXES = ("scripts/ci/",)
ENTRYPOINT_MARKERS = ('if __name__ == "__main__":', "APIRouter(", "FastAPI(", "@mcp.tool(")
MONITOR_TOKENS = ("enforce_monitoring(", "MonitoringGuardService(")
RUNTIME_GUARD_TOKEN = "register_fail_closed_guard("
ALLOW_NO_GUARD_MARKER = "consistency-monitoring: allow-no-guard"
RUNTIME_EXEMPT_MARKER = "consistency-monitoring: runtime-exempt"


def _run_git(args: List[str]) -> Tuple[int, str]:
    proc = subprocess.run(
        ["git"] + args,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    output = proc.stdout.strip()
    if proc.returncode != 0:
        detail = proc.stderr.strip()
        if detail:
            output = f"{output}\n{detail}".strip()
    return proc.returncode, output


def _resolve_base_ref(user_base: str = "") -> str:
    if user_base:
        return user_base
    gh_base = (os.environ.get("GITHUB_BASE_REF") or "").strip()
    if gh_base:
        return f"origin/{gh_base}"
    return "HEAD~1"


def _changed_files(base_ref: str) -> List[Tuple[str, str]]:
    code, out = _run_git(["diff", "--name-status", "--diff-filter=AMR", f"{base_ref}...HEAD"])
    if code != 0:
        code2, out2 = _run_git(["diff", "--name-status", "--diff-filter=AMR", "HEAD~1", "HEAD"])
        if code2 != 0:
            return []
        out = out2
    rows: List[Tuple[str, str]] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0].strip()
        if status.startswith("R") and len(parts) >= 3:
            rows.append(("R", parts[2].strip()))
            continue
        if len(parts) >= 2:
            rows.append((status[:1], parts[1].strip()))
    return rows


def _is_target_py(path: str) -> bool:
    if not path.endswith(".py"):
        return False
    normalized = path.replace("\\", "/")
    if normalized.startswith(EXCLUDED_PREFIXES):
        return False
    return normalized.startswith(TARGET_PREFIXES)


def _file_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="ignore")


def _has_entrypoint_marker(text: str) -> bool:
    return any(marker in text for marker in ENTRYPOINT_MARKERS)


def _modified_added_entrypoint(base_ref: str, path: str) -> bool:
    code, out = _run_git(["diff", "--unified=0", f"{base_ref}...HEAD", "--", path])
    if code != 0:
        code2, out2 = _run_git(["diff", "--unified=0", "HEAD~1", "HEAD", "--", path])
        if code2 != 0:
            return False
        out = out2

    for line in out.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        added = line[1:]
        if any(marker in added for marker in ENTRYPOINT_MARKERS):
            return True
    return False


def _check_path(path: str) -> List[str]:
    errors: List[str] = []
    text = _file_text(path)

    if ALLOW_NO_GUARD_MARKER in text:
        return errors
    if not _has_entrypoint_marker(text):
        return errors

    if not any(token in text for token in MONITOR_TOKENS):
        errors.append("missing_monitoring_call(enforce_monitoring|MonitoringGuardService)")

    if 'if __name__ == "__main__":' in text and RUNTIME_EXEMPT_MARKER not in text:
        if RUNTIME_GUARD_TOKEN not in text:
            errors.append("missing_runtime_fail_closed_guard(register_fail_closed_guard)")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Consistency monitoring entrypoint gate")
    parser.add_argument("--scope", choices=["changed", "all"], default="changed")
    parser.add_argument("--base-ref", default="")
    args = parser.parse_args()

    base_ref = _resolve_base_ref(args.base_ref)
    candidates: List[str] = []

    if args.scope == "all":
        code, out = _run_git(["ls-files"])
        if code != 0:
            print("[FAIL] git ls-files failed")
            return 2
        for row in out.splitlines():
            row = row.strip()
            if _is_target_py(row):
                candidates.append(row)
    else:
        for status, path in _changed_files(base_ref):
            if not _is_target_py(path):
                continue
            if status in {"A", "R"}:
                candidates.append(path)
                continue
            if status == "M" and _modified_added_entrypoint(base_ref, path):
                candidates.append(path)

    violations: Dict[str, List[str]] = {}
    for path in sorted(set(candidates)):
        try:
            errs = _check_path(path)
        except FileNotFoundError:
            continue
        if errs:
            violations[path] = errs

    if violations:
        print("[FAIL] consistency entrypoint gate")
        for path, errs in violations.items():
            for err in errs:
                print(f" - {path}: {err}")
        return 1

    print("[PASS] consistency entrypoint gate")
    print(f"checked={len(set(candidates))} base_ref={base_ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
