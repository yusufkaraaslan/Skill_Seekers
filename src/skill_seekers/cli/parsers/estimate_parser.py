"""Estimate subcommand parser."""

from skill_seekers.cli.constants import DEFAULT_MAX_DISCOVERY

from .base import SubcommandParser


class EstimateParser(SubcommandParser):
    """Parser for estimate subcommand."""

    @property
    def name(self) -> str:
        return "estimate"

    @property
    def help(self) -> str:
        return "Estimate page count before scraping"

    @property
    def description(self) -> str:
        return "Estimate total pages for documentation scraping"

    def add_arguments(self, parser):
        """Add estimate-specific arguments."""
        parser.add_argument("config", nargs="?", help="Config JSON file")
        parser.add_argument("--all", action="store_true", help="List all available configs")
        parser.add_argument(
            "--max-discovery",
            "-m",
            type=int,
            default=DEFAULT_MAX_DISCOVERY,
            help=(
                f"Maximum pages to discover (default: {DEFAULT_MAX_DISCOVERY}, use -1 for unlimited). "
                "Without a default the unified CLI passed None, which estimate_pages treats as "
                "unlimited."
            ),
        )
        # Keep in sync with estimate_pages.main()'s parser — a flag defined there
        # but not here is REJECTED by the unified CLI before main() runs.
        parser.add_argument(
            "--unlimited",
            "-u",
            action="store_true",
            help="Remove discovery limit - discover all pages (same as --max-discovery -1)",
        )
        parser.add_argument(
            "--timeout",
            "-t",
            type=int,
            default=30,
            help="HTTP request timeout in seconds (default: 30)",
        )
