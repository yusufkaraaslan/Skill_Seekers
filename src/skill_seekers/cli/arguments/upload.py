"""Upload command argument definitions.

This module defines ALL arguments for the upload command in ONE place.
Both upload_skill.py (standalone) and parsers/upload_parser.py (unified CLI)
import and use these definitions.
"""

import argparse
from typing import Any

UPLOAD_ARGUMENTS: dict[str, dict[str, Any]] = {
    # Positional argument
    "package_file": {
        "flags": ("package_file",),
        "kwargs": {
            "type": str,
            "help": "Path to skill package file (e.g., output/react.zip)",
        },
    },
    # Target platform
    "target": {
        "flags": ("--target",),
        "kwargs": {
            "type": str,
            "choices": ["claude", "gemini", "openai", "chroma", "weaviate"],
            "default": "claude",
            "help": "Target platform (default: claude)",
            "metavar": "PLATFORM",
        },
    },
    "api_key": {
        "flags": ("--api-key",),
        "kwargs": {
            "type": str,
            "help": "Platform API key (or set environment variable)",
            "metavar": "KEY",
        },
    },
    # ChromaDB options
    "chroma_url": {
        "flags": ("--chroma-url",),
        "kwargs": {
            "type": str,
            "help": "ChromaDB URL (default: http://localhost:8000 for HTTP, or use --persist-directory for local)",
            "metavar": "URL",
        },
    },
    "persist_directory": {
        "flags": ("--persist-directory",),
        "kwargs": {
            "type": str,
            "help": "Local directory for persistent ChromaDB storage (default: ./chroma_db)",
            "metavar": "DIR",
        },
    },
    # Embedding options
    "embedding_function": {
        "flags": ("--embedding-function",),
        "kwargs": {
            "type": str,
            "choices": ["openai", "sentence-transformers", "none"],
            "help": "Embedding function for ChromaDB/Weaviate (default: platform default)",
            "metavar": "FUNC",
        },
    },
    "openai_api_key": {
        "flags": ("--openai-api-key",),
        "kwargs": {
            "type": str,
            "help": "OpenAI API key for embeddings (or set OPENAI_API_KEY env var)",
            "metavar": "KEY",
        },
    },
    # Weaviate options
    "weaviate_url": {
        "flags": ("--weaviate-url",),
        "kwargs": {
            "type": str,
            "default": "http://localhost:8080",
            "help": "Weaviate URL (default: http://localhost:8080)",
            "metavar": "URL",
        },
    },
    "use_cloud": {
        "flags": ("--use-cloud",),
        "kwargs": {
            "action": "store_true",
            "help": "Use Weaviate Cloud (requires --api-key and --cluster-url)",
        },
    },
    "cluster_url": {
        "flags": ("--cluster-url",),
        "kwargs": {
            "type": str,
            "help": "Weaviate Cloud cluster URL (e.g., https://xxx.weaviate.network)",
            "metavar": "URL",
        },
    },
}

def add_upload_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all upload command arguments to a parser."""
    for arg_name, arg_def in UPLOAD_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = arg_def["kwargs"]
        parser.add_argument(*flags, **kwargs)
