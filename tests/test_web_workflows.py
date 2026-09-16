"""Workflow YAML management through the HUD."""
# ruff: noqa: F811

from tests.test_web_api import workspace  # noqa: F401


def test_list_copy_edit_validate_delete(workspace, monkeypatch, tmp_path):
    _, client = workspace
    import skill_seekers.cli.workflows_command as wc

    monkeypatch.setattr(wc, "USER_WORKFLOWS_DIR", tmp_path / "wf")
    rows = client.get("/api/workflows").json()
    bundled = [r for r in rows if r["origin"] == "bundled"]
    assert bundled and all(r["yaml"] and r["steps"] >= 1 for r in bundled)
    name = bundled[0]["name"]
    assert client.post(f"/api/workflows/{name}/copy").status_code == 200
    assert client.post(f"/api/workflows/{name}/copy").status_code == 409
    assert (tmp_path / "wf" / f"{name}.yaml").is_file()
    assert client.get(f"/api/workflows/{name}").json()["origin"] == "user"
    assert (
        client.put("/api/workflows/mine", json={"yaml": "name: mine\nstages: ["}).status_code == 400
    )
    assert (
        client.put(
            "/api/workflows/mine",
            json={"yaml": bundled[0]["yaml"].replace(f"name: {name}", "name: mine")},
        ).status_code
        == 200
    )
    assert client.post("/api/workflows/mine/validate").json()["valid"] is True
    assert client.delete("/api/workflows/mine").status_code == 200
    assert client.delete(
        f"/api/workflows/{bundled[1]['name'] if len(bundled) > 1 else name}"
    ).status_code in (400, 200)
    assert client.delete("/api/workflows/../x").status_code in (400, 404)
