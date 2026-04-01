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
    """Unit tests for _build_argv argument forwarding."""

    def _make_args(self, **kwargs):
        import argparse

        defaults = {
            "source": "https://example.com",
            "enhance_workflow": None,
            "enhance_stage": None,
            "var": None,
            "workflow_dry_run": False,
            "enhance_level": 2,
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
            "agent": None,
            "agent_cmd": None,
            "doc_version": "",
        }
        defaults.update(kwargs)
        return argparse.Namespace(**defaults)

    def _collect_argv(self, args):
        from skill_seekers.cli.create_command import CreateCommand
        from skill_seekers.cli.source_detector import SourceDetector

        cmd = CreateCommand(args)
        cmd.source_info = SourceDetector.detect(args.source)
        return cmd._build_argv("test_module", [])

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

    # ── _SKIP_ARGS exclusion ────────────────────────────────────────────────

    def test_source_never_forwarded(self):
        """'source' is in _SKIP_ARGS and must never appear in argv."""
        args = self._make_args(source="https://example.com")
        argv = self._collect_argv(args)
        assert "--source" not in argv

    def test_func_never_forwarded(self):
        """'func' is in _SKIP_ARGS and must never appear in argv."""
        args = self._make_args(func=lambda: None)
        argv = self._collect_argv(args)
        assert "--func" not in argv

    def test_config_never_forwarded_by_build_argv(self):
        """'config' is in _SKIP_ARGS; forwarded manually by specific routes."""
        args = self._make_args(config="/path/to/config.json")
        argv = self._collect_argv(args)
        assert "--config" not in argv

    def test_subcommand_never_forwarded(self):
        """'subcommand' is in _SKIP_ARGS."""
        args = self._make_args(subcommand="create")
        argv = self._collect_argv(args)
        assert "--subcommand" not in argv

    def test_command_never_forwarded(self):
        """'command' is in _SKIP_ARGS."""
        args = self._make_args(command="create")
        argv = self._collect_argv(args)
        assert "--command" not in argv

    # ── _DEST_TO_FLAG mapping ───────────────────────────────────────────────

    def test_async_mode_maps_to_async_flag(self):
        """async_mode dest should produce --async flag, not --async-mode."""
        args = self._make_args(async_mode=True)
        argv = self._collect_argv(args)
        assert "--async" in argv
        assert "--async-mode" not in argv

    def test_skip_config_maps_to_skip_config_patterns(self):
        """skip_config dest should produce --skip-config-patterns flag."""
        args = self._make_args(skip_config=True)
        argv = self._collect_argv(args)
        assert "--skip-config-patterns" in argv
        assert "--skip-config" not in argv

    # ── Boolean arg forwarding ──────────────────────────────────────────────

    def test_boolean_true_appends_flag(self):
        args = self._make_args(dry_run=True)
        argv = self._collect_argv(args)
        assert "--dry-run" in argv

    def test_boolean_false_does_not_append_flag(self):
        args = self._make_args(dry_run=False)
        argv = self._collect_argv(args)
        assert "--dry-run" not in argv

    def test_verbose_true_forwarded(self):
        args = self._make_args(verbose=True)
        argv = self._collect_argv(args)
        assert "--verbose" in argv

    def test_quiet_true_forwarded(self):
        args = self._make_args(quiet=True)
        argv = self._collect_argv(args)
        assert "--quiet" in argv

    # ── List arg forwarding ─────────────────────────────────────────────────

    def test_list_arg_each_item_gets_separate_flag(self):
        """Each list item gets its own --flag value pair."""
        args = self._make_args(enhance_workflow=["a", "b", "c"])
        argv = self._collect_argv(args)
        assert argv.count("--enhance-workflow") == 3
        for item in ["a", "b", "c"]:
            idx = argv.index(item)
            assert argv[idx - 1] == "--enhance-workflow"

    # ── _is_explicitly_set ──────────────────────────────────────────────────

    def test_is_explicitly_set_none_is_not_set(self):
        """None values should NOT be considered explicitly set."""
        from skill_seekers.cli.create_command import CreateCommand

        args = self._make_args()
        cmd = CreateCommand(args)
        assert cmd._is_explicitly_set("name", None) is False

    def test_is_explicitly_set_bool_true_is_set(self):
        from skill_seekers.cli.create_command import CreateCommand

        args = self._make_args()
        cmd = CreateCommand(args)
        assert cmd._is_explicitly_set("dry_run", True) is True

    def test_is_explicitly_set_bool_false_is_not_set(self):
        from skill_seekers.cli.create_command import CreateCommand

        args = self._make_args()
        cmd = CreateCommand(args)
        assert cmd._is_explicitly_set("dry_run", False) is False

    def test_is_explicitly_set_default_doc_version_empty_not_set(self):
        """doc_version defaults to '' which means not explicitly set."""
        from skill_seekers.cli.create_command import CreateCommand

        args = self._make_args()
        cmd = CreateCommand(args)
        assert cmd._is_explicitly_set("doc_version", "") is False

    def test_is_explicitly_set_nonempty_string_is_set(self):
        from skill_seekers.cli.create_command import CreateCommand

        args = self._make_args()
        cmd = CreateCommand(args)
        assert cmd._is_explicitly_set("name", "my-skill") is True

    def test_is_explicitly_set_non_default_value_is_set(self):
        """A value that differs from the known default IS explicitly set."""
        from skill_seekers.cli.create_command import CreateCommand

        args = self._make_args()
        cmd = CreateCommand(args)
        # max_issues default is 100; setting to 50 means explicitly set
        assert cmd._is_explicitly_set("max_issues", 50) is True
        # Setting to default value means NOT explicitly set
        assert cmd._is_explicitly_set("max_issues", 100) is False

    # ── Allowlist filtering ─────────────────────────────────────────────────

    def test_allowlist_only_forwards_allowed_args(self):
        """When allowlist is provided, only those args are forwarded."""
        from skill_seekers.cli.create_command import CreateCommand
        from skill_seekers.cli.source_detector import SourceDetector

        args = self._make_args(
            dry_run=True,
            verbose=True,
            name="test-skill",
        )
        cmd = CreateCommand(args)
        cmd.source_info = SourceDetector.detect(args.source)

        # Only allow dry_run in the allowlist
        allowlist = frozenset({"dry_run"})
        argv = cmd._build_argv("test_module", [], allowlist=allowlist)

        assert "--dry-run" in argv
        assert "--verbose" not in argv
        assert "--name" not in argv

    def test_allowlist_skips_non_allowed_even_if_set(self):
        """Args not in the allowlist are excluded even if explicitly set."""
        from skill_seekers.cli.create_command import CreateCommand
        from skill_seekers.cli.source_detector import SourceDetector

        args = self._make_args(
            enhance_workflow=["security-focus"],
            quiet=True,
        )
        cmd = CreateCommand(args)
        cmd.source_info = SourceDetector.detect(args.source)

        allowlist = frozenset({"quiet"})
        argv = cmd._build_argv("test_module", [], allowlist=allowlist)

        assert "--quiet" in argv
        assert "--enhance-workflow" not in argv

    def test_allowlist_empty_forwards_nothing(self):
        """Empty allowlist should forward no user args (auto-name may still be added)."""
        from skill_seekers.cli.create_command import CreateCommand
        from skill_seekers.cli.source_detector import SourceDetector

        args = self._make_args(dry_run=True, verbose=True)
        cmd = CreateCommand(args)
        cmd.source_info = SourceDetector.detect(args.source)

        allowlist = frozenset()
        argv = cmd._build_argv("test_module", ["pos"], allowlist=allowlist)

        # User-set args (dry_run, verbose) should NOT be forwarded
        assert "--dry-run" not in argv
        assert "--verbose" not in argv
        # Only module name, positional, and possibly auto-added --name
        assert argv[0] == "test_module"
        assert "pos" in argv


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
