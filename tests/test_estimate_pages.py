#!/usr/bin/env python3
"""
Tests for cli/estimate_pages.py functionality
"""

import pytest

import json
import unittest
from pathlib import Path

from skill_seekers.cli.estimate_pages import estimate_pages

pytestmark = pytest.mark.integration


@pytest.fixture
def local_docs_site():
    """Serve a finite documentation site without relying on public websites."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread

    class Handler(BaseHTTPRequestHandler):
        def do_HEAD(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()

        def do_GET(self):
            self.do_HEAD()
            self.wfile.write(b'<html><a href="/one">One</a><a href="/two">Two</a></html>')

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


class TestEstimatePages(unittest.TestCase):
    """Test estimate_pages function"""

    @pytest.fixture(autouse=True)
    def _local_site(self, local_docs_site):
        self.base_url = local_docs_site

    def test_estimate_pages_with_minimal_config(self):
        """Test estimation with minimal configuration"""
        config = {"name": "test", "base_url": self.base_url, "rate_limit": 0.1}

        # Exercise real HEAD and GET requests against the local fixture
        # We use low max_discovery to keep test fast
        result = estimate_pages(config, max_discovery=2, timeout=5)

        # Check result structure
        self.assertIsInstance(result, dict)
        self.assertIn("discovered", result)
        self.assertIn("estimated_total", result)
        # Actual key is elapsed_seconds, not time_elapsed
        self.assertIn("elapsed_seconds", result)

    def test_estimate_pages_returns_discovered_count(self):
        """Test that result contains discovered page count"""
        config = {"name": "test", "base_url": self.base_url, "rate_limit": 0.1}

        result = estimate_pages(config, max_discovery=1, timeout=5)

        self.assertGreaterEqual(result["discovered"], 0)
        self.assertIsInstance(result["discovered"], int)

    def test_estimate_pages_respects_max_discovery(self):
        """Test that estimation respects max_discovery limit"""
        config = {"name": "test", "base_url": self.base_url, "rate_limit": 0.1}

        result = estimate_pages(config, max_discovery=3, timeout=5)

        # Should not discover more than max_discovery
        self.assertLessEqual(result["discovered"], 3)

    def test_estimate_pages_with_start_urls(self):
        """Test estimation with custom start_urls"""
        config = {
            "name": "test",
            "base_url": self.base_url,
            "start_urls": [self.base_url],
            "rate_limit": 0.1,
        }

        result = estimate_pages(config, max_discovery=2, timeout=5)

        self.assertIsInstance(result, dict)
        self.assertIn("discovered", result)


class TestEstimateParserDefault(unittest.TestCase):
    """Regression for CLI-04: the unified `estimate` subcommand parser must give
    --max-discovery a finite default. Without it argparse leaves it None, which
    estimate_pages() treats as UNLIMITED — so `skill-seekers estimate <cfg>`
    crawled the whole site instead of stopping at the 1000-page cap."""

    def test_max_discovery_has_finite_default(self):
        import argparse

        from skill_seekers.cli.constants import DEFAULT_MAX_DISCOVERY
        from skill_seekers.cli.parsers.estimate_parser import EstimateParser

        parser = argparse.ArgumentParser()
        EstimateParser().add_arguments(parser)
        ns = parser.parse_args(["someconfig.json"])
        self.assertIsNotNone(ns.max_discovery)
        self.assertEqual(ns.max_discovery, DEFAULT_MAX_DISCOVERY)


class TestEstimatePagesCLI(unittest.TestCase):
    """Test estimate_pages command-line interface (via entry point)"""

    def test_cli_help_output(self):
        """Test that skill-seekers estimate --help works"""
        import subprocess

        try:
            result = subprocess.run(
                ["skill-seekers", "estimate", "--help"], capture_output=True, text=True, timeout=5
            )

            # Should return successfully (0 or 2 for argparse)
            self.assertIn(result.returncode, [0, 2])
            output = result.stdout + result.stderr
            self.assertTrue("usage:" in output.lower() or "estimate" in output.lower())
        except FileNotFoundError:
            self.skipTest("skill-seekers command not installed")

    def test_cli_executes_with_help_flag(self):
        """Test that skill-seekers-estimate entry point works"""
        import subprocess

        try:
            result = subprocess.run(
                ["skill-seekers-estimate", "--help"], capture_output=True, text=True, timeout=5
            )

            # Should return successfully
            self.assertIn(result.returncode, [0, 2])
        except FileNotFoundError:
            self.skipTest("skill-seekers-estimate command not installed")

    def test_cli_requires_config_argument(self):
        """Test that CLI requires config file argument"""
        import subprocess

        try:
            # Run without config argument
            result = subprocess.run(
                ["skill-seekers", "estimate"], capture_output=True, text=True, timeout=5
            )

            # Should fail (non-zero exit code) or show usage
            self.assertTrue(
                result.returncode != 0
                or "usage" in result.stderr.lower()
                or "usage" in result.stdout.lower()
            )
        except FileNotFoundError:
            self.skipTest("skill-seekers command not installed")

    def test_cli_all_flag_lists_configs(self):
        """Test that --all flag lists all available configs"""
        import subprocess

        try:
            # Run with --all flag
            result = subprocess.run(
                ["skill-seekers", "estimate", "--all"], capture_output=True, text=True, timeout=10
            )

            # Should succeed
            self.assertEqual(result.returncode, 0)

            # Should contain expected output
            output = result.stdout
            self.assertIn("AVAILABLE CONFIGS", output)
            self.assertIn("Total:", output)
            self.assertIn("configs found", output)

            # Should list some known configs
            # (these should exist in api/configs_repo/official/)
            self.assertTrue(
                "react" in output.lower()
                or "django" in output.lower()
                or "godot" in output.lower(),
                "Expected at least one known config name in output",
            )
        except FileNotFoundError:
            self.skipTest("skill-seekers command not installed")

    def test_cli_all_flag_with_direct_entry_point(self):
        """Test --all flag works with skill-seekers-estimate entry point"""
        import subprocess

        try:
            result = subprocess.run(
                ["skill-seekers-estimate", "--all"], capture_output=True, text=True, timeout=10
            )

            # Should succeed
            self.assertEqual(result.returncode, 0)

            # Should show available configs
            output = result.stdout
            self.assertIn("AVAILABLE CONFIGS", output)
        except FileNotFoundError:
            self.skipTest("skill-seekers-estimate command not installed")


class TestEstimatePagesWithRealConfig(unittest.TestCase):
    """Test estimation with real config files (if available)"""

    @pytest.fixture(autouse=True)
    def _local_site(self, local_docs_site):
        self.base_url = local_docs_site

    def test_estimate_with_real_config_file(self):
        """Test estimation using a real config file (if exists)"""
        config_path = Path("configs/react.json")

        if not config_path.exists():
            self.skipTest("configs/react.json not found")

        with open(config_path) as f:
            config = json.load(f)

        config.update(base_url=self.base_url, start_urls=[self.base_url], rate_limit=0)
        config["url_patterns"] = {"include": [], "exclude": []}
        # Use very low max_discovery to keep test fast
        result = estimate_pages(config, max_discovery=3, timeout=5)

        self.assertIsInstance(result, dict)
        self.assertIn("discovered", result)
        self.assertGreater(result["discovered"], 0)


if __name__ == "__main__":
    unittest.main()
