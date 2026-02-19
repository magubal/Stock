#!/usr/bin/env python3
"""
kill_port.py - Windows port cleanup utility
Finds and kills processes listening on specified ports using tree kill.
Safe to run when nothing is listening (no error spam).

Usage:
    python scripts/kill_port.py              # Kill default port (8000 only)
    python scripts/kill_port.py 8000         # Kill single port
    python scripts/kill_port.py 8000 3000    # Kill multiple ports
    python scripts/kill_port.py all          # Kill all dev ports (8000, 8080, 3000)

Why Python instead of PowerShell:
    - AhnLab V3 flags PowerShell pipe commands (Get-Process | Stop-Process)
      as MDP.Powershell.M2514 false positive
    - Python subprocess calls to taskkill are not flagged
"""

import subprocess
import sys
import re


def find_pids_on_port(port: int) -> list[int]:
    """Find PIDs listening on a given port using netstat."""
    try:
        result = subprocess.run(
            ["netstat", "-ano", "-p", "TCP"],
            capture_output=True, text=True, timeout=10
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    pids = set()
    pattern = re.compile(
        rf"^\s*TCP\s+\S+:{port}\s+\S+\s+LISTENING\s+(\d+)",
        re.MULTILINE
    )
    for match in pattern.finditer(result.stdout):
        pid = int(match.group(1))
        if pid > 0:
            pids.add(pid)
    return sorted(pids)


def get_process_name(pid: int) -> str:
    """Get process name for a PID using tasklist."""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=5
        )
        line = result.stdout.strip()
        if line and line.startswith('"'):
            return line.split('"')[1]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return "unknown"


def kill_pid_tree(pid: int) -> bool:
    """Kill a process and all its children using taskkill /F /T."""
    try:
        result = subprocess.run(
            ["taskkill", "/PID", str(pid), "/F", "/T"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def kill_port(port: int) -> dict:
    """Find and kill all processes on a port. Returns summary."""
    pids = find_pids_on_port(port)
    if not pids:
        return {"port": port, "status": "free", "killed": []}

    killed = []
    failed = []
    for pid in pids:
        name = get_process_name(pid)
        if kill_pid_tree(pid):
            killed.append({"pid": pid, "name": name})
        else:
            failed.append({"pid": pid, "name": name})

    status = "cleaned" if not failed else "partial"
    return {"port": port, "status": status, "killed": killed, "failed": failed}


def main():
    # Default: only backend (8000) — the main zombie source (uvicorn --reload)
    # Use "all" to kill all dev ports including dashboard(8080) and frontend(3000)
    DEFAULT_PORTS = [8000]
    ALL_DEV_PORTS = [8000, 8080, 3000]

    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "all":
            ports = ALL_DEV_PORTS
        else:
            try:
                ports = [int(p) for p in sys.argv[1:]]
            except ValueError:
                print(f"Usage: python {sys.argv[0]} [port1] [port2] ... | all")
                sys.exit(1)
    else:
        ports = DEFAULT_PORTS

    print(f"[kill-port] Checking ports: {ports}")
    any_killed = False

    for port in ports:
        result = kill_port(port)
        if result["status"] == "free":
            print(f"  :{port} - free (nothing to kill)")
        elif result["status"] == "cleaned":
            any_killed = True
            for p in result["killed"]:
                print(f"  :{port} - killed PID {p['pid']} ({p['name']})")
        else:
            any_killed = True
            for p in result.get("killed", []):
                print(f"  :{port} - killed PID {p['pid']} ({p['name']})")
            for p in result.get("failed", []):
                print(f"  :{port} - FAILED to kill PID {p['pid']} ({p['name']})")

    if not any_killed:
        print("[kill-port] All ports are free.")
    else:
        print("[kill-port] Cleanup complete.")


if __name__ == "__main__":
    main()
