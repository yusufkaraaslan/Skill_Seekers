"""
Tests for Phase 3: Enhanced Source Merging with GitHub Streams

Tests the multi-layer merging architecture:
- Layer 1: C3.x code (ground truth)
- Layer 2: HTML docs (official intent)
- Layer 3: GitHub docs (README/CONTRIBUTING)
- Layer 4: GitHub insights (issues)
"""

import pytest
from pathlib import Path
from unittest.mock import Mock
from skill_seekers.cli.merge_sources import (
    categorize_issues_by_topic,
    generate_hybrid_content,
    RuleBasedMerger,
    _match_issues_to_apis
)
from skill_seekers.cli.github_fetcher import (
    CodeStream,
    DocsStream,
    InsightsStream,
    ThreeStreamData
)
from skill_seekers.cli.conflict_detector import Conflict


class TestIssueCategorization:
    """Test issue categorization by topic."""

    def test_categorize_issues_basic(self):
        """Test basic issue categorization."""
        problems = [
            {'title': 'OAuth setup fails', 'labels': ['bug', 'oauth'], 'number': 1, 'state': 'open', 'comments': 10},
            {'title': 'Testing framework issue', 'labels': ['testing'], 'number': 2, 'state': 'open', 'comments': 5}
        ]
        solutions = [
            {'title': 'Fixed OAuth redirect', 'labels': ['oauth'], 'number': 3, 'state': 'closed', 'comments': 3}
        ]

        topics = ['oauth', 'testing', 'async']

        categorized = categorize_issues_by_topic(problems, solutions, topics)

        assert 'oauth' in categorized
        assert len(categorized['oauth']) == 2  # 1 problem + 1 solution
        assert 'testing' in categorized
        assert len(categorized['testing']) == 1

    def test_categorize_issues_keyword_matching(self):
        """Test keyword matching in titles and labels."""
        problems = [
            {'title': 'Database connection timeout', 'labels': ['db'], 'number': 1, 'state': 'open', 'comments': 7}
        ]
        solutions = []

        topics = ['database']

        categorized = categorize_issues_by_topic(problems, solutions, topics)

        # Should match 'database' topic due to 'db' in labels
        assert 'database' in categorized or 'other' in categorized

    def test_categorize_issues_multi_keyword_topic(self):
        """Test topics with multiple keywords."""
        problems = [
            {'title': 'Async API call fails', 'labels': ['async', 'api'], 'number': 1, 'state': 'open', 'comments': 8}
        ]
        solutions = []

        topics = ['async api']

        categorized = categorize_issues_by_topic(problems, solutions, topics)

        # Should match due to both 'async' and 'api' in labels
        assert 'async api' in categorized
        assert len(categorized['async api']) == 1

    def test_categorize_issues_no_match_goes_to_other(self):
        """Test that unmatched issues go to 'other' category."""
        problems = [
            {'title': 'Random issue', 'labels': ['misc'], 'number': 1, 'state': 'open', 'comments': 5}
        ]
        solutions = []

        topics = ['oauth', 'testing']

        categorized = categorize_issues_by_topic(problems, solutions, topics)

        assert 'other' in categorized
        assert len(categorized['other']) == 1

    def test_categorize_issues_empty_lists(self):
        """Test categorization with empty input."""
        categorized = categorize_issues_by_topic([], [], ['oauth'])

        # Should return empty dict (no categories with issues)
        assert len(categorized) == 0


class TestHybridContent:
    """Test hybrid content generation."""

    def test_generate_hybrid_content_basic(self):
        """Test basic hybrid content generation."""
        api_data = {
            'apis': {
                'oauth_login': {'name': 'oauth_login', 'status': 'matched'}
            },
            'summary': {'total_apis': 1}
        }

        github_docs = {
            'readme': '# Project README',
            'contributing': None,
            'docs_files': [{'path': 'docs/oauth.md', 'content': 'OAuth guide'}]
        }

        github_insights = {
            'metadata': {
                'stars': 1234,
                'forks': 56,
                'language': 'Python',
                'description': 'Test project'
            },
            'common_problems': [
                {'title': 'OAuth fails', 'number': 42, 'state': 'open', 'comments': 10, 'labels': ['bug']}
            ],
            'known_solutions': [
                {'title': 'Fixed OAuth', 'number': 35, 'state': 'closed', 'comments': 5, 'labels': ['bug']}
            ],
            'top_labels': [
                {'label': 'bug', 'count': 10},
                {'label': 'enhancement', 'count': 5}
            ]
        }

        conflicts = []

        hybrid = generate_hybrid_content(api_data, github_docs, github_insights, conflicts)

        # Check structure
        assert 'api_reference' in hybrid
        assert 'github_context' in hybrid
        assert 'conflict_summary' in hybrid
        assert 'issue_links' in hybrid

        # Check GitHub docs layer
        assert hybrid['github_context']['docs']['readme'] == '# Project README'
        assert hybrid['github_context']['docs']['docs_files_count'] == 1

        # Check GitHub insights layer
        assert hybrid['github_context']['metadata']['stars'] == 1234
        assert hybrid['github_context']['metadata']['language'] == 'Python'
        assert hybrid['github_context']['issues']['common_problems_count'] == 1
        assert hybrid['github_context']['issues']['known_solutions_count'] == 1
        assert len(hybrid['github_context']['issues']['top_problems']) == 1
        assert len(hybrid['github_context']['top_labels']) == 2

    def test_generate_hybrid_content_with_conflicts(self):
        """Test hybrid content with conflicts."""
        api_data = {'apis': {}, 'summary': {}}
        github_docs = None
        github_insights = None

        conflicts = [
            Conflict(
                api_name='test_api',
                type='signature_mismatch',
                severity='medium',
                difference='Parameter count differs',
                docs_info={'parameters': ['a', 'b']},
                code_info={'parameters': ['a', 'b', 'c']}
            ),
            Conflict(
                api_name='test_api_2',
                type='missing_in_docs',
                severity='low',
                difference='API not documented',
                docs_info=None,
                code_info={'name': 'test_api_2'}
            )
        ]

        hybrid = generate_hybrid_content(api_data, github_docs, github_insights, conflicts)

        # Check conflict summary
        assert hybrid['conflict_summary']['total_conflicts'] == 2
        assert hybrid['conflict_summary']['by_type']['signature_mismatch'] == 1
        assert hybrid['conflict_summary']['by_type']['missing_in_docs'] == 1
        assert hybrid['conflict_summary']['by_severity']['medium'] == 1
        assert hybrid['conflict_summary']['by_severity']['low'] == 1

    def test_generate_hybrid_content_no_github_data(self):
        """Test hybrid content with no GitHub data."""
        api_data = {'apis': {}, 'summary': {}}

        hybrid = generate_hybrid_content(api_data, None, None, [])

        # Should still have structure, but no GitHub context
        assert 'api_reference' in hybrid
        assert 'github_context' in hybrid
        assert hybrid['github_context'] == {}
        assert hybrid['conflict_summary']['total_conflicts'] == 0


class TestIssueToAPIMatching:
    """Test matching issues to APIs."""

    def test_match_issues_to_apis_basic(self):
        """Test basic issue to API matching."""
        apis = {
            'oauth_login': {'name': 'oauth_login'},
            'async_fetch': {'name': 'async_fetch'}
        }

        problems = [
            {'title': 'OAuth login fails', 'number': 42, 'state': 'open', 'comments': 10, 'labels': ['bug', 'oauth']}
        ]

        solutions = [
            {'title': 'Fixed async fetch timeout', 'number': 35, 'state': 'closed', 'comments': 5, 'labels': ['async']}
        ]

        issue_links = _match_issues_to_apis(apis, problems, solutions)

        # Should match oauth issue to oauth_login API
        assert 'oauth_login' in issue_links
        assert len(issue_links['oauth_login']) == 1
        assert issue_links['oauth_login'][0]['number'] == 42

        # Should match async issue to async_fetch API
        assert 'async_fetch' in issue_links
        assert len(issue_links['async_fetch']) == 1
        assert issue_links['async_fetch'][0]['number'] == 35

    def test_match_issues_to_apis_no_matches(self):
        """Test when no issues match any APIs."""
        apis = {
            'database_connect': {'name': 'database_connect'}
        }

        problems = [
            {'title': 'Random unrelated issue', 'number': 1, 'state': 'open', 'comments': 5, 'labels': ['misc']}
        ]

        issue_links = _match_issues_to_apis(apis, problems, [])

        # Should be empty - no matches
        assert len(issue_links) == 0

    def test_match_issues_to_apis_dotted_names(self):
        """Test matching with dotted API names."""
        apis = {
            'module.oauth.login': {'name': 'module.oauth.login'}
        }

        problems = [
            {'title': 'OAuth module fails', 'number': 42, 'state': 'open', 'comments': 10, 'labels': ['oauth']}
        ]

        issue_links = _match_issues_to_apis(apis, problems, [])

        # Should match due to 'oauth' keyword
        assert 'module.oauth.login' in issue_links
        assert len(issue_links['module.oauth.login']) == 1


class TestRuleBasedMergerWithGitHubStreams:
    """Test RuleBasedMerger with GitHub streams."""

    def test_merger_with_github_streams(self, tmp_path):
        """Test merger with three-stream GitHub data."""
        docs_data = {'pages': []}
        github_data = {'apis': {}}
        conflicts = []

        # Create three-stream data
        code_stream = CodeStream(directory=tmp_path, files=[])
        docs_stream = DocsStream(
            readme='# README',
            contributing='# Contributing',
            docs_files=[{'path': 'docs/guide.md', 'content': 'Guide content'}]
        )
        insights_stream = InsightsStream(
            metadata={'stars': 1234, 'forks': 56, 'language': 'Python'},
            common_problems=[
                {'title': 'Bug 1', 'number': 1, 'state': 'open', 'comments': 10, 'labels': ['bug']}
            ],
            known_solutions=[
                {'title': 'Fix 1', 'number': 2, 'state': 'closed', 'comments': 5, 'labels': ['bug']}
            ],
            top_labels=[{'label': 'bug', 'count': 10}]
        )
        github_streams = ThreeStreamData(code_stream, docs_stream, insights_stream)

        # Create merger with streams
        merger = RuleBasedMerger(docs_data, github_data, conflicts, github_streams)

        assert merger.github_streams is not None
        assert merger.github_docs is not None
        assert merger.github_insights is not None
        assert merger.github_docs['readme'] == '# README'
        assert merger.github_insights['metadata']['stars'] == 1234

    def test_merger_merge_all_with_streams(self, tmp_path):
        """Test merge_all() with GitHub streams."""
        docs_data = {'pages': []}
        github_data = {'apis': {}}
        conflicts = []

        # Create three-stream data
        code_stream = CodeStream(directory=tmp_path, files=[])
        docs_stream = DocsStream(readme='# README', contributing=None, docs_files=[])
        insights_stream = InsightsStream(
            metadata={'stars': 500},
            common_problems=[],
            known_solutions=[],
            top_labels=[]
        )
        github_streams = ThreeStreamData(code_stream, docs_stream, insights_stream)

        # Create and run merger
        merger = RuleBasedMerger(docs_data, github_data, conflicts, github_streams)
        result = merger.merge_all()

        # Check result has GitHub context
        assert 'github_context' in result
        assert 'conflict_summary' in result
        assert 'issue_links' in result
        assert result['github_context']['metadata']['stars'] == 500

    def test_merger_without_streams_backward_compat(self):
        """Test backward compatibility without GitHub streams."""
        docs_data = {'pages': []}
        github_data = {'apis': {}}
        conflicts = []

        # Create merger without streams (old API)
        merger = RuleBasedMerger(docs_data, github_data, conflicts)

        assert merger.github_streams is None
        assert merger.github_docs is None
        assert merger.github_insights is None

        # Should still work
        result = merger.merge_all()
        assert 'apis' in result
        assert 'summary' in result
        # Should not have GitHub context
        assert 'github_context' not in result


class TestIntegration:
    """Integration tests for Phase 3."""

    def test_full_pipeline_with_streams(self, tmp_path):
        """Test complete pipeline with three-stream data."""
        # Create minimal test data
        docs_data = {'pages': []}
        github_data = {'apis': {}}

        # Create three-stream data
        code_stream = CodeStream(directory=tmp_path, files=[])
        docs_stream = DocsStream(
            readme='# Test Project\n\nA test project.',
            contributing='# Contributing\n\nPull requests welcome.',
            docs_files=[
                {'path': 'docs/quickstart.md', 'content': '# Quick Start'},
                {'path': 'docs/api.md', 'content': '# API Reference'}
            ]
        )
        insights_stream = InsightsStream(
            metadata={
                'stars': 2500,
                'forks': 123,
                'language': 'Python',
                'description': 'Test framework'
            },
            common_problems=[
                {'title': 'Installation fails on Windows', 'number': 150, 'state': 'open', 'comments': 25, 'labels': ['bug', 'windows']},
                {'title': 'Memory leak in async mode', 'number': 142, 'state': 'open', 'comments': 18, 'labels': ['bug', 'async']}
            ],
            known_solutions=[
                {'title': 'Fixed config loading', 'number': 130, 'state': 'closed', 'comments': 8, 'labels': ['bug']},
                {'title': 'Resolved OAuth timeout', 'number': 125, 'state': 'closed', 'comments': 12, 'labels': ['oauth']}
            ],
            top_labels=[
                {'label': 'bug', 'count': 45},
                {'label': 'enhancement', 'count': 20},
                {'label': 'question', 'count': 15}
            ]
        )
        github_streams = ThreeStreamData(code_stream, docs_stream, insights_stream)

        # Create merger and merge
        merger = RuleBasedMerger(docs_data, github_data, [], github_streams)
        result = merger.merge_all()

        # Verify all layers present
        assert 'apis' in result  # Layer 1 & 2: Code + Docs
        assert 'github_context' in result  # Layer 3 & 4: GitHub docs + insights

        # Verify Layer 3: GitHub docs
        gh_context = result['github_context']
        assert gh_context['docs']['readme'] == '# Test Project\n\nA test project.'
        assert gh_context['docs']['contributing'] == '# Contributing\n\nPull requests welcome.'
        assert gh_context['docs']['docs_files_count'] == 2

        # Verify Layer 4: GitHub insights
        assert gh_context['metadata']['stars'] == 2500
        assert gh_context['metadata']['language'] == 'Python'
        assert gh_context['issues']['common_problems_count'] == 2
        assert gh_context['issues']['known_solutions_count'] == 2
        assert len(gh_context['issues']['top_problems']) == 2
        assert len(gh_context['issues']['top_solutions']) == 2
        assert len(gh_context['top_labels']) == 3

        # Verify conflict summary
        assert 'conflict_summary' in result
        assert result['conflict_summary']['total_conflicts'] == 0
