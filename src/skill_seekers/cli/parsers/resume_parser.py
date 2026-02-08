"""Resume subcommand parser."""

from .base import SubcommandParser


class ResumeParser(SubcommandParser):
    """Parser for resume subcommand."""

    @property
    def name(self) -> str:
        return "resume"

    @property
    def help(self) -> str:
        return "Resume interrupted scraping job"

    @property
    def description(self) -> str:
        return "Continue from saved progress checkpoint"

    def add_arguments(self, parser):
        """Add resume-specific arguments."""
        parser.add_argument(
            "job_id", nargs="?", help="Job ID to resume (or use --list to see available jobs)"
        )
        parser.add_argument("--list", action="store_true", help="List all resumable jobs")
        parser.add_argument("--clean", action="store_true", help="Clean up old progress files")
