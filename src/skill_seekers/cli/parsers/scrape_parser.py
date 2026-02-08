"""Scrape subcommand parser."""

from .base import SubcommandParser


class ScrapeParser(SubcommandParser):
    """Parser for scrape subcommand."""

    @property
    def name(self) -> str:
        return "scrape"

    @property
    def help(self) -> str:
        return "Scrape documentation website"

    @property
    def description(self) -> str:
        return "Scrape documentation website and generate skill"

    def add_arguments(self, parser):
        """Add scrape-specific arguments."""
        parser.add_argument("url", nargs="?", help="Documentation URL (positional argument)")
        parser.add_argument("--config", help="Config JSON file")
        parser.add_argument("--name", help="Skill name")
        parser.add_argument("--description", help="Skill description")
        parser.add_argument(
            "--max-pages",
            type=int,
            dest="max_pages",
            help="Maximum pages to scrape (override config)",
        )
        parser.add_argument(
            "--skip-scrape", action="store_true", help="Skip scraping, use cached data"
        )
        parser.add_argument("--enhance", action="store_true", help="AI enhancement (API)")
        parser.add_argument("--enhance-local", action="store_true", help="AI enhancement (local)")
        parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
        parser.add_argument(
            "--async", dest="async_mode", action="store_true", help="Use async scraping"
        )
        parser.add_argument("--workers", type=int, help="Number of async workers")
