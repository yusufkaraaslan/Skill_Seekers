"""Runner job types added for the skill/config/analyze/environment pages."""
# ruff: noqa: F811

import os
from pathlib import Path

from tests.test_web_api import _mk_skill, workspace  # noqa: F401
from skill_seekers.web import runner


def test_run_upload_packages_then_uploads(workspace, monkeypatch):
    root, _ = workspace
    calls = []

    def fake_cli(module, argv):
        calls.append((module, argv))
        if module.endswith("package_skill"):
            Path(argv[0]).with_suffix(".zip").write_text("zip")
        return 0

    monkeypatch.setattr(runner, "_run_cli_main", fake_cli)
    spec = {
        "skill_dir": str(root / "output/demo"),
        "output_dir": str(root / "output/_packages"),
        "target": "chroma",
        "options": {"persist_directory": "./chroma_db"},
        "cwd": str(root),
    }
    assert runner.run_upload(spec) == 0
    upload = next(c for c in calls if c[0].endswith("upload_skill"))
    assert upload[1][0].endswith("chroma/demo.zip")
    assert upload[1][1:5] == ["--target", "chroma", "--persist-directory", "./chroma_db"]


def test_run_upload_picks_newest_archive_by_mtime(workspace, monkeypatch):
    """Regression: run_package's collision naming keeps the ORIGINAL <name>.zip
    and suffixes every later regeneration (<name>-<suffix>.zip). Since "-"
    sorts before ".", a lexical pick (`sorted(...)[-1]`) always returns the
    first-ever archive. run_upload must instead ship whichever archive is
    newest by mtime, or a second upload of a changed skill ships stale bytes.
    """
    root, _ = workspace
    calls = []
    counter = {"n": 0}

    def fake_cli(module, argv):
        calls.append((module, argv))
        if module.endswith("package_skill"):
            counter["n"] += 1
            Path(argv[0]).with_suffix(".zip").write_text(f"content-{counter['n']}")
        return 0

    monkeypatch.setattr(runner, "_run_cli_main", fake_cli)
    spec = {
        "skill_dir": str(root / "output/demo"),
        "output_dir": str(root / "output/_packages"),
        "target": "chroma",
        "options": {},
        "cwd": str(root),
    }
    assert runner.run_upload(spec) == 0
    first_archive = Path(next(c for c in calls if c[0].endswith("upload_skill"))[1][0])
    assert first_archive.read_text() == "content-1"
    # Push the first archive's mtime well into the past so the second archive
    # is unambiguously newer, regardless of filesystem timestamp resolution.
    old = first_archive.stat().st_mtime - 100
    os.utime(first_archive, (old, old))
    calls.clear()

    assert runner.run_upload(spec) == 0
    second_archive = Path(next(c for c in calls if c[0].endswith("upload_skill"))[1][0])
    assert second_archive.read_text() == "content-2"


def test_run_translate_update_quality_argv(workspace, monkeypatch):
    root, _ = workspace
    calls = []
    monkeypatch.setattr(runner, "_run_cli_main", lambda m, a: calls.append((m, a)) or 0)
    skill = str(root / "output/demo")
    assert runner.run_translate({"skill_dir": skill, "languages": ["tr", "de"]}) == 0
    assert runner.run_update({"skill_dir": skill, "apply": False}) == 0
    assert runner.run_update({"skill_dir": skill, "apply": True}) == 0
    assert (
        runner.run_quality({"skill_dir": skill, "output_dir": str(root / "output/_reports")}) == 0
    )
    assert calls[0] == ("skill_seekers.cli.multilang_support", [skill, "--languages", "tr", "de"])
    assert calls[1] == ("skill_seekers.cli.incremental_updater", [skill, "--check-changes"])
    assert calls[2] == ("skill_seekers.cli.incremental_updater", [skill, "--force"])
    assert calls[3][0] == "skill_seekers.cli.quality_metrics"
    assert calls[3][1][:2] == [skill, "--report"] and calls[3][1][2] == "--output"
