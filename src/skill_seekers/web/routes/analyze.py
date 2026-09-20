"""Standalone C3.x analysis runs: submit a job, list past manifests."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..analysis_store import list_recent
from ..context import HudContext

TOOLS = ("patterns", "tests", "guides", "config", "router", "quality")
DEPTHS = ("basic", "c3x")
AI_MODES = ("off", "auto", "api", "local")
REPO_RE = re.compile(r"[\w.-]+/[\w.-]+")


# Module level on purpose: this file uses `from __future__ import annotations`,
# and FastAPI cannot resolve a request model defined inside register().
class Target(BaseModel):
    kind: str
    value: str


class AnalyzeRequest(BaseModel):
    target: Target
    tools: list[str]
    depth: str = "basic"
    min_confidence: float = 0.7
    ai_mode: str = "off"
    attach_to: str | None = None


def register(app: FastAPI, ctx: HudContext) -> None:
    """Wire the analyze endpoints onto the app."""

    @app.post("/api/analyze")
    def analyze(req: AnalyzeRequest) -> dict[str, Any]:
        if not req.tools or set(req.tools) - set(TOOLS):
            raise HTTPException(400, "Choose one or more supported tools")
        if req.depth not in DEPTHS or req.ai_mode not in AI_MODES:
            raise HTTPException(400, "Unsupported depth or AI mode")
        if not 0 <= req.min_confidence <= 1:
            raise HTTPException(400, "min_confidence must be between 0 and 1")
        if req.target.kind == "skill":
            value = str(ctx.skill_dir_for(req.target.value))
        elif req.target.kind == "dir":
            path = (ctx.root / Path(req.target.value).expanduser()).resolve()
            if not path.is_dir():
                raise HTTPException(400, f"not a directory: {path}")
            value = str(path)
        elif req.target.kind == "repo":
            if not REPO_RE.fullmatch(req.target.value):
                raise HTTPException(400, "Use owner/repo")
            value = req.target.value
        else:
            raise HTTPException(400, "Unsupported target kind")
        if req.attach_to:
            ctx.skill_dir_for(req.attach_to)  # 404 on unknown
        job = ctx.submit_job(
            "analyze",
            Path(value).name,
            f"{len(req.tools)} tool(s) · {req.depth}",
            {
                "type": "analyze",
                "target": {"kind": req.target.kind, "value": value},
                "tools": req.tools,
                "depth": req.depth,
                "min_confidence": req.min_confidence,
                "ai_mode": req.ai_mode,
                "attach_to": req.attach_to,
            },
        )
        return {"ok": True, "job": job.to_dict()}

    @app.get("/api/analyze/recent")
    def recent() -> list[dict[str, Any]]:
        return list_recent(ctx.root)
