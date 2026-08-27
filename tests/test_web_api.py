"""Tests for the Seeker HUD web API (skill_seekers.web)."""

import json
import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from skill_seekers.web import registry
from skill_seekers.web.app import create_app
from skill_seekers.web.installer import (
    flatten_skill,
    install_skill_to_cli,
    uninstall_skill_from_cli,
)


def _mk_skill(dir_: Path, name: str | None = None) -> Path:
    """Create a minimal skill directory with a SKILL.md and return it."""
    dir_.mkdir(parents=True, exist_ok=True)
    (dir_ / "SKILL.md").write_text(
        f"---\nname: {name or dir_.name}\ndescription: fixture\n---\n\n# {name or dir_.name}\n",
        encoding="utf-8",
    )
    return dir_


@pytest.fixture()
def workspace(tmp_path, monkeypatch):
    """Isolated workspace root + UI state dir."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    state = tmp_path / "ui-state"
    monkeypatch.setenv("SKILL_SEEKERS_UI_DIR", str(state))
    # paths module reads the env var at import time — patch the module constants
    import skill_seekers.web.paths as paths

    monkeypatch.setattr(paths, "UI_STATE_DIR", state)
    for name, fname in (
        ("PROJECTS_FILE", "projects.json"),
        ("JOBS_FILE", "jobs.json"),
        ("ACTIVITY_FILE", "activity.json"),
        ("SKILLS_META_FILE", "skills.json"),
        ("SETTINGS_FILE", "settings.json"),
    ):
        monkeypatch.setattr(paths, name, state / fname)
    monkeypatch.setattr(paths, "TRASH_DIR", state / "trash")
    monkeypatch.setattr(paths, "MARKET_CACHE_DIR", state / "marketplace_cache")

    # registry imported the path constants — rebind there too
    for name in ("PROJECTS_FILE", "ACTIVITY_FILE", "SKILLS_META_FILE", "TRASH_DIR"):
        monkeypatch.setattr(registry, name, getattr(paths, name))

    from skill_seekers.web.clis import invalidate_installed_cache

    invalidate_installed_cache()
    root = tmp_path / "ws"
    (root / "output" / "demo").mkdir(parents=True)
    (root / "output" / "demo" / "references").mkdir()
    (root / "output" / "demo" / "SKILL.md").write_text(
        "---\nname: demo\ndescription: fixture skill\n---\n\n# demo\n\nbody\n", encoding="utf-8"
    )
    (root / "output" / "demo" / "references" / "api.md").write_text("# api\n", encoding="utf-8")
    app = create_app(root)
    return root, TestClient(app)


def test_health(workspace):
    root, client = workspace
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert r.json()["root"] == str(root)


def test_overview_and_skills(workspace):
    _, client = workspace
    ov = client.get("/api/overview").json()
    assert {"skills", "jobs", "clis", "projects", "activity", "mcpToolCount"} <= set(ov)
    assert ov["mcpToolCount"] == 40
    skills = client.get("/api/skills").json()
    assert len(skills) == 1
    s = skills[0]
    assert s["name"] == "demo"
    assert s["description"] == "fixture skill"
    assert s["scope"] == "global"
    assert 0 <= s["quality"] <= 100
    assert any(f["path"] == "references/api.md" for f in s["files"])
    assert s["content"].startswith("---")


def test_skill_move_and_delete(workspace):
    _, client = workspace
    r = client.post("/api/skills/move", json={"ids": ["demo"], "dest": "pj-x"})
    assert r.json()["ok"] is True
    assert client.get("/api/skills").json()[0]["scope"] == "project"
    assert client.get("/api/skills").json()[0]["projectId"] == "pj-x"

    r = client.post("/api/skills/delete", json={"ids": ["demo"]})
    assert r.json()["ok"] is True
    assert client.get("/api/skills").json() == []


def test_skill_content_roundtrip(workspace):
    _, client = workspace
    new = "---\nname: demo\ndescription: edited\n---\n\n# edited\n"
    r = client.put("/api/skills/demo/content", json={"content": new})
    assert r.json()["ok"] is True
    assert client.get("/api/skills").json()[0]["content"] == new


def test_create_validation(workspace):
    _, client = workspace
    r = client.post("/api/create", json={"entries": [], "name": "x", "targets": []})
    assert r.status_code == 400
    r = client.post(
        "/api/create",
        json={
            "entries": [{"type": "docs", "input": "https://example.com"}],
            "name": "!!",
            "targets": [],
        },
    )
    # name sanitizes to empty -> 400, or accepted with derived name — never 500
    assert r.status_code in (200, 400)


def test_projects_crud(workspace):
    root, client = workspace
    proj_dir = root / "myproj"
    proj_dir.mkdir()
    r = client.post("/api/projects", json={"path": str(proj_dir)})
    assert r.status_code == 200
    project = r.json()["project"]
    assert project["name"] == "myproj"
    # a scan job was spawned
    assert client.get("/api/jobs").json()
    projects = client.get("/api/projects").json()
    assert len(projects) == 1
    r = client.delete(f"/api/projects/{project['id']}")
    assert r.json()["ok"] is True
    assert client.get("/api/projects").json() == []


def test_project_rejects_bad_path(workspace):
    _, client = workspace
    r = client.post("/api/projects", json={"path": "/nonexistent/xyz-123"})
    assert r.status_code == 400


def test_library_and_workflows(workspace):
    root, client = workspace
    cfg_dir = root / "configs"
    cfg_dir.mkdir(exist_ok=True)
    (cfg_dir / "react.json").write_text(
        json.dumps(
            {
                "name": "react",
                "description": "d",
                "sources": [{"type": "documentation", "base_url": "https://react.dev"}],
            }
        ),
        encoding="utf-8",
    )
    lib = client.get("/api/library").json()
    # sources[0] is the built-in official registry; user sources follow
    assert lib["sources"][0]["id"] == "official"
    assert len(lib["sources"]) == 1
    names = [e["name"] for e in lib["entries"]]
    assert "react.json" in names
    assert any(w["id"] for w in lib["workflows"])


def test_library_build_missing_config(workspace):
    _, client = workspace
    r = client.post("/api/library/build", json={"config_path": "/nope/missing.json"})
    assert r.status_code == 404


def test_marketplaces_empty(workspace):
    _, client = workspace
    data = client.get("/api/marketplaces").json()
    assert data["markets"] == []
    assert data["skills"] == []


def test_mcp_tools(workspace):
    _, client = workspace
    data = client.get("/api/mcp/tools").json()
    assert data["count"] == 40
    cats = {t["category"] for t in data["tools"]}
    assert "Core" in cats and "Marketplace" in cats and "Vector DB" in cats


def test_settings_defaults_roundtrip(workspace):
    _, client = workspace
    s = client.get("/api/settings").json()
    assert "clis" in s and "keys" in s and "defaults" in s
    r = client.put("/api/settings/defaults", json={"settings": {"default_agent": "kimi"}})
    assert r.json()["defaults"]["default_agent"] == "kimi"
    assert client.get("/api/settings").json()["defaults"]["default_agent"] == "kimi"


def test_settings_reject_unknown_key(workspace):
    _, client = workspace
    r = client.put("/api/settings/keys", json={"name": "NOT_A_KEY", "value": "x"})
    assert r.status_code == 400


def test_port_installs_and_uninstalls(tmp_path, monkeypatch):
    """Installer integration: dir-kind CLI receives the skill directory."""
    import skill_seekers.web.clis as clis_mod

    fake_home = tmp_path / "home"
    claude_skills = fake_home / ".claude" / "skills"
    specs = []
    for spec in clis_mod.get_cli_specs():
        if spec.id == "claude":
            spec = clis_mod.CliSpec(
                id=spec.id,
                name=spec.name,
                short=spec.short,
                color=spec.color,
                binary=spec.binary,
                global_path=claude_skills,
                kind=spec.kind,
            )
        specs.append(spec)
    monkeypatch.setattr(clis_mod, "get_cli_specs", lambda: specs)
    monkeypatch.setattr(
        "skill_seekers.web.installer.spec_by_id",
        lambda cid: next(s for s in specs if s.id == cid),
    )

    skill_dir = tmp_path / "myskill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: myskill\n---\n\n# m\n", encoding="utf-8")

    dest = install_skill_to_cli(skill_dir, "claude")
    assert (dest / "SKILL.md").is_file()
    assert uninstall_skill_from_cli("myskill", "claude") is True
    assert not dest.exists()


def test_flatten_skill(tmp_path):
    skill_dir = tmp_path / "flat"
    (skill_dir / "references").mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# main\n", encoding="utf-8")
    (skill_dir / "references" / "a.md").write_text("# ref a\n", encoding="utf-8")
    text = flatten_skill(skill_dir)
    assert "# main" in text and "# ref a" in text


def test_port_job_end_to_end(workspace, tmp_path, monkeypatch):
    """A port job runs via subprocess and installs into the CLI skills dir."""
    root, client = workspace
    fake_home = tmp_path / "jobhome"
    monkeypatch.setenv("HOME", str(fake_home))  # subprocess inherits env
    r = client.post(
        "/api/skills/port", json={"ids": ["demo"], "cli": "claude", "ai": False, "agent": "claude"}
    )
    assert r.status_code == 200
    deadline = time.time() + 30
    status = "running"
    while time.time() < deadline:
        job = client.get("/api/jobs").json()[0]
        status = job["status"]
        if status in ("done", "failed"):
            break
        time.sleep(0.5)
    assert status == "done", f"job log: {client.get('/api/jobs').json()[0]['log']}"
    assert (fake_home / ".claude" / "skills" / "demo" / "SKILL.md").is_file()


def test_ui_command_registered():
    from skill_seekers.cli.main import COMMAND_CLASSES, create_parser

    assert "ui" in COMMAND_CLASSES
    parser = create_parser()
    args = parser.parse_args(["ui", "--port", "9999", "--no-browser"])
    assert args.command == "ui"
    assert args.port == 9999
    assert args.no_browser is True


def test_library_official_registry(workspace, monkeypatch):
    """Official registry configs appear as remote entries and can be fetched."""
    import skill_seekers.web.app as web_app

    fake_configs = [
        {"name": "godot", "description": "Godot engine", "type": "unified", "category": "game-dev"},
        {"name": "react", "description": "React", "type": "unified", "category": "web-frameworks"},
    ]
    monkeypatch.setattr(web_app, "fetch_official_configs", lambda: (fake_configs, True))
    monkeypatch.setattr(
        web_app, "_official_cache", {"at": 0.0, "configs": fake_configs, "total": 2}
    )

    _, client = workspace
    lib = client.get("/api/library").json()
    official = lib["sources"][0]
    assert official["id"] == "official"
    assert official["connected"] is True
    assert official["configs"] == 2
    remote = [e for e in lib["entries"] if e.get("remote")]
    assert {e["name"] for e in remote} == {"godot.json", "react.json"}

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "name": "godot",
                "description": "d",
                "sources": [{"type": "documentation", "base_url": "https://docs.godotengine.org"}],
            }

    monkeypatch.setattr(web_app, "OFFICIAL_API_BASE", "https://fake.invalid")
    import httpx

    monkeypatch.setattr(httpx, "get", lambda *_url, **_kw: FakeResp())
    r = client.post("/api/library/official/fetch", json={"name": "godot"})
    assert r.status_code == 200
    # fetched config is now a local entry
    monkeypatch.setattr(web_app, "fetch_official_configs", lambda: (fake_configs, True))
    lib = client.get("/api/library").json()
    godot = [e for e in lib["entries"] if e["name"] == "godot.json"]
    assert godot[0]["fetched"] is True
    assert not godot[0].get("remote")


def test_library_official_offline(workspace, monkeypatch):
    """Registry unreachable: official source shows disconnected, no remote entries."""
    import skill_seekers.web.app as web_app

    monkeypatch.setattr(web_app, "fetch_official_configs", lambda: ([], False))
    _, client = workspace
    lib = client.get("/api/library").json()
    assert lib["sources"][0]["connected"] is False
    assert [e for e in lib["entries"] if e.get("remote")] == []


def test_registry_frontmatter():
    meta, body = registry.parse_frontmatter("---\nname: x\n---\n\nhello\n")
    assert meta["name"] == "x"
    assert body == "hello\n"
    meta, body = registry.parse_frontmatter("no frontmatter\n")
    assert meta == {}


# ── origin: plugin scan + path helpers ───────────────────────────────────────


def test_plugin_scan_skips_catalogue_clones(tmp_path, monkeypatch):
    """Only cache/ and top-level plugin dirs are installs; marketplaces/repos/data are catalogues."""
    fake_home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(fake_home))
    plugins = fake_home / ".claude" / "plugins"
    _mk_skill(
        plugins / "cache" / "official" / "superpowers" / "abc123" / "skills" / "brainstorming"
    )
    _mk_skill(plugins / "my-plugin" / "skills" / "local-skill")
    _mk_skill(
        plugins / "marketplaces" / "official" / "plugins" / "cwc" / "skills" / "catalogue-only"
    )
    _mk_skill(plugins / "repos" / "x" / "skills" / "repo-only")
    _mk_skill(plugins / "data" / "skills" / "data-only")

    from skill_seekers.web.clis import invalidate_installed_cache, iter_installed_skills, spec_by_id

    invalidate_installed_cache()
    names = {n for n, _ in iter_installed_skills(spec_by_id("claude"))}
    assert names == {"brainstorming", "local-skill"}


def test_plugin_name_for_layouts(tmp_path, monkeypatch):
    fake_home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(fake_home))
    plugins = fake_home / ".claude" / "plugins"

    from skill_seekers.web.clis import is_under_plugins, plugin_name_for

    assert (
        plugin_name_for(plugins / "cache" / "official" / "superpowers" / "abc" / "skills" / "x")
        == "superpowers"
    )
    assert (
        plugin_name_for(
            plugins / "cache" / "official" / "vercel" / "0.44.0" / ".claude" / "skills" / "y"
        )
        == "vercel"
    )
    assert plugin_name_for(plugins / "architect-design" / "skills" / "z") == "architect-design"
    assert plugin_name_for(plugins / "my-plugin" / ".claude" / "skills" / "w") == "my-plugin"
    assert plugin_name_for(plugins / "weird-layout" / "SKILL.md") is None
    assert plugin_name_for(fake_home / ".claude" / "skills" / "manual") is None
    assert is_under_plugins(plugins / "weird-layout") is True
    assert is_under_plugins(fake_home / ".claude" / "skills" / "manual") is False


# ── origin classification ────────────────────────────────────────────────────


def _seed_external_skills(home: Path) -> None:
    _mk_skill(
        home
        / ".claude"
        / "plugins"
        / "cache"
        / "official"
        / "superpowers"
        / "abc"
        / "skills"
        / "brainstorming"
    )
    _mk_skill(home / ".claude" / "skills" / "handwritten")
    built = _mk_skill(home / ".claude" / "skills" / "built-elsewhere")
    (built / ".seeker-meta.json").write_text('{"source_type": "github"}', encoding="utf-8")
    from skill_seekers.web.clis import invalidate_installed_cache

    invalidate_installed_cache()


def test_skill_origins(workspace):
    _, client = workspace
    _seed_external_skills(Path(os.environ["HOME"]))
    by_id = {s["id"]: s for s in client.get("/api/skills").json()}

    assert by_id["demo"]["origin"] == "seeker"
    assert by_id["demo"]["pluginName"] is None
    assert by_id["brainstorming"]["origin"] == "plugin"
    assert by_id["brainstorming"]["pluginName"] == "superpowers"
    assert by_id["handwritten"]["origin"] == "manual"
    assert by_id["handwritten"]["pluginName"] is None
    assert by_id["built-elsewhere"]["origin"] == "seeker"
    assert by_id["built-elsewhere"]["sourceType"] == "github"
    assert by_id["handwritten"]["tags"] == []


def test_external_skill_quality_and_source(workspace, monkeypatch):
    _, client = workspace
    home = Path(os.environ["HOME"])
    _seed_external_skills(home)

    import skill_seekers.cli.quality_checker as qc

    class FakeReport:
        quality_score = 42.0

    class FakeChecker:
        def __init__(self, _skill_dir):
            pass

        def check_all(self):
            return FakeReport()

    monkeypatch.setattr(qc, "SkillQualityChecker", FakeChecker)
    ext = {s["id"]: s for s in client.get("/api/skills").json()}["handwritten"]
    assert ext["quality"] == 42
    assert ext["source"] == str(home / ".claude" / "skills" / "handwritten")


def test_origin_of(workspace):
    root, _ = workspace
    _seed_external_skills(Path(os.environ["HOME"]))
    assert registry.origin_of(root, "demo") == "seeker"
    assert registry.origin_of(root, "brainstorming") == "plugin"
    assert registry.origin_of(root, "handwritten") == "manual"
    assert registry.origin_of(root, "built-elsewhere") == "seeker"
    with pytest.raises(KeyError):
        registry.origin_of(root, "nope")


# ── mutation guard ───────────────────────────────────────────────────────────


def test_mutations_rejected_for_external_skills(workspace):
    root, client = workspace
    _seed_external_skills(Path(os.environ["HOME"]))

    r = client.post("/api/skills/move", json={"ids": ["brainstorming"], "dest": "global"})
    assert r.status_code == 403
    assert r.json()["detail"] == "skill 'brainstorming' is managed outside Skill Seekers"
    assert client.post("/api/skills/delete", json={"ids": ["handwritten"]}).status_code == 403
    assert client.post("/api/skills/brainstorming/enhance").status_code == 403
    assert client.put("/api/skills/handwritten/content", json={"content": "x"}).status_code == 403

    # a mixed batch is rejected whole and the seeker skill is untouched
    r = client.post("/api/skills/delete", json={"ids": ["demo", "brainstorming"]})
    assert r.status_code == 403
    assert (root / "output" / "demo" / "SKILL.md").is_file()

    # unknown ids are 404, not 403
    assert (
        client.post("/api/skills/move", json={"ids": ["nope"], "dest": "global"}).status_code == 404
    )

    # copy-style actions stay open to every origin
    r = client.post("/api/skills/brainstorming/package", json={"targets": ["claude"]})
    assert r.status_code == 200
    r = client.post(
        "/api/skills/port",
        json={"ids": ["handwritten"], "cli": "kimi", "ai": False, "agent": "claude"},
    )
    assert r.status_code == 200


# ── MCP status probe ─────────────────────────────────────────────────────────


def test_mcp_status_probe(workspace, monkeypatch):
    import socket

    import skill_seekers.web.app as app_mod

    _, client = workspace
    monkeypatch.setattr(app_mod, "MCP_STDIO_MODULE", "definitely_not_a_module_xyz")
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    monkeypatch.setattr(app_mod, "MCP_HTTP_PORT", port)
    try:
        data = client.get("/api/mcp/status").json()
        assert data["stdio"] == {
            "state": "missing",
            "command": "python -m skill_seekers.mcp.server_fastmcp",
        }
        assert data["http"] == {
            "state": "live",
            "host": "127.0.0.1",
            "port": port,
            "url": f"http://127.0.0.1:{port}/sse",
        }
    finally:
        srv.close()

    monkeypatch.setattr(app_mod, "MCP_STDIO_MODULE", "json")
    data = client.get("/api/mcp/status").json()
    assert data["stdio"]["state"] == "installed"
    assert data["http"]["state"] == "down"
