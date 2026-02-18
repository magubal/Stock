#!/usr/bin/env python3
"""Global change guard for mandatory non-regression checklist.

This script is intended to be run in CI and locally.
It enforces project-wide minimum safety checks for *all* code changes.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

SOURCE_PREFIXES = (
    "backend/",
    "frontend/",
    "dashboard/",
    "scripts/",
    "config/",
    "tests/",
)

DOC_PREFIXES = (
    "docs/development_log_",
)

ALWAYS_IGNORE_PREFIXES = (
    ".git/",
    ".pytest_cache/",
)


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=check,
    )


def run_npm(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run npm with Windows-safe executable resolution."""
    npm_bin = shutil.which("npm") or shutil.which("npm.cmd") or shutil.which("npm.exe")
    if npm_bin:
        return run([npm_bin, *args], check=False)
    if os.name == "nt":
        return run(["cmd", "/c", "npm", *args], check=False)
    return run(["npm", *args], check=False)


def emit(text: str | None) -> None:
    if not text:
        return
    try:
        sys.stdout.write(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        sys.stdout.buffer.write(text.encode(encoding, errors="replace"))
    finally:
        sys.stdout.flush()


def emit_err(text: str | None) -> None:
    if not text:
        return
    try:
        sys.stderr.write(text)
    except UnicodeEncodeError:
        encoding = sys.stderr.encoding or "utf-8"
        sys.stderr.buffer.write(text.encode(encoding, errors="replace"))
    finally:
        sys.stderr.flush()


def normalize_path(path: str) -> str:
    p = path.replace("\\", "/").strip()
    if p.startswith("./"):
        p = p[2:]
    if p.startswith("Test_02/"):
        p = p[len("Test_02/") :]
    return p


def resolve_changed_files() -> list[str]:
    """Return changed file list for CI PR and local runs."""
    base_ref = os.getenv("GITHUB_BASE_REF", "").strip()
    if base_ref:
        cmd = [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=ACMR",
            "--relative",
            f"origin/{base_ref}...HEAD",
        ]
        cp = run(cmd, check=False)
        if cp.returncode == 0 and cp.stdout.strip():
            return [normalize_path(line) for line in cp.stdout.splitlines() if line.strip()]

    cp_local = run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", "--relative"],
        check=False,
    )
    local_files = [normalize_path(line) for line in cp_local.stdout.splitlines() if line.strip()]

    cp_untracked = run(
        ["git", "ls-files", "--others", "--exclude-standard", "--full-name"],
        check=False,
    )
    untracked = [normalize_path(line) for line in cp_untracked.stdout.splitlines() if line.strip()]

    return sorted(set(local_files + untracked))


def is_source_change(path: str) -> bool:
    if path.startswith(ALWAYS_IGNORE_PREFIXES):
        return False
    return path.startswith(SOURCE_PREFIXES)


def print_section(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> int:
    changed = resolve_changed_files()
    if not changed:
        print("[PASS] No changed files detected. Global guard skipped.")
        return 0

    print_section("Changed Files")
    for path in changed:
        print(f"- {path}")

    source_changed = [p for p in changed if is_source_change(p)]
    requests_updated = "REQUESTS.md" in changed
    devlog_updated = any(p.startswith(DOC_PREFIXES) for p in changed)

    if source_changed:
        print_section("Checklist: Required Tracking Docs")
        if not requests_updated:
            print("[FAIL] Source files changed but REQUESTS.md was not updated.")
            return 1
        print("[PASS] REQUESTS.md updated.")

        if not devlog_updated:
            print(
                "[FAIL] Source files changed but docs/development_log_YYYY-MM-DD.md was not updated."
            )
            return 1
        print("[PASS] Development log updated.")

    # Always run dashboard static integrity (fast and deterministic).
    print_section("Checklist: Dashboard Integrity")
    cp_dashboard = run([sys.executable, "scripts/ci/check_dashboard_static_integrity.py"], check=False)
    emit(cp_dashboard.stdout)
    if cp_dashboard.returncode != 0:
        emit_err(cp_dashboard.stderr)
        return cp_dashboard.returncode

    if "dashboard/index.html" in changed:
        print_section("Checklist: Dashboard Runtime Integrity")
        cp_dashboard_runtime = run(
            [sys.executable, "scripts/ci/check_dashboard_runtime_integrity.py"],
            check=False,
        )
        emit(cp_dashboard_runtime.stdout)
        if cp_dashboard_runtime.returncode != 0:
            emit_err(cp_dashboard_runtime.stderr)
            return cp_dashboard_runtime.returncode

        print_section("Checklist: Playwright Structured Suite")
        cp_npm_ci = run_npm(["ci", "--prefix", "tests/playwright"])
        emit(cp_npm_ci.stdout)
        if cp_npm_ci.returncode != 0:
            emit_err(cp_npm_ci.stderr)
            print("[FAIL] npm ci for Playwright suite failed.")
            return cp_npm_ci.returncode

        cp_playwright = run_npm(["run", "test:dashboard", "--prefix", "tests/playwright"])
        emit(cp_playwright.stdout)
        if cp_playwright.returncode != 0:
            emit_err(cp_playwright.stderr)
            print("[FAIL] Playwright structured suite failed.")
            return cp_playwright.returncode

    # Compile changed Python files to block syntax regressions.
    py_files = [p for p in changed if p.endswith(".py") and Path(p).exists()]
    if py_files:
        print_section("Checklist: Python Syntax Compile")
        cp_compile = run([sys.executable, "-m", "py_compile", *py_files], check=False)
        if cp_compile.returncode != 0:
            print(cp_compile.stderr, end="")
            print("[FAIL] Python compile check failed.")
            return cp_compile.returncode
        print(f"[PASS] Compiled {len(py_files)} Python file(s).")

    # Keep existing monitoring entrypoint guard in the unified checklist.
    print_section("Checklist: Monitoring Entrypoint Guard")
    cp_entrypoint = run(
        [sys.executable, "scripts/ci/check_entrypoint_monitoring.py", "--scope", "changed"],
        check=False,
    )
    emit(cp_entrypoint.stdout)
    if cp_entrypoint.returncode != 0:
        emit_err(cp_entrypoint.stderr)
        return cp_entrypoint.returncode

    print("\n[PASS] Global change guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
