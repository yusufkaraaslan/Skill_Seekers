"""Golden-output tests for the HTML scraper (Phase 2 port).

The golden trees under tests/golden/phase2/html*/ were captured from the
PRE-DocumentSkillBuilder code; these tests prove the port is byte-identical.
The fixture exercises every build path: metadata (title/author/language/
description/keywords), headings + sub-headings, multi-language code samples
(incl. >500 chars + quality ordering), tables with and without headers,
images (alt / title-only display), links, the html-specific pattern keyword
("changelog"), language stats, and all three categorization paths:
single-file, keyword-based, and multi-file grouping by source_file.
"""

import copy

from tests.phase2_golden_utils import assert_matches_golden, build_snapshot

LONG_CODE = "def long_example():\n" + "\n".join(f"    x{i} = {i}" for i in range(60))

SECTIONS = [
    {
        "section_number": 1,
        "heading": "Getting Started Guide",
        "heading_level": "h1",
        "headings": [
            {"level": "h2", "text": "Installation Steps"},
            {"level": "h3", "text": "Verify Setup"},
        ],
        "text": "Welcome to the project. This section explains setup.",
        "code_samples": [
            {"language": "python", "code": "print('hello')", "quality_score": 8.5},
            {"language": "bash", "code": "pip install thing", "quality_score": 6.0},
        ],
        "tables": [
            {"headers": ["Option", "Default"], "rows": [["debug", "false"], ["port", "8080"]]},
        ],
        "images": [
            {
                "src": "img/setup.png",
                "alt": "Setup diagram",
                "title": "",
                "width": 640,
                "height": 0,
                "data": b"",
                "index": 0,
            },
        ],
        "links": [
            {"href": "https://example.com/docs", "text": "Project Docs", "title": ""},
            {"href": "https://example.com/install", "text": "Install Guide", "title": "Install"},
        ],
        "source_file": "intro.html",
    },
    {
        "section_number": 2,
        "heading": "API Usage",
        "heading_level": "h2",
        "headings": [],
        "text": "All endpoints are documented here.",
        "code_samples": [
            {"language": "python", "code": LONG_CODE, "quality_score": 9.5},
        ],
        "tables": [
            # Table without headers exercises the headerless rendering path
            {"headers": [], "rows": [["a", "b"], ["c", "d"]]},
        ],
        "images": [
            # alt empty -> display falls back to title
            {
                "src": "img/flow.svg",
                "alt": "",
                "title": "Request Flow",
                "width": 0,
                "height": 0,
                "data": b"",
                "index": 0,
            },
        ],
        "links": [],
        "source_file": "intro.html",
    },
    {
        "section_number": 3,
        "heading": "Troubleshooting",
        "heading_level": "h1",
        "headings": [{"level": "h2", "text": "Common Errors"}],
        "text": "",
        "code_samples": [],
        "tables": [],
        "images": [],
        "links": [],
        "source_file": "extras.html",
    },
    {
        # "changelog" is an html-only pattern keyword (not in the shared base
        # list) — catches accidental use of the base pattern formatter.
        "section_number": 4,
        "heading": "Changelog",
        "heading_level": "h2",
        "headings": [],
        "text": "",
        "code_samples": [],
        "tables": [],
        "images": [],
        "links": [],
        "source_file": "extras.html",
    },
]


def _extracted_data(metadata: dict, total_files: int = 1) -> dict:
    return {
        "pages": copy.deepcopy(SECTIONS),
        "total_sections": 4,
        "total_code_blocks": 3,
        "total_images": 2,
        "total_files": total_files,
        "metadata": metadata,
        "languages_detected": {"python": 2, "bash": 1},
    }


def _converter(config):
    from skill_seekers.cli.html_scraper import HtmlToSkillConverter

    return HtmlToSkillConverter(config)


def test_html_build_matches_golden(tmp_path):
    """Single HTML file → single-category path named after the file stem."""
    html_file = tmp_path / "page.html"
    html_file.write_text("<html><body><h1>stub</h1></body></html>")

    converter = _converter(
        {
            "name": "golden_html",
            "description": "Use when testing the html golden build",
            "html_path": str(html_file),
            "output_dir": str(tmp_path / "skill"),
        }
    )
    converter.extracted_data = _extracted_data(
        {
            "title": "The Web Handbook",
            "author": "Jane Doe",
            "language": "en",
            "description": "A handbook about the web.",
            "keywords": "web, html, docs",
        }
    )
    assert_matches_golden(build_snapshot(converter), "html")


def test_html_keyword_categorization_matches_golden(tmp_path):
    """No html_path → keyword categorization path (incl. 'other' bucket)."""
    converter = _converter(
        {
            "name": "golden_html_kw",
            "description": "Use when testing keyword categorization",
            "output_dir": str(tmp_path / "skill"),
            "categories": {
                "setup": ["setup", "installation"],
                "api": ["endpoints"],
            },
        }
    )
    converter.extracted_data = _extracted_data({})
    assert_matches_golden(build_snapshot(converter), "html_kw")


def test_html_multi_file_matches_golden(tmp_path):
    """total_files > 1 → grouping by source_file + 'Source files' metadata."""
    converter = _converter(
        {
            "name": "golden_html_multi",
            "description": "Use when testing the multi-file html build",
            "html_path": "fixtures/site",  # directory-style path (not a file)
            "output_dir": str(tmp_path / "skill"),
        }
    )
    converter.extracted_data = _extracted_data({"title": "The Web Handbook"}, total_files=2)
    assert_matches_golden(build_snapshot(converter), "html_multi")
