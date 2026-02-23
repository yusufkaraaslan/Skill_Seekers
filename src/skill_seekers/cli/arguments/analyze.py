"""Analyze command argument definitions.

This module defines ALL arguments for the analyze command in ONE place.
Both codebase_scraper.py (standalone) and parsers/analyze_parser.py (unified CLI)
import and use these definitions.

Includes preset system support for #268.

Shared arguments (name, description, output, enhance-level, api-key,
dry-run, verbose, quiet, workflow args) come from common.py / workflow.py
via ``add_all_standard_arguments()``.
"""

import argparse
from typing import Any

from .common import add_all_standard_arguments

# Analyze-specific argument definitions as data structure
# NOTE: Shared args (name, description, output, enhance_level, api_key, dry_run,
#       verbose, quiet, workflow args) are registered by add_all_standard_arguments().
#       The default enhance_level for analyze is 0 (overridden after registration).
ANALYZE_ARGUMENTS: dict[str, dict[str, Any]] = {
    # Core options
    "directory": {
        "flags": ("--directory",),
        "kwargs": {
            "type": str,
            "required": True,
            "help": "Directory to analyze",
            "metavar": "DIR",
        },
    },
    # Preset system (Issue #268)
    "preset": {
        "flags": ("--preset",),
        "kwargs": {
            "type": str,
            "choices": ["quick", "standard", "comprehensive"],
            "help": "Analysis preset: quick (1-2 min), standard (5-10 min, DEFAULT), comprehensive (20-60 min)",
            "metavar": "PRESET",
        },
    },
    "preset_list": {
        "flags": ("--preset-list",),
        "kwargs": {
            "action": "store_true",
            "help": "Show available presets and exit",
        },
    },
    # Legacy preset flags (deprecated but kept for backward compatibility)
    "quick": {
        "flags": ("--quick",),
        "kwargs": {
            "action": "store_true",
            "help": "[DEPRECATED] Quick analysis - use '--preset quick' instead",
        },
    },
    "comprehensive": {
        "flags": ("--comprehensive",),
        "kwargs": {
            "action": "store_true",
            "help": "[DEPRECATED] Comprehensive analysis - use '--preset comprehensive' instead",
        },
    },
    # Legacy depth flag (deprecated)
    "depth": {
        "flags": ("--depth",),
        "kwargs": {
            "type": str,
            "choices": ["surface", "deep", "full"],
            "help": "[DEPRECATED] Analysis depth - use --preset instead",
            "metavar": "DEPTH",
        },
    },
    # Language and file options
    "languages": {
        "flags": ("--languages",),
        "kwargs": {
            "type": str,
            "help": "Comma-separated languages (e.g., Python,JavaScript,C++)",
            "metavar": "LANGS",
        },
    },
    "file_patterns": {
        "flags": ("--file-patterns",),
        "kwargs": {
            "type": str,
            "help": "Comma-separated file patterns",
            "metavar": "PATTERNS",
        },
    },
    # Feature skip options
    "skip_api_reference": {
        "flags": ("--skip-api-reference",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip API docs generation",
        },
    },
    "skip_dependency_graph": {
        "flags": ("--skip-dependency-graph",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip dependency graph generation",
        },
    },
    "skip_patterns": {
        "flags": ("--skip-patterns",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip pattern detection",
        },
    },
    "skip_test_examples": {
        "flags": ("--skip-test-examples",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip test example extraction",
        },
    },
    "skip_how_to_guides": {
        "flags": ("--skip-how-to-guides",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip how-to guide generation",
        },
    },
    "skip_config_patterns": {
        "flags": ("--skip-config-patterns",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip config pattern extraction",
        },
    },
    "skip_docs": {
        "flags": ("--skip-docs",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip project docs (README, docs/)",
        },
    },
    "no_comments": {
        "flags": ("--no-comments",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip comment extraction",
        },
    },
}


def add_analyze_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all analyze command arguments to a parser.

    Registers shared args (name, description, output, enhance-level, api-key,
    dry-run, verbose, quiet, workflow args) via add_all_standard_arguments(),
    then adds analyze-specific args on top.

    The default for --enhance-level is overridden to 0 (off) for analyze,
    and --output default is set to 'output/codebase/'.
    """
    # Shared universal args first
    add_all_standard_arguments(parser)

    # Override defaults that differ for the analyze command
    # enhance-level defaults to 0 (off) for codebase analysis
    for action in parser._actions:
        if hasattr(action, "dest"):
            if action.dest == "enhance_level":
                action.default = 0
            elif action.dest == "output":
                action.default = "output/codebase/"

    # Analyze-specific args
    for arg_name, arg_def in ANALYZE_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = arg_def["kwargs"]
        parser.add_argument(*flags, **kwargs)


def get_analyze_argument_names() -> set:
    """Get the set of analyze argument destination names."""
    from .common import get_all_standard_argument_names

    return get_all_standard_argument_names() | set(ANALYZE_ARGUMENTS.keys())
