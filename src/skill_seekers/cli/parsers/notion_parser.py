"""Notion subcommand parser.

Uses shared argument definitions from arguments.notion to ensure
consistency with the standalone notion_scraper module.
"""

from .base import SubcommandParser
from skill_seekers.cli.arguments.notion import add_notion_arguments


class NotionParser(SubcommandParser):
    """Parser for notion subcommand."""

    @property
    def name(self) -> str:
        return "notion"

    @property
    def help(self) -> str:
        return "Extract from Notion pages"

    @property
    def description(self) -> str:
        return "Extract content from Notion pages and generate skill"

    def add_arguments(self, parser):
        """Add notion-specific arguments.

        Uses shared argument definitions to ensure consistency
        with notion_scraper.py (standalone scraper).
        """
        add_notion_arguments(parser)
