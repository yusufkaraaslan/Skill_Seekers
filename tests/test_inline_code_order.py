"""Text and code blocks must keep page order, not be split into two buckets."""

from pathlib import Path

import pytest

from skill_seekers.cli.doc_scraper import DocToSkillConverter
from skill_seekers.cli.html_parsing import parse_html

FIXTURE = Path(__file__).parent / "fixtures" / "mkdocs_matchers.html"
URL = "https://example.com/matchers/"
CONFIG = {"name": "test", "base_url": "https://example.com/", "selectors": {"main_content": "main"}}
EXPECTED = ["text", "text", "code", "text", "text", "code", "text", "code"]


@pytest.fixture
def converter(tmp_path: Path) -> DocToSkillConverter:
    conv = DocToSkillConverter(CONFIG, dry_run=True)
    conv.skill_dir = str(tmp_path)
    (tmp_path / "references").mkdir()
    return conv


def _pages(converter: DocToSkillConverter) -> list[dict]:
    html = FIXTURE.read_text(encoding="utf-8")
    return [
        converter.extract_content(parse_html(html, context="fixture"), URL),
        converter._extract_html_as_markdown(html, URL),
    ]


def test_body_blocks_interleave_text_and_code(converter: DocToSkillConverter) -> None:
    for page in _pages(converter):
        assert [b["type"] for b in page["body_blocks"]] == EXPECTED
        code = [b["code"] for b in page["body_blocks"] if b["type"] == "code"]
        assert code[0] == "mock.Foo(Equal(&Bar{}))"
        assert code[1].startswith("WhenSingle(mock.Foo(NotEqual(1)))")
        assert code[2].startswith("WhenSingle(mock.Foo(Any[int]()))")


def test_code_samples_and_content_still_populated(converter: DocToSkillConverter) -> None:
    for page in _pages(converter):
        assert len(page["code_samples"]) == 3  # no duplicates, no cap at 4 in extraction
        assert "reflect.DeepEqual compares values" in page["content"]


def test_reference_file_keeps_code_after_its_sentence(converter: DocToSkillConverter) -> None:
    page = _pages(converter)[0]
    page["title"] = "Matchers"
    converter.create_reference_file("matchers", [page])
    out = (Path(converter.skill_dir) / "references" / "matchers.md").read_text(encoding="utf-8")
    intro = out.index("compares values by their content:")
    assert intro < out.index("mock.Foo(Equal(&Bar{}))") < out.index("The NotEqual matcher")
    assert "**Examples:**" not in out


def test_page_without_body_blocks_uses_legacy_layout(converter: DocToSkillConverter) -> None:
    page = {
        "url": URL,
        "title": "Old",
        "headings": [],
        "content": "Legacy cached text that is long enough to be kept.",
        "code_samples": [{"code": "print('legacy example')", "language": "python"}],
    }
    converter.create_reference_file("old", [page])
    out = (Path(converter.skill_dir) / "references" / "old.md").read_text(encoding="utf-8")
    assert "**Examples:**" in out


@pytest.mark.parametrize("fallback", [False, True])
def test_nested_code_keeps_explicit_language(converter, fallback):
    html = '<main><pre><code class="language-ruby">ambiguous sample text</code></pre></main>'
    if fallback:
        page = converter._extract_html_as_markdown(html, URL)
    else:
        converter.config["selectors"] = {"main_content": "main", "code_blocks": "pre, pre code"}
        page = converter.extract_content(parse_html(html), URL)
    assert page["code_samples"] == [{"code": "ambiguous sample text", "language": "ruby"}]


def test_custom_code_paragraph_is_not_reclassified_as_prose(converter):
    converter.config["selectors"] = {"main_content": "main", "code_blocks": "p.code"}
    page = converter.extract_content(
        parse_html('<main><p class="code language-python">print("custom example")</p></main>'), URL
    )
    assert page["code_samples"] == [{"code": 'print("custom example")', "language": "python"}]
    assert [block["type"] for block in page["body_blocks"]] == ["code"]


def test_paragraph_inside_selected_code_container_is_not_rendered_twice(converter):
    converter.config["selectors"] = {"main_content": "main", "code_blocks": ".code"}
    page = converter.extract_content(
        parse_html('<main><div class="code"><p>unique_code_content_long_enough</p></div></main>'),
        URL,
    )
    converter.create_reference_file("nested", [page])
    out = (Path(converter.skill_dir) / "references" / "nested.md").read_text()
    assert out.count("unique_code_content_long_enough") == 1


@pytest.mark.parametrize("fallback", [False, True])
def test_all_examples_render_once_in_order(converter, fallback):
    html = (
        "<main>"
        + "".join(
            f'<p>Explanation for example number {i}.</p><pre><code class="language-python">'
            f'print("example number {i}")</code></pre>'
            for i in range(6)
        )
        + "</main>"
    )
    if fallback:
        page = converter._extract_html_as_markdown(html, URL)
    else:
        page = converter.extract_content(parse_html(html), URL)
    converter.create_reference_file("all", [page])
    out = (Path(converter.skill_dir) / "references" / "all.md").read_text()
    previous = -1
    for i in range(6):
        explanation = f"Explanation for example number {i}."
        code = f'print("example number {i}")'
        assert previous < out.index(explanation) < out.index(code)
        assert out.count(code) == 1
        previous = out.index(code)


def test_embedded_markdown_fences_stay_inside_code_block(converter):
    html = '<main><pre><code class="language-markdown">```python\nprint("example")\n```</code></pre></main>'
    page = converter.extract_content(parse_html(html), URL)
    converter.create_reference_file("fences", [page])
    out = (Path(converter.skill_dir) / "references" / "fences.md").read_text()
    assert '````markdown\n```python\nprint("example")\n```\n````' in out
