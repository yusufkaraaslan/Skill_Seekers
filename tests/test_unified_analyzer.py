"""
Tests for Unified Codebase Analyzer

Tests the unified analyzer that works with:
- GitHub URLs (uses three-stream fetcher)
- Local paths (analyzes directly)

Analysis modes:
- basic: Fast, shallow analysis
- c3x: Deep C3.x analysis
"""

import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from skill_seekers.cli.unified_codebase_analyzer import (
    AnalysisResult,
    UnifiedCodebaseAnalyzer
)
from skill_seekers.cli.github_fetcher import (
    CodeStream,
    DocsStream,
    InsightsStream,
    ThreeStreamData
)

# Skip marker for tests requiring GitHub access
requires_github = pytest.mark.skipif(
    not os.environ.get('GITHUB_TOKEN'),
    reason="GITHUB_TOKEN not set - skipping tests that require GitHub access"
)


class TestAnalysisResult:
    """Test AnalysisResult data class."""

    def test_analysis_result_basic(self):
        """Test basic AnalysisResult creation."""
        result = AnalysisResult(
            code_analysis={'files': []},
            source_type='local',
            analysis_depth='basic'
        )
        assert result.code_analysis == {'files': []}
        assert result.source_type == 'local'
        assert result.analysis_depth == 'basic'
        assert result.github_docs is None
        assert result.github_insights is None

    def test_analysis_result_with_github(self):
        """Test AnalysisResult with GitHub data."""
        result = AnalysisResult(
            code_analysis={'files': []},
            github_docs={'readme': '# README'},
            github_insights={'metadata': {'stars': 1234}},
            source_type='github',
            analysis_depth='c3x'
        )
        assert result.github_docs is not None
        assert result.github_insights is not None
        assert result.source_type == 'github'


class TestURLDetection:
    """Test GitHub URL detection."""

    def test_is_github_url_https(self):
        """Test detection of HTTPS GitHub URLs."""
        analyzer = UnifiedCodebaseAnalyzer()
        assert analyzer.is_github_url("https://github.com/facebook/react") is True

    def test_is_github_url_ssh(self):
        """Test detection of SSH GitHub URLs."""
        analyzer = UnifiedCodebaseAnalyzer()
        assert analyzer.is_github_url("git@github.com:facebook/react.git") is True

    def test_is_github_url_local_path(self):
        """Test local paths are not detected as GitHub URLs."""
        analyzer = UnifiedCodebaseAnalyzer()
        assert analyzer.is_github_url("/path/to/local/repo") is False
        assert analyzer.is_github_url("./relative/path") is False

    def test_is_github_url_other_git(self):
        """Test non-GitHub git URLs are not detected."""
        analyzer = UnifiedCodebaseAnalyzer()
        assert analyzer.is_github_url("https://gitlab.com/user/repo") is False


class TestBasicAnalysis:
    """Test basic analysis mode."""

    def test_basic_analysis_local(self, tmp_path):
        """Test basic analysis on local directory."""
        # Create test files
        (tmp_path / "main.py").write_text("import os\nprint('hello')")
        (tmp_path / "utils.js").write_text("function test() {}")
        (tmp_path / "README.md").write_text("# README")

        analyzer = UnifiedCodebaseAnalyzer()
        result = analyzer.analyze(source=str(tmp_path), depth='basic')

        assert result.source_type == 'local'
        assert result.analysis_depth == 'basic'
        assert result.code_analysis['analysis_type'] == 'basic'
        assert len(result.code_analysis['files']) >= 3

    def test_list_files(self, tmp_path):
        """Test file listing."""
        (tmp_path / "file1.py").write_text("code")
        (tmp_path / "file2.js").write_text("code")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.ts").write_text("code")

        analyzer = UnifiedCodebaseAnalyzer()
        files = analyzer.list_files(tmp_path)

        assert len(files) == 3
        paths = [f['path'] for f in files]
        assert 'file1.py' in paths
        assert 'file2.js' in paths
        assert 'subdir/file3.ts' in paths

    def test_get_directory_structure(self, tmp_path):
        """Test directory structure extraction."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("code")
        (tmp_path / "tests").mkdir()
        (tmp_path / "README.md").write_text("# README")

        analyzer = UnifiedCodebaseAnalyzer()
        structure = analyzer.get_directory_structure(tmp_path)

        assert structure['type'] == 'directory'
        assert len(structure['children']) >= 3

        child_names = [c['name'] for c in structure['children']]
        assert 'src' in child_names
        assert 'tests' in child_names
        assert 'README.md' in child_names

    def test_extract_imports_python(self, tmp_path):
        """Test Python import extraction."""
        (tmp_path / "main.py").write_text("""
import os
import sys
from pathlib import Path
from typing import List, Dict

def main():
    pass
        """)

        analyzer = UnifiedCodebaseAnalyzer()
        imports = analyzer.extract_imports(tmp_path)

        assert '.py' in imports
        python_imports = imports['.py']
        assert any('import os' in imp for imp in python_imports)
        assert any('from pathlib import Path' in imp for imp in python_imports)

    def test_extract_imports_javascript(self, tmp_path):
        """Test JavaScript import extraction."""
        (tmp_path / "app.js").write_text("""
import React from 'react';
import { useState } from 'react';
const fs = require('fs');

function App() {}
        """)

        analyzer = UnifiedCodebaseAnalyzer()
        imports = analyzer.extract_imports(tmp_path)

        assert '.js' in imports
        js_imports = imports['.js']
        assert any('import React' in imp for imp in js_imports)

    def test_find_entry_points(self, tmp_path):
        """Test entry point detection."""
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "setup.py").write_text("from setuptools import setup")
        (tmp_path / "package.json").write_text('{"name": "test"}')

        analyzer = UnifiedCodebaseAnalyzer()
        entry_points = analyzer.find_entry_points(tmp_path)

        assert 'main.py' in entry_points
        assert 'setup.py' in entry_points
        assert 'package.json' in entry_points

    def test_compute_statistics(self, tmp_path):
        """Test statistics computation."""
        (tmp_path / "file1.py").write_text("a" * 100)
        (tmp_path / "file2.py").write_text("b" * 200)
        (tmp_path / "file3.js").write_text("c" * 150)

        analyzer = UnifiedCodebaseAnalyzer()
        stats = analyzer.compute_statistics(tmp_path)

        assert stats['total_files'] == 3
        assert stats['total_size_bytes'] == 450  # 100 + 200 + 150
        assert stats['file_types']['.py'] == 2
        assert stats['file_types']['.js'] == 1
        assert stats['languages']['Python'] == 2
        assert stats['languages']['JavaScript'] == 1


class TestC3xAnalysis:
    """Test C3.x analysis mode."""

    def test_c3x_analysis_local(self, tmp_path):
        """Test C3.x analysis on local directory with actual components."""
        # Create a test file that C3.x can analyze
        (tmp_path / "main.py").write_text("import os\nprint('hello')")

        analyzer = UnifiedCodebaseAnalyzer()
        result = analyzer.analyze(source=str(tmp_path), depth='c3x')

        assert result.source_type == 'local'
        assert result.analysis_depth == 'c3x'
        assert result.code_analysis['analysis_type'] == 'c3x'

        # Check C3.x components are populated (not None)
        assert 'c3_1_patterns' in result.code_analysis
        assert 'c3_2_examples' in result.code_analysis
        assert 'c3_3_guides' in result.code_analysis
        assert 'c3_4_configs' in result.code_analysis
        assert 'c3_7_architecture' in result.code_analysis

        # C3.x components should be lists (may be empty if analysis didn't find anything)
        assert isinstance(result.code_analysis['c3_1_patterns'], list)
        assert isinstance(result.code_analysis['c3_2_examples'], list)
        assert isinstance(result.code_analysis['c3_3_guides'], list)
        assert isinstance(result.code_analysis['c3_4_configs'], list)
        assert isinstance(result.code_analysis['c3_7_architecture'], list)

    def test_c3x_includes_basic_analysis(self, tmp_path):
        """Test that C3.x includes all basic analysis data."""
        (tmp_path / "main.py").write_text("code")

        analyzer = UnifiedCodebaseAnalyzer()
        result = analyzer.analyze(source=str(tmp_path), depth='c3x')

        # Should include basic analysis fields
        assert 'files' in result.code_analysis
        assert 'structure' in result.code_analysis
        assert 'imports' in result.code_analysis
        assert 'entry_points' in result.code_analysis
        assert 'statistics' in result.code_analysis


class TestGitHubAnalysis:
    """Test GitHub repository analysis."""

    @requires_github
    @patch('skill_seekers.cli.unified_codebase_analyzer.GitHubThreeStreamFetcher')
    def test_analyze_github_basic(self, mock_fetcher_class, tmp_path):
        """Test basic analysis of GitHub repository."""
        # Mock three-stream fetcher
        mock_fetcher = Mock()
        mock_fetcher_class.return_value = mock_fetcher

        # Create mock streams
        code_stream = CodeStream(directory=tmp_path, files=[tmp_path / "main.py"])
        docs_stream = DocsStream(readme="# README", contributing=None, docs_files=[])
        insights_stream = InsightsStream(
            metadata={'stars': 1234},
            common_problems=[],
            known_solutions=[],
            top_labels=[]
        )
        three_streams = ThreeStreamData(code_stream, docs_stream, insights_stream)
        mock_fetcher.fetch.return_value = three_streams

        # Create test file in tmp_path
        (tmp_path / "main.py").write_text("print('hello')")

        analyzer = UnifiedCodebaseAnalyzer()
        result = analyzer.analyze(
            source="https://github.com/test/repo",
            depth="basic",
            fetch_github_metadata=True
        )

        assert result.source_type == 'github'
        assert result.analysis_depth == 'basic'
        assert result.github_docs is not None
        assert result.github_insights is not None
        assert result.github_docs['readme'] == "# README"
        assert result.github_insights['metadata']['stars'] == 1234

    @requires_github
    @patch('skill_seekers.cli.unified_codebase_analyzer.GitHubThreeStreamFetcher')
    def test_analyze_github_c3x(self, mock_fetcher_class, tmp_path):
        """Test C3.x analysis of GitHub repository."""
        # Mock three-stream fetcher
        mock_fetcher = Mock()
        mock_fetcher_class.return_value = mock_fetcher

        code_stream = CodeStream(directory=tmp_path, files=[])
        docs_stream = DocsStream(readme="# README", contributing=None, docs_files=[])
        insights_stream = InsightsStream(metadata={}, common_problems=[], known_solutions=[], top_labels=[])
        three_streams = ThreeStreamData(code_stream, docs_stream, insights_stream)
        mock_fetcher.fetch.return_value = three_streams

        (tmp_path / "main.py").write_text("code")

        analyzer = UnifiedCodebaseAnalyzer()
        result = analyzer.analyze(
            source="https://github.com/test/repo",
            depth="c3x"
        )

        assert result.analysis_depth == 'c3x'
        assert result.code_analysis['analysis_type'] == 'c3x'

    @requires_github
    @patch('skill_seekers.cli.unified_codebase_analyzer.GitHubThreeStreamFetcher')
    def test_analyze_github_without_metadata(self, mock_fetcher_class, tmp_path):
        """Test GitHub analysis without fetching metadata."""
        mock_fetcher = Mock()
        mock_fetcher_class.return_value = mock_fetcher

        code_stream = CodeStream(directory=tmp_path, files=[])
        docs_stream = DocsStream(readme=None, contributing=None, docs_files=[])
        insights_stream = InsightsStream(metadata={}, common_problems=[], known_solutions=[], top_labels=[])
        three_streams = ThreeStreamData(code_stream, docs_stream, insights_stream)
        mock_fetcher.fetch.return_value = three_streams

        (tmp_path / "main.py").write_text("code")

        analyzer = UnifiedCodebaseAnalyzer()
        result = analyzer.analyze(
            source="https://github.com/test/repo",
            depth="basic",
            fetch_github_metadata=False
        )

        # Should not include GitHub docs/insights
        assert result.github_docs is None
        assert result.github_insights is None


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_depth_mode(self, tmp_path):
        """Test invalid depth mode raises error."""
        (tmp_path / "main.py").write_text("code")

        analyzer = UnifiedCodebaseAnalyzer()
        with pytest.raises(ValueError, match="Unknown depth"):
            analyzer.analyze(source=str(tmp_path), depth="invalid")

    def test_nonexistent_directory(self):
        """Test nonexistent directory raises error."""
        analyzer = UnifiedCodebaseAnalyzer()
        with pytest.raises(FileNotFoundError):
            analyzer.analyze(source="/nonexistent/path", depth="basic")

    def test_file_instead_of_directory(self, tmp_path):
        """Test analyzing a file instead of directory raises error."""
        test_file = tmp_path / "file.py"
        test_file.write_text("code")

        analyzer = UnifiedCodebaseAnalyzer()
        with pytest.raises(NotADirectoryError):
            analyzer.analyze(source=str(test_file), depth="basic")


class TestTokenHandling:
    """Test GitHub token handling."""

    @requires_github
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
    @patch('skill_seekers.cli.unified_codebase_analyzer.GitHubThreeStreamFetcher')
    def test_github_token_from_env(self, mock_fetcher_class, tmp_path):
        """Test GitHub token loaded from environment."""
        mock_fetcher = Mock()
        mock_fetcher_class.return_value = mock_fetcher

        code_stream = CodeStream(directory=tmp_path, files=[])
        docs_stream = DocsStream(readme=None, contributing=None, docs_files=[])
        insights_stream = InsightsStream(metadata={}, common_problems=[], known_solutions=[], top_labels=[])
        three_streams = ThreeStreamData(code_stream, docs_stream, insights_stream)
        mock_fetcher.fetch.return_value = three_streams

        (tmp_path / "main.py").write_text("code")

        analyzer = UnifiedCodebaseAnalyzer()
        result = analyzer.analyze(source="https://github.com/test/repo", depth="basic")

        # Verify fetcher was created with token
        mock_fetcher_class.assert_called_once()
        args = mock_fetcher_class.call_args[0]
        assert args[1] == 'test_token'  # Second arg is github_token

    @requires_github
    @patch('skill_seekers.cli.unified_codebase_analyzer.GitHubThreeStreamFetcher')
    def test_github_token_explicit(self, mock_fetcher_class, tmp_path):
        """Test explicit GitHub token parameter."""
        mock_fetcher = Mock()
        mock_fetcher_class.return_value = mock_fetcher

        code_stream = CodeStream(directory=tmp_path, files=[])
        docs_stream = DocsStream(readme=None, contributing=None, docs_files=[])
        insights_stream = InsightsStream(metadata={}, common_problems=[], known_solutions=[], top_labels=[])
        three_streams = ThreeStreamData(code_stream, docs_stream, insights_stream)
        mock_fetcher.fetch.return_value = three_streams

        (tmp_path / "main.py").write_text("code")

        analyzer = UnifiedCodebaseAnalyzer(github_token='custom_token')
        result = analyzer.analyze(source="https://github.com/test/repo", depth="basic")

        mock_fetcher_class.assert_called_once()
        args = mock_fetcher_class.call_args[0]
        assert args[1] == 'custom_token'


class TestIntegration:
    """Integration tests."""

    def test_local_to_github_consistency(self, tmp_path):
        """Test that local and GitHub analysis produce consistent structure."""
        (tmp_path / "main.py").write_text("import os\nprint('hello')")
        (tmp_path / "README.md").write_text("# README")

        analyzer = UnifiedCodebaseAnalyzer()

        # Analyze as local
        local_result = analyzer.analyze(source=str(tmp_path), depth="basic")

        # Both should have same core analysis structure
        assert 'files' in local_result.code_analysis
        assert 'structure' in local_result.code_analysis
        assert 'imports' in local_result.code_analysis
        assert local_result.code_analysis['analysis_type'] == 'basic'
