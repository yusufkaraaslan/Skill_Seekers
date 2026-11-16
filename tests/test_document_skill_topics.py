"""Generated usage guidance must describe real content, not category placeholders."""

import pytest

from skill_seekers.cli.html_scraper import HtmlToSkillConverter
from skill_seekers.cli.pdf_scraper import PDFToSkillConverter


@pytest.fixture(params=["html", "pdf"])
def converter(request, tmp_path):
    config = {"name": "example", "description": "Example source", "output_dir": str(tmp_path)}
    if request.param == "pdf":
        config["pdf_path"] = "manual.pdf"
        result = PDFToSkillConverter(config)
        pages = [
            {
                "page_number": 1,
                "headings": [
                    {"level": "h1", "text": "Network Authentication"},
                    {"level": "h2", "text": "Token Refresh"},
                ],
            }
        ]
    else:
        config["html_path"] = "manual.html"
        result = HtmlToSkillConverter(config)
        pages = [
            {
                "section_number": 1,
                "heading": "Network Authentication",
                "heading_level": "h1",
                "headings": [{"level": "h2", "text": "Token Refresh"}],
            }
        ]
    result.extracted_data = {"pages": pages}
    return result


def render(converter, categorized):
    from pathlib import Path

    converter._generate_skill_md(categorized)
    content = (Path(converter.skill_dir) / "SKILL.md").read_text()
    usage = content.split("## 💡 When to Use This Skill\n\n")[1].split("\n## ")[0]
    return content, usage


def test_single_file_uses_document_headings_not_filename(converter):
    _, usage = render(converter, converter.categorize_content())
    assert "- Network Authentication\n" in usage
    assert "- Token Refresh\n" in usage
    assert "- manual" not in usage


def test_empty_categories_do_not_claim_coverage(converter):
    _, usage = render(
        converter,
        {
            "deployment": {"title": "Deployment", "pages": []},
            "auth": {"title": "Authentication", "pages": converter.extracted_data["pages"]},
        },
    )
    assert "- Authentication\n" in usage
    assert "Deployment" not in usage


@pytest.mark.parametrize("title", ["Content", "Other", "Additional Content", None, ""])
def test_fallback_uses_both_document_and_pdf_heading_shapes(converter, title):
    _, usage = render(
        converter, {"content": {"title": title, "pages": converter.extracted_data["pages"]}}
    )
    assert "- Network Authentication\n" in usage
    assert "- Token Refresh\n" in usage
    assert "- None" not in usage


def test_topics_are_unique_single_lines_and_capped_at_four(converter):
    titles = [
        "Authentication",
        " authentication ",
        "Rate\n limits",
        "Caching",
        "Retries",
        "Timeouts",
    ]
    categories = {
        str(i): {"title": title, "pages": converter.extracted_data["pages"]}
        for i, title in enumerate(titles)
    }
    _, usage = render(converter, categories)
    assert [line for line in usage.splitlines() if line.startswith("- ")] == [
        "- Authentication",
        "- Rate limits",
        "- Caching",
        "- Retries",
    ]


def test_no_topics_gets_honest_source_fallback(converter):
    converter.extracted_data = {"pages": []}
    _, usage = render(converter, {"content": {"title": "Content", "pages": []}})
    assert "source material" in usage
    assert "topics are listed" not in usage
    assert "- Content" not in usage


@pytest.mark.parametrize("patterns", ["", "  \n", "*See reference files for detailed content*\n\n"])
def test_quick_reference_is_absent_without_patterns(converter, monkeypatch, patterns):
    monkeypatch.setattr(converter, "_format_patterns_from_content", lambda: patterns)
    content, _ = render(converter, {})
    assert "## ⚡ Quick Reference" not in content
    assert "See reference files for detailed content" not in content


def test_real_quick_reference_patterns_are_preserved(converter):
    if isinstance(converter, PDFToSkillConverter):
        converter.extracted_data["pages"][0]["headings"].append(
            {"level": "h2", "text": "API Examples"}
        )
    else:
        converter.extracted_data["pages"][0]["heading"] = "API Examples"
    content, _ = render(converter, {})
    assert "## ⚡ Quick Reference" in content
    assert "- API Examples (" in content


def test_heading_fallback_prefers_top_levels_and_deduplicates(converter):
    converter.extracted_data = {
        "pages": [
            {
                "headings": [
                    {"level": "h3", "text": "Minor detail"},
                    {"level": "h1", "text": "Authentication"},
                    {"level": "h1", "text": " authentication "},
                    {"level": "h2", "text": "Token Refresh"},
                    {"level": "h1", "text": "Rate Limits"},
                    {"level": "h2", "text": "Retries"},
                    {"level": "h2", "text": "Timeouts"},
                ]
            }
        ]
    }
    _, usage = render(converter, {})
    assert [line for line in usage.splitlines() if line.startswith("- ")] == [
        "- Authentication",
        "- Rate Limits",
        "- Token Refresh",
        "- Retries",
    ]


def test_html_directory_uses_headings_instead_of_source_filenames(tmp_path):
    converter = HtmlToSkillConverter(
        {"name": "example", "html_path": str(tmp_path), "output_dir": str(tmp_path)}
    )
    converter.extracted_data = {
        "total_files": 2,
        "pages": [
            {"heading": "Authentication", "source_file": "intro.html"},
            {"heading": "Rate Limits", "source_file": "extras.html"},
        ],
    }
    _, usage = render(converter, converter.categorize_content())
    assert "- Authentication\n" in usage
    assert "- Rate Limits\n" in usage
    assert "- intro\n" not in usage
    assert "- extras\n" not in usage
