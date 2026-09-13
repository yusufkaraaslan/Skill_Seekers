"""Runner job types added for the skill/config/analyze/environment pages."""
# ruff: noqa: F811

import json
import os
from pathlib import Path

from tests.test_web_api import _mk_skill, workspace  # noqa: F401
from skill_seekers.web import analysis_store, runner


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


def test_run_analyze_invokes_each_tool_and_writes_manifest(workspace, monkeypatch):
    root, _ = workspace
    calls = []

    def fake_cli(module, argv):
        calls.append(module.rsplit(".", 1)[-1])
        out = argv[argv.index("--output") + 1] if "--output" in argv else None
        if out:
            Path(out).write_text(json.dumps({"patterns": [1, 2], "metrics": {"overall": 91}}))
        return 0

    monkeypatch.setattr(runner, "_run_cli_main", fake_cli)
    spec = {
        "cwd": str(root),
        "output_dir": str(root / "output"),
        "target": {"kind": "dir", "value": str(root)},
        "tools": ["patterns", "quality"],
        "depth": "basic",
        "min_confidence": 0.7,
        "ai_mode": "off",
        "attach_to": None,
    }
    assert runner.run_analyze(spec) == 0
    assert calls == ["pattern_recognizer", "quality_metrics"]
    manifests = analysis_store.list_recent(root)
    assert len(manifests) == 1 and set(manifests[0]["results"]) == {"patterns", "quality"}


def _analyze_spec(root, target, tools, kind="dir", **extra):
    """Spec shaped like the one routes/analyze.py submits."""
    return {
        "cwd": str(root),
        "output_dir": str(root / "output"),
        "configs_dir": str(root / "configs"),
        "target": {"kind": kind, "value": str(target)},
        "tools": tools,
        "depth": "basic",
        "min_confidence": 0.7,
        "ai_mode": "off",
        "attach_to": None,
        **extra,
    }


def test_run_analyze_resolves_patterns_output_directory(workspace, monkeypatch):
    """pattern_recognizer's --output is a DIRECTORY holding detected_patterns.json."""
    root, _ = workspace

    def fake_cli(_module, argv):
        out = Path(argv[argv.index("--output") + 1])
        out.mkdir(parents=True, exist_ok=True)
        (out / "detected_patterns.json").write_text(
            json.dumps(
                {
                    "total_files_analyzed": 3,
                    "files_with_patterns": 1,
                    "total_patterns_detected": 2,
                    "reports": [{"file_path": "x.py", "patterns": [1, 2]}],
                }
            )
        )
        return 0

    monkeypatch.setattr(runner, "_run_cli_main", fake_cli)
    assert runner.run_analyze(_analyze_spec(root, root, ["patterns"])) == 0
    manifest = analysis_store.list_recent(root)[0]
    assert manifest["results"]["patterns"]["count"] == 2
    assert manifest["results"]["patterns"]["path"].endswith("/patterns/detected_patterns.json")
    assert manifest["tools"] == ["patterns"] and manifest["skipped"] == []


def test_run_analyze_records_the_router_config_it_generated(workspace, monkeypatch):
    root, _ = workspace
    skill = _mk_skill(root / "output/hub")
    configs = root / "configs"
    configs.mkdir()
    (configs / "hub.json").write_text(
        json.dumps({"name": "hub", "sources": [{"name": "a"}, {"name": "b"}]})
    )
    for name in ("a", "b"):
        (configs / f"{name}.json").write_text(json.dumps({"name": name}))
    calls = []

    def fake_cli(module, argv):
        calls.append((module, argv))
        out_dir = Path(argv[argv.index("--output-dir") + 1])
        name = argv[argv.index("--name") + 1]
        # generate_router does not create --output-dir; the runner must have.
        assert out_dir.is_dir()
        (out_dir / f"{name}.json").write_text(
            json.dumps({"name": name, "_router": True, "_sub_skills": ["a", "b"]})
        )
        return 0

    monkeypatch.setattr(runner, "_run_cli_main", fake_cli)
    spec = _analyze_spec(root, skill, ["router"], kind="skill")
    assert runner.run_analyze(spec) == 0
    assert calls[0][0] == "skill_seekers.cli.generate_router"
    assert calls[0][1][:2] == [str(configs / "a.json"), str(configs / "b.json")]
    slug = analysis_store.slug_for(str(skill))
    manifest = analysis_store.list_recent(root)[0]
    assert manifest["results"]["router"] == {
        "count": 2,
        "path": str(root / "output/_analysis" / slug / "router" / f"{slug}.json"),
    }
    assert manifest["tools"] == ["router"] and manifest["skipped"] == []


def test_run_analyze_never_reports_a_previous_runs_files(workspace, monkeypatch):
    """A leftover tests.json must not let `guides` run, nor be counted as fresh."""
    root, _ = workspace
    target = root / "src"
    target.mkdir()
    stale = root / "output/_analysis" / analysis_store.slug_for(str(target))
    stale.mkdir(parents=True)
    (stale / "tests.json").write_text(json.dumps({"examples": [1, 2, 3]}))
    calls = []
    monkeypatch.setattr(runner, "_run_cli_main", lambda m, _a: calls.append(m) or 0)

    assert runner.run_analyze(_analyze_spec(root, target, ["guides"])) == 0
    assert calls == []
    manifest = analysis_store.list_recent(root)[0]
    assert "guides" not in manifest["results"]
    assert manifest["tools"] == [] and manifest["skipped"] == ["guides"]
    assert not (stale / "tests.json").exists()


def test_slug_for_separates_targets_sharing_a_basename():
    assert analysis_store.slug_for("/a/src") != analysis_store.slug_for("/b/src")
    assert analysis_store.slug_for("/a/src").startswith("src-")
