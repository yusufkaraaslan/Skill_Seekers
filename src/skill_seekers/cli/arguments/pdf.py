"""PDF command argument definitions.

This module defines ALL arguments for the pdf command in ONE place.
Both pdf_scraper.py (standalone) and parsers/pdf_parser.py (unified CLI)
import and use these definitions.
"""

import argparse
from typing import Any

PDF_ARGUMENTS: dict[str, dict[str, Any]] = {
    "config": {
        "flags": ("--config",),
        "kwargs": {
            "type": str,
            "help": "PDF config JSON file",
            "metavar": "FILE",
        },
    },
    "pdf": {
        "flags": ("--pdf",),
        "kwargs": {
            "type": str,
            "help": "Direct PDF file path",
            "metavar": "PATH",
        },
    },
    "name": {
        "flags": ("--name",),
        "kwargs": {
            "type": str,
            "help": "Skill name (used with --pdf)",
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
    "from_json": {
        "flags": ("--from-json",),
        "kwargs": {
            "type": str,
            "help": "Build skill from extracted JSON",
            "metavar": "FILE",
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
    # Enhancement level
    "enhance_level": {
        "flags": ("--enhance-level",),
        "kwargs": {
            "type": int,
            "choices": [0, 1, 2, 3],
            "default": 0,
            "help": (
                "AI enhancement level (auto-detects API vs LOCAL mode): "
                "0=disabled (default for PDF), 1=SKILL.md only, 2=+architecture/config, 3=full enhancement. "
                "Mode selection: uses API if ANTHROPIC_API_KEY is set, otherwise LOCAL (Claude Code)"
            ),
            "metavar": "LEVEL",
        },
    },
}


def add_pdf_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all pdf command arguments to a parser."""
    for arg_name, arg_def in PDF_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = arg_def["kwargs"]
        parser.add_argument(*flags, **kwargs)
