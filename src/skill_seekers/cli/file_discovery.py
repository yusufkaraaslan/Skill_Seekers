"""Pruned filesystem traversal shared by local source and metadata extractors."""

import os
from fnmatch import fnmatch
from pathlib import Path

COMMON_EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    "build",
    "dist",
    "*.egg-info",
}


def walk_project(root: Path, excluded_dirs=(), gitignore_spec=None):
    """Yield directories/files without descending into dependencies or environments.

    Detect virtual environments by pyvenv.cfg, including custom names such as
    venv_e2e. Match directory ignore rules before os.walk visits their children.
    """
    root = Path(root).resolve()
    excluded = COMMON_EXCLUDED_DIRS | set(excluded_dirs)
    for directory, subdirs, files in os.walk(root, followlinks=False):
        current = Path(directory)
        subdirs[:] = sorted(
            name
            for name in subdirs
            if not any(fnmatch(name, pattern) for pattern in excluded)
            and not (current / name / "pyvenv.cfg").is_file()
            and not (
                gitignore_spec
                and gitignore_spec.match_file((current / name).relative_to(root).as_posix() + "/")
            )
        )
        yield current, files
