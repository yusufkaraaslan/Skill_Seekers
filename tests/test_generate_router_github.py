"""
Tests for Phase 4: Router Generation with GitHub Integration

Tests the enhanced router generator that integrates GitHub insights:
- Enhanced topic definition using issue labels (2x weight)
- Router template with repository stats and top issues
- Sub-skill templates with "Common Issues" section
- GitHub issue linking
"""

import pytest
import json
import tempfile
from pathlib import Path
from skill_seekers.cli.generate_router import RouterGenerator
from skill_seekers.cli.github_fetcher import (
    CodeStream,
    DocsStream,
    InsightsStream,
    ThreeStreamData
)


class TestRouterGeneratorBasic:
    """Test basic router generation without GitHub streams (backward compat)."""

    def test_router_generator_init(self, tmp_path):
        """Test router generator initialization."""
        # Create test configs
        config1 = {
            'name': 'test-oauth',
            'description': 'OAuth authentication',
            'base_url': 'https://example.com',
            'categories': {'authentication': ['auth', 'oauth']}
        }
        config2 = {
            'name': 'test-async',
            'description': 'Async operations',
            'base_url': 'https://example.com',
            'categories': {'async': ['async', 'await']}
        }

        config_path1 = tmp_path / 'config1.json'
        config_path2 = tmp_path / 'config2.json'

        with open(config_path1, 'w') as f:
            json.dump(config1, f)
        with open(config_path2, 'w') as f:
            json.dump(config2, f)

        # Create generator
        generator = RouterGenerator([str(config_path1), str(config_path2)])

        assert generator.router_name == 'test'
        assert len(generator.configs) == 2
        assert generator.github_streams is None

    def test_infer_router_name(self, tmp_path):
        """Test router name inference from sub-skill names."""
        config1 = {
            'name': 'fastmcp-oauth',
            'base_url': 'https://example.com'
        }
        config2 = {
            'name': 'fastmcp-async',
            'base_url': 'https://example.com'
        }

        config_path1 = tmp_path / 'config1.json'
        config_path2 = tmp_path / 'config2.json'

        with open(config_path1, 'w') as f:
            json.dump(config1, f)
        with open(config_path2, 'w') as f:
            json.dump(config2, f)

        generator = RouterGenerator([str(config_path1), str(config_path2)])

        assert generator.router_name == 'fastmcp'

    def test_extract_routing_keywords_basic(self, tmp_path):
        """Test basic keyword extraction without GitHub."""
        config = {
            'name': 'test-oauth',
            'base_url': 'https://example.com',
            'categories': {
                'authentication': ['auth', 'oauth'],
                'tokens': ['token', 'jwt']
            }
        }

        config_path = tmp_path / 'config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f)

        generator = RouterGenerator([str(config_path)])
        routing = generator.extract_routing_keywords()

        assert 'test-oauth' in routing
        keywords = routing['test-oauth']
        assert 'authentication' in keywords
        assert 'tokens' in keywords
        assert 'oauth' in keywords  # From name


class TestRouterGeneratorWithGitHub:
    """Test router generation with GitHub streams (Phase 4)."""

    def test_router_with_github_metadata(self, tmp_path):
        """Test router generator with GitHub metadata."""
        config = {
            'name': 'test-oauth',
            'description': 'OAuth skill',
            'base_url': 'https://github.com/test/repo',
            'categories': {'oauth': ['oauth', 'auth']}
        }

        config_path = tmp_path / 'config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f)

        # Create GitHub streams
        code_stream = CodeStream(directory=tmp_path, files=[])
        docs_stream = DocsStream(
            readme='# Test Project\n\nA test OAuth library.',
            contributing=None,
            docs_files=[]
        )
        insights_stream = InsightsStream(
            metadata={'stars': 1234, 'forks': 56, 'language': 'Python', 'description': 'OAuth helper'},
            common_problems=[
                {'title': 'OAuth fails on redirect', 'number': 42, 'state': 'open', 'comments': 15, 'labels': ['bug', 'oauth']}
            ],
            known_solutions=[],
            top_labels=[{'label': 'oauth', 'count': 20}, {'label': 'bug', 'count': 10}]
        )
        github_streams = ThreeStreamData(code_stream, docs_stream, insights_stream)

        # Create generator with GitHub streams
        generator = RouterGenerator([str(config_path)], github_streams=github_streams)

        assert generator.github_metadata is not None
        assert generator.github_metadata['stars'] == 1234
        assert generator.github_docs is not None
        assert generator.github_docs['readme'].startswith('# Test Project')
        assert generator.github_issues is not None

    def test_extract_keywords_with_github_labels(self, tmp_path):
        """Test keyword extraction with GitHub issue labels (2x weight)."""
        config = {
            'name': 'test-oauth',
            'base_url': 'https://example.com',
            'categories': {'oauth': ['oauth', 'auth']}
        }

        config_path = tmp_path / 'config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f)

        # Create GitHub streams with top labels
        code_stream = CodeStream(directory=tmp_path, files=[])
        docs_stream = DocsStream(readme=None, contributing=None, docs_files=[])
        insights_stream = InsightsStream(
            metadata={},
            common_problems=[],
            known_solutions=[],
            top_labels=[
                {'label': 'oauth', 'count': 50},  # Matches 'oauth' keyword
                {'label': 'authentication', 'count': 30},  # Related
                {'label': 'bug', 'count': 20}  # Not related
            ]
        )
        github_streams = ThreeStreamData(code_stream, docs_stream, insights_stream)

        generator = RouterGenerator([str(config_path)], github_streams=github_streams)
        routing = generator.extract_routing_keywords()

        keywords = routing['test-oauth']
        # 'oauth' label should appear twice (2x weight)
        oauth_count = keywords.count('oauth')
        assert oauth_count >= 4  # Base 'oauth' from categories + name + 2x from label

    def test_generate_skill_md_with_github(self, tmp_path):
        """Test SKILL.md generation with GitHub metadata."""
        config = {
            'name': 'test-oauth',
            'description': 'OAuth authentication skill',
            'base_url': 'https://github.com/test/oauth',
            'categories': {'oauth': ['oauth']}
        }

        config_path = tmp_path / 'config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f)

        # Create GitHub streams
        code_stream = CodeStream(directory=tmp_path, files=[])
        docs_stream = DocsStream(
            readme='# OAuth Library\n\nQuick start: Install with pip install oauth',
            contributing=None,
            docs_files=[]
        )
        insights_stream = InsightsStream(
            metadata={'stars': 5000, 'forks': 200, 'language': 'Python', 'description': 'OAuth 2.0 library'},
            common_problems=[
                {'title': 'Redirect URI mismatch', 'number': 100, 'state': 'open', 'comments': 25, 'labels': ['bug', 'oauth']},
                {'title': 'Token refresh fails', 'number': 95, 'state': 'open', 'comments': 18, 'labels': ['oauth']}
            ],
            known_solutions=[],
            top_labels=[]
        )
        github_streams = ThreeStreamData(code_stream, docs_stream, insights_stream)

        generator = RouterGenerator([str(config_path)], github_streams=github_streams)
        skill_md = generator.generate_skill_md()

        # Check GitHub metadata section
        assert '⭐ 5,000' in skill_md
        assert 'Python' in skill_md
        assert 'OAuth 2.0 library' in skill_md

        # Check Quick Start from README
        assert '## Quick Start' in skill_md
        assert 'OAuth Library' in skill_md

        # Check that issue was converted to question in Examples section (Fix 1)
        assert '## Common Issues' in skill_md or '## Examples' in skill_md
        assert 'how do i handle redirect uri mismatch' in skill_md.lower() or 'how do i fix redirect uri mismatch' in skill_md.lower()
        # Note: Issue #100 may appear in Common Issues or as converted question in Examples

    def test_generate_skill_md_without_github(self, tmp_path):
        """Test SKILL.md generation without GitHub (backward compat)."""
        config = {
            'name': 'test-oauth',
            'description': 'OAuth skill',
            'base_url': 'https://example.com',
            'categories': {'oauth': ['oauth']}
        }

        config_path = tmp_path / 'config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f)

        # No GitHub streams
        generator = RouterGenerator([str(config_path)])
        skill_md = generator.generate_skill_md()

        # Should not have GitHub-specific sections
        assert '⭐' not in skill_md
        assert 'Repository Info' not in skill_md
        assert 'Quick Start (from README)' not in skill_md
        assert 'Common Issues (from GitHub)' not in skill_md

        # Should have basic sections
        assert 'When to Use This Skill' in skill_md
        assert 'How It Works' in skill_md


class TestSubSkillIssuesSection:
    """Test sub-skill issue section generation (Phase 4)."""

    def test_generate_subskill_issues_section(self, tmp_path):
        """Test generation of issues section for sub-skills."""
        config = {
            'name': 'test-oauth',
            'base_url': 'https://example.com',
            'categories': {'oauth': ['oauth']}
        }

        config_path = tmp_path / 'config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f)

        # Create GitHub streams with issues
        code_stream = CodeStream(directory=tmp_path, files=[])
        docs_stream = DocsStream(readme=None, contributing=None, docs_files=[])
        insights_stream = InsightsStream(
            metadata={},
            common_problems=[
                {'title': 'OAuth redirect fails', 'number': 50, 'state': 'open', 'comments': 20, 'labels': ['oauth', 'bug']},
                {'title': 'Token expiration issue', 'number': 45, 'state': 'open', 'comments': 15, 'labels': ['oauth']}
            ],
            known_solutions=[
                {'title': 'Fixed OAuth flow', 'number': 40, 'state': 'closed', 'comments': 10, 'labels': ['oauth']}
            ],
            top_labels=[]
        )
        github_streams = ThreeStreamData(code_stream, docs_stream, insights_stream)

        generator = RouterGenerator([str(config_path)], github_streams=github_streams)

        # Generate issues section for oauth topic
        issues_section = generator.generate_subskill_issues_section('test-oauth', ['oauth'])

        # Check content
        assert 'Common Issues (from GitHub)' in issues_section
        assert 'OAuth redirect fails' in issues_section
        assert 'Issue #50' in issues_section
        assert '20 comments' in issues_section
        assert '🔴' in issues_section  # Open issue icon
        assert '✅' in issues_section  # Closed issue icon

    def test_generate_subskill_issues_no_matches(self, tmp_path):
        """Test issues section when no issues match the topic."""
        config = {
            'name': 'test-async',
            'base_url': 'https://example.com',
            'categories': {'async': ['async']}
        }

        config_path = tmp_path / 'config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f)

        # Create GitHub streams with oauth issues (not async)
        code_stream = CodeStream(directory=tmp_path, files=[])
        docs_stream = DocsStream(readme=None, contributing=None, docs_files=[])
        insights_stream = InsightsStream(
            metadata={},
            common_problems=[
                {'title': 'OAuth fails', 'number': 1, 'state': 'open', 'comments': 5, 'labels': ['oauth']}
            ],
            known_solutions=[],
            top_labels=[]
        )
        github_streams = ThreeStreamData(code_stream, docs_stream, insights_stream)

        generator = RouterGenerator([str(config_path)], github_streams=github_streams)

        # Generate issues section for async topic (no matches)
        issues_section = generator.generate_subskill_issues_section('test-async', ['async'])

        # Unmatched issues go to 'other' category, so section is generated
        assert 'Common Issues (from GitHub)' in issues_section
        assert 'Other' in issues_section  # Unmatched issues
        assert 'OAuth fails' in issues_section  # The oauth issue


class TestIntegration:
    """Integration tests for Phase 4."""

    def test_full_router_generation_with_github(self, tmp_path):
        """Test complete router generation workflow with GitHub streams."""
        # Create multiple sub-skill configs
        config1 = {
            'name': 'fastmcp-oauth',
            'description': 'OAuth authentication in FastMCP',
            'base_url': 'https://github.com/test/fastmcp',
            'categories': {'oauth': ['oauth', 'auth']}
        }
        config2 = {
            'name': 'fastmcp-async',
            'description': 'Async operations in FastMCP',
            'base_url': 'https://github.com/test/fastmcp',
            'categories': {'async': ['async', 'await']}
        }

        config_path1 = tmp_path / 'config1.json'
        config_path2 = tmp_path / 'config2.json'

        with open(config_path1, 'w') as f:
            json.dump(config1, f)
        with open(config_path2, 'w') as f:
            json.dump(config2, f)

        # Create comprehensive GitHub streams
        code_stream = CodeStream(directory=tmp_path, files=[])
        docs_stream = DocsStream(
            readme='# FastMCP\n\nFast MCP server framework.\n\n## Installation\n\n```bash\npip install fastmcp\n```',
            contributing='# Contributing\n\nPull requests welcome!',
            docs_files=[
                {'path': 'docs/oauth.md', 'content': '# OAuth Guide'},
                {'path': 'docs/async.md', 'content': '# Async Guide'}
            ]
        )
        insights_stream = InsightsStream(
            metadata={
                'stars': 10000,
                'forks': 500,
                'language': 'Python',
                'description': 'Fast MCP server framework'
            },
            common_problems=[
                {'title': 'OAuth setup fails', 'number': 150, 'state': 'open', 'comments': 30, 'labels': ['bug', 'oauth']},
                {'title': 'Async deadlock', 'number': 142, 'state': 'open', 'comments': 25, 'labels': ['async', 'bug']},
                {'title': 'Token refresh issue', 'number': 130, 'state': 'open', 'comments': 20, 'labels': ['oauth']}
            ],
            known_solutions=[
                {'title': 'Fixed OAuth redirect', 'number': 120, 'state': 'closed', 'comments': 15, 'labels': ['oauth']},
                {'title': 'Resolved async race', 'number': 110, 'state': 'closed', 'comments': 12, 'labels': ['async']}
            ],
            top_labels=[
                {'label': 'oauth', 'count': 45},
                {'label': 'async', 'count': 38},
                {'label': 'bug', 'count': 30}
            ]
        )
        github_streams = ThreeStreamData(code_stream, docs_stream, insights_stream)

        # Create router generator
        generator = RouterGenerator(
            [str(config_path1), str(config_path2)],
            github_streams=github_streams
        )

        # Generate SKILL.md
        skill_md = generator.generate_skill_md()

        # Verify all Phase 4 enhancements present
        # 1. Repository metadata
        assert '⭐ 10,000' in skill_md
        assert 'Python' in skill_md
        assert 'Fast MCP server framework' in skill_md

        # 2. Quick start from README
        assert '## Quick Start' in skill_md
        assert 'pip install fastmcp' in skill_md

        # 3. Sub-skills listed
        assert 'fastmcp-oauth' in skill_md
        assert 'fastmcp-async' in skill_md

        # 4. Examples section with converted questions (Fix 1)
        assert '## Examples' in skill_md
        # Issues converted to natural questions
        assert 'how do i fix oauth setup' in skill_md.lower() or 'how do i handle oauth setup' in skill_md.lower()
        assert 'how do i handle async deadlock' in skill_md.lower() or 'how do i fix async deadlock' in skill_md.lower()
        # Common Issues section may still exist with other issues
        # Note: Issue numbers may appear in Common Issues or Common Patterns sections

        # 5. Routing keywords include GitHub labels (2x weight)
        routing = generator.extract_routing_keywords()
        oauth_keywords = routing['fastmcp-oauth']
        async_keywords = routing['fastmcp-async']

        # Labels should be included with 2x weight
        assert oauth_keywords.count('oauth') >= 2
        assert async_keywords.count('async') >= 2

        # Generate config
        router_config = generator.create_router_config()
        assert router_config['name'] == 'fastmcp'
        assert router_config['_router'] is True
        assert len(router_config['_sub_skills']) == 2
