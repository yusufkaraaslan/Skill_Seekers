#!/usr/bin/env python3
"""
Tests for IBM Bob adaptor.
"""

import tempfile
import unittest
from pathlib import Path

from skill_seekers.cli.adaptors import get_adaptor, is_platform_available
from skill_seekers.cli.adaptors.base import SkillMetadata
from skill_seekers.cli.adaptors.ibm_bob import IBMBobAdaptor


class TestIBMBobAdaptor(unittest.TestCase):
    """Test IBM Bob adaptor functionality."""

    def setUp(self):
        self.adaptor = get_adaptor("ibm-bob")

    def test_platform_info(self):
        self.assertEqual(self.adaptor.PLATFORM, "ibm-bob")
        self.assertEqual(self.adaptor.PLATFORM_NAME, "IBM Bob")
        self.assertIsNone(self.adaptor.DEFAULT_API_ENDPOINT)

    def test_platform_available(self):
        self.assertTrue(is_platform_available("ibm-bob"))

    def test_validate_api_key_always_true(self):
        self.assertTrue(self.adaptor.validate_api_key(""))
        self.assertTrue(self.adaptor.validate_api_key("anything"))

    def test_no_enhancement_support(self):
        self.assertFalse(self.adaptor.supports_enhancement())

    def test_upload_returns_local_path(self):
        result = self.adaptor.upload(Path("/some/path"), "")
        self.assertTrue(result["success"])
        self.assertIn("local", result["message"].lower())

    def test_skill_dir_name_normalization(self):
        self.assertEqual(IBMBobAdaptor._to_skill_dir_name("My Cool Skill"), "my-cool-skill")
        self.assertEqual(IBMBobAdaptor._to_skill_dir_name("Bob_skill.v2"), "bob-skill-v2")
        self.assertEqual(IBMBobAdaptor._to_skill_dir_name("!!!"), "skill")

    def test_format_skill_md_has_frontmatter(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "test.md").write_text("# Test content")

            metadata = SkillMetadata(
                name="django-orm",
                description="Guide to Django ORM patterns and queries",
                version="1.2.0",
                tags=["django", "orm"],
            )
            formatted = self.adaptor.format_skill_md(skill_dir, metadata)

            self.assertTrue(formatted.startswith("---"))
            self.assertIn('name: "django-orm"', formatted)
            self.assertIn('description: "Guide to Django ORM patterns and queries"', formatted)
            self.assertIn('version: "1.2.0"', formatted)
            self.assertIn("tags:", formatted)
            self.assertIn("- django", formatted)

    def test_format_with_existing_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            existing = (
                "---\nname: test\ndescription: desc\n---\n\n# Existing Content\n\n" + "x" * 200
            )
            (skill_dir / "SKILL.md").write_text(existing)

            metadata = SkillMetadata(name="test", description="Test")
            formatted = self.adaptor.format_skill_md(skill_dir, metadata)

            self.assertTrue(formatted.startswith("---"))
            self.assertIn("Existing Content", formatted)

    def test_package_creates_bob_layout(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: Test Skill\ndescription: Test skill for Bob\nversion: 1.0.0\n---\n\n# Test"
            )
            refs = skill_dir / "references"
            refs.mkdir()
            (refs / "guide.md").write_text("# Guide")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            result_path = self.adaptor.package(skill_dir, output_dir)
            bob_skill_dir = result_path / ".bob" / "skills" / "test-skill"

            self.assertTrue(result_path.exists())
            self.assertTrue(result_path.is_dir())
            self.assertTrue(bob_skill_dir.exists())
            self.assertTrue((bob_skill_dir / "SKILL.md").exists())
            self.assertTrue((bob_skill_dir / "references" / "guide.md").exists())

    def test_package_excludes_backup_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# Test")
            refs = skill_dir / "references"
            refs.mkdir()
            (refs / "guide.md").write_text("# Guide")
            (refs / "guide.md.backup").write_text("# Old")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            result_path = self.adaptor.package(skill_dir, output_dir)
            bob_skill_dir = result_path / ".bob" / "skills" / "test-skill"

            self.assertTrue((bob_skill_dir / "references" / "guide.md").exists())
            self.assertFalse((bob_skill_dir / "references" / "guide.md.backup").exists())


if __name__ == "__main__":
    unittest.main()
