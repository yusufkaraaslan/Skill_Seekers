"""Upload subcommand parser."""
from .base import SubcommandParser


class UploadParser(SubcommandParser):
    """Parser for upload subcommand."""

    @property
    def name(self) -> str:
        return "upload"

    @property
    def help(self) -> str:
        return "Upload skill to Claude"

    @property
    def description(self) -> str:
        return "Upload .zip file to Claude via Anthropic API"

    def add_arguments(self, parser):
        """Add upload-specific arguments."""
        parser.add_argument("zip_file", help=".zip file to upload")
        parser.add_argument("--api-key", help="Anthropic API key")
