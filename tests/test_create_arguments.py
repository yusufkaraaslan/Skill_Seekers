"""Tests for create command argument definitions.

Tests the three-tier argument system:
1. Universal arguments (work for all sources)
2. Source-specific arguments
3. Advanced arguments
"""

import pytest
from skill_seekers.cli.arguments.create import (
    UNIVERSAL_ARGUMENTS,
    WEB_ARGUMENTS,
    GITHUB_ARGUMENTS,
    LOCAL_ARGUMENTS,
    PDF_ARGUMENTS,
    ADVANCED_ARGUMENTS,
    get_universal_argument_names,
    get_source_specific_arguments,
    get_compatible_arguments,
    add_create_arguments,
)


class TestUniversalArguments:
    """Test universal argument definitions."""

    def test_universal_count(self):
        """Should have exactly 13 universal arguments (after Phase 1 consolidation)."""
        assert len(UNIVERSAL_ARGUMENTS) == 13

    def test_universal_argument_names(self):
        """Universal arguments should have expected names."""
        expected_names = {
            'name', 'description', 'output',
            'enhance_level', 'api_key',  # Phase 1: consolidated from enhance + enhance_local
            'dry_run', 'verbose', 'quiet',
            'chunk_for_rag', 'chunk_size', 'chunk_overlap',  # Phase 2: RAG args from common.py
            'preset', 'config'
        }
        assert set(UNIVERSAL_ARGUMENTS.keys()) == expected_names

    def test_all_universal_have_flags(self):
        """All universal arguments should have flags."""
        for arg_name, arg_def in UNIVERSAL_ARGUMENTS.items():
            assert 'flags' in arg_def
            assert len(arg_def['flags']) > 0

    def test_all_universal_have_kwargs(self):
        """All universal arguments should have kwargs."""
        for arg_name, arg_def in UNIVERSAL_ARGUMENTS.items():
            assert 'kwargs' in arg_def
            assert 'help' in arg_def['kwargs']


class TestSourceSpecificArguments:
    """Test source-specific argument definitions."""

    def test_web_arguments_exist(self):
        """Web-specific arguments should be defined."""
        assert len(WEB_ARGUMENTS) > 0
        assert 'max_pages' in WEB_ARGUMENTS
        assert 'rate_limit' in WEB_ARGUMENTS
        assert 'workers' in WEB_ARGUMENTS

    def test_github_arguments_exist(self):
        """GitHub-specific arguments should be defined."""
        assert len(GITHUB_ARGUMENTS) > 0
        assert 'repo' in GITHUB_ARGUMENTS
        assert 'token' in GITHUB_ARGUMENTS
        assert 'max_issues' in GITHUB_ARGUMENTS

    def test_local_arguments_exist(self):
        """Local-specific arguments should be defined."""
        assert len(LOCAL_ARGUMENTS) > 0
        assert 'directory' in LOCAL_ARGUMENTS
        assert 'languages' in LOCAL_ARGUMENTS
        assert 'skip_patterns' in LOCAL_ARGUMENTS

    def test_pdf_arguments_exist(self):
        """PDF-specific arguments should be defined."""
        assert len(PDF_ARGUMENTS) > 0
        assert 'pdf' in PDF_ARGUMENTS
        assert 'ocr' in PDF_ARGUMENTS

    def test_no_duplicate_flags_across_sources(self):
        """Source-specific arguments should not have duplicate flags."""
        # Collect all flags from source-specific arguments
        all_flags = set()

        for source_args in [WEB_ARGUMENTS, GITHUB_ARGUMENTS, LOCAL_ARGUMENTS, PDF_ARGUMENTS]:
            for arg_name, arg_def in source_args.items():
                flags = arg_def['flags']
                for flag in flags:
                    # Check if this flag already exists in source-specific args
                    if flag not in [f for arg in UNIVERSAL_ARGUMENTS.values() for f in arg['flags']]:
                        assert flag not in all_flags, f"Duplicate flag: {flag}"
                        all_flags.add(flag)


class TestAdvancedArguments:
    """Test advanced/rare argument definitions."""

    def test_advanced_arguments_exist(self):
        """Advanced arguments should be defined."""
        assert len(ADVANCED_ARGUMENTS) > 0
        assert 'no_rate_limit' in ADVANCED_ARGUMENTS
        assert 'interactive_enhancement' in ADVANCED_ARGUMENTS


class TestArgumentHelpers:
    """Test helper functions."""

    def test_get_universal_argument_names(self):
        """Should return set of universal argument names."""
        names = get_universal_argument_names()
        assert isinstance(names, set)
        assert len(names) == 13
        assert 'name' in names
        assert 'enhance_level' in names  # Phase 1: consolidated flag

    def test_get_source_specific_web(self):
        """Should return web-specific arguments."""
        args = get_source_specific_arguments('web')
        assert args == WEB_ARGUMENTS

    def test_get_source_specific_github(self):
        """Should return github-specific arguments."""
        args = get_source_specific_arguments('github')
        assert args == GITHUB_ARGUMENTS

    def test_get_source_specific_local(self):
        """Should return local-specific arguments."""
        args = get_source_specific_arguments('local')
        assert args == LOCAL_ARGUMENTS

    def test_get_source_specific_pdf(self):
        """Should return pdf-specific arguments."""
        args = get_source_specific_arguments('pdf')
        assert args == PDF_ARGUMENTS

    def test_get_source_specific_config(self):
        """Config should return empty dict (no extra args)."""
        args = get_source_specific_arguments('config')
        assert args == {}

    def test_get_source_specific_unknown(self):
        """Unknown source should return empty dict."""
        args = get_source_specific_arguments('unknown')
        assert args == {}


class TestCompatibleArguments:
    """Test compatible argument detection."""

    def test_web_compatible_arguments(self):
        """Web source should include universal + web + advanced."""
        compatible = get_compatible_arguments('web')

        # Should include universal arguments
        assert 'name' in compatible
        assert 'enhance_level' in compatible  # Phase 1: consolidated flag

        # Should include web-specific arguments
        assert 'max_pages' in compatible
        assert 'rate_limit' in compatible

        # Should include advanced arguments
        assert 'no_rate_limit' in compatible

    def test_github_compatible_arguments(self):
        """GitHub source should include universal + github + advanced."""
        compatible = get_compatible_arguments('github')

        # Should include universal arguments
        assert 'name' in compatible

        # Should include github-specific arguments
        assert 'repo' in compatible
        assert 'token' in compatible

        # Should include advanced arguments
        assert 'interactive_enhancement' in compatible

    def test_local_compatible_arguments(self):
        """Local source should include universal + local + advanced."""
        compatible = get_compatible_arguments('local')

        # Should include universal arguments
        assert 'description' in compatible

        # Should include local-specific arguments
        assert 'directory' in compatible
        assert 'languages' in compatible

    def test_pdf_compatible_arguments(self):
        """PDF source should include universal + pdf + advanced."""
        compatible = get_compatible_arguments('pdf')

        # Should include universal arguments
        assert 'output' in compatible

        # Should include pdf-specific arguments
        assert 'pdf' in compatible
        assert 'ocr' in compatible

    def test_config_compatible_arguments(self):
        """Config source should include universal + advanced only."""
        compatible = get_compatible_arguments('config')

        # Should include universal arguments
        assert 'config' in compatible

        # Should include advanced arguments
        assert 'no_preserve_code_blocks' in compatible

        # Should not include source-specific arguments
        assert 'repo' not in compatible
        assert 'directory' not in compatible


class TestAddCreateArguments:
    """Test add_create_arguments function."""

    def test_default_mode_adds_universal_only(self):
        """Default mode should add only universal arguments + source positional."""
        import argparse
        parser = argparse.ArgumentParser()
        add_create_arguments(parser, mode='default')

        # Parse to get all arguments
        args = vars(parser.parse_args([]))

        # Should have universal arguments
        assert 'name' in args
        assert 'enhance_level' in args
        assert 'chunk_for_rag' in args

        # Should not have source-specific arguments (they're not added in default mode)
        # Note: argparse won't error on unknown args, but they won't be in namespace

    def test_web_mode_adds_web_arguments(self):
        """Web mode should add universal + web arguments."""
        import argparse
        parser = argparse.ArgumentParser()
        add_create_arguments(parser, mode='web')

        args = vars(parser.parse_args([]))

        # Should have universal arguments
        assert 'name' in args

        # Should have web-specific arguments
        assert 'max_pages' in args
        assert 'rate_limit' in args

    def test_all_mode_adds_all_arguments(self):
        """All mode should add every argument."""
        import argparse
        parser = argparse.ArgumentParser()
        add_create_arguments(parser, mode='all')

        args = vars(parser.parse_args([]))

        # Should have universal arguments
        assert 'name' in args

        # Should have all source-specific arguments
        assert 'max_pages' in args  # web
        assert 'repo' in args  # github
        assert 'directory' in args  # local
        assert 'pdf' in args  # pdf

        # Should have advanced arguments
        assert 'no_rate_limit' in args

    def test_positional_source_argument_always_added(self):
        """Source positional argument should always be added."""
        import argparse
        for mode in ['default', 'web', 'github', 'local', 'pdf', 'all']:
            parser = argparse.ArgumentParser()
            add_create_arguments(parser, mode=mode)

            # Should accept source as positional
            args = parser.parse_args(['some_source'])
            assert args.source == 'some_source'


class TestNoDuplicates:
    """Test that there are no duplicate arguments across tiers."""

    def test_no_duplicates_between_universal_and_web(self):
        """Universal and web args should not overlap."""
        universal_flags = {
            flag for arg in UNIVERSAL_ARGUMENTS.values()
            for flag in arg['flags']
        }
        web_flags = {
            flag for arg in WEB_ARGUMENTS.values()
            for flag in arg['flags']
        }

        # Allow some overlap since we intentionally include common args
        # in multiple places, but check that they're properly defined
        overlap = universal_flags & web_flags
        # There should be minimal overlap (only if intentional)
        assert len(overlap) == 0, f"Unexpected overlap: {overlap}"

    def test_no_duplicates_between_source_specific_args(self):
        """Different source-specific arg groups should not overlap."""
        web_flags = {flag for arg in WEB_ARGUMENTS.values() for flag in arg['flags']}
        github_flags = {flag for arg in GITHUB_ARGUMENTS.values() for flag in arg['flags']}
        local_flags = {flag for arg in LOCAL_ARGUMENTS.values() for flag in arg['flags']}
        pdf_flags = {flag for arg in PDF_ARGUMENTS.values() for flag in arg['flags']}

        # No overlap between different source types
        assert len(web_flags & github_flags) == 0
        assert len(web_flags & local_flags) == 0
        assert len(web_flags & pdf_flags) == 0
        assert len(github_flags & local_flags) == 0
        assert len(github_flags & pdf_flags) == 0
        assert len(local_flags & pdf_flags) == 0


class TestArgumentQuality:
    """Test argument definition quality."""

    def test_all_arguments_have_help_text(self):
        """Every argument should have help text."""
        all_args = {
            **UNIVERSAL_ARGUMENTS,
            **WEB_ARGUMENTS,
            **GITHUB_ARGUMENTS,
            **LOCAL_ARGUMENTS,
            **PDF_ARGUMENTS,
            **ADVANCED_ARGUMENTS,
        }

        for arg_name, arg_def in all_args.items():
            assert 'help' in arg_def['kwargs'], f"{arg_name} missing help text"
            assert len(arg_def['kwargs']['help']) > 0, f"{arg_name} has empty help text"

    def test_boolean_arguments_use_store_true(self):
        """Boolean flags should use store_true action."""
        all_args = {
            **UNIVERSAL_ARGUMENTS,
            **WEB_ARGUMENTS,
            **GITHUB_ARGUMENTS,
            **LOCAL_ARGUMENTS,
            **PDF_ARGUMENTS,
            **ADVANCED_ARGUMENTS,
        }

        boolean_args = [
            'dry_run', 'verbose', 'quiet',
            'chunk_for_rag', 'skip_scrape', 'resume', 'fresh', 'async_mode',
            'no_issues', 'no_changelog', 'no_releases', 'scrape_only',
            'skip_patterns', 'skip_test_examples', 'ocr', 'no_rate_limit'
        ]

        for arg_name in boolean_args:
            if arg_name in all_args:
                action = all_args[arg_name]['kwargs'].get('action')
                assert action == 'store_true', f"{arg_name} should use store_true"
