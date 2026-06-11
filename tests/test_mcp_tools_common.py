#!/usr/bin/env python3
"""
Tests that MCP tool modules share one TextContent fallback and one CLI_DIR.

Guards against the boilerplate being copy-pasted back into each module (the
class of duplication consolidated into mcp/tools/_common.py).
"""

import importlib
import pathlib
import unittest

# Modules that carried the duplicated TextContent fallback.
_TEXTCONTENT_MODULES = [
    "packaging_tools",
    "scraping_tools",
    "splitting_tools",
    "config_tools",
    "marketplace_tools",
    "vector_db_tools",
    "sync_config_tools",
    "source_tools",
]

# Modules that actually use CLI_DIR — only the ones that still invoke CLI
# scripts via subprocess. config_tools/vector_db_tools/source_tools switched
# to absolute `skill_seekers.cli.*` imports (Phase 5a); splitting_tools and
# scraping_tools dispatch in-process via run_cli_main (Phase 5d). Only
# packaging_tools still shells out (LOCAL-agent enhancement paths).
_CLI_DIR_MODULES = [
    "packaging_tools",
]


def _mod(name):
    return importlib.import_module(f"skill_seekers.mcp.tools.{name}")


class TestSharedCommon(unittest.TestCase):
    def test_textcontent_is_shared(self):
        from skill_seekers.mcp.tools import _common

        for name in _TEXTCONTENT_MODULES:
            self.assertIs(
                _mod(name).TextContent,
                _common.TextContent,
                f"{name}.TextContent should be the shared _common.TextContent",
            )

    def test_cli_dir_is_shared(self):
        from skill_seekers.mcp.tools import _common

        for name in _CLI_DIR_MODULES:
            self.assertIs(
                _mod(name).CLI_DIR,
                _common.CLI_DIR,
                f"{name}.CLI_DIR should be the shared _common.CLI_DIR",
            )

    def test_no_duplicate_fallback_definitions(self):
        """The fallback class must live only in _common, not be re-pasted."""
        for name in _TEXTCONTENT_MODULES:
            src = pathlib.Path(_mod(name).__file__).read_text()
            self.assertNotIn(
                "Fallback TextContent for when MCP is not installed",
                src,
                f"{name} should import TextContent from _common, not redefine it",
            )


if __name__ == "__main__":
    unittest.main()
