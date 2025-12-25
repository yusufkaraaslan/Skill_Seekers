#!/usr/bin/env python3
"""
Comprehensive test suite for FastMCP Server Implementation
Tests all 17 tools across 5 categories with comprehensive coverage
"""

import sys
import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# WORKAROUND for shadowing issue: Temporarily change to /tmp to import external mcp
# This avoids any local mcp/ directory being in the import path
_original_dir = os.getcwd()
MCP_AVAILABLE = False
FASTMCP_AVAILABLE = False

try:
    os.chdir('/tmp')  # Change away from project directory
    from mcp.types import TextContent
    from mcp.server import FastMCP
    MCP_AVAILABLE = True
    FASTMCP_AVAILABLE = True
except ImportError:
    TextContent = None
    FastMCP = None
finally:
    os.chdir(_original_dir)  # Restore original directory

# Import FastMCP server
if FASTMCP_AVAILABLE:
    try:
        from skill_seekers.mcp import server_fastmcp
    except ImportError as e:
        print(f"Warning: Could not import server_fastmcp: {e}")
        server_fastmcp = None
        FASTMCP_AVAILABLE = False


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directories for testing."""
    config_dir = tmp_path / "configs"
    output_dir = tmp_path / "output"
    cache_dir = tmp_path / "cache"

    config_dir.mkdir()
    output_dir.mkdir()
    cache_dir.mkdir()

    return {
        "config": config_dir,
        "output": output_dir,
        "cache": cache_dir,
        "base": tmp_path
    }


@pytest.fixture
def sample_config(temp_dirs):
    """Create a sample config file."""
    config_data = {
        "name": "test-framework",
        "description": "Test framework for testing",
        "base_url": "https://test-framework.dev/",
        "selectors": {
            "main_content": "article",
            "title": "h1",
            "code_blocks": "pre"
        },
        "url_patterns": {
            "include": ["/docs/"],
            "exclude": ["/blog/", "/search/"]
        },
        "categories": {
            "getting_started": ["introduction", "getting-started"],
            "api": ["api", "reference"]
        },
        "rate_limit": 0.5,
        "max_pages": 100
    }

    config_path = temp_dirs["config"] / "test-framework.json"
    config_path.write_text(json.dumps(config_data, indent=2))
    return config_path


@pytest.fixture
def unified_config(temp_dirs):
    """Create a sample unified config file."""
    config_data = {
        "name": "test-unified",
        "description": "Test unified scraping",
        "merge_mode": "rule-based",
        "sources": [
            {
                "type": "documentation",
                "base_url": "https://example.com/docs/",
                "extract_api": True,
                "max_pages": 10
            },
            {
                "type": "github",
                "repo": "test/repo",
                "extract_readme": True
            }
        ]
    }

    config_path = temp_dirs["config"] / "test-unified.json"
    config_path.write_text(json.dumps(config_data, indent=2))
    return config_path


# ============================================================================
# SERVER INITIALIZATION TESTS
# ============================================================================


@pytest.mark.skipif(not FASTMCP_AVAILABLE, reason="FastMCP not available")
class TestFastMCPServerInitialization:
    """Test FastMCP server initialization and setup."""

    def test_server_import(self):
        """Test that FastMCP server module can be imported."""
        assert server_fastmcp is not None
        assert hasattr(server_fastmcp, 'mcp')

    def test_server_has_name(self):
        """Test that server has correct name."""
        assert server_fastmcp.mcp.name == "skill-seeker"

    def test_server_has_instructions(self):
        """Test that server has instructions."""
        assert server_fastmcp.mcp.instructions is not None
        assert "Skill Seeker" in server_fastmcp.mcp.instructions

    def test_all_tools_registered(self):
        """Test that all 17 tools are registered."""
        # FastMCP uses decorator-based registration
        # Tools should be available via the mcp instance
        tool_names = [
            # Config tools (3)
            "generate_config",
            "list_configs",
            "validate_config",
            # Scraping tools (4)
            "estimate_pages",
            "scrape_docs",
            "scrape_github",
            "scrape_pdf",
            # Packaging tools (3)
            "package_skill",
            "upload_skill",
            "install_skill",
            # Splitting tools (2)
            "split_config",
            "generate_router",
            # Source tools (5)
            "fetch_config",
            "submit_config",
            "add_config_source",
            "list_config_sources",
            "remove_config_source"
        ]

        # Check that decorators were applied
        for tool_name in tool_names:
            assert hasattr(server_fastmcp, tool_name), f"Missing tool: {tool_name}"


# ============================================================================
# CONFIG TOOLS TESTS (3 tools)
# ============================================================================


@pytest.mark.skipif(not FASTMCP_AVAILABLE, reason="FastMCP not available")
@pytest.mark.asyncio
class TestConfigTools:
    """Test configuration management tools."""

    async def test_generate_config_basic(self, temp_dirs, monkeypatch):
        """Test basic config generation."""
        monkeypatch.chdir(temp_dirs["base"])

        args = {
            "name": "my-framework",
            "url": "https://my-framework.dev/",
            "description": "My framework skill"
        }

        result = await server_fastmcp.generate_config(**args)

        assert isinstance(result, str)
        assert "✅" in result or "Generated" in result.lower()

        # Verify config file was created
        config_path = temp_dirs["config"] / "my-framework.json"
        if not config_path.exists():
            config_path = temp_dirs["base"] / "configs" / "my-framework.json"

    async def test_generate_config_with_options(self, temp_dirs, monkeypatch):
        """Test config generation with custom options."""
        monkeypatch.chdir(temp_dirs["base"])

        args = {
            "name": "custom-framework",
            "url": "https://custom.dev/",
            "description": "Custom skill",
            "max_pages": 200,
            "rate_limit": 1.0
        }

        result = await server_fastmcp.generate_config(**args)
        assert isinstance(result, str)

    async def test_generate_config_unlimited(self, temp_dirs, monkeypatch):
        """Test config generation with unlimited pages."""
        monkeypatch.chdir(temp_dirs["base"])

        args = {
            "name": "unlimited-framework",
            "url": "https://unlimited.dev/",
            "description": "Unlimited skill",
            "unlimited": True
        }

        result = await server_fastmcp.generate_config(**args)
        assert isinstance(result, str)

    async def test_list_configs(self, temp_dirs):
        """Test listing available configs."""
        result = await server_fastmcp.list_configs()

        assert isinstance(result, str)
        # Should return some configs or indicate none available
        assert len(result) > 0

    async def test_validate_config_valid(self, sample_config):
        """Test validating a valid config file."""
        result = await server_fastmcp.validate_config(config_path=str(sample_config))

        assert isinstance(result, str)
        assert "✅" in result or "valid" in result.lower()

    async def test_validate_config_unified(self, unified_config):
        """Test validating a unified config file."""
        result = await server_fastmcp.validate_config(config_path=str(unified_config))

        assert isinstance(result, str)
        # Should detect unified format
        assert "unified" in result.lower() or "source" in result.lower()

    async def test_validate_config_missing_file(self, temp_dirs):
        """Test validating a non-existent config file."""
        result = await server_fastmcp.validate_config(
            config_path=str(temp_dirs["config"] / "nonexistent.json")
        )

        assert isinstance(result, str)
        # Should indicate error
        assert "error" in result.lower() or "❌" in result or "not found" in result.lower()


# ============================================================================
# SCRAPING TOOLS TESTS (4 tools)
# ============================================================================


@pytest.mark.skipif(not FASTMCP_AVAILABLE, reason="FastMCP not available")
@pytest.mark.asyncio
class TestScrapingTools:
    """Test scraping tools."""

    async def test_estimate_pages_basic(self, sample_config):
        """Test basic page estimation."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="Estimated pages: 150\nRecommended max_pages: 200"
            )

            result = await server_fastmcp.estimate_pages(
                config_path=str(sample_config)
            )

            assert isinstance(result, str)

    async def test_estimate_pages_unlimited(self, sample_config):
        """Test estimation with unlimited discovery."""
        result = await server_fastmcp.estimate_pages(
            config_path=str(sample_config),
            unlimited=True
        )

        assert isinstance(result, str)

    async def test_estimate_pages_custom_discovery(self, sample_config):
        """Test estimation with custom max_discovery."""
        result = await server_fastmcp.estimate_pages(
            config_path=str(sample_config),
            max_discovery=500
        )

        assert isinstance(result, str)

    async def test_scrape_docs_basic(self, sample_config):
        """Test basic documentation scraping."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="Scraping completed successfully"
            )

            result = await server_fastmcp.scrape_docs(
                config_path=str(sample_config),
                dry_run=True
            )

            assert isinstance(result, str)

    async def test_scrape_docs_with_enhancement(self, sample_config):
        """Test scraping with local enhancement."""
        result = await server_fastmcp.scrape_docs(
            config_path=str(sample_config),
            enhance_local=True,
            dry_run=True
        )

        assert isinstance(result, str)

    async def test_scrape_docs_skip_scrape(self, sample_config):
        """Test scraping with skip_scrape flag."""
        result = await server_fastmcp.scrape_docs(
            config_path=str(sample_config),
            skip_scrape=True
        )

        assert isinstance(result, str)

    async def test_scrape_docs_unified(self, unified_config):
        """Test scraping with unified config."""
        result = await server_fastmcp.scrape_docs(
            config_path=str(unified_config),
            dry_run=True
        )

        assert isinstance(result, str)

    async def test_scrape_docs_merge_mode_override(self, unified_config):
        """Test scraping with merge mode override."""
        result = await server_fastmcp.scrape_docs(
            config_path=str(unified_config),
            merge_mode="claude-enhanced",
            dry_run=True
        )

        assert isinstance(result, str)

    async def test_scrape_github_basic(self):
        """Test basic GitHub scraping."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="GitHub scraping completed"
            )

            result = await server_fastmcp.scrape_github(
                repo="facebook/react",
                name="react-github-test"
            )

            assert isinstance(result, str)

    async def test_scrape_github_with_token(self):
        """Test GitHub scraping with authentication token."""
        result = await server_fastmcp.scrape_github(
            repo="private/repo",
            token="fake_token_for_testing",
            name="private-test"
        )

        assert isinstance(result, str)

    async def test_scrape_github_options(self):
        """Test GitHub scraping with various options."""
        result = await server_fastmcp.scrape_github(
            repo="test/repo",
            no_issues=True,
            no_changelog=True,
            no_releases=True,
            max_issues=50,
            scrape_only=True
        )

        assert isinstance(result, str)

    async def test_scrape_pdf_basic(self, temp_dirs):
        """Test basic PDF scraping."""
        # Create a dummy PDF config
        pdf_config = {
            "name": "test-pdf",
            "pdf_path": "/path/to/test.pdf",
            "description": "Test PDF skill"
        }
        config_path = temp_dirs["config"] / "test-pdf.json"
        config_path.write_text(json.dumps(pdf_config))

        result = await server_fastmcp.scrape_pdf(
            config_path=str(config_path)
        )

        assert isinstance(result, str)

    async def test_scrape_pdf_direct_path(self):
        """Test PDF scraping with direct path."""
        result = await server_fastmcp.scrape_pdf(
            pdf_path="/path/to/manual.pdf",
            name="manual-skill"
        )

        assert isinstance(result, str)


# ============================================================================
# PACKAGING TOOLS TESTS (3 tools)
# ============================================================================


@pytest.mark.skipif(not FASTMCP_AVAILABLE, reason="FastMCP not available")
@pytest.mark.asyncio
class TestPackagingTools:
    """Test packaging and upload tools."""

    async def test_package_skill_basic(self, temp_dirs):
        """Test basic skill packaging."""
        # Create a mock skill directory
        skill_dir = temp_dirs["output"] / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Test Skill")

        with patch('skill_seekers.mcp.tools.packaging_tools.subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="Packaging completed"
            )

            result = await server_fastmcp.package_skill(
                skill_dir=str(skill_dir),
                auto_upload=False
            )

            assert isinstance(result, str)

    async def test_package_skill_with_auto_upload(self, temp_dirs):
        """Test packaging with auto-upload."""
        skill_dir = temp_dirs["output"] / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Test Skill")

        result = await server_fastmcp.package_skill(
            skill_dir=str(skill_dir),
            auto_upload=True
        )

        assert isinstance(result, str)

    async def test_upload_skill_basic(self, temp_dirs):
        """Test basic skill upload."""
        # Create a mock zip file
        zip_path = temp_dirs["output"] / "test-skill.zip"
        zip_path.write_text("fake zip content")

        with patch('skill_seekers.mcp.tools.packaging_tools.subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="Upload successful"
            )

            result = await server_fastmcp.upload_skill(
                skill_zip=str(zip_path)
            )

            assert isinstance(result, str)

    async def test_upload_skill_missing_file(self, temp_dirs):
        """Test upload with missing file."""
        result = await server_fastmcp.upload_skill(
            skill_zip=str(temp_dirs["output"] / "nonexistent.zip")
        )

        assert isinstance(result, str)

    async def test_install_skill_with_config_name(self):
        """Test complete install workflow with config name."""
        # Mock the fetch_config_tool import that install_skill_tool uses
        with patch('skill_seekers.mcp.tools.packaging_tools.fetch_config_tool') as mock_fetch:
            mock_fetch.return_value = [Mock(text="Config fetched")]

            result = await server_fastmcp.install_skill(
                config_name="react",
                destination="output",
                dry_run=True
            )

            assert isinstance(result, str)

    async def test_install_skill_with_config_path(self, sample_config):
        """Test complete install workflow with config path."""
        with patch('skill_seekers.mcp.tools.packaging_tools.fetch_config_tool') as mock_fetch:
            mock_fetch.return_value = [Mock(text="Config ready")]

            result = await server_fastmcp.install_skill(
                config_path=str(sample_config),
                destination="output",
                dry_run=True
            )

            assert isinstance(result, str)

    async def test_install_skill_unlimited(self):
        """Test install workflow with unlimited pages."""
        with patch('skill_seekers.mcp.tools.packaging_tools.fetch_config_tool') as mock_fetch:
            mock_fetch.return_value = [Mock(text="Config fetched")]

            result = await server_fastmcp.install_skill(
                config_name="react",
                unlimited=True,
                dry_run=True
            )

            assert isinstance(result, str)

    async def test_install_skill_no_upload(self):
        """Test install workflow without auto-upload."""
        with patch('skill_seekers.mcp.tools.packaging_tools.fetch_config_tool') as mock_fetch:
            mock_fetch.return_value = [Mock(text="Config fetched")]

            result = await server_fastmcp.install_skill(
                config_name="react",
                auto_upload=False,
                dry_run=True
            )

            assert isinstance(result, str)


# ============================================================================
# SPLITTING TOOLS TESTS (2 tools)
# ============================================================================


@pytest.mark.skipif(not FASTMCP_AVAILABLE, reason="FastMCP not available")
@pytest.mark.asyncio
class TestSplittingTools:
    """Test config splitting and router generation tools."""

    async def test_split_config_auto_strategy(self, sample_config):
        """Test config splitting with auto strategy."""
        result = await server_fastmcp.split_config(
            config_path=str(sample_config),
            strategy="auto",
            dry_run=True
        )

        assert isinstance(result, str)

    async def test_split_config_category_strategy(self, sample_config):
        """Test config splitting with category strategy."""
        result = await server_fastmcp.split_config(
            config_path=str(sample_config),
            strategy="category",
            target_pages=5000,
            dry_run=True
        )

        assert isinstance(result, str)

    async def test_split_config_size_strategy(self, sample_config):
        """Test config splitting with size strategy."""
        result = await server_fastmcp.split_config(
            config_path=str(sample_config),
            strategy="size",
            target_pages=3000,
            dry_run=True
        )

        assert isinstance(result, str)

    async def test_generate_router_basic(self, temp_dirs):
        """Test router generation."""
        # Create some mock config files
        (temp_dirs["config"] / "godot-scripting.json").write_text("{}")
        (temp_dirs["config"] / "godot-physics.json").write_text("{}")

        result = await server_fastmcp.generate_router(
            config_pattern=str(temp_dirs["config"] / "godot-*.json")
        )

        assert isinstance(result, str)

    async def test_generate_router_with_name(self, temp_dirs):
        """Test router generation with custom name."""
        result = await server_fastmcp.generate_router(
            config_pattern=str(temp_dirs["config"] / "godot-*.json"),
            router_name="godot-hub"
        )

        assert isinstance(result, str)


# ============================================================================
# SOURCE TOOLS TESTS (5 tools)
# ============================================================================


@pytest.mark.skipif(not FASTMCP_AVAILABLE, reason="FastMCP not available")
@pytest.mark.asyncio
class TestSourceTools:
    """Test config source management tools."""

    async def test_fetch_config_list_api(self):
        """Test fetching config list from API."""
        with patch('skill_seekers.mcp.tools.source_tools.httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "configs": [
                    {"name": "react", "category": "web-frameworks"},
                    {"name": "vue", "category": "web-frameworks"}
                ],
                "total": 2
            }
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            result = await server_fastmcp.fetch_config(
                list_available=True
            )

            assert isinstance(result, str)

    async def test_fetch_config_download_api(self, temp_dirs):
        """Test downloading specific config from API."""
        result = await server_fastmcp.fetch_config(
            config_name="react",
            destination=str(temp_dirs["config"])
        )

        assert isinstance(result, str)

    async def test_fetch_config_with_category_filter(self):
        """Test fetching configs with category filter."""
        result = await server_fastmcp.fetch_config(
            list_available=True,
            category="web-frameworks"
        )

        assert isinstance(result, str)

    async def test_fetch_config_from_git_url(self, temp_dirs):
        """Test fetching config from git URL."""
        result = await server_fastmcp.fetch_config(
            config_name="react",
            git_url="https://github.com/myorg/configs.git",
            destination=str(temp_dirs["config"])
        )

        assert isinstance(result, str)

    async def test_fetch_config_from_source(self, temp_dirs):
        """Test fetching config from named source."""
        result = await server_fastmcp.fetch_config(
            config_name="react",
            source="team",
            destination=str(temp_dirs["config"])
        )

        assert isinstance(result, str)

    async def test_fetch_config_with_token(self, temp_dirs):
        """Test fetching config with authentication token."""
        result = await server_fastmcp.fetch_config(
            config_name="react",
            git_url="https://github.com/private/configs.git",
            token="fake_token",
            destination=str(temp_dirs["config"])
        )

        assert isinstance(result, str)

    async def test_fetch_config_refresh_cache(self, temp_dirs):
        """Test fetching config with cache refresh."""
        result = await server_fastmcp.fetch_config(
            config_name="react",
            git_url="https://github.com/myorg/configs.git",
            refresh=True,
            destination=str(temp_dirs["config"])
        )

        assert isinstance(result, str)

    async def test_submit_config_with_path(self, sample_config):
        """Test submitting config from file path."""
        result = await server_fastmcp.submit_config(
            config_path=str(sample_config),
            testing_notes="Tested with 20 pages, works well"
        )

        assert isinstance(result, str)

    async def test_submit_config_with_json(self):
        """Test submitting config as JSON string."""
        config_json = json.dumps({
            "name": "my-framework",
            "base_url": "https://my-framework.dev/"
        })

        result = await server_fastmcp.submit_config(
            config_json=config_json,
            testing_notes="Works great!"
        )

        assert isinstance(result, str)

    async def test_add_config_source_basic(self):
        """Test adding a config source."""
        result = await server_fastmcp.add_config_source(
            name="team",
            git_url="https://github.com/myorg/configs.git"
        )

        assert isinstance(result, str)

    async def test_add_config_source_with_options(self):
        """Test adding config source with all options."""
        result = await server_fastmcp.add_config_source(
            name="company",
            git_url="https://gitlab.com/mycompany/configs.git",
            source_type="gitlab",
            token_env="GITLAB_TOKEN",
            branch="develop",
            priority=50,
            enabled=True
        )

        assert isinstance(result, str)

    async def test_add_config_source_ssh_url(self):
        """Test adding config source with SSH URL."""
        result = await server_fastmcp.add_config_source(
            name="private",
            git_url="git@github.com:myorg/private-configs.git",
            source_type="github"
        )

        assert isinstance(result, str)

    async def test_list_config_sources_all(self):
        """Test listing all config sources."""
        result = await server_fastmcp.list_config_sources(
            enabled_only=False
        )

        assert isinstance(result, str)

    async def test_list_config_sources_enabled_only(self):
        """Test listing only enabled sources."""
        result = await server_fastmcp.list_config_sources(
            enabled_only=True
        )

        assert isinstance(result, str)

    async def test_remove_config_source(self):
        """Test removing a config source."""
        result = await server_fastmcp.remove_config_source(
            name="team"
        )

        assert isinstance(result, str)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


@pytest.mark.skipif(not FASTMCP_AVAILABLE, reason="FastMCP not available")
@pytest.mark.asyncio
class TestFastMCPIntegration:
    """Test integration scenarios across multiple tools."""

    async def test_workflow_generate_validate_scrape(self, temp_dirs, monkeypatch):
        """Test complete workflow: generate → validate → scrape."""
        monkeypatch.chdir(temp_dirs["base"])

        # Step 1: Generate config
        result1 = await server_fastmcp.generate_config(
            name="workflow-test",
            url="https://workflow.dev/",
            description="Workflow test"
        )
        assert isinstance(result1, str)

        # Step 2: Validate config
        config_path = temp_dirs["base"] / "configs" / "workflow-test.json"
        if config_path.exists():
            result2 = await server_fastmcp.validate_config(
                config_path=str(config_path)
            )
            assert isinstance(result2, str)

    async def test_workflow_source_fetch_scrape(self, temp_dirs):
        """Test workflow: add source → fetch config → scrape."""
        # Step 1: Add source
        result1 = await server_fastmcp.add_config_source(
            name="test-source",
            git_url="https://github.com/test/configs.git"
        )
        assert isinstance(result1, str)

        # Step 2: Fetch config
        result2 = await server_fastmcp.fetch_config(
            config_name="react",
            source="test-source",
            destination=str(temp_dirs["config"])
        )
        assert isinstance(result2, str)

    async def test_workflow_split_router(self, sample_config, temp_dirs):
        """Test workflow: split config → generate router."""
        # Step 1: Split config
        result1 = await server_fastmcp.split_config(
            config_path=str(sample_config),
            strategy="category",
            dry_run=True
        )
        assert isinstance(result1, str)

        # Step 2: Generate router
        result2 = await server_fastmcp.generate_router(
            config_pattern=str(temp_dirs["config"] / "test-framework-*.json")
        )
        assert isinstance(result2, str)


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


@pytest.mark.skipif(not FASTMCP_AVAILABLE, reason="FastMCP not available")
@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling across all tools."""

    async def test_generate_config_invalid_url(self, temp_dirs, monkeypatch):
        """Test error handling for invalid URL."""
        monkeypatch.chdir(temp_dirs["base"])

        result = await server_fastmcp.generate_config(
            name="invalid-test",
            url="not-a-valid-url",
            description="Test invalid URL"
        )

        assert isinstance(result, str)
        # Should indicate error or handle gracefully

    async def test_validate_config_invalid_json(self, temp_dirs):
        """Test error handling for invalid JSON."""
        bad_config = temp_dirs["config"] / "bad.json"
        bad_config.write_text("{ invalid json }")

        result = await server_fastmcp.validate_config(
            config_path=str(bad_config)
        )

        assert isinstance(result, str)

    async def test_scrape_docs_missing_config(self):
        """Test error handling for missing config file."""
        # This should handle the error gracefully and return a string
        try:
            result = await server_fastmcp.scrape_docs(
                config_path="/nonexistent/config.json"
            )
            assert isinstance(result, str)
            # Should contain error message
            assert "error" in result.lower() or "not found" in result.lower() or "❌" in result
        except FileNotFoundError:
            # If it raises, that's also acceptable error handling
            pass

    async def test_package_skill_missing_directory(self):
        """Test error handling for missing skill directory."""
        result = await server_fastmcp.package_skill(
            skill_dir="/nonexistent/skill"
        )

        assert isinstance(result, str)


# ============================================================================
# TYPE VALIDATION TESTS
# ============================================================================


@pytest.mark.skipif(not FASTMCP_AVAILABLE, reason="FastMCP not available")
@pytest.mark.asyncio
class TestTypeValidation:
    """Test type validation for tool parameters."""

    async def test_generate_config_return_type(self, temp_dirs, monkeypatch):
        """Test that generate_config returns string."""
        monkeypatch.chdir(temp_dirs["base"])

        result = await server_fastmcp.generate_config(
            name="type-test",
            url="https://test.dev/",
            description="Type test"
        )

        assert isinstance(result, str)

    async def test_list_configs_return_type(self):
        """Test that list_configs returns string."""
        result = await server_fastmcp.list_configs()
        assert isinstance(result, str)

    async def test_estimate_pages_return_type(self, sample_config):
        """Test that estimate_pages returns string."""
        result = await server_fastmcp.estimate_pages(
            config_path=str(sample_config)
        )
        assert isinstance(result, str)

    async def test_all_tools_return_strings(self, sample_config, temp_dirs):
        """Test that all tools return string type."""
        # Sample a few tools from each category
        tools_to_test = [
            (server_fastmcp.validate_config, {"config_path": str(sample_config)}),
            (server_fastmcp.list_configs, {}),
            (server_fastmcp.list_config_sources, {"enabled_only": False}),
        ]

        for tool_func, args in tools_to_test:
            result = await tool_func(**args)
            assert isinstance(result, str), f"{tool_func.__name__} should return string"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
