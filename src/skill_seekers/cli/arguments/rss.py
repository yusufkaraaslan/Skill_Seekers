"""RSS command argument definitions.

This module defines ALL arguments for the rss command in ONE place.
Both rss_scraper.py (standalone) and parsers/rss_parser.py (unified CLI)
import and use these definitions.

Shared arguments (name, description, output, enhance-level, api-key,
dry-run, verbose, quiet, workflow args) come from common.py / workflow.py
via ``add_all_standard_arguments()``.
"""

import argparse
from typing import Any

from .common import add_all_standard_arguments

# RSS-specific argument definitions as data structure
# NOTE: Shared args (name, description, output, enhance_level, api_key, dry_run,
#       verbose, quiet, workflow args) are registered by add_all_standard_arguments().
RSS_ARGUMENTS: dict[str, dict[str, Any]] = {
    "feed_url": {
        "flags": ("--feed-url",),
        "kwargs": {
            "type": str,
            "help": "URL of the RSS/Atom feed",
            "metavar": "URL",
        },
    },
    "feed_path": {
        "flags": ("--feed-path",),
        "kwargs": {
            "type": str,
            "help": "Path to local RSS/Atom feed file",
            "metavar": "PATH",
        },
    },
    "follow_links": {
        "flags": ("--follow-links",),
        "kwargs": {
            "action": "store_true",
            "default": True,
            "help": "Follow article links and extract full content (default: True)",
        },
    },
    "no_follow_links": {
        "flags": ("--no-follow-links",),
        "kwargs": {
            "action": "store_false",
            "dest": "follow_links",
            "help": "Do not follow article links; use feed summary only",
        },
    },
    "max_articles": {
        "flags": ("--max-articles",),
        "kwargs": {
            "type": int,
            "default": 50,
            "help": "Maximum number of articles to extract (default: 50)",
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


def add_rss_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all rss command arguments to a parser.

    Registers shared args (name, description, output, enhance-level, api-key,
    dry-run, verbose, quiet, workflow args) via add_all_standard_arguments(),
    then adds RSS-specific args on top.

    The default for --enhance-level is overridden to 0 (disabled) for RSS.
    """
    # Shared universal args first
    add_all_standard_arguments(parser)

    # Override enhance-level default to 0 for RSS
    for action in parser._actions:
        if hasattr(action, "dest") and action.dest == "enhance_level":
            action.default = 0
            action.help = (
                "AI enhancement level (auto-detects API vs LOCAL mode): "
                "0=disabled (default for RSS), 1=SKILL.md only, "
                "2=+architecture/config, 3=full enhancement. "
                "Mode selection: uses API if API key is set (ANTHROPIC_API_KEY, MOONSHOT_API_KEY, etc.), "
                "otherwise LOCAL (AI coding agent)"
            )

    # RSS-specific args
    for arg_name, arg_def in RSS_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = arg_def["kwargs"]
        parser.add_argument(*flags, **kwargs)
