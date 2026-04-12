"""Centralized default configuration loader.

Loads defaults.json once at import time and exposes every value as a module-level
constant.  All modules that need a default MUST import from here — never hardcode
a magic number or duplicate a value from constants.py.

Usage::

    from skill_seekers.cli.defaults import DEFAULTS, get_default

    # Full section access
    rate_limit = DEFAULTS["scraping"]["rate_limit"]

    # Safe nested lookup with fallback
    rate_limit = get_default("scraping.rate_limit", 0.5)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DEFAULTS_PATH = Path(__file__).parent / "defaults.json"

with open(_DEFAULTS_PATH, encoding="utf-8") as _f:
    DEFAULTS: dict[str, Any] = json.load(_f)


def get_default(dotted_key: str, fallback: Any = None) -> Any:
    """Look up a value using dot-separated keys.

    Args:
        dotted_key: e.g. ``"scraping.rate_limit"`` or ``"limits.api_content_limit"``
        fallback: returned when any segment is missing

    Returns:
        The value from defaults.json, or *fallback* if the path does not exist.
    """
    obj: Any = DEFAULTS
    for part in dotted_key.split("."):
        if isinstance(obj, dict) and part in obj:
            obj = obj[part]
        else:
            return fallback
    return obj
