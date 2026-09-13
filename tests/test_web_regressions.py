"""Regression coverage for HUD data safety, runner outputs, and persistence."""
# ruff: noqa: F811 -- imported pytest fixture shares its injection parameter name

import sys
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.test_web_api import _mk_skill, workspace  # noqa: F401
from skill_seekers.web import registry, runner
from skill_seekers.web.installer import install_skill_to_cli
from skill_seekers.web.jobs import Job, JobManager, get_job_manager


def test_same_install_is_noop_and_replacement_is_explicit(workspace):
    root, _ = workspace
    source = root / "output/demo"
    dest = install_skill_to_cli(source, "claude")
    original = (dest / "SKILL.md").read_bytes()
    assert install_skill_to_cli(dest, "claude") == dest
    assert (dest / "SKILL.md").read_bytes() == original
    (source / "SKILL.md").write_text("changed")
    with pytest.raises(FileExistsError):
        install_skill_to_cli(source, "claude")
    assert (dest / "SKILL.md").read_bytes() == original
    install_skill_to_cli(source, "claude", replace=True)
    assert (dest / "SKILL.md").read_text() == "changed"


def test_failed_replacement_preserves_install(workspace, monkeypatch):
    import skill_seekers.web.installer as installer

    root, _ = workspace
    source = root / "output/demo"
    dest = install_skill_to_cli(source, "claude")
    before = (dest / "SKILL.md").read_bytes()

    def fail(*_args, **_kwargs):
        raise OSError("copy failed")

    monkeypatch.setattr(installer.shutil, "copytree", fail)
    with pytest.raises(OSError, match="copy failed"):
        install_skill_to_cli(source, "claude", replace=True)
    assert (dest / "SKILL.md").read_bytes() == before


def test_full_editor_content_and_revision_conflicts(workspace):
    root, client = workspace
    content = "# Large skill\n" + "🧭 content\n" * 40000
    path = root / "output/demo/SKILL.md"
    path.write_text(content)
    summary = client.get("/api/skills").json()[0]
    assert summary["contentTruncated"]
    full = client.get("/api/skills/demo/content").json()
    assert full["content"] == content
    assert client.put("/api/skills/demo/content", json={"content": "bad"}).status_code == 428
    path.write_text(content + "external edit")
    assert (
        client.put(
            "/api/skills/demo/content", json={"content": "bad", "revision": full["revision"]}
        ).status_code
        == 409
    )
    assert path.read_text().endswith("external edit")


def test_api_boundaries_and_archive_restore(workspace):
    root, client = workspace
    assert (
        client.get("/api/skills", headers={"Origin": "https://attacker.invalid"}).status_code == 403
    )
    assert (
        client.post(
            "/api/skills/delete", content='{"ids":["demo"]}', headers={"Content-Type": "text/plain"}
        ).status_code
        == 415
    )
    assert client.get("/api/health", headers={"Host": "attacker.invalid"}).status_code == 400
    for value in ["..", "../outside", str(root / "output/demo")]:
        assert client.post("/api/skills/delete", json={"ids": [value]}).status_code in (400, 404)
    outside = _mk_skill(root.parent / "outside")
    (root / "output/escape").symlink_to(outside, target_is_directory=True)
    assert "escape" not in {s["name"] for s in client.get("/api/skills").json()}
    assert client.post("/api/skills/delete", json={"ids": ["demo"]}).status_code == 200
    archived = client.get("/api/skills/archived").json()
    assert len(archived) == 1
    assert client.post(f"/api/skills/archived/{archived[0]['id']}/restore").status_code == 200
    assert (root / "output/demo/SKILL.md").exists()
    assert outside.exists()


def test_dist_symlink_cannot_serve_external_file(workspace, monkeypatch):
    import skill_seekers.web.app as app_module
    from fastapi.testclient import TestClient

    root, _ = workspace
    dist = root / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("SPA")
    private = root / "private.txt"
    private.write_text("PRIVATE DATA")
    (dist / "leak.txt").symlink_to(private)
    monkeypatch.setattr(app_module, "DIST_DIR", dist)
    client = TestClient(app_module.create_app(root), base_url="http://127.0.0.1")
    response = client.get("/leak.txt")
    assert "PRIVATE DATA" not in response.text
    assert client.get("/skills").text == "SPA"
    assert client.get("/api/unknown").status_code == 404


def test_unmatched_api_path_404s_for_every_method_when_dist_exists(workspace, monkeypatch):
    """A dist build makes the SPA route match any path — non-API routes must
    keep their normal 405 for a disallowed method, but an unmatched path
    under "api/" must 404 regardless of HTTP verb (see app.py's narrow
    "/api/{full_path:path}" catch-all, registered only when a dist exists)."""
    import skill_seekers.web.app as app_module
    from fastapi.testclient import TestClient

    root, _ = workspace
    dist = root / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("SPA")
    monkeypatch.setattr(app_module, "DIST_DIR", dist)
    client = TestClient(app_module.create_app(root), base_url="http://127.0.0.1")
    assert client.delete("/api/nope").status_code == 404
    assert client.post("/api/nope", json={}).status_code == 404
    assert client.get("/skills").text == "SPA"
    assert client.post("/some-route").status_code == 405


def test_identical_names_across_clis_have_distinct_ids(workspace):
    root, client = workspace
    _mk_skill(Path.home() / ".claude/skills/demo")
    _mk_skill(Path.home() / ".kimi/skills/demo")
    from skill_seekers.web.clis import invalidate_installed_cache

    invalidate_installed_cache()
    matches = [s for s in client.get("/api/skills").json() if s["name"] == "demo"]
    assert len(matches) == 3
    assert len({s["id"] for s in matches}) == 3
    assert client.get("/api/skills/demo/content").status_code == 404
    owned = next(s for s in matches if s["dir"] == str(root / "output/demo"))
    assert owned["installs"] == []
    assert client.get(f"/api/skills/{owned['id']}/content").status_code == 200


def test_concurrent_state_updates_preserve_all_records(workspace):
    root, _ = workspace

    def write(i):
        registry.log_activity("test", str(i))
        registry.set_skill_override(f"skill-{i}", scope="global")
        registry.add_project(str(root / str(i) / "same-name"))

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(write, range(30)))
    assert len(registry.list_projects()) == 30
    assert len({p["id"] for p in registry.list_projects()}) == 30
    from skill_seekers.web.paths import read_json

    assert len(read_json(registry.SKILLS_META_FILE, {})["skills"]) == 30
    assert len(registry.list_activity()) == 30


def test_job_history_keeps_newest_and_recovers_active(workspace):
    root, _ = workspace
    manager = get_job_manager()
    manager._jobs = [
        Job(str(i), "create", str(i), "", status="done", spec={"cwd": str(root)})
        for i in range(120)
    ]
    manager._jobs.append(
        Job("active", "scan", "scan", "", status="cancelling", spec={"cwd": str(root)})
    )
    manager._persist()
    loaded = JobManager()
    assert [j["id"] for j in loaded.list()][:100] == [str(i) for i in range(100)]
    assert loaded.get("active")["status"] == "failed"
    assert "spec" not in loaded.get("active")
    manager._jobs.clear()  # fixture teardown only waits for actual submitted jobs


@pytest.mark.parametrize("exit_code,expected", [(None, 0), (0, 0), (2, 2), ("error", 1)])
def test_runner_catches_cli_system_exit(monkeypatch, exit_code, expected):
    def main():
        raise SystemExit(exit_code)

    monkeypatch.setitem(sys.modules, "test_hud_cli", SimpleNamespace(main=main))
    previous = sys.argv
    assert runner._run_cli_main("test_hud_cli", []) == expected
    assert sys.argv is previous


def test_real_package_job_preserves_multiple_outputs(workspace):
    root, _ = workspace
    source = root / "output/demo"
    before = (source / "SKILL.md").read_bytes()
    manager = get_job_manager()
    job = manager.submit(
        "package",
        "demo",
        "two formats",
        {
            "type": "package",
            "skill_dir": str(source),
            "output_dir": str(root / "packages"),
            "cwd": str(root),
            "targets": ["claude", "markdown"],
        },
    )
    deadline = time.monotonic() + 30
    while job.status in ("running", "queued") and time.monotonic() < deadline:
        time.sleep(0.05)
    assert job.status == "done", job.log
    assert len(job.to_dict()["downloadableArtifacts"]) >= 2
    assert all(Path(p).exists() for p in job.artifacts)
    assert any("claude" in p for p in job.artifacts)
    assert any("markdown" in p for p in job.artifacts)
    assert (source / "SKILL.md").read_bytes() == before


def test_same_archive_filename_preserved_for_each_target(workspace, monkeypatch):
    root, _ = workspace

    def package(_module, argv):
        Path(argv[0]).with_suffix(".zip").write_text(argv[2])
        return 0

    monkeypatch.setattr(runner, "_run_cli_main", package)
    out = root / "packages"
    assert (
        runner.run_package(
            {
                "skill_dir": str(root / "output/demo"),
                "output_dir": str(out),
                "targets": ["claude", "openai"],
            }
        )
        == 0
    )
    assert (out / "claude/demo.zip").read_text() == "claude"
    assert (out / "openai/demo.zip").read_text() == "openai"


def test_capabilities_defaults_and_invalid_flags(workspace, monkeypatch):
    root, client = workspace
    from skill_seekers.cli.adaptors import list_platforms

    assert client.get("/api/capabilities").json()["targets"] == list_platforms()
    assert (
        client.put(
            "/api/settings/defaults", json={"settings": {"default_agent": "local"}}
        ).status_code
        == 400
    )
    assert (
        client.put(
            "/api/settings/defaults",
            json={
                "settings": {
                    "default_agent": "kimi",
                    "output_dir": "custom-out",
                    "configs_dir": "custom-cfg",
                }
            },
        ).status_code
        == 200
    )
    calls = []
    monkeypatch.setattr(
        get_job_manager(),
        "submit",
        lambda *args: calls.append(args[3]) or SimpleNamespace(to_dict=lambda: {"id": "fake"}),
    )
    request = {
        "entries": [{"type": "docs", "input": "https://example.invalid"}],
        "name": "demo",
        "targets": [],
    }
    for flags in [
        {"agent": "local"},
        {"workers": 0},
        {"rate_limit": "nan"},
        {"local_skips": ["--output=/tmp"]},
        {"fresh": True, "resume": True},
    ]:
        assert client.post("/api/create", json={**request, "flags": flags}).status_code == 400
    assert client.post("/api/create", json={**request, "targets": ["cursor"]}).status_code == 400
    assert client.post("/api/create", json=request).status_code == 200
    assert calls[-1]["output_dir"] == str(root / "custom-out")
    assert calls[-1]["configs_dir"] == str(root / "custom-cfg")
    assert calls[-1]["flags"]["agent"] == "kimi"


def test_failed_scan_marks_project_and_does_not_overwrite_fast_completion(workspace, monkeypatch):
    root, client = workspace
    manager = get_job_manager()

    def finish(*args):
        job = Job(
            "instant",
            "scan",
            "scan",
            "",
            status="failed",
            error="agent unavailable",
            spec=args[3],
            meta=args[4],
        )
        for hook in manager._hooks:
            hook(job)
        return job

    monkeypatch.setattr(manager, "submit", finish)
    response = client.post("/api/projects", json={"path": str(root)})
    assert response.status_code == 200
    assert response.json()["project"]["status"] == "failed"
    assert client.get("/api/projects").json()[0]["error"] == "agent unavailable"


def test_marketplace_browse_has_no_network_and_install_preflight(workspace, monkeypatch):
    from skill_seekers.web import market

    root, client = workspace
    monkeypatch.setattr(market, "sync_marketplace", lambda *_: pytest.fail("GET must not sync"))
    assert client.get("/api/marketplaces").status_code == 200
    source = _mk_skill(root / "cache/new-skill")
    installed = install_skill_to_cli(source, "claude")
    with pytest.raises(FileExistsError):
        market.install_marketplace_item(source, "skill", root, ["claude"])
    assert not (root / "output/new-skill").exists()
    assert (installed / "SKILL.md").exists()


def test_archive_preserves_same_name_in_other_cli(workspace):
    root, client = workspace
    source = root / "output/demo"
    installed = install_skill_to_cli(source, "claude")
    unrelated = _mk_skill(Path.home() / ".config/opencode/skills/demo")
    from skill_seekers.web.clis import invalidate_installed_cache

    invalidate_installed_cache()
    skill_id = registry.skill_id_for(source)
    assert client.post("/api/skills/delete", json={"ids": [skill_id]}).status_code == 200
    assert not installed.exists()
    assert (unrelated / "SKILL.md").exists()


@pytest.mark.parametrize(
    "cli,directory",
    [
        ("codex", ".agents/skills"),
        ("cursor", ".cursor/skills"),
        ("windsurf", ".codeium/windsurf/skills"),
        ("opencode", ".config/opencode/skills"),
    ],
)
def test_native_install_preserves_supporting_files(workspace, cli, directory):
    root, _ = workspace
    source = root / "output/demo"
    dest = install_skill_to_cli(source, cli)
    assert dest == Path.home() / directory / "demo"
    assert (dest / "references/api.md").read_bytes() == (source / "references/api.md").read_bytes()


def test_job_cancel_and_retry_real_process_group(workspace, monkeypatch):
    import skill_seekers.web.jobs as jobs_module

    root, _ = workspace
    original_popen = jobs_module.subprocess.Popen

    def sleeping_worker(_argv, **kwargs):
        script = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); print('ready',flush=True); time.sleep(30)"
        return original_popen([sys.executable, "-c", script], **kwargs)

    monkeypatch.setattr(jobs_module.subprocess, "Popen", sleeping_worker)
    manager = get_job_manager()
    job = manager.submit("create", "cancel fixture", "", {"type": "create", "cwd": str(root)})
    deadline = time.monotonic() + 5
    while "ready" not in job.log and time.monotonic() < deadline:
        time.sleep(0.02)
    assert job.status == "running"
    from skill_seekers.web.paths import read_json

    assert read_json(jobs_module.JOBS_FILE, [])[0]["status"] == "running"
    assert manager.cancel(job.id)
    while job.status == "cancelling" and time.monotonic() < deadline:
        time.sleep(0.02)
    assert job.status == "cancelled"
    retried = manager.retry(job.id)
    assert retried.id != job.id
    assert manager.cancel(retried.id)
    manager.shutdown(root)


def test_subprocess_state_transactions_preserve_updates(workspace):
    import os
    import subprocess

    root, _ = workspace
    env = os.environ.copy()
    import skill_seekers

    env["PYTHONPATH"] = str(Path(skill_seekers.__file__).resolve().parents[1])
    script = "from skill_seekers.web.registry import set_skill_override; import sys; [set_skill_override(sys.argv[1]+str(i),scope='global') for i in range(10)]"
    processes = [
        subprocess.Popen([sys.executable, "-c", script, prefix], cwd=root, env=env)
        for prefix in ("a", "b", "c")
    ]
    assert all(process.wait(timeout=10) == 0 for process in processes)
    from skill_seekers.web.paths import read_json

    assert len(read_json(registry.SKILLS_META_FILE, {})["skills"]) == 30


def test_fetched_config_cache_is_indexed(workspace, monkeypatch):
    import skill_seekers.web.app as app_module
    from skill_seekers.services.source_manager import SourceManager
    from skill_seekers.services.git_repo import GitConfigRepo

    _, client = workspace
    monkeypatch.setattr(app_module, "fetch_official_configs", lambda: ([], False))
    manager = SourceManager()
    manager.add_source("team", "https://github.com/example/configs.git")
    config_dir = GitConfigRepo().cache_dir / "team"
    config_dir.mkdir(parents=True)
    (config_dir / "recipe.json").write_text(
        json.dumps(
            {
                "name": "recipe",
                "sources": [{"type": "documentation", "base_url": "https://example.invalid"}],
            }
        )
    )
    data = client.get("/api/library").json()
    assert any(
        entry["source"] == "team" and entry["name"] == "recipe.json" for entry in data["entries"]
    )
    assert next(source for source in data["sources"] if source["id"] == "team")["configs"] == 1


def test_github_key_survives_environment_clear(workspace, monkeypatch, tmp_path):
    from skill_seekers.cli.config_manager import ConfigManager

    _, client = workspace
    config = tmp_path / "credentials"
    monkeypatch.setattr(ConfigManager, "CONFIG_DIR", config)
    monkeypatch.setattr(ConfigManager, "CONFIG_FILE", config / "config.json")
    monkeypatch.setattr(ConfigManager, "PROGRESS_DIR", config / "progress")
    monkeypatch.setenv("GITHUB_TOKEN", "")
    assert (
        client.put(
            "/api/settings/keys",
            json={"name": "GITHUB_TOKEN", "value": "fixture-token-not-a-secret"},
        ).status_code
        == 200
    )
    monkeypatch.delenv("GITHUB_TOKEN")
    assert ConfigManager().get_github_token() == "fixture-token-not-a-secret"


def test_ipv6_loopback_origin_and_nonlocal_binding(workspace):
    from argparse import Namespace
    from skill_seekers.cli.ui_command import UiCommand

    root, client = workspace
    assert (
        client.get(
            "/api/health", headers={"Host": "[::1]:8770", "Origin": "http://[::1]:8770"}
        ).status_code
        == 200
    )
    assert (
        UiCommand(
            Namespace(
                host="0.0.0.0", root=str(root), port=8770, no_browser=True, log_level="warning"
            )
        ).execute()
        == 1
    )


def test_create_sidecar_and_configured_output_survive_packaging(workspace, monkeypatch):
    root, _ = workspace
    output = root / "custom-output"

    def create(_module, argv):
        assert argv[argv.index("--output") + 1] == str(output / "built")
        _mk_skill(output / "built")
        return 0

    packaged = []
    monkeypatch.setattr(runner, "_run_cli_main", create)
    monkeypatch.setattr(runner, "run_package", lambda spec: packaged.append(spec) or 0)
    assert (
        runner.run_create(
            {
                "entries": [{"type": "docs", "input": "https://example.invalid"}],
                "cwd": str(root),
                "output_dir": str(output),
                "name": "built",
                "targets": ["claude", "markdown"],
            }
        )
        == 0
    )
    assert (output / "built/.seeker-meta.json").exists()
    assert packaged[0]["targets"] == ["claude", "markdown"]
    assert packaged[0]["output_dir"] == str(output / "_packages")


def test_fetched_official_config_stays_under_official_filter(workspace, monkeypatch):
    import httpx
    import skill_seekers.web.app as app_module

    _, client = workspace
    monkeypatch.setattr(app_module, "fetch_official_configs", lambda: ([{"name": "recipe"}], True))
    config = {
        "name": "recipe",
        "sources": [{"type": "documentation", "base_url": "https://example.invalid"}],
    }
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *_args, **_kwargs: SimpleNamespace(
            raise_for_status=lambda: None, json=lambda: config
        ),
    )
    assert client.post("/api/library/official/fetch", json={"name": "recipe"}).status_code == 200
    entries = client.get("/api/library").json()["entries"]
    recipes = [e for e in entries if e["name"] == "recipe.json"]
    assert len(recipes) == 1
    assert recipes[0]["source"] == "official"
    assert recipes[0]["fetched"] is True


def test_opencode_flat_skill_is_in_inventory(workspace):
    _, client = workspace
    path = Path.home() / ".config/opencode/skills/review.md"
    path.parent.mkdir(parents=True)
    path.write_text("---\nname: review\ndescription: test\n---\n# Review")
    from skill_seekers.web.clis import invalidate_installed_cache

    invalidate_installed_cache()
    entries = client.get("/api/skills").json()
    skill = next(s for s in entries if s["name"] == "review")
    assert skill["installs"] == ["opencode"]
    assert client.get(f"/api/skills/{skill['id']}/content").json()["content"].endswith("# Review")
