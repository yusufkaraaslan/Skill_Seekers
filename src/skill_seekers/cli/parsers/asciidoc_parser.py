"""AsciiDoc subcommand parser.

Uses shared argument definitions from arguments.asciidoc to ensure
consistency with the standalone asciidoc_scraper module.
"""

from .base import SubcommandParser
from skill_seekers.cli.arguments.asciidoc import add_asciidoc_arguments


class AsciiDocParser(SubcommandParser):
    """Parser for asciidoc subcommand."""

    @property
    def name(self) -> str:
        return "asciidoc"

    @property
    def help(self) -> str:
        return "Extract from AsciiDoc documents (.adoc)"

    @property
    def description(self) -> str:
        return "Extract content from AsciiDoc documents (.adoc) and generate skill"

    def add_arguments(self, parser):
        """Add asciidoc-specific arguments.

        Uses shared argument definitions to ensure consistency
        with asciidoc_scraper.py (standalone scraper).
        """
        add_asciidoc_arguments(parser)
