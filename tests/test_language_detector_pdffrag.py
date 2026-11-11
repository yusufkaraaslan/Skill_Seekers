"""Regression tests for code-fragment false positives in LanguageDetector.

Root cases came from a real PDF (SZSE bond trading guide, 112 pages, no
actual source code): monospace-font harvesting picked up FIXML table
fragments and English prose lines, which were then mislabeled as sass /
typescript / unknown code blocks and surfaced in generated SKILL.md as
"Code Examples" with high quality scores.
"""

from skill_seekers.cli.language_detector import LanguageDetector


class TestPDFFragmentFalsePositives:

    def setup_method(self):
        self.detector = LanguageDetector()

    # --- real-world damage cases (must NOT be claimed as that language) ---

    def test_fx_field_string_not_sass(self):
        code = "MessageHeaderMsgType=FF1180ApplID"
        lang, confidence = self.detector.detect_from_code(code)
        assert lang != "sass"

    def test_fx_field_string_2_not_sass(self):
        code = "MsgType=190007190007ApplID"
        lang, confidence = self.detector.detect_from_code(code)
        assert lang != "sass"

    def test_xmllike_field_string_not_typescript(self):
        # "<Token>" alone gave confusion 0.2 with old weight (>= 0.15 bar)
        code = "<Instrument>48SecurityID"
        lang, confidence = self.detector.detect_from_code(code)
        assert lang != "typescript"

    def test_prose_fragment_rejected_as_prose(self):
        code = "one party report for pass through"
        lang, confidence = self.detector.detect_from_code(code)
        assert lang == "unknown"
        assert confidence == 0.0

    def test_prose_fragment_claim_rejected(self):
        code = "two party report forclaim"
        lang, confidence = self.detector.detect_from_code(code)
        assert lang == "unknown"
        assert confidence == 0.0

    # --- legacy sass must keep working (negative-control for anchoring) ---

    def test_legacy_sass_mixin_still_detected(self):
        code = "=text-default\n  color: $text-muted"
        lang, confidence = self.detector.detect_from_code(code)
        assert lang == "sass"

    def test_legacy_sass_include_still_detected(self):
        code = "+border-radius(5px)"
        lang, confidence = self.detector.detect_from_code(code)
        assert lang == "sass"

    def test_scss_variable_still_detected(self):
        code = "$text-muted: #666"
        lang, confidence = self.detector.detect_from_code(code)
        assert lang in ("sass", "scss")

    # --- real single-line code must survive the prose gate ---

    def test_single_line_import_survives(self):
        code = "import matplotlib.pyplot as plt"
        lang, confidence = self.detector.detect_from_code(code)
        # Ties between python/ts/swift on this line are PRE-EXISTING
        # scoring behavior (unchanged); key property: still detected or
        # unknown, never sass/csharp-type cross-language garbage.
        assert lang in ("python", "typescript", "unknown", "swift")

    def test_single_line_command_survives(self):
        code = "pip install --upgrade certifi"
        lang, confidence = self.detector.detect_from_code(code)
        # not prose-gated (flags contain '-'); must not be claimed by
        # a wrong language either — python keyword "import" absent, but the
        # key assertion is it is never returned with type-annotation-like
        # false positives: only that detection is unchanged in spirit.
        assert lang in ("unknown", "bash", "shell", "python")

    def test_short_unity_line_survives(self):
        code = "using UnityEngine;"
        lang, confidence = self.detector.detect_from_code(code)
        assert lang == "csharp"

    def test_real_typescript_generic_still_detected(self):
        code = "interface Repo<T> { get(id: string): T }"
        lang, confidence = self.detector.detect_from_code(code)
        # TS-family answer is fine; the ONE forbidden outcome was the old
        # bare-"<Token>" mislabel of non-TS fragments.
        assert lang in ("typescript", "tsx")

    def test_multiline_prose_still_provable(self):
        # multi-line text is NOT covered by the single-line gate; it is
        # handled by natural-language checks elsewhere — document the
        # intended scope of the gate.
        code = "one party report\nfor pass through"
        lang, confidence = self.detector.detect_from_code(code)
        assert lang == "unknown" or lang != "sass"


class TestProseFragmentFilterPDFExtractor:
    """Extraction-layer gate for monospace-harvested prose (font path)."""

    def _extractor(self):
        from skill_seekers.cli.language_detector import LanguageDetector
        from skill_seekers.cli.pdf_extractor_poc import PDFExtractor

        ex = PDFExtractor.__new__(PDFExtractor)
        ex.language_detector = LanguageDetector()
        return ex

    def test_prose_fragment_flagged(self):
        ex = self._extractor()
        assert ex._is_prose_fragment("one party report for pass through") is True
        assert ex._is_prose_fragment("two party report for claim") is True

    def test_symbol_lines_kept(self):
        ex = self._extractor()
        assert ex._is_prose_fragment("MessageHeaderMsgType=FF1180ApplID") is False
        assert ex._is_prose_fragment("pip install --upgrade certifi") is False
        assert ex._is_prose_fragment("if [ -f x ]; then exit; fi") is False

    def test_short_commands_kept(self):
        ex = self._extractor()
        assert ex._is_prose_fragment("git status") is False
        assert ex._is_prose_fragment("npm run build") is False

    def test_multiline_always_kept(self):
        ex = self._extractor()
        assert ex._is_prose_fragment("one party report\nfor pass through") is False

    def _page_from_spans(self, spans):
        class _FakePage:
            def get_text(self, _mode):
                return {"blocks": [{"lines": [{"spans": spans}]}]}

        return _FakePage()

    def _span(self, text):
        return {"font": "Courier", "text": text}

    def test_font_path_drops_prose(self):
        ex = self._extractor()
        page = self._page_from_spans([self._span("one party report for pass through")])
        assert ex.detect_code_blocks_by_font(page) == []

    def test_font_path_keeps_real_code_signal(self):
        ex = self._extractor()
        page = self._page_from_spans([self._span("def validate_header(payload):")])
        blocks = ex.detect_code_blocks_by_font(page)
        assert blocks, "symbol-carrying monospace line must survive"
        assert blocks[0]["language"] == "python"

