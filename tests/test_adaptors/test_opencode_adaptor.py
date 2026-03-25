#!/usr/bin/env python3
"""
Tests for OpenCode adaptor
"""

import tempfile
import unittest
from pathlib import Path

from skill_seekers.cli.adaptors import get_adaptor, is_platform_available
from skill_seekers.cli.adaptors.base import SkillMetadata
from skill_seekers.cli.adaptors.opencode import OpenCodeAdaptor


class TestOpenCodeAdaptor(unittest.TestCase):
    """Test OpenCode adaptor functionality"""

    def setUp(self):
        self.adaptor = get_adaptor("opencode")

    def test_platform_info(self):
        self.assertEqual(self.adaptor.PLATFORM, "opencode")
        self.assertEqual(self.adaptor.PLATFORM_NAME, "OpenCode")
        self.assertIsNone(self.adaptor.DEFAULT_API_ENDPOINT)

    def test_platform_available(self):
        self.assertTrue(is_platform_available("opencode"))

    def test_validate_api_key_always_true(self):
        self.assertTrue(self.adaptor.validate_api_key(""))
        self.assertTrue(self.adaptor.validate_api_key("anything"))

    def test_no_enhancement_support(self):
        self.assertFalse(self.adaptor.supports_enhancement())

    def test_upload_returns_local_path(self):
        result = self.adaptor.upload(Path("/some/path"), "")
        self.assertTrue(result["success"])
        self.assertIn("local", result["message"].lower())

    # --- Kebab-case conversion ---

    def test_kebab_case_spaces(self):
        self.assertEqual(OpenCodeAdaptor._to_kebab_case("My Cool Skill"), "my-cool-skill")

    def test_kebab_case_underscores(self):
        self.assertEqual(OpenCodeAdaptor._to_kebab_case("my_cool_skill"), "my-cool-skill")

    def test_kebab_case_special_chars(self):
        self.assertEqual(OpenCodeAdaptor._to_kebab_case("My Skill! (v2.0)"), "my-skill-v2-0")

    def test_kebab_case_uppercase(self):
        self.assertEqual(OpenCodeAdaptor._to_kebab_case("ALLCAPS"), "allcaps")

    def test_kebab_case_truncation(self):
        long_name = "a" * 100
        result = OpenCodeAdaptor._to_kebab_case(long_name)
        self.assertLessEqual(len(result), 64)

    def test_kebab_case_empty(self):
        self.assertEqual(OpenCodeAdaptor._to_kebab_case("!!!"), "skill")

    def test_kebab_case_valid_regex(self):
        """All converted names must match OpenCode's regex"""
        test_names = [
            "My Skill",
            "test_skill_v2",
            "UPPERCASE NAME",
            "special!@#chars",
            "dots.and.periods",
            "a",
        ]
        for name in test_names:
            result = OpenCodeAdaptor._to_kebab_case(name)
            self.assertRegex(result, r"^[a-z0-9]+(-[a-z0-9]+)*$", f"Failed for: {name}")

    # --- Format ---

    def test_format_skill_md_has_frontmatter(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "test.md").write_text("# Test content")

            metadata = SkillMetadata(name="test-skill", description="Test description")
            formatted = self.adaptor.format_skill_md(skill_dir, metadata)

            self.assertTrue(formatted.startswith("---"))
            self.assertIn("name: test-skill", formatted)
            self.assertIn("compatibility: opencode", formatted)
            self.assertIn("generated-by: skill-seekers", formatted)

    def test_format_description_truncation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            long_desc = "x" * 2000
            metadata = SkillMetadata(name="test", description=long_desc)
            formatted = self.adaptor.format_skill_md(skill_dir, metadata)

            # The description in frontmatter should be truncated to 1024 chars
            # (plus YAML quotes around it)
            lines = formatted.split("\n")
            for line in lines:
                if line.startswith("description:"):
                    desc_value = line[len("description:") :].strip()
                    # Strip surrounding quotes for length check
                    inner = desc_value.strip('"')
                    self.assertLessEqual(len(inner), 1024)
                    break

    def test_format_with_existing_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            existing = "# Existing Content\n\n" + "x" * 200
            (skill_dir / "SKILL.md").write_text(existing)

            metadata = SkillMetadata(name="test", description="Test")
            formatted = self.adaptor.format_skill_md(skill_dir, metadata)

            self.assertTrue(formatted.startswith("---"))
            self.assertIn("Existing Content", formatted)

    # --- Package ---

    def test_package_creates_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# Test")
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "guide.md").write_text("# Guide")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            result_path = self.adaptor.package(skill_dir, output_dir)

            self.assertTrue(result_path.exists())
            self.assertTrue(result_path.is_dir())
            self.assertIn("opencode", result_path.name)

    def test_package_contains_skill_md(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# Test content")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            result_path = self.adaptor.package(skill_dir, output_dir)

            self.assertTrue((result_path / "SKILL.md").exists())
            content = (result_path / "SKILL.md").read_text()
            self.assertEqual(content, "# Test content")

    def test_package_copies_references(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# Test")
            refs = skill_dir / "references"
            refs.mkdir()
            (refs / "guide.md").write_text("# Guide")
            (refs / "api.md").write_text("# API")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            result_path = self.adaptor.package(skill_dir, output_dir)

            self.assertTrue((result_path / "references" / "guide.md").exists())
            self.assertTrue((result_path / "references" / "api.md").exists())

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

            self.assertTrue((result_path / "references" / "guide.md").exists())
            self.assertFalse((result_path / "references" / "guide.md.backup").exists())

    def test_package_without_references(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# Test")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            result_path = self.adaptor.package(skill_dir, output_dir)

            self.assertTrue(result_path.exists())
            self.assertTrue((result_path / "SKILL.md").exists())
            self.assertFalse((result_path / "references").exists())


if __name__ == "__main__":
    unittest.main()
