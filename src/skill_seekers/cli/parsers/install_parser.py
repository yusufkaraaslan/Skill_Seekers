"""Install subcommand parser."""

from .base import SubcommandParser


class InstallParser(SubcommandParser):
    """Parser for install subcommand."""

    @property
    def name(self) -> str:
        return "install"

    @property
    def help(self) -> str:
        return "Complete workflow: fetch -> scrape -> enhance -> package -> upload"

    @property
    def description(self) -> str:
        return "One-command skill installation (AI enhancement MANDATORY)"

    def add_arguments(self, parser):
        """Add install-specific arguments."""
        parser.add_argument(
            "--config",
            required=True,
            help="Config name (e.g., 'react') or path (e.g., 'configs/custom.json')",
        )
        parser.add_argument(
            "--destination", default="output", help="Output directory (default: output/)"
        )
        parser.add_argument(
            "--no-upload", action="store_true", help="Skip automatic upload to target platform"
        )
        parser.add_argument(
            "--unlimited", action="store_true", help="Remove page limits during scraping"
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Preview workflow without executing"
        )
        # Was module-only until Phase 5c — the unified CLI rejected
        # `install --target` even though install_skill.main() supported it.
        from skill_seekers.cli.adaptors import get_enhancement_platforms

        parser.add_argument(
            "--target",
            # install requires AI enhancement, so targets are the enhancement-capable
            # platforms (derived from the registry) plus markdown (export-only).
            choices=get_enhancement_platforms() + ["markdown"],
            default=None,
            help="Target LLM platform (auto-detected from API keys, or 'claude' if none set)",
        )
