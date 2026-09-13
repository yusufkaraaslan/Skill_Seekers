"""Route modules for the HUD; each exposes register(app, ctx)."""

from __future__ import annotations

from fastapi import FastAPI

from ..context import HudContext


def register_all(app: FastAPI, ctx: HudContext) -> None:
    from . import analyze, configs, environment, skill_detail, workflows

    skill_detail.register(app, ctx)
    analyze.register(app, ctx)
    configs.register(app, ctx)
    workflows.register(app, ctx)
    environment.register(app, ctx)
