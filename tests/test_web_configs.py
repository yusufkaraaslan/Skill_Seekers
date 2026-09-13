"""Routed config page API."""
# ruff: noqa: F811

import json

from tests.test_web_api import workspace  # noqa: F401
from skill_seekers.web import registry
from skill_seekers.web.jobs import Job, get_job_manager


def _write_config(root, name="react", **extra):
    path = root / "configs" / f"{name}.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "name": name,
                "description": "d",
                "sources": [{"type": "documentation", "base_url": "https://example.invalid/docs"}],
                **extra,
            },
            indent=2,
        )
    )
    return path


def test_config_detail_and_revisioned_save(workspace):
    root, client = workspace
    path = _write_config(root)
    cfg_id = registry.config_id_for(path)
    assert client.get("/api/library").json()["entries"][0]["id"] == cfg_id
    detail = client.get(f"/api/configs/{cfg_id}").json()
    assert detail["name"] == "react.json" and detail["data"]["name"] == "react"
    assert detail["validation"]["valid"] is True
    new = {**detail["data"], "description": "edited"}
    assert client.put(f"/api/configs/{cfg_id}", json={"data": new}).status_code == 428
    assert (
        client.put(
            f"/api/configs/{cfg_id}", json={"data": new, "revision": detail["revision"]}
        ).status_code
        == 200
    )
    assert (
        client.put(
            f"/api/configs/{cfg_id}", json={"data": new, "revision": detail["revision"]}
        ).status_code
        == 409
    )
    assert json.loads(path.read_text())["description"] == "edited"
    assert client.get("/api/configs/cfg-nope").status_code == 404


def test_validate_reports_errors_without_writing(workspace):
    root, client = workspace
    path = _write_config(root, name="broken")
    path.write_text(json.dumps({"name": "broken", "sources": [{"type": "documentation"}]}))
    cfg_id = registry.config_id_for(path)
    result = client.post(f"/api/configs/{cfg_id}/validate").json()
    assert result["valid"] is False and result["errors"]


def test_estimate_submits_job(workspace, monkeypatch):
    root, client = workspace
    path = _write_config(root)
    submitted = []
    monkeypatch.setattr(
        get_job_manager(),
        "submit",
        lambda *a: submitted.append(a[3]) or Job("j", a[0], a[1], a[2], spec=a[3]),
    )
    assert (
        client.post(
            f"/api/configs/{registry.config_id_for(path)}/estimate", json={"max_discovery": 0}
        ).status_code
        == 400
    )
    assert (
        client.post(
            f"/api/configs/{registry.config_id_for(path)}/estimate",
            json={"max_discovery": 50, "timeout": 10},
        ).status_code
        == 200
    )
    assert submitted[0]["type"] == "estimate" and submitted[0]["config_path"] == str(path)
