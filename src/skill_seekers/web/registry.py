"""Discovery of skills, projects, configs and activity for the web UI.

Skills are discovered from the workspace ``output/`` directory (any folder
with a SKILL.md), enriched with:

- frontmatter parsed from SKILL.md (name/description)
- a quality score from the existing SkillQualityChecker (cached by mtime)
- install state across detected CLIs (by resolved installation paths)
- provenance sidecars (``.seeker-meta.json``) written by create jobs
- user overrides (scope/project/tags) stored in the UI state dir
"""

from __future__ import annotations

import re
import shutil
import time
import hashlib
import uuid
from pathlib import Path
from typing import Any

import yaml

from .paths import (
    ACTIVITY_FILE,
    PROJECTS_FILE,
    SKILLS_META_FILE,
    TRASH_DIR,
    read_json,
    write_json,
    update_json,
    state_transaction,
    workspace_dir,
    safe_name,
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


def list_skill_files(skill_dir: Path) -> list[dict[str, str]]:
    """List at most 200 supporting files for a skill detail view."""
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
    key = str(skill_dir.resolve())
    cached = meta_cache.get("_quality_cache", {}).get(key)
    if cached and abs(cached.get("mtime", 0) - mtime) < 1e-6:
        return int(cached.get("score", 0))
    score = 75  # neutral default when the checker cannot run
    try:
        from skill_seekers.cli.quality_checker import SkillQualityChecker

        report = SkillQualityChecker(skill_dir).check_all()
        score = int(round(report.quality_score))
    except Exception:  # noqa: BLE001 — quality is best-effort metadata
        pass
    meta_cache.setdefault("_quality_cache", {})[key] = {"mtime": mtime, "score": score}
    return score


def skill_quality_breakdown(skill_dir: Path) -> list[dict[str, Any]]:
    """Per-dimension scores the skill page charts; falls back to neutral values.

    The chart's four labels are the design's, not the checker's — map each
    label to the real ``QualityIssue.category`` it reflects: ``content``
    covers YAML-frontmatter presence (plus a couple of unrelated content
    checks), ``enhancement`` covers code-example/section counts.
    """
    label_to_category = {
        "frontmatter": "content",
        "structure": "structure",
        "examples": "enhancement",
        "links": "links",
    }
    try:
        from skill_seekers.cli.quality_checker import SkillQualityChecker

        report = SkillQualityChecker(skill_dir).check_all()
        issues = report.errors + report.warnings
        by_cat: dict[str, int] = {}
        for issue in issues:
            by_cat[issue.category] = by_cat.get(issue.category, 0) + 1
        return [
            {"label": label, "score": max(0, 100 - 12 * by_cat.get(category, 0))}
            for label, category in label_to_category.items()
        ]
    except Exception:  # noqa: BLE001 — quality is best-effort metadata
        return [{"label": label, "score": 75} for label in label_to_category]


def discover_skills(root: Path, enabled_clis: list[str] | None = None) -> list[dict[str, Any]]:
    """Find all built skills under ``root/output`` and describe them for the UI."""
    out_dir = workspace_dir(root, "output")
    meta = read_json(SKILLS_META_FILE, {})
    if not isinstance(meta, dict):
        meta = {}
    overrides: dict[str, Any] = meta.get("skills", {})
    skills: list[dict[str, Any]] = []
    if out_dir.is_dir():
        for child in sorted(out_dir.iterdir()):
            if not child.is_dir() or child.name.endswith("_data") or child.name.startswith("."):
                continue
            if not child.resolve().is_relative_to(out_dir) or (child / "SKILL.md").is_symlink():
                continue
            skill_md = child / "SKILL.md"
            if not skill_md.is_file():
                continue
            entry = _describe_skill(
                child,
                overrides.get(skill_id_for(child), overrides.get(child.name, {})),
                meta,
                enabled_clis,
            )
            entry["id"] = skill_id_for(child)
            skills.append(entry)
    # Skills installed globally but not present in this workspace's output/
    for cli_name, cli_dir in _global_only_skills(out_dir):
        skills.append(
            _describe_global_only(
                cli_name,
                cli_dir,
                overrides.get(skill_id_for(cli_dir), {}),
                meta,
                enabled_clis,
                root,
            )
        )
    install_index = installation_index()
    for entry in skills:
        location = Path(entry["dir"])
        entry["id"] = skill_id_for(location)
        content_path = location if location.is_file() else location / "SKILL.md"
        raw = content_path.read_bytes()
        entry["revision"] = hashlib.sha256(raw).hexdigest()
        entry["contentTruncated"] = len(raw) > MAX_CONTENT_BYTES
        entry["content"] = raw[:MAX_CONTENT_BYTES].decode("utf-8", errors="replace")
        entry["editable"] = entry["origin"] == "seeker" and location.is_dir()
        entry["installations"] = install_index.get(str(location.resolve()), [])
        entry["installs"] = sorted({i["cli"] for i in entry["installations"]})
    quality = meta.get("_quality_cache", {})
    if quality:

        def merge_cache(current):
            current.setdefault("_quality_cache", {}).update(quality)
            return current

        update_json(SKILLS_META_FILE, merge_cache, {})
    return skills


def skill_id_for(path: Path) -> str:
    """Stable identity for a particular skill location, independent of its name."""
    return "sk-" + hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:20]


def resolve_skill(root: Path, skill_id: str) -> Path:
    """Resolve a registered ID (or an unambiguous legacy name), never a path."""
    try:
        safe_name(skill_id)
    except ValueError:
        raise KeyError(skill_id) from None
    out = workspace_dir(root, "output")
    candidates = []
    if out.is_dir():
        candidates.extend(
            p
            for p in out.iterdir()
            if p.is_dir()
            and not p.name.startswith(".")
            and (p / "SKILL.md").is_file()
            and not (p / "SKILL.md").is_symlink()
            and p.resolve().is_relative_to(out)
        )
    candidates.extend(p for _, p in _global_only_skills(out))
    exact = [p for p in candidates if skill_id_for(p) == skill_id]
    legacy = [p for p in candidates if (p.stem if p.is_file() else p.name) == skill_id]
    matches = exact or legacy
    if len(matches) != 1:
        raise KeyError(skill_id)
    return matches[0]


def installation_index() -> dict[str, list[dict[str, str]]]:
    """Index actual locations and their recorded source without name matching."""
    from .clis import get_cli_specs, iter_installed_skills

    index: dict[str, list[dict[str, str]]] = {}
    for cli in get_cli_specs():
        for _, location in iter_installed_skills(cli):
            marker = (
                location / ".seeker-install.json"
                if location.is_dir()
                else location.with_suffix(location.suffix + ".seeker-install.json")
            )
            metadata = read_json(marker, {})
            own_path = str(location.resolve())
            source = metadata.get("source")
            index.setdefault(own_path, []).append(
                {"cli": cli.id, "path": str(location), "owned": str(source == own_path).lower()}
            )
            if isinstance(source, str) and source != own_path:
                index.setdefault(source, []).append(
                    {"cli": cli.id, "path": str(location), "owned": "true"}
                )
    return index


def installations_for(source: Path) -> list[dict[str, str]]:
    """Explicit install locations; never infer ownership from a shared name."""
    return installation_index().get(str(source.resolve()), [])


def _global_only_skills(out_dir: Path) -> list[tuple[str, Path]]:
    """All distinct installed locations across every supported CLI."""
    from .clis import iter_installed_skills, get_cli_specs

    local = {p.resolve() for p in out_dir.iterdir() if p.is_dir()} if out_dir.is_dir() else set()
    found = {}
    for spec in get_cli_specs():
        for name, path in iter_installed_skills(spec):
            resolved = path.resolve()
            if resolved in local:
                continue
            # A copy Skill Seekers installed from a workspace skill is that
            # skill's installation, not a second skill.
            marker = (
                path / ".seeker-install.json"
                if path.is_dir()
                else path.with_suffix(path.suffix + ".seeker-install.json")
            )
            source = read_json(marker, {}).get("source")
            if isinstance(source, str) and Path(source).resolve() in local:
                continue
            found.setdefault(resolved, (name, path))
    return list(found.values())


def _read_sidecar(skill_dir: Path) -> dict[str, Any]:
    sidecar = skill_dir / ".seeker-meta.json"
    data = read_json(sidecar, {})
    return data if isinstance(data, dict) else {}


def _describe_skill(
    skill_dir: Path,
    override: dict[str, Any],
    meta_cache: dict[str, Any],
    _enabled_clis: list[str] | None,
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
    source_type = override.get("source_type") or sidecar.get("source_type") or "docs"
    if source_type not in KNOWN_SOURCE_TYPES:
        source_type = "docs"
    return {
        "id": skill_dir.name,
        "name": name,
        "description": description,
        "scope": override.get("scope", "global"),
        "projectId": override.get("project_id"),
        "installs": [],
        "source": override.get("source") or sidecar.get("source") or str(skill_dir),
        "sourceType": source_type,
        "version": str(front.get("version") or sidecar.get("version") or "1.0.0"),
        "sizeKb": _dir_size_kb(skill_dir),
        "updatedAt": updated,
        "quality": _quality_for(skill_dir, meta_cache),
        "tags": override.get("tags", []),
        "files": list_skill_files(skill_dir),
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
    _enabled_clis: list[str] | None,
    root: Path,
) -> dict[str, Any]:
    skill_md = skill_dir if skill_dir.is_file() else skill_dir / "SKILL.md"
    raw = skill_md.read_text(encoding="utf-8", errors="replace") if skill_md.is_file() else ""
    front, _ = parse_frontmatter(raw)
    sidecar = _read_sidecar(skill_dir)
    if len(raw.encode("utf-8")) > MAX_CONTENT_BYTES:
        raw = raw[:MAX_CONTENT_BYTES]
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
        "installs": [],
        "source": override.get("source") or sidecar.get("source") or str(skill_dir),
        "sourceType": source_type,
        "version": str(front.get("version") or sidecar.get("version") or "1.0.0"),
        "sizeKb": _dir_size_kb(skill_dir)
        if skill_dir.is_dir()
        else max(1, round(skill_dir.stat().st_size / 1024)),
        "updatedAt": time.strftime("%Y-%m-%d", time.localtime(skill_md.stat().st_mtime))
        if skill_md.is_file()
        else "—",
        "quality": _quality_for(skill_dir, meta_cache) if skill_dir.is_dir() else 0,
        "tags": override.get("tags", []),
        "files": list_skill_files(skill_dir) if skill_dir.is_dir() else [],
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
        skill_dir.resolve().relative_to(workspace_dir(root, "output"))
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
    return classify_origin(resolve_skill(root, skill_id), root)[0]


@state_transaction()
def set_skill_override(name: str, **fields: Any) -> None:
    """Persist user overrides (scope/project/tags) for a skill."""
    meta = read_json(SKILLS_META_FILE, {})
    if not isinstance(meta, dict):
        meta = {}
    entry = meta.setdefault("skills", {}).setdefault(name, {})
    entry.update(fields)
    write_json(SKILLS_META_FILE, meta)


def move_skills(names: list[str], dest: str) -> None:
    """Change scope of skills ('global' or a project id)."""
    for name in names:
        if dest == "global":
            set_skill_override(name, scope="global", project_id=None)
        else:
            set_skill_override(name, scope="project", project_id=dest)


@state_transaction()
def delete_skills(names: list[str], root: Path, uninstall: bool = True) -> list[str]:
    """Uninstall skills from all CLIs and archive their output dirs to trash.

    Returns:
        Names that were processed.
    """
    processed = []
    resolved = [(name, resolve_skill(root, name)) for name in names]
    for name, skill_dir in resolved:
        if classify_origin(skill_dir, root)[0] != "seeker":
            raise ValueError("Cannot archive an externally managed skill")
    for name, skill_dir in resolved:
        if uninstall:
            for install in installations_for(skill_dir):
                if (
                    install["owned"] == "true"
                    and Path(install["path"]).resolve() != skill_dir.resolve()
                ):
                    location = Path(install["path"])
                    # Compatibility locations may be shared by several CLIs.
                    # Remove this exact owned copy, never a same-name default path.
                    if location.is_dir() and not location.is_symlink():
                        shutil.rmtree(location)
                    elif location.is_file():
                        location.unlink()
                        location.with_suffix(location.suffix + ".seeker-install.json").unlink(
                            missing_ok=True
                        )
        if skill_dir.is_dir():
            archive_id = uuid.uuid4().hex
            dest = TRASH_DIR / archive_id
            dest.mkdir(parents=True)
            write_json(
                dest / "manifest.json",
                {
                    "id": archive_id,
                    "name": skill_dir.name,
                    "original": str(skill_dir.resolve()),
                    "root": str(root.resolve()),
                    "archivedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
            )
            shutil.move(str(skill_dir), str(dest / "skill"))
        processed.append(name)
    from .clis import invalidate_installed_cache

    invalidate_installed_cache()
    return processed


def list_archived(root: Path) -> list[dict[str, Any]]:
    """List recoverable skills archived by this workspace."""
    if not TRASH_DIR.is_dir():
        return []
    return [
        data
        for p in TRASH_DIR.glob("*/manifest.json")
        if (data := read_json(p, {})).get("root") == str(root.resolve())
        and (p.parent / "skill" / "SKILL.md").is_file()
    ]


@state_transaction()
def restore_skill(root: Path, archive_id: str) -> Path:
    """Restore an archived skill, refusing to replace anything already present."""
    safe_name(archive_id)
    data = next((a for a in list_archived(root) if a["id"] == archive_id), None)
    if data is None:
        raise KeyError(archive_id)
    dest = Path(data["original"])
    if dest.exists():
        raise FileExistsError(f"Cannot restore: {dest} already exists")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(TRASH_DIR / archive_id / "skill"), str(dest))
    from .clis import invalidate_installed_cache

    invalidate_installed_cache()
    return dest


# ── projects ──────────────────────────────────────────────────────────────────


def list_projects() -> list[dict[str, Any]]:
    """All tracked projects."""
    data = read_json(PROJECTS_FILE, [])
    return data if isinstance(data, list) else []


def get_project(project_id: str) -> dict[str, Any] | None:
    """One project by id."""
    return next((p for p in list_projects() if p.get("id") == project_id), None)


@state_transaction()
def save_project(project: dict[str, Any]) -> None:
    """Insert or replace a project entry."""
    projects = [p for p in list_projects() if p.get("id") != project.get("id")]
    projects.append(project)
    write_json(PROJECTS_FILE, projects)


@state_transaction()
def remove_project(project_id: str) -> bool:
    """Remove a project from tracking (does not touch the filesystem)."""
    projects = list_projects()
    remaining = [p for p in projects if p.get("id") != project_id]
    if len(remaining) == len(projects):
        return False
    write_json(PROJECTS_FILE, remaining)
    meta = read_json(SKILLS_META_FILE, {})
    for fields in meta.get("skills", {}).values():
        if fields.get("project_id") == project_id:
            fields.update(scope="global", project_id=None)
    write_json(SKILLS_META_FILE, meta)
    return True


@state_transaction()
def add_project(path: str) -> dict[str, Any]:
    """Register a project directory for tracking."""
    resolved = Path(path).expanduser().resolve()
    existing = next((p for p in list_projects() if Path(p["path"]).resolve() == resolved), None)
    if existing:
        return existing
    name = resolved.name or "project"
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "project"
    project = {
        "id": f"pj-{slug}-{hashlib.sha256(str(resolved).encode()).hexdigest()[:10]}",
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


@state_transaction()
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


def config_id_for(path: Path) -> str:
    """Stable identity for a config file location, independent of its name."""
    return "cfg-" + hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:20]


def resolve_config(root: Path, cfg_id: str) -> Path:
    """Map a cfg-… id back to a file in the workspace or a fetched source cache."""
    safe_name(cfg_id)
    from skill_seekers.services.git_repo import GitConfigRepo

    roots = [workspace_dir(root, "configs")]
    cache = GitConfigRepo().cache_dir
    if cache.is_dir():
        roots.extend(p for p in cache.iterdir() if p.is_dir())
    for base in roots:
        if not base.is_dir():
            continue
        for path in base.rglob("*.json"):
            if config_id_for(path) == cfg_id:
                return path
    raise KeyError(cfg_id)


def list_config_entries(
    root: Path, config_dir: Path | None = None, source_id: str = "local"
) -> list[dict[str, Any]]:
    """Scan the workspace configs dir for unified config JSON files."""
    entries: list[dict[str, Any]] = []
    configs_root = config_dir or workspace_dir(root, "configs")
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
                "id": config_id_for(path),
                "name": path.name,
                "path": str(path),
                "framework": str(data.get("name") or path.stem),
                "origin": origin,
                "source": (
                    read_json(path.with_name(f".{path.name}.seeker-source.json"), {}).get(
                        "source", source_id
                    )
                    if source_id == "local"
                    else source_id
                ),
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


@state_transaction()
def log_activity(icon: str, text: str) -> None:
    """Append an activity entry (ring buffer of 50)."""
    items = read_json(ACTIVITY_FILE, [])
    if not isinstance(items, list):
        items = []
    items.insert(
        0,
        {
            "id": f"a-{uuid.uuid4().hex}",
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
