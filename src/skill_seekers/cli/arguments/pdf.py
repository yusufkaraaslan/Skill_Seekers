"""PDF command argument definitions.

This module defines ALL arguments for the pdf command in ONE place.
Both pdf_scraper.py (standalone) and parsers/pdf_parser.py (unified CLI)
import and use these definitions.
"""

import argparse
from typing import Dict, Any


PDF_ARGUMENTS: Dict[str, Dict[str, Any]] = {
    "config": {
        "flags": ("--config",),
        "kwargs": {
            "type": str,
            "help": "PDF config JSON file",
            "metavar": "FILE",
        },
    },
    "pdf": {
        "flags": ("--pdf",),
        "kwargs": {
            "type": str,
            "help": "Direct PDF file path",
            "metavar": "PATH",
        },
    },
    "name": {
        "flags": ("--name",),
        "kwargs": {
            "type": str,
            "help": "Skill name (used with --pdf)",
            "metavar": "NAME",
        },
    },
    "description": {
        "flags": ("--description",),
        "kwargs": {
            "type": str,
            "help": "Skill description",
            "metavar": "TEXT",
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
}


def add_pdf_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all pdf command arguments to a parser."""
    for arg_name, arg_def in PDF_ARGUMENTS.items():
        flags = arg_def["flags"]
        kwargs = arg_def["kwargs"]
        parser.add_argument(*flags, **kwargs)
