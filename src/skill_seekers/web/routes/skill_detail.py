from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from ..context import HudContext


def register(app: FastAPI, ctx: HudContext) -> None:  # noqa: ARG001 -- skeleton; Task 2 fills it in
    @app.get("/api/skills/{skill_id}/detail")
    def skill_detail(skill_id: str) -> dict[str, Any]:
        return {"id": skill_id}
