import atexit
import os
import sys
import threading


_LOCK = threading.Lock()
_STATE = {
    "registered": False,
    "called": False,
    "entrypoint": "",
}


def register_fail_closed_guard(entrypoint: str) -> None:
    """Register runtime fail-closed guard for script entrypoints.

    If the process exits without a monitoring call mark, force non-zero exit.
    Disable only with CONSISTENCY_RUNTIME_GUARD=0.
    """
    if str(os.environ.get("CONSISTENCY_RUNTIME_GUARD", "1")).strip() in {"0", "false", "False"}:
        return
    with _LOCK:
        if _STATE["registered"]:
            return
        _STATE["registered"] = True
        _STATE["entrypoint"] = entrypoint or "unknown"
    atexit.register(_verify_guard_called)


def mark_monitoring_called() -> None:
    with _LOCK:
        _STATE["called"] = True


def _verify_guard_called() -> None:
    with _LOCK:
        registered = _STATE["registered"]
        called = _STATE["called"]
        entrypoint = _STATE["entrypoint"]
    if not registered or called:
        return

    message = (
        "[CONSISTENCY MONITORING][FAIL-CLOSED] "
        f"monitoring call missing before process exit: {entrypoint}"
    )
    try:
        sys.stderr.write(message + "\n")
        sys.stderr.flush()
    except Exception:
        pass
    os._exit(97)
