"""Golden-output tests for the PDF scraper (Phase 2 port).

The golden trees under tests/golden/phase2/pdf*/ were captured from the
PRE-DocumentSkillBuilder code; these tests prove the port is byte-identical.
The fixture exercises every build path PDF supports: page_number-keyed pages,
headings list (no top-level heading), multi-language code samples (incl.
>500 chars + quality ordering), the code_blocks compat key, extracted_images
(pre-saved) and legacy raw-bytes images, pattern keywords, language stats,
quality statistics, and all three categorization paths (single-source,
chapters, keywords incl. the empty-category and "other" buckets).
"""

import copy

from tests.phase2_golden_utils import assert_matches_golden, build_snapshot

LONG_CODE = "def long_example():\n" + "\n".join(f"    x{i} = {i}" for i in range(60))

PAGES = [
    {
        "page_number": 1,
        "text": "Welcome to the project. This page explains setup and installation.",
        "headings": [
            {"level": "h1", "text": "Getting Started Guide"},
            {"level": "h2", "text": "Installation Steps"},
        ],
        "code_samples": [
            {"language": "python", "code": "print('hello')", "quality_score": 8.5},
            {"language": "bash", "code": "pip install thing", "quality_score": 6.0},
        ],
        # pdf_extractor_poc format: already saved to disk, only linked
        "extracted_images": [
            {
                "filename": "manual_page1_img1.png",
                "page_number": 1,
                "width": 100,
                "height": 80,
            }
        ],
    },
    {
        "page_number": 2,
        "text": "All endpoints are documented here.",
        "headings": [{"level": "h2", "text": "API Usage"}],
        "code_samples": [
            {"language": "python", "code": LONG_CODE, "quality_score": 9.5},
        ],
        # Legacy format: raw bytes saved to assets/ during the build
        "images": [{"index": 0, "data": b"\x89PNG-fake-bytes"}],
    },
    {
        "page_number": 3,
        "text": "Common errors and how to fix them.",
        "headings": [{"level": "h1", "text": "Troubleshooting"}],
        # code_blocks (not code_samples) exercises the compat fallback
        "code_blocks": [{"language": "text", "code": "ERROR 42: retry the request"}],
    },
]


def _extracted_data() -> dict:
    return {
        "pages": copy.deepcopy(PAGES),
        "total_pages": 3,
        "total_code_blocks": 4,
        "total_images": 2,
        "metadata": {"title": "The Manual", "author": "Jane Doe"},
        "languages_detected": {"python": 2, "bash": 1, "text": 1},
        "quality_statistics": {"average_quality": 7.4, "valid_code_blocks": 4},
    }


def test_pdf_build_matches_golden(tmp_path):
    """pdf_path set → single-category fast path."""
    from skill_seekers.cli.pdf_scraper import PDFToSkillConverter

    converter = PDFToSkillConverter(
        {
            "name": "golden_pdf",
            "description": "Use when testing the pdf golden build",
            "pdf_path": "fixtures/manual.pdf",
            "output_dir": str(tmp_path / "skill"),
        }
    )
    converter.extracted_data = _extracted_data()
    assert_matches_golden(build_snapshot(converter), "pdf")


def test_pdf_keyword_categorization_matches_golden(tmp_path):
    """No pdf_path, no chapters → keyword categorization (multi-source).

    Covers the scored-match, "other"-bucket, and empty-category paths.
    """
    from skill_seekers.cli.pdf_scraper import PDFToSkillConverter

    converter = PDFToSkillConverter(
        {
            "name": "golden_pdf_kw",
            "description": "Use when testing keyword categorization",
            "output_dir": str(tmp_path / "skill"),
            "categories": {
                "setup": ["setup", "installation"],
                "api": ["endpoints"],
                "deployment": ["kubernetes"],  # stays empty
            },
        }
    )
    converter.extracted_data = _extracted_data()
    assert_matches_golden(build_snapshot(converter), "pdf_kw")


def test_pdf_chapter_categorization_matches_golden(tmp_path):
    """No pdf_path, chapters present → chapter-range categorization,
    incl. the uncategorized ("Additional Content") bucket."""
    from skill_seekers.cli.pdf_scraper import PDFToSkillConverter

    converter = PDFToSkillConverter(
        {
            "name": "golden_pdf_ch",
            "description": "Use when testing chapter categorization",
            "output_dir": str(tmp_path / "skill"),
        }
    )
    data = _extracted_data()
    # Page 4 falls outside every chapter range → "uncategorized" bucket.
    data["pages"].append(
        {
            "page_number": 4,
            "text": "Appendix material outside any chapter.",
            "headings": [],
        }
    )
    data["total_pages"] = 4
    data["chapters"] = [
        {"title": "Chapter 1: Basics", "start_page": 1, "end_page": 2},
        {"title": "Chapter 2: Advanced", "start_page": 3, "end_page": 3},
    ]
    converter.extracted_data = data
    assert_matches_golden(build_snapshot(converter), "pdf_chapters")
