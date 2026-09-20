from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .. import registry
from ..context import HudContext


def upload_targets() -> set[str]:
    """Targets whose adaptor actually uploads.

    Derived from the adaptor registry rather than hand-listed: faiss and qdrant
    package fine but have no uploading adaptor, so accepting them here queued a
    job that died in ``upload_skill``'s argparse.
    """
    from skill_seekers.cli.adaptors import get_upload_platforms

    return set(get_upload_platforms())


class UploadRequest(BaseModel):
    target: str
    options: dict[str, Any] = {}


class TranslateRequest(BaseModel):
    languages: list[str]


class UpdateRequest(BaseModel):
    apply: bool = False


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

    @app.post("/api/skills/{skill_id}/upload")
    def upload_skill(skill_id: str, req: UploadRequest) -> dict[str, Any]:
        from ..paths import workspace_dir

        if req.target not in upload_targets():
            raise HTTPException(400, f"Unsupported upload target: {req.target}")
        skill_dir = ctx.skill_dir_for(skill_id)
        job = ctx.submit_job(
            "upload",
            f"{skill_dir.name} → {req.target}",
            f"upload to {req.target}",
            {
                "type": "upload",
                "skill_dir": str(skill_dir),
                "target": req.target,
                "options": req.options,
                "output_dir": str(workspace_dir(ctx.root, "output") / "_packages"),
            },
        )
        return {"ok": True, "job": job.to_dict()}

    @app.post("/api/skills/{skill_id}/translate")
    def translate_skill(skill_id: str, req: TranslateRequest) -> dict[str, Any]:
        if not req.languages or any(
            not re.fullmatch(r"[a-z]{2,3}(-[A-Za-z]{2,4})?", lang) for lang in req.languages
        ):
            raise HTTPException(400, "Provide one or more language codes such as tr, de, zh-Hans")
        ctx.require_seeker([skill_id])
        skill_dir = ctx.skill_dir_for(skill_id)
        job = ctx.submit_job(
            "translate",
            skill_dir.name,
            f"translate → {', '.join(req.languages)}",
            {"type": "translate", "skill_dir": str(skill_dir), "languages": req.languages},
        )
        return {"ok": True, "job": job.to_dict()}

    @app.post("/api/skills/{skill_id}/update")
    def update_skill(skill_id: str, req: UpdateRequest) -> dict[str, Any]:
        ctx.require_seeker([skill_id])
        skill_dir = ctx.skill_dir_for(skill_id)
        job = ctx.submit_job(
            "update",
            skill_dir.name,
            "apply upstream changes" if req.apply else "check upstream for changes",
            {"type": "update", "skill_dir": str(skill_dir), "apply": req.apply},
        )
        return {"ok": True, "job": job.to_dict()}

    @app.post("/api/skills/{skill_id}/quality")
    def quality_skill(skill_id: str) -> dict[str, Any]:
        from ..paths import workspace_dir

        skill_dir = ctx.skill_dir_for(skill_id)
        job = ctx.submit_job(
            "quality",
            skill_dir.name,
            "quality report",
            {
                "type": "quality",
                "skill_dir": str(skill_dir),
                "output_dir": str(workspace_dir(ctx.root, "output") / "_reports"),
            },
        )
        return {"ok": True, "job": job.to_dict()}
