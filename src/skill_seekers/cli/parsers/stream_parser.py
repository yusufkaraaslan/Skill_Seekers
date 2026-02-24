"""Stream subcommand parser."""

from .base import SubcommandParser


class StreamParser(SubcommandParser):
    """Parser for stream subcommand."""

    @property
    def name(self) -> str:
        return "stream"

    @property
    def help(self) -> str:
        return "Stream large files chunk-by-chunk"

    @property
    def description(self) -> str:
        return "Ingest large documentation files using streaming"

    def add_arguments(self, parser):
        """Add stream-specific arguments."""
        parser.add_argument("input_file", help="Large file to stream")
        parser.add_argument(
            "--streaming-chunk-chars",
            type=int,
            default=4000,
            help="Maximum characters per chunk (default: 4000)",
        )
        parser.add_argument("--output", help="Output directory")
