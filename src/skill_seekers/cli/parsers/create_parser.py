"""Create subcommand parser with multi-mode help support.

Implements progressive disclosure:
- Default help: Universal arguments only (15 flags)
- Source-specific help: --help-web, --help-github, --help-local, --help-pdf
- Advanced help: --help-advanced
- Complete help: --help-all

Follows existing SubcommandParser pattern for consistency.
"""

import argparse
from .base import SubcommandParser
from skill_seekers.cli.arguments.create import add_create_arguments

class CreateParser(SubcommandParser):
    """Parser for create subcommand with multi-mode help."""

    @property
    def name(self) -> str:
        return "create"

    @property
    def help(self) -> str:
        return "Create skill from any source (auto-detects type)"

    @property
    def description(self) -> str:
        return """Auto-detects source type and creates skill.

Quick Examples:
  skill-seekers create https://docs.react.dev/ -p quick
  skill-seekers create facebook/react -p standard
  skill-seekers create ./my-project -p comprehensive

Source Types (auto-detected):
  URLs → web docs | owner/repo → GitHub | ./path → local code
  file.pdf → PDF | file.json → config (multi-source)

Progressive Help (NEW -p shortcut):
  Default help shows 13 flags. For more: --help-web, --help-github,
  --help-local, --help-pdf, --help-advanced, --help-all (120+ flags)

Presets: -p quick (1-2min) | -p standard (5-10min) | -p comprehensive (20-60min)
"""

    def add_arguments(self, parser):
        """Add create-specific arguments.

        Uses shared argument definitions with progressive disclosure.
        Default mode shows only universal arguments (15 flags).

        Multi-mode help handled via custom flags detected in argument parsing.
        """
        # Add all arguments in 'default' mode (universal only)
        # This keeps help text clean and focused
        add_create_arguments(parser, mode='default')

        # Add hidden help mode flags
        # These won't show in default help but can be used to get source-specific help
        parser.add_argument(
            '--help-web',
            action='store_true',
            help='Show web scraping specific options',
            dest='_help_web'
        )
        parser.add_argument(
            '--help-github',
            action='store_true',
            help='Show GitHub repository specific options',
            dest='_help_github'
        )
        parser.add_argument(
            '--help-local',
            action='store_true',
            help='Show local codebase specific options',
            dest='_help_local'
        )
        parser.add_argument(
            '--help-pdf',
            action='store_true',
            help='Show PDF extraction specific options',
            dest='_help_pdf'
        )
        parser.add_argument(
            '--help-advanced',
            action='store_true',
            help='Show advanced/rare options',
            dest='_help_advanced'
        )
        parser.add_argument(
            '--help-all',
            action='store_true',
            help='Show all available options (120+ flags)',
            dest='_help_all'
        )

    def register(self, subparsers):
        """Register this parser with custom formatter to prevent text wrapping.

        Args:
            subparsers: Subparsers object from main parser

        Returns:
            Configured ArgumentParser for this subcommand
        """
        # Custom formatter that preserves line breaks
        class NoWrapFormatter(argparse.RawDescriptionHelpFormatter):
            def _split_lines(self, text, width):
                return text.splitlines()

        parser = subparsers.add_parser(
            self.name,
            help=self.help,
            description=self.description,
            formatter_class=NoWrapFormatter
        )
        self.add_arguments(parser)
        return parser
