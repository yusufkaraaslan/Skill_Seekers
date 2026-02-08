"""Install subcommand parser."""

from .base import SubcommandParser


class InstallParser(SubcommandParser):
    """Parser for install subcommand."""

    @property
    def name(self) -> str:
        return "install"

    @property
    def help(self) -> str:
        return "Complete workflow: fetch → scrape → enhance → package → upload"

    @property
    def description(self) -> str:
        return "One-command skill installation (AI enhancement MANDATORY)"

    def add_arguments(self, parser):
        """Add install-specific arguments."""
        parser.add_argument(
            "--config",
            required=True,
            help="Config name (e.g., 'react') or path (e.g., 'configs/custom.json')",
        )
        parser.add_argument(
            "--destination", default="output", help="Output directory (default: output/)"
        )
        parser.add_argument(
            "--no-upload", action="store_true", help="Skip automatic upload to Claude"
        )
        parser.add_argument(
            "--unlimited", action="store_true", help="Remove page limits during scraping"
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Preview workflow without executing"
        )
