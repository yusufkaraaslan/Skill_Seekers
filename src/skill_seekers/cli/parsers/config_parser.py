"""Config subcommand parser."""

from .base import SubcommandParser


class ConfigParser(SubcommandParser):
    """Parser for config subcommand."""

    @property
    def name(self) -> str:
        return "config"

    @property
    def help(self) -> str:
        return "Configure GitHub tokens, API keys, and settings"

    @property
    def description(self) -> str:
        return "Interactive configuration wizard"

    def add_arguments(self, parser):
        """Add config-specific arguments."""
        parser.add_argument(
            "--github", action="store_true", help="Go directly to GitHub token setup"
        )
        parser.add_argument("--api-keys", action="store_true", help="Go directly to API keys setup")
        parser.add_argument(
            "--show", action="store_true", help="Show current configuration and exit"
        )
        parser.add_argument("--test", action="store_true", help="Test connections and exit")
