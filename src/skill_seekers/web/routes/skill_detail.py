from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

from .. import registry
from ..context import HudContext


def _entry_for(ctx: HudContext, skill_id: str) -> dict[str, Any]:
    from ..paths import load_settings

    skill_dir = ctx.skill_dir_for(skill_id)  # 404 on unknown
    settings = load_settings()
    for entry in registry.discover_skills(ctx.root, settings.get("enabled_clis") or None):
        if Path(entry["dir"]).resolve() == skill_dir.resolve():
            return entry
    raise HTTPException(404, f"unknown skill: {skill_id}")


def _matches_skill(job: dict[str, Any], skill_dir: Path, name: str) -> bool:
    spec = job.get("spec") or {}
    candidates = [spec.get("skill_dir"), *(spec.get("skill_dirs") or [])]
    if any(c and Path(c).resolve() == skill_dir.resolve() for c in candidates):
        return True
    return job["type"] == "create" and (spec.get("name") == name or job["label"] == name)


def register(app: FastAPI, ctx: HudContext) -> None:
    @app.get("/api/skills/{skill_id}/detail")
    def skill_detail(skill_id: str) -> dict[str, Any]:
        from skill_seekers.cli.enhance_status import read_status

        from ..analysis_store import list_for_skill

        entry = _entry_for(ctx, skill_id)
        skill_dir = Path(entry["dir"])
        files = entry.get("files") or []
        status = None
        if skill_dir.is_dir():
            try:
                status = read_status(str(skill_dir))
            except Exception:  # noqa: BLE001 — a corrupt status file must not 500 the page
                status = None
        return {
            **{k: v for k, v in entry.items() if k not in ("content", "files")},
            "fileCount": len(files),
            "config": registry._read_sidecar(skill_dir).get("config"),
            "qualityBreakdown": registry.skill_quality_breakdown(skill_dir)
            if skill_dir.is_dir()
            else [],
            "enhanceStatus": status,
            "analysis": list_for_skill(ctx.root, skill_id),
        }

    @app.get("/api/skills/{skill_id}/history")
    def skill_history(skill_id: str) -> list[dict[str, Any]]:
        skill_dir = ctx.skill_dir_for(skill_id)
        name = skill_dir.stem if skill_dir.is_file() else skill_dir.name
        with ctx.jobs._lock:
            rows = [
                {**j.to_dict(), "spec": j.spec}
                for j in ctx.jobs._jobs
                if j.spec.get("cwd") in (None, str(ctx.root))
            ]
        return [
            {k: v for k, v in r.items() if k != "spec"}
            for r in rows
            if _matches_skill(r, skill_dir, name)
        ]

    @app.get("/api/skills/{skill_id}/enhance-status")
    def skill_enhance_status(skill_id: str) -> dict[str, Any] | None:
        from skill_seekers.cli.enhance_status import read_status

        skill_dir = ctx.skill_dir_for(skill_id)
        return read_status(str(skill_dir)) if skill_dir.is_dir() else None
