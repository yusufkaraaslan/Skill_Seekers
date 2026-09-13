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


def test_lifecycle_jobs_submit_with_expected_specs(workspace, monkeypatch):
    root, client = workspace
    path = _write_config(root)
    cfg_id = registry.config_id_for(path)
    from skill_seekers.services.source_manager import SourceManager

    SourceManager().add_source("team", "https://github.com/example/configs.git")
    submitted = []
    monkeypatch.setattr(
        get_job_manager(),
        "submit",
        lambda *a: submitted.append(a[3]) or Job("j", a[0], a[1], a[2], spec=a[3]),
    )
    assert (
        client.post(f"/api/configs/{cfg_id}/split", json={"strategy": "weird"}).status_code == 400
    )
    assert (
        client.post(
            f"/api/configs/{cfg_id}/split", json={"strategy": "category", "target_pages": 500}
        ).status_code
        == 200
    )
    assert (
        client.post(f"/api/configs/{cfg_id}/push", json={"source": "nope", "message": "m"})
    ).status_code == 404
    assert (
        client.post(f"/api/configs/{cfg_id}/push", json={"source": "team", "message": "m"})
    ).status_code == 200
    assert client.post(f"/api/configs/{cfg_id}/submit", json={}).status_code == 200
    assert client.post(f"/api/configs/{cfg_id}/sync/check").status_code == 200
    assert (
        client.post("/api/configs/generate", json={"kind": "url", "value": "not a url"}).status_code
        == 400
    )
    assert (
        client.post(
            "/api/configs/generate", json={"kind": "url", "value": "https://docs.example.invalid/"}
        ).status_code
        == 200
    )
    assert [s["type"] for s in submitted] == [
        "split",
        "push",
        "submit",
        "sync-check",
        "generate-config",
    ]


def test_sync_settings_persist(workspace):
    root, client = workspace
    cfg_id = registry.config_id_for(_write_config(root))
    assert (
        client.put(
            f"/api/configs/{cfg_id}/sync", json={"enabled": True, "interval": "yearly"}
        ).status_code
        == 400
    )
    assert (
        client.put(
            f"/api/configs/{cfg_id}/sync",
            json={"enabled": True, "interval": "daily", "auto_rebuild": True},
        ).status_code
        == 200
    )
    assert client.get(f"/api/configs/{cfg_id}").json()["syncSettings"] == {
        "enabled": True,
        "interval": "daily",
        "auto_rebuild": True,
    }


def test_sync_state_name_is_sanitised(workspace):
    """A config ``name`` is a request-derived path component: it must not let
    the detail read reach outside ~/.skill-seekers/sync/."""
    root, client = workspace
    path = _write_config(root, name="evil")
    path.write_text(json.dumps({"name": "../../evil", "sources": []}))
    assert client.get(f"/api/configs/{registry.config_id_for(path)}").status_code == 400


def test_detail_and_sync_check_agree_on_the_state_file(workspace, monkeypatch):
    """A nameless config used to be read as ``_sync.json`` and written as
    ``<stem>_sync.json``, so a finished check rendered as "never checked"."""
    from pathlib import Path

    from skill_seekers.sync import detector as detector_mod
    from skill_seekers.sync.models import ChangeReport
    from skill_seekers.web import runner

    root, client = workspace
    path = _write_config(root)
    path.write_text(
        json.dumps(
            {
                "name": "",
                "sources": [{"type": "documentation", "base_url": "https://example.invalid/d"}],
            }
        )
    )
    cfg_id = registry.config_id_for(path)
    submitted = []
    monkeypatch.setattr(
        get_job_manager(),
        "submit",
        lambda *a: submitted.append(a[3]) or Job("j", a[0], a[1], a[2], spec=a[3]),
    )
    assert client.post(f"/api/configs/{cfg_id}/sync/check").status_code == 200
    assert Path(submitted[0]["state_path"]).name == f"{path.stem}_sync.json"

    class FakeDetector:
        def check_pages(self, urls, previous_hashes, generate_diffs=False):
            return ChangeReport(skill_name="unknown", total_pages=len(urls), unchanged=len(urls))

    monkeypatch.setattr(detector_mod, "ChangeDetector", FakeDetector)
    assert runner.run_sync_check(submitted[0]) == 0
    assert client.get(f"/api/configs/{cfg_id}").json()["sync"]["total_checks"] == 1
