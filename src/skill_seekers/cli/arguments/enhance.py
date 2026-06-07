"""Enhance command argument definitions.

This module defines ALL arguments for the enhance command in ONE place.
Both enhance_command.py (dispatcher), enhance_skill_local.py (standalone),
and parsers/enhance_parser.py (unified CLI) import and use these definitions.
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
    # Mode selection — used by smart dispatcher (enhance_command.py)
    "target": {
        "flags": ("--target",),
        "kwargs": {
            # choices is filled at parser-build time from
            # get_enhancement_platforms() so it can never drift from the
            # adaptors that actually support enhancement.
            "type": str,
            "help": (
                "AI platform for enhancement (uses API mode). "
                "Auto-detected from env vars if not specified: "
                "ANTHROPIC_API_KEY->claude, GOOGLE_API_KEY->gemini, OPENAI_API_KEY->openai, MOONSHOT_API_KEY->kimi. "
                "Falls back to LOCAL mode (AI coding agent) when no API keys are found."
            ),
            "metavar": "PLATFORM",
        },
    },
    "model": {
        "flags": ("--model",),
        "kwargs": {
            "type": str,
            "help": (
                "Override the enhancement model for the target platform "
                "(API mode only), e.g. 'MiniMax-M2.7'. "
                "Defaults to the platform's default model."
            ),
            "metavar": "MODEL",
        },
    },
    "api_key": {
        "flags": ("--api-key",),
        "kwargs": {
            "type": str,
            "help": (
                "API key for the target platform "
                "(or set ANTHROPIC_API_KEY / GOOGLE_API_KEY / OPENAI_API_KEY / MOONSHOT_API_KEY)"
            ),
            "metavar": "KEY",
        },
    },
    "dry_run": {
        "flags": ("--dry-run",),
        "kwargs": {
            "action": "store_true",
            "help": "Preview what would be enhanced without calling AI",
        },
    },
    # Agent options — LOCAL mode only
    "agent": {
        "flags": ("--agent",),
        "kwargs": {
            "type": str,
            "choices": ["claude", "codex", "copilot", "opencode", "kimi", "custom"],
            "help": "Local coding agent to use (default: AI agent from SKILL_SEEKER_AGENT env var)",
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
    # Execution options — LOCAL mode only
    "interactive_enhancement": {
        "flags": ("--interactive-enhancement",),
        "kwargs": {
            "action": "store_true",
            "help": "Open terminal window for enhancement (default: headless mode)",
        },
    },
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
            "default": None,  # Resolved at runtime via get_default_timeout()
            "help": (
                "Timeout in seconds "
                "(default: 45 minutes, set SKILL_SEEKER_ENHANCE_TIMEOUT to override)"
            ),
            "metavar": "SECONDS",
        },
    },
}


def add_enhance_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all enhance command arguments to a parser.

    The ``--target`` choices are resolved dynamically from the adaptors that
    report ``supports_enhancement()`` so newly added enhancement-capable
    platforms (minimax, deepseek, qwen, ...) are accepted without touching
    this list.
    """
    from skill_seekers.cli.adaptors import get_enhancement_platforms

    enhancement_platforms = get_enhancement_platforms()

    for arg_name, arg_def in ENHANCE_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = dict(arg_def["kwargs"])
        if arg_name == "target":
            kwargs["choices"] = enhancement_platforms
        parser.add_argument(*flags, **kwargs)
