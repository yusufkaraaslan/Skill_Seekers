"""PDF subcommand parser.

Uses shared argument definitions from arguments.pdf to ensure
consistency with the standalone pdf_scraper module.
"""

from .base import SubcommandParser
from skill_seekers.cli.arguments.pdf import add_pdf_arguments

class PDFParser(SubcommandParser):
    """Parser for pdf subcommand."""

    @property
    def name(self) -> str:
        return "pdf"

    @property
    def help(self) -> str:
        return "Extract from PDF file"

    @property
    def description(self) -> str:
        return "Extract content from PDF and generate skill"

    def add_arguments(self, parser):
        """Add pdf-specific arguments.

        Uses shared argument definitions to ensure consistency
        with pdf_scraper.py (standalone scraper).
        """
        add_pdf_arguments(parser)
