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
        # dest must match streaming_ingest.main (args.input).
        parser.add_argument("input", metavar="input_file", help="Large file to stream")
        parser.add_argument(
            "--streaming-chunk-chars",
            type=int,
            default=4000,
            help="Maximum characters per chunk (default: 4000)",
        )
        # Keep in sync with streaming_ingest.main()'s parser — a flag defined there
        # but not here is REJECTED by the unified CLI before main() runs.
        parser.add_argument(
            "--streaming-overlap-chars",
            type=int,
            default=200,
            help="Chunk overlap in characters (default: 200)",
        )
        parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
        parser.add_argument("--checkpoint", help="Checkpoint file path")
        parser.add_argument(
            "--output",
            help="Write the collected chunks as JSON (a .json file path, or a "
            "directory that will receive chunks.json)",
        )
