#!/usr/bin/env python3
"""Fail-fast integrity checks for dashboard/index.html.

Purpose:
- prevent accidental removal of core monitoring links
- prevent malformed JSX/HTML close tags (e.g. /span>)
- prevent comment/code merged lines that break Babel parsing
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_FILE = ROOT / "dashboard" / "index.html"


REQUIRED_LINKS = (
    "monitor_disclosures.html",
    "liquidity_stress.html",
    "crypto_trends.html",
    "moat_analysis.html",
    "idea_board.html",
)

CODE_TOKENS = (
    "const ",
    "let ",
    "var ",
    "function ",
    "setTimeout(",
    "ReactDOM.render(",
    "return ",
)

BROKEN_CLOSE_RE = re.compile(r"(?<!<)/(span|div|h[1-6]|label|button|a|strong|p)>")


def main() -> int:
    if not DASHBOARD_FILE.exists():
        print(f"[FAIL] Missing file: {DASHBOARD_FILE}")
        return 1

    text = DASHBOARD_FILE.read_text(encoding="utf-8", errors="strict")
    lines = text.splitlines()
    failures: list[str] = []

    if '<meta charset="UTF-8">' not in text:
        failures.append("Missing UTF-8 meta charset declaration.")

    if "시장 모니터링" not in text:
        failures.append("Missing '시장 모니터링' section title.")

    for link in REQUIRED_LINKS:
        if link not in text:
            failures.append(f"Missing required monitoring link: {link}")

    for idx, line in enumerate(lines, start=1):
        if BROKEN_CLOSE_RE.search(line):
            failures.append(f"Malformed close tag at line {idx}: {line.strip()}")

    for idx, line in enumerate(lines, start=1):
        if "//" not in line:
            continue
        comment_idx = line.find("//")
        comment_tail = line[comment_idx + 2 :]
        if any(token in comment_tail for token in CODE_TOKENS):
            failures.append(
                f"Comment/code merged line at {idx}; split into separate lines."
            )

    if failures:
        print("[FAIL] dashboard/index.html integrity check failed:")
        for msg in failures:
            print(f" - {msg}")
        return 1

    print("[PASS] dashboard/index.html integrity check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

