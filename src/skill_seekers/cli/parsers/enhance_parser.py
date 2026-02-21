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
        return "AI-powered enhancement (auto: API or LOCAL mode)"

    @property
    def description(self) -> str:
        return (
            "Enhance SKILL.md using AI. "
            "Automatically uses API mode (Gemini/OpenAI/Claude) when an API key is "
            "available, or falls back to LOCAL mode (Claude Code CLI)."
        )

    def add_arguments(self, parser):
        """Add enhance-specific arguments.

        Uses shared argument definitions to ensure consistency
        with enhance_skill_local.py (standalone enhancer).
        """
        add_enhance_arguments(parser)
