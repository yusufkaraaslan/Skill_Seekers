"""Manifests for standalone analysis runs under ``output/_analysis/<slug>/``.

Each ``analyze`` job writes one ``manifest.json`` recording what was analysed,
when, which tools ran, and where their JSON results landed. The Analyze page
lists them newest first; the skill detail page shows the subset a run was
explicitly attached to.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .paths import atomic_write, read_json, safe_name, workspace_dir


def analysis_root(root: Path) -> Path:
    """Directory holding one subdirectory per analysis run."""
    return workspace_dir(root, "output") / "_analysis"


def slug_for(value: str) -> str:
    """Filesystem-safe run name derived from the analysed target."""
    return re.sub(r"[^a-z0-9]+", "-", Path(value).name.lower()).strip("-") or "analysis"


def write_manifest(root: Path, slug: str, data: dict[str, Any]) -> Path:
    """Record one analysis run; ``slug`` must be a single path component."""
    safe_name(slug)
    path = analysis_root(root) / slug / "manifest.json"
    atomic_write(path, json.dumps({"slug": slug, **data}, indent=2).encode("utf-8"))
    return path


def list_recent(root: Path) -> list[dict[str, Any]]:
    """All recorded runs, newest first."""
    base = analysis_root(root)
    if not base.is_dir():
        return []
    rows = [read_json(p, {}) for p in base.glob("*/manifest.json")]
    return sorted(
        (r for r in rows if isinstance(r, dict) and r.get("slug")),
        key=lambda r: r.get("startedAt", ""),
        reverse=True,
    )


def list_for_skill(root: Path, skill_id: str) -> list[dict[str, Any]]:
    """Per-tool rows for the runs attached to ``skill_id``, newest first."""
    out: list[dict[str, Any]] = []
    for m in list_recent(root):
        if m.get("attachedTo") != skill_id:
            continue
        for tool, result in (m.get("results") or {}).items():
            out.append(
                {
                    "tool": tool,
                    "count": result.get("count"),
                    "ranAt": m.get("startedAt"),
                    "path": result.get("path"),
                }
            )
    return out
