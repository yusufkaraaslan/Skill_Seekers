"""FastAPI application exposing the Skill Seekers toolchain to the HUD.

Serves:

- ``/api/*``   — JSON API for skills, projects, jobs, create, library,
  marketplaces, MCP tools and settings.
- ``/*``       — the built single-page app from ``ui/dist`` (when present).

Run with: ``skill-seekers ui`` (see cli/ui_command.py).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import market, registry
from .clis import detect_clis
from .jobs import Job, get_job_manager
from .paths import load_settings, save_settings

DIST_DIR = Path(__file__).resolve().parents[3] / "ui" / "dist"

OFFICIAL_API_BASE = "https://api.skillseekersweb.com"
_official_cache: dict[str, Any] = {"at": 0.0, "configs": None, "total": 0}
OFFICIAL_CACHE_TTL = 180.0


def fetch_official_configs() -> tuple[list[dict[str, Any]], bool]:
    """List configs from the official remote registry (offline-tolerant).

    Returns:
        (configs, connected) — configs is [] when the API is unreachable.
    """
    import time

    import httpx

    now = time.time()
    if _official_cache["configs"] is not None and now - _official_cache["at"] < OFFICIAL_CACHE_TTL:
        return _official_cache["configs"], True
    try:
        resp = httpx.get(f"{OFFICIAL_API_BASE}/api/configs", timeout=8.0)
        resp.raise_for_status()
        data = resp.json()
        configs = data.get("configs", [])
        _official_cache.update(
            {"at": now, "configs": configs, "total": data.get("total", len(configs))}
        )
        return configs, True
    except Exception:  # noqa: BLE001 — registry unreachable: degrade gracefully
        return [], False


_cli_cache: dict[str, Any] = {"at": 0.0, "data": None}
CLI_CACHE_TTL = 60.0


def cached_detect_clis() -> list[dict[str, Any]]:
    """detect_clis with a TTL cache (binary probing spawns subprocesses)."""
    import time

    now = time.time()
    if _cli_cache["data"] is None or now - _cli_cache["at"] > CLI_CACHE_TTL:
        _cli_cache["data"] = detect_clis()
        _cli_cache["at"] = now
    return _cli_cache["data"]


API_KEY_PROVIDERS: dict[str, str] = {
    "ANTHROPIC_API_KEY": "anthropic",
    "GOOGLE_API_KEY": "google",
    "OPENAI_API_KEY": "openai",
    "MOONSHOT_API_KEY": "moonshot",
    "MINIMAX_API_KEY": "minimax",
    "GITHUB_TOKEN": "github",
}

MCP_TOOLS: list[dict[str, str]] = [
    # Core
    {
        "name": "list_configs",
        "desc": "List preset configurations",
        "category": "Core",
        "nl": "What presets are available?",
    },
    {
        "name": "generate_config",
        "desc": "Generate config from docs URL",
        "category": "Core",
        "nl": "Make a config for docs.react.dev",
    },
    {
        "name": "validate_config",
        "desc": "Validate config structure",
        "category": "Core",
        "nl": "Is my godot.json valid?",
    },
    {
        "name": "estimate_pages",
        "desc": "Estimate page count",
        "category": "Core",
        "nl": "How big is the Django docs site?",
    },
    {
        "name": "scrape_docs",
        "desc": "Scrape documentation",
        "category": "Core",
        "nl": "Scrape the React documentation",
    },
    {
        "name": "package_skill",
        "desc": "Package to platform bundle",
        "category": "Core",
        "nl": "Package output/react for Claude",
    },
    {
        "name": "upload_skill",
        "desc": "Upload to platform",
        "category": "Core",
        "nl": "Upload react-pro to Claude",
    },
    {
        "name": "enhance_skill",
        "desc": "AI enhancement",
        "category": "Core",
        "nl": "Enhance the fastapi skill",
    },
    {
        "name": "install_skill",
        "desc": "Complete workflow",
        "category": "Core",
        "nl": "Install django docs as a skill",
    },
    # Extended
    {
        "name": "scrape_github",
        "desc": "GitHub repository analysis",
        "category": "Extended",
        "nl": "Analyze facebook/react repo",
    },
    {
        "name": "scrape_pdf",
        "desc": "PDF extraction",
        "category": "Extended",
        "nl": "Extract this PDF manual",
    },
    {
        "name": "scrape_video",
        "desc": "Video transcript extraction",
        "category": "Extended",
        "nl": "Pull code from this tutorial",
    },
    {
        "name": "scrape_codebase",
        "desc": "Local codebase analysis",
        "category": "Extended",
        "nl": "Scan my project folder",
    },
    {
        "name": "scrape_generic",
        "desc": "Generic scraper (10+ source types)",
        "category": "Extended",
        "nl": "Scrape this Confluence space",
    },
    {
        "name": "sync_config",
        "desc": "Sync config from remote source",
        "category": "Extended",
        "nl": "Sync my presets from the registry",
    },
    {
        "name": "detect_patterns",
        "desc": "Pattern detection",
        "category": "Extended",
        "nl": "Find patterns in this codebase",
    },
    {
        "name": "extract_test_examples",
        "desc": "Examples from tests",
        "category": "Extended",
        "nl": "Pull usage examples from tests",
    },
    {
        "name": "build_how_to_guides",
        "desc": "Generate how-to guides",
        "category": "Extended",
        "nl": "Build how-to guides for axum",
    },
    {
        "name": "extract_config_patterns",
        "desc": "Extract config patterns",
        "category": "Extended",
        "nl": "Extract config patterns",
    },
    # Config sources
    {
        "name": "add_config_source",
        "desc": "Register git repo as config source",
        "category": "Config Sources",
        "nl": "Add our team preset repo",
    },
    {
        "name": "list_config_sources",
        "desc": "List registered sources",
        "category": "Config Sources",
        "nl": "Show my config sources",
    },
    {
        "name": "remove_config_source",
        "desc": "Remove config source",
        "category": "Config Sources",
        "nl": "Remove the old preset repo",
    },
    {
        "name": "fetch_config",
        "desc": "Fetch configs from git",
        "category": "Config Sources",
        "nl": "Fetch latest from the registry",
    },
    {
        "name": "submit_config",
        "desc": "Submit config to source",
        "category": "Config Sources",
        "nl": "Submit my godot config",
    },
    # Splitting
    {
        "name": "split_config",
        "desc": "Split large config",
        "category": "Splitting",
        "nl": "Split the godot config by topic",
    },
    {
        "name": "generate_router",
        "desc": "Generate router skill",
        "category": "Splitting",
        "nl": "Make a router for split configs",
    },
    # Publishing
    {
        "name": "push_config",
        "desc": "Push validated config to source repo",
        "category": "Publishing",
        "nl": "Push react.json to my fork",
    },
    # Marketplace
    {
        "name": "add_marketplace",
        "desc": "Register marketplace repository",
        "category": "Marketplace",
        "nl": "Add the anthropic skills market",
    },
    {
        "name": "list_marketplaces",
        "desc": "List registered marketplaces",
        "category": "Marketplace",
        "nl": "Show connected marketplaces",
    },
    {
        "name": "remove_marketplace",
        "desc": "Remove marketplace",
        "category": "Marketplace",
        "nl": "Disconnect the community market",
    },
    {
        "name": "publish_to_marketplace",
        "desc": "Publish skill to marketplace",
        "category": "Marketplace",
        "nl": "Publish godot-shader-lab",
    },
    # Vector DB
    {
        "name": "export_to_weaviate",
        "desc": "Export to Weaviate",
        "category": "Vector DB",
        "nl": "Export react to Weaviate",
    },
    {
        "name": "export_to_chroma",
        "desc": "Export to ChromaDB",
        "category": "Vector DB",
        "nl": "Push docs to Chroma",
    },
    {
        "name": "export_to_faiss",
        "desc": "Export to FAISS",
        "category": "Vector DB",
        "nl": "Build a FAISS index",
    },
    {
        "name": "export_to_qdrant",
        "desc": "Export to Qdrant",
        "category": "Vector DB",
        "nl": "Upsert into Qdrant",
    },
    # Workflows
    {
        "name": "list_workflows",
        "desc": "List all workflows",
        "category": "Workflows",
        "nl": "List workflow presets",
    },
    {
        "name": "get_workflow",
        "desc": "Get workflow YAML",
        "category": "Workflows",
        "nl": "Show security-focus.yaml",
    },
    {
        "name": "create_workflow",
        "desc": "Create new workflow",
        "category": "Workflows",
        "nl": "Create an api-review workflow",
    },
    {
        "name": "update_workflow",
        "desc": "Update workflow",
        "category": "Workflows",
        "nl": "Tweak the security preset",
    },
    {
        "name": "delete_workflow",
        "desc": "Delete workflow",
        "category": "Workflows",
        "nl": "Delete the old preset",
    },
]


# ── request models ────────────────────────────────────────────────────────────


class SourceEntry(BaseModel):
    type: str
    input: str


class CreateRequest(BaseModel):
    entries: list[SourceEntry]
    name: str = ""
    description: str = ""
    targets: list[str] = []
    flags: dict[str, Any] = {}


class MoveRequest(BaseModel):
    ids: list[str]
    dest: str


class IdsRequest(BaseModel):
    ids: list[str]


class PortRequest(BaseModel):
    ids: list[str]
    cli: str
    ai: bool = False
    agent: str = "claude"


class PackageRequest(BaseModel):
    targets: list[str] = ["claude"]


class ContentRequest(BaseModel):
    content: str


class ProjectRequest(BaseModel):
    path: str


class SourceRepoRequest(BaseModel):
    repo: str
    name: str = ""
    branch: str = "main"


class MarketplaceRequest(BaseModel):
    repo: str
    name: str = ""
    branch: str = "main"


class InstallRequest(BaseModel):
    path: str
    kind: str = "skill"
    name: str = ""
    clis: list[str] = ["claude"]


class PublishRequest(BaseModel):
    skill_name: str
    marketplace: str
    category: str = "community"


class BuildRequest(BaseModel):
    config_path: str
    name: str = ""


class FetchOfficialRequest(BaseModel):
    name: str


class KeyRequest(BaseModel):
    name: str
    value: str


class DefaultsRequest(BaseModel):
    settings: dict[str, Any]


# ── app factory ───────────────────────────────────────────────────────────────


def create_app(root: Path | None = None) -> FastAPI:
    """Build the FastAPI app bound to a workspace root directory."""
    root = (root or Path.cwd()).resolve()
    jobs = get_job_manager()

    app = FastAPI(title="Skill Seekers UI", version="3.9.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def skills_payload() -> list[dict[str, Any]]:
        settings = load_settings()
        return registry.discover_skills(root, settings.get("enabled_clis") or None)

    def skill_dir_for(skill_id: str) -> Path:
        for s in skills_payload():
            if s["id"] == skill_id:
                return Path(s["dir"])
        raise HTTPException(status_code=404, detail=f"unknown skill: {skill_id}")

    def on_job_done(job: Job) -> None:
        """Post-completion hooks: ingest scan results, refresh registry state."""
        if job.type == "scan" and job.status == "done" and job.meta.get("project_id"):
            out_dir = root / "configs" / "scanned" / job.meta.get("project_slug", "")
            frameworks = []
            if out_dir.is_dir():
                for cfg in sorted(out_dir.glob("*.json")):
                    try:
                        data = json.loads(cfg.read_text(encoding="utf-8"))
                        frameworks.append(
                            {
                                "name": str(data.get("name") or cfg.stem),
                                "version": str(data.get("version") or "—"),
                            }
                        )
                    except (OSError, ValueError):
                        continue
            registry.update_project_scan(job.meta["project_id"], frameworks, len(frameworks))
            registry.log_activity("scan", f"{job.label} scan: {len(frameworks)} configs emitted")
        if job.type == "create" and job.status == "done":
            registry.log_activity("create", f"{job.label} created ({job.detail})")
        if job.type == "port" and job.status == "done":
            registry.log_activity("port", job.detail)

    jobs.register_hook(on_job_done)

    # ── health & overview ────────────────────────────────────────────────

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {"ok": True, "root": str(root), "running": jobs.running_count()}

    @app.get("/api/overview")
    def overview() -> dict[str, Any]:
        return {
            "skills": skills_payload(),
            "jobs": jobs.list()[:12],
            "clis": cached_detect_clis(),
            "projects": registry.list_projects(),
            "activity": registry.list_activity(),
            "mcpToolCount": len(MCP_TOOLS),
        }

    # ── skills ───────────────────────────────────────────────────────────

    @app.get("/api/skills")
    def list_skills() -> list[dict[str, Any]]:
        return skills_payload()

    @app.post("/api/skills/move")
    def move_skills(req: MoveRequest) -> dict[str, Any]:
        registry.move_skills(req.ids, req.dest)
        dest_name = "global scope" if req.dest == "global" else req.dest
        registry.log_activity("move", f"moved {len(req.ids)} skill(s) → {dest_name}")
        return {"ok": True}

    @app.post("/api/skills/delete")
    def delete_skills(req: IdsRequest) -> dict[str, Any]:
        processed = registry.delete_skills(req.ids, root)
        registry.log_activity(
            "delete", f"deleted {len(processed)} skill(s): {', '.join(processed)}"
        )
        return {"ok": True, "deleted": processed}

    @app.post("/api/skills/port")
    def port_skills(req: PortRequest) -> dict[str, Any]:
        dirs = [str(skill_dir_for(i)) for i in req.ids]
        job = jobs.submit(
            "port",
            f"{len(dirs)} skill(s) → {req.cli}",
            f"install to {req.cli}" + (" (AI-assisted)" if req.ai else ""),
            {"type": "port", "skill_dirs": dirs, "cli": req.cli, "cwd": str(root)},
        )
        return {"ok": True, "job": job.to_dict()}

    @app.post("/api/skills/{skill_id}/enhance")
    def enhance_skill(skill_id: str) -> dict[str, Any]:
        skill_dir = skill_dir_for(skill_id)
        settings = load_settings()
        job = jobs.submit(
            "enhance",
            skill_id,
            "AI enhancement pass",
            {
                "type": "enhance",
                "skill_dir": str(skill_dir),
                "agent": settings.get("default_agent") or "claude",
                "cwd": str(root),
            },
        )
        registry.log_activity("enhance", f"{skill_id} enhancement queued")
        return {"ok": True, "job": job.to_dict()}

    @app.post("/api/skills/{skill_id}/package")
    def package_skill(skill_id: str, req: PackageRequest) -> dict[str, Any]:
        skill_dir = skill_dir_for(skill_id)
        job = jobs.submit(
            "package",
            f"{skill_id} → {', '.join(req.targets)}",
            f"package {skill_dir.name} for {len(req.targets)} target(s)",
            {
                "type": "package",
                "skill_dir": str(skill_dir),
                "targets": req.targets,
                "cwd": str(root),
            },
        )
        registry.log_activity("package", f"{skill_id} packaging → {', '.join(req.targets)}")
        return {"ok": True, "job": job.to_dict()}

    @app.put("/api/skills/{skill_id}/content")
    def save_skill_content(skill_id: str, req: ContentRequest) -> dict[str, Any]:
        skill_dir = skill_dir_for(skill_id)
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            raise HTTPException(status_code=404, detail="SKILL.md not found")
        skill_md.write_text(req.content, encoding="utf-8")
        return {"ok": True}

    # ── projects ─────────────────────────────────────────────────────────

    @app.get("/api/projects")
    def list_projects() -> list[dict[str, Any]]:
        return registry.list_projects()

    @app.post("/api/projects")
    def add_project(req: ProjectRequest) -> dict[str, Any]:
        path = Path(req.path).expanduser()
        if not path.is_dir():
            raise HTTPException(status_code=400, detail=f"not a directory: {path}")
        project = registry.add_project(str(path))
        slug = project["id"].removeprefix("pj-")
        out = root / "configs" / "scanned" / slug
        job = jobs.submit(
            "scan",
            project["name"],
            f"{project['path']} → configs/scanned/{slug}/",
            {"type": "scan", "directory": str(path), "out": str(out), "cwd": str(root)},
            meta={"project_id": project["id"], "project_slug": slug},
        )
        project["status"] = "scanning"
        registry.save_project(project)
        return {"ok": True, "project": project, "job": job.to_dict()}

    @app.post("/api/projects/{project_id}/rescan")
    def rescan_project(project_id: str) -> dict[str, Any]:
        project = registry.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="unknown project")
        slug = project_id.removeprefix("pj-")
        out = root / "configs" / "scanned" / slug
        job = jobs.submit(
            "scan",
            project["name"],
            f"{project['path']} → configs/scanned/{slug}/",
            {"type": "scan", "directory": project["path"], "out": str(out), "cwd": str(root)},
            meta={"project_id": project_id, "project_slug": slug},
        )
        project["status"] = "scanning"
        registry.save_project(project)
        return {"ok": True, "job": job.to_dict()}

    @app.delete("/api/projects/{project_id}")
    def delete_project(project_id: str) -> dict[str, Any]:
        if not registry.remove_project(project_id):
            raise HTTPException(status_code=404, detail="unknown project")
        return {"ok": True}

    # ── jobs ─────────────────────────────────────────────────────────────

    @app.get("/api/jobs")
    def list_jobs() -> list[dict[str, Any]]:
        return jobs.list()

    @app.post("/api/jobs/{job_id}/cancel")
    def cancel_job(job_id: str) -> dict[str, Any]:
        return {"ok": jobs.cancel(job_id)}

    # ── create ───────────────────────────────────────────────────────────

    @app.post("/api/create")
    def create(req: CreateRequest) -> dict[str, Any]:
        if not req.entries:
            raise HTTPException(status_code=400, detail="at least one source is required")
        name = req.name.strip() or _derive_name(req.entries[0].input)
        name = re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-").lower()
        if not name:
            raise HTTPException(status_code=400, detail="invalid skill name")
        settings = load_settings()
        spec = {
            "type": "create",
            "entries": [e.model_dump() for e in req.entries],
            "name": name,
            "targets": req.targets,
            "flags": {**req.flags, "description": req.description},
            "output_dir": settings.get("output_dir", "output"),
            "configs_dir": str(root / settings.get("configs_dir", "configs")),
            "cwd": str(root),
        }
        job = jobs.submit(
            "create",
            name,
            f"{len(req.entries)} source(s) → {', '.join(req.targets) or 'no packaging'}",
            spec,
        )
        return {"ok": True, "job": job.to_dict(), "name": name}

    # ── library ──────────────────────────────────────────────────────────

    @app.get("/api/library")
    def library() -> dict[str, Any]:
        from skill_seekers.services.source_manager import SourceManager

        manager = SourceManager()
        official_configs, official_online = fetch_official_configs()
        sources = [
            {
                "id": "official",
                "name": "official-registry",
                "repo": OFFICIAL_API_BASE,
                "kind": "official",
                "branch": "—",
                "configs": _official_cache.get("total", len(official_configs)),
                "lastFetch": "live" if official_online else "offline",
                "autoSync": True,
                "enabled": True,
                "connected": official_online,
            }
        ]
        for s in manager.list_sources():
            name = s.get("name", "")
            sources.append(
                {
                    "id": name,
                    "name": name,
                    "repo": s.get("git_url", ""),
                    "kind": "official"
                    if s.get("source_type") == "official"
                    or "skill-seekers-configs" in s.get("git_url", "")
                    else "custom",
                    "branch": s.get("branch", "main"),
                    "configs": 0,
                    "lastFetch": s.get("updated_at", s.get("created_at", "—")),
                    "autoSync": bool(s.get("auto_sync", False)),
                    "enabled": s.get("enabled", True),
                    "connected": True,
                }
            )
        entries = registry.list_config_entries(root)
        skills = skills_payload()
        for entry in entries:
            stem = entry["name"].removesuffix(".json")
            entry["usedIn"] = [
                s["name"] for s in skills if s["name"] == stem or stem in s["source"]
            ]
            entry["fetched"] = True
        local_names = {e["name"] for e in entries}
        for cfg in official_configs:
            fname = f"{cfg.get('name', '')}.json"
            if not cfg.get("name") or fname in local_names:
                continue
            entries.append(
                {
                    "id": f"cfg-remote-{cfg['name']}",
                    "name": fname,
                    "path": "",
                    "framework": cfg.get("name", ""),
                    "origin": "synced",
                    "source": "official",
                    "version": "—",
                    "sources": cfg.get("type", ""),
                    "description": str(cfg.get("description") or "")[:140],
                    "status": "ready",
                    "usedIn": [],
                    "remote": True,
                    "fetched": False,
                    "category": cfg.get("category", ""),
                }
            )
        return {"sources": sources, "entries": entries, "workflows": registry.list_workflows()}

    @app.post("/api/library/official/fetch")
    def fetch_official(req: FetchOfficialRequest) -> dict[str, Any]:
        """Download a config from the official remote registry into configs/."""
        name = req.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="config name required")
        import httpx

        try:
            resp = httpx.get(f"{OFFICIAL_API_BASE}/api/download/{name}.json", timeout=15.0)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:  # noqa: BLE001 — surface as 502
            raise HTTPException(status_code=502, detail=f"registry fetch failed: {e}") from e
        if not isinstance(data, dict) or "sources" not in data:
            raise HTTPException(status_code=422, detail="remote file is not a unified config")
        dest_dir = root / load_settings().get("configs_dir", "configs")
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{name}.json"
        dest.write_text(json.dumps(data, indent=2), encoding="utf-8")
        registry.log_activity("scan", f"fetched {name}.json from official registry")
        return {"ok": True, "path": str(dest)}

    @app.post("/api/library/sources")
    def add_source(req: SourceRepoRequest) -> dict[str, Any]:
        from skill_seekers.services.source_manager import SourceManager

        manager = SourceManager()
        name = req.name.strip() or req.repo.rstrip("/").removesuffix(".git").split("/")[-1]
        git_url = (
            req.repo if "://" in req.repo or req.repo.endswith(".git") else f"https://{req.repo}"
        )
        result = manager.add_source(name=name, git_url=git_url, branch=req.branch)
        job = jobs.submit(
            "fetch",
            f"fetch_config · {name}",
            f"git pull {git_url} ({req.branch})",
            {
                "type": "fetch",
                "name": name,
                "git_url": git_url,
                "branch": req.branch,
                "cwd": str(root),
            },
        )
        return {"ok": True, "source": result, "job": job.to_dict()}

    @app.delete("/api/library/sources/{name}")
    def remove_source(name: str) -> dict[str, Any]:
        from skill_seekers.services.source_manager import SourceManager

        ok = SourceManager().remove_source(name)
        if not ok:
            raise HTTPException(status_code=404, detail="unknown source")
        return {"ok": True}

    @app.post("/api/library/sources/{name}/fetch")
    def fetch_source(name: str) -> dict[str, Any]:
        from skill_seekers.services.source_manager import SourceManager

        source = SourceManager().get_source(name)
        if not source:
            raise HTTPException(status_code=404, detail="unknown source")
        job = jobs.submit(
            "fetch",
            f"fetch_config · {name}",
            f"git pull {source.get('git_url')} ({source.get('branch', 'main')})",
            {
                "type": "fetch",
                "name": name,
                "git_url": source.get("git_url"),
                "branch": source.get("branch", "main"),
                "token_env": source.get("token_env"),
                "cwd": str(root),
            },
        )
        return {"ok": True, "job": job.to_dict()}

    @app.post("/api/library/build")
    def build_config(req: BuildRequest) -> dict[str, Any]:
        cfg_path = Path(req.config_path)
        if not cfg_path.is_file():
            raise HTTPException(status_code=404, detail="config not found")
        try:
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"invalid JSON config: {e}") from e
        name = req.name.strip() or str(data.get("name") or cfg_path.stem)
        job = jobs.submit(
            "create",
            f"build · {cfg_path.name}",
            f"skill-seekers create --config {cfg_path}",
            {
                "type": "create",
                "entries": [{"type": "config", "input": str(cfg_path)}],
                "name": name,
                "targets": [],
                "flags": {},
                "configs_dir": str(root / "configs"),
                "cwd": str(root),
            },
        )
        return {"ok": True, "job": job.to_dict()}

    # ── marketplaces ─────────────────────────────────────────────────────

    @app.get("/api/marketplaces")
    def marketplaces() -> dict[str, Any]:
        from skill_seekers.services.marketplace_manager import MarketplaceManager

        manager = MarketplaceManager()
        markets = []
        skills: list[dict[str, Any]] = []
        installed_names = {s["name"] for s in skills_payload()}
        for m in manager.list_marketplaces():
            market_id = m.get("name", "")
            connected = False
            try:
                repo_path = market.sync_marketplace(m.get("git_url", ""), m.get("branch", "main"))
                connected = True
                skills.extend(market.browse_marketplace(repo_path, market_id))
            except Exception:  # noqa: BLE001 — offline marketplaces shown as disconnected
                pass
            markets.append(
                {
                    "id": market_id,
                    "name": market_id,
                    "repo": m.get("git_url", ""),
                    "type": m.get("type", "community"),
                    "skills": sum(1 for s in skills if s["market"] == market_id),
                    "lastSync": m.get("updated_at", m.get("created_at", "—")),
                    "connected": connected,
                }
            )
        for s in skills:
            s["installed"] = s["name"] in installed_names
        return {"markets": markets, "skills": skills}

    @app.post("/api/marketplaces")
    def add_marketplace(req: MarketplaceRequest) -> dict[str, Any]:
        from skill_seekers.services.marketplace_manager import MarketplaceManager

        name = req.name.strip() or req.repo.rstrip("/").removesuffix(".git").split("/")[-1]
        git_url = (
            req.repo if "://" in req.repo or req.repo.endswith(".git") else f"https://{req.repo}"
        )
        result = MarketplaceManager().add_marketplace(name=name, git_url=git_url, branch=req.branch)
        registry.log_activity("scan", f"marketplace {name} registered")
        return {"ok": True, "marketplace": result}

    @app.delete("/api/marketplaces/{name}")
    def remove_marketplace(name: str) -> dict[str, Any]:
        from skill_seekers.services.marketplace_manager import MarketplaceManager

        if not MarketplaceManager().remove_marketplace(name):
            raise HTTPException(status_code=404, detail="unknown marketplace")
        return {"ok": True}

    @app.post("/api/marketplaces/install")
    def install_from_marketplace(req: InstallRequest) -> dict[str, Any]:
        item_path = Path(req.path)
        if not item_path.exists():
            raise HTTPException(status_code=404, detail="item not found in marketplace cache")
        dest = market.install_marketplace_item(item_path, req.kind, root, req.clis)
        registry.log_activity("create", f"installed {item_path.name} from marketplace")
        return {"ok": True, "dest": str(dest)}

    @app.post("/api/marketplaces/publish")
    def publish_to_marketplace(req: PublishRequest) -> dict[str, Any]:
        skill_dir = skill_dir_for(req.skill_name)
        job = jobs.submit(
            "publish",
            f"{req.skill_name} → {req.marketplace}",
            "publish_to_marketplace",
            {
                "type": "publish",
                "skill_dir": str(skill_dir),
                "marketplace": req.marketplace,
                "category": req.category,
                "cwd": str(root),
            },
        )
        return {"ok": True, "job": job.to_dict()}

    # ── MCP tools ────────────────────────────────────────────────────────

    @app.get("/api/mcp/tools")
    def mcp_tools() -> dict[str, Any]:
        return {"tools": MCP_TOOLS, "count": len(MCP_TOOLS)}

    # ── settings ─────────────────────────────────────────────────────────

    @app.get("/api/settings")
    def settings() -> dict[str, Any]:
        from skill_seekers.cli.config_manager import ConfigManager

        manager = ConfigManager()
        keys = []
        for env_name, provider in API_KEY_PROVIDERS.items():
            is_set = bool(os.environ.get(env_name)) or bool(manager.get_api_key(provider))
            keys.append({"name": env_name, "set": is_set})
        return {
            "clis": cached_detect_clis(),
            "keys": keys,
            "defaults": load_settings(),
            "root": str(root),
        }

    @app.put("/api/settings/keys")
    def set_key(req: KeyRequest) -> dict[str, Any]:
        from skill_seekers.cli.config_manager import ConfigManager

        provider = API_KEY_PROVIDERS.get(req.name)
        if not provider:
            raise HTTPException(status_code=400, detail=f"unknown key: {req.name}")
        if provider == "github":
            os.environ[req.name] = req.value
        else:
            ConfigManager().set_api_key(provider, req.value)
        os.environ[req.name] = req.value
        return {"ok": True}

    @app.put("/api/settings/defaults")
    def set_defaults(req: DefaultsRequest) -> dict[str, Any]:
        current = load_settings()
        current.update(req.settings)
        save_settings(current)
        return {"ok": True, "defaults": current}

    @app.post("/api/settings/reprobe")
    def reprobe() -> dict[str, Any]:
        from .clis import invalidate_installed_cache

        _cli_cache["at"] = 0.0
        invalidate_installed_cache()
        return {"ok": True, "clis": cached_detect_clis()}

    # ── SPA static serving ───────────────────────────────────────────────

    if DIST_DIR.is_dir():
        app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

        @app.get("/{full_path:path}")
        def spa(full_path: str) -> FileResponse:
            candidate = DIST_DIR / full_path
            if full_path and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(DIST_DIR / "index.html")

    return app


def _derive_name(source: str) -> str:
    """Derive a skill name from a source input (URL, repo, or path)."""
    source = source.strip().rstrip("/")
    if not source:
        return ""
    tail = source.split("/")[-1] or source.split("/")[-2]
    tail = re.sub(r"\.(git|pdf|docx|epub|pptx|ipynb|yaml|yml|json|adoc|rss)$", "", tail)
    return tail


app = create_app()
