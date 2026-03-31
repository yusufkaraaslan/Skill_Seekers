"""Chat command argument definitions.

This module defines ALL arguments for the chat command in ONE place.
Both chat_scraper.py (standalone) and parsers/chat_parser.py (unified CLI)
import and use these definitions.

Shared arguments (name, description, output, enhance-level, api-key,
dry-run, verbose, quiet, workflow args) come from common.py / workflow.py
via ``add_all_standard_arguments()``.
"""

import argparse
from typing import Any

from .common import add_all_standard_arguments

# Chat-specific argument definitions as data structure
# NOTE: Shared args (name, description, output, enhance_level, api_key, dry_run,
#       verbose, quiet, workflow args) are registered by add_all_standard_arguments().
CHAT_ARGUMENTS: dict[str, dict[str, Any]] = {
    "export_path": {
        "flags": ("--export-path",),
        "kwargs": {
            "type": str,
            "help": "Path to chat export directory or file",
            "metavar": "PATH",
        },
    },
    "platform": {
        "flags": ("--platform",),
        "kwargs": {
            "type": str,
            "choices": ["slack", "discord"],
            "default": "slack",
            "help": "Chat platform type (default: slack)",
        },
    },
    "token": {
        "flags": ("--token",),
        "kwargs": {
            "type": str,
            "help": "API token for chat platform authentication",
            "metavar": "TOKEN",
        },
    },
    "channel": {
        "flags": ("--channel",),
        "kwargs": {
            "type": str,
            "help": "Channel name or ID to extract from",
            "metavar": "CHANNEL",
        },
    },
    "max_messages": {
        "flags": ("--max-messages",),
        "kwargs": {
            "type": int,
            "default": 10000,
            "help": "Maximum number of messages to extract (default: 10000)",
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


def add_chat_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all chat command arguments to a parser.

    Registers shared args (name, description, output, enhance-level, api-key,
    dry-run, verbose, quiet, workflow args) via add_all_standard_arguments(),
    then adds Chat-specific args on top.

    The default for --enhance-level is overridden to 0 (disabled) for Chat.
    """
    # Shared universal args first
    add_all_standard_arguments(parser)

    # Override enhance-level default to 0 for Chat
    for action in parser._actions:
        if hasattr(action, "dest") and action.dest == "enhance_level":
            action.default = 0
            action.help = (
                "AI enhancement level (auto-detects API vs LOCAL mode): "
                "0=disabled (default for Chat), 1=SKILL.md only, "
                "2=+architecture/config, 3=full enhancement. "
                "Mode selection: uses API if ANTHROPIC_API_KEY is set, "
                "otherwise LOCAL (Claude Code, Kimi, etc.)"
            )

    # Chat-specific args
    for arg_name, arg_def in CHAT_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = arg_def["kwargs"]
        parser.add_argument(*flags, **kwargs)
