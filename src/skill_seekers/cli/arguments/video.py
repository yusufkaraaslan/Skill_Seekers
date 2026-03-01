"""Video command argument definitions.

This module defines ALL arguments for the video command in ONE place.
Both video_scraper.py (standalone) and parsers/video_parser.py (unified CLI)
import and use these definitions.

Shared arguments (name, description, output, enhance-level, api-key,
dry-run, verbose, quiet, workflow args) come from common.py / workflow.py
via ``add_all_standard_arguments()``.
"""

import argparse
from typing import Any

from .common import add_all_standard_arguments

# Video-specific argument definitions as data structure
# NOTE: Shared args (name, description, output, enhance_level, api_key, dry_run,
#       verbose, quiet, workflow args) are registered by add_all_standard_arguments().
VIDEO_ARGUMENTS: dict[str, dict[str, Any]] = {
    "url": {
        "flags": ("--url",),
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
    "playlist": {
        "flags": ("--playlist",),
        "kwargs": {
            "type": str,
            "help": "Playlist URL",
            "metavar": "URL",
        },
    },
    "languages": {
        "flags": ("--languages",),
        "kwargs": {
            "type": str,
            "default": "en",
            "help": "Transcript language preference (comma-separated, default: en)",
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
    "from_json": {
        "flags": ("--from-json",),
        "kwargs": {
            "type": str,
            "help": "Build skill from extracted JSON",
            "metavar": "FILE",
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
            "help": "Minimum gap between extracted frames in seconds (default: 0.5)",
            "metavar": "SECS",
        },
    },
    "visual_similarity": {
        "flags": ("--visual-similarity",),
        "kwargs": {
            "type": float,
            "default": 3.0,
            "help": "Pixel-diff threshold for duplicate frame detection; lower = more frames kept (default: 3.0)",
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
    "setup": {
        "flags": ("--setup",),
        "kwargs": {
            "action": "store_true",
            "help": "Auto-detect GPU and install visual extraction deps (PyTorch, easyocr, etc.)",
        },
    },
}


def add_video_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all video command arguments to a parser.

    Registers shared args (name, description, output, enhance-level, api-key,
    dry-run, verbose, quiet, workflow args) via add_all_standard_arguments(),
    then adds video-specific args on top.

    The default for --enhance-level is overridden to 0 (disabled) for video.
    """
    # Shared universal args first
    add_all_standard_arguments(parser)

    # Override enhance-level default to 0 for video
    for action in parser._actions:
        if hasattr(action, "dest") and action.dest == "enhance_level":
            action.default = 0
            action.help = (
                "AI enhancement level (auto-detects API vs LOCAL mode): "
                "0=disabled (default for video), 1=SKILL.md only, 2=+architecture/config, 3=full enhancement. "
                "Mode selection: uses API if ANTHROPIC_API_KEY is set, otherwise LOCAL (Claude Code)"
            )

    # Video-specific args
    for arg_name, arg_def in VIDEO_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = arg_def["kwargs"]
        parser.add_argument(*flags, **kwargs)
