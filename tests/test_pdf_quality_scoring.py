"""Lower short PDF sample scores without rejecting valid examples by default."""

import pytest

from skill_seekers.cli.language_detector import LanguageDetector
from skill_seekers.cli.pdf_extractor_poc import PDFExtractor


@pytest.fixture
def extractor():
    instance = PDFExtractor.__new__(PDFExtractor)
    instance.language_detector = LanguageDetector()
    return instance


@pytest.mark.parametrize(
    "code",
    ["MessageHeaderMsgType=FF1180ApplID", "one party report for pass through"],
)
def test_uncertain_fragments_get_neutral_scores(extractor, code):
    language, confidence = extractor.detect_language_from_code(code)
    assert (language, confidence) == ("unknown", 0.0)
    assert extractor.score_code_quality(code, language, confidence) == 5.0


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ('print("Hello world")', 5.4),
        ("import os\nimport sys", 5.4),
        ("git push origin main", 5.0),
        ("pip install requests flask", 5.0),
        ("using UnityEngine;", 6.0),
    ],
)
def test_short_code_remains_at_or_above_default_threshold(extractor, code, expected):
    language, confidence = extractor.detect_language_from_code(code)
    score = extractor.score_code_quality(code, language, confidence)
    assert score == pytest.approx(expected)
    assert score >= 5.0


def test_blank_lines_do_not_inflate_short_sample_score(extractor):
    code = "\nimport os\n\nimport sys\n\n"
    language, confidence = extractor.detect_language_from_code(code)
    assert extractor.score_code_quality(code, language, confidence) == pytest.approx(5.4)


def test_three_or_more_nonempty_lines_retain_existing_score(extractor):
    code = (
        "def validate_header(payload):\n"
        "    if not payload:\n"
        "        raise ValueError('empty payload')\n"
        "    return parse_fields(payload)\n"
    )
    language, confidence = extractor.detect_language_from_code(code)
    assert extractor.score_code_quality(code, language, confidence) == 10.0


@pytest.mark.parametrize("code", ["", "x"])
def test_cap_does_not_raise_existing_low_scores(extractor, code):
    assert extractor.score_code_quality(code, "unknown", 0.0) < 5.0


@pytest.mark.parametrize("threshold", [0.0, 5.0, 5.5])
@pytest.mark.parametrize(
    "code",
    [
        'print("Hello world")',
        "import os\nimport sys",
        "git push origin main",
        "pip install requests flask",
        "using UnityEngine;",
        "MessageHeaderMsgType=FF1180ApplID",
        "one party report for pass through",
    ],
)
def test_real_pdf_preserves_examples_by_default_and_allows_stricter_filtering(
    tmp_path, code, threshold
):
    fitz = pytest.importorskip("fitz")
    pdf_path = tmp_path / "sample.pdf"
    with fitz.open() as document:
        page = document.new_page()
        page.insert_text((72, 72), code, fontname="cour")
        document.save(pdf_path)

    extractor = PDFExtractor(
        str(pdf_path), min_quality=threshold, extract_images=False, use_cache=False, verbose=False
    )
    result = extractor.extract_all()
    samples = result["pages"][0]["code_samples"]
    should_keep = threshold <= 5.0 or code == "using UnityEngine;"
    assert bool(samples) == should_keep
    assert result["pages"][0]["text"].strip()
    for sample in samples:
        assert sample["quality_score"] >= threshold
        assert sample["quality_score"] <= 6.0
    if should_keep:
        combined = "\n".join(sample["code"] for sample in samples)
        for line in code.splitlines():
            assert line in combined
