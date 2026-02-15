"""Enhance command argument definitions.

This module defines ALL arguments for the enhance command in ONE place.
Both enhance_skill_local.py (standalone) and parsers/enhance_parser.py (unified CLI)
import and use these definitions.
"""

import argparse
from typing import Any

ENHANCE_ARGUMENTS: dict[str, dict[str, Any]] = {
    # Positional argument
    "skill_directory": {
        "flags": ("skill_directory",),
        "kwargs": {
            "type": str,
            "help": "Skill directory path",
        },
    },
    # Agent options
    "agent": {
        "flags": ("--agent",),
        "kwargs": {
            "type": str,
            "choices": ["claude", "codex", "copilot", "opencode", "custom"],
            "help": "Local coding agent to use (default: claude or SKILL_SEEKER_AGENT)",
            "metavar": "AGENT",
        },
    },
    "agent_cmd": {
        "flags": ("--agent-cmd",),
        "kwargs": {
            "type": str,
            "help": "Override agent command template (use {prompt_file} or stdin)",
            "metavar": "CMD",
        },
    },
    # Execution options
    "background": {
        "flags": ("--background",),
        "kwargs": {
            "action": "store_true",
            "help": "Run in background",
        },
    },
    "daemon": {
        "flags": ("--daemon",),
        "kwargs": {
            "action": "store_true",
            "help": "Run as daemon",
        },
    },
    "no_force": {
        "flags": ("--no-force",),
        "kwargs": {
            "action": "store_true",
            "help": "Disable force mode (enable confirmations)",
        },
    },
    "timeout": {
        "flags": ("--timeout",),
        "kwargs": {
            "type": int,
            "default": 600,
            "help": "Timeout in seconds (default: 600)",
            "metavar": "SECONDS",
        },
    },
}


def add_enhance_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all enhance command arguments to a parser."""
    for arg_name, arg_def in ENHANCE_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = arg_def["kwargs"]
        parser.add_argument(*flags, **kwargs)
