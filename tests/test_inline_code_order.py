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
