"""Manifests for standalone analysis runs under ``output/_analysis/<slug>/``.

Each ``analyze`` job writes one ``manifest.json`` recording what was analysed,
when, which tools ran, and where their JSON results landed. The Analyze page
lists them newest first; the skill detail page shows the subset a run was
explicitly attached to.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .paths import atomic_write, read_json, safe_name, workspace_dir


def analysis_root(root: Path) -> Path:
    """Directory holding one subdirectory per analysis run."""
    return workspace_dir(root, "output") / "_analysis"


def slug_for(value: str) -> str:
    """Filesystem-safe run name for a target.

    The basename alone collides (``/a/src`` and ``/b/src``), which would let one
    target's run directory and manifest overwrite another's, so the full target
    string is hashed into the suffix.
    """
    stem = re.sub(r"[^a-z0-9]+", "-", Path(value).name.lower()).strip("-") or "analysis"
    return f"{stem}-{hashlib.sha256(value.encode('utf-8')).hexdigest()[:8]}"


def read_manifest(root: Path, slug: str) -> dict[str, Any]:
    """The manifest already recorded for ``slug``, or ``{}`` if there is none.

    A run of one tool merges into whatever earlier runs of the other tools
    recorded, so the reader has to tolerate a missing or malformed file.
    """
    safe_name(slug)
    data = read_json(analysis_root(root) / slug / "manifest.json", {})
    return data if isinstance(data, dict) else {}


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
