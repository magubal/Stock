#!/usr/bin/env python3
"""
kill_port.py - Windows port cleanup utility (safer v2)

Goals:
- Kill ONLY real, existing processes (PID validation before kill)
- Prefer graceful termination first, then force (/F) only if needed
- Detect "ghost listeners" (netstat shows PID but tasklist can't find it)
  and provide actionable diagnostics instead of blindly taskkill-ing
- Keep AhnLab V3 false-positive avoidance: no PowerShell pipelines

Usage:
    python scripts/kill_port.py                  # default: 8000
    python scripts/kill_port.py 8000 3000        # ports
    python scripts/kill_port.py all              # 8000,8080,3000
    python scripts/kill_port.py diagnose 8000    # diagnostics for a port
"""

from __future__ import annotations

import subprocess
import sys
import re
import time
from dataclasses import dataclass
from typing import List, Tuple, Dict


DEFAULT_PORTS = [8000]
ALL_DEV_PORTS = [8000, 8080, 3000]


@dataclass(frozen=True)
class Listener:
    proto: str
    local_addr: str
    local_port: int
    pid: int


def _safe_run(cmd: List[str], timeout: int = 10) -> Tuple[int, str, str]:
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return cp.returncode, cp.stdout or "", cp.stderr or ""
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return 999, "", str(e)


def parse_netstat_listeners(port: int) -> List[Listener]:
    """Parse netstat output to find TCP LISTENING lines for a given port."""
    rc, out, _ = _safe_run(["netstat", "-ano", "-p", "TCP"], timeout=12)
    if rc != 0 or not out:
        return []

    listeners: List[Listener] = []
    pattern = re.compile(
        rf"^\s*TCP\s+(\S+):{port}\s+\S+\s+LISTENING\s+(\d+)\s*$",
        re.MULTILINE
    )

    for m in pattern.finditer(out):
        local = m.group(1)
        pid = int(m.group(2))
        if pid > 0:
            listeners.append(Listener(proto="TCP", local_addr=local, local_port=port, pid=pid))

    return listeners


def pid_exists(pid: int) -> bool:
    """Check if PID exists using tasklist (no PS pipeline)."""
    rc, out, _ = _safe_run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], timeout=5)
    if rc != 0:
        return False
    text = (out or "").strip()
    if not text or text.lower().startswith("info:"):
        return False
    return text.startswith('"')


def get_process_name(pid: int) -> str:
    rc, out, _ = _safe_run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], timeout=5)
    line = (out or "").strip()
    if line.startswith('"'):
        parts = line.split('","')
        if parts:
            return parts[0].strip('"')
    return "unknown"


def try_kill_pid(pid: int, force: bool) -> Tuple[bool, str]:
    """Kill a PID tree. force=False: graceful, force=True: taskkill /F /T."""
    cmd = ["taskkill", "/PID", str(pid), "/T"]
    if force:
        cmd.insert(1, "/F")

    rc, out, err = _safe_run(cmd, timeout=12)
    ok = (rc == 0)
    msg = (out.strip() or err.strip() or f"returncode={rc}").strip()
    return ok, msg


def diagnose_http_and_portproxy(port: int) -> Dict[str, str]:
    """Lightweight diagnostics without PowerShell pipeline."""
    info: Dict[str, str] = {}

    # portproxy
    rc, out, err = _safe_run(["netsh", "interface", "portproxy", "show", "all"], timeout=10)
    text = (out or err or "").strip()
    if text:
        lines = [ln for ln in text.splitlines() if str(port) in ln]
        info["portproxy"] = "\n".join(lines).strip() if lines else "(no matches)"
    else:
        info["portproxy"] = "(no output)"

    # http servicestate filtered using cmd /c (PS-free)
    cmd = ["cmd", "/c", f'netsh http show servicestate | findstr /i ":{port} {port}"']
    rc, out, err = _safe_run(cmd, timeout=15)
    info["http_servicestate_matches"] = (out or err or "").strip() or "(no matches)"

    # http service state
    rc, out, err = _safe_run(["sc", "query", "http"], timeout=10)
    info["sc_query_http"] = (out or err or "").strip() or "(no output)"

    return info


def cleanup_port(port: int, diagnose: bool = False) -> Dict:
    listeners = parse_netstat_listeners(port)
    if not listeners:
        return {"port": port, "status": "free", "killed": [], "ghost": []}

    pids = sorted({l.pid for l in listeners if l.pid > 0})

    killed = []
    failed = []
    ghost = []

    for pid in pids:
        exists = pid_exists(pid)
        name = get_process_name(pid) if exists else "missing"
        if not exists:
            ghost.append({"pid": pid, "name": name})
            continue

        # Step 1: try non-force kill
        ok, msg = try_kill_pid(pid, force=False)
        if not ok:
            # Step 2: force kill
            ok, msg = try_kill_pid(pid, force=True)

        time.sleep(0.2)

        if ok:
            killed.append({"pid": pid, "name": name, "msg": msg})
        else:
            failed.append({"pid": pid, "name": name, "msg": msg})

    # Re-check
    remaining = parse_netstat_listeners(port)
    still_listening = bool(remaining)

    status = "cleaned"
    if still_listening and (failed or ghost):
        status = "stuck"
    elif failed:
        status = "partial"
    elif ghost and still_listening:
        status = "ghost"
    elif not killed and ghost:
        status = "ghost"

    result = {
        "port": port,
        "status": status,
        "killed": killed,
        "failed": failed,
        "ghost": ghost,
        "still_listening": still_listening,
        "remaining_pids": sorted({l.pid for l in remaining}) if remaining else [],
        "remaining_addrs": sorted({l.local_addr for l in remaining}) if remaining else [],
    }

    if diagnose or status in ("ghost", "stuck"):
        result["diagnostics"] = diagnose_http_and_portproxy(port)

    return result


def _print_result(res: Dict) -> None:
    port = res["port"]
    status = res["status"]

    if status == "free":
        print(f"  :{port} - free (nothing to kill)")
        return

    for p in res.get("killed", []):
        print(f"  :{port} - killed PID {p['pid']} ({p['name']})")
    for p in res.get("failed", []):
        print(f"  :{port} - FAILED PID {p['pid']} ({p['name']}) :: {p.get('msg','')}")
    for p in res.get("ghost", []):
        print(f"  :{port} - GHOST PID {p['pid']} (not in tasklist)")

    if res.get("still_listening"):
        addrs = ", ".join(res.get("remaining_addrs", []))
        pids = ", ".join(str(x) for x in res.get("remaining_pids", []))
        print(f"  :{port} - STILL LISTENING (addrs={addrs} pids={pids})")

    if status in ("ghost", "stuck"):
        print(f"  :{port} - NOTE: Listener appears to be kernel/service-level or stale mapping.")
        diag = res.get("diagnostics", {})
        if diag:
            print("  Diagnostics:")
            print("    [portproxy matches]")
            print("    " + (diag.get("portproxy", "(n/a)").replace("\n", "\n    ")))
            print("    [http servicestate matches]")
            print("    " + (diag.get("http_servicestate_matches", "(n/a)").replace("\n", "\n    ")))
            http_state = diag.get("sc_query_http", "")
            if http_state:
                print("    [sc query http]")
                print("    " + http_state.replace("\n", "\n    "))
        print("  If this persists:")
        print("    - Try: net stop http && net start http (admin)")
        print("    - If sc query http shows STOP_PENDING for long: reboot may be required.")
        print("    - As workaround: use a different dev port (e.g., 8001).")


def parse_ports(argv: List[str]) -> Tuple[bool, List[int]]:
    """Returns (diagnose_flag, ports)"""
    if not argv:
        return False, DEFAULT_PORTS

    if argv[0].lower() == "all":
        return False, ALL_DEV_PORTS

    diagnose = False
    args = argv[:]
    if args[0].lower() in ("diag", "diagnose"):
        diagnose = True
        args = args[1:]

    if not args:
        return diagnose, DEFAULT_PORTS

    ports: List[int] = []
    for a in args:
        try:
            ports.append(int(a))
        except ValueError:
            print(f"Usage: python {sys.argv[0]} [diagnose] [port1] [port2] ... | all")
            sys.exit(1)

    return diagnose, ports


def main() -> None:
    diagnose, ports = parse_ports(sys.argv[1:])
    print(f"[kill-port] Checking ports: {ports} (diagnose={diagnose})")

    any_action = False
    for port in ports:
        res = cleanup_port(port, diagnose=diagnose)
        if res["status"] != "free":
            any_action = True
        _print_result(res)

    if not any_action:
        print("[kill-port] All ports are free.")
    else:
        print("[kill-port] Done.")


if __name__ == "__main__":
    main()
