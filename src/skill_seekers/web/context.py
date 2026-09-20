"""Shared handles the route modules need from create_app()."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .jobs import Job, JobManager


@dataclass(frozen=True)
class HudContext:
    root: Path
    jobs: JobManager
    submit_job: Callable[..., Job]
    skill_dir_for: Callable[[str], Path]
    require_seeker: Callable[[list[str]], None]
    capabilities: Callable[[], dict[str, Any]]
    validate_targets: Callable[[list[str]], None]
    cached_detect_clis: Callable[[], list[dict[str, Any]]]
