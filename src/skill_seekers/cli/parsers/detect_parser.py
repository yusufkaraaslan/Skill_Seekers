"""Source detection subcommand parser."""

from .base import SubcommandParser


class DetectParser(SubcommandParser):
    """Parser for the read-only ``skill-seekers detect`` command."""

    @property
    def name(self) -> str:
        return "detect"

    @property
    def help(self) -> str:
        return "Detect a source type without creating a skill"

    @property
    def description(self) -> str:
        return "Inspect how Skill Seekers would classify and parse a source"

    def add_arguments(self, parser):
        parser.add_argument("source", help="URL, repository, path, or file to inspect")
        parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
