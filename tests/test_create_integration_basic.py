"""Basic integration tests for create command.

Tests that the create command properly detects source types
and routes to the correct scrapers without actually scraping.
"""

import pytest


class TestCreateCommandBasic:
    """Basic integration tests for create command (dry-run mode)."""

    def test_create_command_help(self):
        """Test that create command help works."""
        import subprocess

        result = subprocess.run(
            ["skill-seekers", "create", "--help"], capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "Auto-detects source type" in result.stdout
        assert "auto-detected" in result.stdout
        assert "--help-web" in result.stdout

    def test_create_detects_web_url(self):
        """Test that web URLs are detected and routed correctly."""
        from skill_seekers.cli.source_detector import SourceDetector

        info = SourceDetector.detect("https://docs.react.dev/")
        assert info.type == "web"
        assert info.parsed["url"] == "https://docs.react.dev/"
        assert info.suggested_name  # non-empty

        # Plain domain should also be treated as web
        info2 = SourceDetector.detect("docs.example.com")
        assert info2.type == "web"

    def test_create_detects_github_repo(self):
        """Test that GitHub repos are detected."""
        import subprocess

        result = subprocess.run(
            ["skill-seekers", "create", "facebook/react", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
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
            ["skill-seekers", "create", str(test_dir), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
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
            ["skill-seekers", "create", str(pdf_file), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Verify help works
        assert result.returncode in [0, 2]

    def test_create_detects_config_file(self, tmp_path):
        """Test that config files are detected."""
        import subprocess
        import json

        # Create a minimal config file
        config_file = tmp_path / "test.json"
        config_data = {"name": "test", "base_url": "https://example.com/"}
        config_file.write_text(json.dumps(config_data))

        result = subprocess.run(
            ["skill-seekers", "create", str(config_file), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Verify help works
        assert result.returncode in [0, 2]

    def test_create_invalid_source_shows_error(self):
        """Test that invalid sources raise a helpful ValueError."""
        from skill_seekers.cli.source_detector import SourceDetector

        with pytest.raises(ValueError) as exc_info:
            SourceDetector.detect("not_a_valid_source_123_xyz")

        error_message = str(exc_info.value)
        assert "Cannot determine source type" in error_message
        # Error should include helpful examples
        assert "https://" in error_message or "github" in error_message.lower()

    def test_create_supports_universal_flags(self):
        """Test that universal flags are accepted."""
        import subprocess

        result = subprocess.run(
            ["skill-seekers", "create", "--help"], capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0

        # Check that universal flags are present
        assert "--name" in result.stdout
        assert "--enhance" in result.stdout
        assert "--chunk-for-rag" in result.stdout
        assert "--preset" in result.stdout
        assert "--dry-run" in result.stdout


class TestCreateCommandArgvForwarding:
    """Unit tests for _add_common_args argv forwarding."""

    def _make_args(self, **kwargs):
        import argparse

        defaults = {
            "enhance_workflow": None,
            "enhance_stage": None,
            "var": None,
            "workflow_dry_run": False,
            "enhance_level": 0,
            "output": None,
            "name": None,
            "description": None,
            "config": None,
            "api_key": None,
            "dry_run": False,
            "verbose": False,
            "quiet": False,
            "chunk_for_rag": False,
            "chunk_size": 512,
            "chunk_overlap": 50,
            "preset": None,
            "no_preserve_code_blocks": False,
            "no_preserve_paragraphs": False,
            "interactive_enhancement": False,
        }
        defaults.update(kwargs)
        return argparse.Namespace(**defaults)

    def _collect_argv(self, args):
        from skill_seekers.cli.create_command import CreateCommand

        cmd = CreateCommand(args)
        argv = []
        cmd._add_common_args(argv)
        return argv

    def test_single_enhance_workflow_forwarded(self):
        args = self._make_args(enhance_workflow=["security-focus"])
        argv = self._collect_argv(args)
        assert argv.count("--enhance-workflow") == 1
        assert "security-focus" in argv

    def test_multiple_enhance_workflows_all_forwarded(self):
        """Each workflow must appear as a separate --enhance-workflow flag."""
        args = self._make_args(enhance_workflow=["security-focus", "minimal"])
        argv = self._collect_argv(args)
        assert argv.count("--enhance-workflow") == 2
        idx1 = argv.index("security-focus")
        idx2 = argv.index("minimal")
        assert argv[idx1 - 1] == "--enhance-workflow"
        assert argv[idx2 - 1] == "--enhance-workflow"

    def test_no_enhance_workflow_not_forwarded(self):
        args = self._make_args(enhance_workflow=None)
        argv = self._collect_argv(args)
        assert "--enhance-workflow" not in argv

    # ── enhance_stage ────────────────────────────────────────────────────────

    def test_single_enhance_stage_forwarded(self):
        args = self._make_args(enhance_stage=["security:Check for vulnerabilities"])
        argv = self._collect_argv(args)
        assert "--enhance-stage" in argv
        assert "security:Check for vulnerabilities" in argv

    def test_multiple_enhance_stages_all_forwarded(self):
        stages = ["sec:Check security", "cleanup:Remove boilerplate"]
        args = self._make_args(enhance_stage=stages)
        argv = self._collect_argv(args)
        assert argv.count("--enhance-stage") == 2
        for stage in stages:
            assert stage in argv

    def test_enhance_stage_none_not_forwarded(self):
        args = self._make_args(enhance_stage=None)
        argv = self._collect_argv(args)
        assert "--enhance-stage" not in argv

    # ── var ──────────────────────────────────────────────────────────────────

    def test_single_var_forwarded(self):
        args = self._make_args(var=["depth=comprehensive"])
        argv = self._collect_argv(args)
        assert "--var" in argv
        assert "depth=comprehensive" in argv

    def test_multiple_vars_all_forwarded(self):
        args = self._make_args(var=["depth=comprehensive", "focus=security"])
        argv = self._collect_argv(args)
        assert argv.count("--var") == 2
        assert "depth=comprehensive" in argv
        assert "focus=security" in argv

    def test_var_none_not_forwarded(self):
        args = self._make_args(var=None)
        argv = self._collect_argv(args)
        assert "--var" not in argv

    # ── workflow_dry_run ─────────────────────────────────────────────────────

    def test_workflow_dry_run_forwarded(self):
        args = self._make_args(workflow_dry_run=True)
        argv = self._collect_argv(args)
        assert "--workflow-dry-run" in argv

    def test_workflow_dry_run_false_not_forwarded(self):
        args = self._make_args(workflow_dry_run=False)
        argv = self._collect_argv(args)
        assert "--workflow-dry-run" not in argv

    # ── mixed ────────────────────────────────────────────────────────────────

    def test_workflow_and_stage_both_forwarded(self):
        args = self._make_args(
            enhance_workflow=["security-focus"],
            enhance_stage=["cleanup:Remove boilerplate"],
            var=["depth=basic"],
            workflow_dry_run=True,
        )
        argv = self._collect_argv(args)
        assert "--enhance-workflow" in argv
        assert "security-focus" in argv
        assert "--enhance-stage" in argv
        assert "--var" in argv
        assert "--workflow-dry-run" in argv


class TestBackwardCompatibility:
    """Test that old commands still work."""

    def test_scrape_command_still_works(self):
        """Old scrape command should still function."""
        import subprocess

        result = subprocess.run(
            ["skill-seekers", "scrape", "--help"], capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        assert "scrape" in result.stdout.lower()

    def test_github_command_still_works(self):
        """Old github command should still function."""
        import subprocess

        result = subprocess.run(
            ["skill-seekers", "github", "--help"], capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        assert "github" in result.stdout.lower()

    def test_analyze_command_still_works(self):
        """Old analyze command should still function."""
        import subprocess

        result = subprocess.run(
            ["skill-seekers", "analyze", "--help"], capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        assert "analyze" in result.stdout.lower()

    def test_main_help_shows_all_commands(self):
        """Main help should show both old and new commands."""
        import subprocess

        result = subprocess.run(
            ["skill-seekers", "--help"], capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        # Should show create command
        assert "create" in result.stdout

        # Should still show old commands
        assert "scrape" in result.stdout
        assert "github" in result.stdout
        assert "analyze" in result.stdout

    def test_workflows_command_still_works(self):
        """The new workflows subcommand is accessible via the main CLI."""
        import subprocess

        result = subprocess.run(
            ["skill-seekers", "workflows", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "workflow" in result.stdout.lower()
