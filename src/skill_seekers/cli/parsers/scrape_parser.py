"""Scrape subcommand parser.

Uses shared argument definitions from arguments.scrape to ensure
consistency with the standalone doc_scraper module.
"""

from .base import SubcommandParser
from skill_seekers.cli.arguments.scrape import add_scrape_arguments

class ScrapeParser(SubcommandParser):
    """Parser for scrape subcommand."""

    @property
    def name(self) -> str:
        return "scrape"

    @property
    def help(self) -> str:
        return "Scrape documentation website"

    @property
    def description(self) -> str:
        return "Scrape documentation website and generate skill"

    def add_arguments(self, parser):
        """Add scrape-specific arguments.

        Uses shared argument definitions to ensure consistency
        with doc_scraper.py (standalone scraper).
        """
        # Add all scrape arguments from shared definitions
        # This ensures the unified CLI has exactly the same arguments
        # as the standalone scraper - they CANNOT drift out of sync
        add_scrape_arguments(parser)
