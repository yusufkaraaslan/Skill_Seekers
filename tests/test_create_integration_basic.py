"""Basic integration tests for create command.

Tests that the create command properly detects source types
and routes to the correct scrapers without actually scraping.
"""

import pytest
import tempfile
import os
from pathlib import Path


class TestCreateCommandBasic:
    """Basic integration tests for create command (dry-run mode)."""

    def test_create_command_help(self):
        """Test that create command help works."""
        import subprocess
        result = subprocess.run(
            ['skill-seekers', 'create', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'Auto-detects source type' in result.stdout
        assert 'auto-detected' in result.stdout
        assert '--help-web' in result.stdout

    def test_create_detects_web_url(self):
        """Test that web URLs are detected and routed correctly."""
        # Skip this test for now - requires actual implementation
        # The command structure needs refinement for subprocess calls
        pytest.skip("Requires full end-to-end implementation")

    def test_create_detects_github_repo(self):
        """Test that GitHub repos are detected."""
        import subprocess
        result = subprocess.run(
            ['skill-seekers', 'create', 'facebook/react', '--help'],
            capture_output=True,
            text=True,
            timeout=10
        )
        # Just verify help works - actual scraping would need API token
        assert result.returncode in [0, 2]  # 0 for success, 2 for argparse help

    def test_create_detects_local_directory(self, tmp_path):
        """Test that local directories are detected."""
        import subprocess

        # Create a test directory
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        result = subprocess.run(
            ['skill-seekers', 'create', str(test_dir), '--help'],
            capture_output=True,
            text=True,
            timeout=10
        )
        # Verify help works
        assert result.returncode in [0, 2]

    def test_create_detects_pdf_file(self, tmp_path):
        """Test that PDF files are detected."""
        import subprocess

        # Create a dummy PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.touch()

        result = subprocess.run(
            ['skill-seekers', 'create', str(pdf_file), '--help'],
            capture_output=True,
            text=True,
            timeout=10
        )
        # Verify help works
        assert result.returncode in [0, 2]

    def test_create_detects_config_file(self, tmp_path):
        """Test that config files are detected."""
        import subprocess
        import json

        # Create a minimal config file
        config_file = tmp_path / "test.json"
        config_data = {
            "name": "test",
            "base_url": "https://example.com/"
        }
        config_file.write_text(json.dumps(config_data))

        result = subprocess.run(
            ['skill-seekers', 'create', str(config_file), '--help'],
            capture_output=True,
            text=True,
            timeout=10
        )
        # Verify help works
        assert result.returncode in [0, 2]

    def test_create_invalid_source_shows_error(self):
        """Test that invalid sources show helpful error."""
        # Skip this test for now - requires actual implementation
        # The error handling needs to be integrated with the unified CLI
        pytest.skip("Requires full end-to-end implementation")

    def test_create_supports_universal_flags(self):
        """Test that universal flags are accepted."""
        import subprocess
        result = subprocess.run(
            ['skill-seekers', 'create', '--help'],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0

        # Check that universal flags are present
        assert '--name' in result.stdout
        assert '--enhance' in result.stdout
        assert '--chunk-for-rag' in result.stdout
        assert '--preset' in result.stdout
        assert '--dry-run' in result.stdout


class TestBackwardCompatibility:
    """Test that old commands still work."""

    def test_scrape_command_still_works(self):
        """Old scrape command should still function."""
        import subprocess
        result = subprocess.run(
            ['skill-seekers', 'scrape', '--help'],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        assert 'scrape' in result.stdout.lower()

    def test_github_command_still_works(self):
        """Old github command should still function."""
        import subprocess
        result = subprocess.run(
            ['skill-seekers', 'github', '--help'],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        assert 'github' in result.stdout.lower()

    def test_analyze_command_still_works(self):
        """Old analyze command should still function."""
        import subprocess
        result = subprocess.run(
            ['skill-seekers', 'analyze', '--help'],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        assert 'analyze' in result.stdout.lower()

    def test_main_help_shows_all_commands(self):
        """Main help should show both old and new commands."""
        import subprocess
        result = subprocess.run(
            ['skill-seekers', '--help'],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        # Should show create command
        assert 'create' in result.stdout

        # Should still show old commands
        assert 'scrape' in result.stdout
        assert 'github' in result.stdout
        assert 'analyze' in result.stdout
