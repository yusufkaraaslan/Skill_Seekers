"""Man page subcommand parser.

Uses shared argument definitions from arguments.manpage to ensure
consistency with the standalone man_scraper module.
"""

from .base import SubcommandParser
from skill_seekers.cli.arguments.manpage import add_manpage_arguments


class ManPageParser(SubcommandParser):
    """Parser for manpage subcommand."""

    @property
    def name(self) -> str:
        return "manpage"

    @property
    def help(self) -> str:
        return "Extract from man pages"

    @property
    def description(self) -> str:
        return "Extract content from man pages and generate skill"

    def add_arguments(self, parser):
        """Add manpage-specific arguments.

        Uses shared argument definitions to ensure consistency
        with man_scraper.py (standalone scraper).
        """
        add_manpage_arguments(parser)
