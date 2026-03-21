#!/usr/bin/env python3
"""
Tests for OpenCode skill splitter and converter.
"""

import tempfile
import unittest
from pathlib import Path

from skill_seekers.cli.opencode_skill_splitter import (
    OpenCodeSkillConverter,
    OpenCodeSkillSplitter,
)


class TestOpenCodeSkillSplitter(unittest.TestCase):
    """Test skill splitting for OpenCode"""

    def _create_skill(self, temp_dir, name="test-skill", content=None, refs=None):
        """Helper to create a test skill directory."""
        skill_dir = Path(temp_dir) / name
        skill_dir.mkdir()

        if content is None:
            content = "# Test Skill\n\n## Section A\n\nContent A\n\n## Section B\n\nContent B\n\n## Section C\n\nContent C"
        (skill_dir / "SKILL.md").write_text(content)

        if refs:
            refs_dir = skill_dir / "references"
            refs_dir.mkdir()
            for fname, fcontent in refs.items():
                (refs_dir / fname).write_text(fcontent)

        return skill_dir

    def test_needs_splitting_small(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._create_skill(tmp, content="Small content")
            splitter = OpenCodeSkillSplitter(skill_dir, max_chars=50000)
            self.assertFalse(splitter.needs_splitting())

    def test_needs_splitting_large(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._create_skill(tmp, content="x" * 60000)
            splitter = OpenCodeSkillSplitter(skill_dir, max_chars=50000)
            self.assertTrue(splitter.needs_splitting())

    def test_extract_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._create_skill(tmp)
            splitter = OpenCodeSkillSplitter(skill_dir)
            content = (skill_dir / "SKILL.md").read_text()
            sections = splitter._extract_sections(content)
            # Should have: overview + Section A + Section B + Section C
            self.assertGreaterEqual(len(sections), 3)

    def test_extract_sections_strips_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = "---\nname: test\n---\n\n## Section A\n\nContent A"
            skill_dir = self._create_skill(tmp, content=content)
            splitter = OpenCodeSkillSplitter(skill_dir)
            sections = splitter._extract_sections(content)
            self.assertEqual(len(sections), 1)
            self.assertEqual(sections[0]["title"], "Section A")

    def test_split_creates_sub_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._create_skill(tmp)
            splitter = OpenCodeSkillSplitter(skill_dir, max_chars=10)

            output_dir = Path(tmp) / "output"
            result = splitter.split(output_dir)

            # Should create router + sub-skills
            self.assertGreater(len(result), 1)

            # Each should have SKILL.md
            for d in result:
                self.assertTrue((d / "SKILL.md").exists())

    def test_split_router_has_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._create_skill(tmp)
            splitter = OpenCodeSkillSplitter(skill_dir, max_chars=10)

            output_dir = Path(tmp) / "output"
            result = splitter.split(output_dir)

            # Router is first
            router_content = (result[0] / "SKILL.md").read_text()
            self.assertTrue(router_content.startswith("---"))
            self.assertIn("is-router: true", router_content)

    def test_split_sub_skills_have_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._create_skill(tmp)
            splitter = OpenCodeSkillSplitter(skill_dir, max_chars=10)

            output_dir = Path(tmp) / "output"
            result = splitter.split(output_dir)

            # Sub-skills (skip router at index 0)
            for d in result[1:]:
                content = (d / "SKILL.md").read_text()
                self.assertTrue(content.startswith("---"))
                self.assertIn("compatibility: opencode", content)
                self.assertIn("parent-skill:", content)

    def test_split_by_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Skill with no H2 sections but multiple reference files
            skill_dir = self._create_skill(
                tmp,
                content="# Simple Skill\n\nJust one paragraph.",
                refs={
                    "getting-started.md": "# Getting Started\n\nContent here",
                    "api-reference.md": "# API Reference\n\nAPI docs",
                    "advanced-topics.md": "# Advanced Topics\n\nAdvanced content",
                },
            )
            splitter = OpenCodeSkillSplitter(skill_dir, max_chars=10)

            output_dir = Path(tmp) / "output"
            result = splitter.split(output_dir)

            # Should split by references: router + 3 sub-skills
            self.assertEqual(len(result), 4)

    def test_no_split_needed(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._create_skill(tmp, content="# Simple\n\nSmall content")
            splitter = OpenCodeSkillSplitter(skill_dir, max_chars=100000)

            output_dir = Path(tmp) / "output"
            result = splitter.split(output_dir)

            # Should return original skill dir (no split)
            self.assertEqual(len(result), 1)

    def test_group_small_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._create_skill(tmp)
            splitter = OpenCodeSkillSplitter(skill_dir, max_chars=100000)

            sections = [
                {"title": "a", "content": "short"},
                {"title": "b", "content": "also short"},
                {"title": "c", "content": "x" * 50000},
            ]
            grouped = splitter._group_small_sections(sections)

            # a and b should be merged, c stays separate
            self.assertEqual(len(grouped), 2)


class TestOpenCodeSkillConverter(unittest.TestCase):
    """Test bi-directional skill format converter"""

    def test_import_opencode_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "my-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: my-skill\ndescription: Test skill\nversion: 2.0.0\n---\n\n# Content\n\nHello"
            )
            refs = skill_dir / "references"
            refs.mkdir()
            (refs / "guide.md").write_text("# Guide")

            data = OpenCodeSkillConverter.import_opencode_skill(skill_dir)

            self.assertEqual(data["name"], "my-skill")
            self.assertEqual(data["description"], "Test skill")
            self.assertEqual(data["version"], "2.0.0")
            self.assertIn("# Content", data["content"])
            self.assertIn("guide.md", data["references"])
            self.assertEqual(data["source_format"], "opencode")

    def test_import_opencode_skill_no_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "plain-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# Plain content\n\nNo frontmatter")

            data = OpenCodeSkillConverter.import_opencode_skill(skill_dir)

            self.assertEqual(data["name"], "plain-skill")
            self.assertIn("Plain content", data["content"])

    def test_import_missing_skill(self):
        with self.assertRaises(FileNotFoundError):
            OpenCodeSkillConverter.import_opencode_skill("/nonexistent/path")

    def test_export_to_claude(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Create source skill
            source = Path(tmp) / "source"
            source.mkdir()
            (source / "SKILL.md").write_text("---\nname: test\ndescription: Test\n---\n\n# Content")

            # Import and export
            data = OpenCodeSkillConverter.import_opencode_skill(source)
            output = Path(tmp) / "output"
            result = OpenCodeSkillConverter.export_to_target(data, "claude", output)

            self.assertTrue(result.exists())
            self.assertTrue((result / "SKILL.md").exists())

    def test_export_to_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            (source / "SKILL.md").write_text("# Simple content")

            data = OpenCodeSkillConverter.import_opencode_skill(source)
            output = Path(tmp) / "output"
            result = OpenCodeSkillConverter.export_to_target(data, "markdown", output)

            self.assertTrue(result.exists())
            self.assertTrue((result / "SKILL.md").exists())

    def test_roundtrip_opencode(self):
        """Test import from OpenCode -> export to OpenCode preserves content."""
        with tempfile.TemporaryDirectory() as tmp:
            # Create original
            original = Path(tmp) / "original"
            original.mkdir()
            original_content = "---\nname: roundtrip-test\ndescription: Roundtrip test\n---\n\n# Roundtrip Content\n\nImportant data here."
            (original / "SKILL.md").write_text(original_content)
            refs = original / "references"
            refs.mkdir()
            (refs / "ref.md").write_text("# Reference")

            # Import
            data = OpenCodeSkillConverter.import_opencode_skill(original)

            # Export to opencode
            output = Path(tmp) / "output"
            result = OpenCodeSkillConverter.export_to_target(data, "opencode", output)

            # Verify
            exported = (result / "SKILL.md").read_text()
            self.assertIn("roundtrip-test", exported)
            self.assertIn("compatibility: opencode", exported)


class TestGitHubActionsTemplate(unittest.TestCase):
    """Test that GitHub Actions template exists and is valid YAML."""

    def test_template_exists(self):
        template = (
            Path(__file__).parent.parent / "templates" / "github-actions" / "update-skills.yml"
        )
        self.assertTrue(template.exists(), f"Template not found at {template}")

    def test_template_has_required_keys(self):
        template = (
            Path(__file__).parent.parent / "templates" / "github-actions" / "update-skills.yml"
        )
        content = template.read_text()

        self.assertIn("name:", content)
        self.assertIn("on:", content)
        self.assertIn("jobs:", content)
        self.assertIn("skill-seekers", content)
        self.assertIn("schedule:", content)
        self.assertIn("workflow_dispatch:", content)

    def test_template_lists_all_targets(self):
        template = (
            Path(__file__).parent.parent / "templates" / "github-actions" / "update-skills.yml"
        )
        content = template.read_text()

        for target in ["claude", "opencode", "gemini", "openai", "kimi", "deepseek", "qwen"]:
            self.assertIn(target, content, f"Target '{target}' not found in template")


if __name__ == "__main__":
    unittest.main()
