"""Tests for skill-seekers doctor command (#316)."""

from __future__ import annotations

import os
from unittest.mock import patch

from skill_seekers.cli.doctor import (
    CheckResult,
    check_api_keys,
    check_core_deps,
    check_git,
    check_mcp_server,
    check_optional_deps,
    check_output_directory,
    check_package_installed,
    check_python_version,
    print_report,
    run_all_checks,
)


class TestCheckPythonVersion:
    def test_passes_on_current_python(self):
        result = check_python_version()
        assert result.status == "pass"
        assert result.critical is True

    def test_detail_contains_version(self):
        result = check_python_version()
        assert "." in result.detail  # e.g. "3.14.3"


class TestCheckPackageInstalled:
    def test_passes_when_installed(self):
        result = check_package_installed()
        assert result.status == "pass"
        assert result.detail.startswith("v")

    def test_fails_when_import_broken(self):
        with (
            patch.dict("sys.modules", {"skill_seekers._version": None}),
            patch("builtins.__import__", side_effect=ImportError("mocked")),
        ):
            result = check_package_installed()
            assert result.status == "fail"


class TestCheckGit:
    def test_passes_when_git_available(self):
        result = check_git()
        # Most CI/dev environments have git
        assert result.status in ("pass", "warn")

    def test_warns_when_git_missing(self):
        with patch("skill_seekers.cli.doctor.shutil.which", return_value=None):
            result = check_git()
            assert result.status == "warn"


class TestCheckCoreDeps:
    def test_passes_in_normal_environment(self):
        result = check_core_deps()
        assert result.status == "pass"
        assert result.critical is True

    def test_detail_shows_count(self):
        result = check_core_deps()
        assert "found" in result.detail.lower() or "missing" in result.detail.lower()


class TestCheckOptionalDeps:
    def test_returns_result(self):
        result = check_optional_deps()
        assert result.status in ("pass", "warn")
        assert "/" in result.detail  # e.g. "7/10 installed"


class TestCheckApiKeys:
    def test_warns_when_no_keys(self):
        with patch.dict(os.environ, {}, clear=True):
            result = check_api_keys()
            assert result.status == "warn"

    def test_passes_when_all_set(self):
        env = {
            "ANTHROPIC_API_KEY": "sk-ant-test123456789",
            "GITHUB_TOKEN": "ghp_test123456789",
            "GOOGLE_API_KEY": "AIza_test123456789",
            "OPENAI_API_KEY": "sk-test123456789",
            "MOONSHOT_API_KEY": "sk-moon-test123456789",
        }
        with patch.dict(os.environ, env, clear=True):
            result = check_api_keys()
            assert result.status == "pass"

    def test_partial_keys_warns(self):
        env = {"ANTHROPIC_API_KEY": "sk-ant-test123456789"}
        with patch.dict(os.environ, env, clear=True):
            result = check_api_keys()
            assert result.status == "warn"
            assert "1 set" in result.detail


class TestCheckMcpServer:
    def test_returns_result(self):
        result = check_mcp_server()
        assert result.status in ("pass", "warn")


class TestCheckOutputDirectory:
    def test_passes_in_writable_dir(self):
        result = check_output_directory()
        assert result.status == "pass"
        assert result.critical is True


class TestRunAllChecks:
    def test_returns_8_results(self):
        results = run_all_checks()
        assert len(results) == 8

    def test_all_have_name_and_status(self):
        results = run_all_checks()
        for r in results:
            assert isinstance(r, CheckResult)
            assert r.name
            assert r.status in ("pass", "warn", "fail")


class TestPrintReport:
    def test_returns_0_when_no_failures(self, capsys):
        results = [
            CheckResult("Test1", "pass", "ok", critical=True),
            CheckResult("Test2", "warn", "meh"),
        ]
        code = print_report(results)
        assert code == 0
        captured = capsys.readouterr()
        assert "1 passed" in captured.out
        assert "1 warnings" in captured.out

    def test_returns_1_when_critical_failure(self, capsys):
        results = [
            CheckResult("Test1", "pass", "ok"),
            CheckResult("Test2", "fail", "broken", critical=True),
        ]
        code = print_report(results)
        assert code == 1

    def test_verbose_shows_detail(self, capsys):
        results = [
            CheckResult("Test1", "pass", "ok", verbose_detail="  extra: info"),
        ]
        print_report(results, verbose=True)
        captured = capsys.readouterr()
        assert "extra: info" in captured.out

    def test_no_verbose_hides_detail(self, capsys):
        results = [
            CheckResult("Test1", "pass", "ok", verbose_detail="  secret: hidden"),
        ]
        print_report(results, verbose=False)
        captured = capsys.readouterr()
        assert "secret: hidden" not in captured.out
