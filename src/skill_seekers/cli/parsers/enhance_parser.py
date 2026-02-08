"""Enhance subcommand parser."""

from .base import SubcommandParser


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
        """Add enhance-specific arguments."""
        parser.add_argument("skill_directory", help="Skill directory path")
        parser.add_argument(
            "--agent",
            choices=["claude", "codex", "copilot", "opencode", "custom"],
            help="Local coding agent to use (default: claude or SKILL_SEEKER_AGENT)",
        )
        parser.add_argument(
            "--agent-cmd",
            help="Override agent command template (use {prompt_file} or stdin).",
        )
        parser.add_argument("--background", action="store_true", help="Run in background")
        parser.add_argument("--daemon", action="store_true", help="Run as daemon")
        parser.add_argument(
            "--no-force", action="store_true", help="Disable force mode (enable confirmations)"
        )
        parser.add_argument("--timeout", type=int, default=600, help="Timeout in seconds")
