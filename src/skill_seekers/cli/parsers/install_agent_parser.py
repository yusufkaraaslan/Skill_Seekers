"""Install-agent subcommand parser."""

from .base import SubcommandParser


class InstallAgentParser(SubcommandParser):
    """Parser for install-agent subcommand."""

    @property
    def name(self) -> str:
        return "install-agent"

    @property
    def help(self) -> str:
        return "Install skill to AI agent directories"

    @property
    def description(self) -> str:
        return "Copy skill to agent-specific installation directories"

    def add_arguments(self, parser):
        """Add install-agent-specific arguments."""
        parser.add_argument("skill_directory", help="Skill directory path (e.g., output/react/)")
        parser.add_argument(
            "--agent",
            required=True,
            help="Agent name (claude, cursor, vscode, amp, goose, opencode, all)",
        )
        parser.add_argument(
            "--force", action="store_true", help="Overwrite existing installation without asking"
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Preview installation without making changes"
        )
