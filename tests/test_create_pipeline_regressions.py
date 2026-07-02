"""Regression tests for verified create-pipeline bugs (PR #409 review).

Covers:
1. create_command: --dry-run must gate steps 6/7 — enhancement made REAL AI
   calls (and workflows executed) when a converter previewed-and-returned-0
   and leftover output from a prior run existed.
2. create_command: CLI --skip-scrape only landed in the config dict while
   SkillConverter.run() reads the instance attribute via getattr — the CLI
   flag was a silent no-op (full network re-scrape), including unified config
   sources whose converter is built through a factory-shaped dict.
3. skill_converter: the skip_scrape branch went straight to build_skill()
   without reloading cached data — document-family converters (pdf, word,
   epub, …) have self.extracted_data=None and crashed with AttributeError.
4. workflow_runner + create_command: unified configs ran their config-file
   "workflows" list TWICE — once in UnifiedScraper.run() Phase 5, again via
   create step 7's new ExecutionContext fallback.
5. unified_scraper: the CLI --output override (resolved into self.output_dir
   in __init__) never reached UnifiedSkillBuilder, which re-resolves
   skill_dir from the raw config — final skill landed in output/<name>
   while intermediates honored --output.
"""

import argparse
import json
from unittest.mock import MagicMock, patch

import pytest

from skill_seekers.cli.create_command import CreateCommand
from skill_seekers.cli.execution_context import ExecutionContext
from skill_seekers.cli.source_detector import SourceInfo
from skill_seekers.cli.workflow_runner import run_workflows


# ─────────────────────────── helpers ────────────────────────────────────────


def make_create_args(**overrides):
    """Minimal argparse.Namespace for CreateCommand tests."""
    base = {
        "source": "https://docs.example.com",
        "config": None,
        "name": "exampledocs",
        "description": None,
        "output": None,
        "dry_run": False,
        "skip_scrape": False,
        "enhance_workflow": None,
        "enhance_stage": None,
        "var": None,
        "workflow_dry_run": False,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def make_workflow_args(enhance_workflow=None, enhance_stage=None):
    """Minimal argparse.Namespace for run_workflows tests."""
    return argparse.Namespace(
        enhance_workflow=enhance_workflow,
        enhance_stage=enhance_stage,
        var=None,
        workflow_dry_run=False,
    )


class StubConverter:
    """Converter stub that records run() calls without doing any work."""

    def __init__(self):
        self.run_called = False

    def run(self):
        self.run_called = True
        return 0


@pytest.fixture(autouse=True)
def _reset_execution_context():
    """Each test gets a fresh ExecutionContext singleton."""
    ExecutionContext.reset()
    yield
    ExecutionContext.reset()


# ═══════════════════════════════════════════════════════════════════════════
# 1. --dry-run must gate steps 6/7 (create_command.py:106)
# ═══════════════════════════════════════════════════════════════════════════


class TestDryRunGatesEnhancementAndWorkflows:
    """A preview run must not make AI calls or execute workflows, even when
    the converter previews-and-returns-0 (e.g. UnifiedScraper dry_run)."""

    def test_dry_run_skips_enhancement_and_workflows(self):
        args = make_create_args(dry_run=True)
        cmd = CreateCommand(args)

        with (
            patch.object(CreateCommand, "_route_to_scraper", return_value=0),
            patch.object(CreateCommand, "_run_enhancement") as enhance,
            patch.object(CreateCommand, "_run_workflows") as workflows,
        ):
            result = cmd.execute()

        assert result == 0
        enhance.assert_not_called()
        workflows.assert_not_called()

    def test_real_run_still_enhances_and_runs_workflows(self):
        """Control: without --dry-run, steps 6/7 run (enhancement defaults to
        enabled=True / level=2)."""
        args = make_create_args(dry_run=False)
        cmd = CreateCommand(args)

        with (
            patch.object(CreateCommand, "_route_to_scraper", return_value=0),
            patch.object(CreateCommand, "_run_enhancement") as enhance,
            patch.object(CreateCommand, "_run_workflows") as workflows,
        ):
            result = cmd.execute()

        assert result == 0
        enhance.assert_called_once()
        workflows.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════
# 2. CLI --skip-scrape must reach the converter instance (create_command.py:271)
# ═══════════════════════════════════════════════════════════════════════════


class TestSkipScrapePromotedToConverter:
    """SkillConverter.run() reads the skip_scrape ATTRIBUTE (same contract the
    MCP scraping tools use); leaving the flag only in the config dict made
    `create <url> --skip-scrape` a silent no-op."""

    def _execute_with_stub(self, args):
        stub = StubConverter()
        cmd = CreateCommand(args)
        with (
            patch("skill_seekers.cli.create_command.get_converter", return_value=stub),
            patch.object(CreateCommand, "_run_enhancement"),
            patch.object(CreateCommand, "_run_workflows"),
        ):
            result = cmd.execute()
        return result, stub

    def test_skip_scrape_flag_sets_converter_attribute(self):
        result, stub = self._execute_with_stub(make_create_args(skip_scrape=True))
        assert result == 0
        assert stub.run_called
        assert getattr(stub, "skip_scrape", False) is True

    def test_no_flag_leaves_attribute_unset(self):
        result, stub = self._execute_with_stub(make_create_args(skip_scrape=False))
        assert result == 0
        assert stub.run_called
        assert not hasattr(stub, "skip_scrape")

    def test_config_source_skip_scrape_flag_sets_converter_attribute(self, tmp_path):
        config = {
            "name": "uni",
            "description": "d",
            "sources": [{"type": "documentation", "base_url": "https://example.com"}],
        }
        cfg = tmp_path / "uni.json"
        cfg.write_text(json.dumps(config), encoding="utf-8")

        result, stub = self._execute_with_stub(make_create_args(source=str(cfg), skip_scrape=True))

        assert result == 0
        assert stub.run_called
        assert getattr(stub, "skip_scrape", False) is True


# ═══════════════════════════════════════════════════════════════════════════
# 3. skip_scrape must reload cached data before build (skill_converter.py:62)
# ═══════════════════════════════════════════════════════════════════════════


class TestSkipScrapeLoadsCachedData:
    """Document-family converters keep extraction results in memory; skipping
    extract() without reloading the on-disk cache crashed build_skill() with
    AttributeError on self.extracted_data=None."""

    def _make_pdf_converter(self, tmp_path):
        from skill_seekers.cli.pdf_scraper import PDFToSkillConverter

        return PDFToSkillConverter(
            {
                "name": "pdfskill",
                # Deliberately nonexistent: if extract() ran despite
                # skip_scrape, PDFExtractor would fail and run() returned 1.
                "pdf_path": str(tmp_path / "manual.pdf"),
                "output_dir": str(tmp_path / "pdfskill"),
            }
        )

    def test_skip_scrape_builds_from_cached_extraction(self, tmp_path):
        converter = self._make_pdf_converter(tmp_path)
        cached = {
            "total_pages": 1,
            "total_code_blocks": 0,
            "total_images": 0,
            "pages": [
                {
                    "page_number": 1,
                    "text": "Getting started with installation and usage.",
                    "headings": [{"text": "Getting Started", "level": 1}],
                    "code_samples": [],
                }
            ],
        }
        with open(converter.data_file, "w", encoding="utf-8") as f:
            json.dump(cached, f)

        converter.skip_scrape = True
        result = converter.run()

        assert result == 0
        assert converter.extracted_data is not None
        assert converter.extracted_data["total_pages"] == 1
        assert (tmp_path / "pdfskill" / "SKILL.md").exists()

    def test_skip_scrape_without_cache_fails_with_clear_error(self, tmp_path, caplog):
        converter = self._make_pdf_converter(tmp_path)
        converter.skip_scrape = True

        result = converter.run()

        assert result == 1
        # The failure must name the missing cache file, not be a bare
        # AttributeError from dereferencing extracted_data=None.
        assert str(converter.data_file) in caplog.text
        assert "skip_scrape" in caplog.text


# ═══════════════════════════════════════════════════════════════════════════
# 4. Unified config workflows must not run twice (workflow_runner.py:119)
# ═══════════════════════════════════════════════════════════════════════════


class TestUnifiedWorkflowsRunOnce:
    """UnifiedScraper.run() Phase 5 already executes config-file workflows;
    create step 7's ExecutionContext fallback must be disabled for the
    'config' source type (and kept for every other type, where step 7 is
    the only executor)."""

    def test_fallback_disabled_skips_context_workflows(self):
        args = make_workflow_args()

        mock_ctx = MagicMock()
        mock_ctx.enhancement.workflows = ["security-focus"]
        mock_ctx.enhancement.stages = []
        mock_ctx.enhancement.workflow_vars = {}

        with (
            patch(
                "skill_seekers.cli.execution_context.ExecutionContext.get",
                return_value=mock_ctx,
            ),
            patch("skill_seekers.cli.enhancement_workflow.WorkflowEngine") as MockEngine,
        ):
            executed, names = run_workflows(args, use_context_fallback=False)

        assert executed is False
        assert names == []
        MockEngine.assert_not_called()

    def test_fallback_enabled_still_runs_context_workflows(self):
        """Control: single-source configs rely on the fallback as the ONLY
        executor of config-declared workflows."""
        args = make_workflow_args()

        mock_ctx = MagicMock()
        mock_ctx.enhancement.workflows = ["security-focus"]
        mock_ctx.enhancement.stages = []
        mock_ctx.enhancement.workflow_vars = {}

        mock_engine = MagicMock()
        mock_engine.workflow.description = "desc"
        mock_engine.workflow.stages = []

        with (
            patch(
                "skill_seekers.cli.execution_context.ExecutionContext.get",
                return_value=mock_ctx,
            ),
            patch(
                "skill_seekers.cli.enhancement_workflow.WorkflowEngine",
                return_value=mock_engine,
            ),
        ):
            executed, names = run_workflows(args)

        assert executed is True
        assert names == ["security-focus"]
        mock_engine.run.assert_called_once()

    def test_cli_flags_still_run_when_fallback_disabled(self):
        """Explicit --enhance-workflow flags are unaffected by the fallback
        switch (they never go through the ExecutionContext)."""
        args = make_workflow_args(enhance_workflow=["minimal"])

        mock_engine = MagicMock()
        mock_engine.workflow.description = "desc"
        mock_engine.workflow.stages = []

        with patch(
            "skill_seekers.cli.enhancement_workflow.WorkflowEngine",
            return_value=mock_engine,
        ):
            executed, names = run_workflows(args, use_context_fallback=False)

        assert executed is True
        assert names == ["minimal"]
        mock_engine.run.assert_called_once()

    def _make_command_with_source_type(self, source_type):
        cmd = CreateCommand(make_create_args())
        cmd.source_info = SourceInfo(
            type=source_type,
            parsed={},
            suggested_name="uni",
            raw_input="uni.json" if source_type == "config" else "https://docs.example.com",
        )
        return cmd

    def test_create_disables_fallback_for_config_source(self):
        cmd = self._make_command_with_source_type("config")
        with patch("skill_seekers.cli.workflow_runner.run_workflows") as rw:
            cmd._run_workflows()
        rw.assert_called_once()
        assert rw.call_args.kwargs["use_context_fallback"] is False

    def test_create_keeps_fallback_for_other_sources(self):
        cmd = self._make_command_with_source_type("web")
        with patch("skill_seekers.cli.workflow_runner.run_workflows") as rw:
            cmd._run_workflows()
        rw.assert_called_once()
        assert rw.call_args.kwargs["use_context_fallback"] is True


# ═══════════════════════════════════════════════════════════════════════════
# 5. --output must reach UnifiedSkillBuilder (unified_scraper.py:1603)
# ═══════════════════════════════════════════════════════════════════════════


class TestUnifiedOutputOverrideReachesBuilder:
    """UnifiedSkillBuilder re-resolves skill_dir from the config dict, so the
    resolved --output value must be written back into self.config."""

    def _write_config(self, tmp_path, **extra):
        config = {
            "name": "uni",
            "description": "d",
            "sources": [
                {"type": "documentation", "base_url": "https://example.com/docs/"},
            ],
            **extra,
        }
        path = tmp_path / "uni.json"
        path.write_text(json.dumps(config))
        return path

    def test_output_override_written_back_to_config(self, tmp_path, monkeypatch):
        from skill_seekers.cli.unified_scraper import UnifiedScraper

        cfg = self._write_config(tmp_path)
        out_dir = tmp_path / "mydir"
        monkeypatch.chdir(tmp_path)

        scraper = UnifiedScraper(
            {"config_path": str(cfg), "output_dir": str(out_dir), "dry_run": True}
        )

        assert scraper.output_dir == str(out_dir)
        assert scraper.config["output_dir"] == str(out_dir)

    def test_builder_skill_dir_honors_output_override(self, tmp_path, monkeypatch):
        """End-to-end: the builder constructed from scraper.config (exactly as
        build_skill does) writes to --output, not output/<name>."""
        from skill_seekers.cli.unified_scraper import UnifiedScraper
        from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder

        cfg = self._write_config(tmp_path)
        out_dir = tmp_path / "mydir"
        monkeypatch.chdir(tmp_path)

        scraper = UnifiedScraper(
            {"config_path": str(cfg), "output_dir": str(out_dir), "dry_run": True}
        )
        builder = UnifiedSkillBuilder(scraper.config, {}, None, [], cache_dir=scraper.cache_dir)

        assert builder.skill_dir == str(out_dir)
        # The pre-fix bug: final skill silently landed in output/<name>.
        assert not (tmp_path / "output" / "uni").exists()

    def test_config_only_run_unchanged(self, tmp_path, monkeypatch):
        """No --output: behavior identical to before (config value, else
        output/<name>)."""
        from skill_seekers.cli.unified_scraper import UnifiedScraper

        monkeypatch.chdir(tmp_path)

        cfg_default = self._write_config(tmp_path)
        scraper = UnifiedScraper({"config_path": str(cfg_default), "dry_run": True})
        assert scraper.output_dir == "output/uni"
        assert scraper.config["output_dir"] == "output/uni"

        cfg_explicit = self._write_config(tmp_path, output_dir="cfg-out/")
        scraper = UnifiedScraper({"config_path": str(cfg_explicit), "dry_run": True})
        assert scraper.output_dir == "cfg-out"
        assert scraper.config["output_dir"] == "cfg-out"
