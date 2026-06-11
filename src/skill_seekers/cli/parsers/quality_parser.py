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
        # dest must match what quality_metrics.main reads (args.skill_dir);
        # metavar keeps the help display as "skill_directory".
        parser.add_argument("skill_dir", metavar="skill_directory", help="Skill directory path")
        parser.add_argument("--report", action="store_true", help="Generate detailed report")
        # Keep in sync with quality_metrics.main()'s parser — a flag defined there
        # but not here is REJECTED by the unified CLI before main() runs.
        parser.add_argument("--output", help="Output path for JSON report")
        parser.add_argument(
            "--threshold",
            type=float,
            default=None,
            help="Quality gate threshold (0-10). When set, exit non-zero if the "
            "skill scores below it; without it the command only reports.",
        )
