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
from skill_seekers.cli.parsers.scrape_parser import ScrapeParser
from skill_seekers.cli.parsers.github_parser import GitHubParser
from skill_seekers.cli.parsers.package_parser import PackageParser


class TestParserRegistry:
    """Test parser registry functionality."""

    def test_all_parsers_registered(self):
        """Test that all 19 parsers are registered."""
        assert len(PARSERS) == 19, f"Expected 19 parsers, got {len(PARSERS)}"

    def test_get_parser_names(self):
        """Test getting list of parser names."""
        names = get_parser_names()
        assert len(names) == 19
        assert "scrape" in names
        assert "github" in names
        assert "package" in names
        assert "upload" in names
        assert "analyze" in names
        assert "config" in names

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

    def test_scrape_parser_creates_subparser(self):
        """Test that ScrapeParser creates valid subparser."""
        main_parser = argparse.ArgumentParser()
        subparsers = main_parser.add_subparsers()

        scrape_parser = ScrapeParser()
        subparser = scrape_parser.create_parser(subparsers)

        assert subparser is not None
        assert scrape_parser.name == "scrape"
        assert scrape_parser.help == "Scrape documentation website"

    def test_github_parser_creates_subparser(self):
        """Test that GitHubParser creates valid subparser."""
        main_parser = argparse.ArgumentParser()
        subparsers = main_parser.add_subparsers()

        github_parser = GitHubParser()
        subparser = github_parser.create_parser(subparsers)

        assert subparser is not None
        assert github_parser.name == "github"

    def test_package_parser_creates_subparser(self):
        """Test that PackageParser creates valid subparser."""
        main_parser = argparse.ArgumentParser()
        subparsers = main_parser.add_subparsers()

        package_parser = PackageParser()
        subparser = package_parser.create_parser(subparsers)

        assert subparser is not None
        assert package_parser.name == "package"

    def test_register_parsers_creates_all_subcommands(self):
        """Test that register_parsers creates all 19 subcommands."""
        main_parser = argparse.ArgumentParser()
        subparsers = main_parser.add_subparsers(dest="command")

        # Register all parsers
        register_parsers(subparsers)

        # Test that all commands can be parsed
        test_commands = [
            "config --show",
            "scrape --config test.json",
            "github --repo owner/repo",
            "package output/test/",
            "upload test.zip",
            "analyze --directory .",
            "enhance output/test/",
            "estimate test.json",
        ]

        for cmd in test_commands:
            args = main_parser.parse_args(cmd.split())
            assert args.command is not None


class TestSpecificParsers:
    """Test specific parser implementations."""

    def test_scrape_parser_arguments(self):
        """Test ScrapeParser has correct arguments."""
        main_parser = argparse.ArgumentParser()
        subparsers = main_parser.add_subparsers(dest="command")

        scrape_parser = ScrapeParser()
        scrape_parser.create_parser(subparsers)

        # Test various argument combinations
        args = main_parser.parse_args(["scrape", "--config", "test.json"])
        assert args.command == "scrape"
        assert args.config == "test.json"

        args = main_parser.parse_args(["scrape", "--config", "test.json", "--max-pages", "100"])
        assert args.max_pages == 100

        args = main_parser.parse_args(["scrape", "--enhance"])
        assert args.enhance is True

    def test_github_parser_arguments(self):
        """Test GitHubParser has correct arguments."""
        main_parser = argparse.ArgumentParser()
        subparsers = main_parser.add_subparsers(dest="command")

        github_parser = GitHubParser()
        github_parser.create_parser(subparsers)

        args = main_parser.parse_args(["github", "--repo", "owner/repo"])
        assert args.command == "github"
        assert args.repo == "owner/repo"

        args = main_parser.parse_args(["github", "--repo", "owner/repo", "--non-interactive"])
        assert args.non_interactive is True

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

    def test_analyze_parser_arguments(self):
        """Test AnalyzeParser has correct arguments."""
        main_parser = argparse.ArgumentParser()
        subparsers = main_parser.add_subparsers(dest="command")

        from skill_seekers.cli.parsers.analyze_parser import AnalyzeParser

        analyze_parser = AnalyzeParser()
        analyze_parser.create_parser(subparsers)

        args = main_parser.parse_args(["analyze", "--directory", "."])
        assert args.command == "analyze"
        assert args.directory == "."

        args = main_parser.parse_args(["analyze", "--directory", ".", "--quick"])
        assert args.quick is True

        args = main_parser.parse_args(["analyze", "--directory", ".", "--comprehensive"])
        assert args.comprehensive is True

        args = main_parser.parse_args(["analyze", "--directory", ".", "--skip-patterns"])
        assert args.skip_patterns is True


class TestBackwardCompatibility:
    """Test backward compatibility with old CLI."""

    def test_all_original_commands_still_work(self):
        """Test that all original commands are still registered."""
        names = get_parser_names()

        # Original commands from old main.py
        original_commands = [
            "config",
            "scrape",
            "github",
            "pdf",
            "unified",
            "enhance",
            "enhance-status",
            "package",
            "upload",
            "estimate",
            "extract-test-examples",
            "install-agent",
            "analyze",
            "install",
            "resume",
            "stream",
            "update",
            "multilang",
            "quality",
        ]

        for cmd in original_commands:
            assert cmd in names, f"Command '{cmd}' not found in parser registry!"

    def test_command_count_matches(self):
        """Test that we have exactly 19 commands (same as original)."""
        assert len(PARSERS) == 19
        assert len(get_parser_names()) == 19


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
