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


class TestSharedHelperIsDeduplicated(unittest.TestCase):
    """All MCP tool modules must route through the single shared helper.

    Guards against the regression where the streaming fix was applied to one
    copy while three duplicate definitions kept the old (Windows-deadlocking)
    implementation.
    """

    def test_tool_modules_use_shared_helper(self):
        # Phase 5d: scraping_tools and splitting_tools no longer shell out at
        # all (in-process run_cli_main); packaging_tools still uses the
        # subprocess helper for the LOCAL-agent enhancement paths.
        from skill_seekers.mcp.tools import (
            subprocess_utils,
            packaging_tools,
        )

        shared = subprocess_utils.run_subprocess_with_streaming
        self.assertIs(packaging_tools.run_subprocess_with_streaming, shared)

    def test_server_legacy_uses_shared_helper(self):
        from skill_seekers.mcp.tools import subprocess_utils
        from skill_seekers.mcp import server_legacy

        self.assertIs(
            server_legacy.run_subprocess_with_streaming,
            subprocess_utils.run_subprocess_with_streaming,
        )

    def test_no_duplicate_definitions_remain(self):
        """Only subprocess_utils should *define* the helper (others import it)."""
        import inspect
        from skill_seekers.mcp.tools import (
            subprocess_utils,
            packaging_tools,
        )

        for module in (packaging_tools,):
            fn = module.run_subprocess_with_streaming
            self.assertEqual(
                inspect.getmodule(fn).__name__,
                subprocess_utils.__name__,
                f"{module.__name__} should import the helper, not redefine it",
            )

    def test_migrated_modules_do_not_shell_out(self):
        """Phase 5d: scraping/splitting tools must not import the subprocess
        helper anymore — they dispatch in-process via _common.run_cli_tool
        (the shaping wrapper over _common.run_cli_main)."""
        from skill_seekers.mcp.tools import _common, scraping_tools, splitting_tools

        for module in (scraping_tools, splitting_tools):
            self.assertFalse(
                hasattr(module, "run_subprocess_with_streaming"),
                f"{module.__name__} should no longer use the subprocess helper",
            )
            self.assertIs(module.run_cli_tool, _common.run_cli_tool)


if __name__ == "__main__":
    unittest.main()
