"""GitHub subcommand parser.

Uses shared argument definitions from arguments.github to ensure
consistency with the standalone github_scraper module.
"""

from .base import SubcommandParser
from skill_seekers.cli.arguments.github import add_github_arguments

class GitHubParser(SubcommandParser):
    """Parser for github subcommand."""

    @property
    def name(self) -> str:
        return "github"

    @property
    def help(self) -> str:
        return "Scrape GitHub repository"

    @property
    def description(self) -> str:
        return "Scrape GitHub repository and generate skill"

    def add_arguments(self, parser):
        """Add github-specific arguments.

        Uses shared argument definitions to ensure consistency
        with github_scraper.py (standalone scraper).
        """
        # Add all github arguments from shared definitions
        # This ensures the unified CLI has exactly the same arguments
        # as the standalone scraper - they CANNOT drift out of sync
        add_github_arguments(parser)
