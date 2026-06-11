#!/usr/bin/env python3
"""Tests for the SkillConverter base (output dir handling — CLI-02)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from skill_seekers.cli.skill_converter import SkillConverter


class TestSkillConverterOutputDir:
    """Regression for CLI-02: --output (config['output_dir']) must be honored for
    every source type, not just local. The base sets skill_dir from output_dir;
    each subclass that re-assigns skill_dir mirrors this."""

    def test_honors_explicit_output_dir(self):
        conv = SkillConverter({"name": "react", "output_dir": "/tmp/custom-out"})
        assert conv.skill_dir == "/tmp/custom-out"

    def test_defaults_when_output_dir_absent(self):
        conv = SkillConverter({"name": "react"})
        assert conv.skill_dir == "output/react"

    def test_blank_output_dir_falls_back_to_default(self):
        conv = SkillConverter({"name": "react", "output_dir": ""})
        assert conv.skill_dir == "output/react"


class TestDocConverterDryRunFromConfig:
    """Regression: --dry-run reaches converters via config['dry_run'] (the create
    command passes it through config, not the ctor), so it must be honored."""

    def test_dry_run_from_config(self):
        from skill_seekers.cli.doc_scraper import DocToSkillConverter

        conv = DocToSkillConverter({"name": "t", "base_url": "https://x.io/", "dry_run": True})
        assert conv.dry_run is True

    def test_dry_run_defaults_false(self):
        from skill_seekers.cli.doc_scraper import DocToSkillConverter

        conv = DocToSkillConverter({"name": "t", "base_url": "https://x.io/"})
        assert conv.dry_run is False


class TestSkipScrape:
    """Regression for MCP-03: setting converter.skip_scrape must actually skip
    extract() (the network scrape) and build from existing data. Previously
    run() ignored the attribute, so skip_scrape was a no-op and data was
    re-scraped anyway."""

    @staticmethod
    def _recorder_class():
        class _Recorder(SkillConverter):
            SOURCE_TYPE = "test"

            def __init__(self, config):
                super().__init__(config)
                self.extracted = False
                self.built = False

            def extract(self):
                self.extracted = True

            def build_skill(self):
                self.built = True
                return True

        return _Recorder

    def test_skip_scrape_skips_extract_but_still_builds(self):
        conv = self._recorder_class()({"name": "react", "output_dir": "/tmp/x"})
        conv.skip_scrape = True
        assert conv.run() == 0
        assert conv.extracted is False  # scrape skipped
        assert conv.built is True  # build still ran (from existing data)

    def test_default_runs_extract(self):
        conv = self._recorder_class()({"name": "react", "output_dir": "/tmp/x"})
        assert conv.run() == 0
        assert conv.extracted is True
        assert conv.built is True


class TestSkillDirNormalization:
    """Trailing separators must be stripped once in the base class: derived
    paths like f"{skill_dir}_extracted.json" would otherwise land INSIDE the
    skill directory (and get packaged) when --output ends with '/'."""

    def test_trailing_slash_stripped(self):
        c = SkillConverter({"name": "x", "output_dir": "out/myskill/"})
        assert c.skill_dir == "out/myskill"
        assert c.data_file_for() == "out/myskill_extracted.json"

    def test_data_file_for_custom_suffix(self):
        c = SkillConverter({"name": "x", "output_dir": "out/k"})
        assert c.data_file_for("_github_data.json") == "out/k_github_data.json"

    def test_resolve_skill_dir_static(self):
        assert SkillConverter.resolve_skill_dir({"output_dir": "a/b/"}, "n") == "a/b"
        assert SkillConverter.resolve_skill_dir({}, "n") == "output/n"
