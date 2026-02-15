"""Update subcommand parser."""

from .base import SubcommandParser


class UpdateParser(SubcommandParser):
    """Parser for update subcommand."""

    @property
    def name(self) -> str:
        return "update"

    @property
    def help(self) -> str:
        return "Update docs without full rescrape"

    @property
    def description(self) -> str:
        return "Incrementally update documentation skills"

    def add_arguments(self, parser):
        """Add update-specific arguments."""
        parser.add_argument("skill_directory", help="Skill directory to update")
        parser.add_argument("--check-changes", action="store_true", help="Check for changes only")
        parser.add_argument("--force", action="store_true", help="Force update all files")
