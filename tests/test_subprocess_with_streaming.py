#!/usr/bin/env python3
"""
Tests for run_subprocess_streaming function in packaging_tools.py

Verifies the function does not hang due to pipe buffering issues and correctly captures stdout, stderr, and return code.
"""

import sys
import unittest

from skill_seekers.mcp.tools.packaging_tools import run_subprocess_with_streaming


class TestRunSubprocessStreaming(unittest.TestCase):
    """
    Unit test for cross-platform subprocess streaming function.
    """

    def test_does_not_hang_on_buffering(self):
        """Subprocesses should write >64KB of data."""
        # Generate more than allowed amount of data
        cmd = [sys.executable, "-c", 'for i in range(2000): print("x" * 100)']

        stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=10)

        self.assertEqual(returncode, 0, f"Timed out or failed: {stderr}")
        self.assertGreater(len(stdout), 100_000, "Expected more than 64KB of stdout")

    def test_timeout(self):
        """Subprocess should timeout if it runs too long."""
        cmd = [sys.executable, "-c", "import time; time.sleep(5)"]

        _stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=2)

        self.assertIn("timeout", stderr.lower())
        self.assertIsNotNone(returncode)

    def test_capture_stdout_stderr(self):
        """Subprocess should capture both stdout and stderr"""
        cmd = [
            sys.executable,
            "-c",
            'import sys; print("Hello stdout"); print("Hello stderr", file=sys.stderr)',
        ]

        stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=5)

        self.assertIn("Hello stdout", stdout)
        self.assertIn("Hello stderr", stderr)
        self.assertEqual(returncode, 0)

    def test_exit_code(self):
        """Subprocess should return correct exit code"""
        cmd = [sys.executable, "-c", "import sys; sys.exit(42)"]

        _stdout, _stderr, returncode = run_subprocess_with_streaming(cmd, timeout=5)

        self.assertEqual(returncode, 42)


if __name__ == "__main__":
    unittest.main()
