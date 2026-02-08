"""Enhance-status subcommand parser."""

from .base import SubcommandParser


class EnhanceStatusParser(SubcommandParser):
    """Parser for enhance-status subcommand."""

    @property
    def name(self) -> str:
        return "enhance-status"

    @property
    def help(self) -> str:
        return "Check enhancement status (for background/daemon modes)"

    @property
    def description(self) -> str:
        return "Monitor background enhancement processes"

    def add_arguments(self, parser):
        """Add enhance-status-specific arguments."""
        parser.add_argument("skill_directory", help="Skill directory path")
        parser.add_argument("--watch", "-w", action="store_true", help="Watch in real-time")
        parser.add_argument("--json", action="store_true", help="JSON output")
        parser.add_argument("--interval", type=int, default=2, help="Watch interval in seconds")
