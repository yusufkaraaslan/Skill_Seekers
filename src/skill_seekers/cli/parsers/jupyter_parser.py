"""Jupyter Notebook subcommand parser.

Uses shared argument definitions from arguments.jupyter to ensure
consistency with the standalone jupyter_scraper module.
"""

from .base import SubcommandParser
from skill_seekers.cli.arguments.jupyter import add_jupyter_arguments


class JupyterParser(SubcommandParser):
    """Parser for jupyter subcommand."""

    @property
    def name(self) -> str:
        return "jupyter"

    @property
    def help(self) -> str:
        return "Extract from Jupyter Notebook (.ipynb)"

    @property
    def description(self) -> str:
        return "Extract content from Jupyter Notebook (.ipynb) and generate skill"

    def add_arguments(self, parser):
        """Add jupyter-specific arguments.

        Uses shared argument definitions to ensure consistency
        with jupyter_scraper.py (standalone scraper).
        """
        add_jupyter_arguments(parser)
