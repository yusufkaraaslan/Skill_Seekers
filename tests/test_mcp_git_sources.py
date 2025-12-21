#!/usr/bin/env python3
"""
MCP Integration Tests for Git Config Sources
Tests the complete MCP tool workflow for git-based config fetching
"""

import json
import pytest
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, Mock

# Test if MCP is available
try:
    import mcp
    from mcp.types import TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    TextContent = None  # Define placeholder


@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directories for testing."""
    config_dir = tmp_path / "config"
    cache_dir = tmp_path / "cache"
    dest_dir = tmp_path / "dest"

    config_dir.mkdir()
    cache_dir.mkdir()
    dest_dir.mkdir()

    return {
        "config": config_dir,
        "cache": cache_dir,
        "dest": dest_dir
    }


@pytest.fixture
def mock_git_repo(temp_dirs):
    """Create a mock git repository with config files."""
    repo_path = temp_dirs["cache"] / "test-source"
    repo_path.mkdir()
    (repo_path / ".git").mkdir()

    # Create sample config files
    react_config = {
        "name": "react",
        "description": "React framework",
        "base_url": "https://react.dev/"
    }
    (repo_path / "react.json").write_text(json.dumps(react_config, indent=2))

    vue_config = {
        "name": "vue",
        "description": "Vue framework",
        "base_url": "https://vuejs.org/"
    }
    (repo_path / "vue.json").write_text(json.dumps(vue_config, indent=2))

    return repo_path


@pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP not available")
@pytest.mark.asyncio
class TestFetchConfigModes:
    """Test fetch_config tool with different modes."""

    async def test_fetch_config_api_mode_list(self):
        """Test API mode - listing available configs."""
        from skill_seekers.mcp.server import fetch_config_tool

        with patch('skill_seekers.mcp.server.httpx.AsyncClient') as mock_client:
            # Mock API response
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "configs": [
                    {"name": "react", "category": "web-frameworks", "description": "React framework", "type": "single"},
                    {"name": "vue", "category": "web-frameworks", "description": "Vue framework", "type": "single"}
                ],
                "total": 2
            }
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            args = {"list_available": True}
            result = await fetch_config_tool(args)

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert "react" in result[0].text
            assert "vue" in result[0].text

    async def test_fetch_config_api_mode_download(self, temp_dirs):
        """Test API mode - downloading specific config."""
        from skill_seekers.mcp.server import fetch_config_tool

        with patch('skill_seekers.mcp.server.httpx.AsyncClient') as mock_client:
            # Mock API responses
            mock_detail_response = MagicMock()
            mock_detail_response.json.return_value = {
                "name": "react",
                "category": "web-frameworks",
                "description": "React framework"
            }

            mock_download_response = MagicMock()
            mock_download_response.json.return_value = {
                "name": "react",
                "base_url": "https://react.dev/"
            }

            mock_client_instance = mock_client.return_value.__aenter__.return_value
            mock_client_instance.get.side_effect = [mock_detail_response, mock_download_response]

            args = {
                "config_name": "react",
                "destination": str(temp_dirs["dest"])
            }
            result = await fetch_config_tool(args)

            assert len(result) == 1
            assert "✅" in result[0].text
            assert "react" in result[0].text

            # Verify file was created
            config_file = temp_dirs["dest"] / "react.json"
            assert config_file.exists()

    @patch('skill_seekers.mcp.server.GitConfigRepo')
    async def test_fetch_config_git_url_mode(self, mock_git_repo_class, temp_dirs):
        """Test Git URL mode - direct git clone."""
        from skill_seekers.mcp.server import fetch_config_tool

        # Mock GitConfigRepo
        mock_repo_instance = MagicMock()
        mock_repo_path = temp_dirs["cache"] / "temp_react"
        mock_repo_path.mkdir()

        # Create mock config file
        react_config = {"name": "react", "base_url": "https://react.dev/"}
        (mock_repo_path / "react.json").write_text(json.dumps(react_config))

        mock_repo_instance.clone_or_pull.return_value = mock_repo_path
        mock_repo_instance.get_config.return_value = react_config
        mock_git_repo_class.return_value = mock_repo_instance

        args = {
            "config_name": "react",
            "git_url": "https://github.com/myorg/configs.git",
            "destination": str(temp_dirs["dest"])
        }
        result = await fetch_config_tool(args)

        assert len(result) == 1
        assert "✅" in result[0].text
        assert "git URL" in result[0].text
        assert "react" in result[0].text

        # Verify clone was called
        mock_repo_instance.clone_or_pull.assert_called_once()

        # Verify file was created
        config_file = temp_dirs["dest"] / "react.json"
        assert config_file.exists()

    @patch('skill_seekers.mcp.server.GitConfigRepo')
    @patch('skill_seekers.mcp.server.SourceManager')
    async def test_fetch_config_source_mode(self, mock_source_manager_class, mock_git_repo_class, temp_dirs):
        """Test Source mode - using named source from registry."""
        from skill_seekers.mcp.server import fetch_config_tool

        # Mock SourceManager
        mock_source_manager = MagicMock()
        mock_source_manager.get_source.return_value = {
            "name": "team",
            "git_url": "https://github.com/myorg/configs.git",
            "branch": "main",
            "token_env": "GITHUB_TOKEN"
        }
        mock_source_manager_class.return_value = mock_source_manager

        # Mock GitConfigRepo
        mock_repo_instance = MagicMock()
        mock_repo_path = temp_dirs["cache"] / "team"
        mock_repo_path.mkdir()

        react_config = {"name": "react", "base_url": "https://react.dev/"}
        (mock_repo_path / "react.json").write_text(json.dumps(react_config))

        mock_repo_instance.clone_or_pull.return_value = mock_repo_path
        mock_repo_instance.get_config.return_value = react_config
        mock_git_repo_class.return_value = mock_repo_instance

        args = {
            "config_name": "react",
            "source": "team",
            "destination": str(temp_dirs["dest"])
        }
        result = await fetch_config_tool(args)

        assert len(result) == 1
        assert "✅" in result[0].text
        assert "git source" in result[0].text
        assert "team" in result[0].text

        # Verify source was retrieved
        mock_source_manager.get_source.assert_called_once_with("team")

        # Verify file was created
        config_file = temp_dirs["dest"] / "react.json"
        assert config_file.exists()

    async def test_fetch_config_source_not_found(self):
        """Test error when source doesn't exist."""
        from skill_seekers.mcp.server import fetch_config_tool

        with patch('skill_seekers.mcp.server.SourceManager') as mock_sm_class:
            mock_sm = MagicMock()
            mock_sm.get_source.side_effect = KeyError("Source 'nonexistent' not found")
            mock_sm_class.return_value = mock_sm

            args = {
                "config_name": "react",
                "source": "nonexistent"
            }
            result = await fetch_config_tool(args)

            assert len(result) == 1
            assert "❌" in result[0].text
            assert "not found" in result[0].text

    @patch('skill_seekers.mcp.server.GitConfigRepo')
    async def test_fetch_config_config_not_found_in_repo(self, mock_git_repo_class, temp_dirs):
        """Test error when config doesn't exist in repository."""
        from skill_seekers.mcp.server import fetch_config_tool

        # Mock GitConfigRepo
        mock_repo_instance = MagicMock()
        mock_repo_path = temp_dirs["cache"] / "temp_django"
        mock_repo_path.mkdir()

        mock_repo_instance.clone_or_pull.return_value = mock_repo_path
        mock_repo_instance.get_config.side_effect = FileNotFoundError(
            "Config 'django' not found in repository. Available configs: react, vue"
        )
        mock_git_repo_class.return_value = mock_repo_instance

        args = {
            "config_name": "django",
            "git_url": "https://github.com/myorg/configs.git"
        }
        result = await fetch_config_tool(args)

        assert len(result) == 1
        assert "❌" in result[0].text
        assert "not found" in result[0].text
        assert "Available configs" in result[0].text

    @patch('skill_seekers.mcp.server.GitConfigRepo')
    async def test_fetch_config_invalid_git_url(self, mock_git_repo_class):
        """Test error handling for invalid git URL."""
        from skill_seekers.mcp.server import fetch_config_tool

        # Mock GitConfigRepo to raise ValueError
        mock_repo_instance = MagicMock()
        mock_repo_instance.clone_or_pull.side_effect = ValueError("Invalid git URL: not-a-url")
        mock_git_repo_class.return_value = mock_repo_instance

        args = {
            "config_name": "react",
            "git_url": "not-a-url"
        }
        result = await fetch_config_tool(args)

        assert len(result) == 1
        assert "❌" in result[0].text
        assert "Invalid git URL" in result[0].text


@pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP not available")
@pytest.mark.asyncio
class TestSourceManagementTools:
    """Test add/list/remove config source tools."""

    async def test_add_config_source(self, temp_dirs):
        """Test adding a new config source."""
        from skill_seekers.mcp.server import add_config_source_tool

        with patch('skill_seekers.mcp.server.SourceManager') as mock_sm_class:
            mock_sm = MagicMock()
            mock_sm.add_source.return_value = {
                "name": "team",
                "git_url": "https://github.com/myorg/configs.git",
                "type": "github",
                "branch": "main",
                "token_env": "GITHUB_TOKEN",
                "priority": 100,
                "enabled": True,
                "added_at": "2025-12-21T10:00:00+00:00"
            }
            mock_sm_class.return_value = mock_sm

            args = {
                "name": "team",
                "git_url": "https://github.com/myorg/configs.git"
            }
            result = await add_config_source_tool(args)

            assert len(result) == 1
            assert "✅" in result[0].text
            assert "team" in result[0].text
            assert "registered" in result[0].text

            # Verify add_source was called
            mock_sm.add_source.assert_called_once()

    async def test_add_config_source_missing_name(self):
        """Test error when name is missing."""
        from skill_seekers.mcp.server import add_config_source_tool

        args = {"git_url": "https://github.com/myorg/configs.git"}
        result = await add_config_source_tool(args)

        assert len(result) == 1
        assert "❌" in result[0].text
        assert "name" in result[0].text.lower()
        assert "required" in result[0].text.lower()

    async def test_add_config_source_missing_git_url(self):
        """Test error when git_url is missing."""
        from skill_seekers.mcp.server import add_config_source_tool

        args = {"name": "team"}
        result = await add_config_source_tool(args)

        assert len(result) == 1
        assert "❌" in result[0].text
        assert "git_url" in result[0].text.lower()
        assert "required" in result[0].text.lower()

    async def test_add_config_source_invalid_name(self):
        """Test error when source name is invalid."""
        from skill_seekers.mcp.server import add_config_source_tool

        with patch('skill_seekers.mcp.server.SourceManager') as mock_sm_class:
            mock_sm = MagicMock()
            mock_sm.add_source.side_effect = ValueError(
                "Invalid source name 'team@company'. Must be alphanumeric with optional hyphens/underscores."
            )
            mock_sm_class.return_value = mock_sm

            args = {
                "name": "team@company",
                "git_url": "https://github.com/myorg/configs.git"
            }
            result = await add_config_source_tool(args)

            assert len(result) == 1
            assert "❌" in result[0].text
            assert "Validation Error" in result[0].text

    async def test_list_config_sources(self):
        """Test listing config sources."""
        from skill_seekers.mcp.server import list_config_sources_tool

        with patch('skill_seekers.mcp.server.SourceManager') as mock_sm_class:
            mock_sm = MagicMock()
            mock_sm.list_sources.return_value = [
                {
                    "name": "team",
                    "git_url": "https://github.com/myorg/configs.git",
                    "type": "github",
                    "branch": "main",
                    "token_env": "GITHUB_TOKEN",
                    "priority": 1,
                    "enabled": True,
                    "added_at": "2025-12-21T10:00:00+00:00"
                },
                {
                    "name": "company",
                    "git_url": "https://gitlab.company.com/configs.git",
                    "type": "gitlab",
                    "branch": "develop",
                    "token_env": "GITLAB_TOKEN",
                    "priority": 2,
                    "enabled": True,
                    "added_at": "2025-12-21T11:00:00+00:00"
                }
            ]
            mock_sm_class.return_value = mock_sm

            args = {}
            result = await list_config_sources_tool(args)

            assert len(result) == 1
            assert "📋" in result[0].text
            assert "team" in result[0].text
            assert "company" in result[0].text
            assert "2 total" in result[0].text

    async def test_list_config_sources_empty(self):
        """Test listing when no sources registered."""
        from skill_seekers.mcp.server import list_config_sources_tool

        with patch('skill_seekers.mcp.server.SourceManager') as mock_sm_class:
            mock_sm = MagicMock()
            mock_sm.list_sources.return_value = []
            mock_sm_class.return_value = mock_sm

            args = {}
            result = await list_config_sources_tool(args)

            assert len(result) == 1
            assert "No config sources registered" in result[0].text

    async def test_list_config_sources_enabled_only(self):
        """Test listing only enabled sources."""
        from skill_seekers.mcp.server import list_config_sources_tool

        with patch('skill_seekers.mcp.server.SourceManager') as mock_sm_class:
            mock_sm = MagicMock()
            mock_sm.list_sources.return_value = [
                {
                    "name": "team",
                    "git_url": "https://github.com/myorg/configs.git",
                    "type": "github",
                    "branch": "main",
                    "token_env": "GITHUB_TOKEN",
                    "priority": 1,
                    "enabled": True,
                    "added_at": "2025-12-21T10:00:00+00:00"
                }
            ]
            mock_sm_class.return_value = mock_sm

            args = {"enabled_only": True}
            result = await list_config_sources_tool(args)

            assert len(result) == 1
            assert "enabled only" in result[0].text

            # Verify list_sources was called with correct parameter
            mock_sm.list_sources.assert_called_once_with(enabled_only=True)

    async def test_remove_config_source(self):
        """Test removing a config source."""
        from skill_seekers.mcp.server import remove_config_source_tool

        with patch('skill_seekers.mcp.server.SourceManager') as mock_sm_class:
            mock_sm = MagicMock()
            mock_sm.remove_source.return_value = True
            mock_sm_class.return_value = mock_sm

            args = {"name": "team"}
            result = await remove_config_source_tool(args)

            assert len(result) == 1
            assert "✅" in result[0].text
            assert "removed" in result[0].text.lower()
            assert "team" in result[0].text

            # Verify remove_source was called
            mock_sm.remove_source.assert_called_once_with("team")

    async def test_remove_config_source_not_found(self):
        """Test removing non-existent source."""
        from skill_seekers.mcp.server import remove_config_source_tool

        with patch('skill_seekers.mcp.server.SourceManager') as mock_sm_class:
            mock_sm = MagicMock()
            mock_sm.remove_source.return_value = False
            mock_sm.list_sources.return_value = [
                {"name": "team", "git_url": "https://example.com/1.git"},
                {"name": "company", "git_url": "https://example.com/2.git"}
            ]
            mock_sm_class.return_value = mock_sm

            args = {"name": "nonexistent"}
            result = await remove_config_source_tool(args)

            assert len(result) == 1
            assert "❌" in result[0].text
            assert "not found" in result[0].text
            assert "Available sources" in result[0].text

    async def test_remove_config_source_missing_name(self):
        """Test error when name is missing."""
        from skill_seekers.mcp.server import remove_config_source_tool

        args = {}
        result = await remove_config_source_tool(args)

        assert len(result) == 1
        assert "❌" in result[0].text
        assert "name" in result[0].text.lower()
        assert "required" in result[0].text.lower()


@pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP not available")
@pytest.mark.asyncio
class TestCompleteWorkflow:
    """Test complete workflow of add → fetch → remove."""

    @patch('skill_seekers.mcp.server.GitConfigRepo')
    @patch('skill_seekers.mcp.server.SourceManager')
    async def test_add_fetch_remove_workflow(self, mock_sm_class, mock_git_repo_class, temp_dirs):
        """Test complete workflow: add source → fetch config → remove source."""
        from skill_seekers.mcp.server import (
            add_config_source_tool,
            fetch_config_tool,
            list_config_sources_tool,
            remove_config_source_tool
        )

        # Step 1: Add source
        mock_sm = MagicMock()
        mock_sm.add_source.return_value = {
            "name": "team",
            "git_url": "https://github.com/myorg/configs.git",
            "type": "github",
            "branch": "main",
            "token_env": "GITHUB_TOKEN",
            "priority": 100,
            "enabled": True,
            "added_at": "2025-12-21T10:00:00+00:00"
        }
        mock_sm_class.return_value = mock_sm

        add_result = await add_config_source_tool({
            "name": "team",
            "git_url": "https://github.com/myorg/configs.git"
        })
        assert "✅" in add_result[0].text

        # Step 2: Fetch config from source
        mock_sm.get_source.return_value = {
            "name": "team",
            "git_url": "https://github.com/myorg/configs.git",
            "branch": "main",
            "token_env": "GITHUB_TOKEN"
        }

        mock_repo = MagicMock()
        mock_repo_path = temp_dirs["cache"] / "team"
        mock_repo_path.mkdir()

        react_config = {"name": "react", "base_url": "https://react.dev/"}
        (mock_repo_path / "react.json").write_text(json.dumps(react_config))

        mock_repo.clone_or_pull.return_value = mock_repo_path
        mock_repo.get_config.return_value = react_config
        mock_git_repo_class.return_value = mock_repo

        fetch_result = await fetch_config_tool({
            "config_name": "react",
            "source": "team",
            "destination": str(temp_dirs["dest"])
        })
        assert "✅" in fetch_result[0].text

        # Verify config file created
        assert (temp_dirs["dest"] / "react.json").exists()

        # Step 3: List sources
        mock_sm.list_sources.return_value = [{
            "name": "team",
            "git_url": "https://github.com/myorg/configs.git",
            "type": "github",
            "branch": "main",
            "token_env": "GITHUB_TOKEN",
            "priority": 100,
            "enabled": True,
            "added_at": "2025-12-21T10:00:00+00:00"
        }]

        list_result = await list_config_sources_tool({})
        assert "team" in list_result[0].text

        # Step 4: Remove source
        mock_sm.remove_source.return_value = True

        remove_result = await remove_config_source_tool({"name": "team"})
        assert "✅" in remove_result[0].text
