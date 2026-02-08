"""PDF subcommand parser."""

from .base import SubcommandParser


class PDFParser(SubcommandParser):
    """Parser for pdf subcommand."""

    @property
    def name(self) -> str:
        return "pdf"

    @property
    def help(self) -> str:
        return "Extract from PDF file"

    @property
    def description(self) -> str:
        return "Extract content from PDF and generate skill"

    def add_arguments(self, parser):
        """Add pdf-specific arguments."""
        parser.add_argument("--config", help="Config JSON file")
        parser.add_argument("--pdf", help="PDF file path")
        parser.add_argument("--name", help="Skill name")
        parser.add_argument("--description", help="Skill description")
        parser.add_argument("--from-json", help="Build from extracted JSON")
