"""Preserve PDF code lines, inline spans, and examples spanning text blocks."""

import ast

import pytest

from skill_seekers.cli.language_detector import LanguageDetector
from skill_seekers.cli.pdf_extractor_poc import PDFExtractor


class FakePage:
    """Supply controlled PDF span layouts without font/rendering dependencies."""

    def __init__(self, blocks):
        self.blocks = blocks

    def get_text(self, _kind):
        return {"blocks": self.blocks}


def span(text, font="Courier"):
    return {"text": text, "font": font}


def block(*lines):
    return {"lines": [{"spans": line} for line in lines]}


@pytest.fixture
def extractor():
    instance = PDFExtractor.__new__(PDFExtractor)
    instance.language_detector = LanguageDetector()
    return instance


@pytest.mark.parametrize("separate_blocks", [False, True])
@pytest.mark.parametrize("end_with_prose", [False, True])
def test_complete_function_preserves_lines_spans_and_short_return(
    extractor, separate_blocks, end_with_prose
):
    # The short return line must stay with the header even across text objects.
    header = [span("def "), span("calculate_total():", "Courier-Bold")]
    body = [span("    return 42")]
    blocks = [block(header), block(body)] if separate_blocks else [block(header, body)]
    if end_with_prose:
        blocks.append(block([span("Explanatory paragraph", "Helvetica")]))
    samples = extractor.detect_code_blocks_by_font(FakePage(blocks))
    assert len(samples) == 1
    assert samples[0]["code"] == "def calculate_total():\n    return 42"
    ast.parse(samples[0]["code"])


def test_prose_separates_candidates_without_dropping_following_code(extractor):
    page = FakePage(
        [
            block(
                [span("from pathlib import Path"), span(" Explanation", "Helvetica")],
                [span('print("hello")')],
            )
        ]
    )
    samples = extractor.detect_code_blocks_by_font(page)
    assert [sample["code"] for sample in samples] == ["from pathlib import Path", 'print("hello")']


def test_continuation_and_blank_lines_are_preserved(extractor):
    lines = ["result = first + \\", "    second", "", "print(result)"]
    page = FakePage([block(*[[span(line)] for line in lines])])
    samples = extractor.detect_code_blocks_by_font(page)
    assert len(samples) == 1
    assert samples[0]["code"] == "\n".join(lines)
    ast.parse(samples[0]["code"])


@pytest.mark.parametrize("separate_blocks", [False, True])
def test_real_pdf_keeps_complete_function(tmp_path, separate_blocks):
    fitz = pytest.importorskip("fitz")
    pdf_path = tmp_path / "function.pdf"
    expected = "def calculate_total():\n    return 42"
    with fitz.open() as document:
        page = document.new_page()
        if separate_blocks:
            page.insert_text((72, 72), "def calculate_total():", fontname="cour")
            page.insert_text((72, 120), "    return 42", fontname="cour")
        else:
            page.insert_text((72, 72), expected, fontname="cour")
        assert len(page.get_text("dict")["blocks"]) == (2 if separate_blocks else 1)
        document.save(pdf_path)

    extractor = PDFExtractor(
        str(pdf_path), min_quality=5.0, extract_images=False, use_cache=False, verbose=False
    )
    result = extractor.extract_all()
    font_samples = [
        sample
        for sample in result["pages"][0]["code_samples"]
        if sample["detection_method"] == "font"
    ]
    assert len(font_samples) == 1
    assert font_samples[0]["code"] == expected
    ast.parse(font_samples[0]["code"])


@pytest.mark.parametrize(
    "code",
    [
        'print("hello")',
        "from pathlib import Path",
        "git push origin main",
        "pip install requests flask",
    ],
)
def test_short_examples_are_still_accepted(extractor, code):
    samples = extractor.detect_code_blocks_by_font(FakePage([block([span(code)])]))
    assert len(samples) == 1
    assert samples[0]["code"] == code
    assert samples[0]["quality_score"] >= 5.0
