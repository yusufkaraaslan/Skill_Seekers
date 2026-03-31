"""
skill-seekers doctor — Environment health check command.

Runs 8 quick offline checks and prints a diagnostic summary,
similar to `brew doctor` or `flutter doctor`.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Literal


@dataclass
class CheckResult:
    """Result of a single health check."""

    name: str
    status: Literal["pass", "warn", "fail"]
    detail: str
    critical: bool = False
    verbose_detail: str = ""


# ── Core dependency import names (from pyproject.toml dependencies) ──────────
CORE_DEPS = {
    "requests": "requests",
    "beautifulsoup4": "bs4",
    "PyGithub": "github",
    "GitPython": "git",
    "httpx": "httpx",
    "anthropic": "anthropic",
    "PyMuPDF": "fitz",
    "Pillow": "PIL",
    "pydantic": "pydantic",
    "pydantic-settings": "pydantic_settings",
    "python-dotenv": "dotenv",
    "jsonschema": "jsonschema",
    "click": "click",
    "Pygments": "pygments",
}

# ── Optional dependency import names ─────────────────────────────────────────
OPTIONAL_DEPS = {
    "mammoth": "mammoth",
    "ebooklib": "ebooklib",
    "yt-dlp": "yt_dlp",
    "mcp": "mcp",
    "google-generativeai": "google.generativeai",
    "openai": "openai",
    "chromadb": "chromadb",
    "weaviate-client": "weaviate",
    "nbformat": "nbformat",
    "feedparser": "feedparser",
}

# ── API keys to check ────────────────────────────────────────────────────────
API_KEYS = ["ANTHROPIC_API_KEY", "GITHUB_TOKEN", "GOOGLE_API_KEY", "OPENAI_API_KEY", "MOONSHOT_API_KEY"]


def _try_import(module_name: str) -> tuple[bool, str]:
    """Try to import a module and return (success, version_or_error)."""
    try:
        mod = __import__(module_name.split(".")[0])
        version = getattr(mod, "__version__", getattr(mod, "VERSION", "installed"))
        return True, str(version)
    except Exception as e:
        return False, str(e)


def check_python_version() -> CheckResult:
    """Check 1: Python version >= 3.10."""
    v = sys.version_info
    version_str = f"{v.major}.{v.minor}.{v.micro}"
    if v >= (3, 10):
        return CheckResult("Python version", "pass", version_str, critical=True)
    return CheckResult("Python version", "fail", f"{version_str} (requires 3.10+)", critical=True)


def check_package_installed() -> CheckResult:
    """Check 2: skill-seekers package importable with version."""
    try:
        from skill_seekers._version import __version__

        return CheckResult("skill-seekers installed", "pass", f"v{__version__}", critical=True)
    except ImportError:
        return CheckResult(
            "skill-seekers installed", "fail", "Cannot import skill_seekers", critical=True
        )


def check_git() -> CheckResult:
    """Check 3: git available in PATH."""
    git_path = shutil.which("git")
    if not git_path:
        return CheckResult("Git", "warn", "git not found in PATH")
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=5)
        version = result.stdout.strip()
        return CheckResult("Git", "pass", version, verbose_detail=f"Path: {git_path}")
    except Exception as e:
        return CheckResult("Git", "warn", f"git found but error: {e}")


def check_core_deps() -> CheckResult:
    """Check 4: Core dependencies importable."""
    found = []
    missing = []
    details = []
    for pkg_name, import_name in CORE_DEPS.items():
        ok, info = _try_import(import_name)
        if ok:
            found.append(pkg_name)
            details.append(f"  {pkg_name}: {info}")
        else:
            missing.append(pkg_name)
            details.append(f"  {pkg_name}: MISSING")

    if not missing:
        return CheckResult(
            "Core dependencies",
            "pass",
            f"All {len(found)} found",
            critical=True,
            verbose_detail="\n".join(details),
        )
    return CheckResult(
        "Core dependencies",
        "fail",
        f"{len(missing)} missing: {', '.join(missing)}",
        critical=True,
        verbose_detail="\n".join(details),
    )


def check_optional_deps() -> CheckResult:
    """Check 5: Optional dependencies status."""
    found = []
    missing = []
    details = []
    for pkg_name, import_name in OPTIONAL_DEPS.items():
        ok, info = _try_import(import_name)
        if ok:
            found.append(pkg_name)
            details.append(f"  {pkg_name}: {info}")
        else:
            missing.append(pkg_name)
            details.append(f"  {pkg_name}: not installed")

    total = len(OPTIONAL_DEPS)
    if not missing:
        return CheckResult(
            "Optional dependencies",
            "pass",
            f"{total}/{total} installed",
            verbose_detail="\n".join(details),
        )
    return CheckResult(
        "Optional dependencies",
        "warn",
        f"{len(found)}/{total} installed (not installed: {', '.join(missing)})",
        verbose_detail="\n".join(details),
    )


def check_api_keys() -> CheckResult:
    """Check 6: API keys set in environment."""
    set_keys = []
    missing_keys = []
    details = []
    for key in API_KEYS:
        val = os.environ.get(key)
        if val:
            set_keys.append(key)
            masked = val[:4] + "..." + val[-4:] if len(val) > 12 else "***"
            details.append(f"  {key}: {masked}")
        else:
            missing_keys.append(key)
            details.append(f"  {key}: not set")

    if not missing_keys:
        return CheckResult(
            "API keys",
            "pass",
            f"All {len(API_KEYS)} set",
            verbose_detail="\n".join(details),
        )
    if set_keys:
        return CheckResult(
            "API keys",
            "warn",
            f"{len(set_keys)} set ({', '.join(missing_keys)} not set)",
            verbose_detail="\n".join(details),
        )
    return CheckResult(
        "API keys",
        "warn",
        "None set (enhancement features will use LOCAL mode)",
        verbose_detail="\n".join(details),
    )


def check_mcp_server() -> CheckResult:
    """Check 7: MCP server module importable."""
    try:
        from skill_seekers.mcp import server_fastmcp  # noqa: F401

        return CheckResult("MCP server", "pass", "Importable")
    except ImportError as e:
        return CheckResult("MCP server", "warn", f"Not available ({e})")
    except Exception as e:
        return CheckResult("MCP server", "warn", f"Import error: {e}")


def check_output_directory() -> CheckResult:
    """Check 8: Current directory is writable."""
    cwd = os.getcwd()
    if os.access(cwd, os.W_OK):
        return CheckResult("Output directory", "pass", f"{cwd} (writable)", critical=True)
    return CheckResult("Output directory", "fail", f"{cwd} (NOT writable)", critical=True)


def run_all_checks() -> list[CheckResult]:
    """Run all 8 health checks and return results."""
    return [
        check_python_version(),
        check_package_installed(),
        check_git(),
        check_core_deps(),
        check_optional_deps(),
        check_api_keys(),
        check_mcp_server(),
        check_output_directory(),
    ]


STATUS_ICONS = {"pass": "\u2705", "warn": "\u26a0\ufe0f ", "fail": "\u274c"}


def print_report(results: list[CheckResult], verbose: bool = False) -> int:
    """Print formatted report and return exit code."""
    try:
        from skill_seekers._version import __version__

        version = __version__
    except ImportError:
        version = "unknown"

    print()
    print("=" * 50)
    print(f"  Skill Seekers Doctor (v{version})")
    print("=" * 50)
    print()

    for r in results:
        icon = STATUS_ICONS[r.status]
        print(f"  {icon} {r.name} — {r.detail}")
        if verbose and r.verbose_detail:
            for line in r.verbose_detail.split("\n"):
                print(f"      {line}")

    passed = sum(1 for r in results if r.status == "pass")
    warnings = sum(1 for r in results if r.status == "warn")
    errors = sum(1 for r in results if r.status == "fail")

    print()
    print("-" * 50)
    print(f"  {passed} passed, {warnings} warnings, {errors} errors")

    if errors == 0:
        if warnings > 0:
            print("  All critical checks passed with some warnings.")
        else:
            print("  All checks passed!")
    else:
        print("  Some critical checks failed. Fix errors above.")

    print()
    return 1 if errors > 0 else 0


def main() -> int:
    """Entry point for doctor command."""
    parser = argparse.ArgumentParser(
        prog="skill-seekers doctor",
        description="Check environment health and dependencies",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed diagnostic info"
    )
    args = parser.parse_args()

    results = run_all_checks()
    return print_report(results, verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main())
