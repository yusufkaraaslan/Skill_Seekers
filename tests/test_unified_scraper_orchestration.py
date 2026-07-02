"""
Tests for UnifiedScraper orchestration methods.

Covers:
- scrape_all_sources()  - routing by source type
- _scrape_documentation() - subprocess invocation and data population
- _scrape_github()       - GitHubScraper delegation and scraped_data append
- _scrape_pdf()          - PDFToSkillConverter delegation and scraped_data append
- _scrape_local()        - analyze_codebase delegation; known 'args' bug
- run()                  - 4-phase orchestration and workflow integration
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from skill_seekers.cli.unified_scraper import UnifiedScraper


# ---------------------------------------------------------------------------
# Shared factory helper
# ---------------------------------------------------------------------------


def _make_scraper(extra_config=None, tmp_path=None):
    """Create a minimal UnifiedScraper bypassing __init__ dir creation."""
    config = {
        "name": "test_unified",
        "description": "Test unified config",
        "sources": [],
        **(extra_config or {}),
    }
    scraper = UnifiedScraper.__new__(UnifiedScraper)
    scraper.config = config
    scraper.name = config["name"]
    scraper.merge_mode = config.get("merge_mode", "rule-based")
    scraper.scraped_data = {
        "documentation": [],
        "github": [],
        "pdf": [],
        "local": [],
    }
    scraper._source_counters = {"documentation": 0, "github": 0, "pdf": 0, "local": 0}

    if tmp_path:
        scraper.output_dir = str(tmp_path / "output")
        scraper.cache_dir = str(tmp_path / "cache")
        scraper.sources_dir = str(tmp_path / "cache/sources")
        scraper.data_dir = str(tmp_path / "cache/data")
        scraper.repos_dir = str(tmp_path / "cache/repos")
        scraper.logs_dir = str(tmp_path / "cache/logs")
        # Pre-create data_dir so tests that write temp configs can proceed
        Path(scraper.data_dir).mkdir(parents=True, exist_ok=True)
    else:
        scraper.output_dir = "output/test_unified"
        scraper.cache_dir = ".skillseeker-cache/test_unified"
        scraper.sources_dir = ".skillseeker-cache/test_unified/sources"
        scraper.data_dir = ".skillseeker-cache/test_unified/data"
        scraper.repos_dir = ".skillseeker-cache/test_unified/repos"
        scraper.logs_dir = ".skillseeker-cache/test_unified/logs"

    # Mock validator so scrape_all_sources() doesn't need real config file
    scraper.validator = MagicMock()
    scraper.validator.is_unified = True
    scraper.validator.needs_api_merge.return_value = False

    return scraper


# ===========================================================================
# 1. scrape_all_sources() routing
# ===========================================================================


class TestScrapeAllSourcesRouting:
    """scrape_all_sources() dispatches to the correct _scrape_* method."""

    def _run_with_sources(self, sources, monkeypatch):
        """Helper: set sources on a fresh scraper and run scrape_all_sources()."""
        scraper = _make_scraper()
        scraper.config["sources"] = sources

        calls = {"documentation": 0, "github": 0, "pdf": 0, "local": 0}

        monkeypatch.setattr(
            scraper,
            "_scrape_documentation",
            lambda _s: calls.__setitem__("documentation", calls["documentation"] + 1),
        )
        monkeypatch.setattr(
            scraper, "_scrape_github", lambda _s: calls.__setitem__("github", calls["github"] + 1)
        )
        monkeypatch.setattr(
            scraper, "_scrape_pdf", lambda _s: calls.__setitem__("pdf", calls["pdf"] + 1)
        )
        monkeypatch.setattr(
            scraper, "_scrape_local", lambda _s: calls.__setitem__("local", calls["local"] + 1)
        )

        scraper.scrape_all_sources()
        return calls

    def test_documentation_source_routes_to_scrape_documentation(self, monkeypatch):
        calls = self._run_with_sources(
            [{"type": "documentation", "base_url": "https://example.com"}], monkeypatch
        )
        assert calls["documentation"] == 1
        assert calls["github"] == 0
        assert calls["pdf"] == 0
        assert calls["local"] == 0

    def test_github_source_routes_to_scrape_github(self, monkeypatch):
        calls = self._run_with_sources([{"type": "github", "repo": "user/repo"}], monkeypatch)
        assert calls["github"] == 1
        assert calls["documentation"] == 0

    def test_pdf_source_routes_to_scrape_pdf(self, monkeypatch):
        calls = self._run_with_sources([{"type": "pdf", "path": "/tmp/doc.pdf"}], monkeypatch)
        assert calls["pdf"] == 1
        assert calls["documentation"] == 0

    def test_local_source_routes_to_scrape_local(self, monkeypatch):
        calls = self._run_with_sources([{"type": "local", "path": "/tmp/project"}], monkeypatch)
        assert calls["local"] == 1
        assert calls["documentation"] == 0

    def test_unknown_source_type_is_skipped(self, monkeypatch):
        """Unknown types are logged as warnings but do not crash or call any scraper."""
        calls = self._run_with_sources([{"type": "unsupported_xyz"}], monkeypatch)
        assert all(v == 0 for v in calls.values())

    def test_multiple_sources_each_scraper_called_once(self, monkeypatch):
        sources = [
            {"type": "documentation", "base_url": "https://a.com"},
            {"type": "github", "repo": "user/repo"},
            {"type": "pdf", "path": "/tmp/a.pdf"},
            {"type": "local", "path": "/tmp/proj"},
        ]
        calls = self._run_with_sources(sources, monkeypatch)
        assert calls == {"documentation": 1, "github": 1, "pdf": 1, "local": 1}

    def test_exception_in_one_source_continues_others(self, monkeypatch):
        """An exception in one scraper does not abort remaining sources."""
        scraper = _make_scraper()
        scraper.config["sources"] = [
            {"type": "documentation", "base_url": "https://a.com"},
            {"type": "github", "repo": "user/repo"},
        ]
        calls = {"documentation": 0, "github": 0}

        def raise_on_doc(_s):
            raise RuntimeError("simulated doc failure")

        def count_github(_s):
            calls["github"] += 1

        monkeypatch.setattr(scraper, "_scrape_documentation", raise_on_doc)
        monkeypatch.setattr(scraper, "_scrape_github", count_github)

        # Should not raise
        scraper.scrape_all_sources()
        assert calls["github"] == 1


# ===========================================================================
# 2. _scrape_documentation()
# ===========================================================================


class TestScrapeDocumentation:
    """_scrape_documentation() calls scrape_documentation() directly."""

    def test_scrape_documentation_called_directly(self, tmp_path):
        """scrape_documentation is called directly (not via subprocess)."""
        scraper = _make_scraper(tmp_path=tmp_path)
        source = {"base_url": "https://docs.example.com/", "type": "documentation"}

        with patch("skill_seekers.cli.doc_scraper.scrape_documentation") as mock_scrape:
            mock_scrape.return_value = 1  # simulate failure
            scraper._scrape_documentation(source)

        assert mock_scrape.called

    def test_nothing_appended_on_scrape_failure(self, tmp_path):
        """If scrape_documentation returns non-zero, scraped_data["documentation"] stays empty."""
        scraper = _make_scraper(tmp_path=tmp_path)
        source = {"base_url": "https://docs.example.com/", "type": "documentation"}

        with patch("skill_seekers.cli.doc_scraper.scrape_documentation") as mock_scrape:
            mock_scrape.return_value = 1
            scraper._scrape_documentation(source)

        assert scraper.scraped_data["documentation"] == []

    def test_llms_txt_url_forwarded_to_doc_config(self, tmp_path):
        """llms_txt_url from source is forwarded to the doc config."""
        scraper = _make_scraper(tmp_path=tmp_path)
        source = {
            "base_url": "https://docs.example.com/",
            "type": "documentation",
            "llms_txt_url": "https://docs.example.com/llms.txt",
        }

        captured_config = {}

        def fake_scrape(config, ctx=None):  # noqa: ARG001
            captured_config.update(config)
            return 1  # fail so we don't need to set up output files

        with patch("skill_seekers.cli.doc_scraper.scrape_documentation", side_effect=fake_scrape):
            scraper._scrape_documentation(source)

        # The llms_txt_url should be in the sources list of the doc config
        sources = captured_config.get("sources", [])
        assert any("llms_txt_url" in s for s in sources)

    def test_start_urls_forwarded_to_doc_config(self, tmp_path):
        """start_urls from source is forwarded to the doc config."""
        scraper = _make_scraper(tmp_path=tmp_path)
        source = {
            "base_url": "https://docs.example.com/",
            "type": "documentation",
            "start_urls": ["https://docs.example.com/intro"],
        }

        captured_config = {}

        def fake_scrape(config, ctx=None):  # noqa: ARG001
            captured_config.update(config)
            return 1

        with patch("skill_seekers.cli.doc_scraper.scrape_documentation", side_effect=fake_scrape):
            scraper._scrape_documentation(source)

        sources = captured_config.get("sources", [])
        assert any("start_urls" in s for s in sources)


# ===========================================================================
# 3. _scrape_github()
# ===========================================================================


class TestScrapeGithub:
    """_scrape_github() delegates to GitHubScraper and populates scraped_data."""

    def _mock_github_scraper(self, monkeypatch, github_data=None):
        """Patch GitHubScraper class in the unified_scraper module."""
        if github_data is None:
            github_data = {"files": [], "readme": "", "stars": 0}

        mock_scraper_cls = MagicMock()
        mock_instance = MagicMock()
        mock_instance.scrape.return_value = github_data
        mock_scraper_cls.return_value = mock_instance

        monkeypatch.setattr(
            "skill_seekers.cli.github_scraper.GitHubScraper",
            mock_scraper_cls,
        )
        return mock_scraper_cls, mock_instance

    def test_github_scraper_instantiated_with_repo(self, tmp_path, monkeypatch):
        scraper = _make_scraper(tmp_path=tmp_path)
        source = {"type": "github", "repo": "user/myrepo", "enable_codebase_analysis": False}

        mock_cls, mock_inst = self._mock_github_scraper(monkeypatch)

        (tmp_path / "output").mkdir(parents=True, exist_ok=True)
        with (
            patch("skill_seekers.cli.unified_scraper.json.dump"),
            patch("skill_seekers.cli.unified_scraper.json.dumps", return_value="{}"),
            patch("builtins.open", MagicMock()),
        ):
            scraper._scrape_github(source)

        mock_cls.assert_called_once()
        init_call_config = mock_cls.call_args[0][0]
        assert init_call_config["repo"] == "user/myrepo"

    def test_scrape_method_called(self, tmp_path, monkeypatch):
        scraper = _make_scraper(tmp_path=tmp_path)
        source = {"type": "github", "repo": "user/myrepo", "enable_codebase_analysis": False}

        _, mock_inst = self._mock_github_scraper(monkeypatch)

        with patch("builtins.open", MagicMock()):
            scraper._scrape_github(source)

        mock_inst.scrape.assert_called_once()

    def test_scraped_data_appended(self, tmp_path, monkeypatch):
        scraper = _make_scraper(tmp_path=tmp_path)
        source = {"type": "github", "repo": "user/myrepo", "enable_codebase_analysis": False}
        gh_data = {"files": [{"path": "README.md"}], "readme": "Hello"}

        self._mock_github_scraper(monkeypatch, github_data=gh_data)

        with patch("builtins.open", MagicMock()):
            scraper._scrape_github(source)

        assert len(scraper.scraped_data["github"]) == 1
        entry = scraper.scraped_data["github"][0]
        assert entry["repo"] == "user/myrepo"
        assert entry["data"] == gh_data

    def test_source_counter_incremented(self, tmp_path, monkeypatch):
        scraper = _make_scraper(tmp_path=tmp_path)
        assert scraper._source_counters["github"] == 0

        source = {"type": "github", "repo": "user/repo1", "enable_codebase_analysis": False}
        self._mock_github_scraper(monkeypatch)

        with patch("builtins.open", MagicMock()):
            scraper._scrape_github(source)

        assert scraper._source_counters["github"] == 1

    def test_c3_analysis_not_triggered_when_disabled(self, tmp_path, monkeypatch):
        """When enable_codebase_analysis=False, _clone_github_repo is never called."""
        scraper = _make_scraper(tmp_path=tmp_path)
        source = {"type": "github", "repo": "user/repo", "enable_codebase_analysis": False}

        self._mock_github_scraper(monkeypatch)
        clone_mock = MagicMock(return_value=None)
        monkeypatch.setattr(scraper, "_clone_github_repo", clone_mock)

        with patch("builtins.open", MagicMock()):
            scraper._scrape_github(source)

        clone_mock.assert_not_called()


# ===========================================================================
# 4. _scrape_pdf()
# ===========================================================================


class TestScrapePdf:
    """_scrape_pdf() delegates to PDFToSkillConverter and populates scraped_data."""

    def _mock_pdf_converter(self, monkeypatch, tmp_path, pages=None):
        """Patch PDFToSkillConverter class and provide a fake data_file."""
        if pages is None:
            pages = [{"page": 1, "content": "Hello world"}]

        # Create a fake data file that the converter will "produce"
        data_file = tmp_path / "pdf_data.json"
        data_file.write_text(json.dumps({"pages": pages}))

        mock_cls = MagicMock()
        mock_instance = MagicMock()
        mock_instance.data_file = str(data_file)
        mock_cls.return_value = mock_instance

        monkeypatch.setattr(
            "skill_seekers.cli.pdf_scraper.PDFToSkillConverter",
            mock_cls,
        )
        return mock_cls, mock_instance

    def test_pdf_converter_instantiated_with_path(self, tmp_path, monkeypatch):
        scraper = _make_scraper(tmp_path=tmp_path)
        pdf_path = str(tmp_path / "manual.pdf")
        source = {"type": "pdf", "path": pdf_path}

        mock_cls, _ = self._mock_pdf_converter(monkeypatch, tmp_path)

        with patch("skill_seekers.cli.unified_scraper.shutil.copy"):
            scraper._scrape_pdf(source)

        mock_cls.assert_called_once()
        init_config = mock_cls.call_args[0][0]
        assert init_config["pdf_path"] == pdf_path
        assert init_config["output_dir"].startswith(scraper.sources_dir)
        assert init_config["output_dir"].endswith("test_unified_pdf_0_manual")

    def test_extract_called(self, tmp_path, monkeypatch):
        scraper = _make_scraper(tmp_path=tmp_path)
        source = {"type": "pdf", "path": str(tmp_path / "doc.pdf")}

        _, mock_inst = self._mock_pdf_converter(monkeypatch, tmp_path)

        with patch("skill_seekers.cli.unified_scraper.shutil.copy"):
            scraper._scrape_pdf(source)

        mock_inst.extract.assert_called_once()

    def test_scraped_data_appended_with_pages(self, tmp_path, monkeypatch):
        scraper = _make_scraper(tmp_path=tmp_path)
        pdf_path = str(tmp_path / "report.pdf")
        source = {"type": "pdf", "path": pdf_path}

        pages = [{"page": 1, "content": "Hello"}, {"page": 2, "content": "World"}]
        self._mock_pdf_converter(monkeypatch, tmp_path, pages=pages)

        with patch("skill_seekers.cli.unified_scraper.shutil.copy"):
            scraper._scrape_pdf(source)

        assert len(scraper.scraped_data["pdf"]) == 1
        entry = scraper.scraped_data["pdf"][0]
        assert entry["pdf_path"] == pdf_path
        assert entry["data"]["pages"] == pages

    def test_source_counter_incremented(self, tmp_path, monkeypatch):
        scraper = _make_scraper(tmp_path=tmp_path)
        assert scraper._source_counters["pdf"] == 0

        source = {"type": "pdf", "path": str(tmp_path / "a.pdf")}
        self._mock_pdf_converter(monkeypatch, tmp_path)

        with patch("skill_seekers.cli.unified_scraper.shutil.copy"):
            scraper._scrape_pdf(source)

        assert scraper._source_counters["pdf"] == 1


# ===========================================================================
# 4b. _scrape_with_converter() shared engine (Phase 4 dispatch refactor)
# ===========================================================================


class TestScrapeWithConverterEngine:
    """The shared engine routes mechanical types through get_converter()."""

    def _mock_pptx_converter(self, monkeypatch, tmp_path, slides=None):
        """Patch PptxToSkillConverter (and its dep check) with a fake data_file."""
        if slides is None:
            slides = [{"slide": 1, "content": "Intro"}]

        data_file = tmp_path / "pptx_data.json"
        data_file.write_text(json.dumps({"slides": slides}))

        mock_cls = MagicMock()
        mock_instance = MagicMock()
        mock_instance.data_file = str(data_file)
        mock_cls.return_value = mock_instance

        monkeypatch.setattr("skill_seekers.cli.pptx_scraper.PptxToSkillConverter", mock_cls)
        # Keep the test hermetic: get_converter() runs the optional-dep check
        # for pptx, which would fail when python-pptx isn't installed.
        monkeypatch.setattr("skill_seekers.cli.pptx_scraper._check_pptx_deps", lambda: None)
        return mock_cls, mock_instance

    def _make_pptx_scraper(self, tmp_path):
        scraper = _make_scraper(tmp_path=tmp_path)
        scraper.scraped_data["pptx"] = []
        scraper._source_counters["pptx"] = 0
        return scraper

    def test_unknown_source_type_warns_and_continues(self, monkeypatch, caplog):
        """An unknown type logs a warning and later sources still run."""
        import logging

        scraper = _make_scraper()
        scraper.config["sources"] = [
            {"type": "unsupported_xyz"},
            {"type": "pdf", "path": "/tmp/a.pdf"},
        ]
        calls = {"pdf": 0}
        monkeypatch.setattr(
            scraper, "_scrape_pdf", lambda _s: calls.__setitem__("pdf", calls["pdf"] + 1)
        )

        with caplog.at_level(logging.WARNING, logger="skill_seekers.cli.unified_scraper"):
            count = scraper.scrape_all_sources()

        assert "Unknown source type: unsupported_xyz" in caplog.text
        assert calls["pdf"] == 1
        assert count == 0  # warning path appends nothing

    def test_pptx_routes_through_get_converter_and_extract(self, tmp_path, monkeypatch):
        """A mechanical type is built via get_converter() and uses public extract()."""
        scraper = self._make_pptx_scraper(tmp_path)
        pptx_path = str(tmp_path / "deck.pptx")
        source = {"type": "pptx", "path": pptx_path}

        slides = [{"slide": 1, "content": "A"}, {"slide": 2, "content": "B"}]
        mock_cls, mock_inst = self._mock_pptx_converter(monkeypatch, tmp_path, slides=slides)

        with patch("skill_seekers.cli.unified_scraper.shutil.copy"):
            scraper._scrape_pptx(source)

        # get_converter() instantiated the registered class with the built config
        mock_cls.assert_called_once()
        init_config = mock_cls.call_args[0][0]
        assert init_config["name"] == "test_unified_pptx_0_deck"
        assert init_config["pptx_path"] == pptx_path

        # Public extract() is used (not the legacy extract_pptx())
        mock_inst.extract.assert_called_once()
        mock_inst.extract_pptx.assert_not_called()

        # Exact record keys are preserved
        assert len(scraper.scraped_data["pptx"]) == 1
        entry = scraper.scraped_data["pptx"][0]
        assert set(entry.keys()) == {"pptx_path", "pptx_id", "idx", "data", "data_file"}
        assert entry["pptx_path"] == pptx_path
        assert entry["pptx_id"] == "deck"
        assert entry["idx"] == 0
        assert entry["data"]["slides"] == slides
        assert entry["data_file"].endswith("pptx_data_0_deck.json")
        assert scraper._source_counters["pptx"] == 1

    def test_engine_still_calls_build_skill(self, tmp_path, monkeypatch):
        """The standalone sub-skill build must survive the refactor (the unified
        build consumes sub-skill references from the cache)."""
        scraper = self._make_pptx_scraper(tmp_path)
        source = {"type": "pptx", "path": str(tmp_path / "deck.pptx")}

        _, mock_inst = self._mock_pptx_converter(monkeypatch, tmp_path)

        with patch("skill_seekers.cli.unified_scraper.shutil.copy"):
            scraper._scrape_pptx(source)

        mock_inst.build_skill.assert_called_once()


# ===========================================================================
# 5. _scrape_local() — known 'args' scoping bug
# ===========================================================================


class TestScrapeLocal:
    """_scrape_local() delegates to analyze_codebase and populates scraped_data."""

    def test_source_counter_incremented(self, tmp_path, monkeypatch):
        """Counter is incremented when _scrape_local() is called."""
        scraper = _make_scraper(tmp_path=tmp_path)
        source = {"type": "local", "path": str(tmp_path)}
        assert scraper._source_counters["local"] == 0

        monkeypatch.setattr(
            "skill_seekers.cli.codebase_scraper.analyze_codebase",
            MagicMock(),
        )

        scraper._scrape_local(source)

        assert scraper._source_counters["local"] == 1

    def test_enhance_level_uses_cli_args_override(self, tmp_path, monkeypatch):
        """CLI --enhance-level overrides per-source enhance_level."""
        import argparse

        scraper = _make_scraper(tmp_path=tmp_path)
        source = {"type": "local", "path": str(tmp_path), "enhance_level": 1}
        scraper._cli_args = argparse.Namespace(enhance_level=3)

        captured_kwargs = {}

        def fake_analyze(**kwargs):
            captured_kwargs.update(kwargs)

        monkeypatch.setattr(
            "skill_seekers.cli.codebase_scraper.analyze_codebase",
            fake_analyze,
        )

        scraper._scrape_local(source)

        assert captured_kwargs.get("enhance_level") == 3

    def test_analyze_codebase_not_called_with_old_kwargs(self, tmp_path, monkeypatch):
        """analyze_codebase() must not receive enhance_with_ai or ai_mode (#323)."""
        scraper = _make_scraper(tmp_path=tmp_path)
        source = {"type": "local", "path": str(tmp_path)}

        captured_kwargs = {}

        def fake_analyze(**kwargs):
            captured_kwargs.update(kwargs)

        monkeypatch.setattr(
            "skill_seekers.cli.codebase_scraper.analyze_codebase",
            fake_analyze,
        )

        scraper._scrape_local(source)

        assert "enhance_with_ai" not in captured_kwargs, (
            "enhance_with_ai is not a valid analyze_codebase() parameter"
        )
        assert "ai_mode" not in captured_kwargs, (
            "ai_mode is not a valid analyze_codebase() parameter"
        )
        assert "enhance_level" in captured_kwargs


# ===========================================================================
# 6. run() orchestration
# ===========================================================================


class TestRunOrchestration:
    """run() executes 4 phases in order and integrates enhancement workflows."""

    def _make_run_scraper(self, extra_config=None):
        """Minimal scraper for run() tests with all heavy methods pre-mocked."""
        scraper = _make_scraper(extra_config=extra_config)
        scraper.scrape_all_sources = MagicMock()
        scraper.detect_conflicts = MagicMock(return_value=[])
        scraper.merge_sources = MagicMock(return_value=None)
        scraper.build_skill = MagicMock()
        return scraper

    def test_four_phases_called(self):
        """scrape_all_sources, detect_conflicts, build_skill are always called."""
        scraper = self._make_run_scraper()

        with patch("skill_seekers.cli.unified_scraper.run_workflows", create=True):
            scraper.run()

        scraper.scrape_all_sources.assert_called_once()
        scraper.detect_conflicts.assert_called_once()
        scraper.build_skill.assert_called_once()

    def test_merge_sources_skipped_when_no_conflicts(self):
        """merge_sources is NOT called when detect_conflicts returns empty list."""
        scraper = self._make_run_scraper()
        scraper.detect_conflicts.return_value = []  # no conflicts

        scraper.run()

        scraper.merge_sources.assert_not_called()

    def test_merge_sources_called_when_conflicts_present(self):
        """merge_sources IS called when conflicts are detected."""
        scraper = self._make_run_scraper()
        conflict = {"type": "api_mismatch", "severity": "high"}
        scraper.detect_conflicts.return_value = [conflict]

        scraper.run()

        scraper.merge_sources.assert_called_once_with([conflict])

    def test_workflow_not_called_without_args_and_no_json_workflows(self):
        """When args=None and config has no workflow fields, run_workflows is never called."""
        scraper = self._make_run_scraper()  # sources=[], no workflow fields

        with patch("skill_seekers.cli.unified_scraper.run_workflows", create=True) as mock_wf:
            scraper.run(args=None)

        mock_wf.assert_not_called()

    def test_workflow_called_when_args_provided(self):
        """When CLI args are passed, run_workflows is invoked."""
        import argparse

        scraper = self._make_run_scraper()
        cli_args = argparse.Namespace(
            enhance_workflow=["security-focus"],
            enhance_stage=None,
            var=None,
            workflow_dry_run=False,
        )

        # run_workflows is imported dynamically inside run() from workflow_runner.
        # Patch at the source module so the local `from ... import` picks it up.
        with patch("skill_seekers.cli.workflow_runner.run_workflows") as mock_wf:
            scraper.run(args=cli_args)

        mock_wf.assert_called_once()

    def test_workflow_called_for_json_config_workflows(self):
        """When config has 'workflows' list, run_workflows is called even with args=None."""
        scraper = self._make_run_scraper(extra_config={"workflows": ["minimal"]})

        captured = {}

        def fake_run_workflows(args, context=None):  # noqa: ARG001
            captured["workflows"] = getattr(args, "enhance_workflow", None)

        import contextlib

        import skill_seekers.cli.unified_scraper as us_mod
        import skill_seekers.cli.workflow_runner as wr_mod

        orig_us = getattr(us_mod, "run_workflows", None)
        orig_wr = getattr(wr_mod, "run_workflows", None)

        us_mod.run_workflows = fake_run_workflows
        wr_mod.run_workflows = fake_run_workflows
        try:
            scraper.run(args=None)
        finally:
            if orig_us is None:
                with contextlib.suppress(AttributeError):
                    delattr(us_mod, "run_workflows")
            else:
                us_mod.run_workflows = orig_us

            if orig_wr is None:
                with contextlib.suppress(AttributeError):
                    delattr(wr_mod, "run_workflows")
            else:
                wr_mod.run_workflows = orig_wr

        assert "minimal" in (captured.get("workflows") or [])


# ===========================================================================
# Regression: issue #364 — guides loaded from fallback location
# ===========================================================================


class TestLoadGuideCollectionFallback:
    """_load_guide_collection must return a falsy value when nothing is loadable.

    Otherwise the ``primary or fallback`` chain in _scrape_local /
    _run_c3_analysis short-circuits on the truthy placeholder and the real
    guide data in the fallback location is silently dropped (issue #364:
    output references contain an empty guide_collection.json even though
    the cache holds 3 generated guides).
    """

    def _scraper(self):
        return UnifiedScraper.__new__(UnifiedScraper)

    def test_returns_empty_dict_when_directory_missing(self, tmp_path):
        scraper = self._scraper()
        result = scraper._load_guide_collection(tmp_path / "nope")
        assert result == {}
        assert not result  # falsy, so `or` fallback fires

    def test_returns_empty_dict_when_directory_has_no_guide_files(self, tmp_path):
        tutorials = tmp_path / "tutorials"
        tutorials.mkdir()
        (tutorials / "index.md").write_text("# Empty\n")
        scraper = self._scraper()
        result = scraper._load_guide_collection(tutorials)
        assert result == {}
        assert not result

    def test_loads_guide_collection_when_present(self, tmp_path):
        tutorials = tmp_path / "tutorials"
        tutorials.mkdir()
        payload = {
            "total_guides": 2,
            "guides_by_complexity": {},
            "guides_by_use_case": {},
            "guides": [{"id": "g1", "title": "One"}, {"id": "g2", "title": "Two"}],
        }
        (tutorials / "guide_collection.json").write_text(json.dumps(payload))
        scraper = self._scraper()
        result = scraper._load_guide_collection(tutorials)
        assert result["total_guides"] == 2
        assert len(result["guides"]) == 2

    def test_or_fallback_picks_up_guides_from_secondary_path(self, tmp_path):
        """Issue #364: when references/tutorials/ is missing but the original
        tutorials/ still has the JSON, the fallback path must win."""
        temp_output = tmp_path / "local_analysis_0_repo"
        refs = temp_output / "references"  # not created — simulates skipped move
        tutorials = temp_output / "tutorials"
        tutorials.mkdir(parents=True)
        payload = {
            "total_guides": 3,
            "guides_by_complexity": {},
            "guides_by_use_case": {},
            "guides": [
                {"id": "g1", "title": "One"},
                {"id": "g2", "title": "Two"},
                {"id": "g3", "title": "Three"},
            ],
        }
        (tutorials / "guide_collection.json").write_text(json.dumps(payload))

        scraper = self._scraper()
        primary = scraper._load_guide_collection(refs / "tutorials")
        fallback = scraper._load_guide_collection(temp_output / "tutorials")
        result = primary or fallback

        assert not primary  # primary missing, must be falsy
        assert result["total_guides"] == 3
        assert len(result["guides"]) == 3


# ===========================================================================
# Unified --output / cache-flow integration (CLI-02 unified path)
# ===========================================================================


class TestUnifiedCacheFlow:
    """Locks the refactored unified flow: sub-converters write straight into the
    cache via output_dir in their sub-config, and the unified scraper reads back
    from there — no output/ staging, no move."""

    def test_documentation_written_to_cache_and_read_back(self, tmp_path, monkeypatch):
        import os

        # Isolate cwd so the "no stray ./output/" check is meaningful (the repo's
        # ./output may hold unrelated leftovers from other runs).
        monkeypatch.chdir(tmp_path)

        scraper = _make_scraper(tmp_path=tmp_path)
        Path(scraper.sources_dir).mkdir(parents=True, exist_ok=True)
        source = {"base_url": "https://docs.example.com/", "type": "documentation"}

        captured = {}

        def fake_scrape(config, **_kwargs):
            # Simulate DocToSkillConverter honoring config["output_dir"].
            out = config["output_dir"]
            captured["output_dir"] = out
            os.makedirs(f"{out}_data", exist_ok=True)
            os.makedirs(os.path.join(out, "references"), exist_ok=True)
            with open(os.path.join(f"{out}_data", "summary.json"), "w") as f:
                json.dump({"pages": [{"url": "https://docs.example.com/a"}], "total_pages": 1}, f)
            return 0

        with patch("skill_seekers.cli.doc_scraper.scrape_documentation", side_effect=fake_scrape):
            scraper._scrape_documentation(source)

        # Sub-config output_dir was redirected into the cache (never bare output/).
        assert captured["output_dir"].startswith(scraper.sources_dir)

        docs = scraper.scraped_data["documentation"]
        assert len(docs) == 1
        assert docs[0]["total_pages"] == 1
        assert docs[0]["data_file"].startswith(scraper.sources_dir)
        assert docs[0]["refs_dir"].startswith(scraper.sources_dir)
        assert not docs[0]["data_file"].startswith("output/")
        # The flow must not create a stray ./output/<name>_docs staging dir.
        assert not (Path.cwd() / "output" / f"{scraper.name}_docs").exists()

    def test_multiple_documentation_sources_use_distinct_cache_dirs(self, tmp_path, monkeypatch):
        import os

        monkeypatch.chdir(tmp_path)

        sources = [
            {"base_url": "https://docs.example.com/a/", "type": "documentation"},
            {"base_url": "https://docs.example.com/b/", "type": "documentation"},
        ]
        scraper = _make_scraper({"sources": sources}, tmp_path=tmp_path)
        Path(scraper.sources_dir).mkdir(parents=True, exist_ok=True)

        captured = []

        def fake_scrape(config, **_kwargs):
            out = config["output_dir"]
            captured.append(out)
            os.makedirs(f"{out}_data", exist_ok=True)
            os.makedirs(os.path.join(out, "references"), exist_ok=True)
            with open(os.path.join(f"{out}_data", "summary.json"), "w") as f:
                json.dump({"pages": [{"url": f"{out}/page"}], "total_pages": 1}, f)
            return 0

        with patch("skill_seekers.cli.doc_scraper.scrape_documentation", side_effect=fake_scrape):
            for source in sources:
                scraper._scrape_documentation(source)

        assert len(captured) == 2
        assert captured[0] != captured[1]
        assert all(path.startswith(scraper.sources_dir) for path in captured)
        assert (
            scraper.scraped_data["documentation"][0]["data_file"]
            != (scraper.scraped_data["documentation"][1]["data_file"])
        )

        reloaded = _make_scraper({"sources": sources}, tmp_path=tmp_path)
        assert reloaded._load_cached_sources() == 2
        loaded_docs = reloaded.scraped_data["documentation"]
        assert loaded_docs[0]["source_id"] != loaded_docs[1]["source_id"]
        assert loaded_docs[0]["data_file"] != loaded_docs[1]["data_file"]


class TestUnifiedDryRunAndOutput:
    """MCP-03 follow-up: dry_run must actually be honored by UnifiedScraper,
    and --output (CLI) must win over the config file."""

    def _write_config(self, tmp_path):
        config = {
            "name": "uni",
            "description": "d",
            "merge_mode": "rule-based",
            "sources": [
                {"type": "documentation", "base_url": "https://example.com/docs/"},
            ],
        }
        path = tmp_path / "uni.json"
        path.write_text(json.dumps(config))
        return path

    def test_dry_run_previews_without_scraping_or_writing(self, tmp_path, monkeypatch):
        cfg = self._write_config(tmp_path)
        out_dir = tmp_path / "out"
        monkeypatch.chdir(tmp_path)
        scraper = UnifiedScraper(str(cfg), dry_run=True, output_dir=str(out_dir))
        with patch.object(scraper, "scrape_all_sources") as scrape:
            result = scraper.run()
        scrape.assert_not_called()
        assert result == 0
        # Dry run must not create the output or cache directories.
        assert not out_dir.exists()
        assert not (tmp_path / ".skillseeker-cache").exists()

    def test_output_dir_param_wins_over_config(self, tmp_path, monkeypatch):
        cfg = self._write_config(tmp_path)
        monkeypatch.chdir(tmp_path)
        # Trailing slash is normalized by the shared resolver.
        scraper = UnifiedScraper(str(cfg), output_dir=str(tmp_path / "custom") + "/", dry_run=True)
        assert scraper.output_dir == str(tmp_path / "custom")


class TestUnifiedSkipScrape:
    """Unified skip_scrape reloads prior cache instead of scraping again."""

    def test_run_loads_cached_sources_without_rescraping(self, tmp_path):
        scraper = _make_scraper(
            {
                "sources": [
                    {"type": "documentation", "base_url": "https://example.com/docs"},
                    {"type": "github", "repo": "owner/repo"},
                ]
            },
            tmp_path=tmp_path,
        )
        scraper.skip_scrape = True

        docs_data = Path(scraper.sources_dir) / "test_unified_docs_data" / "summary.json"
        docs_data.parent.mkdir(parents=True, exist_ok=True)
        docs_data.write_text(
            json.dumps({"pages": [{"title": "Intro", "url": "https://example.com"}]}),
            encoding="utf-8",
        )

        github_data = Path(scraper.data_dir) / "github_data_0_owner_repo.json"
        github_data.write_text(json.dumps({"readme": "cached"}), encoding="utf-8")

        with (
            patch.object(scraper, "scrape_all_sources") as scrape,
            patch.object(scraper, "detect_conflicts", return_value=[]) as detect,
            patch.object(scraper, "build_skill") as build,
        ):
            result = scraper.run()

        assert result == 0
        scrape.assert_not_called()
        detect.assert_called_once()
        build.assert_called_once_with(None)
        assert scraper.scraped_data["documentation"][0]["data_file"] == str(docs_data)
        assert scraper.scraped_data["documentation"][0]["pages"][0]["title"] == "Intro"
        assert scraper.scraped_data["github"][0]["data"] == {"readme": "cached"}

    def test_run_fails_if_skip_scrape_cache_is_missing(self, tmp_path):
        scraper = _make_scraper(
            {"sources": [{"type": "github", "repo": "owner/repo"}]},
            tmp_path=tmp_path,
        )
        scraper.skip_scrape = True

        with (
            patch.object(scraper, "scrape_all_sources") as scrape,
            patch.object(scraper, "build_skill") as build,
        ):
            result = scraper.run()

        assert result == 1
        scrape.assert_not_called()
        build.assert_not_called()

    def test_load_cached_sources_restores_converter_backed_source_shape(self, tmp_path):
        scraper = _make_scraper(
            {"sources": [{"type": "pdf", "path": "/tmp/manual.pdf"}]},
            tmp_path=tmp_path,
        )
        pdf_data = Path(scraper.data_dir) / "pdf_data_0_manual.json"
        pdf_data.write_text(json.dumps({"pages": [{"title": "Manual"}]}), encoding="utf-8")

        assert scraper._load_cached_sources() == 1
        assert scraper.scraped_data["pdf"][0] == {
            "pdf_path": "/tmp/manual.pdf",
            "pdf_id": "manual",
            "idx": 0,
            "data": {"pages": [{"title": "Manual"}]},
            "data_file": str(pdf_data),
        }

    def test_load_cached_video_uses_unified_data_cache(self, tmp_path):
        scraper = _make_scraper(
            {"sources": [{"type": "video", "url": "https://youtu.be/example"}]},
            tmp_path=tmp_path,
        )
        video_data = Path(scraper.data_dir) / "video_data_0.json"
        video_data.write_text(json.dumps({"videos": [{"title": "Demo"}]}), encoding="utf-8")

        assert scraper._load_cached_sources() == 1
        assert scraper.scraped_data["video"][0] == {
            "video_id": "https://youtu.be/example",
            "idx": 0,
            "data": {"videos": [{"title": "Demo"}]},
            "data_file": str(video_data),
        }


# ===========================================================================
# Factory construction (Phase 4.1): get_converter("config", {...})
# ===========================================================================


class TestFactoryConstruction:
    """UnifiedScraper honors the get_converter() factory contract: a single
    factory-shaped config dict ({"config_path": ..., "merge_mode": ...,
    "output_dir": ..., "dry_run": ...}) — while the legacy positional
    config-path str keeps working."""

    def _write_config(self, tmp_path, merge_mode=None):
        config = {
            "name": "uni",
            "description": "d",
            "sources": [
                {"type": "documentation", "base_url": "https://example.com/docs/"},
            ],
        }
        if merge_mode:
            config["merge_mode"] = merge_mode
        path = tmp_path / "uni.json"
        path.write_text(json.dumps(config))
        return path

    def test_factory_dict_honors_config_path_output_dir_dry_run(self, tmp_path, monkeypatch):
        from skill_seekers.cli.skill_converter import get_converter

        cfg = self._write_config(tmp_path)
        out_dir = tmp_path / "factory-out"
        monkeypatch.chdir(tmp_path)

        converter = get_converter(
            "config",
            {
                "config_path": str(cfg),
                "merge_mode": "ai-enhanced",
                "output_dir": str(out_dir),
                "dry_run": True,
            },
        )

        assert isinstance(converter, UnifiedScraper)
        assert converter.config_path == str(cfg)
        assert converter.config["name"] == "uni"
        assert converter.merge_mode == "ai-enhanced"
        assert converter.output_dir == str(out_dir)
        assert converter.dry_run is True
        # dry_run construction must not create output or cache directories.
        assert not out_dir.exists()
        assert not (tmp_path / ".skillseeker-cache").exists()

        # dry_run run() previews without scraping.
        with patch.object(converter, "scrape_all_sources") as scrape:
            assert converter.run() == 0
        scrape.assert_not_called()

    def test_factory_dict_defaults_match_legacy(self, tmp_path, monkeypatch):
        """Omitted optional keys behave exactly like the legacy defaults."""
        from skill_seekers.cli.skill_converter import get_converter

        cfg = self._write_config(tmp_path, merge_mode="claude-enhanced")
        monkeypatch.chdir(tmp_path)

        converter = get_converter("config", {"config_path": str(cfg), "dry_run": True})

        # merge_mode falls back to the config file (normalized alias).
        assert converter.merge_mode == "ai-enhanced"
        # output_dir falls back to output/<name>.
        assert converter.output_dir == "output/uni"

    def test_legacy_positional_str_still_works(self, tmp_path, monkeypatch):
        cfg = self._write_config(tmp_path)
        monkeypatch.chdir(tmp_path)

        scraper = UnifiedScraper(str(cfg), merge_mode="rule-based", dry_run=True)

        assert scraper.config_path == str(cfg)
        assert scraper.config["name"] == "uni"
        assert scraper.merge_mode == "rule-based"
        assert scraper.dry_run is True

    def test_explicit_kwargs_win_over_factory_dict(self, tmp_path, monkeypatch):
        cfg = self._write_config(tmp_path)
        monkeypatch.chdir(tmp_path)

        scraper = UnifiedScraper(
            {"config_path": str(cfg), "merge_mode": "rule-based", "output_dir": "from-dict"},
            merge_mode="ai-enhanced",
            output_dir=str(tmp_path / "from-kwarg"),
            dry_run=True,
        )

        assert scraper.merge_mode == "ai-enhanced"
        assert scraper.output_dir == str(tmp_path / "from-kwarg")
