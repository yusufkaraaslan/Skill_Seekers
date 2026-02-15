"""Enhance subcommand parser.

Uses shared argument definitions from arguments.enhance to ensure
consistency with the standalone enhance_skill_local module.
"""

from .base import SubcommandParser
from skill_seekers.cli.arguments.enhance import add_enhance_arguments


class EnhanceParser(SubcommandParser):
    """Parser for enhance subcommand."""

    @property
    def name(self) -> str:
        return "enhance"

    @property
    def help(self) -> str:
        return "AI-powered enhancement (local, no API key)"

    @property
    def description(self) -> str:
        return "Enhance SKILL.md using a local coding agent"

    def add_arguments(self, parser):
        """Add enhance-specific arguments.

        Uses shared argument definitions to ensure consistency
        with enhance_skill_local.py (standalone enhancer).
        """
        add_enhance_arguments(parser)
