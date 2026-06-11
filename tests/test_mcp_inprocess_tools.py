"""
Phase 5d regression tests: MCP tools dispatch CLI commands in-process.

Covers:
- the shared `run_cli_main` helper in mcp/tools/_common.py (stdout/stderr/log
  capture, sys.argv patching + restoration, SystemExit/KeyboardInterrupt
  containment, exit-code normalization),
- migrated tools' happy paths with the CLI module's main() mocked,
- nonzero-exit → "❌ Error:" output-contract mapping,
- SystemExit containment (a module exit must not kill the server),
- the extract_config_patterns argv fix (the old subprocess invocation passed
  --directory/--json/--markdown, which config_extractor's parser rejected, so
  the tool always failed before Phase 5d).
"""

import json
import logging
import sys

import pytest

from skill_seekers.mcp.tools._common import run_cli_main
from skill_seekers.mcp.tools.packaging_tools import package_skill_tool, upload_skill_tool
from skill_seekers.mcp.tools.scraping_tools import (
    build_how_to_guides_tool,
    detect_patterns_tool,
    estimate_pages_tool,
    extract_config_patterns_tool,
    extract_test_examples_tool,
)
from skill_seekers.mcp.tools.splitting_tools import generate_router, split_config


# ============================================================================
# run_cli_main helper
# ============================================================================


class TestRunCliMain:
    def test_captures_stdout_and_returns_zero_for_none(self):
        def fake_main():
            print("hello from main")
            return None  # falls off the end, like several CLI mains

        stdout, stderr, rc = run_cli_main(fake_main, [])
        assert "hello from main" in stdout
        assert rc == 0

    def test_patches_and_restores_sys_argv(self):
        seen = {}
        original_argv = sys.argv

        def fake_main():
            seen["argv"] = list(sys.argv)
            return 0

        _stdout, _stderr, rc = run_cli_main(fake_main, ["cfg.json", "--max-discovery", "500"])
        assert rc == 0
        assert seen["argv"] == ["skill-seekers", "cfg.json", "--max-discovery", "500"]
        assert sys.argv is original_argv

    def test_sys_argv_restored_on_exception(self):
        original_argv = sys.argv

        def fake_main():
            raise ValueError("boom")

        _stdout, stderr, rc = run_cli_main(fake_main, ["x"])
        assert rc == 1
        assert "ValueError: boom" in stderr
        assert sys.argv is original_argv

    def test_parses_argv_through_a_real_parser(self):
        """A main() that builds its own argparse parser sees the given argv."""
        import argparse

        result = {}

        def fake_main():
            parser = argparse.ArgumentParser()
            parser.add_argument("config")
            parser.add_argument("--max-discovery", type=int, default=1000)
            args = parser.parse_args()
            result["config"] = args.config
            result["max_discovery"] = args.max_discovery
            return 0

        _stdout, _stderr, rc = run_cli_main(fake_main, ["cfg.json", "--max-discovery", "-1"])
        assert rc == 0
        assert result == {"config": "cfg.json", "max_discovery": -1}

    def test_parser_error_is_contained_as_exit_2(self):
        """argparse parser.error() → SystemExit(2) with usage on stderr."""
        import argparse

        def fake_main():
            parser = argparse.ArgumentParser(prog="fake")
            parser.add_argument("required_thing")
            parser.parse_args()

        stdout, stderr, rc = run_cli_main(fake_main, [])
        assert rc == 2
        assert "usage:" in stderr

    def test_system_exit_int_passes_through(self):
        def fake_main():
            sys.exit(42)

        _stdout, _stderr, rc = run_cli_main(fake_main, [])
        assert rc == 42

    def test_system_exit_none_maps_to_zero(self):
        def fake_main():
            sys.exit()

        _stdout, _stderr, rc = run_cli_main(fake_main, [])
        assert rc == 0

    def test_system_exit_message_maps_to_one_with_stderr(self):
        def fake_main():
            sys.exit("fatal: something broke")

        _stdout, stderr, rc = run_cli_main(fake_main, [])
        assert rc == 1
        assert "fatal: something broke" in stderr

    def test_keyboard_interrupt_maps_to_130(self):
        def fake_main():
            raise KeyboardInterrupt

        _stdout, stderr, rc = run_cli_main(fake_main, [])
        assert rc == 130
        assert "Interrupted" in stderr

    def test_skill_seekers_logger_output_is_captured(self):
        # warning(): visible at the default root level, like _run_converter's
        # capture. INFO records flow too once a module sets its own level
        # (e.g. config_extractor.main calls logging.basicConfig(level=INFO)).
        def fake_main():
            logging.getLogger("skill_seekers.cli.something").warning("log line here")
            return 0

        _stdout, stderr, rc = run_cli_main(fake_main, [])
        assert rc == 0
        assert "log line here" in stderr

    def test_log_handler_removed_after_call(self):
        sk_logger = logging.getLogger("skill_seekers")
        before = list(sk_logger.handlers)
        run_cli_main(lambda: 0, [])
        assert list(sk_logger.handlers) == before


# ============================================================================
# Migrated tools: happy path (module main mocked), nonzero exit, SystemExit
# ============================================================================


@pytest.mark.asyncio
class TestEstimatePagesToolInProcess:
    async def test_happy_path(self, monkeypatch):
        import skill_seekers.cli.estimate_pages as estimate_pages

        def fake_main():
            print("Estimated 42 pages")
            return 0

        monkeypatch.setattr(estimate_pages, "main", fake_main)

        result = await estimate_pages_tool({"config_path": "configs/x.json"})
        text = result[0].text
        assert "Estimating page count" in text
        assert "Estimated 42 pages" in text
        assert "❌ Error:" not in text

    async def test_argv_passed_to_module(self, monkeypatch):
        import skill_seekers.cli.estimate_pages as estimate_pages

        seen = {}

        def fake_main():
            seen["argv"] = list(sys.argv[1:])
            return 0

        monkeypatch.setattr(estimate_pages, "main", fake_main)

        await estimate_pages_tool({"config_path": "configs/x.json", "max_discovery": 500})
        assert seen["argv"] == ["configs/x.json", "--max-discovery", "500"]

    async def test_unlimited_maps_to_minus_one(self, monkeypatch):
        import skill_seekers.cli.estimate_pages as estimate_pages

        seen = {}

        def fake_main():
            seen["argv"] = list(sys.argv[1:])
            return 0

        monkeypatch.setattr(estimate_pages, "main", fake_main)

        await estimate_pages_tool({"config_path": "configs/x.json", "unlimited": True})
        assert seen["argv"] == ["configs/x.json", "--max-discovery", "-1"]

    async def test_nonzero_exit_maps_to_error_text(self, monkeypatch):
        import skill_seekers.cli.estimate_pages as estimate_pages

        def fake_main():
            print("partial output")
            print("Config file not found", file=sys.stderr)
            return 1

        monkeypatch.setattr(estimate_pages, "main", fake_main)

        result = await estimate_pages_tool({"config_path": "nonexistent.json"})
        text = result[0].text
        assert "partial output" in text
        assert "❌ Error:" in text
        assert "Config file not found" in text

    async def test_system_exit_does_not_propagate(self, monkeypatch):
        import skill_seekers.cli.estimate_pages as estimate_pages

        def fake_main():
            sys.exit(2)

        monkeypatch.setattr(estimate_pages, "main", fake_main)

        # Must not raise — SystemExit would kill the MCP server.
        result = await estimate_pages_tool({"config_path": "configs/x.json"})
        assert "❌ Error:" in result[0].text

    async def test_output_does_not_claim_hard_timeout_cap(self, monkeypatch):
        """Regression: the in-process run_cli_main path enforces NO timeout,
        so the output must not assert a hard 'Maximum time' cap — the value
        is advisory only."""
        import skill_seekers.cli.estimate_pages as estimate_pages

        monkeypatch.setattr(estimate_pages, "main", lambda: 0)

        result = await estimate_pages_tool({"config_path": "configs/x.json", "unlimited": True})
        text = result[0].text
        assert "Maximum time" not in text
        assert "advisory — not enforced" in text


@pytest.mark.asyncio
class TestDetectPatternsToolInProcess:
    async def test_happy_path_argv(self, monkeypatch):
        import skill_seekers.cli.pattern_recognizer as pattern_recognizer

        seen = {}

        def fake_main():
            seen["argv"] = list(sys.argv[1:])
            print("PATTERN DETECTION RESULTS")
            return 0

        monkeypatch.setattr(pattern_recognizer, "main", fake_main)

        result = await detect_patterns_tool({"file": "src/db.py", "depth": "full", "json": True})
        text = result[0].text
        assert seen["argv"] == ["--file", "src/db.py", "--depth", "full", "--json"]
        assert "Detecting design patterns" in text
        assert "PATTERN DETECTION RESULTS" in text
        assert "❌ Error:" not in text

    async def test_missing_input_short_circuits(self, monkeypatch):
        import skill_seekers.cli.pattern_recognizer as pattern_recognizer

        called = {"n": 0}
        monkeypatch.setattr(
            pattern_recognizer, "main", lambda: called.__setitem__("n", called["n"] + 1)
        )

        result = await detect_patterns_tool({})
        assert "❌ Error: Must specify either 'file' or 'directory'" in result[0].text
        assert called["n"] == 0

    async def test_nonzero_exit(self, monkeypatch):
        import skill_seekers.cli.pattern_recognizer as pattern_recognizer

        def fake_main():
            print("Error: File not found: nope.py", file=sys.stderr)
            return 1

        monkeypatch.setattr(pattern_recognizer, "main", fake_main)

        result = await detect_patterns_tool({"file": "nope.py"})
        text = result[0].text
        assert "❌ Error:" in text
        assert "File not found" in text


@pytest.mark.asyncio
class TestExtractTestExamplesToolInProcess:
    async def test_happy_path_argv(self, monkeypatch):
        import skill_seekers.cli.test_example_extractor as test_example_extractor

        seen = {}

        def fake_main():
            seen["argv"] = list(sys.argv[1:])
            print("Test Example Extraction Results")
            return 0

        monkeypatch.setattr(test_example_extractor, "main", fake_main)

        result = await extract_test_examples_tool({"directory": "tests/", "language": "python"})
        text = result[0].text
        assert seen["argv"] == [
            "tests/",
            "--language",
            "python",
            "--min-confidence",
            "0.5",
            "--max-per-file",
            "10",
        ]
        assert "Extracting usage examples" in text
        assert "Test Example Extraction Results" in text
        assert "❌ Error:" not in text

    async def test_real_parser_round_trip(self, tmp_path):
        """End-to-end through the REAL module parser and main() — pins that
        the argv built by the tool is accepted by test_example_extractor."""
        test_file = tmp_path / "test_sample.py"
        test_file.write_text("def test_one():\n    x = dict(a=1)\n    assert x['a'] == 1\n")

        result = await extract_test_examples_tool({"directory": str(tmp_path), "json": True})
        text = result[0].text
        assert "❌ Error:" not in text


@pytest.mark.asyncio
class TestBuildHowToGuidesToolInProcess:
    async def test_happy_path_argv(self, monkeypatch):
        import skill_seekers.cli.how_to_guide_builder as how_to_guide_builder

        seen = {}

        def fake_main():
            seen["argv"] = list(sys.argv[1:])
            print("Guides generated")
            return 0

        monkeypatch.setattr(how_to_guide_builder, "main", fake_main)

        result = await build_how_to_guides_tool({"input": "examples.json", "no_ai": True})
        text = result[0].text
        assert seen["argv"] == [
            "examples.json",
            "--output",
            "output/codebase/tutorials",
            "--group-by",
            "ai-tutorial-group",
            "--no-ai",
        ]
        assert "Building how-to guides" in text
        assert "❌ Error:" not in text

    async def test_module_sys_exit_contained(self, monkeypatch):
        import skill_seekers.cli.how_to_guide_builder as how_to_guide_builder

        def fake_main():
            print("❌ Error: Input path not found: nope.json")
            sys.exit(1)

        monkeypatch.setattr(how_to_guide_builder, "main", fake_main)

        result = await build_how_to_guides_tool({"input": "nope.json"})
        assert "❌ Error:" in result[0].text


@pytest.mark.asyncio
class TestExtractConfigPatternsToolInProcess:
    async def test_argv_matches_real_parser_flags(self, monkeypatch, tmp_path):
        """The argv must use config_extractor's REAL flags (the old subprocess
        passed --directory/--json/--markdown, which its parser rejected)."""
        import skill_seekers.cli.config_extractor as config_extractor

        seen = {}

        def fake_main():
            seen["argv"] = list(sys.argv[1:])
            return 0

        monkeypatch.setattr(config_extractor, "main", fake_main)

        out_dir = tmp_path / "out"
        result = await extract_config_patterns_tool(
            {"directory": str(tmp_path), "output": str(out_dir)}
        )
        text = result[0].text
        assert seen["argv"] == [
            str(tmp_path),
            "--output",
            str(out_dir / "config_patterns.json"),
            "--max-files",
            "100",
        ]
        assert "--directory" not in seen["argv"]
        assert "--json" not in seen["argv"]
        assert "--markdown" not in seen["argv"]
        assert "❌ Error:" not in text

    async def test_real_run_succeeds(self, tmp_path):
        """Regression: before Phase 5d this tool ALWAYS failed with an
        argparse 'unrecognized arguments' error. Run the real module."""
        (tmp_path / "settings.json").write_text(json.dumps({"db_host": "localhost", "port": 5432}))
        out_dir = tmp_path / "out"

        result = await extract_config_patterns_tool(
            {"directory": str(tmp_path), "output": str(out_dir)}
        )
        text = result[0].text
        assert "❌ Error:" not in text
        assert (out_dir / "config_patterns.json").exists()

    async def test_enhance_maps_to_ai_mode_api(self, monkeypatch, tmp_path):
        """Regression: config_extractor.main() parses --enhance/--enhance-local
        but never reads them — enhancement is driven solely by --ai-mode. With
        the old argv ('--enhance') the tool claimed '🤖 AI enhancement: api'
        while nothing was enhanced. enhance=True must map to '--ai-mode api'."""
        import skill_seekers.cli.config_extractor as config_extractor

        seen = {}

        def fake_main():
            seen["argv"] = list(sys.argv[1:])
            return 0

        monkeypatch.setattr(config_extractor, "main", fake_main)

        result = await extract_config_patterns_tool(
            {"directory": str(tmp_path), "output": str(tmp_path / "out"), "enhance": True}
        )
        text = result[0].text
        assert "--enhance" not in seen["argv"]
        assert seen["argv"][-2:] == ["--ai-mode", "api"]
        assert "🤖 AI enhancement: api" in text

    async def test_enhance_local_maps_to_ai_mode_local(self, monkeypatch, tmp_path):
        import skill_seekers.cli.config_extractor as config_extractor

        seen = {}

        def fake_main():
            seen["argv"] = list(sys.argv[1:])
            return 0

        monkeypatch.setattr(config_extractor, "main", fake_main)

        result = await extract_config_patterns_tool(
            {"directory": str(tmp_path), "output": str(tmp_path / "out"), "enhance_local": True}
        )
        text = result[0].text
        assert "--enhance-local" not in seen["argv"]
        assert seen["argv"][-2:] == ["--ai-mode", "local"]
        assert "🤖 AI enhancement: local" in text

    async def test_explicit_ai_mode_wins_over_enhance_booleans(self, monkeypatch, tmp_path):
        import skill_seekers.cli.config_extractor as config_extractor

        seen = {}

        def fake_main():
            seen["argv"] = list(sys.argv[1:])
            return 0

        monkeypatch.setattr(config_extractor, "main", fake_main)

        result = await extract_config_patterns_tool(
            {
                "directory": str(tmp_path),
                "output": str(tmp_path / "out"),
                "enhance": True,
                "ai_mode": "auto",
            }
        )
        text = result[0].text
        assert seen["argv"][-2:] == ["--ai-mode", "auto"]
        assert seen["argv"].count("--ai-mode") == 1
        assert "🤖 AI enhancement: auto" in text

    async def test_no_enhancement_passes_no_ai_mode(self, monkeypatch, tmp_path):
        import skill_seekers.cli.config_extractor as config_extractor

        seen = {}

        def fake_main():
            seen["argv"] = list(sys.argv[1:])
            return 0

        monkeypatch.setattr(config_extractor, "main", fake_main)

        result = await extract_config_patterns_tool(
            {"directory": str(tmp_path), "output": str(tmp_path / "out")}
        )
        text = result[0].text
        assert "--ai-mode" not in seen["argv"]
        assert "🤖 AI enhancement:" not in text


@pytest.mark.asyncio
class TestSplitConfigToolInProcess:
    async def test_happy_path_argv(self, monkeypatch):
        import skill_seekers.cli.split_config as split_config_cli

        seen = {}

        def fake_main():
            seen["argv"] = list(sys.argv[1:])
            print("Would create 3 config files")
            return 0

        monkeypatch.setattr(split_config_cli, "main", fake_main)

        result = await split_config(
            {"config_path": "configs/godot.json", "strategy": "category", "dry_run": True}
        )
        text = result[0].text
        assert seen["argv"] == [
            "configs/godot.json",
            "--strategy",
            "category",
            "--target-pages",
            "5000",
            "--dry-run",
        ]
        assert "Splitting configuration" in text
        assert "Would create 3 config files" in text
        assert "❌ Error:" not in text

    async def test_module_exception_maps_to_error(self, monkeypatch):
        import skill_seekers.cli.split_config as split_config_cli

        def fake_main():
            raise FileNotFoundError("configs/missing.json")

        monkeypatch.setattr(split_config_cli, "main", fake_main)

        result = await split_config({"config_path": "configs/missing.json"})
        text = result[0].text
        assert "❌ Error:" in text
        assert "missing.json" in text


@pytest.mark.asyncio
class TestGenerateRouterToolInProcess:
    async def test_no_matching_configs_short_circuits(self, tmp_path):
        result = await generate_router({"config_pattern": str(tmp_path / "godot-*.json")})
        assert "❌ No config files match pattern" in result[0].text

    async def test_happy_path_argv(self, monkeypatch, tmp_path):
        import skill_seekers.cli.generate_router as generate_router_cli

        (tmp_path / "godot-2d.json").write_text("{}")
        (tmp_path / "godot-3d.json").write_text("{}")

        seen = {}

        def fake_main():
            seen["argv"] = sorted(sys.argv[1:-2]) + sys.argv[-2:]
            print("Router config created")
            return 0

        monkeypatch.setattr(generate_router_cli, "main", fake_main)

        result = await generate_router(
            {"config_pattern": str(tmp_path / "godot-*.json"), "router_name": "godot-hub"}
        )
        text = result[0].text
        assert seen["argv"] == [
            str(tmp_path / "godot-2d.json"),
            str(tmp_path / "godot-3d.json"),
            "--name",
            "godot-hub",
        ]
        assert "Generating router skill" in text
        assert "Router config created" in text
        assert "❌ Error:" not in text


@pytest.mark.asyncio
class TestPackageSkillToolInProcess:
    async def test_happy_path(self, monkeypatch):
        import skill_seekers.cli.package_skill as package_skill_cli

        seen = {}

        def fake_main():
            seen["argv"] = list(sys.argv[1:])
            print("✅ Package created: output/react.zip")
            return None  # package_skill.main falls through on success

        monkeypatch.setattr(package_skill_cli, "main", fake_main)

        result = await package_skill_tool(
            {"skill_dir": "output/react/", "auto_upload": False, "target": "claude"}
        )
        text = result[0].text
        assert seen["argv"] == [
            "output/react/",
            "--no-open",
            "--skip-quality-check",
            "--target",
            "claude",
        ]
        assert "📦 Packaging skill" in text
        assert "Package created: output/react.zip" in text
        assert "✅ Skill packaged successfully" in text
        assert "❌ Error:" not in text

    async def test_failure_keeps_error_marker_contract(self, monkeypatch):
        """install_skill_tool sniffs '❌ Error:' in package output to abort
        before upload — pin that contract."""
        import skill_seekers.cli.package_skill as package_skill_cli

        def fake_main():
            print("Quality check output")
            sys.exit(1)  # package_skill.main exits 1 on failure

        monkeypatch.setattr(package_skill_cli, "main", fake_main)

        result = await package_skill_tool(
            {"skill_dir": "output/missing/", "auto_upload": False, "target": "claude"}
        )
        text = result[0].text
        assert "❌ Error:" in text
        assert "✅ Skill packaged successfully" not in text


@pytest.mark.asyncio
class TestUploadSkillToolInProcess:
    async def test_happy_path_system_exit_zero(self, monkeypatch):
        """upload_skill.main ALWAYS exits via sys.exit — exit 0 is success."""
        import skill_seekers.cli.upload_skill as upload_skill_cli

        seen = {}

        def fake_main():
            seen["argv"] = list(sys.argv[1:])
            print("Upload successful")
            sys.exit(0)

        monkeypatch.setattr(upload_skill_cli, "main", fake_main)

        result = await upload_skill_tool({"skill_zip": "output/react.zip", "target": "claude"})
        text = result[0].text
        assert seen["argv"] == ["output/react.zip", "--target", "claude"]
        assert "📤 Uploading skill" in text
        assert "Upload successful" in text
        assert "❌ Error:" not in text

    async def test_api_key_forwarded(self, monkeypatch):
        import skill_seekers.cli.upload_skill as upload_skill_cli

        seen = {}

        def fake_main():
            seen["argv"] = list(sys.argv[1:])
            sys.exit(0)

        monkeypatch.setattr(upload_skill_cli, "main", fake_main)

        await upload_skill_tool(
            {"skill_zip": "output/react.zip", "target": "claude", "api_key": "sk-test"}
        )
        assert seen["argv"] == ["output/react.zip", "--target", "claude", "--api-key", "sk-test"]

    async def test_failure_exit_maps_to_error(self, monkeypatch):
        import skill_seekers.cli.upload_skill as upload_skill_cli

        def fake_main():
            print("❌ Upload failed: bad key")
            sys.exit(1)

        monkeypatch.setattr(upload_skill_cli, "main", fake_main)

        result = await upload_skill_tool({"skill_zip": "output/react.zip", "target": "claude"})
        assert "❌ Error:" in result[0].text
