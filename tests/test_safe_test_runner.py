"""The full-suite watchdog caps memory and preserves test exit status."""

import sys

from scripts.run_tests_safe import run_guarded


def test_preserves_failure_status():
    assert run_guarded([sys.executable, "-c", "raise SystemExit(7)"], min_available_mb=0) == 7


def test_memory_budget_stops_worker():
    command = [sys.executable, "-c", "import time; payload = bytearray(64*1024**2); time.sleep(30)"]
    assert run_guarded(command, max_rss_mb=32, min_available_mb=0) == 137


def test_interrupt_is_forwarded_so_pytest_can_finish_its_summary(tmp_path):
    """Ctrl+C must reach the pytest process group as SIGINT, not only a final SIGKILL."""
    import os
    import signal
    import subprocess
    import time
    from pathlib import Path

    if os.name != "posix":
        return
    ready = tmp_path / "ready"
    marker = tmp_path / "interrupted"
    child = (
        "import signal, sys, time; from pathlib import Path; "
        f"signal.signal(signal.SIGINT, lambda *_: (Path({str(marker)!r}).write_text('yes'), sys.exit(130))); "
        f"Path({str(ready)!r}).write_text('1'); time.sleep(30)"
    )
    wrapper = (
        "import sys; from scripts.run_tests_safe import run_guarded; "
        f"sys.exit(run_guarded([sys.executable, '-c', {child!r}], min_available_mb=0))"
    )
    repo = Path(__file__).resolve().parents[1]
    proc = subprocess.Popen([sys.executable, "-c", wrapper], cwd=repo)
    try:
        deadline = time.monotonic() + 10
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert ready.exists(), "guarded child never started"
        proc.send_signal(signal.SIGINT)
        assert proc.wait(timeout=15) == 130
        assert marker.read_text() == "yes"
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
