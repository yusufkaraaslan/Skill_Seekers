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
        # dest must match incremental_updater.main (args.skill_dir).
        parser.add_argument(
            "skill_dir", metavar="skill_directory", help="Skill directory to update"
        )
        parser.add_argument("--check-changes", action="store_true", help="Check for changes only")
        parser.add_argument("--force", action="store_true", help="Force update all files")
        # Keep in sync with incremental_updater.main()'s parser — a flag defined there
        # but not here is REJECTED by the unified CLI before main() runs.
        parser.add_argument("--generate-package", help="Generate update package at specified path")
        parser.add_argument("--apply-update", help="Apply update package from specified path")
