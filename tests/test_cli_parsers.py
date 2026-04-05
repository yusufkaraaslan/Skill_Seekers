#!/usr/bin/env python3
"""
Tests for CLI Parser System

Tests the modular parser registration system.
"""

import argparse
import pytest

from skill_seekers.cli.parsers import (
    PARSERS,
    SubcommandParser,
    get_parser_names,
    register_parsers,
)
from skill_seekers.cli.parsers.package_parser import PackageParser


class TestParserRegistry:
    """Test parser registry functionality."""

    def test_all_parsers_registered(self):
        """Test that all parsers are registered."""
        assert len(PARSERS) == 18, f"Expected 18 parsers, got {len(PARSERS)}"

    def test_get_parser_names(self):
        """Test getting list of parser names."""
        names = get_parser_names()
        assert len(names) == 18
        assert "create" in names
        assert "package" in names
        assert "upload" in names
        assert "config" in names
        assert "workflows" in names

    def test_all_parsers_are_subcommand_parsers(self):
        """Test that all parsers inherit from SubcommandParser."""
        for parser in PARSERS:
            assert isinstance(parser, SubcommandParser)

    def test_all_parsers_have_required_properties(self):
        """Test that all parsers have name, help, description."""
        for parser in PARSERS:
            assert hasattr(parser, "name")
            assert hasattr(parser, "help")
            assert hasattr(parser, "description")
            assert isinstance(parser.name, str)
            assert isinstance(parser.help, str)
            assert isinstance(parser.description, str)
            assert len(parser.name) > 0
            assert len(parser.help) > 0

    def test_all_parsers_have_add_arguments_method(self):
        """Test that all parsers implement add_arguments."""
        for parser in PARSERS:
            assert hasattr(parser, "add_arguments")
            assert callable(parser.add_arguments)

    def test_no_duplicate_parser_names(self):
        """Test that all parser names are unique."""
        names = [p.name for p in PARSERS]
        assert len(names) == len(set(names)), "Duplicate parser names found!"


class TestParserCreation:
    """Test parser creation functionality."""

    def test_package_parser_creates_subparser(self):
        """Test that PackageParser creates valid subparser."""
        main_parser = argparse.ArgumentParser()
        subparsers = main_parser.add_subparsers()

        package_parser = PackageParser()
        subparser = package_parser.create_parser(subparsers)

        assert subparser is not None
        assert package_parser.name == "package"

    def test_register_parsers_creates_all_subcommands(self):
        """Test that register_parsers creates all subcommands."""
        main_parser = argparse.ArgumentParser()
        subparsers = main_parser.add_subparsers(dest="command")

        # Register all parsers
        register_parsers(subparsers)

        # Test that existing commands can be parsed
        test_commands = [
            "config --show",
            "package output/test/",
            "upload test.zip",
            "enhance output/test/",
            "estimate test.json",
        ]

        for cmd in test_commands:
            args = main_parser.parse_args(cmd.split())
            assert args.command is not None


class TestSpecificParsers:
    """Test specific parser implementations."""

    def test_package_parser_arguments(self):
        """Test PackageParser has correct arguments."""
        main_parser = argparse.ArgumentParser()
        subparsers = main_parser.add_subparsers(dest="command")

        package_parser = PackageParser()
        package_parser.create_parser(subparsers)

        args = main_parser.parse_args(["package", "output/test/"])
        assert args.command == "package"
        assert args.skill_directory == "output/test/"

        args = main_parser.parse_args(["package", "output/test/", "--target", "gemini"])
        assert args.target == "gemini"

        args = main_parser.parse_args(["package", "output/test/", "--no-open"])
        assert args.no_open is True


class TestCurrentCommands:
    """Test current CLI commands after Grand Unification."""

    def test_all_current_commands_registered(self):
        """Test that all current commands are registered."""
        names = get_parser_names()

        # Commands that survived the Grand Unification
        # (individual scraper commands removed; use 'create' instead)
        current_commands = [
            "config",
            "create",
            "enhance",
            "enhance-status",
            "package",
            "upload",
            "estimate",
            "extract-test-examples",
            "install-agent",
            "install",
            "resume",
            "stream",
            "update",
            "multilang",
            "quality",
            "doctor",
            "workflows",
            "sync-config",
        ]

        for cmd in current_commands:
            assert cmd in names, f"Command '{cmd}' not found in parser registry!"

    def test_removed_scraper_commands_not_present(self):
        """Test that individual scraper commands were removed."""
        names = get_parser_names()

        removed_commands = [
            "scrape",
            "github",
            "pdf",
            "video",
            "word",
            "epub",
            "jupyter",
            "html",
            "openapi",
            "asciidoc",
            "pptx",
            "rss",
            "manpage",
            "confluence",
            "notion",
            "chat",
        ]

        for cmd in removed_commands:
            assert cmd not in names, f"Removed command '{cmd}' still in parser registry!"

    def test_command_count_matches(self):
        """Test that we have exactly 18 commands."""
        assert len(PARSERS) == 18
        assert len(get_parser_names()) == 18


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
