"""Create command unified argument definitions.

Organizes arguments into three tiers:
1. Universal Arguments - Work for ALL sources (web, github, local, pdf, config)
2. Source-Specific Arguments - Only relevant for specific sources
3. Advanced Arguments - Rarely used, hidden from default help

This enables progressive disclosure in help text while maintaining
100% backward compatibility with existing commands.
"""

import argparse
from typing import Dict, Any, Set, List

from skill_seekers.cli.constants import DEFAULT_RATE_LIMIT


# =============================================================================
# TIER 1: UNIVERSAL ARGUMENTS (15 flags)
# =============================================================================
# These arguments work for ALL source types

UNIVERSAL_ARGUMENTS: Dict[str, Dict[str, Any]] = {
    # Identity arguments
    "name": {
        "flags": ("--name",),
        "kwargs": {
            "type": str,
            "help": "Skill name (default: auto-detected from source)",
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
            "help": "Anthropic API key (or set ANTHROPIC_API_KEY env var)",
            "metavar": "KEY",
        },
    },
    # Behavior arguments
    "dry_run": {
        "flags": ("--dry-run",),
        "kwargs": {
            "action": "store_true",
            "help": "Preview what will be created without actually creating it",
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
            "help": "Minimize output (WARNING level only)",
        },
    },
    # RAG features (NEW - universal for all sources!)
    "chunk_for_rag": {
        "flags": ("--chunk-for-rag",),
        "kwargs": {
            "action": "store_true",
            "help": "Enable semantic chunking for RAG pipelines (all sources)",
        },
    },
    "chunk_size": {
        "flags": ("--chunk-size",),
        "kwargs": {
            "type": int,
            "default": 512,
            "metavar": "TOKENS",
            "help": "Chunk size in tokens for RAG (default: 512)",
        },
    },
    "chunk_overlap": {
        "flags": ("--chunk-overlap",),
        "kwargs": {
            "type": int,
            "default": 50,
            "metavar": "TOKENS",
            "help": "Overlap between chunks in tokens (default: 50)",
        },
    },
    # Preset system
    "preset": {
        "flags": ("--preset",),
        "kwargs": {
            "type": str,
            "choices": ["quick", "standard", "comprehensive"],
            "help": "Analysis preset: quick (1-2 min), standard (5-10 min), comprehensive (20-60 min)",
            "metavar": "PRESET",
        },
    },
    # Config loading
    "config": {
        "flags": ("--config", "-c"),
        "kwargs": {
            "type": str,
            "help": "Load additional settings from JSON file",
            "metavar": "FILE",
        },
    },
}


# =============================================================================
# TIER 2: SOURCE-SPECIFIC ARGUMENTS
# =============================================================================

# Web scraping specific (from scrape.py)
WEB_ARGUMENTS: Dict[str, Dict[str, Any]] = {
    "url": {
        "flags": ("--url",),
        "kwargs": {
            "type": str,
            "help": "Base documentation URL (alternative to positional arg)",
            "metavar": "URL",
        },
    },
    "max_pages": {
        "flags": ("--max-pages",),
        "kwargs": {
            "type": int,
            "metavar": "N",
            "help": "Maximum pages to scrape (for testing/prototyping)",
        },
    },
    "skip_scrape": {
        "flags": ("--skip-scrape",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip scraping, use existing data",
        },
    },
    "resume": {
        "flags": ("--resume",),
        "kwargs": {
            "action": "store_true",
            "help": "Resume from last checkpoint",
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
            "help": f"Rate limit in seconds (default: {DEFAULT_RATE_LIMIT})",
        },
    },
    "workers": {
        "flags": ("--workers", "-w"),
        "kwargs": {
            "type": int,
            "metavar": "N",
            "help": "Number of parallel workers (default: 1, max: 10)",
        },
    },
    "async_mode": {
        "flags": ("--async",),
        "kwargs": {
            "dest": "async_mode",
            "action": "store_true",
            "help": "Enable async mode (2-3x faster)",
        },
    },
}

# GitHub repository specific (from github.py)
GITHUB_ARGUMENTS: Dict[str, Dict[str, Any]] = {
    "repo": {
        "flags": ("--repo",),
        "kwargs": {
            "type": str,
            "help": "GitHub repository (owner/repo)",
            "metavar": "OWNER/REPO",
        },
    },
    "token": {
        "flags": ("--token",),
        "kwargs": {
            "type": str,
            "help": "GitHub personal access token",
            "metavar": "TOKEN",
        },
    },
    "profile": {
        "flags": ("--profile",),
        "kwargs": {
            "type": str,
            "help": "GitHub profile name (from config)",
            "metavar": "PROFILE",
        },
    },
    "non_interactive": {
        "flags": ("--non-interactive",),
        "kwargs": {
            "action": "store_true",
            "help": "Non-interactive mode (fail on rate limits)",
        },
    },
    "no_issues": {
        "flags": ("--no-issues",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip GitHub issues",
        },
    },
    "no_changelog": {
        "flags": ("--no-changelog",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip CHANGELOG",
        },
    },
    "no_releases": {
        "flags": ("--no-releases",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip releases",
        },
    },
    "max_issues": {
        "flags": ("--max-issues",),
        "kwargs": {
            "type": int,
            "default": 100,
            "metavar": "N",
            "help": "Max issues to fetch (default: 100)",
        },
    },
    "scrape_only": {
        "flags": ("--scrape-only",),
        "kwargs": {
            "action": "store_true",
            "help": "Only scrape, don't build skill",
        },
    },
}

# Local codebase specific (from analyze.py)
LOCAL_ARGUMENTS: Dict[str, Dict[str, Any]] = {
    "directory": {
        "flags": ("--directory",),
        "kwargs": {
            "type": str,
            "help": "Directory to analyze",
            "metavar": "DIR",
        },
    },
    "languages": {
        "flags": ("--languages",),
        "kwargs": {
            "type": str,
            "help": "Comma-separated languages (e.g., Python,JavaScript)",
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
    "skip_patterns": {
        "flags": ("--skip-patterns",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip design pattern detection",
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
    "skip_config": {
        "flags": ("--skip-config",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip configuration extraction",
        },
    },
    "skip_docs": {
        "flags": ("--skip-docs",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip documentation extraction",
        },
    },
}

# PDF specific (from pdf.py)
PDF_ARGUMENTS: Dict[str, Dict[str, Any]] = {
    "pdf": {
        "flags": ("--pdf",),
        "kwargs": {
            "type": str,
            "help": "PDF file path",
            "metavar": "PATH",
        },
    },
    "ocr": {
        "flags": ("--ocr",),
        "kwargs": {
            "action": "store_true",
            "help": "Enable OCR for scanned PDFs",
        },
    },
    "pages": {
        "flags": ("--pages",),
        "kwargs": {
            "type": str,
            "help": "Page range (e.g., '1-10', '5,7,9')",
            "metavar": "RANGE",
        },
    },
}


# =============================================================================
# TIER 3: ADVANCED/RARE ARGUMENTS
# =============================================================================
# Hidden from default help, shown only with --help-advanced

ADVANCED_ARGUMENTS: Dict[str, Dict[str, Any]] = {
    "no_rate_limit": {
        "flags": ("--no-rate-limit",),
        "kwargs": {
            "action": "store_true",
            "help": "Disable rate limiting completely",
        },
    },
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
    "interactive_enhancement": {
        "flags": ("--interactive-enhancement",),
        "kwargs": {
            "action": "store_true",
            "help": "Open terminal window for enhancement (use with --enhance-local)",
        },
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_universal_argument_names() -> Set[str]:
    """Get set of universal argument names."""
    return set(UNIVERSAL_ARGUMENTS.keys())


def get_source_specific_arguments(source_type: str) -> Dict[str, Dict[str, Any]]:
    """Get source-specific arguments for a given source type.

    Args:
        source_type: One of 'web', 'github', 'local', 'pdf', 'config'

    Returns:
        Dict of argument definitions
    """
    if source_type == 'web':
        return WEB_ARGUMENTS
    elif source_type == 'github':
        return GITHUB_ARGUMENTS
    elif source_type == 'local':
        return LOCAL_ARGUMENTS
    elif source_type == 'pdf':
        return PDF_ARGUMENTS
    elif source_type == 'config':
        return {}  # Config files don't have extra args
    else:
        return {}


def get_compatible_arguments(source_type: str) -> List[str]:
    """Get list of compatible argument names for a source type.

    Args:
        source_type: Source type ('web', 'github', 'local', 'pdf', 'config')

    Returns:
        List of argument names that are compatible with this source
    """
    # Universal arguments are always compatible
    compatible = list(UNIVERSAL_ARGUMENTS.keys())

    # Add source-specific arguments
    source_specific = get_source_specific_arguments(source_type)
    compatible.extend(source_specific.keys())

    # Advanced arguments are always technically available
    compatible.extend(ADVANCED_ARGUMENTS.keys())

    return compatible


def add_create_arguments(parser: argparse.ArgumentParser, mode: str = 'default') -> None:
    """Add create command arguments to parser.

    Supports multiple help modes for progressive disclosure:
    - 'default': Universal arguments only (15 flags)
    - 'web': Universal + web-specific
    - 'github': Universal + github-specific
    - 'local': Universal + local-specific
    - 'pdf': Universal + pdf-specific
    - 'advanced': Advanced/rare arguments
    - 'all': All 120+ arguments

    Args:
        parser: ArgumentParser to add arguments to
        mode: Help mode (default, web, github, local, pdf, advanced, all)
    """
    # Positional argument for source
    parser.add_argument(
        'source',
        nargs='?',
        type=str,
        help='Source to create skill from (URL, GitHub repo, directory, PDF, or config file)'
    )

    # Always add universal arguments
    for arg_name, arg_def in UNIVERSAL_ARGUMENTS.items():
        parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])

    # Add source-specific arguments based on mode
    if mode in ['web', 'all']:
        for arg_name, arg_def in WEB_ARGUMENTS.items():
            parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])

    if mode in ['github', 'all']:
        for arg_name, arg_def in GITHUB_ARGUMENTS.items():
            parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])

    if mode in ['local', 'all']:
        for arg_name, arg_def in LOCAL_ARGUMENTS.items():
            parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])

    if mode in ['pdf', 'all']:
        for arg_name, arg_def in PDF_ARGUMENTS.items():
            parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])

    # Add advanced arguments if requested
    if mode in ['advanced', 'all']:
        for arg_name, arg_def in ADVANCED_ARGUMENTS.items():
            parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])
