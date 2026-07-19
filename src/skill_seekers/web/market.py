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
from pathlib import Path
from typing import Any

from .installer import install_skill_to_cli
from .paths import MARKET_CACHE_DIR
from .registry import parse_frontmatter

CLONE_TIMEOUT = 120


def _git_url_to_dirname(git_url: str) -> str:
    slug = git_url.rstrip("/").removesuffix(".git").replace(":", "/")
    return "-".join(p for p in slug.split("/") if p)[-80:] or "marketplace"


def sync_marketplace(git_url: str, branch: str = "main") -> Path:
    """Clone or pull a marketplace repo into the cache; returns local path."""
    dest = MARKET_CACHE_DIR / _git_url_to_dirname(git_url)
    if dest.is_dir():
        import contextlib

        with contextlib.suppress(OSError, subprocess.TimeoutExpired):
            subprocess.run(
                ["git", "-C", str(dest), "pull", "--ff-only"],
                capture_output=True,
                timeout=CLONE_TIMEOUT,
                check=False,
            )
        return dest
    MARKET_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", branch, git_url, str(dest)],
        capture_output=True,
        timeout=CLONE_TIMEOUT,
        check=True,
    )
    return dest


def browse_marketplace(repo_path: Path, marketplace_id: str) -> list[dict[str, Any]]:
    """Index skills and configs contained in a marketplace checkout."""
    items: list[dict[str, Any]] = []
    if not repo_path.is_dir():
        return items
    seen = set()
    for skill_md in sorted(repo_path.rglob("SKILL.md")):
        skill_dir = skill_md.parent
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


def install_marketplace_item(item_path: Path, kind: str, root: Path, clis: list[str]) -> Path:
    """Install a marketplace item into the workspace (and CLIs for skills).

    Returns:
        Path to the installed artifact in the workspace.
    """
    if kind == "config":
        dest_dir = root / "configs"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / item_path.name
        shutil.copy2(item_path, dest)
        return dest
    out_dir = root / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / item_path.name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(item_path, dest)
    for cli in clis:
        install_skill_to_cli(dest, cli)
    return dest
