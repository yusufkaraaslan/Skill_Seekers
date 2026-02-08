"""Analyze subcommand parser."""

from .base import SubcommandParser


class AnalyzeParser(SubcommandParser):
    """Parser for analyze subcommand."""

    @property
    def name(self) -> str:
        return "analyze"

    @property
    def help(self) -> str:
        return "Analyze local codebase and extract code knowledge"

    @property
    def description(self) -> str:
        return "Standalone codebase analysis with C3.x features (patterns, tests, guides)"

    def add_arguments(self, parser):
        """Add analyze-specific arguments."""
        parser.add_argument("--directory", required=True, help="Directory to analyze")
        parser.add_argument(
            "--output",
            default="output/codebase/",
            help="Output directory (default: output/codebase/)",
        )

        # Preset selection (NEW - recommended way)
        parser.add_argument(
            "--preset",
            choices=["quick", "standard", "comprehensive"],
            help="Analysis preset: quick (1-2 min), standard (5-10 min, DEFAULT), comprehensive (20-60 min)",
        )
        parser.add_argument(
            "--preset-list", action="store_true", help="Show available presets and exit"
        )

        # Legacy preset flags (kept for backward compatibility)
        parser.add_argument(
            "--quick",
            action="store_true",
            help="[DEPRECATED] Quick analysis - use '--preset quick' instead",
        )
        parser.add_argument(
            "--comprehensive",
            action="store_true",
            help="[DEPRECATED] Comprehensive analysis - use '--preset comprehensive' instead",
        )

        # Deprecated depth flag
        parser.add_argument(
            "--depth",
            choices=["surface", "deep", "full"],
            help="[DEPRECATED] Analysis depth - use --preset instead",
        )
        parser.add_argument(
            "--languages", help="Comma-separated languages (e.g., Python,JavaScript,C++)"
        )
        parser.add_argument("--file-patterns", help="Comma-separated file patterns")
        parser.add_argument(
            "--enhance",
            action="store_true",
            help="Enable AI enhancement (default level 1 = SKILL.md only)",
        )
        parser.add_argument(
            "--enhance-level",
            type=int,
            choices=[0, 1, 2, 3],
            default=None,
            help="AI enhancement level: 0=off, 1=SKILL.md only (default), 2=+Architecture+Config, 3=full",
        )
        parser.add_argument("--skip-api-reference", action="store_true", help="Skip API docs")
        parser.add_argument("--skip-dependency-graph", action="store_true", help="Skip dep graph")
        parser.add_argument("--skip-patterns", action="store_true", help="Skip pattern detection")
        parser.add_argument("--skip-test-examples", action="store_true", help="Skip test examples")
        parser.add_argument("--skip-how-to-guides", action="store_true", help="Skip guides")
        parser.add_argument("--skip-config-patterns", action="store_true", help="Skip config")
        parser.add_argument(
            "--skip-docs", action="store_true", help="Skip project docs (README, docs/)"
        )
        parser.add_argument("--no-comments", action="store_true", help="Skip comments")
        parser.add_argument("--verbose", action="store_true", help="Verbose logging")
