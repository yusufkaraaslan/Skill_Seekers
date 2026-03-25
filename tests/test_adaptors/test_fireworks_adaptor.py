#!/usr/bin/env python3
"""Tests for Fireworks AI adaptor"""

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from skill_seekers.cli.adaptors import get_adaptor, is_platform_available


class TestFireworksAdaptor(unittest.TestCase):
    def setUp(self):
        self.adaptor = get_adaptor("fireworks")

    def test_platform_info(self):
        self.assertEqual(self.adaptor.PLATFORM, "fireworks")
        self.assertEqual(self.adaptor.PLATFORM_NAME, "Fireworks AI")
        self.assertIn("fireworks", self.adaptor.DEFAULT_API_ENDPOINT)
        self.assertIn("llama", self.adaptor.DEFAULT_MODEL.lower())

    def test_platform_available(self):
        self.assertTrue(is_platform_available("fireworks"))

    def test_env_var_name(self):
        self.assertEqual(self.adaptor.get_env_var_name(), "FIREWORKS_API_KEY")

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
            self.assertIn("fireworks", pkg.name)

            with zipfile.ZipFile(pkg) as zf:
                meta = json.loads(zf.read("fireworks_metadata.json"))
                self.assertEqual(meta["platform"], "fireworks")
                self.assertIn("fireworks", meta["api_base"])


if __name__ == "__main__":
    unittest.main()
