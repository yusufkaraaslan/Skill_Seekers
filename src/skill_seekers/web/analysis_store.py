"""Per-skill static analysis run history.

Placeholder for Task 4, which will persist and read back C3.x analysis runs
(pattern detection, test example extraction, etc.) scoped to a skill. Until
then the skill detail endpoint reports no analysis history.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def list_for_skill(root: Path, skill_id: str) -> list[dict[str, Any]]:  # noqa: ARG001
    """Analysis runs recorded for a skill; always empty until Task 4."""
    return []
