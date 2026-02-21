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
    # Enhancement Workflow arguments (mirrors scrape/github/pdf/codebase scrapers)
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
            "help": "Add inline enhancement stage (format: 'name:prompt'). Can be used multiple times.",
            "metavar": "STAGE",
        },
    },
    "var": {
        "flags": ("--var",),
        "kwargs": {
            "action": "append",
            "help": "Override workflow variable (format: 'key=value'). Can be used multiple times.",
            "metavar": "VAR",
        },
    },
    "workflow_dry_run": {
        "flags": ("--workflow-dry-run",),
        "kwargs": {
            "action": "store_true",
            "help": "Preview workflow stages without executing (requires --enhance-workflow)",
        },
    },
    # API key and enhance-level (parity with scrape/github/analyze/pdf)
    "api_key": {
        "flags": ("--api-key",),
        "kwargs": {
            "type": str,
            "help": "Anthropic API key (or set ANTHROPIC_API_KEY env var)",
            "metavar": "KEY",
        },
    },
    "enhance_level": {
        "flags": ("--enhance-level",),
        "kwargs": {
            "type": int,
            "choices": [0, 1, 2, 3],
            "default": None,
            "help": (
                "Global AI enhancement level override (0=off, 1=SKILL.md, "
                "2=+arch/config, 3=full). Overrides per-source enhance_level in config."
            ),
            "metavar": "LEVEL",
        },
    },
}


def add_unified_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all unified command arguments to a parser."""
    for arg_name, arg_def in UNIFIED_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = arg_def["kwargs"]
        parser.add_argument(*flags, **kwargs)
