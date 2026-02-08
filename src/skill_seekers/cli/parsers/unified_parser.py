"""Unified subcommand parser."""

from .base import SubcommandParser


class UnifiedParser(SubcommandParser):
    """Parser for unified subcommand."""

    @property
    def name(self) -> str:
        return "unified"

    @property
    def help(self) -> str:
        return "Multi-source scraping (docs + GitHub + PDF)"

    @property
    def description(self) -> str:
        return "Combine multiple sources into one skill"

    def add_arguments(self, parser):
        """Add unified-specific arguments."""
        parser.add_argument("--config", required=True, help="Unified config JSON file")
        parser.add_argument("--merge-mode", help="Merge mode (rule-based, claude-enhanced)")
        parser.add_argument(
            "--fresh", action="store_true", help="Clear existing data and start fresh"
        )
        parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
