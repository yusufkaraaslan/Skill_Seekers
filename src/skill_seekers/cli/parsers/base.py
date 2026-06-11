"""Base parser class for subcommands."""

from abc import ABC, abstractmethod
import argparse


class SubcommandParser(ABC):
    """Base class for subcommand parsers.

    Each subcommand parser defines:
    - name: Subcommand name (e.g., 'scrape')
    - help: Short help text
    - description: Long description (optional, defaults to help)
    - add_arguments(): Method to add command-specific arguments
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Subcommand name (e.g., 'scrape', 'github', 'package')."""
        pass

    @property
    @abstractmethod
    def help(self) -> str:
        """Short help text shown in command list."""
        pass

    @property
    def description(self) -> str:
        """Long description (defaults to help text)."""
        return self.help

    @abstractmethod
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add subcommand-specific arguments to parser.

        Args:
            parser: ArgumentParser for this subcommand
        """
        pass

    def create_parser(self, subparsers) -> argparse.ArgumentParser:
        """Create and configure subcommand parser.

        Args:
            subparsers: Subparsers object from main parser

        Returns:
            Configured ArgumentParser for this subcommand
        """
        parser = subparsers.add_parser(self.name, help=self.help, description=self.description)
        self.add_arguments(parser)
        return parser

    def build_standalone(
        self, prog: str | None = None, description: str | None = None
    ) -> argparse.ArgumentParser:
        """Build a standalone top-level parser for a module's ``main()`` path.

        Same single-source flags as create_parser(), without the unified CLI's
        subparsers machinery.

        Args:
            prog: Program name override (defaults to argparse's sys.argv[0])
            description: Description override (defaults to ``self.description``)

        Returns:
            Configured standalone ArgumentParser
        """
        if description is None:
            description = self.description
        parser = argparse.ArgumentParser(prog=prog, description=description)
        self.add_arguments(parser)
        return parser
