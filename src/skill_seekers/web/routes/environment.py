"""Environment API: doctor checks, server control, agent skill installation.

Absorbs the old Seeker MCP screen: doctor health checks, start/stop for the
MCP HTTP and embedding servers (stdio is probed only — it runs as a child of
the calling agent, never started from the HUD), and installing the built
Skill Seekers skill into an AI coding agent's skill directory.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..context import HudContext
from ..paths import workspace_dir

SERVERS = {"mcp-stdio": "MCP · stdio", "mcp-http": "MCP · HTTP", "embedding": "Embedding server"}
STARTABLE = {"mcp-http", "embedding"}


# Module level on purpose: this file uses `from __future__ import annotations`,
# and FastAPI cannot resolve a request model defined inside register().
class InstallAgentRequest(BaseModel):
    # No skill_dir field on purpose: the source is always the workspace's own
    # bootstrap output, so a request body can never point the installer at an
    # arbitrary directory on this machine.
    force: bool = False


DOCTOR_LEVELS = {"pass": "ok", "warn": "warning", "fail": "error"}


def _doctor() -> dict[str, Any]:
    from skill_seekers.cli.doctor import run_all_checks

    checks = [
        {
            "name": result.name,
            "ok": result.status == "pass",
            "level": DOCTOR_LEVELS.get(result.status, "error"),
            "found": result.detail,
            "hint": result.verbose_detail,
            "fix": "",
        }
        for result in run_all_checks()
    ]
    return {"checks": checks, "ranAt": time.strftime("%Y-%m-%d %H:%M:%S")}


def _probe_http(url: str) -> bool:
    import httpx

    try:
        return httpx.get(url, timeout=1.5).status_code < 500
    except Exception:  # noqa: BLE001 — any failure means "down"
        return False


def register(app: FastAPI, ctx: HudContext) -> None:
    def running_server_job(server: str) -> dict[str, Any] | None:
        return next(
            (
                j
                for j in ctx.jobs.list(ctx.root)
                if j["type"] == "server"
                and j["label"] == server
                and j["status"] in ("running", "queued")
            ),
            None,
        )

    def servers() -> list[dict[str, Any]]:
        from ..app import probe_mcp_status

        mcp = probe_mcp_status()
        rows = [
            {
                "id": "mcp-stdio",
                "name": SERVERS["mcp-stdio"],
                "address": mcp["stdio"]["command"],
                "state": mcp["stdio"]["state"],
                "jobId": None,
            }
        ]
        for sid, address in (
            ("mcp-http", mcp["http"]["url"]),
            ("embedding", "http://127.0.0.1:8001"),
        ):
            job = running_server_job(sid)
            live = (
                mcp["http"]["state"] == "live"
                if sid == "mcp-http"
                else _probe_http(address + "/health")
            )
            rows.append(
                {
                    "id": sid,
                    "name": SERVERS[sid],
                    "address": address,
                    "state": "running" if job else ("live" if live else "stopped"),
                    "jobId": job["id"] if job else None,
                }
            )
        return rows

    def agents() -> list[dict[str, Any]]:
        from skill_seekers.cli.install_agent import get_agent_path, get_available_agents

        clis = {c["id"]: c for c in ctx.cached_detect_clis()}
        rows = []
        for agent in get_available_agents():
            cli = clis.get(agent, {})
            agent_dir = get_agent_path(agent, project_root=ctx.root)
            rows.append(
                {
                    "id": agent,
                    "name": cli.get("name", agent),
                    "short": cli.get("short", agent[:3].upper()),
                    "color": cli.get("color", "217 12% 55%"),
                    "detected": bool(cli.get("detected")),
                    "version": cli.get("version"),
                    "agentDir": str(agent_dir),
                    "skillInstalled": (agent_dir / "skill-seekers" / "SKILL.md").is_file(),
                }
            )
        return rows

    @app.get("/api/environment")
    def environment() -> dict[str, Any]:
        return {"doctor": _doctor(), "servers": servers(), "agents": agents()}

    @app.post("/api/environment/doctor")
    def rerun_doctor() -> dict[str, Any]:
        return _doctor()

    @app.post("/api/environment/servers/{server}/start")
    def start_server(server: str) -> dict[str, Any]:
        if server not in STARTABLE:
            raise HTTPException(400, "This server is not started from the HUD")
        if running_server_job(server):
            raise HTTPException(409, "Server is already running")
        job = ctx.submit_job(
            "server", server, f"run {SERVERS[server]}", {"type": "server", "server": server}
        )
        return {"ok": True, "job": job.to_dict()}

    @app.post("/api/environment/servers/{server}/stop")
    def stop_server(server: str) -> dict[str, Any]:
        job = running_server_job(server)
        if not job:
            raise HTTPException(409, "Server is not running")
        ctx.jobs.cancel(job["id"])
        return {"ok": True}

    @app.post("/api/environment/agents/{agent}/install")
    def install_agent_route(agent: str, req: InstallAgentRequest) -> dict[str, Any]:
        from skill_seekers.cli.install_agent import get_available_agents

        if agent not in get_available_agents():
            raise HTTPException(400, "Unsupported agent")
        skill_dir = workspace_dir(ctx.root, "output") / "skill-seekers"
        if not (skill_dir / "SKILL.md").is_file():
            raise HTTPException(
                409, "Build the Skill Seekers skill first (scripts/bootstrap_skill.sh)"
            )
        job = ctx.submit_job(
            "install-agent",
            agent,
            f"install skill → {agent}",
            {
                "type": "install-agent",
                "agent": agent,
                "skill_dir": str(skill_dir),
                "force": req.force,
            },
        )
        return {"ok": True, "job": job.to_dict()}
