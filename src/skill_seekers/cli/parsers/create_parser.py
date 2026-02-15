"""Create subcommand parser with multi-mode help support.

Implements progressive disclosure:
- Default help: Universal arguments only (15 flags)
- Source-specific help: --help-web, --help-github, --help-local, --help-pdf
- Advanced help: --help-advanced
- Complete help: --help-all

Follows existing SubcommandParser pattern for consistency.
"""

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
        return """Create skill from web docs, GitHub repos, local code, PDFs, or config files.

Source type is auto-detected from the input:
  - Web:    https://docs.react.dev/ or docs.react.dev
  - GitHub: facebook/react or github.com/facebook/react
  - Local:  ./my-project or /path/to/repo
  - PDF:    tutorial.pdf
  - Config: configs/react.json

Examples:
  skill-seekers create https://docs.react.dev/ --preset quick
  skill-seekers create facebook/react --preset standard
  skill-seekers create ./my-project --preset comprehensive
  skill-seekers create tutorial.pdf --ocr
  skill-seekers create configs/react.json

For source-specific options, use:
  --help-web      Show web scraping options
  --help-github   Show GitHub repository options
  --help-local    Show local codebase options
  --help-pdf      Show PDF extraction options
  --help-advanced Show advanced/rare options
  --help-all      Show all 120+ options
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
