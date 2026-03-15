"""PPTX subcommand parser.

Uses shared argument definitions from arguments.pptx to ensure
consistency with the standalone pptx_scraper module.
"""

from .base import SubcommandParser
from skill_seekers.cli.arguments.pptx import add_pptx_arguments


class PptxParser(SubcommandParser):
    """Parser for pptx subcommand."""

    @property
    def name(self) -> str:
        return "pptx"

    @property
    def help(self) -> str:
        return "Extract from PowerPoint presentations (.pptx)"

    @property
    def description(self) -> str:
        return "Extract content from PowerPoint presentations (.pptx) and generate skill"

    def add_arguments(self, parser):
        """Add pptx-specific arguments.

        Uses shared argument definitions to ensure consistency
        with pptx_scraper.py (standalone scraper).
        """
        add_pptx_arguments(parser)
