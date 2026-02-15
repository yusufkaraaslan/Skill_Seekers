"""Test that unified CLI parsers stay in sync with scraper modules.

This test ensures that the unified CLI (skill-seekers <command>) has exactly
the same arguments as the standalone scraper modules. This prevents the
 parsers from drifting out of sync (Issue #285).
"""

import argparse
import pytest


class TestScrapeParserSync:
    """Ensure scrape_parser has all arguments from doc_scraper."""

    def test_scrape_argument_count_matches(self):
        """Verify unified CLI parser has same argument count as doc_scraper."""
        from skill_seekers.cli.doc_scraper import setup_argument_parser
        from skill_seekers.cli.parsers.scrape_parser import ScrapeParser

        # Get source arguments from doc_scraper
        source_parser = setup_argument_parser()
        source_count = len([a for a in source_parser._actions if a.dest != 'help'])

        # Get target arguments from unified CLI parser
        target_parser = argparse.ArgumentParser()
        ScrapeParser().add_arguments(target_parser)
        target_count = len([a for a in target_parser._actions if a.dest != 'help'])

        assert source_count == target_count, (
            f"Argument count mismatch: doc_scraper has {source_count}, "
            f"but unified CLI parser has {target_count}"
        )

    def test_scrape_argument_dests_match(self):
        """Verify unified CLI parser has same argument destinations as doc_scraper."""
        from skill_seekers.cli.doc_scraper import setup_argument_parser
        from skill_seekers.cli.parsers.scrape_parser import ScrapeParser

        # Get source arguments from doc_scraper
        source_parser = setup_argument_parser()
        source_dests = {a.dest for a in source_parser._actions if a.dest != 'help'}

        # Get target arguments from unified CLI parser
        target_parser = argparse.ArgumentParser()
        ScrapeParser().add_arguments(target_parser)
        target_dests = {a.dest for a in target_parser._actions if a.dest != 'help'}

        # Check for missing arguments
        missing = source_dests - target_dests
        extra = target_dests - source_dests

        assert not missing, f"scrape_parser missing arguments: {missing}"
        assert not extra, f"scrape_parser has extra arguments not in doc_scraper: {extra}"

    def test_scrape_specific_arguments_present(self):
        """Verify key scrape arguments are present in unified CLI."""
        from skill_seekers.cli.main import create_parser

        parser = create_parser()

        # Get the scrape subparser
        subparsers_action = None
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                subparsers_action = action
                break

        assert subparsers_action is not None, "No subparsers found"
        assert 'scrape' in subparsers_action.choices, "scrape subparser not found"

        scrape_parser = subparsers_action.choices['scrape']
        arg_dests = {a.dest for a in scrape_parser._actions if a.dest != 'help'}

        # Check key arguments that were missing in Issue #285
        required_args = [
            'interactive',
            'url',
            'verbose',
            'quiet',
            'resume',
            'fresh',
            'rate_limit',
            'no_rate_limit',
            'chunk_for_rag',
        ]

        for arg in required_args:
            assert arg in arg_dests, f"Required argument '{arg}' missing from scrape parser"


class TestGitHubParserSync:
    """Ensure github_parser has all arguments from github_scraper."""

    def test_github_argument_count_matches(self):
        """Verify unified CLI parser has same argument count as github_scraper."""
        from skill_seekers.cli.github_scraper import setup_argument_parser
        from skill_seekers.cli.parsers.github_parser import GitHubParser

        # Get source arguments from github_scraper
        source_parser = setup_argument_parser()
        source_count = len([a for a in source_parser._actions if a.dest != 'help'])

        # Get target arguments from unified CLI parser
        target_parser = argparse.ArgumentParser()
        GitHubParser().add_arguments(target_parser)
        target_count = len([a for a in target_parser._actions if a.dest != 'help'])

        assert source_count == target_count, (
            f"Argument count mismatch: github_scraper has {source_count}, "
            f"but unified CLI parser has {target_count}"
        )

    def test_github_argument_dests_match(self):
        """Verify unified CLI parser has same argument destinations as github_scraper."""
        from skill_seekers.cli.github_scraper import setup_argument_parser
        from skill_seekers.cli.parsers.github_parser import GitHubParser

        # Get source arguments from github_scraper
        source_parser = setup_argument_parser()
        source_dests = {a.dest for a in source_parser._actions if a.dest != 'help'}

        # Get target arguments from unified CLI parser
        target_parser = argparse.ArgumentParser()
        GitHubParser().add_arguments(target_parser)
        target_dests = {a.dest for a in target_parser._actions if a.dest != 'help'}

        # Check for missing arguments
        missing = source_dests - target_dests
        extra = target_dests - source_dests

        assert not missing, f"github_parser missing arguments: {missing}"
        assert not extra, f"github_parser has extra arguments not in github_scraper: {extra}"


class TestUnifiedCLI:
    """Test the unified CLI main parser."""

    def test_main_parser_creates_successfully(self):
        """Verify the main parser can be created without errors."""
        from skill_seekers.cli.main import create_parser

        parser = create_parser()
        assert parser is not None

    def test_all_subcommands_present(self):
        """Verify all expected subcommands are present."""
        from skill_seekers.cli.main import create_parser

        parser = create_parser()

        # Find subparsers action
        subparsers_action = None
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                subparsers_action = action
                break

        assert subparsers_action is not None, "No subparsers found"

        # Check expected subcommands
        expected_commands = ['scrape', 'github']
        for cmd in expected_commands:
            assert cmd in subparsers_action.choices, f"Subcommand '{cmd}' not found"

    def test_scrape_help_works(self):
        """Verify scrape subcommand help can be generated."""
        from skill_seekers.cli.main import create_parser

        parser = create_parser()

        # This should not raise an exception
        try:
            parser.parse_args(['scrape', '--help'])
        except SystemExit as e:
            # --help causes SystemExit(0) which is expected
            assert e.code == 0

    def test_github_help_works(self):
        """Verify github subcommand help can be generated."""
        from skill_seekers.cli.main import create_parser

        parser = create_parser()

        # This should not raise an exception
        try:
            parser.parse_args(['github', '--help'])
        except SystemExit as e:
            # --help causes SystemExit(0) which is expected
            assert e.code == 0
