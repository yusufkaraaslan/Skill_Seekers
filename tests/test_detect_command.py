"""Tests for the read-only source detection command (``skill-seekers detect``)."""

from __future__ import annotations

import json

from skill_seekers.cli.exit_codes import EXIT_SUCCESS, EXIT_VALIDATION
from skill_seekers.cli.main import main


def test_human_readable_output_for_github_slug(capsys):
    assert main(["detect", "facebook/react"]) == EXIT_SUCCESS
    out = capsys.readouterr().out
    assert "Type: github" in out
    assert "Suggested name: react" in out
    assert "repo: facebook/react" in out
    assert "Validation: OK" in out


def test_json_output_has_source_info_and_validity(capsys):
    assert main(["detect", "https://docs.python.org", "--json"]) == EXIT_SUCCESS
    payload = json.loads(capsys.readouterr().out)
    # Load-bearing keys only: SourceInfo may grow fields without this command changing.
    assert payload["type"] == "web"
    assert payload["parsed"]["url"] == "https://docs.python.org"
    assert payload["suggested_name"] == "python"
    assert payload["raw_input"] == "https://docs.python.org"
    assert payload["valid"] is True
    assert payload["validation_error"] is None


def test_undetectable_source_reports_error_without_traceback(tmp_path, capsys):
    bogus = str(tmp_path / "not-a-source")  # absolute so cwd contents cannot interfere
    assert main(["detect", bogus]) == EXIT_VALIDATION
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Cannot determine source type" in captured.err
    assert "Traceback" not in captured.err


def test_undetectable_source_with_json_still_emits_json(tmp_path, capsys):
    """Scripts parse stdout; an empty stdout with a stderr message is not a contract."""
    bogus = str(tmp_path / "not-a-source")
    assert main(["detect", bogus, "--json"]) == EXIT_VALIDATION
    payload = json.loads(capsys.readouterr().out)
    assert "Cannot determine source type" in payload["error"]


def test_detected_but_missing_file_matches_create_verdict(tmp_path, capsys):
    """`create ./missing.pdf` refuses the source, so `detect` must not say it is fine."""
    missing = str(tmp_path / "missing.pdf")
    assert main(["detect", missing, "--json"]) == EXIT_VALIDATION
    payload = json.loads(capsys.readouterr().out)
    assert payload["type"] == "pdf"
    assert payload["valid"] is False
    assert "does not exist" in payload["validation_error"]

    assert main(["detect", missing]) == EXIT_VALIDATION
    assert "Validation: FAILED" in capsys.readouterr().out


def test_existing_local_sources_validate(tmp_path, capsys):
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    assert main(["detect", str(pdf), "--json"]) == EXIT_SUCCESS
    assert json.loads(capsys.readouterr().out)["type"] == "pdf"

    (tmp_path / "proj").mkdir()
    (tmp_path / "proj" / "main.py").write_text("print(1)\n")
    assert main(["detect", str(tmp_path / "proj"), "--json"]) == EXIT_SUCCESS
    assert json.loads(capsys.readouterr().out)["type"] == "local"
