"""
Tests for GitHub Three-Stream Fetcher

Tests the three-stream architecture that splits GitHub repositories into:
- Code stream (for C3.x)
- Docs stream (README, docs/*.md)
- Insights stream (issues, metadata)
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from skill_seekers.cli.github_fetcher import (
    CodeStream,
    DocsStream,
    InsightsStream,
    ThreeStreamData,
    GitHubThreeStreamFetcher
)


class TestDataClasses:
    """Test data class definitions."""

    def test_code_stream(self):
        """Test CodeStream data class."""
        code_stream = CodeStream(
            directory=Path("/tmp/repo"),
            files=[Path("/tmp/repo/src/main.py")]
        )
        assert code_stream.directory == Path("/tmp/repo")
        assert len(code_stream.files) == 1

    def test_docs_stream(self):
        """Test DocsStream data class."""
        docs_stream = DocsStream(
            readme="# README",
            contributing="# Contributing",
            docs_files=[{"path": "docs/guide.md", "content": "# Guide"}]
        )
        assert docs_stream.readme == "# README"
        assert docs_stream.contributing == "# Contributing"
        assert len(docs_stream.docs_files) == 1

    def test_insights_stream(self):
        """Test InsightsStream data class."""
        insights_stream = InsightsStream(
            metadata={"stars": 1234, "forks": 56},
            common_problems=[{"title": "Bug", "number": 42}],
            known_solutions=[{"title": "Fix", "number": 35}],
            top_labels=[{"label": "bug", "count": 10}]
        )
        assert insights_stream.metadata["stars"] == 1234
        assert len(insights_stream.common_problems) == 1
        assert len(insights_stream.known_solutions) == 1
        assert len(insights_stream.top_labels) == 1

    def test_three_stream_data(self):
        """Test ThreeStreamData combination."""
        three_streams = ThreeStreamData(
            code_stream=CodeStream(Path("/tmp"), []),
            docs_stream=DocsStream(None, None, []),
            insights_stream=InsightsStream({}, [], [], [])
        )
        assert isinstance(three_streams.code_stream, CodeStream)
        assert isinstance(three_streams.docs_stream, DocsStream)
        assert isinstance(three_streams.insights_stream, InsightsStream)


class TestGitHubFetcherInit:
    """Test GitHubThreeStreamFetcher initialization."""

    def test_parse_https_url(self):
        """Test parsing HTTPS GitHub URLs."""
        fetcher = GitHubThreeStreamFetcher("https://github.com/facebook/react")
        assert fetcher.owner == "facebook"
        assert fetcher.repo == "react"

    def test_parse_https_url_with_git(self):
        """Test parsing HTTPS URLs with .git suffix."""
        fetcher = GitHubThreeStreamFetcher("https://github.com/facebook/react.git")
        assert fetcher.owner == "facebook"
        assert fetcher.repo == "react"

    def test_parse_git_url(self):
        """Test parsing git@ URLs."""
        fetcher = GitHubThreeStreamFetcher("git@github.com:facebook/react.git")
        assert fetcher.owner == "facebook"
        assert fetcher.repo == "react"

    def test_invalid_url(self):
        """Test invalid URL raises error."""
        with pytest.raises(ValueError):
            GitHubThreeStreamFetcher("https://invalid.com/repo")

    @patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
    def test_github_token_from_env(self):
        """Test GitHub token loaded from environment."""
        fetcher = GitHubThreeStreamFetcher("https://github.com/facebook/react")
        assert fetcher.github_token == 'test_token'


class TestFileClassification:
    """Test file classification into code vs docs."""

    def test_classify_files(self, tmp_path):
        """Test classify_files separates code and docs correctly."""
        # Create test directory structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hello')")
        (tmp_path / "src" / "utils.js").write_text("function(){}")

        (tmp_path / "docs").mkdir()
        (tmp_path / "README.md").write_text("# README")
        (tmp_path / "docs" / "guide.md").write_text("# Guide")
        (tmp_path / "docs" / "api.rst").write_text("API")

        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "lib.js").write_text("// should be excluded")

        fetcher = GitHubThreeStreamFetcher("https://github.com/test/repo")
        code_files, doc_files = fetcher.classify_files(tmp_path)

        # Check code files
        code_paths = [f.name for f in code_files]
        assert "main.py" in code_paths
        assert "utils.js" in code_paths
        assert "lib.js" not in code_paths  # Excluded

        # Check doc files
        doc_paths = [f.name for f in doc_files]
        assert "README.md" in doc_paths
        assert "guide.md" in doc_paths
        assert "api.rst" in doc_paths

    def test_classify_excludes_hidden_files(self, tmp_path):
        """Test that hidden files are excluded (except in docs/)."""
        (tmp_path / ".hidden.py").write_text("hidden")
        (tmp_path / "visible.py").write_text("visible")

        fetcher = GitHubThreeStreamFetcher("https://github.com/test/repo")
        code_files, doc_files = fetcher.classify_files(tmp_path)

        code_names = [f.name for f in code_files]
        assert ".hidden.py" not in code_names
        assert "visible.py" in code_names

    def test_classify_various_code_extensions(self, tmp_path):
        """Test classification of various code file extensions."""
        extensions = ['.py', '.js', '.ts', '.go', '.rs', '.java', '.kt', '.rb', '.php']

        for ext in extensions:
            (tmp_path / f"file{ext}").write_text("code")

        fetcher = GitHubThreeStreamFetcher("https://github.com/test/repo")
        code_files, doc_files = fetcher.classify_files(tmp_path)

        assert len(code_files) == len(extensions)


class TestIssueAnalysis:
    """Test GitHub issue analysis."""

    def test_analyze_issues_common_problems(self):
        """Test extraction of common problems (open issues with 5+ comments)."""
        issues = [
            {
                'title': 'OAuth fails',
                'number': 42,
                'state': 'open',
                'comments': 10,
                'labels': [{'name': 'bug'}, {'name': 'oauth'}]
            },
            {
                'title': 'Minor issue',
                'number': 43,
                'state': 'open',
                'comments': 2,  # Too few comments
                'labels': []
            }
        ]

        fetcher = GitHubThreeStreamFetcher("https://github.com/test/repo")
        insights = fetcher.analyze_issues(issues)

        assert len(insights['common_problems']) == 1
        assert insights['common_problems'][0]['number'] == 42
        assert insights['common_problems'][0]['comments'] == 10

    def test_analyze_issues_known_solutions(self):
        """Test extraction of known solutions (closed issues with comments)."""
        issues = [
            {
                'title': 'Fixed OAuth',
                'number': 35,
                'state': 'closed',
                'comments': 5,
                'labels': [{'name': 'bug'}]
            },
            {
                'title': 'Closed without comments',
                'number': 36,
                'state': 'closed',
                'comments': 0,  # No comments
                'labels': []
            }
        ]

        fetcher = GitHubThreeStreamFetcher("https://github.com/test/repo")
        insights = fetcher.analyze_issues(issues)

        assert len(insights['known_solutions']) == 1
        assert insights['known_solutions'][0]['number'] == 35

    def test_analyze_issues_top_labels(self):
        """Test counting of top issue labels."""
        issues = [
            {'state': 'open', 'comments': 5, 'labels': [{'name': 'bug'}, {'name': 'oauth'}]},
            {'state': 'open', 'comments': 5, 'labels': [{'name': 'bug'}]},
            {'state': 'closed', 'comments': 3, 'labels': [{'name': 'enhancement'}]}
        ]

        fetcher = GitHubThreeStreamFetcher("https://github.com/test/repo")
        insights = fetcher.analyze_issues(issues)

        # Bug should be top label (appears twice)
        assert insights['top_labels'][0]['label'] == 'bug'
        assert insights['top_labels'][0]['count'] == 2

    def test_analyze_issues_limits_to_10(self):
        """Test that analysis limits results to top 10."""
        issues = [
            {
                'title': f'Issue {i}',
                'number': i,
                'state': 'open',
                'comments': 20 - i,  # Descending comment count
                'labels': []
            }
            for i in range(20)
        ]

        fetcher = GitHubThreeStreamFetcher("https://github.com/test/repo")
        insights = fetcher.analyze_issues(issues)

        assert len(insights['common_problems']) <= 10
        # Should be sorted by comment count (descending)
        if len(insights['common_problems']) > 1:
            assert insights['common_problems'][0]['comments'] >= insights['common_problems'][1]['comments']


class TestGitHubAPI:
    """Test GitHub API interactions."""

    @patch('requests.get')
    def test_fetch_github_metadata(self, mock_get):
        """Test fetching repository metadata via GitHub API."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'stargazers_count': 1234,
            'forks_count': 56,
            'open_issues_count': 12,
            'language': 'Python',
            'description': 'Test repo',
            'homepage': 'https://example.com',
            'created_at': '2020-01-01',
            'updated_at': '2024-01-01'
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = GitHubThreeStreamFetcher("https://github.com/test/repo")
        metadata = fetcher.fetch_github_metadata()

        assert metadata['stars'] == 1234
        assert metadata['forks'] == 56
        assert metadata['language'] == 'Python'

    @patch('requests.get')
    def test_fetch_github_metadata_failure(self, mock_get):
        """Test graceful handling of metadata fetch failure."""
        mock_get.side_effect = Exception("API error")

        fetcher = GitHubThreeStreamFetcher("https://github.com/test/repo")
        metadata = fetcher.fetch_github_metadata()

        # Should return default values instead of crashing
        assert metadata['stars'] == 0
        assert metadata['language'] == 'Unknown'

    @patch('requests.get')
    def test_fetch_issues(self, mock_get):
        """Test fetching issues via GitHub API."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                'title': 'Bug',
                'number': 42,
                'state': 'open',
                'comments': 10,
                'labels': [{'name': 'bug'}]
            }
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = GitHubThreeStreamFetcher("https://github.com/test/repo")
        issues = fetcher.fetch_issues(max_issues=100)

        assert len(issues) > 0
        # Should be called twice (open + closed)
        assert mock_get.call_count == 2

    @patch('requests.get')
    def test_fetch_issues_filters_pull_requests(self, mock_get):
        """Test that pull requests are filtered out of issues."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {'title': 'Issue', 'number': 42, 'state': 'open', 'comments': 5, 'labels': []},
            {'title': 'PR', 'number': 43, 'state': 'open', 'comments': 3, 'labels': [], 'pull_request': {}}
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = GitHubThreeStreamFetcher("https://github.com/test/repo")
        issues = fetcher.fetch_issues(max_issues=100)

        # Should only include the issue, not the PR
        assert all('pull_request' not in issue for issue in issues)


class TestReadFile:
    """Test file reading utilities."""

    def test_read_file_success(self, tmp_path):
        """Test successful file reading."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!")

        fetcher = GitHubThreeStreamFetcher("https://github.com/test/repo")
        content = fetcher.read_file(test_file)

        assert content == "Hello, world!"

    def test_read_file_not_found(self, tmp_path):
        """Test reading non-existent file returns None."""
        fetcher = GitHubThreeStreamFetcher("https://github.com/test/repo")
        content = fetcher.read_file(tmp_path / "missing.txt")

        assert content is None

    def test_read_file_encoding_fallback(self, tmp_path):
        """Test fallback to latin-1 encoding if UTF-8 fails."""
        test_file = tmp_path / "test.txt"
        # Write bytes that are invalid UTF-8 but valid latin-1
        test_file.write_bytes(b'\xff\xfe')

        fetcher = GitHubThreeStreamFetcher("https://github.com/test/repo")
        content = fetcher.read_file(test_file)

        # Should still read successfully with latin-1
        assert content is not None


class TestIntegration:
    """Integration tests for complete three-stream fetching."""

    @patch('subprocess.run')
    @patch('requests.get')
    def test_fetch_integration(self, mock_get, mock_run, tmp_path):
        """Test complete fetch() integration."""
        # Mock git clone
        mock_run.return_value = Mock(returncode=0, stderr="")

        # Mock GitHub API calls
        def api_side_effect(*args, **kwargs):
            url = args[0]
            mock_response = Mock()
            mock_response.raise_for_status = Mock()

            if 'repos/' in url and '/issues' not in url:
                # Metadata call
                mock_response.json.return_value = {
                    'stargazers_count': 1234,
                    'forks_count': 56,
                    'open_issues_count': 12,
                    'language': 'Python'
                }
            else:
                # Issues call
                mock_response.json.return_value = [
                    {
                        'title': 'Test Issue',
                        'number': 42,
                        'state': 'open',
                        'comments': 10,
                        'labels': [{'name': 'bug'}]
                    }
                ]
            return mock_response

        mock_get.side_effect = api_side_effect

        # Create test repo structure
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        (repo_dir / "src").mkdir()
        (repo_dir / "src" / "main.py").write_text("print('hello')")
        (repo_dir / "README.md").write_text("# README")

        fetcher = GitHubThreeStreamFetcher("https://github.com/test/repo")

        # Mock clone to use our tmp_path
        with patch.object(fetcher, 'clone_repo', return_value=repo_dir):
            three_streams = fetcher.fetch()

        # Verify all 3 streams present
        assert three_streams.code_stream is not None
        assert three_streams.docs_stream is not None
        assert three_streams.insights_stream is not None

        # Verify code stream
        assert len(three_streams.code_stream.files) > 0

        # Verify docs stream
        assert three_streams.docs_stream.readme is not None
        assert "# README" in three_streams.docs_stream.readme

        # Verify insights stream
        assert three_streams.insights_stream.metadata['stars'] == 1234
        assert len(three_streams.insights_stream.common_problems) > 0
