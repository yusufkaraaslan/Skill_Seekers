"""PPTX command argument definitions.

This module defines ALL arguments for the pptx command in ONE place.
Both pptx_scraper.py (standalone) and parsers/pptx_parser.py (unified CLI)
import and use these definitions.

Shared arguments (name, description, output, enhance-level, api-key,
dry-run, verbose, quiet, workflow args) come from common.py / workflow.py
via ``add_all_standard_arguments()``.
"""

import argparse
from typing import Any

from .common import add_all_standard_arguments

# PPTX-specific argument definitions as data structure
# NOTE: Shared args (name, description, output, enhance_level, api_key, dry_run,
#       verbose, quiet, workflow args) are registered by add_all_standard_arguments().
PPTX_ARGUMENTS: dict[str, dict[str, Any]] = {
    "pptx": {
        "flags": ("--pptx",),
        "kwargs": {
            "type": str,
            "help": "Path to PowerPoint file (.pptx)",
            "metavar": "PATH",
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


def add_pptx_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all pptx command arguments to a parser.

    Registers shared args (name, description, output, enhance-level, api-key,
    dry-run, verbose, quiet, workflow args) via add_all_standard_arguments(),
    then adds PPTX-specific args on top.

    The default for --enhance-level is overridden to 0 (disabled) for PPTX.
    """
    # Shared universal args first
    add_all_standard_arguments(parser)

    # Override enhance-level default to 0 for PPTX
    for action in parser._actions:
        if hasattr(action, "dest") and action.dest == "enhance_level":
            action.default = 0
            action.help = (
                "AI enhancement level (auto-detects API vs LOCAL mode): "
                "0=disabled (default for PPTX), 1=SKILL.md only, "
                "2=+architecture/config, 3=full enhancement. "
                "Mode selection: uses API if ANTHROPIC_API_KEY is set, "
                "otherwise LOCAL (Claude Code, Kimi, etc.)"
            )

    # PPTX-specific args
    for arg_name, arg_def in PPTX_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = arg_def["kwargs"]
        parser.add_argument(*flags, **kwargs)
