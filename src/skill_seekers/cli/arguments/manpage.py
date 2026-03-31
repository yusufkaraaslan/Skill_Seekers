"""Man page command argument definitions.

This module defines ALL arguments for the manpage command in ONE place.
Both manpage_scraper.py (standalone) and parsers/manpage_parser.py (unified CLI)
import and use these definitions.

Shared arguments (name, description, output, enhance-level, api-key,
dry-run, verbose, quiet, workflow args) come from common.py / workflow.py
via ``add_all_standard_arguments()``.
"""

import argparse
from typing import Any

from .common import add_all_standard_arguments

# ManPage-specific argument definitions as data structure
# NOTE: Shared args (name, description, output, enhance_level, api_key, dry_run,
#       verbose, quiet, workflow args) are registered by add_all_standard_arguments().
MANPAGE_ARGUMENTS: dict[str, dict[str, Any]] = {
    "man_names": {
        "flags": ("--man-names",),
        "kwargs": {
            "type": str,
            "help": "Comma-separated list of man page names (e.g., 'ls,grep,find')",
            "metavar": "NAMES",
        },
    },
    "man_path": {
        "flags": ("--man-path",),
        "kwargs": {
            "type": str,
            "help": "Path to directory containing man page files",
            "metavar": "PATH",
        },
    },
    "sections": {
        "flags": ("--sections",),
        "kwargs": {
            "type": str,
            "help": "Comma-separated section numbers to include (e.g., '1,3,8')",
            "metavar": "SECTIONS",
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


def add_manpage_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all manpage command arguments to a parser.

    Registers shared args (name, description, output, enhance-level, api-key,
    dry-run, verbose, quiet, workflow args) via add_all_standard_arguments(),
    then adds ManPage-specific args on top.

    The default for --enhance-level is overridden to 0 (disabled) for ManPage.
    """
    # Shared universal args first
    add_all_standard_arguments(parser)

    # Override enhance-level default to 0 for ManPage
    for action in parser._actions:
        if hasattr(action, "dest") and action.dest == "enhance_level":
            action.default = 0
            action.help = (
                "AI enhancement level (auto-detects API vs LOCAL mode): "
                "0=disabled (default for ManPage), 1=SKILL.md only, "
                "2=+architecture/config, 3=full enhancement. "
                "Mode selection: uses API if ANTHROPIC_API_KEY is set, "
                "otherwise LOCAL (Claude Code, Kimi, etc.)"
            )

    # ManPage-specific args
    for arg_name, arg_def in MANPAGE_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = arg_def["kwargs"]
        parser.add_argument(*flags, **kwargs)
