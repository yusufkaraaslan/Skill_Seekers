#!/usr/bin/env python3
"""Tests for OpenRouter adaptor"""

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from skill_seekers.cli.adaptors import get_adaptor, is_platform_available


class TestOpenRouterAdaptor(unittest.TestCase):
    def setUp(self):
        self.adaptor = get_adaptor("openrouter")

    def test_platform_info(self):
        self.assertEqual(self.adaptor.PLATFORM, "openrouter")
        self.assertEqual(self.adaptor.PLATFORM_NAME, "OpenRouter")
        self.assertIn("openrouter", self.adaptor.DEFAULT_API_ENDPOINT)
        self.assertEqual(self.adaptor.DEFAULT_MODEL, "openrouter/auto")

    def test_platform_available(self):
        self.assertTrue(is_platform_available("openrouter"))

    def test_env_var_name(self):
        self.assertEqual(self.adaptor.get_env_var_name(), "OPENROUTER_API_KEY")

    def test_supports_enhancement(self):
        self.assertTrue(self.adaptor.supports_enhancement())

    def test_package_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("Test")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            pkg = self.adaptor.package(skill_dir, output_dir)
            self.assertIn("openrouter", pkg.name)

            with zipfile.ZipFile(pkg) as zf:
                meta = json.loads(zf.read("openrouter_metadata.json"))
                self.assertEqual(meta["platform"], "openrouter")
                self.assertIn("openrouter", meta["api_base"])


if __name__ == "__main__":
    unittest.main()
