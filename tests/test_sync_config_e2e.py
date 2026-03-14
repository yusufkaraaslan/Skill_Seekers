#!/usr/bin/env python3
"""End-to-end tests for the sync-config command.

Uses a local HTTP server with realistic multi-page HTML navigation to test
the full pipeline: BFS crawl -> link discovery -> diff -> config update.

Also includes an integration test against a real public docs site.
"""

import json
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import pytest

from skill_seekers.cli.sync_config import discover_urls, sync_config


# ---------------------------------------------------------------------------
# Local test HTTP server
# ---------------------------------------------------------------------------

# Simulates a docs site with this navigation structure:
#
#   /docs/                  (index — links to guide, api, faq)
#   /docs/guide             (links to guide/install, guide/usage)
#   /docs/guide/install     (leaf page)
#   /docs/guide/usage       (leaf page, links back to guide)
#   /docs/api               (links to api/auth, api/users)
#   /docs/api/auth          (leaf page)
#   /docs/api/users         (leaf page)
#   /docs/faq               (leaf page)
#   /blog/post-1            (outside /docs/ — should be excluded)

_SITE_PAGES = {
    "/docs/": """<!DOCTYPE html><html><head><title>Docs Home</title></head><body>
        <h1>Documentation</h1>
        <nav>
            <a href="/docs/guide">Guide</a>
            <a href="/docs/api">API Reference</a>
            <a href="/docs/faq">FAQ</a>
            <a href="/blog/post-1">Blog</a>
            <a href="https://github.com/example/repo">GitHub</a>
        </nav>
    </body></html>""",
    "/docs/guide": """<!DOCTYPE html><html><body>
        <h1>Guide</h1>
        <a href="/docs/guide/install">Installation</a>
        <a href="/docs/guide/usage">Usage</a>
        <a href="/docs/">Back to docs</a>
    </body></html>""",
    "/docs/guide/install": """<!DOCTYPE html><html><body>
        <h1>Installation</h1><p>pip install example</p>
        <a href="/docs/guide">Back to guide</a>
    </body></html>""",
    "/docs/guide/usage": """<!DOCTYPE html><html><body>
        <h1>Usage</h1><p>import example</p>
        <a href="/docs/guide">Back to guide</a>
    </body></html>""",
    "/docs/api": """<!DOCTYPE html><html><body>
        <h1>API Reference</h1>
        <a href="/docs/api/auth">Authentication</a>
        <a href="/docs/api/users">Users</a>
    </body></html>""",
    "/docs/api/auth": """<!DOCTYPE html><html><body>
        <h1>Authentication</h1><p>Use tokens.</p>
    </body></html>""",
    "/docs/api/users": """<!DOCTYPE html><html><body>
        <h1>Users API</h1><p>CRUD operations.</p>
    </body></html>""",
    "/docs/faq": """<!DOCTYPE html><html><body>
        <h1>FAQ</h1><p>Common questions.</p>
    </body></html>""",
    "/blog/post-1": """<!DOCTYPE html><html><body>
        <h1>Blog Post</h1><p>This is a blog post outside /docs/.</p>
    </body></html>""",
}

# All docs pages that should be discovered (excluding /blog/)
_ALL_DOC_URLS_PATHS = {
    "/docs/",
    "/docs/guide",
    "/docs/guide/install",
    "/docs/guide/usage",
    "/docs/api",
    "/docs/api/auth",
    "/docs/api/users",
    "/docs/faq",
}


class _TestHandler(SimpleHTTPRequestHandler):
    """Serve pages from the in-memory _SITE_PAGES dict."""

    def do_GET(self):
        path = self.path.split("?")[0].split("#")[0]
        content = _SITE_PAGES.get(path)
        if content is None:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def log_message(self, format, *args):  # noqa: ARG002
        pass  # Suppress request logging during tests


def _start_server() -> tuple[HTTPServer, int]:
    """Start a local HTTP server on a random port. Returns (server, port)."""
    server = HTTPServer(("127.0.0.1", 0), _TestHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _write_config(config: dict) -> Path:
    """Write a config dict to a temp JSON file and return its path."""
    tmp = tempfile.mktemp(suffix=".json")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    return Path(tmp)


# ---------------------------------------------------------------------------
# E2E tests using local HTTP server
# ---------------------------------------------------------------------------


@pytest.mark.e2e
class TestSyncConfigE2E(unittest.TestCase):
    """End-to-end tests using a local HTTP server with realistic HTML."""

    @classmethod
    def setUpClass(cls):
        cls.server, cls.port = _start_server()
        cls.base_url = f"http://127.0.0.1:{cls.port}/docs/"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    # -- discover_urls --

    def test_discover_finds_all_doc_pages(self):
        """BFS should discover all 8 /docs/ pages from the root."""
        discovered = discover_urls(
            base_url=self.base_url,
            seed_urls=[self.base_url],
            depth=3,
            rate_limit=0,
        )

        expected = {f"http://127.0.0.1:{self.port}{p}" for p in _ALL_DOC_URLS_PATHS}
        self.assertEqual(discovered, expected)

    def test_discover_excludes_blog(self):
        """Pages outside /docs/ base_url should be excluded."""
        discovered = discover_urls(
            base_url=self.base_url,
            seed_urls=[self.base_url],
            depth=3,
            rate_limit=0,
        )

        blog_url = f"http://127.0.0.1:{self.port}/blog/post-1"
        self.assertNotIn(blog_url, discovered)

    def test_discover_excludes_external(self):
        """External URLs (github.com) should be excluded."""
        discovered = discover_urls(
            base_url=self.base_url,
            seed_urls=[self.base_url],
            depth=3,
            rate_limit=0,
        )

        self.assertFalse(
            any("github.com" in u for u in discovered),
            "External URLs should not be discovered",
        )

    def test_discover_depth_1_finds_direct_links_only(self):
        """Depth 1 from root should find guide, api, faq but NOT nested pages."""
        discovered = discover_urls(
            base_url=self.base_url,
            seed_urls=[self.base_url],
            depth=1,
            rate_limit=0,
        )

        # Direct children of /docs/
        self.assertIn(f"http://127.0.0.1:{self.port}/docs/guide", discovered)
        self.assertIn(f"http://127.0.0.1:{self.port}/docs/api", discovered)
        self.assertIn(f"http://127.0.0.1:{self.port}/docs/faq", discovered)

        # Nested pages should NOT be present (they're at depth 2)
        self.assertNotIn(f"http://127.0.0.1:{self.port}/docs/guide/install", discovered)
        self.assertNotIn(f"http://127.0.0.1:{self.port}/docs/api/auth", discovered)

    def test_discover_with_include_pattern(self):
        """Include pattern should filter results."""
        discovered = discover_urls(
            base_url=self.base_url,
            seed_urls=[self.base_url],
            include_patterns=["/api"],
            depth=3,
            rate_limit=0,
        )

        # Only /api/ pages should be discovered
        for url in discovered:
            self.assertIn("/api", url, f"URL {url} does not match include pattern /api")

    def test_discover_with_exclude_pattern(self):
        """Exclude pattern should remove matching pages."""
        discovered = discover_urls(
            base_url=self.base_url,
            seed_urls=[self.base_url],
            exclude_patterns=["/faq"],
            depth=3,
            rate_limit=0,
        )

        faq_url = f"http://127.0.0.1:{self.port}/docs/faq"
        self.assertNotIn(faq_url, discovered)
        # Other pages should still be found
        self.assertIn(f"http://127.0.0.1:{self.port}/docs/guide", discovered)

    def test_discover_max_pages_limit(self):
        """max_pages should cap discovery."""
        discovered = discover_urls(
            base_url=self.base_url,
            seed_urls=[self.base_url],
            depth=3,
            max_pages=3,
            rate_limit=0,
        )

        self.assertLessEqual(len(discovered), 3)

    # -- sync_config (full pipeline with file I/O) --

    def test_sync_config_dry_run_detects_new_pages(self):
        """Dry-run should detect pages missing from the config."""
        config = {
            "name": "test-site",
            "sources": [
                {
                    "type": "documentation",
                    "base_url": self.base_url,
                    "start_urls": [
                        f"http://127.0.0.1:{self.port}/docs/guide",
                        f"http://127.0.0.1:{self.port}/docs/faq",
                    ],
                }
            ],
        }
        path = _write_config(config)

        result = sync_config(str(path), apply=False, depth=3, rate_limit=0)

        self.assertFalse(result["applied"])
        self.assertGreater(len(result["added"]), 0, "Should detect new pages")
        # api, api/auth, api/users, guide/install, guide/usage, /docs/ itself
        # should all be in added
        self.assertGreaterEqual(result["total_discovered"], 6)

        # File should NOT be modified
        with open(path, encoding="utf-8") as f:
            saved = json.load(f)
        self.assertEqual(len(saved["sources"][0]["start_urls"]), 2)
        path.unlink()

    def test_sync_config_apply_updates_config(self):
        """--apply should write all discovered URLs to the config."""
        config = {
            "name": "test-site",
            "sources": [
                {
                    "type": "documentation",
                    "base_url": self.base_url,
                    "start_urls": [f"http://127.0.0.1:{self.port}/docs/guide"],
                }
            ],
        }
        path = _write_config(config)

        result = sync_config(str(path), apply=True, depth=3, rate_limit=0)

        self.assertTrue(result["applied"])

        # Verify the file was updated
        with open(path, encoding="utf-8") as f:
            saved = json.load(f)
        saved_urls = saved["sources"][0]["start_urls"]
        self.assertEqual(len(saved_urls), result["total_discovered"])

        # All expected URLs should be present
        expected = {f"http://127.0.0.1:{self.port}{p}" for p in _ALL_DOC_URLS_PATHS}
        for url in expected:
            self.assertIn(url, saved_urls, f"Expected URL missing from saved config: {url}")

        path.unlink()

    def test_sync_config_idempotent(self):
        """Running sync twice with --apply should be a no-op the second time."""
        config = {
            "name": "test-site",
            "sources": [
                {
                    "type": "documentation",
                    "base_url": self.base_url,
                    "start_urls": [],
                }
            ],
        }
        path = _write_config(config)

        # First run: should apply changes
        result1 = sync_config(str(path), apply=True, depth=3, rate_limit=0)
        self.assertTrue(result1["applied"])
        self.assertGreater(len(result1["added"]), 0)

        # Second run: should detect no changes
        result2 = sync_config(str(path), apply=True, depth=3, rate_limit=0)
        self.assertFalse(result2["applied"])
        self.assertEqual(result2["added"], [])
        self.assertEqual(result2["removed"], [])

        path.unlink()

    def test_sync_config_detects_removed_pages(self):
        """Pages in config but not discovered should show as removed."""
        config = {
            "name": "test-site",
            "sources": [
                {
                    "type": "documentation",
                    "base_url": self.base_url,
                    "start_urls": [
                        f"http://127.0.0.1:{self.port}/docs/guide",
                        f"http://127.0.0.1:{self.port}/docs/old-page-that-no-longer-exists",
                    ],
                }
            ],
        }
        path = _write_config(config)

        result = sync_config(str(path), apply=False, depth=3, rate_limit=0)

        self.assertIn(
            f"http://127.0.0.1:{self.port}/docs/old-page-that-no-longer-exists",
            result["removed"],
        )
        path.unlink()

    def test_sync_config_preserves_other_config_fields(self):
        """--apply should only modify start_urls, preserving all other fields."""
        config = {
            "name": "my-skill",
            "description": "Important skill description",
            "version": "1.0.0",
            "sources": [
                {
                    "type": "documentation",
                    "base_url": self.base_url,
                    "start_urls": [],
                    "selectors": {"main_content": "article", "title": "h1"},
                    "url_patterns": {"include": [], "exclude": []},
                    "rate_limit": 0.5,
                    "max_pages": 100,
                },
                {
                    "type": "github",
                    "repo": "owner/repo",
                },
            ],
        }
        path = _write_config(config)

        sync_config(str(path), apply=True, depth=3, rate_limit=0)

        with open(path, encoding="utf-8") as f:
            saved = json.load(f)

        # Non-start_urls fields should be untouched
        self.assertEqual(saved["name"], "my-skill")
        self.assertEqual(saved["description"], "Important skill description")
        self.assertEqual(saved["version"], "1.0.0")
        self.assertEqual(saved["sources"][0]["selectors"]["main_content"], "article")
        self.assertEqual(saved["sources"][0]["rate_limit"], 0.5)
        self.assertEqual(saved["sources"][1]["type"], "github")
        self.assertEqual(saved["sources"][1]["repo"], "owner/repo")

        # start_urls should be updated
        self.assertGreater(len(saved["sources"][0]["start_urls"]), 0)

        path.unlink()

    def test_sync_config_with_nav_seed_urls(self):
        """nav_seed_urls should be used as BFS seeds instead of start_urls."""
        config = {
            "name": "test-site",
            "sources": [
                {
                    "type": "documentation",
                    "base_url": self.base_url,
                    "start_urls": [],
                    # Only seed from /docs/api — should only discover API pages
                    "nav_seed_urls": [f"http://127.0.0.1:{self.port}/docs/api"],
                }
            ],
        }
        path = _write_config(config)

        result = sync_config(str(path), apply=False, depth=1, rate_limit=0)

        # Should discover at least the API seed page
        self.assertGreater(len(result["added"]), 0, "nav_seed_urls should discover pages")
        # All added URLs should be under /docs/
        for url in result["added"]:
            self.assertTrue(url.startswith(self.base_url), f"URL outside base: {url}")

        path.unlink()

    def test_sync_config_legacy_format(self):
        """Legacy flat config format should work end-to-end."""
        config = {
            "name": "test-site",
            "base_url": self.base_url,
            "start_urls": [f"http://127.0.0.1:{self.port}/docs/guide"],
        }
        path = _write_config(config)

        result = sync_config(str(path), apply=True, depth=3, rate_limit=0)

        self.assertTrue(result["applied"])

        with open(path, encoding="utf-8") as f:
            saved = json.load(f)
        self.assertGreater(len(saved["start_urls"]), 1)

        path.unlink()


# ---------------------------------------------------------------------------
# CLI subprocess tests
# ---------------------------------------------------------------------------


@pytest.mark.e2e
class TestSyncConfigCLIE2E(unittest.TestCase):
    """Test the CLI entry point via subprocess."""

    @classmethod
    def setUpClass(cls):
        cls.server, cls.port = _start_server()
        cls.base_url = f"http://127.0.0.1:{cls.port}/docs/"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_cli_dry_run(self):
        """CLI dry-run should print diff and exit 0."""
        config = {
            "name": "test",
            "sources": [
                {
                    "type": "documentation",
                    "base_url": self.base_url,
                    # Only one URL configured — the rest should show as "new"
                    "start_urls": [f"http://127.0.0.1:{self.port}/docs/faq"],
                    # Seed from root to discover all pages
                    "nav_seed_urls": [self.base_url],
                }
            ],
        }
        path = _write_config(config)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skill_seekers.cli.sync_config",
                "--config",
                str(path),
                "--depth",
                "3",
                "--rate-limit",
                "0",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        self.assertEqual(result.returncode, 0, f"CLI failed: {result.stderr}")
        # Should mention new pages in the output (logged to stderr)
        combined = result.stderr.lower() + result.stdout.lower()
        self.assertIn("new page", combined, f"Expected 'new page' in output: {combined}")
        path.unlink()

    def test_cli_apply(self):
        """CLI --apply should update the config file."""
        config = {
            "name": "test",
            "sources": [
                {
                    "type": "documentation",
                    "base_url": self.base_url,
                    "start_urls": [f"http://127.0.0.1:{self.port}/docs/faq"],
                    "nav_seed_urls": [self.base_url],
                }
            ],
        }
        path = _write_config(config)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skill_seekers.cli.sync_config",
                "--config",
                str(path),
                "--apply",
                "--depth",
                "3",
                "--rate-limit",
                "0",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        self.assertEqual(result.returncode, 0, f"CLI failed: {result.stderr}")

        with open(path, encoding="utf-8") as f:
            saved = json.load(f)
        self.assertGreater(len(saved["sources"][0]["start_urls"]), 0)

        path.unlink()

    def test_cli_help(self):
        """CLI --help should print usage and exit 0."""
        result = subprocess.run(
            [sys.executable, "-m", "skill_seekers.cli.sync_config", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("sync", result.stdout.lower())
        self.assertIn("--config", result.stdout)
        self.assertIn("--apply", result.stdout)
        self.assertIn("--depth", result.stdout)

    def test_cli_missing_config_exits_nonzero(self):
        """CLI with a non-existent config should fail."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skill_seekers.cli.sync_config",
                "--config",
                "/nonexistent/path/config.json",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        self.assertNotEqual(result.returncode, 0)


# ---------------------------------------------------------------------------
# Integration test against real public site
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestSyncConfigRealSite(unittest.TestCase):
    """Integration test against a real public docs site.

    Skipped by default (use ``-m integration`` to run).
    Uses httpbin.org which is a stable, small public HTTP test service.
    """

    def test_discover_urls_real_http(self):
        """discover_urls should work against a real HTTP server."""
        # Use Python docs — small, stable, well-structured
        discovered = discover_urls(
            base_url="https://docs.python.org/3/library/",
            seed_urls=["https://docs.python.org/3/library/functions.html"],
            depth=1,
            max_pages=10,
            rate_limit=0.5,
        )

        # Should find at least the seed page itself
        self.assertGreater(len(discovered), 0)
        # All discovered URLs should be under the base
        for url in discovered:
            self.assertTrue(
                url.startswith("https://docs.python.org/3/library/"),
                f"Discovered URL outside base: {url}",
            )


if __name__ == "__main__":
    unittest.main()
