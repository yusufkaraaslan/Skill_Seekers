"""Confluence command argument definitions.

This module defines ALL arguments for the confluence command in ONE place.
Both confluence_scraper.py (standalone) and parsers/confluence_parser.py (unified CLI)
import and use these definitions.

Shared arguments (name, description, output, enhance-level, api-key,
dry-run, verbose, quiet, workflow args) come from common.py / workflow.py
via ``add_all_standard_arguments()``.
"""

import argparse
from typing import Any

from .common import add_all_standard_arguments

# Confluence-specific argument definitions as data structure
# NOTE: Shared args (name, description, output, enhance_level, api_key, dry_run,
#       verbose, quiet, workflow args) are registered by add_all_standard_arguments().
CONFLUENCE_ARGUMENTS: dict[str, dict[str, Any]] = {
    "base_url": {
        "flags": ("--base-url",),
        "kwargs": {
            "type": str,
            "help": "Confluence instance base URL",
            "metavar": "URL",
        },
    },
    "space_key": {
        "flags": ("--space-key",),
        "kwargs": {
            "type": str,
            "help": "Confluence space key to extract from",
            "metavar": "KEY",
        },
    },
    "export_path": {
        "flags": ("--export-path",),
        "kwargs": {
            "type": str,
            "help": "Path to Confluence HTML/XML export directory",
            "metavar": "PATH",
        },
    },
    "username": {
        "flags": ("--username",),
        "kwargs": {
            "type": str,
            "help": "Confluence username for API authentication",
            "metavar": "USER",
        },
    },
    "token": {
        "flags": ("--token",),
        "kwargs": {
            "type": str,
            "help": "Confluence API token for authentication",
            "metavar": "TOKEN",
        },
    },
    "max_pages": {
        "flags": ("--max-pages",),
        "kwargs": {
            "type": int,
            "default": 500,
            "help": "Maximum number of pages to extract (default: 500)",
            "metavar": "N",
        },
    },
    "from_json": {
        "flags": ("--from-json",),
        "kwargs": {
            "type": str,
            "help": "Build skill from extracted JSON",
            "metavar": "FILE",
        },
    },
}


def add_confluence_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all confluence command arguments to a parser.

    Registers shared args (name, description, output, enhance-level, api-key,
    dry-run, verbose, quiet, workflow args) via add_all_standard_arguments(),
    then adds Confluence-specific args on top.

    The default for --enhance-level is overridden to 0 (disabled) for Confluence.
    """
    # Shared universal args first
    add_all_standard_arguments(parser)

    # Override enhance-level default to 0 for Confluence
    for action in parser._actions:
        if hasattr(action, "dest") and action.dest == "enhance_level":
            action.default = 0
            action.help = (
                "AI enhancement level (auto-detects API vs LOCAL mode): "
                "0=disabled (default for Confluence), 1=SKILL.md only, "
                "2=+architecture/config, 3=full enhancement. "
                "Mode selection: uses API if ANTHROPIC_API_KEY is set, "
                "otherwise LOCAL (Claude Code, Kimi, etc.)"
            )

    # Confluence-specific args
    for arg_name, arg_def in CONFLUENCE_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = arg_def["kwargs"]
        parser.add_argument(*flags, **kwargs)
