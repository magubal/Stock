#!/usr/bin/env python3
"""Runtime integrity check for dashboard/index.html using Playwright."""

from __future__ import annotations

import contextlib
import socket
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_DIR = ROOT / "dashboard"

REQUIRED_TEXTS = (
    "Stock Research ONE",
    "시장 모니터링",
    "프로젝트 현황",
    "오늘의 공시",
    "해자 분석 대시보드",
)

REQUIRED_LINKS = (
    "monitor_disclosures.html",
    "liquidity_stress.html",
    "crypto_trends.html",
    "moat_analysis.html",
    "idea_board.html",
)

IGNORED_CONSOLE_ERROR_PATTERNS = (
    "ReactDOM.render is no longer supported",
    "Access to fetch at 'http://localhost:8000/",
    "Failed to load resource: net::ERR_FAILED",
    "API Error: TypeError: Failed to fetch",
)


def wait_port(host: str, port: int, timeout_sec: float = 10.0) -> bool:
    end = time.time() + timeout_sec
    while time.time() < end:
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.1)
    return False


def pick_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        print(
            "[FAIL] playwright is not installed. Install with: pip install playwright && python -m playwright install chromium"
        )
        return 1

    port = pick_port()
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=DASHBOARD_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        if not wait_port("127.0.0.1", port, timeout_sec=10):
            err = server.stderr.read() if server.stderr else ""
            print("[FAIL] Failed to start dashboard test server.")
            if err:
                print(err)
            return 1

        url = f"http://127.0.0.1:{port}/index.html"
        errors: list[str] = []
        console_errors: list[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on(
                "console",
                lambda msg: console_errors.append(msg.text)
                if msg.type == "error"
                else None,
            )
            resp = page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(700)

            if not resp or resp.status != 200:
                print(f"[FAIL] Dashboard load failed. status={resp.status if resp else None}")
                browser.close()
                return 1

            root_text = page.locator("#root").inner_text()
            failures: list[str] = []

            if errors:
                failures.append(f"pageerror_count={len(errors)}")

            # Ignore known React18 deprecation warning for render API.
            relevant_console = [
                e
                for e in console_errors
                if not any(pattern in e for pattern in IGNORED_CONSOLE_ERROR_PATTERNS)
            ]
            if relevant_console:
                failures.append(f"console_error_count={len(relevant_console)}")

            for text in REQUIRED_TEXTS:
                if text not in root_text:
                    failures.append(f"missing_text={text}")

            html = page.content()
            for link in REQUIRED_LINKS:
                if link not in html:
                    failures.append(f"missing_link={link}")

            card_count = page.locator(".dashboard-card").count()
            if card_count < 8:
                failures.append(f"dashboard_card_count_too_low={card_count}")

            browser.close()

            if failures:
                print("[FAIL] Dashboard runtime integrity check failed:")
                for item in failures:
                    print(f" - {item}")
                return 1

        print("[PASS] Dashboard runtime integrity check passed.")
        return 0
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except Exception:
            server.kill()


if __name__ == "__main__":
    raise SystemExit(main())
