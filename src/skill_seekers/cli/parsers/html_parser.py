"""HTML subcommand parser.

Uses shared argument definitions from arguments.html to ensure
consistency with the standalone html_scraper module.
"""

from .base import SubcommandParser
from skill_seekers.cli.arguments.html import add_html_arguments


class HtmlParser(SubcommandParser):
    """Parser for html subcommand."""

    @property
    def name(self) -> str:
        return "html"

    @property
    def help(self) -> str:
        return "Extract from local HTML files (.html/.htm)"

    @property
    def description(self) -> str:
        return "Extract content from local HTML files (.html/.htm) and generate skill"

    def add_arguments(self, parser):
        """Add html-specific arguments.

        Uses shared argument definitions to ensure consistency
        with html_scraper.py (standalone scraper).
        """
        add_html_arguments(parser)
