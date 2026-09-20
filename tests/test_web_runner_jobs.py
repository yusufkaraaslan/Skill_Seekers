"""Runner job types added for the skill/config/analyze/environment pages."""
# ruff: noqa: F811

import json
import os
from pathlib import Path

import pytest

from tests.test_web_api import _mk_skill, workspace  # noqa: F401
from skill_seekers.cli import estimate_pages as estimate_pages_mod
from skill_seekers.web import analysis_store, runner


def test_run_upload_packages_then_uploads(workspace, monkeypatch):
    """The vector/RAG adaptors write <name>-<target>.json, never an archive."""
    root, _ = workspace
    calls = []

    def fake_cli(module, argv):
        calls.append((module, argv))
        if module.endswith("package_skill"):
            staged = Path(argv[0])
            staged.with_name(f"{staged.name}-chroma.json").write_text("{}")
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
    assert upload[1][0].endswith("chroma/demo-chroma.json")
    assert upload[1][1:5] == ["--target", "chroma", "--persist-directory", "./chroma_db"]


def test_run_upload_fails_cleanly_when_packaging_wrote_nothing(workspace, monkeypatch):
    """No target directory at all must raise the same RuntimeError, not an OSError."""
    root, _ = workspace
    monkeypatch.setattr(runner, "run_package", lambda _spec: 0)
    spec = {
        "skill_dir": str(root / "output/demo"),
        "output_dir": str(root / "output/_packages"),
        "target": "chroma",
        "options": {},
        "cwd": str(root),
    }
    with pytest.raises(RuntimeError, match="produced no output"):
        runner.run_upload(spec)


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
    # Cleanup is per tool now, so a sibling tool's file survives this run — but
    # it is still neither an input for `guides` nor a result of this run.
    assert (stale / "tests.json").exists()


def _patterns_cli(_module, argv):
    """Stand-in for pattern_recognizer: --output is a directory."""
    out = Path(argv[argv.index("--output") + 1])
    out.mkdir(parents=True, exist_ok=True)
    (out / "detected_patterns.json").write_text(json.dumps({"total_patterns_detected": 5}))
    return 0


def test_run_analyze_merges_results_across_per_tool_runs(workspace, monkeypatch):
    """Re-running one tool must not erase the sibling results already recorded."""
    root, _ = workspace

    def fake_cli(module, argv):
        if module.endswith("pattern_recognizer"):
            return _patterns_cli(module, argv)
        Path(argv[argv.index("--output") + 1]).write_text(json.dumps({"metrics": {"overall": 88}}))
        return 0

    monkeypatch.setattr(runner, "_run_cli_main", fake_cli)
    assert runner.run_analyze(_analyze_spec(root, root, ["patterns"])) == 0
    assert runner.run_analyze(_analyze_spec(root, root, ["quality"])) == 0
    manifest = analysis_store.list_recent(root)[0]
    assert set(manifest["results"]) == {"patterns", "quality"}
    assert manifest["results"]["patterns"]["count"] == 5
    assert manifest["results"]["quality"]["count"] == 88
    assert sorted(manifest["tools"]) == ["patterns", "quality"]
    assert "error" not in manifest


def test_run_analyze_records_a_failing_tool_and_keeps_prior_results(workspace, monkeypatch):
    """A tool that exits non-zero must still leave a manifest behind."""
    root, _ = workspace
    monkeypatch.setattr(runner, "_run_cli_main", _patterns_cli)
    assert runner.run_analyze(_analyze_spec(root, root, ["patterns"])) == 0

    monkeypatch.setattr(runner, "_run_cli_main", lambda _m, _a: 3)
    assert runner.run_analyze(_analyze_spec(root, root, ["quality"])) == 3
    manifest = analysis_store.list_recent(root)[0]
    assert manifest["error"] == "quality exited 3"
    assert manifest["results"]["patterns"]["count"] == 5
    assert "quality" not in manifest["results"]
    assert manifest["tools"] == ["patterns"]


def test_slug_for_separates_targets_sharing_a_basename():
    assert analysis_store.slug_for("/a/src") != analysis_store.slug_for("/b/src")
    assert analysis_store.slug_for("/a/src").startswith("src-")


def test_run_estimate_writes_result_and_emits_artifact(workspace, monkeypatch, capsys):
    root, _ = workspace
    config_path = root / "configs" / "react.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "name": "react",
                "description": "d",
                "sources": [{"type": "documentation", "base_url": "https://example.invalid/docs"}],
            }
        )
    )
    seen = {}

    def fake_estimate_pages(_config, max_discovery, timeout):
        seen["max_discovery"] = max_discovery
        seen["timeout"] = timeout
        return {"discovered": 3, "estimated_total": 12, "hit_limit": False}

    # run_estimate does `from skill_seekers.cli.estimate_pages import estimate_pages`
    # inside the function body, so it re-reads the module attribute on every
    # call — patching the module attribute (not `runner.estimate_pages`, which
    # doesn't exist) is what actually takes effect.
    monkeypatch.setattr(estimate_pages_mod, "estimate_pages", fake_estimate_pages)
    result_path = config_path.with_name(".react.json.estimate.json")
    spec = {
        "config_path": str(config_path),
        "max_discovery": 50,
        "timeout": 7,
        "result_path": str(result_path),
    }

    assert runner.run_estimate(spec) == 0
    assert seen == {"max_discovery": 50, "timeout": 7}
    assert result_path.is_file()
    assert json.loads(result_path.read_text())["estimated_total"] == 12
    out = capsys.readouterr().out
    assert "[[ARTIFACT]]" in out
    assert str(result_path.resolve()) in out


def test_run_estimate_fails_cleanly_without_documentation_source(workspace):
    root, _ = workspace
    config_path = root / "configs" / "gh.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {"name": "gh", "description": "d", "sources": [{"type": "github", "repo": "o/r"}]}
        )
    )
    result_path = config_path.with_name(".gh.json.estimate.json")
    spec = {
        "config_path": str(config_path),
        "max_discovery": 50,
        "timeout": 7,
        "result_path": str(result_path),
    }

    assert runner.run_estimate(spec) == 1
    assert not result_path.is_file()


def test_run_split_and_generate_config_argv(workspace, monkeypatch):
    root, _ = workspace
    calls = []
    monkeypatch.setattr(runner, "_run_cli_main", lambda m, a: calls.append((m, a)) or 0)
    cfg = root / "configs/react.json"
    cfg.parent.mkdir(exist_ok=True)
    cfg.write_text('{"name":"react","sources":[]}')
    assert (
        runner.run_split(
            {
                "config_path": str(cfg),
                "strategy": "category",
                "target_pages": 500,
                "output_dir": str(root / "configs"),
            }
        )
        == 0
    )
    assert calls[0] == (
        "skill_seekers.cli.split_config",
        [
            str(cfg),
            "--strategy",
            "category",
            "--target-pages",
            "500",
            "--output-dir",
            str(root / "configs"),
        ],
    )

    import skill_seekers.web.runner as r

    monkeypatch.setattr(
        r,
        "_generate_with_ai",
        lambda _detection, _probe: {
            "name": "svelte",
            "sources": [{"type": "documentation", "base_url": "https://svelte.dev/docs"}],
        },
    )
    assert (
        runner.run_generate_config(
            {
                "kind": "name",
                "value": "Svelte",
                "probe_urls": False,
                "configs_dir": str(root / "configs"),
            }
        )
        == 0
    )
    assert (root / "configs/svelte.json").is_file()


def test_run_sync_check_round_trips_a_syncstate_file(workspace, monkeypatch):
    """The report doubles as sync.monitor's SyncState store, so it must stay
    loadable by SyncState while carrying the flat ``changes`` list the config
    page renders."""
    from skill_seekers.sync import detector as detector_mod
    from skill_seekers.sync.models import ChangeReport, ChangeType, PageChange, SyncState

    root, _ = workspace
    cfg = root / "configs" / "react.json"
    cfg.parent.mkdir(exist_ok=True)
    cfg.write_text(
        json.dumps(
            {
                "name": "react",
                "sources": [
                    {"type": "documentation", "base_url": "https://react.invalid/docs"},
                    {"type": "github", "repo": "facebook/react"},
                ],
            }
        )
    )
    state = root / "sync" / "react_sync.json"
    seen = []

    class FakeDetector:
        def check_pages(self, urls, previous_hashes, generate_diffs=False):
            seen.append((list(urls), dict(previous_hashes)))
            return ChangeReport(
                skill_name="unknown",
                total_pages=len(urls),
                modified=[
                    PageChange(
                        url=urls[0],
                        change_type=ChangeType.MODIFIED,
                        old_hash="a",
                        new_hash="b",
                    )
                ],
            )

    monkeypatch.setattr(detector_mod, "ChangeDetector", FakeDetector)
    spec = {"config_path": str(cfg), "state_path": str(state)}
    assert runner.run_sync_check(spec) == 0
    payload = json.loads(state.read_text())
    # Only documentation sources are watched; the github source is skipped.
    assert seen[0] == (["https://react.invalid/docs"], {})
    assert payload["page_hashes"] == {"https://react.invalid/docs": "b"}
    assert [c["change_type"] for c in payload["changes"]] == ["modified"]
    assert payload["checkedAt"] == payload["last_check"]
    assert SyncState(**payload).total_checks == 1

    # Second run resumes from the stored hashes and accumulates the counters.
    assert runner.run_sync_check(spec) == 0
    assert seen[1][1] == {"https://react.invalid/docs": "b"}
    assert json.loads(state.read_text())["total_checks"] == 2


def test_run_sync_check_without_a_documentation_url_fails(workspace):
    root, _ = workspace
    cfg = root / "configs" / "cli.json"
    cfg.parent.mkdir(exist_ok=True)
    cfg.write_text(json.dumps({"name": "cli", "sources": [{"type": "manpage", "path": "ls"}]}))
    assert runner.run_sync_check({"config_path": str(cfg), "state_path": str(root / "s.json")}) == 1


def test_run_push_and_submit_map_service_results_to_exit_codes(workspace, monkeypatch):
    from skill_seekers.cli import scan_command as scan_mod
    from skill_seekers.services import config_publisher as publisher_mod
    from skill_seekers.services import source_manager as source_mod

    root, _ = workspace
    cfg = root / "configs" / "react.json"
    cfg.parent.mkdir(exist_ok=True)
    cfg.write_text(json.dumps({"name": "react", "sources": []}))
    published = []

    class FakePublisher:
        def publish(
            self, config_path, source_name, category="auto", create_branch=False, force=False
        ):
            published.append((config_path, source_name, category, create_branch, force))
            return {"success": True, "commit_sha": "abc1234"}

    monkeypatch.setattr(publisher_mod, "ConfigPublisher", FakePublisher)
    spec = {"config_path": str(cfg), "source": "team", "message": "note", "branch": True}
    assert runner.run_push(spec) == 0
    assert published == [(str(cfg), "team", "auto", True, False)]

    # submit_config answers {"ok": ..., "message": ...} — not {"success": ...}
    monkeypatch.setattr(source_mod, "submit_config", lambda _path: {"ok": False, "message": "no"})
    assert runner.run_submit({"config_path": str(cfg)}) == 1
    monkeypatch.setattr(source_mod, "submit_config", lambda _path: {"ok": True, "message": "filed"})
    assert runner.run_submit({"config_path": str(cfg)}) == 0

    def _never(_path):
        raise AssertionError("a config with dead URLs must not be submitted")

    monkeypatch.setattr(scan_mod, "_probe_urls", lambda _config: ["https://react.invalid/docs"])
    monkeypatch.setattr(source_mod, "submit_config", _never)
    assert runner.run_submit({"config_path": str(cfg), "probe_urls": True}) == 1


def test_run_sync_check_reports_unreachable_pages(workspace, monkeypatch, capsys):
    """check_pages files a swallowed RequestException into no bucket at all, so
    an unreachable docs site must not read as a clean "0 change(s)" run."""
    from skill_seekers.sync import detector as detector_mod
    from skill_seekers.sync.models import ChangeReport, ChangeType, PageChange

    root, _ = workspace
    cfg = root / "configs" / "react.json"
    cfg.parent.mkdir(exist_ok=True)
    cfg.write_text(
        json.dumps(
            {
                "name": "react",
                "sources": [
                    {
                        "type": "documentation",
                        "base_url": "https://react.invalid/docs",
                        "start_urls": ["https://react.invalid/a", "https://react.invalid/b"],
                    }
                ],
            }
        )
    )
    state = root / "sync" / "react_sync.json"

    class FakeDetector:
        def check_pages(self, urls, previous_hashes, generate_diffs=False):
            # Two pages asked for, only one classified — the other was dropped.
            return ChangeReport(
                skill_name="unknown",
                total_pages=len(urls),
                modified=[
                    PageChange(
                        url=urls[0], change_type=ChangeType.MODIFIED, old_hash="a", new_hash="b"
                    )
                ],
                unchanged=0,
            )

    monkeypatch.setattr(detector_mod, "ChangeDetector", FakeDetector)
    assert runner.run_sync_check({"config_path": str(cfg), "state_path": str(state)}) == 1
    assert "1 page(s) unreachable" in capsys.readouterr().out
    payload = json.loads(state.read_text())
    assert payload["status"] == "error" and payload["error"] == "1 page(s) unreachable"
    # The page that was reached keeps its hash for the next run.
    assert payload["page_hashes"] == {"https://react.invalid/a": "b"}


def test_run_install_agent_argv(workspace, monkeypatch):
    root, _ = workspace
    calls = []
    monkeypatch.setattr(runner, "_run_cli_main", lambda m, a: calls.append((m, a)) or 0)
    assert (
        runner.run_install_agent(
            {"agent": "codex", "skill_dir": str(root / "output/skill-seekers"), "force": True}
        )
        == 0
    )
    assert calls == [
        (
            "skill_seekers.cli.install_agent",
            [str(root / "output/skill-seekers"), "--agent", "codex", "--force"],
        )
    ]
