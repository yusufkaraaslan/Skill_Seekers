#!/usr/bin/env python3
"""Unit tests for package's quality-gate confirmation.

Packaging is non-destructive (it writes a zip), so a non-interactive
invocation (CI, pipes) must proceed past the quality-warning gate instead of
crashing on ``EOFError`` from ``input()``. ``--yes`` forces the same.
"""

from types import SimpleNamespace

from skill_seekers.cli.package_skill import _confirm_packaging


def _report(errors=False, warnings=False):
    return SimpleNamespace(has_errors=errors, has_warnings=warnings)


class TestConfirmPackaging:
    def test_proceeds_when_no_issues(self):
        assert _confirm_packaging(_report(), assume_yes=False) is True

    def test_assume_yes_proceeds_despite_warnings(self):
        assert _confirm_packaging(_report(warnings=True), assume_yes=True) is True

    def test_non_tty_proceeds_without_prompting(self, monkeypatch):
        # input() must NOT be called in non-interactive mode — it would EOFError.
        def _boom(*_a, **_k):
            raise AssertionError("input() should not be called when stdin is not a TTY")

        monkeypatch.setattr("sys.stdin.isatty", lambda: False)
        monkeypatch.setattr("builtins.input", _boom)
        assert _confirm_packaging(_report(warnings=True), assume_yes=False) is True

    def test_tty_declines_on_no(self, monkeypatch):
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr("builtins.input", lambda *_a: "n")
        assert _confirm_packaging(_report(warnings=True), assume_yes=False) is False

    def test_tty_accepts_on_yes(self, monkeypatch):
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr("builtins.input", lambda *_a: "y")
        assert _confirm_packaging(_report(errors=True), assume_yes=False) is True
