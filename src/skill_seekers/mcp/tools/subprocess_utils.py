"""
Shared subprocess helper for MCP tools.

Runs a subprocess while concurrently draining stdout/stderr on reader threads,
so a child that produces a lot of output never deadlocks on a full OS pipe
buffer. This replaces the old ``select``-based polling loop, which did not work
on Windows (``select`` does not support pipes there) and would freeze on large
outputs such as documentation scraping.

All MCP tool modules import ``run_subprocess_with_streaming`` from here so the
implementation lives in exactly one place.
"""

import subprocess
import threading

# Grace period (seconds) for the reader threads to drain buffered output once
# the process has exited or been killed. Normally they hit EOF immediately when
# the write ends close; the bound prevents a grandchild that inherited the pipe
# from hanging the caller forever (so ``timeout`` always bounds wall-clock).
_DRAIN_GRACE_SECONDS = 10


def run_subprocess_with_streaming(cmd: list[str], timeout: int = None) -> tuple[str, str, int]:
    """
    Run a subprocess, streaming stdout/stderr via concurrent reader threads.

    The reader threads keep the OS pipe buffers drained, so the child never
    blocks writing to a full pipe (the deadlock the old ``select`` loop hit on
    Windows). On timeout the process is killed and a marker is appended to
    stderr.

    Args:
        cmd: Command to run as a list of strings.
        timeout: Maximum seconds to wait (None for no timeout).

    Returns:
        Tuple of (stdout, stderr, returncode).
    """
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        stdout_lines: list[str] = []
        stderr_lines: list[str] = []

        def _read(stream, target: list[str]) -> None:
            for line in stream:
                target.append(line)

        t_out = threading.Thread(target=_read, args=(process.stdout, stdout_lines), daemon=True)
        t_err = threading.Thread(target=_read, args=(process.stderr, stderr_lines), daemon=True)
        t_out.start()
        t_err.start()

        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()  # Ensure the process has terminated
            stderr_lines.append(f"\nTimeout: process killed after exceeding {timeout} seconds.")

        # Bounded join: the threads normally finish as soon as the write ends
        # close; the grace stops an inherited-pipe grandchild from hanging us.
        t_out.join(_DRAIN_GRACE_SECONDS)
        t_err.join(_DRAIN_GRACE_SECONDS)

        return "".join(stdout_lines), "".join(stderr_lines), process.returncode or 0

    except Exception as e:
        return "", f"Error running subprocess: {str(e)}", 1
