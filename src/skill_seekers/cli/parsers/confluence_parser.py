"""Confluence subcommand parser.

Uses shared argument definitions from arguments.confluence to ensure
consistency with the standalone confluence_scraper module.
"""

from .base import SubcommandParser
from skill_seekers.cli.arguments.confluence import add_confluence_arguments


class ConfluenceParser(SubcommandParser):
    """Parser for confluence subcommand."""

    @property
    def name(self) -> str:
        return "confluence"

    @property
    def help(self) -> str:
        return "Extract from Confluence wiki"

    @property
    def description(self) -> str:
        return "Extract content from Confluence wiki and generate skill"

    def add_arguments(self, parser):
        """Add confluence-specific arguments.

        Uses shared argument definitions to ensure consistency
        with confluence_scraper.py (standalone scraper).
        """
        add_confluence_arguments(parser)
