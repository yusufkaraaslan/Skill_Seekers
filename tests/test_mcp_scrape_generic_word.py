#!/usr/bin/env python3
"""Tests for the word (docx) source type in the scrape_generic MCP tool (#41)."""

import unittest
from unittest.mock import MagicMock, patch


class TestScrapeGenericWord(unittest.TestCase):
    def test_word_is_a_generic_source_type(self):
        from skill_seekers.mcp.tools.scraping_tools import GENERIC_SOURCE_TYPES

        self.assertIn("word", GENERIC_SOURCE_TYPES)

    def test_word_dispatches_to_converter_with_docx_path(self):
        """scrape_generic(source_type=word) builds a docx_path config and runs
        the registered word converter."""
        import asyncio

        from skill_seekers.mcp.tools import scraping_tools

        fake_converter = MagicMock()
        with (
            patch(
                "skill_seekers.cli.skill_converter.get_converter",
                return_value=fake_converter,
            ) as get_conv,
            patch.object(scraping_tools, "_run_converter", return_value=["ok"]) as run_conv,
        ):
            result = asyncio.run(
                scraping_tools.scrape_generic_tool(
                    {"source_type": "word", "path": "/docs/manual.docx", "name": "manual"}
                )
            )

        self.assertEqual(result, ["ok"])
        source_type, config = get_conv.call_args.args
        self.assertEqual(source_type, "word")
        self.assertEqual(config["name"], "manual")
        self.assertEqual(config["docx_path"], "/docs/manual.docx")
        run_conv.assert_called_once()

    def test_unknown_type_error_lists_word(self):
        """The unknown-type error message advertises word as valid."""
        import asyncio

        from skill_seekers.mcp.tools import scraping_tools

        result = asyncio.run(
            scraping_tools.scrape_generic_tool({"source_type": "nope", "path": "/x", "name": "x"})
        )
        self.assertIn("word", result[0].text)


if __name__ == "__main__":
    unittest.main()
