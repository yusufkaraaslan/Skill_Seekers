"""GitHub subcommand parser."""

from .base import SubcommandParser


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
        """Add github-specific arguments."""
        parser.add_argument("--config", help="Config JSON file")
        parser.add_argument("--repo", help="GitHub repo (owner/repo)")
        parser.add_argument("--name", help="Skill name")
        parser.add_argument("--description", help="Skill description")
        parser.add_argument("--enhance", action="store_true", help="AI enhancement (API)")
        parser.add_argument("--enhance-local", action="store_true", help="AI enhancement (local)")
        parser.add_argument("--api-key", type=str, help="Anthropic API key for --enhance")
        parser.add_argument(
            "--non-interactive",
            action="store_true",
            help="Non-interactive mode (fail fast on rate limits)",
        )
        parser.add_argument("--profile", type=str, help="GitHub profile name from config")
