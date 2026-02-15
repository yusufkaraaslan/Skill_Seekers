"""Analyze subcommand parser.

Uses shared argument definitions from arguments.analyze to ensure
consistency with the standalone codebase_scraper module.

Includes preset system support (Issue #268).
"""

from .base import SubcommandParser
from skill_seekers.cli.arguments.analyze import add_analyze_arguments


class AnalyzeParser(SubcommandParser):
    """Parser for analyze subcommand."""

    @property
    def name(self) -> str:
        return "analyze"

    @property
    def help(self) -> str:
        return "Analyze local codebase and extract code knowledge"

    @property
    def description(self) -> str:
        return "Standalone codebase analysis with patterns, tests, and guides"

    def add_arguments(self, parser):
        """Add analyze-specific arguments.

        Uses shared argument definitions to ensure consistency
        with codebase_scraper.py (standalone scraper).

        Includes preset system for simplified UX.
        """
        add_analyze_arguments(parser)
