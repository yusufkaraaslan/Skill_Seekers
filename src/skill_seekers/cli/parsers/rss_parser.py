"""RSS subcommand parser.

Uses shared argument definitions from arguments.rss to ensure
consistency with the standalone rss_scraper module.
"""

from .base import SubcommandParser
from skill_seekers.cli.arguments.rss import add_rss_arguments


class RssParser(SubcommandParser):
    """Parser for rss subcommand."""

    @property
    def name(self) -> str:
        return "rss"

    @property
    def help(self) -> str:
        return "Extract from RSS/Atom feeds"

    @property
    def description(self) -> str:
        return "Extract content from RSS/Atom feeds and generate skill"

    def add_arguments(self, parser):
        """Add rss-specific arguments.

        Uses shared argument definitions to ensure consistency
        with rss_scraper.py (standalone scraper).
        """
        add_rss_arguments(parser)
