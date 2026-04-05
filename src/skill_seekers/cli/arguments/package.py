"""Package command argument definitions.

This module defines ALL arguments for the package command in ONE place.
Both package_skill.py (standalone) and parsers/package_parser.py (unified CLI)
import and use these definitions.
"""

import argparse
from typing import Any

from .common import DEFAULT_CHUNK_TOKENS, DEFAULT_CHUNK_OVERLAP_TOKENS

PACKAGE_ARGUMENTS: dict[str, dict[str, Any]] = {
    # Positional argument
    "skill_directory": {
        "flags": ("skill_directory",),
        "kwargs": {
            "type": str,
            "help": "Skill directory path (e.g., output/react/)",
        },
    },
    # Control options
    "no_open": {
        "flags": ("--no-open",),
        "kwargs": {
            "action": "store_true",
            "help": "Don't open output folder after packaging",
        },
    },
    "skip_quality_check": {
        "flags": ("--skip-quality-check",),
        "kwargs": {
            "action": "store_true",
            "help": "Skip quality checks before packaging",
        },
    },
    # Target platform
    "target": {
        "flags": ("--target",),
        "kwargs": {
            "type": str,
            "choices": [
                "claude",
                "gemini",
                "openai",
                "markdown",
                "langchain",
                "llama-index",
                "haystack",
                "weaviate",
                "chroma",
                "faiss",
                "qdrant",
                "pinecone",
            ],
            "default": "claude",
            "help": "Target LLM platform (default: claude)",
            "metavar": "PLATFORM",
        },
    },
    "upload": {
        "flags": ("--upload",),
        "kwargs": {
            "action": "store_true",
            "help": "Automatically upload after packaging (requires platform API key)",
        },
    },
    # Streaming options
    "streaming": {
        "flags": ("--streaming",),
        "kwargs": {
            "action": "store_true",
            "help": "Use streaming ingestion for large docs (memory-efficient)",
        },
    },
    "streaming_chunk_chars": {
        "flags": ("--streaming-chunk-chars",),
        "kwargs": {
            "type": int,
            "default": 4000,
            "help": "Maximum characters per chunk (streaming mode, default: 4000)",
            "metavar": "N",
        },
    },
    "streaming_overlap_chars": {
        "flags": ("--streaming-overlap-chars",),
        "kwargs": {
            "type": int,
            "default": 200,
            "help": "Character overlap between chunks (streaming mode, default: 200)",
            "metavar": "N",
        },
    },
    "batch_size": {
        "flags": ("--batch-size",),
        "kwargs": {
            "type": int,
            "default": 100,
            "help": "Number of chunks per batch (streaming mode, default: 100)",
            "metavar": "N",
        },
    },
    # RAG chunking options
    "chunk_for_rag": {
        "flags": ("--chunk-for-rag",),
        "kwargs": {
            "action": "store_true",
            "help": "Enable intelligent chunking for RAG platforms (auto-enabled for RAG adaptors)",
        },
    },
    "chunk_tokens": {
        "flags": ("--chunk-tokens",),
        "kwargs": {
            "type": int,
            "default": DEFAULT_CHUNK_TOKENS,
            "help": f"Maximum tokens per chunk (default: {DEFAULT_CHUNK_TOKENS})",
            "metavar": "N",
        },
    },
    "chunk_overlap_tokens": {
        "flags": ("--chunk-overlap-tokens",),
        "kwargs": {
            "type": int,
            "default": DEFAULT_CHUNK_OVERLAP_TOKENS,
            "help": f"Overlap between chunks in tokens (default: {DEFAULT_CHUNK_OVERLAP_TOKENS})",
            "metavar": "N",
        },
    },
    "no_preserve_code_blocks": {
        "flags": ("--no-preserve-code-blocks",),
        "kwargs": {
            "action": "store_true",
            "help": "Allow code block splitting (default: code blocks preserved)",
        },
    },
}


def add_package_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all package command arguments to a parser."""
    for arg_name, arg_def in PACKAGE_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = arg_def["kwargs"]
        parser.add_argument(*flags, **kwargs)

    # Deprecated alias for backward compatibility (removed in v4.0.0)
    parser.add_argument(
        "--no-preserve-code",
        dest="no_preserve_code_blocks",
        action="store_true",
        help=argparse.SUPPRESS,
    )
