"""Headings must not contain the ¶ of MkDocs/Sphinx ``a.headerlink`` anchors."""

from pathlib import Path

import pytest

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


def test_heading_title_is_clean_in_generated_reference(tmp_path) -> None:
    config = {**CONFIG, "selectors": {**CONFIG["selectors"], "title": "h1"}}
    converter = DocToSkillConverter(config, dry_run=True)
    soup = parse_html(FIXTURE.read_text(encoding="utf-8"), context="fixture")
    page = converter.extract_content(soup, "https://example.com/matchers/")
    assert page["title"] == "Matchers"
    assert page["headings"][0] == {"level": "h1", "text": "Matchers", "id": "matchers"}

    converter.skill_dir = str(tmp_path)
    (tmp_path / "references").mkdir()
    converter.create_reference_file("matchers", [page])
    reference = (tmp_path / "references" / "matchers.md").read_text(encoding="utf-8")
    assert "## Matchers\n" in reference
    assert "- Matchers\n" in reference
    assert "¶" not in reference


@pytest.mark.parametrize("fallback", [False, True])
def test_only_headerlink_elements_are_removed(fallback) -> None:
    html = """<main>
      <h2 id="literal">Section ¶ <code>token</code> <a href="/guide">Guide ¶</a>
        <a class="extra headerlink" href="#literal"><span>#</span></a></h2>
      <h3 id="empty"><a class="headerlink" href="#empty">¶</a></h3>
      <p>A paragraph with a literal ¶ and <a class="headerlink" href="/other">ordinary text</a>.</p>
    </main>"""
    converter = _converter()
    if fallback:
        page = converter._extract_html_as_markdown(html, "https://example.com/x")
    else:
        page = converter.extract_content(parse_html(html), "https://example.com/x")
        assert "https://example.com/guide" in page["links"]
        assert "https://example.com/other" in page["links"]
    assert page["headings"] == [{"level": "h2", "text": "Section ¶ token Guide ¶", "id": "literal"}]
    assert "literal ¶ and ordinary text" in page["content"]
