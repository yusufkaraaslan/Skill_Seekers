"""Estimate subcommand parser."""

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
        parser.add_argument("--max-discovery", type=int, help="Max pages to discover")
