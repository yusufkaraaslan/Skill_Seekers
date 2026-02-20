"""GitHub command argument definitions.

This module defines ALL arguments for the github command in ONE place.
Both github_scraper.py (standalone) and parsers/github_parser.py (unified CLI)
import and use these definitions.

This ensures the parsers NEVER drift out of sync.
"""

import argparse
from typing import Any

# GitHub-specific argument definitions as data structure
GITHUB_ARGUMENTS: dict[str, dict[str, Any]] = {
    # Core GitHub options
    "repo": {
        "flags": ("--repo",),
        "kwargs": {
            "type": str,
            "help": "GitHub repository (owner/repo)",
            "metavar": "OWNER/REPO",
        },
    },
    "config": {
        "flags": ("--config",),
        "kwargs": {
            "type": str,
            "help": "Path to config JSON file",
            "metavar": "FILE",
        },
    },
    "token": {
        "flags": ("--token",),
        "kwargs": {
            "type": str,
            "help": "GitHub personal access token",
            "metavar": "TOKEN",
        },
    },
    "name": {
        "flags": ("--name",),
        "kwargs": {
            "type": str,
            "help": "Skill name (default: repo name)",
            "metavar": "NAME",
        },
    },
    "description": {
        "flags": ("--description",),
        "kwargs": {
            "type": str,
            "help": "Skill description",
            "metavar": "TEXT",
        },
    },
    # Content options
    "no_issues": {
        "flags": ("--no-issues",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip GitHub issues",
        },
    },
    "no_changelog": {
        "flags": ("--no-changelog",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip CHANGELOG",
        },
    },
    "no_releases": {
        "flags": ("--no-releases",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip releases",
        },
    },
    "max_issues": {
        "flags": ("--max-issues",),
        "kwargs": {
            "type": int,
            "default": 100,
            "help": "Max issues to fetch (default: 100)",
            "metavar": "N",
        },
    },
    # Control options
    "scrape_only": {
        "flags": ("--scrape-only",),
        "kwargs": {
            "action": "store_true",
            "help": "Only scrape, don't build skill",
        },
    },
    # Enhancement options
    "enhance_level": {
        "flags": ("--enhance-level",),
        "kwargs": {
            "type": int,
            "choices": [0, 1, 2, 3],
            "default": 2,
            "help": (
                "AI enhancement level (auto-detects API vs LOCAL mode): "
                "0=disabled, 1=SKILL.md only, 2=+architecture/config (default), 3=full enhancement. "
                "Mode selection: uses API if ANTHROPIC_API_KEY is set, otherwise LOCAL (Claude Code)"
            ),
            "metavar": "LEVEL",
        },
    },
    "api_key": {
        "flags": ("--api-key",),
        "kwargs": {
            "type": str,
            "help": "Anthropic API key for --enhance (or set ANTHROPIC_API_KEY)",
            "metavar": "KEY",
        },
    },
    # Enhancement Workflow arguments (NEW - Phase 2)
    "enhance_workflow": {
        "flags": ("--enhance-workflow",),
        "kwargs": {
            "action": "append",
            "help": "Apply enhancement workflow (file path or preset: security-focus, minimal, api-documentation, architecture-comprehensive). Can use multiple times to chain workflows.",
            "metavar": "WORKFLOW",
        },
    },
    "enhance_stage": {
        "flags": ("--enhance-stage",),
        "kwargs": {
            "action": "append",
            "help": "Add inline enhancement stage ('name:prompt'). Can use multiple times.",
            "metavar": "STAGE",
        },
    },
    "var": {
        "flags": ("--var",),
        "kwargs": {
            "action": "append",
            "help": "Override workflow variable ('key=value'). Can use multiple times.",
            "metavar": "VAR",
        },
    },
    "workflow_dry_run": {
        "flags": ("--workflow-dry-run",),
        "kwargs": {
            "action": "store_true",
            "help": "Preview workflow without executing (requires --enhance-workflow)",
        },
    },
    # Mode options
    "non_interactive": {
        "flags": ("--non-interactive",),
        "kwargs": {
            "action": "store_true",
            "help": "Non-interactive mode for CI/CD (fail fast on rate limits)",
        },
    },
    "profile": {
        "flags": ("--profile",),
        "kwargs": {
            "type": str,
            "help": "GitHub profile name to use from config",
            "metavar": "NAME",
        },
    },
    "local_repo_path": {
        "flags": ("--local-repo-path",),
        "kwargs": {
            "type": str,
            "help": "Path to local clone of the repository for unlimited C3.x analysis (bypasses GitHub API file limits)",
            "metavar": "PATH",
        },
    },
}


def add_github_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all github command arguments to a parser.

    This is the SINGLE SOURCE OF TRUTH for github arguments.
    Used by:
    - github_scraper.py (standalone scraper)
    - parsers/github_parser.py (unified CLI)

    Args:
        parser: The ArgumentParser to add arguments to

    Example:
        >>> parser = argparse.ArgumentParser()
        >>> add_github_arguments(parser)  # Adds all github args
    """
    for arg_name, arg_def in GITHUB_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = arg_def["kwargs"]
        parser.add_argument(*flags, **kwargs)


def get_github_argument_names() -> set:
    """Get the set of github argument destination names.

    Returns:
        Set of argument dest names
    """
    return set(GITHUB_ARGUMENTS.keys())


def get_github_argument_count() -> int:
    """Get the total number of github arguments.

    Returns:
        Number of arguments
    """
    return len(GITHUB_ARGUMENTS)
