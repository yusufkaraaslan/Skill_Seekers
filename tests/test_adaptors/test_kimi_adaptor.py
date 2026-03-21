#!/usr/bin/env python3
"""Tests for Kimi (Moonshot AI) adaptor"""

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from skill_seekers.cli.adaptors import get_adaptor, is_platform_available


class TestKimiAdaptor(unittest.TestCase):
    def setUp(self):
        self.adaptor = get_adaptor("kimi")

    def test_platform_info(self):
        self.assertEqual(self.adaptor.PLATFORM, "kimi")
        self.assertEqual(self.adaptor.PLATFORM_NAME, "Kimi (Moonshot AI)")
        self.assertIn("moonshot", self.adaptor.DEFAULT_API_ENDPOINT)
        self.assertEqual(self.adaptor.DEFAULT_MODEL, "moonshot-v1-128k")

    def test_platform_available(self):
        self.assertTrue(is_platform_available("kimi"))

    def test_env_var_name(self):
        self.assertEqual(self.adaptor.get_env_var_name(), "MOONSHOT_API_KEY")

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
            self.assertIn("kimi", pkg.name)

            with zipfile.ZipFile(pkg) as zf:
                meta = json.loads(zf.read("kimi_metadata.json"))
                self.assertEqual(meta["platform"], "kimi")
                self.assertIn("moonshot", meta["api_base"])


if __name__ == "__main__":
    unittest.main()
