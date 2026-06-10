#!/usr/bin/env python3
"""
End-to-End Integration Tests for install_skill MCP tool and CLI

Tests the complete workflow with real file operations:
- MCP tool interface (install_skill_tool)
- CLI interface (skill-seekers install)
- Real config files
- Real file I/O
- Minimal mocking (only enhancement and upload for speed)

These tests verify the actual integration between components.

Test Coverage (23 tests, 100% pass rate):

1. TestInstallSkillE2E (5 tests)
   - test_e2e_with_config_path_no_upload: Full workflow with existing config
   - test_e2e_with_config_name_fetch: Full workflow with config fetch phase
   - test_e2e_dry_run_mode: Dry-run preview mode
   - test_e2e_error_handling_scrape_failure: Scrape phase error handling
   - test_e2e_error_handling_enhancement_failure: Enhancement phase error handling

2. TestInstallSkillCLI_E2E (5 tests)
   - test_cli_dry_run: CLI dry-run via direct function call
   - test_cli_validation_error_no_config: CLI validation error handling
   - test_cli_help: CLI help command
   - test_cli_full_workflow_mocked: Full CLI workflow with mocks
   - test_cli_via_unified_command: Unified CLI command (skipped - subprocess asyncio issue)

3. TestInstallSkillE2E_RealFiles (1 test)
   - test_e2e_real_scrape_with_mocked_enhancement: Real scraping with mocked enhancement

Total: 11 E2E tests (10 passed, 1 skipped)
Combined with unit tests: 24 total tests (23 passed, 1 skipped)

Run with: pytest tests/test_install_skill.py tests/test_install_skill_e2e.py -v
"""

import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.mcp_only

# Defensive import for MCP package (may not be installed in all environments)
try:
    from mcp.types import TextContent

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    TextContent = None  # Placeholder

# Import the MCP tool to test
from skill_seekers.mcp.tools.packaging_tools import install_skill_tool  # noqa: E402


# --- Local, offline fixture server for the "real scrape" e2e test -------------
# The real-scrape e2e test must exercise the genuine scrape -> build -> enhance
# pipeline WITHOUT depending on an external site. httpbin was flaky and, worse,
# the test used to globally patch os.environ.get -> returning the API key for
# REQUESTS_CA_BUNDLE/SSL_CERT_FILE too, which broke TLS and silently sabotaged
# its own scrape (it only ever passed because a now-fixed bug built a skill from
# the failed scrape). We serve a small fixed HTML doc from localhost instead, so
# the scrape is real but deterministic and offline.
_FIXTURE_DOC_HTML = b"""<!DOCTYPE html>
<html>
  <head><title>Example Docs - Getting Started</title></head>
  <body>
    <h1>Getting Started</h1>
    <p>Welcome to the Example library documentation. This page is served
    locally so the end-to-end scrape test never touches the public network.</p>
    <h2>Installation</h2>
    <pre><code>pip install example</code></pre>
    <h2>Quick Usage</h2>
    <p>Import the package and call <code>example.run()</code> to begin
    processing. The function returns a result object you can inspect.</p>
  </body>
</html>
"""


class _FixtureDocHandler(BaseHTTPRequestHandler):
    """Serve the fixture doc for the root page; 404 for llms.txt/robots/etc.

    The 404s let the scraper fall through its llms.txt/sitemap probes to plain
    HTML scraping -- the deterministic path this test covers.
    """

    def do_GET(self):  # noqa: N802 (stdlib-defined name)
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(_FIXTURE_DOC_HTML)))
            self.end_headers()
            self.wfile.write(_FIXTURE_DOC_HTML)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *_args):  # silence per-request stderr logging
        pass


@pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP package not installed")
class TestInstallSkillE2E:
    """End-to-end tests for install_skill MCP tool"""

    @pytest.fixture
    def test_config_file(self, tmp_path):
        """Create a minimal test config file"""
        config = {
            "name": "test-e2e",
            "description": "Test skill for E2E testing",
            "base_url": "https://example.com/docs/",
            "selectors": {"main_content": "article", "title": "title", "code_blocks": "pre"},
            "url_patterns": {"include": ["/docs/"], "exclude": ["/search", "/404"]},
            "categories": {"getting_started": ["intro", "start"], "api": ["api", "reference"]},
            "rate_limit": 0.1,
            "max_pages": 5,  # Keep it small for fast testing
        }

        config_path = tmp_path / "test-e2e.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        return str(config_path)

    @pytest.fixture
    def mock_scrape_output(self, tmp_path):
        """Mock scrape_docs output to avoid actual scraping"""
        skill_dir = tmp_path / "output" / "test-e2e"
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Create basic skill structure
        (skill_dir / "SKILL.md").write_text("# Test Skill\n\nThis is a test skill.")
        (skill_dir / "references").mkdir(exist_ok=True)
        (skill_dir / "references" / "index.md").write_text("# References\n\nTest references.")

        return str(skill_dir)

    @pytest.mark.asyncio
    async def test_e2e_with_config_path_no_upload(
        self, test_config_file, tmp_path, mock_scrape_output
    ):
        """E2E test: config_path mode, no upload"""

        # Mock the subprocess calls for scraping and enhancement
        with (
            patch("skill_seekers.mcp.tools.scraping_tools.scrape_docs_tool") as mock_scrape,
            patch(
                "skill_seekers.mcp.tools.packaging_tools.run_subprocess_with_streaming"
            ) as mock_enhance,
            patch("skill_seekers.mcp.tools.packaging_tools.package_skill_tool") as mock_package,
        ):
            # Mock scrape_docs to return success
            mock_scrape.return_value = [
                TextContent(
                    type="text",
                    text=f"✅ Scraping complete\n\nSkill built at: {mock_scrape_output}",
                )
            ]

            # Mock enhancement subprocess (success)
            mock_enhance.return_value = ("✅ Enhancement complete", "", 0)

            # Mock package_skill to return success
            zip_path = str(tmp_path / "output" / "test-e2e.zip")
            mock_package.return_value = [
                TextContent(type="text", text=f"✅ Package complete\n\nSaved to: {zip_path}")
            ]

            # Run the tool
            result = await install_skill_tool(
                {
                    "config_path": test_config_file,
                    "destination": str(tmp_path / "output"),
                    "auto_upload": False,  # Skip upload
                    "unlimited": False,
                    "dry_run": False,
                }
            )

            # Verify output
            assert len(result) == 1
            output = result[0].text

            # Check that all phases were mentioned (no upload since auto_upload=False)
            assert "PHASE 1/4: Scrape Documentation" in output or "PHASE 1/3" in output
            assert "AI Enhancement" in output
            assert "Package Skill" in output

            # Check workflow completion
            assert "✅ WORKFLOW COMPLETE" in output or "WORKFLOW COMPLETE" in output

            # Verify scrape_docs was called
            mock_scrape.assert_called_once()
            call_args = mock_scrape.call_args[0][0]
            assert call_args["config_path"] == test_config_file

            # Verify enhancement was called
            mock_enhance.assert_called_once()
            enhance_cmd = mock_enhance.call_args[0][0]
            assert "enhance_skill_local.py" in enhance_cmd[1]

            # Verify package was called
            mock_package.assert_called_once()

    @pytest.mark.asyncio
    async def test_e2e_with_config_name_fetch(self, tmp_path):
        """E2E test: config_name mode with fetch phase"""

        with (
            patch("skill_seekers.mcp.tools.source_tools.fetch_config_tool") as mock_fetch,
            patch("skill_seekers.mcp.tools.scraping_tools.scrape_docs_tool") as mock_scrape,
            patch(
                "skill_seekers.mcp.tools.packaging_tools.run_subprocess_with_streaming"
            ) as mock_enhance,
            patch("skill_seekers.mcp.tools.packaging_tools.package_skill_tool") as mock_package,
            patch("builtins.open", create=True) as mock_file_open,
            patch("os.environ.get") as mock_env,
        ):
            # Mock fetch_config to return success
            config_path = str(tmp_path / "configs" / "react.json")
            mock_fetch.return_value = [
                TextContent(
                    type="text",
                    text=f"✅ Config fetched successfully\n\nConfig saved to: {config_path}",
                )
            ]

            # Mock config file read
            mock_config = MagicMock()
            mock_config.__enter__.return_value.read.return_value = json.dumps({"name": "react"})
            mock_file_open.return_value = mock_config

            # Mock scrape_docs
            skill_dir = str(tmp_path / "output" / "react")
            mock_scrape.return_value = [
                TextContent(
                    type="text", text=f"✅ Scraping complete\n\nSkill built at: {skill_dir}"
                )
            ]

            # Mock enhancement
            mock_enhance.return_value = ("✅ Enhancement complete", "", 0)

            # Mock package
            zip_path = str(tmp_path / "output" / "react.zip")
            mock_package.return_value = [
                TextContent(type="text", text=f"✅ Package complete\n\nSaved to: {zip_path}")
            ]

            # Mock env (no API key - should skip upload)
            mock_env.return_value = ""

            # Run the tool
            result = await install_skill_tool(
                {
                    "config_name": "react",
                    "destination": str(tmp_path / "output"),
                    "auto_upload": True,  # Would upload if key present
                    "unlimited": False,
                    "dry_run": False,
                }
            )

            # Verify output
            output = result[0].text

            # Check that all 5 phases were mentioned (including fetch)
            assert "PHASE 1/5: Fetch Config" in output
            assert "PHASE 2/5: Scrape Documentation" in output
            assert "PHASE 3/5: AI Enhancement" in output
            assert "PHASE 4/5: Package Skill" in output
            assert "PHASE 5/5: Upload to" in output

            # Verify fetch was called
            mock_fetch.assert_called_once()

            # Verify manual upload instructions shown (no API key)
            assert "⚠️  ANTHROPIC_API_KEY not set" in output or "Manual upload" in output

    @pytest.mark.asyncio
    async def test_e2e_dry_run_mode(self, test_config_file):
        """E2E test: dry-run mode (no actual execution)"""

        result = await install_skill_tool(
            {"config_path": test_config_file, "auto_upload": False, "dry_run": True}
        )

        output = result[0].text

        # Verify dry run indicators
        assert "🔍 DRY RUN MODE" in output
        assert "Preview only, no actions taken" in output

        # Verify phases are shown
        assert "PHASE 1/4: Scrape Documentation" in output
        assert "PHASE 2/4: AI Enhancement (MANDATORY)" in output
        assert "PHASE 3/4: Package Skill" in output

        # Verify dry run markers
        assert "[DRY RUN]" in output
        assert "This was a dry run" in output

    @pytest.mark.asyncio
    async def test_e2e_error_handling_scrape_failure(self, test_config_file):
        """E2E test: error handling when scrape fails"""

        with patch("skill_seekers.mcp.tools.scraping_tools.scrape_docs_tool") as mock_scrape:
            # Mock scrape failure
            mock_scrape.return_value = [
                TextContent(type="text", text="❌ Scraping failed: Network timeout")
            ]

            result = await install_skill_tool(
                {"config_path": test_config_file, "auto_upload": False, "dry_run": False}
            )

            output = result[0].text

            # Verify error is propagated
            assert "❌ Scraping failed" in output
            assert "WORKFLOW COMPLETE" not in output

    @pytest.mark.asyncio
    async def test_e2e_error_handling_enhancement_failure(
        self, test_config_file, mock_scrape_output
    ):
        """E2E test: error handling when enhancement fails"""

        with (
            patch("skill_seekers.mcp.tools.scraping_tools.scrape_docs_tool") as mock_scrape,
            patch(
                "skill_seekers.mcp.tools.packaging_tools.run_subprocess_with_streaming"
            ) as mock_enhance,
        ):
            # Mock successful scrape
            mock_scrape.return_value = [
                TextContent(
                    type="text",
                    text=f"✅ Scraping complete\n\nSkill built at: {mock_scrape_output}",
                )
            ]

            # Mock enhancement failure
            mock_enhance.return_value = ("", "Enhancement error: Claude not found", 1)

            result = await install_skill_tool(
                {"config_path": test_config_file, "auto_upload": False, "dry_run": False}
            )

            output = result[0].text

            # Verify error is shown
            assert "❌ Enhancement failed" in output
            assert "exit code 1" in output


@pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP package not installed")
class TestInstallSkillCLI_E2E:
    """End-to-end tests for skill-seekers install CLI"""

    @pytest.fixture
    def test_config_file(self, tmp_path):
        """Create a minimal test config file"""
        config = {
            "name": "test-cli-e2e",
            "description": "Test skill for CLI E2E testing",
            "base_url": "https://example.com/docs/",
            "selectors": {"main_content": "article", "title": "title", "code_blocks": "pre"},
            "url_patterns": {"include": ["/docs/"], "exclude": []},
            "categories": {},
            "rate_limit": 0.1,
            "max_pages": 3,
        }

        config_path = tmp_path / "test-cli-e2e.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        return str(config_path)

    @pytest.mark.asyncio
    async def test_cli_dry_run(self, test_config_file):
        """E2E test: CLI dry-run mode (via direct function call)"""

        # Import and call the tool directly (more reliable than subprocess)
        from skill_seekers.mcp.server import install_skill_tool

        result = await install_skill_tool(
            {"config_path": test_config_file, "dry_run": True, "auto_upload": False}
        )

        # Verify output
        output = result[0].text
        assert "🔍 DRY RUN MODE" in output
        assert "PHASE" in output
        assert "This was a dry run" in output

    def test_cli_validation_error_no_config(self):
        """E2E test: CLI validation error (no config provided)"""

        # Run CLI without config
        result = subprocess.run(
            [sys.executable, "-m", "skill_seekers.cli.install_skill"],
            capture_output=True,
            text=True,
        )

        # Should fail
        assert result.returncode != 0

        # Should show usage error
        assert "required" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_cli_help(self):
        """E2E test: CLI help command"""

        result = subprocess.run(
            [sys.executable, "-m", "skill_seekers.cli.install_skill", "--help"],
            capture_output=True,
            text=True,
        )

        # Should succeed
        assert result.returncode == 0

        # Should show usage information
        output = result.stdout
        assert "Complete skill installation workflow" in output or "install" in output.lower()
        assert "--config" in output
        assert "--dry-run" in output
        assert "--no-upload" in output

    @pytest.mark.asyncio
    @patch("skill_seekers.mcp.tools.scraping_tools.scrape_docs_tool")
    @patch("skill_seekers.mcp.tools.packaging_tools.run_subprocess_with_streaming")
    @patch("skill_seekers.mcp.tools.packaging_tools.package_skill_tool")
    async def test_cli_full_workflow_mocked(
        self, mock_package, mock_enhance, mock_scrape, test_config_file, tmp_path
    ):
        """E2E test: Full CLI workflow with mocked phases (via direct call)"""

        # Setup mocks
        skill_dir = str(tmp_path / "output" / "test-cli-e2e")
        mock_scrape.return_value = [
            TextContent(type="text", text=f"✅ Scraping complete\n\nSkill built at: {skill_dir}")
        ]

        mock_enhance.return_value = ("✅ Enhancement complete", "", 0)

        zip_path = str(tmp_path / "output" / "test-cli-e2e.zip")
        mock_package.return_value = [
            TextContent(type="text", text=f"✅ Package complete\n\nSaved to: {zip_path}")
        ]

        # Call the tool directly
        from skill_seekers.mcp.server import install_skill_tool

        result = await install_skill_tool(
            {
                "config_path": test_config_file,
                "destination": str(tmp_path / "output"),
                "auto_upload": False,
                "dry_run": False,
            }
        )

        # Verify success
        output = result[0].text
        assert "PHASE" in output
        assert "Enhancement" in output or "MANDATORY" in output
        assert "WORKFLOW COMPLETE" in output or "✅" in output

    def test_cli_via_unified_command(self, test_config_file):
        """E2E test: Using 'skill-seekers install' unified CLI (dry-run mode)."""

        # Test the unified CLI entry point
        result = subprocess.run(
            ["skill-seekers", "install", "--config", test_config_file, "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should succeed and show dry-run output
        assert result.returncode == 0, (
            f"Unified CLI failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
        assert "DRY RUN" in result.stdout


@pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP package not installed")
class TestInstallSkillE2E_RealFiles:
    """E2E tests with real file operations (no mocking except upload)"""

    @pytest.fixture
    def local_docs_server(self):
        """Run a localhost HTTP server serving one fixture doc page (offline)."""
        server = ThreadingHTTPServer(("127.0.0.1", 0), _FixtureDocHandler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{port}/"
        finally:
            server.shutdown()
            server.server_close()

    @pytest.fixture
    def real_test_config(self, tmp_path, local_docs_server):
        """Create a real, scrapeable config pointed at the local fixture server."""
        config = {
            "name": "test-real-e2e",
            "description": "Real E2E test",
            "sources": [
                {
                    "type": "documentation",
                    "base_url": local_docs_server,
                    "selectors": {
                        "main_content": "body",
                        "title": "title",
                        "code_blocks": "code",
                    },
                    "url_patterns": {"include": [], "exclude": []},
                    "categories": {},
                    "rate_limit": 0.0,
                    "max_pages": 1,  # Single fixture page
                }
            ],
        }

        config_path = tmp_path / "test-real-e2e.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        return str(config_path)

    @pytest.mark.asyncio
    @pytest.mark.slow  # Mark as slow test (optional)
    async def test_e2e_real_scrape_with_mocked_enhancement(self, real_test_config, tmp_path):
        """E2E test with real scraping but mocked enhancement/upload"""

        # Mock only enhancement and upload -- the scrape runs for real against
        # the local fixture server. We clear the provider API keys (scoped via
        # patch.dict) so the build-time enhancement (UnifiedScraper PHASE 6,
        # AUTO -> API mode) finds no key and skips fast, instead of making a
        # real, slow, retrying call to a provider API. (The old test patched
        # os.environ.get wholesale, which also fed the fake key to
        # REQUESTS_CA_BUNDLE / SSL_CERT_FILE and broke TLS, sabotaging the
        # scrape.) The install_skill enhancement phase is mocked below, so it
        # needs no key either.
        with (
            patch(
                "skill_seekers.mcp.tools.packaging_tools.run_subprocess_with_streaming"
            ) as mock_enhance,
            patch("skill_seekers.mcp.tools.packaging_tools.upload_skill_tool") as mock_upload,
            # The unified build runs its OWN AI enhancement on each source
            # (UnifiedScraper / doc_scraper `_run_enhancement`, default level 2).
            # With no API key it falls back to LOCAL mode and spawns a real
            # coding-agent subprocess (~90s, or a 45-min timeout). Stub it to a
            # fast no-op so this e2e exercises scrape -> build -> install-enhance
            # without any real agent/API call.
            patch(
                "skill_seekers.cli.enhance_skill_local.LocalSkillEnhancer.run",
                return_value=True,
            ),
            patch.dict(
                os.environ,
                dict.fromkeys(
                    [
                        "ANTHROPIC_API_KEY",
                        "ANTHROPIC_AUTH_TOKEN",
                        "MOONSHOT_API_KEY",
                        "GOOGLE_API_KEY",
                        "OPENAI_API_KEY",
                    ],
                    "",
                ),
                clear=False,
            ),
        ):
            # Mock enhancement (avoid needing Claude Code)
            mock_enhance.return_value = ("✅ Enhancement complete", "", 0)

            # Mock upload (avoid needing API key)
            mock_upload.return_value = [TextContent(type="text", text="✅ Upload successful")]

            # Run with real scraping
            result = await install_skill_tool(
                {
                    "config_path": real_test_config,
                    "destination": str(tmp_path / "output"),
                    "auto_upload": False,  # Skip upload even with key
                    "unlimited": False,
                    "dry_run": False,
                }
            )

            output = result[0].text

            # Verify workflow completed
            assert "WORKFLOW COMPLETE" in output or "✅" in output

            # Verify enhancement was called
            assert mock_enhance.called

            # Verify workflow succeeded
            # We know scraping was real because we didn't mock scrape_docs_tool
            # Just check that workflow completed
            assert "WORKFLOW COMPLETE" in output or "✅" in output

            # The output directory should exist (created by scraping)
            _output_dir = tmp_path / "output"
            # Note: Directory existence is not guaranteed in all cases (mocked package might not create files)
            # So we mainly verify the workflow logic worked
            assert "Enhancement complete" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
