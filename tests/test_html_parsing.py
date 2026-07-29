"""Tests for html_parsing.parse_html — parser fallback chain (issue #96, F1.4)."""

import logging

import pytest
from bs4 import BeautifulSoup

from skill_seekers.cli import html_parsing
from skill_seekers.cli.html_parsing import (
    PARSER_CHAIN,
    available_parsers,
    parse_html,
)

WELL_FORMED = "<html><body><div id='main'><p>Documentation content</p></div></body></html>"
# html.parser treats the unterminated comment as swallowing the whole
# document, yielding a tree with no tags at all.
UNTERMINATED_COMMENT = "<!-- <div>content</div>"


class TestPrimaryParserUnchanged:
    """Well-formed markup must produce byte-identical output to plain html.parser."""

    def test_well_formed_html_matches_html_parser(self):
        soup = parse_html(WELL_FORMED)
        expected = BeautifulSoup(WELL_FORMED, "html.parser")
        assert str(soup) == str(expected)

    def test_bytes_input(self):
        soup = parse_html(WELL_FORMED.encode("utf-8"))
        assert soup.find("p").get_text() == "Documentation content"

    def test_plain_text_does_not_trigger_fallback(self, caplog):
        text = "just plain text, no tags here"
        with caplog.at_level(logging.WARNING):
            soup = parse_html(text)
        assert soup.find(True) is None
        assert soup.get_text() == text
        assert not caplog.records

    def test_empty_markup(self):
        soup = parse_html("")
        assert soup.find(True) is None


class TestFallback:
    def test_html5lib_available(self):
        # html5lib is a core dependency precisely so the fallback exists
        # everywhere; if this fails the environment is missing it.
        assert "html5lib" in available_parsers()

    def test_tag_free_result_falls_back(self, caplog):
        with caplog.at_level(logging.WARNING):
            soup = parse_html(UNTERMINATED_COMMENT, context="https://example.com/docs")
        # html5lib always builds a proper document skeleton
        assert soup.find(True) is not None
        assert any("recovered with" in r.message for r in caplog.records)
        assert any("https://example.com/docs" in r.getMessage() for r in caplog.records)

    def test_primary_parser_exception_falls_back(self, monkeypatch):
        real_bs = BeautifulSoup

        def flaky(markup, parser, *args, **kwargs):
            if parser == "html.parser":
                raise RecursionError("simulated parser blow-up")
            return real_bs(markup, parser, *args, **kwargs)

        monkeypatch.setattr(html_parsing, "BeautifulSoup", flaky)
        soup = parse_html(WELL_FORMED)
        assert soup.find("p").get_text() == "Documentation content"

    def test_unavailable_parser_skipped_silently(self):
        soup = parse_html(WELL_FORMED, parsers=("no-such-parser", "html.parser"))
        assert soup.find("p").get_text() == "Documentation content"

    def test_all_parsers_tag_free_returns_least_bad(self, caplog):
        # Restrict the chain so no lenient parser can recover
        with caplog.at_level(logging.WARNING):
            soup = parse_html(UNTERMINATED_COMMENT, parsers=("html.parser",))
        assert soup.find(True) is None
        assert any("tag-free" in r.message for r in caplog.records)

    def test_all_parsers_raise_reraises(self, monkeypatch):
        def always_broken(*_args, **_kwargs):
            raise ValueError("simulated total failure")

        monkeypatch.setattr(html_parsing, "BeautifulSoup", always_broken)
        with pytest.raises(ValueError, match="simulated total failure"):
            parse_html(WELL_FORMED)


class TestAvailableParsers:
    def test_html_parser_always_available(self):
        assert "html.parser" in available_parsers()

    def test_unknown_parser_excluded(self):
        assert available_parsers(("no-such-parser", "html.parser")) == ["html.parser"]

    def test_default_chain_order_preserved(self):
        avail = available_parsers()
        assert avail == [p for p in PARSER_CHAIN if p in avail]


class TestScraperIntegration:
    """The scrapers must route document parsing through parse_html."""

    def test_doc_scraper_uses_parse_html(self):
        import inspect

        from skill_seekers.cli import doc_scraper

        src = inspect.getsource(doc_scraper)
        assert 'BeautifulSoup(response.content, "html.parser")' not in src
        assert "parse_html(" in src

    def test_html_scraper_uses_parse_html(self):
        import inspect

        from skill_seekers.cli import html_scraper

        src = inspect.getsource(html_scraper)
        assert 'BeautifulSoup(raw_html, "html.parser")' not in src
        assert "parse_html(" in src
