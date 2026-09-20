"""Workflow YAML list/inspect/copy/save/validate/delete endpoints."""

from __future__ import annotations

from typing import Any

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..context import HudContext
from ..paths import atomic_write, safe_name


class YamlRequest(BaseModel):
    yaml: str


def _validate_yaml(text: str) -> dict[str, Any]:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return {"valid": False, "error": f"YAML: {exc}"}
    if not isinstance(data, dict) or not data.get("name"):
        return {"valid": False, "error": "top-level 'name' is required"}
    stages = data.get("stages") or data.get("steps") or []
    if not isinstance(stages, list) or not stages:
        return {"valid": False, "error": "at least one stage is required"}
    return {"valid": True, "error": None}


def _describe(name: str, origin: str, text: str, file: str) -> dict[str, Any]:
    validation = _validate_yaml(text)
    data = yaml.safe_load(text) if validation["valid"] else {}
    stages = data.get("stages") or data.get("steps") or []
    return {
        "name": name,
        "origin": origin,
        "file": file,
        "yaml": text,
        "steps": len(stages),
        "description": str(data.get("description") or ""),
        "validation": validation,
    }


def register(app: FastAPI, ctx: HudContext) -> None:  # noqa: ARG001 — uniform register(app, ctx) signature
    def user_dir():
        import skill_seekers.cli.workflows_command as wc

        return wc.USER_WORKFLOWS_DIR

    def all_workflows() -> list[dict[str, Any]]:
        from skill_seekers.cli.enhancement_workflow import list_bundled_workflows
        from skill_seekers.cli.workflows_command import _bundled_yaml_text

        rows = []
        user_names = set()
        if user_dir().is_dir():
            for path in sorted(user_dir().glob("*.y*ml")):
                user_names.add(path.stem)
                rows.append(
                    _describe(path.stem, "user", path.read_text(encoding="utf-8"), str(path))
                )
        for name in list_bundled_workflows():
            if name in user_names:
                continue
            text = _bundled_yaml_text(name) or ""
            rows.append(_describe(name, "bundled", text, f"bundled/{name}.yaml"))
        return sorted(rows, key=lambda r: (r["origin"] != "user", r["name"]))

    def one(name: str) -> dict[str, Any]:
        try:
            safe_name(name)
        except ValueError:
            raise HTTPException(404, "unknown workflow") from None
        row = next((r for r in all_workflows() if r["name"] == name), None)
        if not row:
            raise HTTPException(404, "unknown workflow")
        return row

    @app.get("/api/workflows")
    def list_workflows() -> list[dict[str, Any]]:
        return all_workflows()

    @app.get("/api/workflows/{name}")
    def get_workflow(name: str) -> dict[str, Any]:
        return one(name)

    @app.post("/api/workflows/{name}/copy")
    def copy_workflow(name: str) -> dict[str, Any]:
        row = one(name)
        dest = user_dir() / f"{name}.yaml"
        if dest.exists():
            raise HTTPException(409, f"{dest.name} already exists in your workflow directory")
        atomic_write(dest, row["yaml"].encode("utf-8"))
        return {"ok": True, "path": str(dest)}

    @app.put("/api/workflows/{name}")
    def save_workflow(name: str, req: YamlRequest) -> dict[str, Any]:
        safe_name(name)
        validation = _validate_yaml(req.yaml)
        if not validation["valid"]:
            raise HTTPException(400, validation["error"])
        dest = user_dir() / f"{name}.yaml"
        atomic_write(dest, req.yaml.encode("utf-8"))
        return {"ok": True, "path": str(dest)}

    @app.post("/api/workflows/{name}/validate")
    def validate_workflow(name: str) -> dict[str, Any]:
        row = one(name)
        result = _validate_yaml(row["yaml"])
        if result["valid"]:
            try:
                from skill_seekers.cli.enhancement_workflow import WorkflowEngine

                WorkflowEngine(name if row["origin"] == "bundled" else row["file"])
            except Exception as exc:  # noqa: BLE001 — engine load errors are the validation result
                result = {"valid": False, "error": str(exc)}
        return result

    @app.delete("/api/workflows/{name}")
    def delete_workflow(name: str) -> dict[str, Any]:
        row = one(name)
        if row["origin"] != "user":
            raise HTTPException(400, "Bundled workflows cannot be removed; copy one to edit it")
        path = user_dir() / f"{name}.yaml"
        if not path.is_file():
            path = user_dir() / f"{name}.yml"
        path.unlink(missing_ok=True)
        return {"ok": True}
