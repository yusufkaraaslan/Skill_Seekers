"""Notion command argument definitions.

This module defines ALL arguments for the notion command in ONE place.
Both notion_scraper.py (standalone) and parsers/notion_parser.py (unified CLI)
import and use these definitions.

Shared arguments (name, description, output, enhance-level, api-key,
dry-run, verbose, quiet, workflow args) come from common.py / workflow.py
via ``add_all_standard_arguments()``.
"""

import argparse
from typing import Any

from .common import add_all_standard_arguments

# Notion-specific argument definitions as data structure
# NOTE: Shared args (name, description, output, enhance_level, api_key, dry_run,
#       verbose, quiet, workflow args) are registered by add_all_standard_arguments().
NOTION_ARGUMENTS: dict[str, dict[str, Any]] = {
    "database_id": {
        "flags": ("--database-id",),
        "kwargs": {
            "type": str,
            "help": "Notion database ID to extract from",
            "metavar": "ID",
        },
    },
    "page_id": {
        "flags": ("--page-id",),
        "kwargs": {
            "type": str,
            "help": "Notion page ID to extract from",
            "metavar": "ID",
        },
    },
    "export_path": {
        "flags": ("--export-path",),
        "kwargs": {
            "type": str,
            "help": "Path to Notion export directory",
            "metavar": "PATH",
        },
    },
    "token": {
        "flags": ("--token",),
        "kwargs": {
            "type": str,
            "help": "Notion integration token for API authentication",
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


def add_notion_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all notion command arguments to a parser.

    Registers shared args (name, description, output, enhance-level, api-key,
    dry-run, verbose, quiet, workflow args) via add_all_standard_arguments(),
    then adds Notion-specific args on top.

    The default for --enhance-level is overridden to 0 (disabled) for Notion.
    """
    # Shared universal args first
    add_all_standard_arguments(parser)

    # Override enhance-level default to 0 for Notion
    for action in parser._actions:
        if hasattr(action, "dest") and action.dest == "enhance_level":
            action.default = 0
            action.help = (
                "AI enhancement level (auto-detects API vs LOCAL mode): "
                "0=disabled (default for Notion), 1=SKILL.md only, "
                "2=+architecture/config, 3=full enhancement. "
                "Mode selection: uses API if ANTHROPIC_API_KEY is set, "
                "otherwise LOCAL (Claude Code, Kimi, etc.)"
            )

    # Notion-specific args
    for arg_name, arg_def in NOTION_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = arg_def["kwargs"]
        parser.add_argument(*flags, **kwargs)
