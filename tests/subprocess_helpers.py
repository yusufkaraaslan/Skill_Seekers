"""Test subprocesses that clean up descendants even when pytest interrupts them."""

import contextlib
import os
import signal
import subprocess


def run_process_tree(argv, *, cwd=None, env=None, timeout=600):
    """Capture a command and always reap its process tree on timeout/interruption.

    Bootstrap invokes bash -> uv -> Python. Killing only bash leaves the
    expensive Python analysis alive after pytest-timeout fails the test.
    """
    proc = subprocess.Popen(
        argv,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=os.name != "nt",
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        return subprocess.CompletedProcess(argv, proc.returncode, stdout, stderr)
    finally:
        if os.name == "nt":
            if proc.poll() is None:
                subprocess.run(
                    ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                    capture_output=True,
                    check=False,
                )
        else:
            # Test-only workers have no cleanup contract. Kill the whole group,
            # including grandchildren that keep captured pipes open.
            with contextlib.suppress(ProcessLookupError):
                os.killpg(proc.pid, signal.SIGKILL)
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=5)
        proc.stdout.close()
        proc.stderr.close()
