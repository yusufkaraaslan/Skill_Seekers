"""Routed skill page API: detail, history, enhance status, and skill-scoped jobs."""
# ruff: noqa: F811 -- imported pytest fixture shares its injection parameter name

import json

from tests.test_web_api import _mk_skill, workspace  # noqa: F401

from skill_seekers.web.jobs import Job, get_job_manager


def test_context_is_wired_and_routes_registered(workspace):
    _, client = workspace
    paths = {route.path for route in client.app.routes}
    assert "/api/skills/{skill_id}/detail" in paths


def test_detail_merges_registry_installs_and_sidecar(workspace):
    root, client = workspace
    from skill_seekers.web.installer import install_skill_to_cli
    from skill_seekers.web.clis import invalidate_installed_cache

    (root / "output/demo/.seeker-meta.json").write_text(
        json.dumps({"source": "https://react.dev", "source_type": "docs", "targets": ["claude"]})
    )
    install_skill_to_cli(root / "output/demo", "claude")
    invalidate_installed_cache()
    skill_id = client.get("/api/skills").json()[0]["id"]
    detail = client.get(f"/api/skills/{skill_id}/detail").json()
    assert detail["name"] == "demo"
    assert detail["source"] == "https://react.dev"
    assert detail["fileCount"] == 2  # SKILL.md + references/api.md (sidecars excluded)
    # opencode also treats .claude/skills as a compat alt_path (clis.py), so a
    # claude install legitimately shows up under both CLI ids here; assert on
    # the claude installation this test actually created rather than the full
    # (CLI-detection-dependent) list.
    claude_installs = [i for i in detail["installations"] if i["cli"] == "claude"]
    assert len(claude_installs) == 1
    assert claude_installs[0]["owned"] == "true"
    assert {b["label"] for b in detail["qualityBreakdown"]} >= {"frontmatter", "structure"}
    assert detail["enhanceStatus"] is None
    assert client.get("/api/skills/nope/detail").status_code == 404


def test_history_lists_only_jobs_for_this_skill(workspace):
    root, client = workspace
    manager = get_job_manager()
    skill_id = client.get("/api/skills").json()[0]["id"]
    manager._jobs.extend(
        [
            Job(
                "a",
                "package",
                "demo",
                "",
                status="done",
                spec={"cwd": str(root), "skill_dir": str(root / "output/demo")},
            ),
            Job(
                "b",
                "enhance",
                "other",
                "",
                status="done",
                spec={"cwd": str(root), "skill_dir": str(root / "output/other")},
            ),
            Job(
                "c", "create", "demo", "", status="failed", spec={"cwd": str(root), "name": "demo"}
            ),
        ]
    )
    try:
        ids = [j["id"] for j in client.get(f"/api/skills/{skill_id}/history").json()]
    finally:
        manager._jobs.clear()
    assert ids == ["a", "c"]


def test_enhance_status_reads_sidecar_file(workspace):
    root, client = workspace
    skill_id = client.get("/api/skills").json()[0]["id"]
    (root / "output/demo/.enhancement_status.json").write_text(
        json.dumps({"status": "running", "agent": "claude", "started_at": "2026-09-13T09:00:00"})
    )
    status = client.get(f"/api/skills/{skill_id}/enhance-status").json()
    assert status["status"] == "running"
