"""Standalone C3.x analysis runs and their manifests."""
# ruff: noqa: F811

from tests.test_web_api import workspace  # noqa: F401

from skill_seekers.web import analysis_store
from skill_seekers.web.jobs import Job, get_job_manager


def test_analyze_validates_and_submits(workspace, monkeypatch):
    root, client = workspace
    submitted = []
    monkeypatch.setattr(
        get_job_manager(),
        "submit",
        lambda *a: submitted.append(a[3]) or Job("j", a[0], a[1], a[2], spec=a[3]),
    )
    body = {
        "target": {"kind": "dir", "value": str(root)},
        "tools": ["patterns", "quality"],
        "depth": "basic",
    }
    assert client.post("/api/analyze", json={**body, "tools": []}).status_code == 400
    assert client.post("/api/analyze", json={**body, "tools": ["nope"]}).status_code == 400
    assert (
        client.post(
            "/api/analyze",
            json={**body, "target": {"kind": "dir", "value": str(root / "missing")}},
        ).status_code
        == 400
    )
    assert client.post("/api/analyze", json={**body, "depth": "deepest"}).status_code == 400
    assert client.post("/api/analyze", json=body).status_code == 200
    assert submitted[0]["type"] == "analyze" and submitted[0]["tools"] == ["patterns", "quality"]


def test_manifests_list_recent_and_per_skill(workspace):
    root, client = workspace
    skill_id = client.get("/api/skills").json()[0]["id"]
    analysis_store.write_manifest(
        root,
        "one",
        {
            "target": "/a",
            "tools": ["patterns"],
            "startedAt": "2026-09-13 09:00:00",
            "attachedTo": None,
            "results": {"patterns": {"count": 3, "path": "/x"}},
        },
    )
    analysis_store.write_manifest(
        root,
        "two",
        {
            "target": "/b",
            "tools": ["quality"],
            "startedAt": "2026-09-13 10:00:00",
            "attachedTo": skill_id,
            "results": {"quality": {"count": 91, "path": "/y"}},
        },
    )
    recent = client.get("/api/analyze/recent").json()
    assert [m["slug"] for m in recent] == ["two", "one"]
    detail = client.get(f"/api/skills/{skill_id}/detail").json()
    assert detail["analysis"] == [
        {"tool": "quality", "count": 91, "ranAt": "2026-09-13 10:00:00", "path": "/y"}
    ]
