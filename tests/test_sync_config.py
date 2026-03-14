#!/usr/bin/env python3
"""Tests for the sync-config command.

Covers:
- URL diffing logic
- URL filtering (_is_valid_url)
- BFS discovery with mocked HTTP responses
- Config loading (unified + legacy formats)
- --apply writes correct JSON
- CLI argument parsing
- MCP tool wrapper
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from skill_seekers.cli.sync_config import (
    _get_doc_source,
    _is_valid_url,
    _set_start_urls,
    diff_urls,
    discover_urls,
    sync_config,
)


# ---------------------------------------------------------------------------
# diff_urls
# ---------------------------------------------------------------------------


class TestDiffUrls(unittest.TestCase):
    """Test the URL diffing logic."""

    def test_no_changes(self):
        configured = ["https://example.com/a", "https://example.com/b"]
        discovered = set(configured)
        added, removed = diff_urls(discovered, configured)
        self.assertEqual(added, [])
        self.assertEqual(removed, [])

    def test_added_urls(self):
        configured = ["https://example.com/a"]
        discovered = {"https://example.com/a", "https://example.com/b"}
        added, removed = diff_urls(discovered, configured)
        self.assertEqual(added, ["https://example.com/b"])
        self.assertEqual(removed, [])

    def test_removed_urls(self):
        configured = ["https://example.com/a", "https://example.com/b"]
        discovered = {"https://example.com/a"}
        added, removed = diff_urls(discovered, configured)
        self.assertEqual(added, [])
        self.assertEqual(removed, ["https://example.com/b"])

    def test_both_added_and_removed(self):
        configured = ["https://example.com/a", "https://example.com/b"]
        discovered = {"https://example.com/a", "https://example.com/c"}
        added, removed = diff_urls(discovered, configured)
        self.assertEqual(added, ["https://example.com/c"])
        self.assertEqual(removed, ["https://example.com/b"])

    def test_empty_configured(self):
        added, removed = diff_urls({"https://example.com/a"}, [])
        self.assertEqual(added, ["https://example.com/a"])
        self.assertEqual(removed, [])

    def test_empty_discovered(self):
        added, removed = diff_urls(set(), ["https://example.com/a"])
        self.assertEqual(added, [])
        self.assertEqual(removed, ["https://example.com/a"])

    def test_results_sorted(self):
        configured = ["https://example.com/z"]
        discovered = {"https://example.com/b", "https://example.com/a"}
        added, _ = diff_urls(discovered, configured)
        self.assertEqual(added, ["https://example.com/a", "https://example.com/b"])


# ---------------------------------------------------------------------------
# _is_valid_url
# ---------------------------------------------------------------------------


class TestIsValidUrl(unittest.TestCase):
    """Test the URL filtering logic."""

    def test_url_under_base(self):
        self.assertTrue(
            _is_valid_url("https://docs.example.com/guide", "https://docs.example.com/", [], [])
        )

    def test_url_not_under_base(self):
        self.assertFalse(
            _is_valid_url("https://other.com/guide", "https://docs.example.com/", [], [])
        )

    def test_include_pattern_match(self):
        self.assertTrue(
            _is_valid_url(
                "https://docs.example.com/docs/en/guide",
                "https://docs.example.com/",
                ["/docs/en/"],
                [],
            )
        )

    def test_include_pattern_no_match(self):
        self.assertFalse(
            _is_valid_url(
                "https://docs.example.com/blog/post",
                "https://docs.example.com/",
                ["/docs/en/"],
                [],
            )
        )

    def test_exclude_pattern(self):
        self.assertFalse(
            _is_valid_url(
                "https://docs.example.com/docs/en/changelog",
                "https://docs.example.com/",
                [],
                ["/changelog"],
            )
        )

    def test_include_and_exclude(self):
        # Matches include but also matches exclude -> rejected
        self.assertFalse(
            _is_valid_url(
                "https://docs.example.com/docs/en/changelog",
                "https://docs.example.com/",
                ["/docs/en/"],
                ["/changelog"],
            )
        )

    def test_no_patterns_all_valid(self):
        self.assertTrue(
            _is_valid_url("https://docs.example.com/anything", "https://docs.example.com/", [], [])
        )


# ---------------------------------------------------------------------------
# _get_doc_source / _set_start_urls
# ---------------------------------------------------------------------------


class TestConfigHelpers(unittest.TestCase):
    """Test config extraction for both unified and legacy formats."""

    def test_unified_format(self):
        config = {
            "name": "test",
            "sources": [
                {"type": "documentation", "base_url": "https://docs.example.com/"},
                {"type": "github", "repo": "owner/repo"},
            ],
        }
        source = _get_doc_source(config)
        self.assertIsNotNone(source)
        self.assertEqual(source["base_url"], "https://docs.example.com/")

    def test_unified_format_second_source(self):
        config = {
            "name": "test",
            "sources": [
                {"type": "documentation", "base_url": "https://first.com/"},
                {"type": "documentation", "base_url": "https://second.com/"},
            ],
        }
        source = _get_doc_source(config, source_index=1)
        self.assertEqual(source["base_url"], "https://second.com/")

    def test_unified_format_invalid_index(self):
        config = {"name": "test", "sources": [{"type": "github", "repo": "o/r"}]}
        self.assertIsNone(_get_doc_source(config))

    def test_legacy_flat_format(self):
        config = {"name": "test", "base_url": "https://docs.example.com/"}
        source = _get_doc_source(config)
        self.assertEqual(source["base_url"], "https://docs.example.com/")

    def test_no_source_found(self):
        config = {"name": "test"}
        self.assertIsNone(_get_doc_source(config))

    def test_set_start_urls_unified(self):
        config = {
            "sources": [
                {"type": "documentation", "base_url": "https://x.com/", "start_urls": []},
            ]
        }
        _set_start_urls(config, 0, ["https://x.com/a", "https://x.com/b"])
        self.assertEqual(config["sources"][0]["start_urls"], ["https://x.com/a", "https://x.com/b"])

    def test_set_start_urls_legacy(self):
        config = {"base_url": "https://x.com/", "start_urls": []}
        _set_start_urls(config, 0, ["https://x.com/new"])
        self.assertEqual(config["start_urls"], ["https://x.com/new"])


# ---------------------------------------------------------------------------
# discover_urls (with mocked HTTP)
# ---------------------------------------------------------------------------


class TestDiscoverUrls(unittest.TestCase):
    """Test BFS link discovery with mocked HTTP responses."""

    def _make_html(self, links: list[str]) -> str:
        hrefs = "".join(f'<a href="{u}">link</a>' for u in links)
        return f"<html><body>{hrefs}</body></html>"

    @patch("skill_seekers.cli.sync_config.requests.get")
    def test_basic_discovery(self, mock_get):
        """Discover links from a single seed page."""
        mock_resp = MagicMock()
        mock_resp.content = self._make_html(
            [
                "https://docs.example.com/page-a",
                "https://docs.example.com/page-b",
                "https://other.com/external",  # should be filtered out
            ]
        ).encode()
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = discover_urls(
            base_url="https://docs.example.com/",
            seed_urls=["https://docs.example.com/"],
            depth=1,
            rate_limit=0,
        )

        self.assertIn("https://docs.example.com/", result)
        self.assertIn("https://docs.example.com/page-a", result)
        self.assertIn("https://docs.example.com/page-b", result)
        self.assertNotIn("https://other.com/external", result)

    @patch("skill_seekers.cli.sync_config.requests.get")
    def test_depth_limiting(self, mock_get):
        """URLs at depth > limit should be discovered but not followed."""
        # Seed returns one link
        seed_html = self._make_html(["https://docs.example.com/child"])
        child_html = self._make_html(["https://docs.example.com/grandchild"])

        mock_get.side_effect = [
            MagicMock(content=seed_html.encode(), raise_for_status=MagicMock()),
            MagicMock(content=child_html.encode(), raise_for_status=MagicMock()),
        ]

        result = discover_urls(
            base_url="https://docs.example.com/",
            seed_urls=["https://docs.example.com/"],
            depth=1,  # Only follow seed page links, not child page links
            rate_limit=0,
        )

        self.assertIn("https://docs.example.com/child", result)
        # grandchild is at depth 2, which exceeds depth=1
        self.assertNotIn("https://docs.example.com/grandchild", result)

    @patch("skill_seekers.cli.sync_config.requests.get")
    def test_max_pages_limit(self, mock_get):
        """Stop after max_pages."""
        links = [f"https://docs.example.com/page-{i}" for i in range(20)]
        mock_resp = MagicMock()
        mock_resp.content = self._make_html(links).encode()
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = discover_urls(
            base_url="https://docs.example.com/",
            seed_urls=["https://docs.example.com/"],
            depth=1,
            max_pages=5,
            rate_limit=0,
        )

        self.assertLessEqual(len(result), 5)

    @patch("skill_seekers.cli.sync_config.requests.get")
    def test_include_exclude_patterns(self, mock_get):
        """Include/exclude patterns are respected."""
        mock_resp = MagicMock()
        mock_resp.content = self._make_html(
            [
                "https://docs.example.com/docs/en/guide",
                "https://docs.example.com/docs/fr/guide",
                "https://docs.example.com/blog/post",
            ]
        ).encode()
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = discover_urls(
            base_url="https://docs.example.com/",
            seed_urls=["https://docs.example.com/docs/en/overview"],
            include_patterns=["/docs/en/"],
            exclude_patterns=["/blog/"],
            depth=1,
            rate_limit=0,
        )

        self.assertIn("https://docs.example.com/docs/en/guide", result)
        self.assertNotIn("https://docs.example.com/docs/fr/guide", result)
        self.assertNotIn("https://docs.example.com/blog/post", result)

    @patch("skill_seekers.cli.sync_config.requests.get")
    def test_http_error_handled_gracefully(self, mock_get):
        """HTTP errors should not crash the discovery."""
        mock_get.side_effect = ConnectionError("Network error")

        result = discover_urls(
            base_url="https://docs.example.com/",
            seed_urls=["https://docs.example.com/"],
            depth=1,
            rate_limit=0,
        )

        # The seed URL is added to discovered even though fetch fails
        # (it's valid per filters, so it's added before the fetch attempt)
        self.assertIn("https://docs.example.com/", result)

    @patch("skill_seekers.cli.sync_config.requests.get")
    def test_fragments_stripped(self, mock_get):
        """URL fragments (#anchor) should be stripped."""
        mock_resp = MagicMock()
        mock_resp.content = self._make_html(
            [
                "https://docs.example.com/guide#section1",
                "https://docs.example.com/guide#section2",
            ]
        ).encode()
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = discover_urls(
            base_url="https://docs.example.com/",
            seed_urls=["https://docs.example.com/"],
            depth=1,
            rate_limit=0,
        )

        # Both anchors should resolve to the same URL
        self.assertIn("https://docs.example.com/guide", result)


# ---------------------------------------------------------------------------
# sync_config (integration with file I/O)
# ---------------------------------------------------------------------------


class TestSyncConfigIntegration(unittest.TestCase):
    """Test the full sync_config workflow with mocked HTTP."""

    def _write_config(self, config: dict) -> Path:
        tmp = tempfile.mktemp(suffix=".json")  # noqa: SIM115
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return Path(tmp)

    @patch("skill_seekers.cli.sync_config.discover_urls")
    def test_dry_run_does_not_modify_file(self, mock_discover):
        mock_discover.return_value = {
            "https://docs.example.com/a",
            "https://docs.example.com/b",
            "https://docs.example.com/c",
        }

        config = {
            "name": "test",
            "sources": [
                {
                    "type": "documentation",
                    "base_url": "https://docs.example.com/",
                    "start_urls": ["https://docs.example.com/a"],
                }
            ],
        }
        path = self._write_config(config)

        result = sync_config(str(path), apply=False)
        self.assertFalse(result["applied"])
        self.assertEqual(len(result["added"]), 2)

        # File should not be modified
        with open(path, encoding="utf-8") as f:
            saved = json.load(f)
        self.assertEqual(len(saved["sources"][0]["start_urls"]), 1)
        path.unlink()

    @patch("skill_seekers.cli.sync_config.discover_urls")
    def test_apply_writes_updated_urls(self, mock_discover):
        mock_discover.return_value = {
            "https://docs.example.com/a",
            "https://docs.example.com/b",
        }

        config = {
            "name": "test",
            "sources": [
                {
                    "type": "documentation",
                    "base_url": "https://docs.example.com/",
                    "start_urls": ["https://docs.example.com/a", "https://docs.example.com/old"],
                }
            ],
        }
        path = self._write_config(config)

        result = sync_config(str(path), apply=True)
        self.assertTrue(result["applied"])
        self.assertEqual(result["added"], ["https://docs.example.com/b"])
        self.assertEqual(result["removed"], ["https://docs.example.com/old"])

        # File should be updated
        with open(path, encoding="utf-8") as f:
            saved = json.load(f)
        urls = saved["sources"][0]["start_urls"]
        self.assertIn("https://docs.example.com/a", urls)
        self.assertIn("https://docs.example.com/b", urls)
        self.assertNotIn("https://docs.example.com/old", urls)
        path.unlink()

    @patch("skill_seekers.cli.sync_config.discover_urls")
    def test_no_changes_does_not_write(self, mock_discover):
        urls = ["https://docs.example.com/a", "https://docs.example.com/b"]
        mock_discover.return_value = set(urls)

        config = {
            "name": "test",
            "sources": [
                {
                    "type": "documentation",
                    "base_url": "https://docs.example.com/",
                    "start_urls": urls,
                }
            ],
        }
        path = self._write_config(config)

        result = sync_config(str(path), apply=True)
        self.assertFalse(result["applied"])
        self.assertEqual(result["added"], [])
        self.assertEqual(result["removed"], [])
        path.unlink()

    def test_missing_source_returns_error(self):
        config = {"name": "test", "sources": [{"type": "github", "repo": "o/r"}]}
        path = self._write_config(config)

        result = sync_config(str(path))
        self.assertIn("error", result)
        path.unlink()

    @patch("skill_seekers.cli.sync_config.discover_urls")
    def test_legacy_config_format(self, mock_discover):
        mock_discover.return_value = {"https://docs.example.com/a"}

        config = {
            "name": "test",
            "base_url": "https://docs.example.com/",
            "start_urls": ["https://docs.example.com/a", "https://docs.example.com/old"],
        }
        path = self._write_config(config)

        result = sync_config(str(path), apply=True)
        self.assertTrue(result["applied"])
        self.assertEqual(result["removed"], ["https://docs.example.com/old"])

        with open(path, encoding="utf-8") as f:
            saved = json.load(f)
        self.assertEqual(saved["start_urls"], ["https://docs.example.com/a"])
        path.unlink()

    @patch("skill_seekers.cli.sync_config.discover_urls")
    def test_nav_seed_urls_used_over_start_urls(self, mock_discover):
        """When nav_seed_urls is present, it should be used as the seed."""
        mock_discover.return_value = {"https://docs.example.com/a"}

        config = {
            "name": "test",
            "sources": [
                {
                    "type": "documentation",
                    "base_url": "https://docs.example.com/",
                    "start_urls": ["https://docs.example.com/a"],
                    "nav_seed_urls": [
                        "https://docs.example.com/nav1",
                        "https://docs.example.com/nav2",
                    ],
                }
            ],
        }
        path = self._write_config(config)

        sync_config(str(path))

        # Verify discover_urls was called with nav_seed_urls
        call_kwargs = mock_discover.call_args[1]
        self.assertEqual(
            call_kwargs["seed_urls"],
            ["https://docs.example.com/nav1", "https://docs.example.com/nav2"],
        )
        path.unlink()


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------


class TestSyncConfigCLI(unittest.TestCase):
    """Test CLI argument parsing and subcommand registration."""

    def test_sync_config_parser_registered(self):
        """sync-config should be a registered subcommand."""
        from skill_seekers.cli.parsers import get_parser_names

        self.assertIn("sync-config", get_parser_names())

    def test_sync_config_in_command_modules(self):
        """sync-config should be in COMMAND_MODULES."""
        from skill_seekers.cli.main import COMMAND_MODULES

        self.assertIn("sync-config", COMMAND_MODULES)

    def test_arguments_created(self):
        """Argument parser should accept all expected flags."""
        import argparse

        from skill_seekers.cli.arguments.sync_config import add_sync_config_arguments

        parser = argparse.ArgumentParser()
        add_sync_config_arguments(parser)

        args = parser.parse_args(["--config", "test.json", "--apply", "--depth", "3"])
        self.assertEqual(args.config, "test.json")
        self.assertTrue(args.apply)
        self.assertEqual(args.depth, 3)

    def test_default_values(self):
        """Default values should be sensible."""
        import argparse

        from skill_seekers.cli.arguments.sync_config import add_sync_config_arguments

        parser = argparse.ArgumentParser()
        add_sync_config_arguments(parser)

        args = parser.parse_args(["--config", "test.json"])
        self.assertFalse(args.apply)
        self.assertEqual(args.depth, 2)
        self.assertEqual(args.max_pages, 500)
        self.assertIsNone(args.rate_limit)
        self.assertEqual(args.source_index, 0)


# ---------------------------------------------------------------------------
# MCP tool
# ---------------------------------------------------------------------------


class TestSyncConfigMCPTool(unittest.TestCase):
    """Test MCP tool wrapper."""

    def test_mcp_tool_importable(self):
        """The sync_config MCP tool should be importable."""
        from skill_seekers.mcp.tools import sync_config_impl

        self.assertTrue(callable(sync_config_impl))

    def test_mcp_tool_missing_config_path(self):
        """Missing config_path should return an error."""
        import asyncio

        from skill_seekers.mcp.tools.sync_config_tools import sync_config_tool

        result = asyncio.run(sync_config_tool({}))
        self.assertTrue(any("Error" in r.text for r in result))


if __name__ == "__main__":
    unittest.main()
