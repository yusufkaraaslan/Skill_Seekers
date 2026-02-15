"""Unified subcommand parser.

Uses shared argument definitions from arguments.unified to ensure
consistency with the standalone unified_scraper module.
"""

from .base import SubcommandParser
from skill_seekers.cli.arguments.unified import add_unified_arguments

class UnifiedParser(SubcommandParser):
    """Parser for unified subcommand."""

    @property
    def name(self) -> str:
        return "unified"

    @property
    def help(self) -> str:
        return "Multi-source scraping (docs + GitHub + PDF)"

    @property
    def description(self) -> str:
        return "Combine multiple sources into one skill"

    def add_arguments(self, parser):
        """Add unified-specific arguments.

        Uses shared argument definitions to ensure consistency
        with unified_scraper.py (standalone scraper).
        """
        add_unified_arguments(parser)
