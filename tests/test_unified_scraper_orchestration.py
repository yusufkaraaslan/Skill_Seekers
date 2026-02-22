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
    """_scrape_documentation() writes a temp config and runs doc_scraper as subprocess."""

    def test_subprocess_called_with_config_and_fresh_flag(self, tmp_path):
        """subprocess.run is called with --config and --fresh for the doc scraper."""
        scraper = _make_scraper(tmp_path=tmp_path)
        source = {"base_url": "https://docs.example.com/", "type": "documentation"}

        with patch("skill_seekers.cli.unified_scraper.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            scraper._scrape_documentation(source)

        assert mock_run.called
        cmd_args = mock_run.call_args[0][0]
        assert "--fresh" in cmd_args
        assert "--config" in cmd_args

    def test_nothing_appended_on_subprocess_failure(self, tmp_path):
        """If subprocess returns non-zero, scraped_data["documentation"] stays empty."""
        scraper = _make_scraper(tmp_path=tmp_path)
        source = {"base_url": "https://docs.example.com/", "type": "documentation"}

        with patch("skill_seekers.cli.unified_scraper.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="err")
            scraper._scrape_documentation(source)

        assert scraper.scraped_data["documentation"] == []

    def test_llms_txt_url_forwarded_to_doc_config(self, tmp_path):
        """llms_txt_url from source is forwarded to the temporary doc config."""
        scraper = _make_scraper(tmp_path=tmp_path)
        source = {
            "base_url": "https://docs.example.com/",
            "type": "documentation",
            "llms_txt_url": "https://docs.example.com/llms.txt",
        }

        written_configs = []

        original_json_dump = json.dumps

        def capture_dump(obj, f, **kwargs):
            if isinstance(f, str):
                return original_json_dump(obj, f, **kwargs)
            written_configs.append(obj)
            return original_json_dump(obj)

        with (
            patch("skill_seekers.cli.unified_scraper.subprocess.run") as mock_run,
            patch(
                "skill_seekers.cli.unified_scraper.json.dump",
                side_effect=lambda obj, _f, **_kw: written_configs.append(obj),
            ),
        ):
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
            scraper._scrape_documentation(source)

        assert any("llms_txt_url" in c for c in written_configs)

    def test_start_urls_forwarded_to_doc_config(self, tmp_path):
        """start_urls from source is forwarded to the temporary doc config."""
        scraper = _make_scraper(tmp_path=tmp_path)
        source = {
            "base_url": "https://docs.example.com/",
            "type": "documentation",
            "start_urls": ["https://docs.example.com/intro"],
        }

        written_configs = []

        with (
            patch("skill_seekers.cli.unified_scraper.subprocess.run") as mock_run,
            patch(
                "skill_seekers.cli.unified_scraper.json.dump",
                side_effect=lambda obj, _f, **_kw: written_configs.append(obj),
            ),
        ):
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
            scraper._scrape_documentation(source)

        assert any("start_urls" in c for c in written_configs)


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

    def test_extract_pdf_called(self, tmp_path, monkeypatch):
        scraper = _make_scraper(tmp_path=tmp_path)
        source = {"type": "pdf", "path": str(tmp_path / "doc.pdf")}

        _, mock_inst = self._mock_pdf_converter(monkeypatch, tmp_path)

        with patch("skill_seekers.cli.unified_scraper.shutil.copy"):
            scraper._scrape_pdf(source)

        mock_inst.extract_pdf.assert_called_once()

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
