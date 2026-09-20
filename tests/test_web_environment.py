"""Doctor, server control and agent skill installation."""
# ruff: noqa: F811

from tests.test_web_api import _mk_skill, workspace  # noqa: F401
from skill_seekers.web.jobs import Job, get_job_manager


def test_environment_snapshot_shape(workspace):
    root, client = workspace
    env = client.get("/api/environment").json()
    assert {c["name"] for c in env["doctor"]["checks"]} >= {"Python version", "Git"} or len(
        env["doctor"]["checks"]
    ) >= 5
    assert all(c["level"] in ("ok", "warning", "error") for c in env["doctor"]["checks"])
    assert {s["id"] for s in env["servers"]} == {"mcp-stdio", "mcp-http", "embedding"}
    assert all(
        s["state"] in ("installed", "missing", "running", "stopped", "live", "down")
        for s in env["servers"]
    )
    claude = next(a for a in env["agents"] if a["id"] == "claude")
    assert claude["detected"] is True and claude["skillInstalled"] is False
    # cursor's install path (".cursor/skills/") is project-relative — it must
    # resolve under the HUD's workspace root, not the server process's cwd.
    cursor = next(a for a in env["agents"] if a["id"] == "cursor")
    assert cursor["agentDir"].startswith(str(root))


def test_server_start_stop_and_agent_install_jobs(workspace, monkeypatch):
    root, client = workspace
    manager = get_job_manager()
    submitted = []
    monkeypatch.setattr(
        manager,
        "submit",
        lambda *a: submitted.append(a) or Job("srv", a[0], a[1], a[2], status="running", spec=a[3]),
    )
    assert client.post("/api/environment/servers/mcp-stdio/start").status_code == 400
    assert client.post("/api/environment/servers/embedding/start").status_code == 200
    assert submitted[-1][3] == {"type": "server", "server": "embedding"} | {
        k: v for k, v in submitted[-1][3].items() if k in ("cwd", "output_dir", "configs_dir")
    }
    cancelled = []
    monkeypatch.setattr(manager, "cancel", lambda job_id: cancelled.append(job_id) or True)
    manager._jobs.append(
        Job(
            "srv",
            "server",
            "embedding",
            "",
            status="running",
            spec={"cwd": str(root), "type": "server", "server": "embedding"},
        )
    )
    try:
        assert client.post("/api/environment/servers/embedding/stop").status_code == 200
        assert cancelled == ["srv"]
    finally:
        manager._jobs.clear()
    assert (
        client.post("/api/environment/agents/claude/install", json={}).status_code == 409
    )  # no bootstrap output yet
    _mk_skill(root / "output/skill-seekers")
    assert client.post("/api/environment/agents/claude/install", json={}).status_code == 200
    assert submitted[-1][3]["type"] == "install-agent" and submitted[-1][3]["agent"] == "claude"
    assert client.post("/api/environment/agents/nope/install", json={}).status_code == 400


def test_agent_install_ignores_a_caller_supplied_skill_dir(workspace, monkeypatch):
    """The install source is the workspace bootstrap output, never request input."""
    root, client = workspace
    submitted = []
    monkeypatch.setattr(
        get_job_manager(),
        "submit",
        lambda *a: submitted.append(a) or Job("srv", a[0], a[1], a[2], status="running", spec=a[3]),
    )
    _mk_skill(root / "output/skill-seekers")
    response = client.post("/api/environment/agents/claude/install", json={"skill_dir": "/etc"})
    assert response.status_code in (200, 422)
    if response.status_code == 200:
        assert submitted[-1][3]["skill_dir"] == str(root / "output" / "skill-seekers")
