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
        parser.add_argument("skill_directory", help="Skill directory path")
        parser.add_argument("--languages", nargs="+", help="Languages to process (e.g., en es fr)")
        parser.add_argument("--detect", action="store_true", help="Auto-detect languages")
