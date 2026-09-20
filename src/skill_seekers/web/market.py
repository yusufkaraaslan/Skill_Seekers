"""Marketplace browsing for the web UI.

Marketplaces are git repositories containing skill directories (with
SKILL.md) or unified config JSONs. This module clones registered
marketplaces into a local cache and indexes their contents so the UI can
offer one-click installs. Installs copy skill dirs into the local workspace
``output/`` and (optionally) into detected CLIs via the installer.
"""

from __future__ import annotations

import shutil
import subprocess
import time
import hashlib
import tempfile
from pathlib import Path
from typing import Any

from .installer import install_skill_to_cli, installation_path
from .paths import (
    MARKET_CACHE_DIR,
    workspace_dir,
    state_transaction,
    write_json,
    read_json,
    atomic_write,
)
from .registry import parse_frontmatter

CLONE_TIMEOUT = 120


def _git_url_to_dirname(git_url: str) -> str:
    slug = git_url.rstrip("/").removesuffix(".git").replace(":", "/")
    return "-".join(p for p in slug.split("/") if p)[-80:] or "marketplace"


def sync_marketplace(git_url: str, branch: str = "main") -> Path:
    """Clone or pull a marketplace repo into the cache; returns local path."""
    dest = cache_path(git_url, branch)
    status = status_path(git_url, branch)
    if dest.is_dir():
        try:
            subprocess.run(
                ["git", "-C", str(dest), "pull", "--ff-only"],
                capture_output=True,
                timeout=CLONE_TIMEOUT,
                check=True,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            write_json(
                status,
                {
                    "connected": False,
                    "error": str(exc),
                    "lastSync": read_json(status, {}).get("lastSync", "—"),
                },
            )
            raise
        write_json(status, {"connected": True, "lastSync": time.strftime("%Y-%m-%d %H:%M:%S")})
        return dest
    MARKET_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".clone-", dir=MARKET_CACHE_DIR))
    try:
        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                branch,
                "--",
                git_url,
                str(staging / "repo"),
            ],
            capture_output=True,
            timeout=CLONE_TIMEOUT,
            check=True,
        )
        with state_transaction():
            if not dest.exists():
                (staging / "repo").rename(dest)
        write_json(status, {"connected": True, "lastSync": time.strftime("%Y-%m-%d %H:%M:%S")})
    except (OSError, subprocess.SubprocessError) as exc:
        write_json(status, {"connected": False, "error": str(exc), "lastSync": "—"})
        raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return dest


def cache_path(git_url: str, branch: str = "main") -> Path:
    """Stable cache identity including the requested branch."""
    digest = hashlib.sha256(f"{git_url}\n{branch}".encode()).hexdigest()[:12]
    return MARKET_CACHE_DIR / f"{_git_url_to_dirname(git_url)}-{digest}"


def status_path(git_url: str, branch: str = "main") -> Path:
    """Status sidecar beside the cache dir (with_suffix would truncate at the first dot)."""
    cache = cache_path(git_url, branch)
    return cache.with_name(cache.name + ".status.json")


def cache_status(git_url: str, branch: str = "main") -> dict:
    """Last completed synchronization, without network access."""
    return read_json(status_path(git_url, branch), {"connected": False, "lastSync": "never"})


def browse_marketplace(repo_path: Path, marketplace_id: str) -> list[dict[str, Any]]:
    """Index skills and configs contained in a marketplace checkout."""
    items: list[dict[str, Any]] = []
    if not repo_path.is_dir():
        return items
    seen = set()
    for skill_md in sorted(repo_path.rglob("SKILL.md")):
        skill_dir = skill_md.parent
        if not skill_md.resolve().is_relative_to(repo_path.resolve()):
            continue
        if any(part.startswith(".git") for part in skill_dir.parts):
            continue
        try:
            raw = skill_md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        front, _ = parse_frontmatter(raw)
        name = str(front.get("name") or skill_dir.name)
        if name in seen:
            continue
        seen.add(name)
        try:
            updated = time.strftime("%Y-%m-%d", time.localtime(skill_md.stat().st_mtime))
        except OSError:
            updated = "—"
        items.append(
            {
                "id": f"{marketplace_id}:{name}",
                "name": name,
                "author": str(front.get("author") or repo_path.name),
                "desc": str(front.get("description") or "")[:200],
                "market": marketplace_id,
                "installs": 0,
                "stars": 0,
                "updated": updated,
                "tags": list(front.get("tags") or [])[:4]
                if isinstance(front.get("tags"), list)
                else [],
                "path": str(skill_dir),
                "kind": "skill",
            }
        )
    for cfg in sorted(repo_path.rglob("*.json")):
        if not cfg.resolve().is_relative_to(repo_path.resolve()):
            continue
        if any(part.startswith(".git") for part in cfg.parts):
            continue
        import json

        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict) or "sources" not in data:
            continue
        name = str(data.get("name") or cfg.stem)
        if name in seen:
            continue
        seen.add(name)
        items.append(
            {
                "id": f"{marketplace_id}:{name}",
                "name": name,
                "author": repo_path.name,
                "desc": str(data.get("description") or "")[:200],
                "market": marketplace_id,
                "installs": 0,
                "stars": 0,
                "updated": "—",
                "tags": ["config"],
                "path": str(cfg),
                "kind": "config",
            }
        )
    return items


@state_transaction()
def install_marketplace_item(
    item_path: Path, kind: str, root: Path, clis: list[str], replace: bool = False
) -> Path:
    """Install a marketplace item into the workspace (and CLIs for skills).

    Returns:
        Path to the installed artifact in the workspace.
    """
    if kind == "config":
        dest_dir = workspace_dir(root, "configs")
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / item_path.name
        if dest.exists() and not replace:
            raise FileExistsError(f"{dest} already exists; enable replacement to overwrite it")
        atomic_write(dest, item_path.read_bytes())
        return dest
    out_dir = workspace_dir(root, "output")
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / item_path.name
    if dest.exists():
        # Replacing a local build is separate from replacing a CLI installation.
        raise FileExistsError(f"{dest} already exists; archive or rename the local skill first")
    for file in item_path.rglob("*"):
        if file.is_symlink():
            raise ValueError("Marketplace skills containing symlinks cannot be installed")
    for cli in clis:
        target = installation_path(item_path.name, cli)
        if target.is_symlink() or (target.exists() and not replace):
            raise FileExistsError(f"{target} already exists; enable replacement to overwrite it")
    staging = Path(tempfile.mkdtemp(prefix=".market-install-", dir=out_dir))
    try:
        shutil.copytree(item_path, staging / "skill")
        (staging / "skill").rename(dest)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    for cli in clis:
        install_skill_to_cli(dest, cli, replace=replace)
    return dest
