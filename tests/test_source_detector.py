"""Tests for source type detection.

Tests the SourceDetector class's ability to identify and parse:
- Web URLs
- GitHub repositories
- Local directories
- PDF files
- Config files
"""

import os
import tempfile
import pytest
from pathlib import Path

from skill_seekers.cli.source_detector import SourceDetector, SourceInfo


class TestWebDetection:
    """Test web URL detection."""

    def test_detect_full_https_url(self):
        """Full HTTPS URL should be detected as web."""
        info = SourceDetector.detect("https://docs.react.dev/")
        assert info.type == 'web'
        assert info.parsed['url'] == "https://docs.react.dev/"
        assert info.suggested_name == 'react'

    def test_detect_full_http_url(self):
        """Full HTTP URL should be detected as web."""
        info = SourceDetector.detect("http://example.com/docs")
        assert info.type == 'web'
        assert info.parsed['url'] == "http://example.com/docs"

    def test_detect_domain_only(self):
        """Domain without protocol should add https:// and detect as web."""
        info = SourceDetector.detect("docs.react.dev")
        assert info.type == 'web'
        assert info.parsed['url'] == "https://docs.react.dev"
        assert info.suggested_name == 'react'

    def test_detect_complex_url(self):
        """Complex URL with path should be detected as web."""
        info = SourceDetector.detect("https://docs.python.org/3/library/")
        assert info.type == 'web'
        assert info.parsed['url'] == "https://docs.python.org/3/library/"
        assert info.suggested_name == 'python'

    def test_suggested_name_removes_www(self):
        """Should remove www. prefix from suggested name."""
        info = SourceDetector.detect("https://www.example.com/")
        assert info.type == 'web'
        assert info.suggested_name == 'example'

    def test_suggested_name_removes_docs(self):
        """Should remove docs. prefix from suggested name."""
        info = SourceDetector.detect("https://docs.vue.org/")
        assert info.type == 'web'
        assert info.suggested_name == 'vue'


class TestGitHubDetection:
    """Test GitHub repository detection."""

    def test_detect_owner_repo_format(self):
        """owner/repo format should be detected as GitHub."""
        info = SourceDetector.detect("facebook/react")
        assert info.type == 'github'
        assert info.parsed['repo'] == "facebook/react"
        assert info.suggested_name == 'react'

    def test_detect_github_https_url(self):
        """Full GitHub HTTPS URL should be detected."""
        info = SourceDetector.detect("https://github.com/facebook/react")
        assert info.type == 'github'
        assert info.parsed['repo'] == "facebook/react"
        assert info.suggested_name == 'react'

    def test_detect_github_url_with_git_suffix(self):
        """GitHub URL with .git should strip suffix."""
        info = SourceDetector.detect("https://github.com/facebook/react.git")
        assert info.type == 'github'
        assert info.parsed['repo'] == "facebook/react"
        assert info.suggested_name == 'react'

    def test_detect_github_url_without_protocol(self):
        """GitHub URL without protocol should be detected."""
        info = SourceDetector.detect("github.com/vuejs/vue")
        assert info.type == 'github'
        assert info.parsed['repo'] == "vuejs/vue"
        assert info.suggested_name == 'vue'

    def test_owner_repo_with_dots_and_dashes(self):
        """Repo names with dots and dashes should work."""
        info = SourceDetector.detect("microsoft/vscode-python")
        assert info.type == 'github'
        assert info.parsed['repo'] == "microsoft/vscode-python"
        assert info.suggested_name == 'vscode-python'


class TestLocalDetection:
    """Test local directory detection."""

    def test_detect_relative_directory(self, tmp_path):
        """Relative directory path should be detected."""
        # Create a test directory
        test_dir = tmp_path / "my_project"
        test_dir.mkdir()

        # Change to parent directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            info = SourceDetector.detect("./my_project")
            assert info.type == 'local'
            assert 'my_project' in info.parsed['directory']
            assert info.suggested_name == 'my_project'
        finally:
            os.chdir(original_cwd)

    def test_detect_absolute_directory(self, tmp_path):
        """Absolute directory path should be detected."""
        # Create a test directory
        test_dir = tmp_path / "test_repo"
        test_dir.mkdir()

        info = SourceDetector.detect(str(test_dir))
        assert info.type == 'local'
        assert info.parsed['directory'] == str(test_dir.resolve())
        assert info.suggested_name == 'test_repo'

    def test_detect_current_directory(self):
        """Current directory (.) should be detected."""
        cwd = os.getcwd()
        info = SourceDetector.detect(".")
        assert info.type == 'local'
        assert info.parsed['directory'] == cwd


class TestPDFDetection:
    """Test PDF file detection."""

    def test_detect_pdf_extension(self):
        """File with .pdf extension should be detected."""
        info = SourceDetector.detect("tutorial.pdf")
        assert info.type == 'pdf'
        assert info.parsed['file_path'] == "tutorial.pdf"
        assert info.suggested_name == 'tutorial'

    def test_detect_pdf_with_path(self):
        """PDF file with path should be detected."""
        info = SourceDetector.detect("/path/to/guide.pdf")
        assert info.type == 'pdf'
        assert info.parsed['file_path'] == "/path/to/guide.pdf"
        assert info.suggested_name == 'guide'

    def test_suggested_name_removes_pdf_extension(self):
        """Suggested name should not include .pdf extension."""
        info = SourceDetector.detect("my-awesome-guide.pdf")
        assert info.type == 'pdf'
        assert info.suggested_name == 'my-awesome-guide'


class TestConfigDetection:
    """Test config file detection."""

    def test_detect_json_extension(self):
        """File with .json extension should be detected as config."""
        info = SourceDetector.detect("react.json")
        assert info.type == 'config'
        assert info.parsed['config_path'] == "react.json"
        assert info.suggested_name == 'react'

    def test_detect_config_with_path(self):
        """Config file with path should be detected."""
        info = SourceDetector.detect("configs/django.json")
        assert info.type == 'config'
        assert info.parsed['config_path'] == "configs/django.json"
        assert info.suggested_name == 'django'


class TestValidation:
    """Test source validation."""

    def test_validate_existing_directory(self, tmp_path):
        """Validation should pass for existing directory."""
        test_dir = tmp_path / "exists"
        test_dir.mkdir()

        info = SourceDetector.detect(str(test_dir))
        # Should not raise
        SourceDetector.validate_source(info)

    def test_validate_nonexistent_directory(self):
        """Validation should fail for nonexistent directory."""
        # Use a path that definitely doesn't exist
        nonexistent = "/tmp/definitely_does_not_exist_12345"

        # First try to detect it (will succeed since it looks like a path)
        with pytest.raises(ValueError, match="Directory does not exist"):
            info = SourceInfo(
                type='local',
                parsed={'directory': nonexistent},
                suggested_name='test',
                raw_input=nonexistent
            )
            SourceDetector.validate_source(info)

    def test_validate_existing_pdf(self, tmp_path):
        """Validation should pass for existing PDF."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.touch()

        info = SourceDetector.detect(str(pdf_file))
        # Should not raise
        SourceDetector.validate_source(info)

    def test_validate_nonexistent_pdf(self):
        """Validation should fail for nonexistent PDF."""
        with pytest.raises(ValueError, match="PDF file does not exist"):
            info = SourceInfo(
                type='pdf',
                parsed={'file_path': '/tmp/nonexistent.pdf'},
                suggested_name='test',
                raw_input='/tmp/nonexistent.pdf'
            )
            SourceDetector.validate_source(info)

    def test_validate_existing_config(self, tmp_path):
        """Validation should pass for existing config."""
        config_file = tmp_path / "test.json"
        config_file.touch()

        info = SourceDetector.detect(str(config_file))
        # Should not raise
        SourceDetector.validate_source(info)

    def test_validate_nonexistent_config(self):
        """Validation should fail for nonexistent config."""
        with pytest.raises(ValueError, match="Config file does not exist"):
            info = SourceInfo(
                type='config',
                parsed={'config_path': '/tmp/nonexistent.json'},
                suggested_name='test',
                raw_input='/tmp/nonexistent.json'
            )
            SourceDetector.validate_source(info)


class TestAmbiguousCases:
    """Test handling of ambiguous inputs."""

    def test_invalid_input_raises_error(self):
        """Invalid input should raise clear error with examples."""
        with pytest.raises(ValueError) as exc_info:
            SourceDetector.detect("invalid_input_without_dots_or_slashes")

        error_msg = str(exc_info.value)
        assert "Cannot determine source type" in error_msg
        assert "Examples:" in error_msg
        assert "skill-seekers create" in error_msg

    def test_github_takes_precedence_over_web(self):
        """GitHub URL should be detected as github, not web."""
        # Even though this is a URL, it should be detected as GitHub
        info = SourceDetector.detect("https://github.com/owner/repo")
        assert info.type == 'github'
        assert info.parsed['repo'] == "owner/repo"

    def test_directory_takes_precedence_over_domain(self, tmp_path):
        """Existing directory should be detected even if it looks like domain."""
        # Create a directory that looks like a domain
        dir_like_domain = tmp_path / "example.com"
        dir_like_domain.mkdir()

        info = SourceDetector.detect(str(dir_like_domain))
        # Should detect as local directory, not web
        assert info.type == 'local'


class TestRawInputPreservation:
    """Test that raw_input is preserved correctly."""

    def test_raw_input_preserved_for_web(self):
        """Original input should be stored in raw_input."""
        original = "https://docs.python.org/"
        info = SourceDetector.detect(original)
        assert info.raw_input == original

    def test_raw_input_preserved_for_github(self):
        """Original input should be stored even after parsing."""
        original = "facebook/react"
        info = SourceDetector.detect(original)
        assert info.raw_input == original

    def test_raw_input_preserved_for_local(self, tmp_path):
        """Original input should be stored before path normalization."""
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        original = str(test_dir)
        info = SourceDetector.detect(original)
        assert info.raw_input == original


class TestEdgeCases:
    """Test edge cases and corner cases."""

    def test_trailing_slash_in_url(self):
        """URLs with and without trailing slash should work."""
        info1 = SourceDetector.detect("https://docs.react.dev/")
        info2 = SourceDetector.detect("https://docs.react.dev")

        assert info1.type == 'web'
        assert info2.type == 'web'

    def test_uppercase_in_github_repo(self):
        """GitHub repos with uppercase should be detected."""
        info = SourceDetector.detect("Microsoft/TypeScript")
        assert info.type == 'github'
        assert info.parsed['repo'] == "Microsoft/TypeScript"

    def test_numbers_in_repo_name(self):
        """GitHub repos with numbers should be detected."""
        info = SourceDetector.detect("python/cpython3.11")
        assert info.type == 'github'

    def test_nested_directory_path(self, tmp_path):
        """Nested directory paths should work."""
        nested = tmp_path / "a" / "b" / "c"
        nested.mkdir(parents=True)

        info = SourceDetector.detect(str(nested))
        assert info.type == 'local'
        assert info.suggested_name == 'c'
