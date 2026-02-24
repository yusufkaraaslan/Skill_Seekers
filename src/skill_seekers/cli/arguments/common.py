"""Common CLI arguments shared across multiple commands.

These arguments are used by most commands (scrape, github, pdf, analyze, etc.)
and provide consistent behavior for configuration, output control, and help.

Hierarchy:
    COMMON_ARGUMENTS     - Identity + enhancement (name, description, output, enhance-level, api-key)
    BEHAVIOR_ARGUMENTS   - Runtime behavior (dry-run, verbose, quiet)
    WORKFLOW_ARGUMENTS   - Enhancement workflows (from workflow.py)

    add_all_standard_arguments(parser)  - Registers all three groups at once.
    Every scraper should call this so the `create` command can forward flags safely.
"""

import argparse
from typing import Any

# Common argument definitions as data structure
# These are arguments that appear in MULTIPLE commands
COMMON_ARGUMENTS: dict[str, dict[str, Any]] = {
    "name": {
        "flags": ("--name",),
        "kwargs": {
            "type": str,
            "help": "Skill name (used for output directory and filenames)",
            "metavar": "NAME",
        },
    },
    "description": {
        "flags": ("--description", "-d"),
        "kwargs": {
            "type": str,
            "help": "Skill description (used in SKILL.md)",
            "metavar": "TEXT",
        },
    },
    "output": {
        "flags": ("--output", "-o"),
        "kwargs": {
            "type": str,
            "help": "Output directory (default: auto-generated from name)",
            "metavar": "DIR",
        },
    },
    "enhance_level": {
        "flags": ("--enhance-level",),
        "kwargs": {
            "type": int,
            "choices": [0, 1, 2, 3],
            "default": 2,
            "help": (
                "AI enhancement level (auto-detects API vs LOCAL mode): "
                "0=disabled, 1=SKILL.md only, 2=+architecture/config (default), 3=full enhancement. "
                "Mode selection: uses API if ANTHROPIC_API_KEY is set, otherwise LOCAL (Claude Code)"
            ),
            "metavar": "LEVEL",
        },
    },
    "api_key": {
        "flags": ("--api-key",),
        "kwargs": {
            "type": str,
            "help": "Anthropic API key for --enhance (or set ANTHROPIC_API_KEY env var)",
            "metavar": "KEY",
        },
    },
}

# Behavior arguments — runtime flags shared by every scraper
BEHAVIOR_ARGUMENTS: dict[str, dict[str, Any]] = {
    "dry_run": {
        "flags": ("--dry-run",),
        "kwargs": {
            "action": "store_true",
            "help": "Preview what will happen without actually executing",
        },
    },
    "verbose": {
        "flags": ("--verbose", "-v"),
        "kwargs": {
            "action": "store_true",
            "help": "Enable verbose output (DEBUG level logging)",
        },
    },
    "quiet": {
        "flags": ("--quiet", "-q"),
        "kwargs": {
            "action": "store_true",
            "help": "Minimize output (WARNING level logging only)",
        },
    },
}

# RAG (Retrieval-Augmented Generation) arguments
# These are shared across commands that support RAG chunking
RAG_ARGUMENTS: dict[str, dict[str, Any]] = {
    "chunk_for_rag": {
        "flags": ("--chunk-for-rag",),
        "kwargs": {
            "action": "store_true",
            "help": "Enable semantic chunking for RAG pipelines",
        },
    },
    "chunk_tokens": {
        "flags": ("--chunk-tokens",),
        "kwargs": {
            "type": int,
            "default": 512,
            "metavar": "TOKENS",
            "help": "Chunk size in tokens for RAG (default: 512)",
        },
    },
    "chunk_overlap_tokens": {
        "flags": ("--chunk-overlap-tokens",),
        "kwargs": {
            "type": int,
            "default": 50,
            "metavar": "TOKENS",
            "help": "Overlap between chunks in tokens (default: 50)",
        },
    },
}


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """Add common arguments to a parser.

    These arguments are shared across most commands for consistent UX.

    Args:
        parser: The ArgumentParser to add arguments to

    Example:
        >>> parser = argparse.ArgumentParser()
        >>> add_common_arguments(parser)
        >>> # Now parser has --name, --description, etc.
    """
    for arg_name, arg_def in COMMON_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = arg_def["kwargs"]
        parser.add_argument(*flags, **kwargs)


def add_behavior_arguments(parser: argparse.ArgumentParser) -> None:
    """Add behavior arguments (--dry-run, --verbose, --quiet) to a parser."""
    for arg_name, arg_def in BEHAVIOR_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = arg_def["kwargs"]
        parser.add_argument(*flags, **kwargs)


def add_all_standard_arguments(parser: argparse.ArgumentParser) -> None:
    """Add common + behavior + workflow arguments to a parser.

    This is the ONE call every scraper should make to accept all universal flags
    that the ``create`` command may forward.
    """
    add_common_arguments(parser)
    add_behavior_arguments(parser)
    # Import here to avoid circular imports
    from .workflow import add_workflow_arguments

    add_workflow_arguments(parser)


def get_common_argument_names() -> set:
    """Get the set of common argument destination names.

    Returns:
        Set of argument dest names (e.g., {'name', 'description', ...})
    """
    return set(COMMON_ARGUMENTS.keys())


def add_rag_arguments(parser: argparse.ArgumentParser) -> None:
    """Add RAG (Retrieval-Augmented Generation) arguments to a parser.

    These arguments enable semantic chunking for RAG pipelines.

    Args:
        parser: The ArgumentParser to add arguments to

    Example:
        >>> parser = argparse.ArgumentParser()
        >>> add_rag_arguments(parser)
        >>> # Now parser has --chunk-for-rag, --chunk-tokens, --chunk-overlap-tokens
    """
    for arg_name, arg_def in RAG_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = arg_def["kwargs"]
        parser.add_argument(*flags, **kwargs)


def get_rag_argument_names() -> set:
    """Get the set of RAG argument destination names.

    Returns:
        Set of argument dest names (e.g., {'chunk_for_rag', 'chunk_tokens', 'chunk_overlap_tokens'})
    """
    return set(RAG_ARGUMENTS.keys())


def get_behavior_argument_names() -> set:
    """Get the set of behavior argument destination names."""
    return set(BEHAVIOR_ARGUMENTS.keys())


def get_all_standard_argument_names() -> set:
    """Get the combined set of common + behavior + workflow dest names."""
    from .workflow import WORKFLOW_ARGUMENTS

    return (
        set(COMMON_ARGUMENTS.keys())
        | set(BEHAVIOR_ARGUMENTS.keys())
        | set(WORKFLOW_ARGUMENTS.keys())
    )


def get_argument_help(arg_name: str) -> str:
    """Get the help text for a common or behavior argument.

    Args:
        arg_name: Name of the argument (e.g., 'name', 'dry_run')

    Returns:
        Help text string

    Raises:
        KeyError: If argument doesn't exist in either dict
    """
    if arg_name in COMMON_ARGUMENTS:
        return COMMON_ARGUMENTS[arg_name]["kwargs"]["help"]
    return BEHAVIOR_ARGUMENTS[arg_name]["kwargs"]["help"]
