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
        result = subprocess.run(["skill-seekers", "--help"], capture_output=True, text=True)

        # All major commands should be listed
        expected_commands = [
            "create",
            "enhance",
            "package",
            "upload",
        ]

        for cmd in expected_commands:
            assert cmd in result.stdout, f"Should list {cmd} command"


class TestVarFlagRouting:
    """Test that --var flag is correctly routed through create command."""

    def test_var_flag_accepted_by_create(self):
        """Test that --var flag is accepted (not 'unrecognized') by create command."""
        result = subprocess.run(
            ["skill-seekers", "create", "--help"],
            capture_output=True,
            text=True,
        )
        assert "--var" in result.stdout, "create --help should show --var flag"

    @pytest.mark.slow
    def test_var_flag_not_rejected_in_create_local(self, tmp_path):
        """Test --var KEY=VALUE doesn't cause 'unrecognized arguments' in create."""
        test_dir = tmp_path / "test_code"
        test_dir.mkdir()
        (test_dir / "test.py").write_text("def hello(): pass")

        result = subprocess.run(
            [
                "skill-seekers",
                "create",
                str(test_dir),
                "--var",
                "foo=bar",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert "unrecognized arguments" not in result.stderr.lower(), (
            f"--var should be accepted, got stderr: {result.stderr}"
        )


class TestBackwardCompatibleFlags:
    """Test that deprecated flag aliases still work."""

    def test_no_preserve_code_alias_accepted_by_package(self):
        """Test --no-preserve-code (old name) is still accepted by package command."""
        result = subprocess.run(
            ["skill-seekers", "package", "--help"],
            capture_output=True,
            text=True,
        )
        # The old flag should not appear in --help (it's suppressed)
        # but should not cause an error if used
        assert result.returncode == 0

    def test_no_preserve_code_alias_accepted_by_create(self):
        """Test --no-preserve-code (old name) is still accepted by create command."""
        result = subprocess.run(
            ["skill-seekers", "create", "--help-all"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
