#!/usr/bin/env python3
"""
Tests for install_skill MCP tool and CLI

Tests the complete workflow orchestration for A1.7:
- Input validation
- Dry-run mode
- Phase orchestration
- Error handling
- CLI integration
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Defensive import for MCP package (may not be installed in all environments)
try:
    from mcp.types import TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    TextContent = None  # Placeholder

# Import the function to test
from skill_seekers.mcp.tools.packaging_tools import install_skill_tool


@pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP package not installed")
class TestInstallSkillValidation:
    """Test input validation"""

    @pytest.mark.asyncio
    async def test_validation_no_config(self):
        """Test error when neither config_name nor config_path provided"""
        result = await install_skill_tool({})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "❌ Error: Must provide either config_name or config_path" in result[0].text
        assert "Examples:" in result[0].text

    @pytest.mark.asyncio
    async def test_validation_both_configs(self):
        """Test error when both config_name and config_path provided"""
        result = await install_skill_tool({
            "config_name": "react",
            "config_path": "configs/react.json"
        })

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "❌ Error: Cannot provide both config_name and config_path" in result[0].text
        assert "Choose one:" in result[0].text


@pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP package not installed")
class TestInstallSkillDryRun:
    """Test dry-run mode"""

    @pytest.mark.asyncio
    async def test_dry_run_with_config_name(self):
        """Test dry run with config name (includes fetch phase)"""
        result = await install_skill_tool({
            "config_name": "react",
            "dry_run": True
        })

        assert len(result) == 1
        output = result[0].text

        # Verify dry run mode is indicated
        assert "🔍 DRY RUN MODE" in output
        assert "Preview only, no actions taken" in output

        # Verify all 5 phases are shown
        assert "PHASE 1/5: Fetch Config" in output
        assert "PHASE 2/5: Scrape Documentation" in output
        assert "PHASE 3/5: AI Enhancement (MANDATORY)" in output
        assert "PHASE 4/5: Package Skill" in output
        assert "PHASE 5/5: Upload to Claude" in output

        # Verify dry run indicators
        assert "[DRY RUN]" in output
        assert "This was a dry run. No actions were taken." in output

    @pytest.mark.asyncio
    async def test_dry_run_with_config_path(self):
        """Test dry run with config path (skips fetch phase)"""
        result = await install_skill_tool({
            "config_path": "configs/react.json",
            "dry_run": True
        })

        assert len(result) == 1
        output = result[0].text

        # Verify dry run mode
        assert "🔍 DRY RUN MODE" in output

        # Verify only 4 phases (no fetch)
        assert "PHASE 1/4: Scrape Documentation" in output
        assert "PHASE 2/4: AI Enhancement (MANDATORY)" in output
        assert "PHASE 3/4: Package Skill" in output
        assert "PHASE 4/4: Upload to Claude" in output

        # Should not show fetch phase
        assert "PHASE 1/5" not in output
        assert "Fetch Config" not in output


@pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP package not installed")
class TestInstallSkillEnhancementMandatory:
    """Test that enhancement is always included"""

    @pytest.mark.asyncio
    async def test_enhancement_is_mandatory(self):
        """Test that enhancement phase is always present and mandatory"""
        result = await install_skill_tool({
            "config_name": "react",
            "dry_run": True
        })

        output = result[0].text

        # Verify enhancement phase is present
        assert "AI Enhancement (MANDATORY)" in output
        assert "Enhancement is REQUIRED for quality (3/10→9/10 boost)" in output or \
               "REQUIRED for quality" in output

        # Verify it's not optional
        assert "MANDATORY" in output
        assert "no skip option" in output.lower() or "MANDATORY" in output


@pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP package not installed")
class TestInstallSkillPhaseOrchestration:
    """Test phase orchestration and data flow"""

    @pytest.mark.asyncio
    @patch('skill_seekers.mcp.server.fetch_config_tool')
    @patch('skill_seekers.mcp.server.scrape_docs_tool')
    @patch('skill_seekers.mcp.server.run_subprocess_with_streaming')
    @patch('skill_seekers.mcp.server.package_skill_tool')
    @patch('skill_seekers.mcp.server.upload_skill_tool')
    @patch('builtins.open')
    @patch('os.environ.get')
    async def test_full_workflow_with_fetch(
        self,
        mock_env_get,
        mock_open,
        mock_upload,
        mock_package,
        mock_subprocess,
        mock_scrape,
        mock_fetch
    ):
        """Test complete workflow when config_name is provided"""

        # Mock fetch_config response
        mock_fetch.return_value = [TextContent(
            type="text",
            text="✅ Config fetched successfully\n\nConfig saved to: configs/react.json"
        )]

        # Mock config file read
        import json
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = json.dumps({"name": "react"})
        mock_open.return_value = mock_file

        # Mock scrape_docs response
        mock_scrape.return_value = [TextContent(
            type="text",
            text="✅ Scraping complete\n\nSkill built at: output/react/"
        )]

        # Mock enhancement subprocess
        mock_subprocess.return_value = ("✅ Enhancement complete", "", 0)

        # Mock package response
        mock_package.return_value = [TextContent(
            type="text",
            text="✅ Package complete\n\nSaved to: output/react.zip"
        )]

        # Mock upload response
        mock_upload.return_value = [TextContent(
            type="text",
            text="✅ Upload successful"
        )]

        # Mock env (has API key)
        mock_env_get.return_value = "sk-ant-test-key"

        # Run the workflow
        result = await install_skill_tool({
            "config_name": "react",
            "auto_upload": True
        })

        output = result[0].text

        # Verify all phases executed
        assert "PHASE 1/5: Fetch Config" in output
        assert "PHASE 2/5: Scrape Documentation" in output
        assert "PHASE 3/5: AI Enhancement" in output
        assert "PHASE 4/5: Package Skill" in output
        assert "PHASE 5/5: Upload to Claude" in output

        # Verify workflow completion
        assert "✅ WORKFLOW COMPLETE" in output
        assert "fetch_config" in output
        assert "scrape_docs" in output
        assert "enhance_skill" in output
        assert "package_skill" in output
        assert "upload_skill" in output

    @pytest.mark.asyncio
    @patch('skill_seekers.mcp.server.scrape_docs_tool')
    @patch('skill_seekers.mcp.server.run_subprocess_with_streaming')
    @patch('skill_seekers.mcp.server.package_skill_tool')
    @patch('builtins.open')
    @patch('os.environ.get')
    async def test_workflow_with_existing_config(
        self,
        mock_env_get,
        mock_open,
        mock_package,
        mock_subprocess,
        mock_scrape
    ):
        """Test workflow when config_path is provided (skips fetch)"""

        # Mock config file read
        import json
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = json.dumps({"name": "custom"})
        mock_open.return_value = mock_file

        # Mock scrape response
        mock_scrape.return_value = [TextContent(
            type="text",
            text="✅ Scraping complete"
        )]

        # Mock enhancement subprocess
        mock_subprocess.return_value = ("✅ Enhancement complete", "", 0)

        # Mock package response
        mock_package.return_value = [TextContent(
            type="text",
            text="✅ Package complete\n\nSaved to: output/custom.zip"
        )]

        # Mock env (no API key - should skip upload)
        mock_env_get.return_value = ""

        # Run the workflow
        result = await install_skill_tool({
            "config_path": "configs/custom.json",
            "auto_upload": True
        })

        output = result[0].text

        # Should only have 4 phases (no fetch)
        assert "PHASE 1/4: Scrape Documentation" in output
        assert "PHASE 2/4: AI Enhancement" in output
        assert "PHASE 3/4: Package Skill" in output
        assert "PHASE 4/4: Upload to Claude" in output

        # Should not have fetch phase
        assert "Fetch Config" not in output

        # Should show manual upload instructions (no API key)
        assert "⚠️  ANTHROPIC_API_KEY not set" in output
        assert "Manual upload:" in output


@pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP package not installed")
class TestInstallSkillErrorHandling:
    """Test error handling at each phase"""

    @pytest.mark.asyncio
    @patch('skill_seekers.mcp.server.fetch_config_tool')
    async def test_fetch_phase_failure(self, mock_fetch):
        """Test handling of fetch phase failure"""

        # Mock fetch failure
        mock_fetch.return_value = [TextContent(
            type="text",
            text="❌ Failed to fetch config: Network error"
        )]

        result = await install_skill_tool({
            "config_name": "react"
        })

        output = result[0].text

        # Verify error is shown
        assert "❌ Failed to fetch config" in output

    @pytest.mark.asyncio
    @patch('skill_seekers.mcp.server.scrape_docs_tool')
    @patch('builtins.open')
    async def test_scrape_phase_failure(self, mock_open, mock_scrape):
        """Test handling of scrape phase failure"""

        # Mock config read
        import json
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = json.dumps({"name": "test"})
        mock_open.return_value = mock_file

        # Mock scrape failure
        mock_scrape.return_value = [TextContent(
            type="text",
            text="❌ Scraping failed: Connection timeout"
        )]

        result = await install_skill_tool({
            "config_path": "configs/test.json"
        })

        output = result[0].text

        # Verify error is shown and workflow stops
        assert "❌ Scraping failed" in output
        assert "WORKFLOW COMPLETE" not in output

    @pytest.mark.asyncio
    @patch('skill_seekers.mcp.server.scrape_docs_tool')
    @patch('skill_seekers.mcp.server.run_subprocess_with_streaming')
    @patch('builtins.open')
    async def test_enhancement_phase_failure(self, mock_open, mock_subprocess, mock_scrape):
        """Test handling of enhancement phase failure"""

        # Mock config read
        import json
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = json.dumps({"name": "test"})
        mock_open.return_value = mock_file

        # Mock scrape success
        mock_scrape.return_value = [TextContent(
            type="text",
            text="✅ Scraping complete"
        )]

        # Mock enhancement failure
        mock_subprocess.return_value = ("", "Enhancement error: Claude not found", 1)

        result = await install_skill_tool({
            "config_path": "configs/test.json"
        })

        output = result[0].text

        # Verify error is shown
        assert "❌ Enhancement failed" in output
        assert "exit code 1" in output


@pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP package not installed")
class TestInstallSkillOptions:
    """Test various option combinations"""

    @pytest.mark.asyncio
    async def test_no_upload_option(self):
        """Test that no_upload option skips upload phase"""
        result = await install_skill_tool({
            "config_name": "react",
            "auto_upload": False,
            "dry_run": True
        })

        output = result[0].text

        # Should not show upload phase
        assert "PHASE 5/5: Upload" not in output
        assert "PHASE 4/5: Package" in output  # Should still be 4/5 for fetch path

    @pytest.mark.asyncio
    async def test_unlimited_option(self):
        """Test that unlimited option is passed to scraper"""
        result = await install_skill_tool({
            "config_path": "configs/react.json",
            "unlimited": True,
            "dry_run": True
        })

        output = result[0].text

        # Verify unlimited mode is indicated
        assert "Unlimited mode: True" in output

    @pytest.mark.asyncio
    async def test_custom_destination(self):
        """Test custom destination directory"""
        result = await install_skill_tool({
            "config_name": "react",
            "destination": "/tmp/skills",
            "dry_run": True
        })

        output = result[0].text

        # Verify custom destination
        assert "Destination: /tmp/skills/" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
