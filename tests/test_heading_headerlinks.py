"""Headings must not contain the ¶ of MkDocs/Sphinx ``a.headerlink`` anchors."""

from pathlib import Path

from skill_seekers.cli.doc_scraper import DocToSkillConverter
from skill_seekers.cli.html_parsing import parse_html

FIXTURE = Path(__file__).parent / "fixtures" / "mkdocs_headerlinks.html"
CONFIG = {"name": "test", "base_url": "https://example.com/", "selectors": {"main_content": "main"}}


def _converter() -> DocToSkillConverter:
    return DocToSkillConverter(CONFIG, dry_run=True)


def test_extract_content_strips_pilcrow_from_real_mkdocs_page() -> None:
    soup = parse_html(FIXTURE.read_text(encoding="utf-8"), context="fixture")
    page = _converter().extract_content(soup, "https://example.com/matchers/")
    assert [h["text"] for h in page["headings"]] == ["Matchers", "Equal", "Not Equal"]


def test_html_fallback_strips_pilcrow_from_real_mkdocs_page() -> None:
    page = _converter()._extract_html_as_markdown(
        FIXTURE.read_text(encoding="utf-8"), "https://example.com/matchers/"
    )
    assert [h["text"] for h in page["headings"]] == ["Matchers", "Equal", "Not Equal"]


def test_pilcrow_in_ordinary_content_is_kept() -> None:
    soup = parse_html("<main><h2>Section ¶ sign</h2></main>", context="inline")
    page = _converter().extract_content(soup, "https://example.com/x")
    assert page["headings"][0]["text"] == "Section ¶ sign"
