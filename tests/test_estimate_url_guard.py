#!/usr/bin/env python3
"""Unit tests for estimate's input guard.

`estimate` takes a config JSON file, but `create` accepts URLs — so users
naturally try `estimate <url>`. The error must explain that and point them at
the right command instead of the bare "Config file not found: <url>".
"""

import pytest

from skill_seekers.cli.estimate_pages import load_config


class TestEstimateUrlGuard:
    def test_url_argument_gives_actionable_error(self, capsys):
        with pytest.raises(SystemExit) as exc:
            load_config("https://docs.example.com/")
        assert exc.value.code != 0
        out = capsys.readouterr().out.lower()
        # Names that a config file is required and points at how to make one.
        assert "config" in out
        assert "create" in out

    def test_missing_file_still_errors_cleanly(self, capsys):
        with pytest.raises(SystemExit) as exc:
            load_config("/nonexistent/path/to/config.json")
        assert exc.value.code != 0
        out = capsys.readouterr().out.lower()
        assert "not found" in out
