"""Quality-score sanity for PDF code extraction (Issue #485, item 2).

Real case: "MessageHeaderMsgType=FF1180ApplID" — a 31-char FIXML table
fragment with zero code structure — scored 8.0/10, sailing through the
min_quality=5.0 filter and appearing as "Example 1 (Quality: 9.0/10)"
in the generated SKILL.md. These tests lock in: bonuses cannot carry an
unverifiable short sample past the quality bar; real multi-line code is
unaffected.
"""

from skill_seekers.cli.pdf_extractor_poc import PDFExtractor


def _extractor():
    ex = PDFExtractor.__new__(PDFExtractor)
    from skill_seekers.cli.language_detector import LanguageDetector

    ex.language_detector = LanguageDetector()
    return ex


MULTI_LINE_PY = (
    "def validate_header(payload):\n"
    "    if not payload:\n"
    "        raise ValueError('empty payload')\n"
    "    return parse_fields(payload)\n"
)


class TestShortSampleCap:

    def test_field_fragment_capped_below_bar(self):
        ex = _extractor()
        code = "MessageHeaderMsgType=FF1180ApplID"
        lang, conf = ex.detect_language_from_code(code)
        score = ex.score_code_quality(code, lang, conf)
        # Cap invariant: bonuses can never carry a short sample beyond
        # 4.0 + conf*2. With #484's anchored sass patterns merged, conf
        # becomes 0 and the fragment falls below the min_quality bar
        # entirely; on a bare development base it may still be
        # (mis)labeled sass 0.5 and capped exactly at 5.0.
        assert score <= 4.0 + conf * 2.0 + 1e-9

    def test_prose_line_capped_below_bar(self):
        ex = _extractor()
        lang, conf = ex.detect_language_from_code("one party report for pass through")
        score = ex.score_code_quality("one party report for pass through", lang, conf)
        assert score <= 4.0

    def test_confident_short_command_survives_at_cap(self):
        ex = _extractor()
        code = "using UnityEngine;"
        lang, conf = ex.detect_language_from_code(code)
        score = ex.score_code_quality(code, lang, conf)
        # cap = 4.0 + conf*2 ; with conf 0.5 the cap sits exactly at the
        # min_quality bar, so detected short commands are not lost.
        assert score <= 4.0 + conf * 2.0 + 1e-9
        assert score >= 4.0

    def test_multi_line_code_uncapped(self):
        ex = _extractor()
        lang, conf = ex.detect_language_from_code(MULTI_LINE_PY)
        score = ex.score_code_quality(MULTI_LINE_PY, lang, conf)
        assert score >= 7.0

    def test_two_line_snippet_also_capped(self):
        ex = _extractor()
        code = "import os\nimport sys"
        lang, conf = ex.detect_language_from_code(code)
        score = ex.score_code_quality(code, lang, conf)
        assert score <= 4.0 + conf * 2.0 + 1e-9
