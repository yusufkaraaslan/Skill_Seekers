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
from ..paths import atomic_write, read_json, safe_name, state_transaction


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


class SplitRequest(BaseModel):
    strategy: str = "auto"
    target_pages: int = 5000


class PushRequest(BaseModel):
    source: str
    message: str = ""
    branch: bool = False
    force: bool = False


class SubmitRequest(BaseModel):
    probe_urls: bool = True


class SyncSettings(BaseModel):
    enabled: bool
    interval: str = "daily"
    auto_rebuild: bool = False


class GenerateRequest(BaseModel):
    kind: str
    value: str
    probe_urls: bool = True


SYNC_FILE = "sync.json"
SPLIT_STRATEGIES = ("auto", "none", "source", "category", "router", "size")
SYNC_INTERVALS = ("hourly", "daily", "weekly", "manual")


def sync_state_path(path: Path, data: dict[str, Any]) -> Path:
    """The one spelling of a config's sync-state file — reader and writer.

    ``safe_name`` keeps a config ``name`` from escaping the sync directory; an
    empty or missing name falls back to the config's file stem so the detail
    read and the sync-check write can never disagree.
    """
    name = safe_name(str(data.get("name") or path.stem))
    return Path.home() / ".skill-seekers" / "sync" / f"{name}_sync.json"


def sync_settings_all() -> dict[str, Any]:
    """Per-config sync preferences, keyed by config id."""
    from ..paths import UI_STATE_DIR

    return read_json(UI_STATE_DIR / SYNC_FILE, {})


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

    @app.post("/api/configs/generate")
    def generate(req: GenerateRequest) -> dict[str, Any]:
        # Registered before the /{cfg_id} routes so "generate" is never read
        # as a config id.
        if req.kind not in ("url", "name", "dir") or not req.value.strip():
            raise HTTPException(400, "Choose a URL, framework name or directory")
        if req.kind == "url" and not req.value.startswith(("http://", "https://")):
            raise HTTPException(400, "Enter a documentation URL")
        if req.kind == "dir" and not (ctx.root / Path(req.value).expanduser()).resolve().is_dir():
            raise HTTPException(400, "Directory not found")
        job = ctx.submit_job(
            "generate-config",
            req.value.strip(),
            "AI config generation",
            {
                "type": "generate-config",
                "kind": req.kind,
                "value": req.value.strip(),
                "probe_urls": req.probe_urls,
            },
        )
        return {"ok": True, "job": job.to_dict()}

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
        sync_state = read_json(sync_state_path(path, data), None)
        estimate = read_json(path.with_name(f".{path.name}.estimate.json"), None)
        return {
            "id": cfg_id,
            **entry_for(path),
            "data": data,
            "revision": hashlib.sha256(raw).hexdigest(),
            "validation": _validate(path),
            "usedBy": used_by,
            "sync": sync_state,
            "syncSettings": sync_settings_all().get(cfg_id),
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

    @app.post("/api/configs/{cfg_id}/split")
    def split_config(cfg_id: str, req: SplitRequest) -> dict[str, Any]:
        from ..paths import workspace_dir

        if req.strategy not in SPLIT_STRATEGIES or not 100 <= req.target_pages <= 100_000:
            raise HTTPException(400, "Unsupported split strategy or target size")
        path = path_for(cfg_id)
        job = ctx.submit_job(
            "split",
            path.name,
            f"split · {req.strategy}",
            {
                "type": "split",
                "config_path": str(path),
                "strategy": req.strategy,
                "target_pages": req.target_pages,
                "output_dir": str(workspace_dir(ctx.root, "configs")),
            },
        )
        return {"ok": True, "job": job.to_dict()}

    @app.post("/api/configs/{cfg_id}/push")
    def push_config(cfg_id: str, req: PushRequest) -> dict[str, Any]:
        from skill_seekers.services.source_manager import SourceManager

        from ..paths import safe_name

        safe_name(req.source)
        try:
            SourceManager().get_source(req.source)
        except KeyError:
            raise HTTPException(404, "unknown config source") from None
        path = path_for(cfg_id)
        job = ctx.submit_job(
            "push",
            path.name,
            f"push → {req.source}",
            {
                "type": "push",
                "config_path": str(path),
                "source": req.source,
                "message": req.message,
                "branch": req.branch,
                "force": req.force,
            },
        )
        return {"ok": True, "job": job.to_dict()}

    @app.post("/api/configs/{cfg_id}/submit")
    def submit_config(cfg_id: str, req: SubmitRequest) -> dict[str, Any]:
        path = path_for(cfg_id)
        job = ctx.submit_job(
            "submit",
            path.name,
            "submit to community registry",
            {"type": "submit", "config_path": str(path), "probe_urls": req.probe_urls},
        )
        return {"ok": True, "job": job.to_dict()}

    @app.post("/api/configs/{cfg_id}/sync/check")
    def sync_check(cfg_id: str) -> dict[str, Any]:
        path = path_for(cfg_id)
        state = sync_state_path(path, json.loads(path.read_text(encoding="utf-8")))
        job = ctx.submit_job(
            "sync-check",
            path.name,
            "check upstream pages for changes",
            {"type": "sync-check", "config_path": str(path), "state_path": str(state)},
        )
        return {"ok": True, "job": job.to_dict()}

    @app.put("/api/configs/{cfg_id}/sync")
    def set_sync(cfg_id: str, req: SyncSettings) -> dict[str, Any]:
        from ..paths import UI_STATE_DIR, update_json

        if req.interval not in SYNC_INTERVALS:
            raise HTTPException(400, "Unsupported interval")
        path_for(cfg_id)
        data = update_json(
            UI_STATE_DIR / SYNC_FILE, lambda cur: {**cur, cfg_id: req.model_dump()}, {}
        )
        return {"ok": True, "syncSettings": data[cfg_id]}
