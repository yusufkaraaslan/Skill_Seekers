"""Upload subcommand parser.

Uses shared argument definitions from arguments.upload to ensure
consistency with the standalone upload_skill module.
"""

from .base import SubcommandParser
from skill_seekers.cli.arguments.upload import add_upload_arguments

class UploadParser(SubcommandParser):
    """Parser for upload subcommand."""

    @property
    def name(self) -> str:
        return "upload"

    @property
    def help(self) -> str:
        return "Upload skill to LLM platform or vector database"

    @property
    def description(self) -> str:
        return "Upload skill package to Claude, Gemini, OpenAI, ChromaDB, or Weaviate"

    def add_arguments(self, parser):
        """Add upload-specific arguments.

        Uses shared argument definitions to ensure consistency
        with upload_skill.py (standalone uploader).
        """
        add_upload_arguments(parser)
