"""Regression tests for the HUD review findings (lock order, inventory, history, packaging)."""
# ruff: noqa: F811 -- imported pytest fixture shares its injection parameter name

import io
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.test_web_api import _mk_skill, workspace  # noqa: F401
from skill_seekers.web import runner
from skill_seekers.web.clis import invalidate_installed_cache
from skill_seekers.web.installer import install_skill_to_cli
from skill_seekers.web.jobs import Job, JobManager, get_job_manager


def test_state_lock_and_job_lock_are_never_nested_in_opposite_orders(workspace, monkeypatch):
    """save_skill_content must not call jobs.list inside a state transaction, and
    _persist must not write state while holding the job lock (ABBA deadlock)."""
    import skill_seekers.web.jobs as jobs_module
    import skill_seekers.web.paths as paths

    root, client = workspace
    manager = get_job_manager()
    violations: list[str] = []
    original_list = manager.list

    def guarded_list(*args, **kwargs):
        if getattr(paths._transaction, "active", False):
            violations.append("jobs.list called inside state_transaction")
        return original_list(*args, **kwargs)

    original_write = jobs_module.write_json

    def guarded_write(*args, **kwargs):
        if manager._lock._is_owned():
            violations.append("write_json called while holding the job lock")
        return original_write(*args, **kwargs)

    monkeypatch.setattr(manager, "list", guarded_list)
    monkeypatch.setattr(jobs_module, "write_json", guarded_write)
    revision = client.get("/api/skills/demo/content").json()["revision"]
    response = client.put(
        "/api/skills/demo/content", json={"content": "# edited\n", "revision": revision}
    )
    assert response.status_code == 200
    manager._jobs.append(Job("h", "package", "demo", "", status="done", spec={"cwd": str(root)}))
    try:
        manager._persist()
    finally:
        manager._jobs.clear()  # fixture teardown only waits for jobs it saw finish
    assert violations == []


def test_installed_copy_of_workspace_skill_is_not_a_second_entry(workspace):
    root, client = workspace
    install_skill_to_cli(root / "output/demo", "claude")
    invalidate_installed_cache()
    demo = [s for s in client.get("/api/skills").json() if s["name"] == "demo"]
    assert [s["dir"] for s in demo] == [str(root / "output/demo")]
    assert "claude" in demo[0]["installs"]


def test_legacy_history_rows_without_spec_stay_visible(workspace):
    import skill_seekers.web.jobs as jobs_module
    from skill_seekers.web.paths import write_json

    root, _ = workspace
    write_json(
        jobs_module.JOBS_FILE,
        [
            {
                "id": "old",
                "type": "create",
                "label": "legacy",
                "detail": "",
                "status": "done",
                "progress": 100.0,
                "log": [],
                "meta": {},
            }
        ],
    )
    loaded = JobManager()
    assert [j["id"] for j in loaded.list(root)] == ["old"]


def test_unified_config_has_stable_name_across_runs(workspace, monkeypatch):
    root, _ = workspace

    def create(_module, argv):
        _mk_skill(Path(argv[argv.index("--output") + 1]))
        return 0

    monkeypatch.setattr(runner, "_run_cli_main", create)
    spec = {
        "entries": [
            {"type": "docs", "input": "https://a.invalid"},
            {"type": "docs", "input": "https://b.invalid"},
        ],
        "cwd": str(root),
        "output_dir": str(root / "output"),
        "configs_dir": str(root / "configs"),
        "name": "multi",
        "targets": [],
    }
    assert runner.run_create(spec) == 0
    assert runner.run_create(spec) == 0
    assert [p.name for p in (root / "configs").glob("*.json")] == ["multi-unified.json"]


def test_github_key_from_hud_keeps_existing_default_profile(workspace, monkeypatch, tmp_path):
    from skill_seekers.cli.config_manager import ConfigManager

    _, client = workspace
    config = tmp_path / "credentials"
    monkeypatch.setattr(ConfigManager, "CONFIG_DIR", config)
    monkeypatch.setattr(ConfigManager, "CONFIG_FILE", config / "config.json")
    monkeypatch.setattr(ConfigManager, "PROGRESS_DIR", config / "progress")
    ConfigManager().add_github_profile("work", "ghp_work_fixture_not_a_secret", set_as_default=True)
    monkeypatch.setenv("GITHUB_TOKEN", "")
    response = client.put(
        "/api/settings/keys", json={"name": "GITHUB_TOKEN", "value": "ghp_hud_fixture_not_a_secret"}
    )
    assert response.status_code == 200
    manager = ConfigManager()
    assert manager.config["github"]["default_profile"] == "work"
    assert manager.config["github"]["profiles"]["seeker-ui"]["token"] == (
        "ghp_hud_fixture_not_a_secret"
    )


@pytest.mark.usefixtures("workspace")
def test_marketplace_status_is_tracked_per_repository():
    from skill_seekers.web import market
    from skill_seekers.web.paths import write_json

    first = "https://github.com/owner/repo"
    second = "https://github.com/other/skills.git"
    market.MARKET_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    assert market.status_path(first) != market.status_path(second)
    write_json(market.status_path(first), {"connected": True, "lastSync": "earlier"})
    assert market.cache_status(first)["lastSync"] == "earlier"
    assert market.cache_status(second) == {"connected": False, "lastSync": "never"}


def test_port_to_undetected_cli_is_rejected(workspace):
    _, client = workspace
    response = client.post("/api/skills/port", json={"ids": ["demo"], "cli": "windsurf"})
    assert response.status_code == 400
    assert "not detected" in response.json()["detail"]


def test_single_target_package_uses_target_directory(workspace, monkeypatch):
    root, _ = workspace

    def package(_module, argv):
        Path(argv[0]).with_suffix(".zip").write_text(argv[2])
        return 0

    monkeypatch.setattr(runner, "_run_cli_main", package)
    out = root / "packages"
    spec = {"skill_dir": str(root / "output/demo"), "output_dir": str(out), "targets": ["claude"]}
    assert runner.run_package(spec) == 0
    assert (out / "claude/demo.zip").read_text() == "claude"


def test_multi_target_package_progress_advances_per_target(workspace, monkeypatch, capsys):
    root, _ = workspace

    def package(_module, argv):
        Path(argv[0]).with_suffix(".zip").write_text("x")
        return 0

    monkeypatch.setattr(runner, "_run_cli_main", package)
    spec = {
        "skill_dir": str(root / "output/demo"),
        "output_dir": str(root / "packages"),
        "targets": ["claude", "openai", "markdown"],
    }
    assert runner.run_package(spec) == 0
    pcts = [
        int(m) for m in re.findall(r"\[\[PROGRESS:(\d+)\]\] packaging", capsys.readouterr().out)
    ]
    assert len(pcts) == 3
    assert pcts == sorted(pcts) and len(set(pcts)) == 3


def test_test_client_hostname_is_not_trusted_in_production(workspace):
    _, client = workspace
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/health", headers={"Host": "testserver"}).status_code == 400


def test_sync_all_skips_marketplaces_with_cancelling_jobs(workspace, monkeypatch):
    from skill_seekers.services.marketplace_manager import MarketplaceManager

    root, client = workspace
    MarketplaceManager().add_marketplace(name="shop", git_url="https://example.invalid/shop.git")
    manager = get_job_manager()
    manager._jobs.append(
        Job("c", "market-sync", "shop", "", status="cancelling", spec={"cwd": str(root)})
    )

    def refuse(*_args, **_kwargs):
        pytest.fail("must not resubmit")

    monkeypatch.setattr(manager, "submit", refuse)
    try:
        assert client.post("/api/marketplaces/sync").json()["jobs"] == []
    finally:
        manager._jobs.clear()


def test_pump_survives_state_persist_failure(workspace, monkeypatch):
    import skill_seekers.web.jobs as jobs_module

    root, _ = workspace
    manager = get_job_manager()
    job = Job("p", "package", "demo", "", status="running", spec={"cwd": str(root)})
    manager._jobs.append(job)
    seen: list[Job] = []
    manager.register_hook(seen.append)

    def fail(*_args, **_kwargs):
        raise OSError("lock timeout")

    monkeypatch.setattr(jobs_module, "write_json", fail)
    proc = SimpleNamespace(stdout=io.StringIO(""), wait=lambda: 0)
    manager._pump("p", proc, root / "spec.json")
    assert job.status == "done"
    assert seen and seen[-1] is job
