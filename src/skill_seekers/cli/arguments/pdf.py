"""PDF command argument definitions.

This module defines ALL arguments for the pdf command in ONE place.
Both pdf_scraper.py (standalone) and parsers/pdf_parser.py (unified CLI)
import and use these definitions.

Shared arguments (name, description, output, enhance-level, api-key,
dry-run, verbose, quiet, workflow args) come from common.py / workflow.py
via ``add_all_standard_arguments()``.
"""

import argparse
from typing import Any

from .common import add_all_standard_arguments

# PDF-specific argument definitions as data structure
# NOTE: Shared args (name, description, output, enhance_level, api_key, dry_run,
#       verbose, quiet, workflow args) are registered by add_all_standard_arguments().
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
    "from_json": {
        "flags": ("--from-json",),
        "kwargs": {
            "type": str,
            "help": "Build skill from extracted JSON",
            "metavar": "FILE",
        },
    },
}


def add_pdf_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all pdf command arguments to a parser.

    Registers shared args (name, description, output, enhance-level, api-key,
    dry-run, verbose, quiet, workflow args) via add_all_standard_arguments(),
    then adds PDF-specific args on top.

    The default for --enhance-level is overridden to 0 (disabled) for PDF.
    """
    # Shared universal args first
    add_all_standard_arguments(parser)

    # Override enhance-level default to 0 for PDF
    for action in parser._actions:
        if hasattr(action, "dest") and action.dest == "enhance_level":
            action.default = 0
            action.help = (
                "AI enhancement level (auto-detects API vs LOCAL mode): "
                "0=disabled (default for PDF), 1=SKILL.md only, 2=+architecture/config, 3=full enhancement. "
                "Mode selection: uses API if ANTHROPIC_API_KEY is set, otherwise LOCAL (Claude Code)"
            )

    # PDF-specific args
    for arg_name, arg_def in PDF_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = arg_def["kwargs"]
        parser.add_argument(*flags, **kwargs)
