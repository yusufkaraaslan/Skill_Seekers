"""Tests for the read-only source detection command."""

from __future__ import annotations

import json

from skill_seekers.cli.main import main


def test_detect_command_prints_human_readable_source_info(capsys):
    exit_code = main(["detect", "facebook/react"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Type: github" in output
    assert "Suggested name: react" in output
    assert "repo: facebook/react" in output


def test_detect_command_prints_machine_readable_json(capsys):
    exit_code = main(["detect", "https://docs.python.org", "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "type": "web",
        "parsed": {"url": "https://docs.python.org"},
        "suggested_name": "python",
        "raw_input": "https://docs.python.org",
    }


def test_detect_command_reports_invalid_source_without_traceback(capsys):
    exit_code = main(["detect", "not-a-source"])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Cannot determine source type" in captured.err
    assert "Traceback" not in captured.err
