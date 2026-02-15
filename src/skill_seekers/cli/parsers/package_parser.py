"""Package subcommand parser.

Uses shared argument definitions from arguments.package to ensure
consistency with the standalone package_skill module.
"""

from .base import SubcommandParser
from skill_seekers.cli.arguments.package import add_package_arguments


class PackageParser(SubcommandParser):
    """Parser for package subcommand."""

    @property
    def name(self) -> str:
        return "package"

    @property
    def help(self) -> str:
        return "Package skill into platform-specific format"

    @property
    def description(self) -> str:
        return "Package skill directory into uploadable format for various LLM platforms"

    def add_arguments(self, parser):
        """Add package-specific arguments.
        
        Uses shared argument definitions to ensure consistency
        with package_skill.py (standalone packager).
        """
        add_package_arguments(parser)
