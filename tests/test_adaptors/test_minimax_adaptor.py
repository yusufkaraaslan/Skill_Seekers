#!/usr/bin/env python3
"""
Tests for MiniMax AI adaptor
"""

import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock

try:
    from openai import APITimeoutError, APIConnectionError
except ImportError:
    APITimeoutError = None
    APIConnectionError = None

from skill_seekers.cli.adaptors import get_adaptor, is_platform_available
from skill_seekers.cli.adaptors.base import SkillMetadata


class TestMiniMaxAdaptor(unittest.TestCase):
    """Test MiniMax AI adaptor functionality"""

    def setUp(self):
        """Set up test adaptor"""
        self.adaptor = get_adaptor("minimax")

    def test_platform_info(self):
        """Test platform identifiers"""
        self.assertEqual(self.adaptor.PLATFORM, "minimax")
        self.assertEqual(self.adaptor.PLATFORM_NAME, "MiniMax AI")
        self.assertIsNotNone(self.adaptor.DEFAULT_API_ENDPOINT)
        self.assertIn("minimax", self.adaptor.DEFAULT_API_ENDPOINT)

    def test_platform_available(self):
        """Test that minimax platform is registered"""
        self.assertTrue(is_platform_available("minimax"))

    def test_validate_api_key_valid(self):
        """Test valid MiniMax API keys (any string >10 chars)"""
        self.assertTrue(
            self.adaptor.validate_api_key("eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test.key")
        )
        self.assertTrue(self.adaptor.validate_api_key("sk-some-long-api-key-string-here"))
        self.assertTrue(self.adaptor.validate_api_key("  a-valid-key-with-spaces  "))

    def test_validate_api_key_invalid(self):
        """Test invalid API keys"""
        self.assertFalse(self.adaptor.validate_api_key(""))
        self.assertFalse(self.adaptor.validate_api_key("   "))
        self.assertFalse(self.adaptor.validate_api_key("short"))

    def test_get_env_var_name(self):
        """Test environment variable name"""
        self.assertEqual(self.adaptor.get_env_var_name(), "MINIMAX_API_KEY")

    def test_supports_enhancement(self):
        """Test enhancement support"""
        self.assertTrue(self.adaptor.supports_enhancement())

    def test_format_skill_md_no_frontmatter(self):
        """Test that MiniMax format has no YAML frontmatter"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)

            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "test.md").write_text("# Test content")

            metadata = SkillMetadata(name="test-skill", description="Test skill description")

            formatted = self.adaptor.format_skill_md(skill_dir, metadata)

            self.assertFalse(formatted.startswith("---"))
            self.assertIn("You are an expert assistant", formatted)
            self.assertIn("test-skill", formatted)
            self.assertIn("Test skill description", formatted)

    def test_format_skill_md_with_existing_content(self):
        """Test formatting when SKILL.md already has substantial content"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)

            (skill_dir / "references").mkdir()
            existing_content = "# Existing Content\n\n" + "x" * 200
            (skill_dir / "SKILL.md").write_text(existing_content)

            metadata = SkillMetadata(name="test-skill", description="Test description")

            formatted = self.adaptor.format_skill_md(skill_dir, metadata)

            self.assertIn("You are an expert assistant", formatted)
            self.assertIn("test-skill", formatted)

    def test_format_skill_md_without_references(self):
        """Test formatting without references directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)

            metadata = SkillMetadata(name="test-skill", description="Test description")

            formatted = self.adaptor.format_skill_md(skill_dir, metadata)

            self.assertIn("You are an expert assistant", formatted)
            self.assertIn("test-skill", formatted)

    def test_package_creates_zip(self):
        """Test that package creates ZIP file with correct structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()

            (skill_dir / "SKILL.md").write_text("You are an expert assistant")
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "test.md").write_text("# Reference")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            package_path = self.adaptor.package(skill_dir, output_dir)

            self.assertTrue(package_path.exists())
            self.assertTrue(str(package_path).endswith(".zip"))
            self.assertIn("minimax", package_path.name)

            with zipfile.ZipFile(package_path, "r") as zf:
                names = zf.namelist()
                self.assertIn("system_instructions.txt", names)
                self.assertIn("minimax_metadata.json", names)
                self.assertTrue(any("knowledge_files" in name for name in names))

    def test_package_metadata_content(self):
        """Test that packaged ZIP contains correct metadata"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()

            (skill_dir / "SKILL.md").write_text("Test instructions")
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "guide.md").write_text("# User Guide")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            package_path = self.adaptor.package(skill_dir, output_dir)

            with zipfile.ZipFile(package_path, "r") as zf:
                instructions = zf.read("system_instructions.txt").decode("utf-8")
                self.assertEqual(instructions, "Test instructions")

                self.assertIn("knowledge_files/guide.md", zf.namelist())

                metadata_content = zf.read("minimax_metadata.json").decode("utf-8")
                metadata = json.loads(metadata_content)
                self.assertEqual(metadata["platform"], "minimax")
                self.assertEqual(metadata["name"], "test-skill")
                self.assertEqual(metadata["model"], "MiniMax-M2.7")
                self.assertIn("minimax", metadata["api_base"])

    def test_package_output_path_as_file(self):
        """Test packaging when output_path is a file path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("Test")

            output_file = Path(temp_dir) / "output" / "custom-name-minimax.zip"
            output_file.parent.mkdir(parents=True, exist_ok=True)

            package_path = self.adaptor.package(skill_dir, output_file)

            self.assertTrue(package_path.exists())
            self.assertTrue(str(package_path).endswith(".zip"))

    def test_package_without_references(self):
        """Test packaging without reference files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("Test instructions")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            package_path = self.adaptor.package(skill_dir, output_dir)

            self.assertTrue(package_path.exists())
            with zipfile.ZipFile(package_path, "r") as zf:
                names = zf.namelist()
                self.assertIn("system_instructions.txt", names)
                self.assertIn("minimax_metadata.json", names)
                self.assertFalse(any("knowledge_files" in name for name in names))

    def test_upload_missing_library(self):
        """Test upload when openai library is not installed"""
        with tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
            with patch.dict(sys.modules, {"openai": None}):
                result = self.adaptor.upload(Path(tmp.name), "test-api-key")

            self.assertFalse(result["success"])
            self.assertIn("openai", result["message"])
            self.assertIn("not installed", result["message"])

    def test_upload_invalid_file(self):
        """Test upload with invalid file"""
        result = self.adaptor.upload(Path("/nonexistent/file.zip"), "test-api-key")

        self.assertFalse(result["success"])
        self.assertIn("not found", result["message"].lower())

    def test_upload_wrong_format(self):
        """Test upload with wrong file format"""
        with tempfile.NamedTemporaryFile(suffix=".tar.gz") as tmp:
            result = self.adaptor.upload(Path(tmp.name), "test-api-key")

            self.assertFalse(result["success"])
            self.assertIn("not a zip", result["message"].lower())

    @unittest.skip("covered by test_upload_success_mocked")
    def test_upload_success(self):
        """Test successful upload - skipped (needs real API for integration test)"""
        pass

    def test_enhance_missing_references(self):
        """Test enhance when no reference files exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)

            success = self.adaptor.enhance(skill_dir, "test-api-key")
            self.assertFalse(success)

    @patch("openai.OpenAI")
    def test_enhance_success_mocked(self, mock_openai_class):
        """Test successful enhancement with mocked OpenAI client"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Enhanced SKILL.md content"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            refs_dir = skill_dir / "references"
            refs_dir.mkdir()
            (refs_dir / "test.md").write_text("# Test\nContent")
            (skill_dir / "SKILL.md").write_text("Original content")

            success = self.adaptor.enhance(skill_dir, "test-api-key")

            self.assertTrue(success)
            new_content = (skill_dir / "SKILL.md").read_text()
            self.assertEqual(new_content, "Enhanced SKILL.md content")
            backup = skill_dir / "SKILL.md.backup"
            self.assertTrue(backup.exists())
            self.assertEqual(backup.read_text(), "Original content")
            mock_client.chat.completions.create.assert_called_once()

    def test_enhance_missing_library(self):
        """Test enhance when openai library is not installed"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            refs_dir = skill_dir / "references"
            refs_dir.mkdir()
            (refs_dir / "test.md").write_text("Test content")

            with patch.dict(sys.modules, {"openai": None}):
                success = self.adaptor.enhance(skill_dir, "test-api-key")

            self.assertFalse(success)

    def test_read_reference_files(self):
        """Test reading reference files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            refs_dir = Path(temp_dir)
            (refs_dir / "guide.md").write_text("# Guide\nContent here")
            (refs_dir / "api.md").write_text("# API\nAPI docs")

            references = self.adaptor._read_reference_files(refs_dir)

            self.assertEqual(len(references), 2)
            self.assertIn("guide.md", references)
            self.assertIn("api.md", references)

    def test_read_reference_files_empty_dir(self):
        """Test reading from empty references directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            references = self.adaptor._read_reference_files(Path(temp_dir))
            self.assertEqual(len(references), 0)

    def test_read_reference_files_nonexistent(self):
        """Test reading from nonexistent directory"""
        references = self.adaptor._read_reference_files(Path("/nonexistent/path"))
        self.assertEqual(len(references), 0)

    def test_read_reference_files_truncation(self):
        """Test that large reference files are truncated"""
        with tempfile.TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / "large.md").write_text("x" * 50000)

            references = self.adaptor._read_reference_files(Path(temp_dir))

            self.assertIn("large.md", references)
            self.assertIn("truncated", references["large.md"])
            self.assertLessEqual(len(references["large.md"]), 31000)

    def test_build_enhancement_prompt(self):
        """Test enhancement prompt generation"""
        references = {
            "guide.md": "# User Guide\nContent here",
            "api.md": "# API Reference\nAPI docs",
        }

        prompt = self.adaptor._build_enhancement_prompt(
            "test-skill", references, "Existing SKILL.md content"
        )

        self.assertIn("test-skill", prompt)
        self.assertIn("guide.md", prompt)
        self.assertIn("api.md", prompt)
        self.assertIn("Existing SKILL.md content", prompt)
        self.assertIn("MiniMax", prompt)

    def test_build_enhancement_prompt_no_existing(self):
        """Test enhancement prompt when no existing SKILL.md"""
        references = {"test.md": "# Test\nContent"}

        prompt = self.adaptor._build_enhancement_prompt("test-skill", references, None)

        self.assertIn("test-skill", prompt)
        self.assertIn("create from scratch", prompt)

    def test_config_initialization(self):
        """Test adaptor initializes with config"""
        config = {"custom_model": "MiniMax-M2.5"}
        adaptor = get_adaptor("minimax", config)
        self.assertEqual(adaptor.config, config)

    def test_default_config(self):
        """Test adaptor initializes with empty config by default"""
        self.assertEqual(self.adaptor.config, {})

    def test_package_excludes_backup_files(self):
        """Test that backup files are excluded from package"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()

            (skill_dir / "SKILL.md").write_text("Test instructions")
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "guide.md").write_text("# Guide")
            (skill_dir / "references" / "guide.md.backup").write_text("# Old backup")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            package_path = self.adaptor.package(skill_dir, output_dir)

            with zipfile.ZipFile(package_path, "r") as zf:
                names = zf.namelist()
                self.assertIn("knowledge_files/guide.md", names)
                self.assertNotIn("knowledge_files/guide.md.backup", names)

    @patch("openai.OpenAI")
    def test_upload_success_mocked(self, mock_openai_class):
        """Test successful upload with mocked OpenAI client"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Ready to assist with Python testing"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("You are an expert assistant")
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "test.md").write_text("# Test")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            package_path = self.adaptor.package(skill_dir, output_dir)
            result = self.adaptor.upload(package_path, "test-long-api-key-string")

            self.assertTrue(result["success"])
            self.assertIn("validated", result["message"])
            self.assertEqual(result["url"], "https://platform.minimaxi.com/")
            mock_client.chat.completions.create.assert_called_once()

    @unittest.skipUnless(APITimeoutError, "openai library not installed")
    @patch("openai.OpenAI")
    def test_upload_network_error(self, mock_openai_class):
        """Test upload with network timeout error"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = APITimeoutError(request=MagicMock())
        mock_openai_class.return_value = mock_client

        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("Test")
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "test.md").write_text("Content")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            package_path = self.adaptor.package(skill_dir, output_dir)
            result = self.adaptor.upload(package_path, "test-long-api-key-string")

            self.assertFalse(result["success"])
            self.assertIn("timed out", result["message"].lower())

    @unittest.skipUnless(APIConnectionError, "openai library not installed")
    @patch("openai.OpenAI")
    def test_upload_connection_error(self, mock_openai_class):
        """Test upload with connection error"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = APIConnectionError(request=MagicMock())
        mock_openai_class.return_value = mock_client

        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("Test")
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "test.md").write_text("Content")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            package_path = self.adaptor.package(skill_dir, output_dir)
            result = self.adaptor.upload(package_path, "test-long-api-key-string")

            self.assertFalse(result["success"])
            self.assertIn("connection", result["message"].lower())

    def test_validate_api_key_format(self):
        """Test that API key validation uses length-based check"""
        # Valid - long enough strings
        self.assertTrue(self.adaptor.validate_api_key("eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test"))
        self.assertTrue(self.adaptor.validate_api_key("sk-api-abc123-long-enough"))
        # Invalid - too short
        self.assertFalse(self.adaptor.validate_api_key("eyJshort"))
        self.assertFalse(self.adaptor.validate_api_key("short"))


class TestMiniMaxAdaptorIntegration(unittest.TestCase):
    """Integration tests for MiniMax AI adaptor (require MINIMAX_API_KEY)"""

    def setUp(self):
        """Set up test adaptor"""
        self.adaptor = get_adaptor("minimax")

    @unittest.skipUnless(
        os.getenv("MINIMAX_API_KEY"), "MINIMAX_API_KEY not set - skipping integration test"
    )
    def test_enhance_with_real_api(self):
        """Test enhancement with real MiniMax API"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            refs_dir = skill_dir / "references"
            refs_dir.mkdir()
            (refs_dir / "test.md").write_text(
                "# Python Testing\n\n"
                "Use pytest for testing:\n"
                "```python\n"
                "def test_example():\n"
                "    assert 1 + 1 == 2\n"
                "```\n"
            )

            api_key = os.getenv("MINIMAX_API_KEY")
            success = self.adaptor.enhance(skill_dir, api_key)

            self.assertTrue(success)
            skill_md = (skill_dir / "SKILL.md").read_text()
            self.assertTrue(len(skill_md) > 100)

    @unittest.skipUnless(
        os.getenv("MINIMAX_API_KEY"), "MINIMAX_API_KEY not set - skipping integration test"
    )
    def test_upload_with_real_api(self):
        """Test upload validation with real MiniMax API"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("You are an expert assistant for Python testing.")
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "test.md").write_text("# Test\nContent")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            package_path = self.adaptor.package(skill_dir, output_dir)
            api_key = os.getenv("MINIMAX_API_KEY")
            result = self.adaptor.upload(package_path, api_key)

            self.assertTrue(result["success"])
            self.assertIn("validated", result["message"])

    @unittest.skipUnless(
        os.getenv("MINIMAX_API_KEY"), "MINIMAX_API_KEY not set - skipping integration test"
    )
    def test_validate_api_key_real(self):
        """Test validating a real API key"""
        api_key = os.getenv("MINIMAX_API_KEY")
        self.assertTrue(self.adaptor.validate_api_key(api_key))


if __name__ == "__main__":
    unittest.main()
