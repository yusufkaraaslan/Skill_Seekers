#!/usr/bin/env python3
"""
Tests for the shared scraper helpers in cli/scraper_utils.py.

Pins the exact scoring behavior so the consolidation of 8 duplicated
`_score_code_quality` functions (3 logic variants) into one parametrized helper
cannot silently change scores.
"""

import pathlib
import unittest

from skill_seekers.cli.scraper_utils import (
    score_code_quality,
    extract_table_from_html,
    parse_leading_int,
)

# Representative inputs with their pinned scores (captured from the pre-merge
# implementations: standard == the 6-module/asciidoc variant; notebook == jupyter).
_FIXTURES = {
    "empty": "",
    "short": "x=1",
    "func": "def foo():\n    return 1\n",
    "long": "\n".join(f"line_{i} = {i}" for i in range(12)),
    "magic": "%matplotlib inline\n!pip install x\n",
    "docstring": 'def f():\n    """doc"""\n    return 1\n' + "\n".join(str(i) for i in range(8)),
}
_STANDARD = {"empty": 0.0, "short": 3.3, "func": 5.3, "long": 7.3, "magic": 5.0, "docstring": 9.3}
_NOTEBOOK = {"empty": 0.0, "short": 3.3, "func": 5.3, "long": 7.3, "magic": 4.2, "docstring": 9.6}

_SCORE_MODULES = [
    "asciidoc_scraper",
    "chat_scraper",
    "pptx_scraper",
    "confluence_scraper",
    "epub_scraper",
    "jupyter_scraper",
    "word_scraper",
    "html_scraper",
]


class TestScoreCodeQuality(unittest.TestCase):
    def test_standard_mode_parity(self):
        for key, expected in _STANDARD.items():
            self.assertAlmostEqual(score_code_quality(_FIXTURES[key]), expected, places=2, msg=key)

    def test_notebook_mode_parity(self):
        for key, expected in _NOTEBOOK.items():
            self.assertAlmostEqual(
                score_code_quality(_FIXTURES[key], notebook_mode=True), expected, places=2, msg=key
            )

    def test_clamped_range(self):
        self.assertEqual(score_code_quality(""), 0.0)
        big = "def f():\n" + "\n".join(f"    x{i} = import_thing()" for i in range(50))
        self.assertLessEqual(score_code_quality(big), 10.0)


class TestExtractTable(unittest.TestCase):
    def test_thead_and_rows(self):
        from bs4 import BeautifulSoup

        html = "<table><thead><tr><th>A</th><th>B</th></tr></thead>"
        html += "<tbody><tr><td>1</td><td>2</td></tr></tbody></table>"
        table = BeautifulSoup(html, "html.parser").find("table")
        self.assertEqual(
            extract_table_from_html(table), {"headers": ["A", "B"], "rows": [["1", "2"]]}
        )

    def test_no_thead_uses_first_row_as_header(self):
        from bs4 import BeautifulSoup

        html = "<table><tr><td>H1</td><td>H2</td></tr><tr><td>x</td><td>y</td></tr></table>"
        table = BeautifulSoup(html, "html.parser").find("table")
        self.assertEqual(
            extract_table_from_html(table), {"headers": ["H1", "H2"], "rows": [["x", "y"]]}
        )

    def test_empty_table_returns_none(self):
        from bs4 import BeautifulSoup

        table = BeautifulSoup("<table></table>", "html.parser").find("table")
        self.assertIsNone(extract_table_from_html(table))

    def test_body_row_equal_to_header_is_kept(self):
        """DOC-13: a body row whose text equals the header must NOT be dropped —
        the old `cells != headers` skip discarded legitimate data rows."""
        from bs4 import BeautifulSoup

        html = (
            "<table><thead><tr><th>A</th><th>B</th></tr></thead>"
            "<tbody><tr><td>A</td><td>B</td></tr><tr><td>1</td><td>2</td></tr></tbody></table>"
        )
        table = BeautifulSoup(html, "html.parser").find("table")
        self.assertEqual(
            extract_table_from_html(table),
            {"headers": ["A", "B"], "rows": [["A", "B"], ["1", "2"]]},
        )


class TestParseLeadingInt(unittest.TestCase):
    """DOC-15: width/height attrs like '100%'/'50px' must not crash int()."""

    def test_percentage(self):
        self.assertEqual(parse_leading_int("100%"), 100)

    def test_pixels(self):
        self.assertEqual(parse_leading_int("50px"), 50)

    def test_plain_int(self):
        self.assertEqual(parse_leading_int("30"), 30)
        self.assertEqual(parse_leading_int(30), 30)

    def test_non_numeric_and_none_use_default(self):
        self.assertEqual(parse_leading_int("auto"), 0)
        self.assertEqual(parse_leading_int(""), 0)
        self.assertEqual(parse_leading_int(None), 0)
        self.assertEqual(parse_leading_int(None, default=7), 7)


class TestNoDuplicateDefinitions(unittest.TestCase):
    """No scraper should still define its own _score_code_quality."""

    def test_score_helper_not_redefined(self):
        import skill_seekers.cli as cli_pkg

        cli_dir = pathlib.Path(cli_pkg.__file__).parent
        for mod in _SCORE_MODULES:
            src = (cli_dir / f"{mod}.py").read_text()
            self.assertNotIn(
                "def _score_code_quality",
                src,
                f"{mod} should import score_code_quality from scraper_utils, not redefine it",
            )


if __name__ == "__main__":
    unittest.main()
