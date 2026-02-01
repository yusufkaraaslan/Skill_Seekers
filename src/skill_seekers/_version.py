"""
Single source of truth for skill-seekers version.

This module dynamically reads the version from pyproject.toml to avoid
version mismatches across multiple files.
"""

import sys
from pathlib import Path

# Use tomllib (built-in) for Python 3.11+, tomli (package) for earlier versions
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        # Fallback if tomli not available
        tomllib = None


def get_version() -> str:
    """
    Read version from pyproject.toml.

    Returns:
        Version string (e.g., "2.8.0")
    """
    if tomllib is None:
        # Fallback if TOML library not available
        return "2.8.0"  # Hardcoded fallback

    try:
        # Get path to pyproject.toml (3 levels up from this file)
        repo_root = Path(__file__).parent.parent.parent
        pyproject_path = repo_root / "pyproject.toml"

        if not pyproject_path.exists():
            # Fallback for installed package
            return "2.8.0"  # Hardcoded fallback

        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)

        return pyproject_data["project"]["version"]

    except Exception:
        # Fallback if anything goes wrong
        return "2.8.0"  # Hardcoded fallback


__version__ = get_version()
