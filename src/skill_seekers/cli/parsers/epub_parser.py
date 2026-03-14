"""EPUB subcommand parser.

Uses shared argument definitions from arguments.epub to ensure
consistency with the standalone epub_scraper module.
"""

from .base import SubcommandParser
from skill_seekers.cli.arguments.epub import add_epub_arguments


class EpubParser(SubcommandParser):
    """Parser for epub subcommand."""

    @property
    def name(self) -> str:
        return "epub"

    @property
    def help(self) -> str:
        return "Extract from EPUB e-book (.epub)"

    @property
    def description(self) -> str:
        return "Extract content from EPUB e-book (.epub) and generate skill"

    def add_arguments(self, parser):
        """Add epub-specific arguments.

        Uses shared argument definitions to ensure consistency
        with epub_scraper.py (standalone scraper).
        """
        add_epub_arguments(parser)
