"""Reject misleading PDF fragment labels while preserving real code snippets."""

import pytest

from skill_seekers.cli.language_detector import LanguageDetector


@pytest.mark.parametrize(
    "text",
    [
        "MessageHeaderMsgType=FF1180ApplID",
        "MsgType=190007190007ApplID",
        "field+token reference",
        "<Instrument>48SecurityID",
        "<Instrument> <SecurityID>",
        "one party report for pass through",
    ],
)
def test_document_fragment_has_no_language_label(text):
    """Assignment fragments and XML tags alone are insufficient language evidence."""
    assert LanguageDetector().detect_from_code(text) == ("unknown", 0.0)


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("=text-default\n  color: $text-muted", "sass"),
        ("+border-radius(5px)", "sass"),
        ("body\n  +border-radius(5px)", "sass"),
        ("$text-muted: #666", "scss"),
        ("interface Repo<T> { get(id: string): T }", "tsx"),
        ("export type Names = Array<string>;", "typescript"),
        ("from pathlib import Path", "python"),
        ("using UnityEngine;", "csharp"),
    ],
)
def test_real_language_signals_are_preserved(code, expected):
    """Anchors support indented Sass; generic TypeScript retains other evidence."""
    language, confidence = LanguageDetector().detect_from_code(code)
    assert language == expected
    assert confidence >= 0.15


@pytest.mark.parametrize("followed_by_prose", [False, True], ids=["page-end", "font-change"])
@pytest.mark.parametrize(
    ("code", "expected_language"),
    [
        ("from pathlib import Path", "python"),
        ("from collections import deque", "python"),
        ("git push origin main", "unknown"),
        ("pip install requests flask", "unknown"),
        ("select name from users", "sql"),
        ("MessageHeaderMsgType=FF1180ApplID", "unknown"),
        ("<Instrument>48SecurityID", "unknown"),
    ],
)
def test_pdf_font_extraction_preserves_content(code, expected_language, followed_by_prose):
    """Real PDFs retain alphabetic code and fragments without misleading labels."""
    fitz = pytest.importorskip("fitz")
    from skill_seekers.cli.pdf_extractor_poc import PDFExtractor

    extractor = PDFExtractor.__new__(PDFExtractor)
    extractor.language_detector = LanguageDetector()
    with fitz.open() as document:
        page = document.new_page()
        page.insert_text((72, 72), code, fontname="cour")
        if followed_by_prose:
            page.insert_text((72, 100), "Explanatory paragraph.", fontname="helv")
        blocks = extractor.detect_code_blocks_by_font(page)

    assert len(blocks) == 1
    assert blocks[0]["code"] == code
    assert blocks[0]["language"] == expected_language
