"""OpenAPI subcommand parser.

Uses shared argument definitions from arguments.openapi to ensure
consistency with the standalone openapi_scraper module.
"""

from .base import SubcommandParser
from skill_seekers.cli.arguments.openapi import add_openapi_arguments


class OpenAPIParser(SubcommandParser):
    """Parser for openapi subcommand."""

    @property
    def name(self) -> str:
        return "openapi"

    @property
    def help(self) -> str:
        return "Extract from OpenAPI/Swagger spec"

    @property
    def description(self) -> str:
        return "Extract content from OpenAPI/Swagger spec and generate skill"

    def add_arguments(self, parser):
        """Add openapi-specific arguments.

        Uses shared argument definitions to ensure consistency
        with openapi_scraper.py (standalone scraper).
        """
        add_openapi_arguments(parser)
