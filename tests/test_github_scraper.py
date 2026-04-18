#!/usr/bin/env python3
"""
Tests for GitHub Scraper (cli/github_scraper.py)

Tests cover:
- GitHubScraper initialization and configuration (C1.1)
- README extraction (C1.2)
- Language detection (C1.4)
- GitHub Issues extraction (C1.7)
- CHANGELOG extraction (C1.8)
- GitHub Releases extraction (C1.9)
- GitHubToSkillConverter and skill building (C1.10)
- Authentication handling
- Error handling and edge cases
"""

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

try:
    from github import Github, GithubException  # noqa: F401

    PYGITHUB_AVAILABLE = True
except ImportError:
    PYGITHUB_AVAILABLE = False


class TestGitHubScraperInitialization(unittest.TestCase):
    """Test GitHubScraper initialization and configuration (C1.1)"""

    def setUp(self):
        if not PYGITHUB_AVAILABLE:
            self.skipTest("PyGithub not installed")
        from skill_seekers.cli.github_scraper import GitHubScraper

        self.GitHubScraper = GitHubScraper

        # Create temporary directory for test output
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir)

    def tearDown(self):
        # Clean up temporary directory
        if hasattr(self, "temp_dir"):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_with_repo_name(self):
        """Test initialization with repository name"""
        config = {"repo": "facebook/react", "name": "react", "github_token": None}

        scraper = self.GitHubScraper(config)

        self.assertEqual(scraper.repo_name, "facebook/react")
        self.assertEqual(scraper.name, "react")
        self.assertIsNotNone(scraper.github)

    def test_init_with_token_from_config(self):
        """Test initialization with token from config"""
        config = {
            "repo": "facebook/react",
            "name": "react",
            "github_token": "test_token_123",
        }

        # Clear GITHUB_TOKEN env var so config token is used (env takes priority)
        env = {k: v for k, v in os.environ.items() if k != "GITHUB_TOKEN"}
        with (
            patch.dict(os.environ, env, clear=True),
            patch("skill_seekers.cli.github_scraper.Github") as mock_github,
        ):
            _scraper = self.GitHubScraper(config)
            mock_github.assert_called_once_with("test_token_123")

    def test_init_with_token_from_env(self):
        """Test initialization with token from environment variable"""
        config = {"repo": "facebook/react", "name": "react", "github_token": None}

        with (
            patch.dict(os.environ, {"GITHUB_TOKEN": "env_token_456"}),
            patch("skill_seekers.cli.github_scraper.Github") as mock_github,
        ):
            _scraper = self.GitHubScraper(config)
            mock_github.assert_called_once_with("env_token_456")

    def test_init_without_token(self):
        """Test initialization without authentication"""
        config = {"repo": "facebook/react", "name": "react", "github_token": None}

        with (
            patch("skill_seekers.cli.github_scraper.Github"),
            patch.dict(os.environ, {}, clear=True),
        ):
            scraper = self.GitHubScraper(config)
            # Should create unauthenticated client
            self.assertIsNotNone(scraper.github)

    def test_token_priority_env_over_config(self):
        """Test that GITHUB_TOKEN env var takes priority over config"""
        config = {
            "repo": "facebook/react",
            "name": "react",
            "github_token": "config_token",
        }

        with patch.dict(os.environ, {"GITHUB_TOKEN": "env_token"}):
            scraper = self.GitHubScraper(config)
            token = scraper._get_token()
            self.assertEqual(token, "env_token")


class TestREADMEExtraction(unittest.TestCase):
    """Test README extraction (C1.2)"""

    def setUp(self):
        if not PYGITHUB_AVAILABLE:
            self.skipTest("PyGithub not installed")
        from skill_seekers.cli.github_scraper import GitHubScraper

        self.GitHubScraper = GitHubScraper

    def test_extract_readme_success(self):
        """Test successful README extraction"""
        config = {"repo": "facebook/react", "name": "react", "github_token": None}

        mock_content = Mock()
        mock_content.decoded_content = b"# React\n\nA JavaScript library"

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_contents.return_value = mock_content

            scraper._extract_readme()

            self.assertIn("readme", scraper.extracted_data)
            self.assertEqual(scraper.extracted_data["readme"], "# React\n\nA JavaScript library")

    def test_extract_readme_tries_multiple_locations(self):
        """Test that README extraction tries multiple file locations"""
        config = {"repo": "facebook/react", "name": "react", "github_token": None}

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()

            # Make first attempts fail, succeed on third
            def side_effect(path):
                if path in ["README.md", "README.rst"]:
                    raise GithubException(404, "Not found")
                mock_content = Mock()
                mock_content.decoded_content = b"# README"
                return mock_content

            scraper.repo.get_contents.side_effect = side_effect

            scraper._extract_readme()

            # Should have tried multiple paths
            self.assertGreaterEqual(scraper.repo.get_contents.call_count, 1)

    def test_extract_readme_not_found(self):
        """Test README extraction when no README exists"""
        config = {"repo": "test/norepo", "name": "norepo", "github_token": None}

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_contents.side_effect = GithubException(404, "Not found")

            scraper._extract_readme()

            # Should not crash, just log warning (readme initialized as empty string)
            self.assertEqual(scraper.extracted_data["readme"], "")


class TestLanguageDetection(unittest.TestCase):
    """Test language detection (C1.4)"""

    def setUp(self):
        if not PYGITHUB_AVAILABLE:
            self.skipTest("PyGithub not installed")
        from skill_seekers.cli.github_scraper import GitHubScraper

        self.GitHubScraper = GitHubScraper

    def test_extract_languages_success(self):
        """Test successful language detection"""
        config = {"repo": "facebook/react", "name": "react", "github_token": None}

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_languages.return_value = {
                "JavaScript": 8000,
                "TypeScript": 2000,
            }

            scraper._extract_languages()

            self.assertIn("languages", scraper.extracted_data)
            self.assertIn("JavaScript", scraper.extracted_data["languages"])
            self.assertIn("TypeScript", scraper.extracted_data["languages"])

            # Check percentages
            js_data = scraper.extracted_data["languages"]["JavaScript"]
            self.assertEqual(js_data["bytes"], 8000)
            self.assertEqual(js_data["percentage"], 80.0)

            ts_data = scraper.extracted_data["languages"]["TypeScript"]
            self.assertEqual(ts_data["bytes"], 2000)
            self.assertEqual(ts_data["percentage"], 20.0)

    def test_extract_languages_empty(self):
        """Test language detection with no languages"""
        config = {"repo": "test/norepo", "name": "norepo", "github_token": None}

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_languages.return_value = {}

            scraper._extract_languages()

            self.assertIn("languages", scraper.extracted_data)
            self.assertEqual(scraper.extracted_data["languages"], {})

    def test_extract_languages_filters_non_integer_metadata(self):
        """Test that non-integer metadata keys (e.g., 'url') are filtered out (#322)"""
        config = {"repo": "xyflow/xyflow", "name": "xyflow", "github_token": None}

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_languages.return_value = {
                "TypeScript": 707330,
                "Svelte": 95784,
                "url": "https://api.github.com/repos/xyflow/xyflow/languages",
            }

            scraper._extract_languages()

            self.assertIn("languages", scraper.extracted_data)
            self.assertIn("TypeScript", scraper.extracted_data["languages"])
            self.assertIn("Svelte", scraper.extracted_data["languages"])
            self.assertNotIn("url", scraper.extracted_data["languages"])

            # Percentages should be calculated only from real languages
            ts_data = scraper.extracted_data["languages"]["TypeScript"]
            total = 707330 + 95784
            self.assertEqual(ts_data["percentage"], round(707330 / total * 100, 2))


class TestIssuesExtraction(unittest.TestCase):
    """Test GitHub Issues extraction (C1.7)"""

    def setUp(self):
        if not PYGITHUB_AVAILABLE:
            self.skipTest("PyGithub not installed")
        from skill_seekers.cli.github_scraper import GitHubScraper

        self.GitHubScraper = GitHubScraper

    def test_extract_issues_success(self):
        """Test successful issues extraction"""
        config = {
            "repo": "facebook/react",
            "name": "react",
            "github_token": None,
            "max_issues": 10,
        }

        # Create mock issues
        mock_label1 = Mock()
        mock_label1.name = "bug"
        mock_label2 = Mock()
        mock_label2.name = "high-priority"

        mock_milestone = Mock()
        mock_milestone.title = "v18.0"

        mock_issue1 = Mock()
        mock_issue1.number = 123
        mock_issue1.title = "Bug in useState"
        mock_issue1.state = "open"
        mock_issue1.labels = [mock_label1, mock_label2]
        mock_issue1.milestone = mock_milestone
        mock_issue1.created_at = datetime(2023, 1, 1)
        mock_issue1.updated_at = datetime(2023, 1, 2)
        mock_issue1.closed_at = None
        mock_issue1.html_url = "https://github.com/facebook/react/issues/123"
        mock_issue1.body = "Issue description"
        mock_issue1.pull_request = None
        mock_issue1.get_comments.return_value = []

        mock_label3 = Mock()
        mock_label3.name = "enhancement"

        mock_issue2 = Mock()
        mock_issue2.number = 124
        mock_issue2.title = "Feature request"
        mock_issue2.state = "closed"
        mock_issue2.labels = [mock_label3]
        mock_issue2.milestone = None
        mock_issue2.created_at = datetime(2023, 1, 3)
        mock_issue2.updated_at = datetime(2023, 1, 4)
        mock_issue2.closed_at = datetime(2023, 1, 5)
        mock_issue2.html_url = "https://github.com/facebook/react/issues/124"
        mock_issue2.body = "Feature description"
        mock_issue2.pull_request = None
        mock_issue2.get_comments.return_value = []

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_issues.return_value = [mock_issue1, mock_issue2]

            scraper._extract_issues()

            self.assertIn("issues", scraper.extracted_data)
            issues = scraper.extracted_data["issues"]
            self.assertEqual(len(issues), 2)

            # Check first issue
            self.assertEqual(issues[0]["number"], 123)
            self.assertEqual(issues[0]["title"], "Bug in useState")
            self.assertEqual(issues[0]["state"], "open")
            self.assertEqual(issues[0]["labels"], ["bug", "high-priority"])
            self.assertEqual(issues[0]["milestone"], "v18.0")

            # Check second issue
            self.assertEqual(issues[1]["number"], 124)
            self.assertEqual(issues[1]["state"], "closed")
            self.assertIsNone(issues[1]["milestone"])

    def test_extract_issues_filters_pull_requests(self):
        """Test that pull requests are filtered out from issues"""
        config = {
            "repo": "facebook/react",
            "name": "react",
            "github_token": None,
            "max_issues": 10,
        }

        # Create mock issue (need all required attributes)
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.title = "Real issue"
        mock_issue.state = "open"
        mock_issue.labels = []
        mock_issue.milestone = None
        mock_issue.created_at = datetime(2023, 1, 1)
        mock_issue.updated_at = datetime(2023, 1, 2)
        mock_issue.closed_at = None
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.body = "Issue body"
        mock_issue.pull_request = None
        mock_issue.get_comments.return_value = []

        mock_pr = Mock()
        mock_pr.number = 124
        mock_pr.title = "Pull request"
        mock_pr.pull_request = Mock()  # Has pull_request attribute

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_issues.return_value = [mock_issue, mock_pr]

            scraper._extract_issues()

            issues = scraper.extracted_data["issues"]
            # Should only have the real issue, not the PR
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0]["number"], 123)

    def test_extract_issues_respects_max_limit(self):
        """Test that max_issues limit is respected"""
        config = {
            "repo": "facebook/react",
            "name": "react",
            "github_token": None,
            "max_issues": 2,
        }

        # Create 5 mock issues
        mock_issues = []
        for i in range(5):
            mock_issue = Mock()
            mock_issue.number = i
            mock_issue.title = f"Issue {i}"
            mock_issue.state = "open"
            mock_issue.labels = []
            mock_issue.milestone = None
            mock_issue.created_at = datetime(2023, 1, 1)
            mock_issue.updated_at = datetime(2023, 1, 2)
            mock_issue.closed_at = None
            mock_issue.html_url = f"https://github.com/test/repo/issues/{i}"
            mock_issue.body = None
            mock_issue.pull_request = None
            mock_issue.get_comments.return_value = []
            mock_issues.append(mock_issue)

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_issues.return_value = mock_issues

            scraper._extract_issues()

            issues = scraper.extracted_data["issues"]
            # Should only extract first 2 issues
            self.assertEqual(len(issues), 2)


class TestChangelogExtraction(unittest.TestCase):
    """Test CHANGELOG extraction (C1.8)"""

    def setUp(self):
        if not PYGITHUB_AVAILABLE:
            self.skipTest("PyGithub not installed")
        from skill_seekers.cli.github_scraper import GitHubScraper

        self.GitHubScraper = GitHubScraper

    def test_extract_changelog_success(self):
        """Test successful CHANGELOG extraction"""
        config = {"repo": "facebook/react", "name": "react", "github_token": None}

        mock_content = Mock()
        mock_content.decoded_content = b"# Changelog\n\n## v1.0.0\n- Initial release"

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_contents.return_value = mock_content

            scraper._extract_changelog()

            self.assertIn("changelog", scraper.extracted_data)
            self.assertIn("Initial release", scraper.extracted_data["changelog"])

    def test_extract_changelog_tries_multiple_locations(self):
        """Test that CHANGELOG extraction tries multiple file locations"""
        config = {"repo": "facebook/react", "name": "react", "github_token": None}

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()

            # Make first attempts fail
            call_count = {"count": 0}

            def side_effect(path):
                call_count["count"] += 1
                if path in ["CHANGELOG.md", "CHANGES.md"]:
                    raise GithubException(404, "Not found")
                mock_content = Mock()
                mock_content.decoded_content = b"# History"
                return mock_content

            scraper.repo.get_contents.side_effect = side_effect

            scraper._extract_changelog()

            # Should have tried multiple paths
            self.assertGreaterEqual(call_count["count"], 1)

    def test_extract_changelog_not_found(self):
        """Test CHANGELOG extraction when no changelog exists"""
        config = {"repo": "test/norepo", "name": "norepo", "github_token": None}

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_contents.side_effect = GithubException(404, "Not found")

            scraper._extract_changelog()

            # Should not crash, just log warning (changelog initialized as empty string)
            self.assertEqual(scraper.extracted_data["changelog"], "")


class TestReleasesExtraction(unittest.TestCase):
    """Test GitHub Releases extraction (C1.9)"""

    def setUp(self):
        if not PYGITHUB_AVAILABLE:
            self.skipTest("PyGithub not installed")
        from skill_seekers.cli.github_scraper import GitHubScraper

        self.GitHubScraper = GitHubScraper

    def test_extract_releases_success(self):
        """Test successful releases extraction"""
        config = {"repo": "facebook/react", "name": "react", "github_token": None}

        # Create mock releases
        mock_release1 = Mock()
        mock_release1.tag_name = "v18.0.0"
        mock_release1.title = "React 18.0.0"
        mock_release1.body = "New features:\n- Concurrent rendering"
        mock_release1.draft = False
        mock_release1.prerelease = False
        mock_release1.created_at = datetime(2023, 3, 1)
        mock_release1.published_at = datetime(2023, 3, 1)
        mock_release1.html_url = "https://github.com/facebook/react/releases/tag/v18.0.0"
        mock_release1.tarball_url = "https://github.com/facebook/react/archive/v18.0.0.tar.gz"
        mock_release1.zipball_url = "https://github.com/facebook/react/archive/v18.0.0.zip"

        mock_release2 = Mock()
        mock_release2.tag_name = "v18.0.0-rc.0"
        mock_release2.title = "React 18.0.0 RC"
        mock_release2.body = "Release candidate"
        mock_release2.draft = False
        mock_release2.prerelease = True
        mock_release2.created_at = datetime(2023, 2, 1)
        mock_release2.published_at = datetime(2023, 2, 1)
        mock_release2.html_url = "https://github.com/facebook/react/releases/tag/v18.0.0-rc.0"
        mock_release2.tarball_url = "https://github.com/facebook/react/archive/v18.0.0-rc.0.tar.gz"
        mock_release2.zipball_url = "https://github.com/facebook/react/archive/v18.0.0-rc.0.zip"

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_releases.return_value = [mock_release1, mock_release2]

            scraper._extract_releases()

            self.assertIn("releases", scraper.extracted_data)
            releases = scraper.extracted_data["releases"]
            self.assertEqual(len(releases), 2)

            # Check first release
            self.assertEqual(releases[0]["tag_name"], "v18.0.0")
            self.assertEqual(releases[0]["name"], "React 18.0.0")
            self.assertFalse(releases[0]["draft"])
            self.assertFalse(releases[0]["prerelease"])
            self.assertIn("Concurrent rendering", releases[0]["body"])

            # Check second release (prerelease)
            self.assertEqual(releases[1]["tag_name"], "v18.0.0-rc.0")
            self.assertTrue(releases[1]["prerelease"])

    def test_extract_releases_empty(self):
        """Test releases extraction with no releases"""
        config = {"repo": "test/norepo", "name": "norepo", "github_token": None}

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_releases.return_value = []

            scraper._extract_releases()

            self.assertIn("releases", scraper.extracted_data)
            self.assertEqual(scraper.extracted_data["releases"], [])


class TestGitHubToSkillConverter(unittest.TestCase):
    """Test GitHubToSkillConverter and skill building (C1.10)"""

    def setUp(self):
        if not PYGITHUB_AVAILABLE:
            self.skipTest("PyGithub not installed")
        from skill_seekers.cli.github_scraper import GitHubToSkillConverter

        self.GitHubToSkillConverter = GitHubToSkillConverter

        # Create temporary directory for test output
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir)

        # Create mock data file
        self.data_file = self.output_dir / "test_github_data.json"
        self.mock_data = {
            "repo_info": {
                "name": "react",
                "full_name": "facebook/react",
                "description": "A JavaScript library",
                "stars": 200000,
                "language": "JavaScript",
            },
            "readme": "# React\n\nA JavaScript library for building user interfaces.",
            "languages": {
                "JavaScript": {"bytes": 8000, "percentage": 80.0},
                "TypeScript": {"bytes": 2000, "percentage": 20.0},
            },
            "issues": [
                {
                    "number": 123,
                    "title": "Bug in useState",
                    "state": "open",
                    "labels": ["bug"],
                    "milestone": "v18.0",
                    "created_at": "2023-01-01T10:00:00",
                    "updated_at": "2023-01-02T10:00:00",
                    "closed_at": None,
                    "url": "https://github.com/facebook/react/issues/123",
                    "body": "Issue description",
                }
            ],
            "changelog": "# Changelog\n\n## v18.0.0\n- New features",
            "releases": [
                {
                    "tag_name": "v18.0.0",
                    "name": "React 18.0.0",
                    "body": "Release notes",
                    "published_at": "2023-03-01T10:00:00",
                    "prerelease": False,
                    "draft": False,
                    "url": "https://github.com/facebook/react/releases/tag/v18.0.0",
                }
            ],
        }

        with open(self.data_file, "w") as f:
            json.dump(self.mock_data, f)

    def tearDown(self):
        # Clean up temporary directory
        if hasattr(self, "temp_dir"):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_loads_data(self):
        """Test that converter loads data file on initialization"""
        config = {"repo": "facebook/react", "name": "test", "description": "Test skill"}

        # Override data file path
        with patch("skill_seekers.cli.github_scraper.GitHubToSkillConverter.__init__") as mock_init:
            mock_init.return_value = None
            converter = self.GitHubToSkillConverter(config)
            converter.data_file = str(self.data_file)
            converter.data = converter._load_data()

            self.assertIn("repo_info", converter.data)
            self.assertEqual(converter.data["repo_info"]["name"], "react")

    def test_build_skill_creates_directory_structure(self):
        """Test that build_skill creates proper directory structure"""
        # Create data file in expected location
        data_file_path = self.output_dir / "test_github_data.json"
        with open(data_file_path, "w") as f:
            json.dump(self.mock_data, f)

        config = {"repo": "facebook/react", "name": "test", "description": "Test skill"}

        # Patch the paths to use our temp directory
        with patch(
            "skill_seekers.cli.github_scraper.GitHubToSkillConverter._load_data"
        ) as mock_load:
            mock_load.return_value = self.mock_data
            converter = self.GitHubToSkillConverter(config)
            converter.skill_dir = str(self.output_dir / "test_skill")
            converter.data = self.mock_data

            converter.build_skill()

            skill_dir = Path(converter.skill_dir)
            self.assertTrue(skill_dir.exists())
            self.assertTrue((skill_dir / "SKILL.md").exists())
            self.assertTrue((skill_dir / "references").exists())


class TestSymlinkHandling(unittest.TestCase):
    """Test symlink handling (Issue #225)"""

    def setUp(self):
        if not PYGITHUB_AVAILABLE:
            self.skipTest("PyGithub not installed")
        from skill_seekers.cli.github_scraper import GitHubScraper

        self.GitHubScraper = GitHubScraper

    def test_get_file_content_regular_file(self):
        """Test _get_file_content with regular file"""
        config = {"repo": "facebook/react", "name": "react", "github_token": None}

        # Create mock regular file
        mock_content = Mock()
        mock_content.type = "file"
        mock_content.encoding = "base64"
        mock_content.decoded_content = b"# React\n\nA JavaScript library"

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_contents.return_value = mock_content

            result = scraper._get_file_content("README.md")

            self.assertEqual(result, "# React\n\nA JavaScript library")
            scraper.repo.get_contents.assert_called_once_with("README.md")

    def test_get_file_content_symlink(self):
        """Test _get_file_content with symlink file"""
        config = {"repo": "vercel/ai", "name": "ai", "github_token": None}

        # Create mock symlink
        mock_symlink = Mock()
        mock_symlink.type = "symlink"
        mock_symlink.encoding = None
        mock_symlink.target = "packages/ai/README.md"

        # Create mock target file
        mock_target = Mock()
        mock_target.type = "file"
        mock_target.encoding = "base64"
        mock_target.decoded_content = b"# AI SDK\n\nReal content from symlink target"

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()

            # First call returns symlink, second call returns target
            scraper.repo.get_contents.side_effect = [mock_symlink, mock_target]

            result = scraper._get_file_content("README.md")

            self.assertEqual(result, "# AI SDK\n\nReal content from symlink target")
            # Should have called get_contents twice: once for symlink, once for target
            self.assertEqual(scraper.repo.get_contents.call_count, 2)
            scraper.repo.get_contents.assert_any_call("README.md")
            scraper.repo.get_contents.assert_any_call("packages/ai/README.md")

    def test_get_file_content_broken_symlink(self):
        """Test _get_file_content with broken symlink"""
        config = {"repo": "test/repo", "name": "test", "github_token": None}

        # Create mock symlink with broken target
        mock_symlink = Mock()
        mock_symlink.type = "symlink"
        mock_symlink.encoding = None
        mock_symlink.target = "nonexistent/file.md"

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()

            # First call returns symlink, second call raises 404
            scraper.repo.get_contents.side_effect = [
                mock_symlink,
                GithubException(404, "Not found"),
            ]

            result = scraper._get_file_content("README.md")

            # Should return None gracefully
            self.assertIsNone(result)

    def test_get_file_content_symlink_no_target(self):
        """Test _get_file_content with symlink that has no target attribute"""
        config = {"repo": "test/repo", "name": "test", "github_token": None}

        # Create mock symlink without target
        mock_symlink = Mock()
        mock_symlink.type = "symlink"
        mock_symlink.encoding = None
        mock_symlink.target = None

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_contents.return_value = mock_symlink

            result = scraper._get_file_content("README.md")

            # Should return None gracefully
            self.assertIsNone(result)

    def test_extract_readme_with_symlink(self):
        """Test README extraction with symlinked README.md (Integration test for Issue #225)"""
        config = {"repo": "vercel/ai", "name": "ai", "github_token": None}

        # Create mock symlink
        mock_symlink = Mock()
        mock_symlink.type = "symlink"
        mock_symlink.encoding = None
        mock_symlink.target = "packages/ai/README.md"

        # Create mock target file
        mock_target = Mock()
        mock_target.type = "file"
        mock_target.encoding = "base64"
        mock_target.decoded_content = b"# AI SDK\n\nThe AI SDK is a TypeScript toolkit"

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_contents.side_effect = [mock_symlink, mock_target]

            scraper._extract_readme()

            # Should successfully extract README content
            self.assertIn("readme", scraper.extracted_data)
            self.assertEqual(
                scraper.extracted_data["readme"],
                "# AI SDK\n\nThe AI SDK is a TypeScript toolkit",
            )

    def test_extract_changelog_with_symlink(self):
        """Test CHANGELOG extraction with symlinked CHANGELOG.md"""
        config = {"repo": "test/repo", "name": "test", "github_token": None}

        # Create mock symlink
        mock_symlink = Mock()
        mock_symlink.type = "symlink"
        mock_symlink.encoding = None
        mock_symlink.target = "docs/CHANGELOG.md"

        # Create mock target file
        mock_target = Mock()
        mock_target.type = "file"
        mock_target.encoding = "base64"
        mock_target.decoded_content = b"# Changelog\n\n## v1.0.0\n- Initial release"

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_contents.side_effect = [mock_symlink, mock_target]

            scraper._extract_changelog()

            # Should successfully extract CHANGELOG content
            self.assertIn("changelog", scraper.extracted_data)
            self.assertIn("Initial release", scraper.extracted_data["changelog"])

    def test_get_file_content_encoding_error(self):
        """Test _get_file_content handles encoding errors gracefully"""
        config = {"repo": "test/repo", "name": "test", "github_token": None}

        # Create mock file with invalid UTF-8 content
        mock_content = Mock()
        mock_content.type = "file"
        mock_content.encoding = "base64"
        # Mock decoded_content that can't be decoded as UTF-8
        mock_content.decoded_content = b"\xff\xfe Invalid UTF-8"

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_contents.return_value = mock_content

            # Should try latin-1 fallback
            result = scraper._get_file_content("README.md")

            # Should not crash (will try latin-1 fallback)
            self.assertIsNotNone(result)

    def test_get_file_content_large_file(self):
        """Test _get_file_content handles large files with encoding='none' (Issue #219)"""
        config = {"repo": "ccxt/ccxt", "name": "ccxt", "github_token": None}

        # Create mock large file (encoding="none")
        mock_content = Mock()
        mock_content.type = "file"
        mock_content.encoding = "none"  # Large files have encoding="none"
        mock_content.size = 1388271  # 1.4MB CHANGELOG
        mock_content.download_url = (
            "https://raw.githubusercontent.com/ccxt/ccxt/master/CHANGELOG.md"
        )

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_contents.return_value = mock_content

            # Mock requests.get
            with patch("requests.get") as mock_requests:
                mock_response = Mock()
                mock_response.text = "# Changelog\n\n## v1.0.0\n- Initial release"
                mock_response.raise_for_status = Mock()
                mock_requests.return_value = mock_response

                result = scraper._get_file_content("CHANGELOG.md")

                # Should download via download_url
                self.assertEqual(result, "# Changelog\n\n## v1.0.0\n- Initial release")
                mock_requests.assert_called_once_with(
                    "https://raw.githubusercontent.com/ccxt/ccxt/master/CHANGELOG.md",
                    timeout=30,
                )

    def test_extract_changelog_large_file(self):
        """Test CHANGELOG extraction with large file (Integration test for Issue #219)"""
        config = {"repo": "ccxt/ccxt", "name": "ccxt", "github_token": None}

        # Create mock large CHANGELOG
        mock_content = Mock()
        mock_content.type = "file"
        mock_content.encoding = "none"
        mock_content.size = 1388271
        mock_content.download_url = (
            "https://raw.githubusercontent.com/ccxt/ccxt/master/CHANGELOG.md"
        )

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_contents.return_value = mock_content

            # Mock requests.get
            with patch("requests.get") as mock_requests:
                mock_response = Mock()
                mock_response.text = "# CCXT Changelog\n\n## v4.0.0\n- Major update"
                mock_response.raise_for_status = Mock()
                mock_requests.return_value = mock_response

                scraper._extract_changelog()

                # Should successfully extract CHANGELOG content
                self.assertIn("changelog", scraper.extracted_data)
                self.assertIn("Major update", scraper.extracted_data["changelog"])


class TestGitignoreSupport(unittest.TestCase):
    """Test .gitignore support in github_scraper (C2.1)"""

    def setUp(self):
        """Set up test environment"""
        if not PYGITHUB_AVAILABLE:
            self.skipTest("PyGithub not installed")
        from skill_seekers.cli.github_scraper import GitHubScraper

        self.GitHubScraper = GitHubScraper

        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_gitignore_exists(self):
        """Test loading existing .gitignore file."""
        # Create .gitignore
        gitignore_path = self.repo_path / ".gitignore"
        gitignore_path.write_text("*.log\ntemp/\n__pycache__/")

        config = {"repo": "test/repo", "local_repo_path": str(self.repo_path)}

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)

            # Should load .gitignore if pathspec available
            if hasattr(scraper, "gitignore_spec"):
                # pathspec is installed
                self.assertIsNotNone(scraper.gitignore_spec)
            else:
                # pathspec not installed
                self.assertIsNone(scraper.gitignore_spec)

    def test_load_gitignore_missing(self):
        """Test behavior when no .gitignore exists."""
        config = {"repo": "test/repo", "local_repo_path": str(self.repo_path)}

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)

            # Should be None when no .gitignore found
            self.assertIsNone(scraper.gitignore_spec)

    def test_should_exclude_dir_with_gitignore(self):
        """Test directory exclusion with .gitignore rules."""
        # Create .gitignore
        gitignore_path = self.repo_path / ".gitignore"
        gitignore_path.write_text("temp/\nbuild/\n*.egg-info")

        config = {"repo": "test/repo", "local_repo_path": str(self.repo_path)}

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)

            # Test .gitignore exclusion (if pathspec available)
            if scraper.gitignore_spec:
                self.assertTrue(scraper.should_exclude_dir("temp", "temp"))
                self.assertTrue(scraper.should_exclude_dir("build", "build"))

                # Non-excluded dir should pass
                self.assertFalse(scraper.should_exclude_dir("src", "src"))

    def test_should_exclude_dir_default_exclusions(self):
        """Test that default exclusions still work."""
        config = {"repo": "test/repo", "local_repo_path": str(self.repo_path)}

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)

            # Default exclusions should still work
            self.assertTrue(scraper.should_exclude_dir("node_modules"))
            self.assertTrue(scraper.should_exclude_dir("venv"))
            self.assertTrue(scraper.should_exclude_dir("__pycache__"))

            # Normal directories should not be excluded
            self.assertFalse(scraper.should_exclude_dir("src"))
            self.assertFalse(scraper.should_exclude_dir("tests"))


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""

    def setUp(self):
        if not PYGITHUB_AVAILABLE:
            self.skipTest("PyGithub not installed")
        from skill_seekers.cli.github_scraper import GitHubScraper

        self.GitHubScraper = GitHubScraper

    def test_invalid_repo_name(self):
        """Test handling of invalid repository name"""
        config = {"repo": "invalid_repo_format", "name": "test", "github_token": None}

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = None
            scraper.github.get_repo = Mock(side_effect=GithubException(404, "Not found"))

            # Should raise ValueError with helpful message
            with self.assertRaises(ValueError) as context:
                scraper._fetch_repository()

            self.assertIn("Repository not found", str(context.exception))

    def test_rate_limit_error(self):
        """Test handling of rate limit errors"""
        config = {
            "repo": "facebook/react",
            "name": "react",
            "github_token": None,
            "max_issues": 10,
        }

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_issues.side_effect = GithubException(403, "Rate limit exceeded")

            # Should handle gracefully and log warning
            scraper._extract_issues()
            # Should not crash, just log warning

    def test_extract_issues_passes_state_filter(self):
        """Test that _extract_issues passes issue_state to get_issues."""
        config = {
            "repo": "facebook/react",
            "name": "react",
            "github_token": None,
            "max_issues": 10,
            "issue_state": "open",
        }

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_issues.return_value = []

            scraper._extract_issues()

            call_kwargs = scraper.repo.get_issues.call_args[1]
            self.assertEqual(call_kwargs["state"], "open")

    def test_extract_issues_passes_labels_filter(self):
        """Test that _extract_issues passes issue_labels to get_issues."""
        config = {
            "repo": "facebook/react",
            "name": "react",
            "github_token": None,
            "max_issues": 10,
            "issue_labels": ["bug", "enhancement"],
        }

        mock_label_bug = Mock()
        mock_label_bug.name = "bug"
        mock_label_enh = Mock()
        mock_label_enh.name = "enhancement"

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_label.side_effect = [mock_label_bug, mock_label_enh]
            scraper.repo.get_issues.return_value = []

            scraper._extract_issues()

            # Verify get_label was called for each label
            self.assertEqual(scraper.repo.get_label.call_count, 2)
            scraper.repo.get_label.assert_any_call("bug")
            scraper.repo.get_label.assert_any_call("enhancement")
            # Verify labels were passed to get_issues
            call_kwargs = scraper.repo.get_issues.call_args[1]
            self.assertIn("labels", call_kwargs)

    def test_extract_issues_passes_since_filter(self):
        """Test that _extract_issues passes issue_since to get_issues."""
        config = {
            "repo": "facebook/react",
            "name": "react",
            "github_token": None,
            "max_issues": 10,
            "issue_since": "2026-01-01",
        }

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_issues.return_value = []

            scraper._extract_issues()

            call_kwargs = scraper.repo.get_issues.call_args[1]
            self.assertIn("since", call_kwargs)
            self.assertEqual(call_kwargs["since"], datetime.fromisoformat("2026-01-01"))

    def test_extract_issues_no_filters_by_default(self):
        """Test that _extract_issues uses defaults when no filters set."""
        config = {
            "repo": "facebook/react",
            "name": "react",
            "github_token": None,
            "max_issues": 10,
        }

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_issues.return_value = []

            scraper._extract_issues()

            call_kwargs = scraper.repo.get_issues.call_args[1]
            self.assertEqual(call_kwargs["state"], "all")
            self.assertNotIn("labels", call_kwargs)
            self.assertNotIn("since", call_kwargs)

    def test_issue_filter_args_in_config(self):
        """Test that issue filter config keys are read in __init__."""
        config = {
            "repo": "facebook/react",
            "name": "react",
            "github_token": None,
            "issue_since": "2026-03-01",
            "issue_labels": ["bug"],
            "issue_state": "closed",
        }

        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            self.assertEqual(scraper.issue_since, "2026-03-01")
            self.assertEqual(scraper.issue_labels, ["bug"])
            self.assertEqual(scraper.issue_state, "closed")


class TestExtractIssuesFullBodyAndComments(unittest.TestCase):
    """Test full issue body and comment fetching."""

    def setUp(self):
        if not PYGITHUB_AVAILABLE:
            self.skipTest("PyGithub not installed")
        from skill_seekers.cli.github_scraper import GitHubScraper

        self.GitHubScraper = GitHubScraper

    def _make_mock_issue(self, number=1, body="Full body text here", comments=None):
        """Helper to create a mock issue with comments."""
        mock_issue = Mock()
        mock_issue.number = number
        mock_issue.title = f"Issue {number}"
        mock_issue.state = "open"
        mock_issue.labels = []
        mock_issue.milestone = None
        mock_issue.created_at = datetime(2023, 1, 1)
        mock_issue.updated_at = datetime(2023, 1, 2)
        mock_issue.closed_at = None
        mock_issue.html_url = f"https://github.com/test/repo/issues/{number}"
        mock_issue.body = body
        mock_issue.pull_request = None
        mock_issue.get_comments.return_value = comments or []
        return mock_issue

    def _make_mock_comment(self, author="alice", body="Comment body", date=None):
        """Helper to create a mock comment."""
        comment = Mock()
        comment.user = Mock()
        comment.user.login = author
        comment.created_at = date or datetime(2023, 2, 1)
        comment.body = body
        return comment

    def test_body_truncated_by_default(self):
        """Issue body is truncated to 500 chars by default."""
        long_body = "x" * 2000
        mock_issue = self._make_mock_issue(body=long_body)

        config = {"repo": "test/repo", "name": "repo", "github_token": None, "max_issues": 10}
        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_issues.return_value = [mock_issue]

            scraper._extract_issues()

            issues = scraper.extracted_data["issues"]
            self.assertEqual(len(issues[0]["body"]), 500)

    def test_full_body_with_per_issue_files(self):
        """Issue body is stored in full when per_issue_files is enabled."""
        long_body = "x" * 2000
        mock_issue = self._make_mock_issue(body=long_body)

        config = {
            "repo": "test/repo",
            "name": "repo",
            "github_token": None,
            "max_issues": 10,
            "per_issue_files": True,
        }
        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_issues.return_value = [mock_issue]

            scraper._extract_issues()

            issues = scraper.extracted_data["issues"]
            self.assertEqual(len(issues[0]["body"]), 2000)

    def test_comments_not_fetched_by_default(self):
        """Comments are NOT fetched when max_comments is 0 (default)."""
        comment1 = self._make_mock_comment(author="alice", body="First comment")
        mock_issue = self._make_mock_issue(comments=[comment1])

        config = {"repo": "test/repo", "name": "repo", "github_token": None, "max_issues": 10}
        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_issues.return_value = [mock_issue]

            scraper._extract_issues()

            issues = scraper.extracted_data["issues"]
            self.assertEqual(len(issues[0]["comments"]), 0)

    def test_comments_fetched(self):
        """Comments are fetched when max_comments > 0."""
        comment1 = self._make_mock_comment(author="alice", body="First comment")
        comment2 = self._make_mock_comment(author="bob", body="Second comment")
        mock_issue = self._make_mock_issue(comments=[comment1, comment2])

        config = {
            "repo": "test/repo",
            "name": "repo",
            "github_token": None,
            "max_issues": 10,
            "max_comments": 50,
        }
        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_issues.return_value = [mock_issue]

            scraper._extract_issues()

            issues = scraper.extracted_data["issues"]
            self.assertEqual(len(issues[0]["comments"]), 2)
            self.assertEqual(issues[0]["comments"][0]["author"], "alice")
            self.assertEqual(issues[0]["comments"][0]["body"], "First comment")
            self.assertEqual(issues[0]["comments"][1]["author"], "bob")

    def test_max_comments_respected(self):
        """Only max_comments comments are stored per issue."""
        comments = [self._make_mock_comment(author=f"user{i}") for i in range(10)]
        mock_issue = self._make_mock_issue(comments=comments)

        config = {
            "repo": "test/repo",
            "name": "repo",
            "github_token": None,
            "max_issues": 10,
            "max_comments": 3,
        }
        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            scraper.repo = Mock()
            scraper.repo.get_issues.return_value = [mock_issue]

            scraper._extract_issues()

            issues = scraper.extracted_data["issues"]
            self.assertEqual(len(issues[0]["comments"]), 3)

    def test_max_comments_config_default(self):
        """max_comments defaults to 0 (disabled) in config."""
        config = {"repo": "test/repo", "name": "repo", "github_token": None}
        with patch("skill_seekers.cli.github_scraper.Github"):
            scraper = self.GitHubScraper(config)
            self.assertEqual(scraper.max_comments, 0)


class TestPerIssueFileGeneration(unittest.TestCase):
    """Test per-issue markdown file generation."""

    def setUp(self):
        if not PYGITHUB_AVAILABLE:
            self.skipTest("PyGithub not installed")
        from skill_seekers.cli.github_scraper import GitHubToSkillConverter

        self.GitHubToSkillConverter = GitHubToSkillConverter
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if hasattr(self, "temp_dir"):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setup_converter(self, issues):
        """Create a converter with pre-built data."""
        name = "test-repo"
        data_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(data_dir, exist_ok=True)

        # Write extracted data
        data = {
            "readme": "# Test Repo",
            "issues": issues,
            "releases": [],
            "file_tree": [],
        }
        data_file = os.path.join(data_dir, f"{name}_github_data.json")
        with open(data_file, "w") as f:
            json.dump(data, f)

        config = {"repo": "test/test-repo", "name": name, "per_issue_files": True}

        # Patch the data file path
        with patch.object(
            self.GitHubToSkillConverter,
            "_load_data",
            return_value=data,
        ):
            converter = self.GitHubToSkillConverter(config)

        converter.data = data
        converter.skill_dir = os.path.join(data_dir, name)
        os.makedirs(os.path.join(converter.skill_dir, "references"), exist_ok=True)
        return converter

    def test_per_issue_files_created(self):
        """Per-issue files are created with correct naming."""
        issues = [
            {
                "number": 42,
                "title": "Bug report",
                "state": "open",
                "labels": ["bug"],
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-02T00:00:00",
                "closed_at": None,
                "url": "https://github.com/test/test-repo/issues/42",
                "body": "Full bug description here",
                "comments": [],
            },
        ]
        converter = self._setup_converter(issues)
        converter._generate_issues_reference()

        expected_file = os.path.join(converter.skill_dir, "references", "test-repo_42.md")
        self.assertTrue(os.path.exists(expected_file))

    def test_per_issue_file_content(self):
        """Per-issue file contains full body and YAML frontmatter."""
        issues = [
            {
                "number": 99,
                "title": "Feature request",
                "state": "open",
                "labels": ["enhancement"],
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-02T00:00:00",
                "closed_at": None,
                "url": "https://github.com/test/repo/issues/99",
                "body": "Please add dark mode support",
                "comments": [],
            },
        ]
        converter = self._setup_converter(issues)
        converter._generate_issues_reference()

        filepath = os.path.join(converter.skill_dir, "references", "test-repo_99.md")
        content = Path(filepath).read_text()

        # Check YAML frontmatter
        self.assertTrue(content.startswith("---"))
        self.assertIn("type: github_issue", content)
        self.assertIn("issue_number: 99", content)
        self.assertIn("state: open", content)

        # Check body
        self.assertIn("Please add dark mode support", content)

    def test_per_issue_file_with_comments(self):
        """Per-issue file includes comments section."""
        issues = [
            {
                "number": 7,
                "title": "Question",
                "state": "open",
                "labels": [],
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-02T00:00:00",
                "closed_at": None,
                "url": "https://github.com/test/repo/issues/7",
                "body": "How do I configure X?",
                "comments": [
                    {
                        "author": "maintainer",
                        "created_at": "2023-01-03T00:00:00",
                        "body": "You can configure X by editing config.yaml",
                    },
                    {
                        "author": "user123",
                        "created_at": "2023-01-04T00:00:00",
                        "body": "Thanks, that worked!",
                    },
                ],
            },
        ]
        converter = self._setup_converter(issues)
        converter._generate_issues_reference()

        filepath = os.path.join(converter.skill_dir, "references", "test-repo_7.md")
        content = Path(filepath).read_text()

        self.assertIn("## Comments (2)", content)
        self.assertIn("### maintainer", content)
        self.assertIn("You can configure X by editing config.yaml", content)
        self.assertIn("### user123", content)
        self.assertIn("Thanks, that worked!", content)

    def test_summary_file_still_generated(self):
        """issues.md summary file is still generated alongside per-issue files."""
        issues = [
            {
                "number": 1,
                "title": "Test",
                "state": "open",
                "labels": [],
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-02T00:00:00",
                "closed_at": None,
                "url": "https://github.com/test/repo/issues/1",
                "body": "Test body",
                "comments": [],
            },
        ]
        converter = self._setup_converter(issues)
        converter._generate_issues_reference()

        summary_file = os.path.join(converter.skill_dir, "references", "issues.md")
        self.assertTrue(os.path.exists(summary_file))


if __name__ == "__main__":
    unittest.main()
