"""Shared state locations for the Skill Seekers web UI.

All UI-level state lives under ``~/.skill-seekers/ui/`` so the web layer
never writes into the user's project workspace except through the normal
toolchain outputs (``output/``, ``configs/``).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

UI_STATE_DIR = Path(os.environ.get("SKILL_SEEKERS_UI_DIR", Path.home() / ".skill-seekers" / "ui"))

PROJECTS_FILE = UI_STATE_DIR / "projects.json"
JOBS_FILE = UI_STATE_DIR / "jobs.json"
ACTIVITY_FILE = UI_STATE_DIR / "activity.json"
SKILLS_META_FILE = UI_STATE_DIR / "skills.json"
SETTINGS_FILE = UI_STATE_DIR / "settings.json"
TRASH_DIR = UI_STATE_DIR / "trash"
MARKET_CACHE_DIR = UI_STATE_DIR / "marketplace_cache"

DEFAULT_SETTINGS: dict[str, Any] = {
    "output_dir": "output",
    "configs_dir": "configs",
    "default_agent": "claude",
    "auto_upload": False,
    "publish_configs": False,
    "watch_mode": False,
    "enabled_clis": [],
}


def ensure_dirs() -> None:
    """Create the UI state directory tree if missing."""
    UI_STATE_DIR.mkdir(parents=True, exist_ok=True)
    TRASH_DIR.mkdir(parents=True, exist_ok=True)
    MARKET_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def read_json(path: Path, default: Any) -> Any:
    """Read a JSON file, returning ``default`` when missing or corrupt."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path: Path, data: Any) -> None:
    """Atomically write JSON to ``path``."""
    ensure_dirs()
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    tmp.replace(path)


def load_settings() -> dict[str, Any]:
    """Load UI settings merged over defaults."""
    stored = read_json(SETTINGS_FILE, {})
    merged = dict(DEFAULT_SETTINGS)
    if isinstance(stored, dict):
        merged.update(stored)
    return merged


def save_settings(settings: dict[str, Any]) -> None:
    """Persist UI settings."""
    write_json(SETTINGS_FILE, settings)
