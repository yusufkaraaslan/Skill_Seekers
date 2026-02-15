"""Unified command argument definitions.

This module defines ALL arguments for the unified command in ONE place.
Both unified_scraper.py (standalone) and parsers/unified_parser.py (unified CLI)
import and use these definitions.
"""

import argparse
from typing import Any

UNIFIED_ARGUMENTS: dict[str, dict[str, Any]] = {
    "config": {
        "flags": ("--config", "-c"),
        "kwargs": {
            "type": str,
            "required": True,
            "help": "Path to unified config JSON file",
            "metavar": "FILE",
        },
    },
    "merge_mode": {
        "flags": ("--merge-mode",),
        "kwargs": {
            "type": str,
            "help": "Merge mode (rule-based, claude-enhanced)",
            "metavar": "MODE",
        },
    },
    "fresh": {
        "flags": ("--fresh",),
        "kwargs": {
            "action": "store_true",
            "help": "Clear existing data and start fresh",
        },
    },
    "dry_run": {
        "flags": ("--dry-run",),
        "kwargs": {
            "action": "store_true",
            "help": "Dry run mode",
        },
    },
}

def add_unified_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all unified command arguments to a parser."""
    for arg_name, arg_def in UNIFIED_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = arg_def["kwargs"]
        parser.add_argument(*flags, **kwargs)
