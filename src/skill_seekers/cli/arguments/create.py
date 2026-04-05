"""Create command unified argument definitions.

Organizes arguments into three tiers:
1. Universal Arguments - Work for ALL sources (web, github, local, pdf, config)
2. Source-Specific Arguments - Only relevant for specific sources
3. Advanced Arguments - Rarely used, hidden from default help

This enables progressive disclosure in help text while maintaining
100% backward compatibility with existing commands.
"""

import argparse
from typing import Any

from skill_seekers.cli.constants import DEFAULT_RATE_LIMIT
from .common import RAG_ARGUMENTS

# =============================================================================
# TIER 1: UNIVERSAL ARGUMENTS (19 flags)
# =============================================================================
# These arguments work for ALL source types
# Includes: 11 core + 4 workflow + 4 RAG (merged from common.py)

UNIVERSAL_ARGUMENTS: dict[str, dict[str, Any]] = {
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
                "Mode selection: uses API if API key is set (ANTHROPIC_API_KEY, MOONSHOT_API_KEY, etc.), otherwise LOCAL (AI coding agent)"
            ),
            "metavar": "LEVEL",
        },
    },
    "api_key": {
        "flags": ("--api-key",),
        "kwargs": {
            "type": str,
            "help": "API key for enhancement (ANTHROPIC_API_KEY, GOOGLE_API_KEY, OPENAI_API_KEY, MOONSHOT_API_KEY)",
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
    # RAG features (imported from common.py - see RAG_ARGUMENTS)
    # Note: RAG arguments are merged into UNIVERSAL_ARGUMENTS at runtime
    # Preset system
    "preset": {
        "flags": ("--preset", "-p"),
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
    # Enhancement Workflow arguments (NEW - Phase 2)
    "enhance_workflow": {
        "flags": ("--enhance-workflow",),
        "kwargs": {
            "action": "append",
            "help": "Apply enhancement workflow (file path or preset: security-focus, minimal, api-documentation, architecture-comprehensive). Can use multiple times to chain workflows.",
            "metavar": "WORKFLOW",
        },
    },
    "enhance_stage": {
        "flags": ("--enhance-stage",),
        "kwargs": {
            "action": "append",
            "help": "Add inline enhancement stage (format: 'name:prompt'). Can be used multiple times.",
            "metavar": "STAGE",
        },
    },
    "var": {
        "flags": ("--var",),
        "kwargs": {
            "action": "append",
            "help": "Override workflow variable (format: 'key=value'). Can be used multiple times.",
            "metavar": "VAR",
        },
    },
    "workflow_dry_run": {
        "flags": ("--workflow-dry-run",),
        "kwargs": {
            "action": "store_true",
            "help": "Preview workflow stages without executing (requires --enhance-workflow)",
        },
    },
    "local_repo_path": {
        "flags": ("--local-repo-path",),
        "kwargs": {
            "type": str,
            "help": "Path to local clone of a GitHub repository for unlimited C3.x analysis (bypasses GitHub API file limits)",
            "metavar": "PATH",
        },
    },
    "doc_version": {
        "flags": ("--doc-version",),
        "kwargs": {
            "type": str,
            "default": "",
            "help": "Documentation version tag for RAG metadata (e.g., '16.2')",
            "metavar": "VERSION",
        },
    },
    # Agent selection for enhancement (added in v3.4.0 - multi-agent support)
    "agent": {
        "flags": ("--agent",),
        "kwargs": {
            "type": str,
            "choices": ["claude", "codex", "copilot", "opencode", "kimi", "custom"],
            "help": "Local coding agent for enhancement (default: AI agent from SKILL_SEEKER_AGENT env var)",
            "metavar": "AGENT",
        },
    },
    "agent_cmd": {
        "flags": ("--agent-cmd",),
        "kwargs": {
            "type": str,
            "help": "Override agent command template (advanced)",
            "metavar": "CMD",
        },
    },
}

# Merge RAG arguments from common.py into universal arguments
UNIVERSAL_ARGUMENTS.update(RAG_ARGUMENTS)


# =============================================================================
# TIER 2: SOURCE-SPECIFIC ARGUMENTS
# =============================================================================

# Web scraping specific (from scrape.py)
WEB_ARGUMENTS: dict[str, dict[str, Any]] = {
    "browser": {
        "flags": ("--browser",),
        "kwargs": {
            "action": "store_true",
            "help": "Use headless browser (Playwright) to render JavaScript SPA sites",
        },
    },
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
GITHUB_ARGUMENTS: dict[str, dict[str, Any]] = {
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
LOCAL_ARGUMENTS: dict[str, dict[str, Any]] = {
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
    "skip_api_reference": {
        "flags": ("--skip-api-reference",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip API reference generation",
        },
    },
    "skip_dependency_graph": {
        "flags": ("--skip-dependency-graph",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip dependency graph analysis",
        },
    },
    "skip_config_patterns": {
        "flags": ("--skip-config-patterns",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip configuration pattern extraction",
        },
    },
    "no_comments": {
        "flags": ("--no-comments",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip comment extraction from source code",
        },
    },
    "depth": {
        "flags": ("--depth",),
        "kwargs": {
            "type": str,
            "choices": ["surface", "deep", "full"],
            "help": "Analysis depth (deprecated, use --preset instead)",
            "metavar": "LEVEL",
        },
    },
}

# PDF specific (from pdf.py)
PDF_ARGUMENTS: dict[str, dict[str, Any]] = {
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

# Word document specific (from word.py)
WORD_ARGUMENTS: dict[str, dict[str, Any]] = {
    "docx": {
        "flags": ("--docx",),
        "kwargs": {
            "type": str,
            "help": "DOCX file path",
            "metavar": "PATH",
        },
    },
}

# EPUB specific (from epub.py)
EPUB_ARGUMENTS: dict[str, dict[str, Any]] = {
    "epub": {
        "flags": ("--epub",),
        "kwargs": {
            "type": str,
            "help": "EPUB file path",
            "metavar": "PATH",
        },
    },
}

# Video specific (from video.py)
VIDEO_ARGUMENTS: dict[str, dict[str, Any]] = {
    "setup": {
        "flags": ("--setup",),
        "kwargs": {
            "action": "store_true",
            "help": "Auto-detect GPU and install video dependencies",
        },
    },
    "video_url": {
        "flags": ("--video-url",),
        "kwargs": {
            "type": str,
            "help": "Video URL (YouTube, Vimeo)",
            "metavar": "URL",
        },
    },
    "video_file": {
        "flags": ("--video-file",),
        "kwargs": {
            "type": str,
            "help": "Local video file path",
            "metavar": "PATH",
        },
    },
    "video_playlist": {
        "flags": ("--video-playlist",),
        "kwargs": {
            "type": str,
            "help": "Playlist URL",
            "metavar": "URL",
        },
    },
    "video_languages": {
        "flags": ("--video-languages",),
        "kwargs": {
            "type": str,
            "default": "en",
            "help": "Transcript language preference (comma-separated)",
            "metavar": "LANGS",
        },
    },
    "visual": {
        "flags": ("--visual",),
        "kwargs": {
            "action": "store_true",
            "help": "Enable visual extraction (requires video-full deps)",
        },
    },
    "whisper_model": {
        "flags": ("--whisper-model",),
        "kwargs": {
            "type": str,
            "default": "base",
            "help": "Whisper model size (default: base)",
            "metavar": "MODEL",
        },
    },
    "visual_interval": {
        "flags": ("--visual-interval",),
        "kwargs": {
            "type": float,
            "default": 0.7,
            "help": "Visual scan interval in seconds (default: 0.7)",
            "metavar": "SECS",
        },
    },
    "visual_min_gap": {
        "flags": ("--visual-min-gap",),
        "kwargs": {
            "type": float,
            "default": 0.5,
            "help": "Min gap between extracted frames in seconds (default: 0.5)",
            "metavar": "SECS",
        },
    },
    "visual_similarity": {
        "flags": ("--visual-similarity",),
        "kwargs": {
            "type": float,
            "default": 3.0,
            "help": "Pixel-diff threshold for duplicate detection; lower = more frames (default: 3.0)",
            "metavar": "THRESH",
        },
    },
    "vision_ocr": {
        "flags": ("--vision-ocr",),
        "kwargs": {
            "action": "store_true",
            "help": "Use Claude Vision API as fallback for low-confidence code frames (requires ANTHROPIC_API_KEY, ~$0.004/frame)",
        },
    },
    "start_time": {
        "flags": ("--start-time",),
        "kwargs": {
            "type": str,
            "default": None,
            "metavar": "TIME",
            "help": "Start time for extraction (seconds, MM:SS, or HH:MM:SS). Single video only.",
        },
    },
    "end_time": {
        "flags": ("--end-time",),
        "kwargs": {
            "type": str,
            "default": None,
            "metavar": "TIME",
            "help": "End time for extraction (seconds, MM:SS, or HH:MM:SS). Single video only.",
        },
    },
}

# Multi-source config specific (from unified_scraper.py)
# Note: --fresh is in WEB_ARGUMENTS, shared with config sources via dynamic forwarding
CONFIG_ARGUMENTS: dict[str, dict[str, Any]] = {
    "merge_mode": {
        "flags": ("--merge-mode",),
        "kwargs": {
            "type": str,
            "choices": ["rule-based", "ai-enhanced", "claude-enhanced"],
            "help": "Override merge mode from config (rule-based or ai-enhanced). 'claude-enhanced' accepted as alias.",
            "metavar": "MODE",
        },
    },
    "skip_codebase_analysis": {
        "flags": ("--skip-codebase-analysis",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip C3.x codebase analysis for GitHub sources in unified config",
        },
    },
    # Note: --fresh is intentionally omitted here — it already lives in WEB_ARGUMENTS.
    # For unified config files, use `skill-seekers unified --fresh` directly.
}

# New source type arguments (v3.2.0+)
# These are minimal dicts since most flags are handled by each scraper's own argument module.
# The create command only needs the primary input flag for routing.

JUPYTER_ARGUMENTS: dict[str, dict[str, Any]] = {
    "notebook": {
        "flags": ("--notebook",),
        "kwargs": {"type": str, "help": "Jupyter Notebook file path (.ipynb)", "metavar": "PATH"},
    },
}

HTML_ARGUMENTS: dict[str, dict[str, Any]] = {
    "html_path": {
        "flags": ("--html-path",),
        "kwargs": {"type": str, "help": "Local HTML file or directory path", "metavar": "PATH"},
    },
}

OPENAPI_ARGUMENTS: dict[str, dict[str, Any]] = {
    "spec": {
        "flags": ("--spec",),
        "kwargs": {"type": str, "help": "OpenAPI/Swagger spec file path", "metavar": "PATH"},
    },
    "spec_url": {
        "flags": ("--spec-url",),
        "kwargs": {"type": str, "help": "OpenAPI/Swagger spec URL", "metavar": "URL"},
    },
}

ASCIIDOC_ARGUMENTS: dict[str, dict[str, Any]] = {
    "asciidoc_path": {
        "flags": ("--asciidoc-path",),
        "kwargs": {"type": str, "help": "AsciiDoc file or directory path", "metavar": "PATH"},
    },
}

PPTX_ARGUMENTS: dict[str, dict[str, Any]] = {
    "pptx": {
        "flags": ("--pptx",),
        "kwargs": {"type": str, "help": "PowerPoint file path (.pptx)", "metavar": "PATH"},
    },
}

RSS_ARGUMENTS: dict[str, dict[str, Any]] = {
    "feed_url": {
        "flags": ("--feed-url",),
        "kwargs": {"type": str, "help": "RSS/Atom feed URL", "metavar": "URL"},
    },
    "feed_path": {
        "flags": ("--feed-path",),
        "kwargs": {"type": str, "help": "RSS/Atom feed file path", "metavar": "PATH"},
    },
}

MANPAGE_ARGUMENTS: dict[str, dict[str, Any]] = {
    "man_names": {
        "flags": ("--man-names",),
        "kwargs": {
            "type": str,
            "help": "Comma-separated man page names (e.g., 'git,curl')",
            "metavar": "NAMES",
        },
    },
    "man_path": {
        "flags": ("--man-path",),
        "kwargs": {"type": str, "help": "Directory of man page files", "metavar": "PATH"},
    },
}

CONFLUENCE_ARGUMENTS: dict[str, dict[str, Any]] = {
    "conf_base_url": {
        "flags": ("--conf-base-url",),
        "kwargs": {"type": str, "help": "Confluence base URL", "metavar": "URL"},
    },
    "space_key": {
        "flags": ("--space-key",),
        "kwargs": {"type": str, "help": "Confluence space key", "metavar": "KEY"},
    },
    "conf_export_path": {
        "flags": ("--conf-export-path",),
        "kwargs": {"type": str, "help": "Confluence export directory", "metavar": "PATH"},
    },
}

NOTION_ARGUMENTS: dict[str, dict[str, Any]] = {
    "database_id": {
        "flags": ("--database-id",),
        "kwargs": {"type": str, "help": "Notion database ID", "metavar": "ID"},
    },
    "page_id": {
        "flags": ("--page-id",),
        "kwargs": {"type": str, "help": "Notion page ID", "metavar": "ID"},
    },
    "notion_export_path": {
        "flags": ("--notion-export-path",),
        "kwargs": {"type": str, "help": "Notion export directory", "metavar": "PATH"},
    },
}

CHAT_ARGUMENTS: dict[str, dict[str, Any]] = {
    "chat_export_path": {
        "flags": ("--chat-export-path",),
        "kwargs": {"type": str, "help": "Slack/Discord export directory", "metavar": "PATH"},
    },
    "platform": {
        "flags": ("--platform",),
        "kwargs": {
            "type": str,
            "choices": ["slack", "discord"],
            "default": "slack",
            "help": "Chat platform (default: slack)",
        },
    },
}

# =============================================================================
# TIER 3: ADVANCED/RARE ARGUMENTS
# =============================================================================
# Hidden from default help, shown only with --help-advanced

ADVANCED_ARGUMENTS: dict[str, dict[str, Any]] = {
    "from_json": {
        "flags": ("--from-json",),
        "kwargs": {
            "type": str,
            "help": "Build skill from pre-extracted JSON data (skip scraping). Supported by: PDF, Video, Jupyter, HTML, OpenAPI, AsciiDoc, PPTX, RSS, Manpage, Confluence, Notion, Chat.",
            "metavar": "PATH",
        },
    },
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


def get_universal_argument_names() -> set[str]:
    """Get set of universal argument names."""
    return set(UNIVERSAL_ARGUMENTS.keys())


def get_source_specific_arguments(source_type: str) -> dict[str, dict[str, Any]]:
    """Get source-specific arguments for a given source type.

    Args:
        source_type: One of 'web', 'github', 'local', 'pdf', 'config'

    Returns:
        Dict of argument definitions
    """
    source_args = {
        "web": WEB_ARGUMENTS,
        "github": GITHUB_ARGUMENTS,
        "local": LOCAL_ARGUMENTS,
        "pdf": PDF_ARGUMENTS,
        "word": WORD_ARGUMENTS,
        "epub": EPUB_ARGUMENTS,
        "video": VIDEO_ARGUMENTS,
        "config": CONFIG_ARGUMENTS,
        # New source types (v3.2.0+)
        "jupyter": JUPYTER_ARGUMENTS,
        "html": HTML_ARGUMENTS,
        "openapi": OPENAPI_ARGUMENTS,
        "asciidoc": ASCIIDOC_ARGUMENTS,
        "pptx": PPTX_ARGUMENTS,
        "rss": RSS_ARGUMENTS,
        "manpage": MANPAGE_ARGUMENTS,
        "confluence": CONFLUENCE_ARGUMENTS,
        "notion": NOTION_ARGUMENTS,
        "chat": CHAT_ARGUMENTS,
    }
    return source_args.get(source_type, {})


def get_compatible_arguments(source_type: str) -> list[str]:
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


def add_create_arguments(parser: argparse.ArgumentParser, mode: str = "default") -> None:
    """Add create command arguments to parser.

    Supports multiple help modes for progressive disclosure:
    - 'default': Universal arguments only (15 flags)
    - 'web': Universal + web-specific
    - 'github': Universal + github-specific
    - 'local': Universal + local-specific
    - 'pdf': Universal + pdf-specific
    - 'word': Universal + word-specific
    - 'epub': Universal + epub-specific
    - 'video': Universal + video-specific
    - 'advanced': Advanced/rare arguments
    - 'all': All 120+ arguments

    Args:
        parser: ArgumentParser to add arguments to
        mode: Help mode (default, web, github, local, pdf, word, advanced, all)
    """
    # Positional argument for source
    parser.add_argument(
        "source",
        nargs="?",
        type=str,
        help="Source to create skill from (URL, GitHub repo, directory, PDF, or config file)",
    )

    # Always add universal arguments
    for arg_name, arg_def in UNIVERSAL_ARGUMENTS.items():
        parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])

    # Add source-specific arguments based on mode
    if mode in ["web", "all"]:
        for arg_name, arg_def in WEB_ARGUMENTS.items():
            parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])

    if mode in ["github", "all"]:
        for arg_name, arg_def in GITHUB_ARGUMENTS.items():
            parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])

    if mode in ["local", "all"]:
        for arg_name, arg_def in LOCAL_ARGUMENTS.items():
            parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])

    if mode in ["pdf", "all"]:
        for arg_name, arg_def in PDF_ARGUMENTS.items():
            parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])

    if mode in ["word", "all"]:
        for arg_name, arg_def in WORD_ARGUMENTS.items():
            parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])

    if mode in ["epub", "all"]:
        for arg_name, arg_def in EPUB_ARGUMENTS.items():
            parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])

    if mode in ["video", "all"]:
        for arg_name, arg_def in VIDEO_ARGUMENTS.items():
            parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])

    if mode in ["config", "all"]:
        for arg_name, arg_def in CONFIG_ARGUMENTS.items():
            parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])

    # New source types (v3.2.0+)
    _NEW_SOURCE_ARGS = {
        "jupyter": JUPYTER_ARGUMENTS,
        "html": HTML_ARGUMENTS,
        "openapi": OPENAPI_ARGUMENTS,
        "asciidoc": ASCIIDOC_ARGUMENTS,
        "pptx": PPTX_ARGUMENTS,
        "rss": RSS_ARGUMENTS,
        "manpage": MANPAGE_ARGUMENTS,
        "confluence": CONFLUENCE_ARGUMENTS,
        "notion": NOTION_ARGUMENTS,
        "chat": CHAT_ARGUMENTS,
    }
    for stype, sargs in _NEW_SOURCE_ARGS.items():
        if mode in [stype, "all"]:
            for arg_name, arg_def in sargs.items():
                parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])

    # Add advanced arguments if requested
    if mode in ["advanced", "all"]:
        for arg_name, arg_def in ADVANCED_ARGUMENTS.items():
            parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])

    # Deprecated alias for backward compatibility (removed in v4.0.0)
    parser.add_argument(
        "--no-preserve-code",
        dest="no_preserve_code_blocks",
        action="store_true",
        help=argparse.SUPPRESS,
    )


def get_create_defaults() -> dict[str, Any]:
    """Build a defaults dict from a throwaway parser with all create arguments.

    Used by CreateCommand._is_explicitly_set() to compare argument values
    against their registered defaults instead of hardcoded values.
    """
    temp = argparse.ArgumentParser(add_help=False)
    add_create_arguments(temp, mode="all")
    return {action.dest: action.default for action in temp._actions if action.dest != "help"}
