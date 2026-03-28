"""Doctor subcommand parser."""

from .base import SubcommandParser


class DoctorParser(SubcommandParser):
    """Parser for doctor subcommand."""

    @property
    def name(self) -> str:
        return "doctor"

    @property
    def help(self) -> str:
        return "Check environment health and dependencies"

    @property
    def description(self) -> str:
        return "Run diagnostic checks on Python version, dependencies, API keys, and more"

    def add_arguments(self, parser):
        """Add doctor-specific arguments."""
        parser.add_argument(
            "--verbose", "-v", action="store_true", help="Show detailed diagnostic info"
        )
