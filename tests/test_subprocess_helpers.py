"""Regression tests for bootstrap process cleanup, without repository analysis."""

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests.subprocess_helpers import run_process_tree


@pytest.mark.skipif(os.name != "posix", reason="POSIX process group cleanup")
@pytest.mark.parametrize("interrupted", [False, True])
def test_descendants_are_stopped(tmp_path, monkeypatch, interrupted):
    marker = tmp_path / "child.pid"
    child_script = "import time; time.sleep(30)"
    parent_script = (
        "import subprocess,sys,time; from pathlib import Path; "
        f"child=subprocess.Popen([sys.executable,'-c',{child_script!r}]); "
        f"Path({str(marker)!r}).write_text(str(child.pid)); time.sleep(30)"
    )
    if interrupted:

        def interrupt(_self, **_kwargs):
            deadline = time.monotonic() + 3
            while not marker.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            raise KeyboardInterrupt

        monkeypatch.setattr(subprocess.Popen, "communicate", interrupt)
    expected = KeyboardInterrupt if interrupted else subprocess.TimeoutExpired
    with pytest.raises(expected):
        run_process_tree([sys.executable, "-c", parent_script], timeout=0.5)
    assert marker.exists(), "fixture child did not start"
    pid = int(marker.read_text())
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        # Linux may retain a reparented zombie briefly; it uses no memory/CPU.
        stat = Path(f"/proc/{pid}/stat")
        if stat.exists() and stat.read_text().split()[2] == "Z":
            return
        time.sleep(0.02)
    pytest.fail(f"child {pid} survived test cleanup")


def test_real_agent_process_is_rejected():
    """The suite must fail safely even on machines with agent CLIs installed."""
    with pytest.raises(pytest.fail.Exception, match="attempted to launch real agent"):
        subprocess.run(["claude", "-p", "never execute this"], check=False)
