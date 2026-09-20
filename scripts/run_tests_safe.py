#!/usr/bin/env python3
"""Run pytest with a memory budget and clean up its entire process tree.

Usage: python scripts/run_tests_safe.py --max-rss-mb 4096 -- tests/ -q
Requires the development dependency psutil. Pass pytest-timeout's --timeout
option when installed to also limit individual test duration.
"""

import argparse
import contextlib
import os
import signal
import subprocess
import sys
import time

import psutil


def run_guarded(command, max_rss_mb=4096, min_available_mb=2048):
    """Monitor aggregate RSS and stop only this command's workers on exit."""
    process = subprocess.Popen(command, start_new_session=os.name != "nt")
    root = psutil.Process(process.pid)
    tracked = {root}
    peak = 0
    try:
        while process.poll() is None:
            # Remember descendants even if their immediate parent later exits.
            for parent in list(tracked):
                with contextlib.suppress(psutil.Error):
                    tracked.update(parent.children(recursive=True))
            rss = 0
            for child in list(tracked):
                try:
                    rss += child.memory_info().rss
                except psutil.Error:
                    tracked.discard(child)
            peak = max(peak, rss)
            available = psutil.virtual_memory().available
            if rss > max_rss_mb * 1024**2 or available < min_available_mb * 1024**2:
                print(
                    f"\nMemory guard stopped tests: tree RSS {rss / 1024**2:.0f} MiB, "
                    f"available {available / 1024**2:.0f} MiB.",
                    file=sys.stderr,
                    flush=True,
                )
                return 137
            time.sleep(0.2)
        return process.returncode
    except KeyboardInterrupt:
        # Forward Ctrl+C so pytest can stop cleanly and print its summary; the
        # finally block below still reaps anything that ignores the signal.
        if os.name != "nt":
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGINT)
        with contextlib.suppress(subprocess.TimeoutExpired):
            process.wait(timeout=10)
        return 130
    finally:
        if os.name != "nt":
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
        for child in tracked:
            with contextlib.suppress(psutil.Error):
                child.kill()
        process.wait()
        psutil.wait_procs(list(tracked), timeout=3)
        print(f"\nTest process tree peak RSS: {peak / 1024**2:.0f} MiB", flush=True)


def main():
    """Parse memory limits separately from pytest arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-rss-mb", type=int, default=4096)
    parser.add_argument("--min-available-mb", type=int, default=2048)
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.max_rss_mb <= 0 or args.min_available_mb < 0:
        parser.error("memory budget must be positive; available-memory floor cannot be negative")
    pytest_args = args.pytest_args
    if pytest_args[:1] == ["--"]:
        pytest_args = pytest_args[1:]
    return run_guarded(
        [sys.executable, "-m", "pytest", *(pytest_args or ["tests/", "-q"])],
        args.max_rss_mb,
        args.min_available_mb,
    )


if __name__ == "__main__":

    def terminate(signum, _frame):
        """Let finally clean up workers when CI sends SIGTERM."""
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, terminate)
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
