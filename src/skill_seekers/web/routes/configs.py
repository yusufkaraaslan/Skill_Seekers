"""Config detail, save, validate and estimate endpoints for the Config page."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .. import registry
from ..context import HudContext
from ..paths import atomic_write, read_json, state_transaction


def _validate(path: Path) -> dict[str, Any]:
    from skill_seekers.cli.config_validator import UniSkillConfigValidator

    try:
        validator = UniSkillConfigValidator(str(path))
        valid = bool(validator.validate())
        return {
            "valid": valid,
            "errors": list(getattr(validator, "errors", [])),
            "warnings": list(getattr(validator, "warnings", [])),
        }
    except Exception as exc:  # noqa: BLE001 — a validator crash is itself a validation failure
        return {"valid": False, "errors": [str(exc)], "warnings": []}


class SaveRequest(BaseModel):
    data: dict[str, Any]
    revision: str | None = None


class EstimateRequest(BaseModel):
    max_discovery: int = 100
    timeout: int = 10


def register(app: FastAPI, ctx: HudContext) -> None:
    def path_for(cfg_id: str) -> Path:
        try:
            return registry.resolve_config(ctx.root, cfg_id)
        except (KeyError, ValueError):
            raise HTTPException(404, "unknown config") from None

    def entry_for(path: Path) -> dict[str, Any]:
        from skill_seekers.services.git_repo import GitConfigRepo

        entries = registry.list_config_entries(ctx.root)
        cache = GitConfigRepo().cache_dir
        if cache.is_dir():
            for source_dir in cache.iterdir():
                if source_dir.is_dir():
                    entries += registry.list_config_entries(ctx.root, source_dir, source_dir.name)
        return next(
            (e for e in entries if Path(e["path"]).resolve() == path.resolve()),
            {
                "name": path.name,
                "path": str(path),
                "source": "local",
                "origin": "custom",
                "framework": path.stem,
                "version": "—",
            },
        )

    @app.get("/api/configs/{cfg_id}")
    def config_detail(cfg_id: str) -> dict[str, Any]:
        from ..paths import load_settings

        path = path_for(cfg_id)
        raw = path.read_bytes()
        data = json.loads(raw.decode("utf-8"))
        skills = registry.discover_skills(ctx.root, load_settings().get("enabled_clis") or None)
        used_by = [
            {"id": s["id"], "name": s["name"]}
            for s in skills
            if s["name"] == path.stem or path.stem in (s.get("source") or "")
        ]
        sync_state = read_json(
            Path.home() / ".skill-seekers" / "sync" / f"{data.get('name', path.stem)}_sync.json",
            None,
        )
        estimate = read_json(path.with_name(f".{path.name}.estimate.json"), None)
        return {
            "id": cfg_id,
            **entry_for(path),
            "data": data,
            "revision": hashlib.sha256(raw).hexdigest(),
            "validation": _validate(path),
            "usedBy": used_by,
            "sync": sync_state,
            "lastEstimate": estimate,
        }

    @app.put("/api/configs/{cfg_id}")
    def save_config(cfg_id: str, req: SaveRequest) -> dict[str, Any]:
        path = path_for(cfg_id)
        if "sources" not in req.data:
            raise HTTPException(400, "A unified config needs a sources list")
        with state_transaction():
            current = hashlib.sha256(path.read_bytes()).hexdigest()
            if req.revision is None:
                raise HTTPException(428, "Load the current revision before saving")
            if req.revision != current:
                raise HTTPException(409, "Config changed since it was opened; reload before saving")
            encoded = json.dumps(req.data, indent=2).encode("utf-8")
            atomic_write(path, encoded)
        return {"ok": True, "revision": hashlib.sha256(encoded).hexdigest()}

    @app.post("/api/configs/{cfg_id}/validate")
    def validate_config(cfg_id: str) -> dict[str, Any]:
        return _validate(path_for(cfg_id))

    @app.post("/api/configs/{cfg_id}/estimate")
    def estimate_config(cfg_id: str, req: EstimateRequest) -> dict[str, Any]:
        if not 1 <= req.max_discovery <= 5000 or not 1 <= req.timeout <= 300:
            raise HTTPException(400, "max_discovery must be 1–5000 and timeout 1–300")
        path = path_for(cfg_id)
        job = ctx.submit_job(
            "estimate",
            path.name,
            f"estimate pages (max {req.max_discovery})",
            {
                "type": "estimate",
                "config_path": str(path),
                "max_discovery": req.max_discovery,
                "timeout": req.timeout,
                "result_path": str(path.with_name(f".{path.name}.estimate.json")),
            },
        )
        return {"ok": True, "job": job.to_dict()}
