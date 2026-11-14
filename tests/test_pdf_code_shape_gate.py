"""Structural gate for font-path code candidates (Issue #485, item 1).

Real case: a 112-page exchange-rule PDF has ZERO source code, yet
font-based detection stored monospace table fragments
("MessageHeaderMsgType=FF1180ApplID", vertically stacked cells like
"ApplID\nSTEP\nBinary") as code blocks — monospace font alone was
treated as proof of code. These tests lock in the shape gate (real
code structure on some line, or a strong language signature, or a
statement terminator + token spacing for single lines) and the line
structure preservation for multi-line monospace runs.
"""

from skill_seekers.cli.pdf_extractor_poc import PDFExtractor


class _FakePage:
    def __init__(self, blocks):
        self._blocks = blocks

    def get_text(self, kind, **kwargs):
        if kind == "dict":
            return {"blocks": self._blocks}
        return ""


def _mono(text, font="Courier"):
    return {"font": font, "text": text}


def _prose(text, font="Helvetica"):
    return {"font": font, "text": text}


def _line(*spans):
    return {"spans": list(spans)}


def _block(*lines):
    return {"lines": list(lines)}


def _page(*blocks):
    return _FakePage(list(blocks))


def _extractor():
    ex = PDFExtractor.__new__(PDFExtractor)
    from skill_seekers.cli.language_detector import LanguageDetector

    ex.language_detector = LanguageDetector()
    return ex


class TestShapeGate:

    def test_single_line_fragment_rejected(self):
        """KEY=VALUE table fragment: no terminator, no spacing -> dropped."""
        ex = _extractor()
        blocks = [_block(_line(_mono("MessageHeaderMsgType=FF1180ApplID")))]
        assert ex.detect_code_blocks_by_font(_page(*blocks)) == []

    def test_fragments_on_separate_lines_rejected(self):
        ex = _extractor()
        blocks = [
            _block(_line(_mono("MsgType=190007190007ApplID"))),
            _block(_line(_mono("Standard Header"))),
        ]
        assert ex.detect_code_blocks_by_font(_page(*blocks)) == []

    def test_stacked_table_cells_rejected(self):
        """Vertically adjacent monospace table cells form a multi-line
        run with no code structure -> dropped (real-case regression)."""
        ex = _extractor()
        blocks = [_block(_line(_mono("ApplID")), _line(_mono("STEP")), _line(_mono("Binary")))]
        assert ex.detect_code_blocks_by_font(_page(*blocks)) == []

    def test_stacked_digits_rejected(self):
        ex = _extractor()
        blocks = [_block(_line(_mono("D")), _line(_mono("104101")), _line(_mono("410")))]
        assert ex.detect_code_blocks_by_font(_page(*blocks)) == []

    def test_multiline_run_kept_with_line_structure(self):
        """A real multi-line run is kept AND keeps its newlines."""
        ex = _extractor()
        blocks = [
            _block(
                _line(_mono("def bond_trade(price, qty):")),
                _line(_mono("    return price * qty")),
            )
        ]
        found = ex.detect_code_blocks_by_font(_page(*blocks))
        assert len(found) == 1
        assert "\n" in found[0]["code"]

    def test_statement_with_terminator_kept(self):
        """Single statement ending in ';' with token spacing survives."""
        ex = _extractor()
        blocks = [_block(_line(_mono("using UnityEngine;")))]
        found = ex.detect_code_blocks_by_font(_page(*blocks))
        assert len(found) == 1

    def test_strong_language_signature_kept(self):
        """SQL at confidence 0.9 survives without a terminator."""
        ex = _extractor()
        blocks = [_block(_line(_mono("SELECT * FROM bond_trades")))]
        found = ex.detect_code_blocks_by_font(_page(*blocks))
        assert len(found) == 1

    def test_prose_line_rejected(self):
        ex = _extractor()
        blocks = [_block(_line(_mono("one party report for pass through")))]
        assert ex.detect_code_blocks_by_font(_page(*blocks)) == []

    def test_fragment_after_prose_not_merged(self):
        """Non-mono text between two mono lines splits runs (no silent merge)."""
        ex = _extractor()
        blocks = [
            _block(
                _line(_mono("MsgType=190007190007ApplID"), _prose(" Table 4.3 ")),
                _line(_mono("MessageHeaderMsgType=FF1180ApplID")),
            )
        ]
        # both runs are shapeless fragments -> nothing stored
        assert ex.detect_code_blocks_by_font(_page(*blocks)) == []


class TestStackedCellsRegressions:
    """Residuals from the first real-case re-run: field-name/value
    column stacks that slipped past the first gate version."""

    def test_field_name_value_stacks_rejected(self):
        ex = _extractor()
        cases = [
            ["MessageHeader", "MsgType=F", "F"],
            ["60", "TransactTime"],
            ["1122", "RootPartySubIDType"],
            ["1121", "RootPartySubID"],
            ["527", "SecondaryExecID"],
        ]
        for stack in cases:
            blocks = [_block(*[_line(_mono(s)) for s in stack])]
            assert ex.detect_code_blocks_by_font(_page(*blocks)) == [], stack

    def test_keyword_led_lines_kept(self):
        ex = _extractor()
        blocks = [_block(_line(_mono("if qty <= 0:")), _line(_mono("    return reject()")))]
        found = ex.detect_code_blocks_by_font(_page(*blocks))
        assert len(found) == 1
