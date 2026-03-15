"""Chat subcommand parser.

Uses shared argument definitions from arguments.chat to ensure
consistency with the standalone chat_scraper module.
"""

from .base import SubcommandParser
from skill_seekers.cli.arguments.chat import add_chat_arguments


class ChatParser(SubcommandParser):
    """Parser for chat subcommand."""

    @property
    def name(self) -> str:
        return "chat"

    @property
    def help(self) -> str:
        return "Extract from Slack/Discord chat exports"

    @property
    def description(self) -> str:
        return "Extract content from Slack/Discord chat exports and generate skill"

    def add_arguments(self, parser):
        """Add chat-specific arguments.

        Uses shared argument definitions to ensure consistency
        with chat_scraper.py (standalone scraper).
        """
        add_chat_arguments(parser)
