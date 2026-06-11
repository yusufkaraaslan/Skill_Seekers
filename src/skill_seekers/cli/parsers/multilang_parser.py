"""Multilang subcommand parser."""

from .base import SubcommandParser


class MultilangParser(SubcommandParser):
    """Parser for multilang subcommand."""

    @property
    def name(self) -> str:
        return "multilang"

    @property
    def help(self) -> str:
        return "Multi-language documentation support"

    @property
    def description(self) -> str:
        return "Handle multi-language documentation scraping and organization"

    def add_arguments(self, parser):
        """Add multilang-specific arguments."""
        # dest must match multilang_support.main (args.skill_dir).
        parser.add_argument("skill_dir", metavar="skill_directory", help="Skill directory path")
        parser.add_argument(
            "--languages",
            nargs="+",
            help="Restrict --detect/--export to these languages (e.g., en es fr)",
        )
        parser.add_argument("--detect", action="store_true", help="Auto-detect languages")
        # Keep in sync with multilang_support.main()'s parser — a flag defined there
        # but not here is REJECTED by the unified CLI before main() runs.
        parser.add_argument("--report", action="store_true", help="Generate translation report")
        parser.add_argument("--export", help="Export by language to specified directory")
