"""Word document subcommand parser.

Uses shared argument definitions from arguments.word to ensure
consistency with the standalone word_scraper module.
"""

from .base import SubcommandParser
from skill_seekers.cli.arguments.word import add_word_arguments


class WordParser(SubcommandParser):
    """Parser for word subcommand."""

    @property
    def name(self) -> str:
        return "word"

    @property
    def help(self) -> str:
        return "Extract from Word document (.docx)"

    @property
    def description(self) -> str:
        return "Extract content from Word document (.docx) and generate skill"

    def add_arguments(self, parser):
        """Add word-specific arguments.

        Uses shared argument definitions to ensure consistency
        with word_scraper.py (standalone scraper).
        """
        add_word_arguments(parser)
