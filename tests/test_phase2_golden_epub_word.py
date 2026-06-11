"""Golden-output tests for the EPUB and Word scrapers (Phase 2 port).

The golden trees under tests/golden/phase2/{epub,word}/ were captured from
the PRE-DocumentSkillBuilder code; these tests prove the port is
byte-identical. The fixture exercises every build path: metadata, headings,
sub-headings, multi-language code samples (incl. >500 chars + quality
ordering), tables with and without headers, images, keyword categorization
pattern keywords, language stats.
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
        "images": [{"index": 0, "data": b"\x89PNG-fake-bytes"}],
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
        "images": [],
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
    },
]


def _extracted_data(metadata: dict) -> dict:
    return {
        "pages": copy.deepcopy(SECTIONS),
        "total_sections": 3,
        "total_code_blocks": 3,
        "total_images": 1,
        "metadata": metadata,
        "languages_detected": {"python": 2, "bash": 1},
    }


def test_epub_build_matches_golden(tmp_path):
    from skill_seekers.cli.epub_scraper import EpubToSkillConverter

    converter = EpubToSkillConverter(
        {
            "name": "golden_epub",
            "description": "Use when testing the epub golden build",
            "epub_path": "fixtures/handbook.epub",
            "output_dir": str(tmp_path / "skill"),
        }
    )
    converter.extracted_data = _extracted_data(
        {
            "title": "The Handbook",
            "author": "Jane Doe",
            "language": "en",
            "publisher": "Acme Press",
            "date": "2024-01-01",
        }
    )
    assert_matches_golden(build_snapshot(converter), "epub")


def test_epub_keyword_categorization_matches_golden(tmp_path):
    """No epub_path → keyword categorization path (multi-source scenario)."""
    from skill_seekers.cli.epub_scraper import EpubToSkillConverter

    converter = EpubToSkillConverter(
        {
            "name": "golden_epub_kw",
            "description": "Use when testing keyword categorization",
            "output_dir": str(tmp_path / "skill"),
            "categories": {
                "setup": ["setup", "installation"],
                "api": ["endpoints"],
            },
        }
    )
    converter.extracted_data = _extracted_data({})
    assert_matches_golden(build_snapshot(converter), "epub_kw")


def test_word_build_matches_golden(tmp_path):
    from skill_seekers.cli.word_scraper import WordToSkillConverter

    converter = WordToSkillConverter(
        {
            "name": "golden_word",
            "description": "Use when testing the word golden build",
            "docx_path": "fixtures/manual.docx",
            "output_dir": str(tmp_path / "skill"),
        }
    )
    converter.extracted_data = _extracted_data(
        {
            "title": "The Manual",
            "author": "John Roe",
            "created": "2023-05-05",
            "modified": "2024-02-02",
        }
    )
    assert_matches_golden(build_snapshot(converter), "word")
