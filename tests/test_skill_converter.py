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
