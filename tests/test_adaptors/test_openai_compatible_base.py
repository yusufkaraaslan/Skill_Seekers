#!/usr/bin/env python3
"""
Tests for OpenAI-compatible base adaptor class.

Tests shared behavior across all OpenAI-compatible platforms.
"""

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from skill_seekers.cli.adaptors.openai_compatible import OpenAICompatibleAdaptor
from skill_seekers.cli.adaptors.base import SkillMetadata


class ConcreteTestAdaptor(OpenAICompatibleAdaptor):
    """Concrete subclass for testing the base class."""

    PLATFORM = "testplatform"
    PLATFORM_NAME = "Test Platform"
    DEFAULT_API_ENDPOINT = "https://api.test.example.com/v1"
    DEFAULT_MODEL = "test-model-v1"
    ENV_VAR_NAME = "TEST_PLATFORM_API_KEY"
    PLATFORM_URL = "https://test.example.com/"


class TestOpenAICompatibleBase(unittest.TestCase):
    """Test shared OpenAI-compatible base behavior"""

    def setUp(self):
        self.adaptor = ConcreteTestAdaptor()

    def test_constants_used_in_env_var(self):
        self.assertEqual(self.adaptor.get_env_var_name(), "TEST_PLATFORM_API_KEY")

    def test_supports_enhancement(self):
        self.assertTrue(self.adaptor.supports_enhancement())

    def test_validate_api_key_valid(self):
        self.assertTrue(self.adaptor.validate_api_key("sk-some-long-api-key-string"))

    def test_validate_api_key_invalid(self):
        self.assertFalse(self.adaptor.validate_api_key(""))
        self.assertFalse(self.adaptor.validate_api_key("   "))
        self.assertFalse(self.adaptor.validate_api_key("short"))

    def test_format_skill_md_no_frontmatter(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "test.md").write_text("# Test")

            metadata = SkillMetadata(name="test-skill", description="Test description")
            formatted = self.adaptor.format_skill_md(skill_dir, metadata)

            self.assertFalse(formatted.startswith("---"))
            self.assertIn("You are an expert assistant", formatted)
            self.assertIn("test-skill", formatted)

    def test_format_skill_md_with_existing_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            existing = "# Existing\n\n" + "x" * 200
            (skill_dir / "SKILL.md").write_text(existing)

            metadata = SkillMetadata(name="test", description="Test")
            formatted = self.adaptor.format_skill_md(skill_dir, metadata)

            self.assertIn("You are an expert assistant", formatted)

    def test_package_creates_zip_with_platform_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("Test instructions")
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "guide.md").write_text("# Guide")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            package_path = self.adaptor.package(skill_dir, output_dir)

            self.assertTrue(package_path.exists())
            self.assertTrue(str(package_path).endswith(".zip"))
            self.assertIn("testplatform", package_path.name)

    def test_package_metadata_uses_constants(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("Test")
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "guide.md").write_text("# Guide")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            package_path = self.adaptor.package(skill_dir, output_dir)

            with zipfile.ZipFile(package_path, "r") as zf:
                metadata_content = zf.read("testplatform_metadata.json").decode("utf-8")
                metadata = json.loads(metadata_content)
                self.assertEqual(metadata["platform"], "testplatform")
                self.assertEqual(metadata["model"], "test-model-v1")
                self.assertEqual(metadata["api_base"], "https://api.test.example.com/v1")

    def test_package_zip_structure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("Test")
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "test.md").write_text("# Test")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            package_path = self.adaptor.package(skill_dir, output_dir)

            with zipfile.ZipFile(package_path, "r") as zf:
                names = zf.namelist()
                self.assertIn("system_instructions.txt", names)
                self.assertIn("testplatform_metadata.json", names)
                self.assertTrue(any("knowledge_files" in n for n in names))

    def test_upload_missing_file(self):
        result = self.adaptor.upload(Path("/nonexistent/file.zip"), "test-key")
        self.assertFalse(result["success"])
        self.assertIn("not found", result["message"].lower())

    def test_upload_wrong_format(self):
        with tempfile.NamedTemporaryFile(suffix=".tar.gz") as tmp:
            result = self.adaptor.upload(Path(tmp.name), "test-key")
            self.assertFalse(result["success"])
            self.assertIn("not a zip", result["message"].lower())

    def test_upload_missing_library(self):
        with tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
            with patch.dict(sys.modules, {"openai": None}):
                result = self.adaptor.upload(Path(tmp.name), "test-key")
            self.assertFalse(result["success"])
            self.assertIn("openai", result["message"])

    @patch("openai.OpenAI")
    def test_upload_success_mocked(self, mock_openai_class):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Ready"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("Test")
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "test.md").write_text("# Test")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            package_path = self.adaptor.package(skill_dir, output_dir)
            result = self.adaptor.upload(package_path, "test-long-api-key-string")

            self.assertTrue(result["success"])
            self.assertEqual(result["url"], "https://test.example.com/")
            self.assertIn("validated", result["message"])

    def test_read_reference_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            refs_dir = Path(temp_dir)
            (refs_dir / "guide.md").write_text("# Guide\nContent")
            (refs_dir / "api.md").write_text("# API\nDocs")

            refs = self.adaptor._read_reference_files(refs_dir)
            self.assertEqual(len(refs), 2)

    def test_read_reference_files_truncation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / "large.md").write_text("x" * 50000)
            refs = self.adaptor._read_reference_files(Path(temp_dir))
            self.assertIn("truncated", refs["large.md"])
            self.assertLessEqual(len(refs["large.md"]), 31000)

    def test_build_enhancement_prompt_uses_platform_name(self):
        refs = {"test.md": "# Test\nContent"}
        prompt = self.adaptor._build_enhancement_prompt("skill", refs, None)
        self.assertIn("Test Platform", prompt)

    @patch("openai.OpenAI")
    def test_enhance_success_mocked(self, mock_openai_class):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Enhanced content"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            refs_dir = skill_dir / "references"
            refs_dir.mkdir()
            (refs_dir / "test.md").write_text("# Test\nContent")
            (skill_dir / "SKILL.md").write_text("Original")

            success = self.adaptor.enhance(skill_dir, "test-api-key")

            self.assertTrue(success)
            self.assertEqual((skill_dir / "SKILL.md").read_text(), "Enhanced content")
            self.assertTrue((skill_dir / "SKILL.md.backup").exists())

    def test_enhance_missing_references(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertFalse(self.adaptor.enhance(Path(temp_dir), "key"))


if __name__ == "__main__":
    unittest.main()
