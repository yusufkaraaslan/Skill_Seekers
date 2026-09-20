"""Tests for skill-seekers doctor command (#316)."""

from __future__ import annotations

import json
import os
from argparse import Namespace
from unittest.mock import patch

from skill_seekers.cli.doctor import (
    CheckResult,
    DoctorCommand,
    check_api_keys,
    check_core_deps,
    check_git,
    check_mcp_server,
    check_optional_deps,
    check_output_directory,
    check_package_installed,
    check_python_version,
    main,
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

    def test_set_keys_are_named(self):
        """The summary must name which keys are set, so a bare GITHUB_TOKEN
        isn't misread as an AI provider key being configured."""
        env = {"GITHUB_TOKEN": "ghp_test123456789"}
        with patch.dict(os.environ, env, clear=True):
            result = check_api_keys()
            assert result.status == "warn"
            assert "1 set" in result.detail
            assert "GITHUB_TOKEN" in result.detail


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


class TestJsonReport:
    def test_main_json_forwards_dependency_stdout_to_stderr(self, capsys):
        def noisy_checks():
            print("third-party import warning")
            return [CheckResult("Python version", "pass", "3.12.0", critical=True)]

        with patch("skill_seekers.cli.doctor.run_all_checks", side_effect=noisy_checks):
            code = DoctorCommand(Namespace(verbose=False, json=True)).execute()

        assert code == 0
        captured = capsys.readouterr()
        payload = json.loads(captured.out)  # stdout is exactly one document
        assert payload["checks"][0]["name"] == "Python version"
        assert "third-party import warning" in captured.err  # not silently dropped

    def test_json_hides_verbose_detail_unless_verbose(self, capsys):
        """verbose_detail carries masked API-key fragments; CI logs must not get them by default."""
        results = [CheckResult("API keys", "warn", "1 set", verbose_detail="  KEY: sk-a...TAIL")]

        with patch("skill_seekers.cli.doctor.run_all_checks", return_value=results):
            DoctorCommand(Namespace(verbose=False, json=True)).execute()
            quiet = json.loads(capsys.readouterr().out)
            DoctorCommand(Namespace(verbose=True, json=True)).execute()
            loud = json.loads(capsys.readouterr().out)

        assert quiet["checks"][0]["verbose_detail"] == ""
        assert "TAIL" not in json.dumps(quiet)
        assert loud["checks"][0]["verbose_detail"] == "  KEY: sk-a...TAIL"

    def test_json_includes_version(self, capsys):
        with patch("skill_seekers.cli.doctor.run_all_checks", return_value=[]):
            DoctorCommand(Namespace(verbose=False, json=True)).execute()
        payload = json.loads(capsys.readouterr().out)
        assert isinstance(payload["version"], str) and payload["version"]

    def test_crashing_check_becomes_error_document(self, capsys):
        with patch(
            "skill_seekers.cli.doctor.run_all_checks", side_effect=FileNotFoundError("cwd gone")
        ):
            code = DoctorCommand(Namespace(verbose=False, json=True)).execute()
        assert code == 1
        assert "cwd gone" in json.loads(capsys.readouterr().out)["error"]

    def test_json_flag_reaches_command_through_the_real_cli(self, capsys):
        """Parser-driven: a typo in doctor_parser.py or the dispatch table must fail here."""
        from skill_seekers.cli.main import main as cli_main

        results = [CheckResult("Python version", "pass", "3.12.0", critical=True)]
        with patch("skill_seekers.cli.doctor.run_all_checks", return_value=results):
            assert cli_main(["doctor", "--json"]) == 0
        assert json.loads(capsys.readouterr().out)["healthy"] is True

    def test_human_and_json_agree_on_exit_code(self, capsys):
        results = [CheckResult("Python version", "fail", "3.9", critical=True)]
        with patch("skill_seekers.cli.doctor.run_all_checks", return_value=results):
            human = DoctorCommand(Namespace(verbose=False, json=False)).execute()
            capsys.readouterr()
            machine = DoctorCommand(Namespace(verbose=False, json=True)).execute()
        assert human == machine == json.loads(capsys.readouterr().out)["exit_code"] == 1

    def test_main_json_outputs_structured_checks_and_summary(self, capsys):
        results = [
            CheckResult("Python version", "pass", "3.12.0", critical=True),
            CheckResult("API keys", "warn", "No API keys configured"),
        ]

        with patch("skill_seekers.cli.doctor.run_all_checks", return_value=results):
            code = DoctorCommand(Namespace(verbose=False, json=True)).execute()

        assert code == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["checks"] == [
            {
                "name": "Python version",
                "status": "pass",
                "detail": "3.12.0",
                "critical": True,
                "verbose_detail": "",
            },
            {
                "name": "API keys",
                "status": "warn",
                "detail": "No API keys configured",
                "critical": False,
                "verbose_detail": "",
            },
        ]
        assert payload["summary"] == {"passed": 1, "warnings": 1, "failed": 0}
        assert payload["healthy"] is True
        assert payload["exit_code"] == 0

    def test_main_json_preserves_critical_failure_exit_code(self, capsys):
        results = [CheckResult("Python version", "fail", "3.9", critical=True)]

        with patch("skill_seekers.cli.doctor.run_all_checks", return_value=results):
            code = DoctorCommand(Namespace(verbose=False, json=True)).execute()

        assert code == 1
        payload = json.loads(capsys.readouterr().out)
        assert payload["healthy"] is False
        assert payload["exit_code"] == 1


class TestDoctorEntryPoints:
    """The unified CLI dispatch, the console script and ``python -m`` all reach the same code."""

    _ok = [CheckResult("python", "pass", "3.12")]

    def test_command_class_dispatch_contract(self, capsys):
        from argparse import Namespace

        with patch("skill_seekers.cli.doctor.run_all_checks", return_value=self._ok):
            assert DoctorCommand(Namespace(verbose=True)).execute() == 0
        assert "python" in capsys.readouterr().out

    def test_main_parses_argv_from_central_parser(self, capsys):
        with (
            patch("skill_seekers.cli.doctor.run_all_checks", return_value=self._ok),
            patch("skill_seekers.cli.doctor.print_report", return_value=0) as report,
            patch("sys.argv", ["skill-seekers-doctor", "--verbose"]),
        ):
            assert main() == 0
        assert report.call_args.kwargs["verbose"] is True

    def test_main_accepts_preparsed_namespace(self):
        from argparse import Namespace

        with patch("skill_seekers.cli.doctor.run_all_checks", return_value=self._ok):
            assert main(Namespace(verbose=False)) == 0

    def test_module_is_runnable(self):
        """``python -m skill_seekers.cli.doctor`` must run the checks, not silently exit 0."""
        import subprocess
        import sys

        proc = subprocess.run(
            [sys.executable, "-m", "skill_seekers.cli.doctor", "--help"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert proc.returncode == 0
        assert "--verbose" in proc.stdout
