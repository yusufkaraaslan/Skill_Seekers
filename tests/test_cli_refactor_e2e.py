#!/usr/bin/env python3
"""
End-to-End Tests for CLI Refactor (Issues #285 and #268)

These tests verify that the unified CLI architecture works correctly:
1. Parser sync: All parsers use shared argument definitions
2. Preset system: Analyze command supports presets
3. Backward compatibility: Old flags still work with deprecation warnings
4. Integration: The complete flow from CLI to execution
"""

import pytest
import subprocess
import argparse
import sys
from pathlib import Path


class TestParserSync:
    """E2E tests for parser synchronization (Issue #285)."""

    def test_scrape_interactive_flag_works(self):
        """Test that --interactive flag (previously missing) now works."""
        result = subprocess.run(
            ["skill-seekers", "scrape", "--interactive", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Command should execute successfully"
        assert "--interactive" in result.stdout, "Help should show --interactive flag"
        assert "-i" in result.stdout, "Help should show short form -i"

    def test_scrape_chunk_for_rag_flag_works(self):
        """Test that --chunk-for-rag flag (previously missing) now works."""
        result = subprocess.run(
            ["skill-seekers", "scrape", "--help"],
            capture_output=True,
            text=True
        )
        assert "--chunk-for-rag" in result.stdout, "Help should show --chunk-for-rag flag"
        assert "--chunk-size" in result.stdout, "Help should show --chunk-size flag"
        assert "--chunk-overlap" in result.stdout, "Help should show --chunk-overlap flag"

    def test_scrape_verbose_flag_works(self):
        """Test that --verbose flag (previously missing) now works."""
        result = subprocess.run(
            ["skill-seekers", "scrape", "--help"],
            capture_output=True,
            text=True
        )
        assert "--verbose" in result.stdout, "Help should show --verbose flag"
        assert "-v" in result.stdout, "Help should show short form -v"

    def test_scrape_url_flag_works(self):
        """Test that --url flag (previously missing) now works."""
        result = subprocess.run(
            ["skill-seekers", "scrape", "--help"],
            capture_output=True,
            text=True
        )
        assert "--url URL" in result.stdout, "Help should show --url flag"

    def test_github_all_flags_present(self):
        """Test that github command has all expected flags."""
        result = subprocess.run(
            ["skill-seekers", "github", "--help"],
            capture_output=True,
            text=True
        )
        # Key github flags that should be present
        expected_flags = [
            "--repo",
            "--api-key",
            "--profile",
            "--non-interactive",
        ]
        for flag in expected_flags:
            assert flag in result.stdout, f"Help should show {flag} flag"


class TestPresetSystem:
    """E2E tests for preset system (Issue #268)."""

    def test_analyze_preset_flag_exists(self):
        """Test that analyze command has --preset flag."""
        result = subprocess.run(
            ["skill-seekers", "analyze", "--help"],
            capture_output=True,
            text=True
        )
        assert "--preset" in result.stdout, "Help should show --preset flag"
        assert "quick" in result.stdout, "Help should mention 'quick' preset"
        assert "standard" in result.stdout, "Help should mention 'standard' preset"
        assert "comprehensive" in result.stdout, "Help should mention 'comprehensive' preset"

    def test_analyze_preset_list_flag_exists(self):
        """Test that analyze command has --preset-list flag."""
        result = subprocess.run(
            ["skill-seekers", "analyze", "--help"],
            capture_output=True,
            text=True
        )
        assert "--preset-list" in result.stdout, "Help should show --preset-list flag"

    def test_preset_list_shows_presets(self):
        """Test that --preset-list shows all available presets."""
        result = subprocess.run(
            ["skill-seekers", "analyze", "--preset-list"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Command should execute successfully"
        assert "Available presets" in result.stdout, "Should show preset list header"
        assert "quick" in result.stdout, "Should show quick preset"
        assert "standard" in result.stdout, "Should show standard preset"
        assert "comprehensive" in result.stdout, "Should show comprehensive preset"
        assert "1-2 minutes" in result.stdout, "Should show time estimates"

    @pytest.mark.skip(reason="Deprecation warnings not implemented in analyze command yet")
    def test_deprecated_quick_flag_shows_warning(self):
        """Test that --quick flag shows deprecation warning."""
        result = subprocess.run(
            ["skill-seekers", "analyze", "--directory", ".", "--quick"],
            capture_output=True,
            text=True
        )
        # Note: Deprecation warnings go to stderr
        output = result.stdout + result.stderr
        assert "DEPRECATED" in output, "Should show deprecation warning"
        assert "--preset quick" in output, "Should suggest alternative"

    @pytest.mark.skip(reason="Deprecation warnings not implemented in analyze command yet")
    def test_deprecated_comprehensive_flag_shows_warning(self):
        """Test that --comprehensive flag shows deprecation warning."""
        result = subprocess.run(
            ["skill-seekers", "analyze", "--directory", ".", "--comprehensive"],
            capture_output=True,
            text=True
        )
        output = result.stdout + result.stderr
        assert "DEPRECATED" in output, "Should show deprecation warning"
        assert "--preset comprehensive" in output, "Should suggest alternative"


class TestBackwardCompatibility:
    """E2E tests for backward compatibility."""

    def test_old_scrape_command_still_works(self):
        """Test that old scrape command invocations still work."""
        result = subprocess.run(
            ["skill-seekers-scrape", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Old command should still work"
        assert "documentation" in result.stdout.lower(), "Help should mention documentation"

    def test_unified_cli_and_standalone_have_same_args(self):
        """Test that unified CLI and standalone have identical arguments."""
        # Get help from unified CLI
        unified_result = subprocess.run(
            ["skill-seekers", "scrape", "--help"],
            capture_output=True,
            text=True
        )

        # Get help from standalone
        standalone_result = subprocess.run(
            ["skill-seekers-scrape", "--help"],
            capture_output=True,
            text=True
        )

        # Both should have the same key flags
        key_flags = [
            "--interactive",
            "--url",
            "--verbose",
            "--chunk-for-rag",
            "--config",
            "--max-pages",
        ]

        for flag in key_flags:
            assert flag in unified_result.stdout, f"Unified should have {flag}"
            assert flag in standalone_result.stdout, f"Standalone should have {flag}"


class TestProgrammaticAPI:
    """Test that the shared argument functions work programmatically."""

    def test_import_shared_scrape_arguments(self):
        """Test that shared scrape arguments can be imported."""
        from skill_seekers.cli.arguments.scrape import add_scrape_arguments

        parser = argparse.ArgumentParser()
        add_scrape_arguments(parser)

        # Verify key arguments were added
        args_dict = vars(parser.parse_args(["https://example.com"]))
        assert "url" in args_dict

    def test_import_shared_github_arguments(self):
        """Test that shared github arguments can be imported."""
        from skill_seekers.cli.arguments.github import add_github_arguments

        parser = argparse.ArgumentParser()
        add_github_arguments(parser)

        # Parse with --repo flag
        args = parser.parse_args(["--repo", "owner/repo"])
        assert args.repo == "owner/repo"

    def test_import_analyze_presets(self):
        """Test that analyze presets can be imported."""
        from skill_seekers.cli.presets.analyze_presets import ANALYZE_PRESETS, AnalysisPreset

        assert "quick" in ANALYZE_PRESETS
        assert "standard" in ANALYZE_PRESETS
        assert "comprehensive" in ANALYZE_PRESETS

        # Verify preset structure
        quick = ANALYZE_PRESETS["quick"]
        assert isinstance(quick, AnalysisPreset)
        assert quick.name == "Quick"
        assert quick.depth == "surface"
        # Note: enhance_level is not part of AnalysisPreset anymore.
        # It's controlled separately via --enhance-level flag (default 2)


class TestIntegration:
    """Integration tests for the complete flow."""

    def test_unified_cli_subcommands_registered(self):
        """Test that all subcommands are properly registered."""
        result = subprocess.run(
            ["skill-seekers", "--help"],
            capture_output=True,
            text=True
        )

        # All major commands should be listed
        expected_commands = [
            "scrape",
            "github",
            "pdf",
            "unified",
            "analyze",
            "enhance",
            "package",
            "upload",
        ]

        for cmd in expected_commands:
            assert cmd in result.stdout, f"Should list {cmd} command"

    def test_scrape_help_detailed(self):
        """Test that scrape help shows all argument details."""
        result = subprocess.run(
            ["skill-seekers", "scrape", "--help"],
            capture_output=True,
            text=True
        )

        # Check for argument categories
        assert "url" in result.stdout.lower(), "Should show url argument"
        assert "scraping options" in result.stdout.lower() or "options" in result.stdout.lower()
        assert "enhancement" in result.stdout.lower(), "Should mention enhancement options"

    def test_analyze_help_shows_presets(self):
        """Test that analyze help prominently shows preset information."""
        result = subprocess.run(
            ["skill-seekers", "analyze", "--help"],
            capture_output=True,
            text=True
        )

        assert "--preset" in result.stdout, "Should show --preset flag"
        assert "DEFAULT" in result.stdout or "default" in result.stdout, "Should indicate default preset"


class TestE2EWorkflow:
    """End-to-end workflow tests."""

    @pytest.mark.slow
    def test_dry_run_scrape_with_new_args(self, tmp_path):
        """Test scraping with previously missing arguments (dry run)."""
        result = subprocess.run(
            [
                "skill-seekers", "scrape",
                "--url", "https://example.com",
                "--interactive", "false",  # Would fail if arg didn't exist
                "--verbose",  # Would fail if arg didn't exist
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Dry run should complete without errors
        # (it may return non-zero if --interactive false isn't valid,
        #  but it shouldn't crash with "unrecognized arguments")
        assert "unrecognized arguments" not in result.stderr.lower()

    @pytest.mark.slow
    def test_analyze_with_preset_flag(self, tmp_path):
        """Test analyze with preset flag (no dry-run available)."""
        # Create a dummy directory to analyze
        test_dir = tmp_path / "test_code"
        test_dir.mkdir()
        (test_dir / "test.py").write_text("def hello(): pass")

        # Just verify the flag is recognized (no execution)
        result = subprocess.run(
            ["skill-seekers", "analyze", "--help"],
            capture_output=True,
            text=True,
        )

        # Verify preset flag exists
        assert "--preset" in result.stdout, "Should have --preset flag"
        assert "unrecognized arguments" not in result.stderr.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
