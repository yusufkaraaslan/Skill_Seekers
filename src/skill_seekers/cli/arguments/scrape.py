"""Scrape command argument definitions.

This module defines ALL arguments for the scrape command in ONE place.
Both doc_scraper.py (standalone) and parsers/scrape_parser.py (unified CLI)
import and use these definitions.

This ensures the parsers NEVER drift out of sync.
"""

import argparse
from typing import Any

from skill_seekers.cli.constants import DEFAULT_RATE_LIMIT
from .common import RAG_ARGUMENTS

# Scrape-specific argument definitions as data structure
# This enables introspection for UI generation and testing
SCRAPE_ARGUMENTS: dict[str, dict[str, Any]] = {
    # Positional argument
    "url_positional": {
        "flags": ("url",),
        "kwargs": {
            "nargs": "?",
            "type": str,
            "help": "Base documentation URL (alternative to --url)",
        },
    },
    # Common arguments (also defined in common.py for other commands)
    "config": {
        "flags": ("--config", "-c"),
        "kwargs": {
            "type": str,
            "help": "Load configuration from JSON file (e.g., configs/react.json)",
            "metavar": "FILE",
        },
    },
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
    # Enhancement arguments
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
    # Scrape-specific options
    "interactive": {
        "flags": ("--interactive", "-i"),
        "kwargs": {
            "action": "store_true",
            "help": "Interactive configuration mode",
        },
    },
    "url": {
        "flags": ("--url",),
        "kwargs": {
            "type": str,
            "help": "Base documentation URL (alternative to positional URL)",
            "metavar": "URL",
        },
    },
    "max_pages": {
        "flags": ("--max-pages",),
        "kwargs": {
            "type": int,
            "metavar": "N",
            "help": "Maximum pages to scrape (overrides config). Use with caution - for testing/prototyping only.",
        },
    },
    "skip_scrape": {
        "flags": ("--skip-scrape",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip scraping, use existing data",
        },
    },
    "dry_run": {
        "flags": ("--dry-run",),
        "kwargs": {
            "action": "store_true",
            "help": "Preview what will be scraped without actually scraping",
        },
    },
    "resume": {
        "flags": ("--resume",),
        "kwargs": {
            "action": "store_true",
            "help": "Resume from last checkpoint (for interrupted scrapes)",
        },
    },
    "fresh": {
        "flags": ("--fresh",),
        "kwargs": {
            "action": "store_true",
            "help": "Clear checkpoint and start fresh",
        },
    },
    "rate_limit": {
        "flags": ("--rate-limit", "-r"),
        "kwargs": {
            "type": float,
            "metavar": "SECONDS",
            "help": f"Override rate limit in seconds (default: from config or {DEFAULT_RATE_LIMIT}). Use 0 for no delay.",
        },
    },
    "workers": {
        "flags": ("--workers", "-w"),
        "kwargs": {
            "type": int,
            "metavar": "N",
            "help": "Number of parallel workers for faster scraping (default: 1, max: 10)",
        },
    },
    "async_mode": {
        "flags": ("--async",),
        "kwargs": {
            "dest": "async_mode",
            "action": "store_true",
            "help": "Enable async mode for better parallel performance (2-3x faster than threads)",
        },
    },
    "no_rate_limit": {
        "flags": ("--no-rate-limit",),
        "kwargs": {
            "action": "store_true",
            "help": "Disable rate limiting completely (same as --rate-limit 0)",
        },
    },
    "interactive_enhancement": {
        "flags": ("--interactive-enhancement",),
        "kwargs": {
            "action": "store_true",
            "help": "Open terminal window for enhancement (use with --enhance-local)",
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
    # RAG chunking options (imported from common.py - see RAG_ARGUMENTS)
    # Note: RAG arguments will be merged at runtime
    "no_preserve_code_blocks": {
        "flags": ("--no-preserve-code-blocks",),
        "kwargs": {
            "action": "store_true",
            "help": "Allow splitting code blocks across chunks (not recommended)",
        },
    },
    "no_preserve_paragraphs": {
        "flags": ("--no-preserve-paragraphs",),
        "kwargs": {
            "action": "store_true",
            "help": "Ignore paragraph boundaries when chunking (not recommended)",
        },
    },
}

# Merge RAG arguments from common.py
SCRAPE_ARGUMENTS.update(RAG_ARGUMENTS)

def add_scrape_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all scrape command arguments to a parser.

    This is the SINGLE SOURCE OF TRUTH for scrape arguments.
    Used by:
    - doc_scraper.py (standalone scraper)
    - parsers/scrape_parser.py (unified CLI)

    Args:
        parser: The ArgumentParser to add arguments to

    Example:
        >>> parser = argparse.ArgumentParser()
        >>> add_scrape_arguments(parser)  # Adds all 26 scrape args
    """
    for arg_name, arg_def in SCRAPE_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = arg_def["kwargs"]
        parser.add_argument(*flags, **kwargs)

def get_scrape_argument_names() -> set:
    """Get the set of scrape argument destination names.

    Returns:
        Set of argument dest names
    """
    return set(SCRAPE_ARGUMENTS.keys())

def get_scrape_argument_count() -> int:
    """Get the total number of scrape arguments.

    Returns:
        Number of arguments
    """
    return len(SCRAPE_ARGUMENTS)
