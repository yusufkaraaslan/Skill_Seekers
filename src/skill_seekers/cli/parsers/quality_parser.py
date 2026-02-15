"""Quality subcommand parser."""

from .base import SubcommandParser


class QualityParser(SubcommandParser):
    """Parser for quality subcommand."""

    @property
    def name(self) -> str:
        return "quality"

    @property
    def help(self) -> str:
        return "Quality scoring for SKILL.md"

    @property
    def description(self) -> str:
        return "Analyze and score skill documentation quality"

    def add_arguments(self, parser):
        """Add quality-specific arguments."""
        parser.add_argument("skill_directory", help="Skill directory path")
        parser.add_argument("--report", action="store_true", help="Generate detailed report")
        parser.add_argument("--threshold", type=float, default=7.0, help="Quality threshold (0-10)")
