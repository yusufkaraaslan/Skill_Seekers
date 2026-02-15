"""Extract-test-examples subcommand parser."""

from .base import SubcommandParser


class TestExamplesParser(SubcommandParser):
    """Parser for extract-test-examples subcommand."""

    @property
    def name(self) -> str:
        return "extract-test-examples"

    @property
    def help(self) -> str:
        return "Extract usage examples from test files"

    @property
    def description(self) -> str:
        return "Analyze test files to extract real API usage patterns"

    def add_arguments(self, parser):
        """Add extract-test-examples-specific arguments."""
        parser.add_argument("directory", nargs="?", help="Directory containing test files")
        parser.add_argument("--file", help="Single test file to analyze")
        parser.add_argument(
            "--language", help="Filter by programming language (python, javascript, etc.)"
        )
        parser.add_argument(
            "--min-confidence",
            type=float,
            default=0.5,
            help="Minimum confidence threshold (0.0-1.0, default: 0.5)",
        )
        parser.add_argument(
            "--max-per-file", type=int, default=10, help="Maximum examples per file (default: 10)"
        )
        parser.add_argument("--json", action="store_true", help="Output JSON format")
        parser.add_argument("--markdown", action="store_true", help="Output Markdown format")
