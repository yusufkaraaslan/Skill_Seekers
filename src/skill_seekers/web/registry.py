"""Discovery of skills, projects, configs and activity for the web UI.

Skills are discovered from the workspace ``output/`` directory (any folder
with a SKILL.md), enriched with:

- frontmatter parsed from SKILL.md (name/description)
- a quality score from the existing SkillQualityChecker (cached by mtime)
- install state across detected CLIs (via installer.installed_clis_for)
- provenance sidecars (``.seeker-meta.json``) written by create jobs
- user overrides (scope/project/tags) stored in the UI state dir
"""

from __future__ import annotations

import re
import shutil
import time
from pathlib import Path
from typing import Any

import yaml

from .installer import installed_clis_for, uninstall_skill_from_cli
from .paths import (
    ACTIVITY_FILE,
    PROJECTS_FILE,
    SKILLS_META_FILE,
    TRASH_DIR,
    read_json,
    write_json,
)

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
MAX_CONTENT_BYTES = 256 * 1024

# Frontend source-type ids (must match ui/src/lib/data.ts SOURCE_META keys)
KNOWN_SOURCE_TYPES = {
    "docs",
    "github",
    "local",
    "pdf",
    "video",
    "notebook",
    "wiki",
    "openapi",
    "chat",
    "docx",
    "epub",
    "pptx",
    "asciidoc",
    "html",
    "rss",
    "manpage",
    "confluence",
    "notion",
    "config",
}


# ── skills ────────────────────────────────────────────────────────────────────


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split YAML frontmatter from markdown body (tolerates malformed input)."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    try:
        meta = yaml.safe_load(m.group(1)) or {}
        if not isinstance(meta, dict):
            meta = {}
    except yaml.YAMLError:
        meta = {}
    return meta, text[m.end() :]


def _dir_size_kb(path: Path) -> int:
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                continue
    return max(1, round(total / 1024))


def _list_files(skill_dir: Path) -> list[dict[str, str]]:
    files = []
    for p in sorted(skill_dir.rglob("*")):
        if p.is_file() and not p.name.startswith(".seeker"):
            try:
                size = p.stat().st_size
            except OSError:
                continue
            files.append(
                {
                    "path": str(p.relative_to(skill_dir)),
                    "size": f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B",
                }
            )
    return files[:200]


def _quality_for(skill_dir: Path, meta_cache: dict[str, Any]) -> int:
    """Quality score via SkillQualityChecker, cached by SKILL.md mtime."""
    skill_md = skill_dir / "SKILL.md"
    try:
        mtime = skill_md.stat().st_mtime
    except OSError:
        return 0
    cached = meta_cache.get("_quality_cache", {}).get(skill_dir.name)
    if cached and abs(cached.get("mtime", 0) - mtime) < 1e-6:
        return int(cached.get("score", 0))
    score = 75  # neutral default when the checker cannot run
    try:
        from skill_seekers.cli.quality_checker import SkillQualityChecker

        report = SkillQualityChecker(skill_dir).check_all()
        score = int(round(report.quality_score))
    except Exception:  # noqa: BLE001 — quality is best-effort metadata
        pass
    meta_cache.setdefault("_quality_cache", {})[skill_dir.name] = {"mtime": mtime, "score": score}
    return score


def discover_skills(root: Path, enabled_clis: list[str] | None = None) -> list[dict[str, Any]]:
    """Find all built skills under ``root/output`` and describe them for the UI."""
    out_dir = root / "output"
    meta = read_json(SKILLS_META_FILE, {})
    if not isinstance(meta, dict):
        meta = {}
    overrides: dict[str, Any] = meta.get("skills", {})
    skills: list[dict[str, Any]] = []
    if out_dir.is_dir():
        for child in sorted(out_dir.iterdir()):
            if not child.is_dir() or child.name.endswith("_data"):
                continue
            skill_md = child / "SKILL.md"
            if not skill_md.is_file():
                continue
            skills.append(_describe_skill(child, overrides.get(child.name, {}), meta, enabled_clis))
    # Skills installed globally but not present in this workspace's output/
    for cli_name, cli_dir in _global_only_skills(out_dir):
        skills.append(
            _describe_global_only(
                cli_name, cli_dir, overrides.get(cli_name, {}), meta, enabled_clis, root
            )
        )
    meta["skills"] = overrides
    write_json(SKILLS_META_FILE, meta)
    return skills


def _global_only_skills(out_dir: Path) -> list[tuple[str, Path]]:
    """(name, dir) pairs installed for claude but absent from output/."""
    from .clis import iter_installed_skills, spec_by_id

    local = {p.name for p in out_dir.iterdir() if p.is_dir()} if out_dir.is_dir() else set()
    return [(n, d) for n, d in iter_installed_skills(spec_by_id("claude")) if n not in local]


def _read_sidecar(skill_dir: Path) -> dict[str, Any]:
    sidecar = skill_dir / ".seeker-meta.json"
    data = read_json(sidecar, {})
    return data if isinstance(data, dict) else {}


def _describe_skill(
    skill_dir: Path,
    override: dict[str, Any],
    meta_cache: dict[str, Any],
    enabled_clis: list[str] | None,
) -> dict[str, Any]:
    skill_md = skill_dir / "SKILL.md"
    raw = skill_md.read_text(encoding="utf-8", errors="replace")
    front, _body = parse_frontmatter(raw)
    sidecar = _read_sidecar(skill_dir)
    name = str(front.get("name") or skill_dir.name)
    description = str(front.get("description") or "")
    if len(raw.encode("utf-8")) > MAX_CONTENT_BYTES:
        raw = raw[:MAX_CONTENT_BYTES]
    try:
        updated = time.strftime("%Y-%m-%d", time.localtime(skill_md.stat().st_mtime))
    except OSError:
        updated = "—"
    installs = installed_clis_for(name) or installed_clis_for(skill_dir.name)
    if enabled_clis:
        installs = [c for c in installs if c in enabled_clis] or installs
    source_type = override.get("source_type") or sidecar.get("source_type") or "docs"
    if source_type not in KNOWN_SOURCE_TYPES:
        source_type = "docs"
    return {
        "id": skill_dir.name,
        "name": name,
        "description": description,
        "scope": override.get("scope", "global"),
        "projectId": override.get("project_id"),
        "installs": installs,
        "source": override.get("source") or sidecar.get("source") or str(skill_dir),
        "sourceType": source_type,
        "version": str(front.get("version") or sidecar.get("version") or "1.0.0"),
        "sizeKb": _dir_size_kb(skill_dir),
        "updatedAt": updated,
        "quality": _quality_for(skill_dir, meta_cache),
        "tags": override.get("tags", []),
        "files": _list_files(skill_dir),
        "content": raw,
        "dir": str(skill_dir),
        # Everything under <workspace>/output was built here.
        "origin": "seeker",
        "pluginName": None,
    }


def _describe_global_only(
    name: str,
    skill_dir: Path,
    override: dict[str, Any],
    meta_cache: dict[str, Any],
    enabled_clis: list[str] | None,
    root: Path,
) -> dict[str, Any]:
    skill_md = skill_dir / "SKILL.md"
    raw = skill_md.read_text(encoding="utf-8", errors="replace") if skill_md.is_file() else ""
    front, _ = parse_frontmatter(raw)
    sidecar = _read_sidecar(skill_dir)
    if len(raw.encode("utf-8")) > MAX_CONTENT_BYTES:
        raw = raw[:MAX_CONTENT_BYTES]
    installs = installed_clis_for(name)
    if enabled_clis:
        installs = [c for c in installs if c in enabled_clis] or installs
    origin, plugin_name = classify_origin(skill_dir, root)
    source_type = override.get("source_type") or sidecar.get("source_type") or "docs"
    if source_type not in KNOWN_SOURCE_TYPES:
        source_type = "docs"
    return {
        "id": name,
        "name": str(front.get("name") or name),
        "description": str(front.get("description") or "installed outside this workspace"),
        "scope": override.get("scope", "global"),
        "projectId": override.get("project_id"),
        "installs": installs,
        "source": override.get("source") or sidecar.get("source") or str(skill_dir),
        "sourceType": source_type,
        "version": str(front.get("version") or sidecar.get("version") or "1.0.0"),
        "sizeKb": _dir_size_kb(skill_dir) if skill_dir.is_dir() else 0,
        "updatedAt": time.strftime("%Y-%m-%d", time.localtime(skill_md.stat().st_mtime))
        if skill_md.is_file()
        else "—",
        "quality": _quality_for(skill_dir, meta_cache) if skill_md.is_file() else 0,
        "tags": override.get("tags", []),
        "files": _list_files(skill_dir) if skill_dir.is_dir() else [],
        "content": raw,
        "dir": str(skill_dir),
        "origin": origin,
        "pluginName": plugin_name,
    }


# ── origin ────────────────────────────────────────────────────────────────────

SKILL_ORIGINS = ("seeker", "plugin", "manual")


def classify_origin(skill_dir: Path, root: Path) -> tuple[str, str | None]:
    """(origin, plugin_name) for a skill directory.

    Evaluated in order — location beats provenance:

    seeker: built in this workspace (under root/output).
    plugin: installed under ~/.claude/plugins — even when the directory
            carries a .seeker-meta.json sidecar, e.g. a Skill-Seekers-built
            skill that was republished inside a plugin. Location wins over
            provenance: once a skill lives in a plugin bundle, it is managed
            by that plugin, not by Skill Seekers.
    seeker: (fallback) carries the .seeker-meta.json sidecar a create job
            writes (copied along by the installer, so builds from other
            workspaces still count), as long as it isn't under plugins.
    manual: anything else found in a CLI's skills dir.
    """
    from .clis import is_under_plugins, plugin_name_for

    try:
        skill_dir.resolve().relative_to((root / "output").resolve())
        return "seeker", None
    except ValueError:
        pass
    if is_under_plugins(skill_dir):
        return "plugin", plugin_name_for(skill_dir)
    if (skill_dir / ".seeker-meta.json").is_file():
        return "seeker", None
    return "manual", None


def origin_of(root: Path, skill_id: str) -> str:
    """Origin of a skill by id, without building the full payload.

    Raises:
        KeyError: when no skill with that id is known.
    """
    out_dir = root / "output"
    if (out_dir / skill_id / "SKILL.md").is_file():
        return "seeker"
    for name, skill_dir in _global_only_skills(out_dir):
        if name == skill_id:
            return classify_origin(skill_dir, root)[0]
    raise KeyError(skill_id)


def set_skill_override(name: str, **fields: Any) -> None:
    """Persist user overrides (scope/project/tags) for a skill."""
    meta = read_json(SKILLS_META_FILE, {})
    if not isinstance(meta, dict):
        meta = {}
    entry = meta.setdefault("skills", {}).setdefault(name, {})
    entry.update({k: v for k, v in fields.items() if v is not None})
    write_json(SKILLS_META_FILE, meta)


def move_skills(names: list[str], dest: str) -> None:
    """Change scope of skills ('global' or a project id)."""
    for name in names:
        if dest == "global":
            set_skill_override(name, scope="global", project_id=None)
        else:
            set_skill_override(name, scope="project", project_id=dest)


def delete_skills(names: list[str], root: Path, uninstall: bool = True) -> list[str]:
    """Uninstall skills from all CLIs and archive their output dirs to trash.

    Returns:
        Names that were processed.
    """
    processed = []
    for name in names:
        if uninstall:
            for cli_id in ("claude", "kimi", "cursor", "windsurf", "gemini", "codex", "opencode"):
                uninstall_skill_from_cli(name, cli_id)
        skill_dir = root / "output" / name
        if skill_dir.is_dir():
            dest = TRASH_DIR / f"{name}-{int(time.time())}"
            shutil.move(str(skill_dir), str(dest))
        processed.append(name)
    return processed


# ── projects ──────────────────────────────────────────────────────────────────


def list_projects() -> list[dict[str, Any]]:
    """All tracked projects."""
    data = read_json(PROJECTS_FILE, [])
    return data if isinstance(data, list) else []


def get_project(project_id: str) -> dict[str, Any] | None:
    """One project by id."""
    return next((p for p in list_projects() if p.get("id") == project_id), None)


def save_project(project: dict[str, Any]) -> None:
    """Insert or replace a project entry."""
    projects = [p for p in list_projects() if p.get("id") != project.get("id")]
    projects.append(project)
    write_json(PROJECTS_FILE, projects)


def remove_project(project_id: str) -> bool:
    """Remove a project from tracking (does not touch the filesystem)."""
    projects = list_projects()
    remaining = [p for p in projects if p.get("id") != project_id]
    if len(remaining) == len(projects):
        return False
    write_json(PROJECTS_FILE, remaining)
    return True


def add_project(path: str) -> dict[str, Any]:
    """Register a project directory for tracking."""
    resolved = Path(path).expanduser()
    name = resolved.name or "project"
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "project"
    project = {
        "id": f"pj-{slug}",
        "name": name,
        "path": str(resolved),
        "frameworks": [],
        "lastScan": "—",
        "status": "new",
        "configsFound": 0,
        "addedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_project(project)
    return project


def update_project_scan(
    project_id: str, frameworks: list[dict[str, str]], configs_found: int
) -> None:
    """Record scan results on a project."""
    project = get_project(project_id)
    if not project:
        return
    project["frameworks"] = frameworks
    project["configsFound"] = configs_found
    project["lastScan"] = time.strftime("%Y-%m-%d %H:%M")
    project["status"] = "clean" if configs_found else "stale"
    save_project(project)


# ── config library ────────────────────────────────────────────────────────────


def list_config_entries(root: Path) -> list[dict[str, Any]]:
    """Scan the workspace configs dir for unified config JSON files."""
    entries: list[dict[str, Any]] = []
    configs_root = root / "configs"
    if not configs_root.is_dir():
        return entries
    for path in sorted(configs_root.rglob("*.json")):
        try:
            import json

            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict) or "sources" not in data:
            continue
        rel = path.relative_to(configs_root)
        origin = (
            "scanned"
            if "scanned" in rel.parts
            else "preset"
            if path.parent == configs_root
            else "custom"
        )
        sources = data.get("sources") or []
        source_types = ",".join(
            sorted({s.get("type", "?") for s in sources if isinstance(s, dict)})
        )
        entries.append(
            {
                "id": f"cfg-{path.stem}",
                "name": path.name,
                "path": str(path),
                "framework": str(data.get("name") or path.stem),
                "origin": origin,
                "source": "local",
                "version": str(data.get("version") or "—"),
                "sources": source_types,
                "description": str(data.get("description") or "")[:140],
                "status": "ready",
                "usedIn": [],
            }
        )
    return entries


def list_workflows() -> list[dict[str, str]]:
    """Bundled + user workflow presets."""
    workflows: list[dict[str, str]] = []
    builtin = Path(__file__).resolve().parent.parent / "workflows"
    user = Path.home() / ".config" / "skill-seekers" / "workflows"
    for base in (builtin, user):
        if not base.is_dir():
            continue
        for path in sorted(base.glob("*.yaml")):
            desc = ""
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    desc = str(data.get("description") or "")
            except (OSError, yaml.YAMLError):
                pass
            entry = {"id": path.stem, "desc": desc or "workflow preset"}
            if entry not in workflows:
                workflows.append(entry)
    return workflows


# ── activity feed ─────────────────────────────────────────────────────────────


def log_activity(icon: str, text: str) -> None:
    """Append an activity entry (ring buffer of 50)."""
    items = read_json(ACTIVITY_FILE, [])
    if not isinstance(items, list):
        items = []
    items.insert(
        0,
        {
            "id": f"a-{int(time.time() * 1000)}",
            "time": time.strftime("%H:%M"),
            "icon": icon,
            "text": text,
        },
    )
    write_json(ACTIVITY_FILE, items[:50])


def list_activity() -> list[dict[str, Any]]:
    """Recent activity entries."""
    data = read_json(ACTIVITY_FILE, [])
    return data if isinstance(data, list) else []
