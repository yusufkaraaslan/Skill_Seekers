#!/usr/bin/env python3
"""
Tests for OpenAI adaptor
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import zipfile

from skill_seekers.cli.adaptors import get_adaptor
from skill_seekers.cli.adaptors.base import SkillMetadata


class TestOpenAIAdaptor(unittest.TestCase):
    """Test OpenAI adaptor functionality"""

    def setUp(self):
        """Set up test adaptor"""
        self.adaptor = get_adaptor('openai')

    def test_platform_info(self):
        """Test platform identifiers"""
        self.assertEqual(self.adaptor.PLATFORM, 'openai')
        self.assertEqual(self.adaptor.PLATFORM_NAME, 'OpenAI ChatGPT')
        self.assertIsNotNone(self.adaptor.DEFAULT_API_ENDPOINT)

    def test_validate_api_key_valid(self):
        """Test valid OpenAI API keys"""
        self.assertTrue(self.adaptor.validate_api_key('sk-proj-abc123'))
        self.assertTrue(self.adaptor.validate_api_key('sk-abc123'))
        self.assertTrue(self.adaptor.validate_api_key('  sk-test  '))  # with whitespace

    def test_validate_api_key_invalid(self):
        """Test invalid API keys"""
        self.assertFalse(self.adaptor.validate_api_key('AIzaSyABC123'))  # Gemini key
        # Note: Can't distinguish Claude keys (sk-ant-*) from OpenAI keys (sk-*)
        self.assertFalse(self.adaptor.validate_api_key('invalid'))
        self.assertFalse(self.adaptor.validate_api_key(''))

    def test_get_env_var_name(self):
        """Test environment variable name"""
        self.assertEqual(self.adaptor.get_env_var_name(), 'OPENAI_API_KEY')

    def test_supports_enhancement(self):
        """Test enhancement support"""
        self.assertTrue(self.adaptor.supports_enhancement())

    def test_format_skill_md_no_frontmatter(self):
        """Test that OpenAI format has no YAML frontmatter"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)

            # Create minimal skill structure
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "test.md").write_text("# Test content")

            metadata = SkillMetadata(
                name="test-skill",
                description="Test skill description"
            )

            formatted = self.adaptor.format_skill_md(skill_dir, metadata)

            # Should NOT start with YAML frontmatter
            self.assertFalse(formatted.startswith('---'))
            # Should contain assistant-style instructions
            self.assertIn('You are an expert assistant', formatted)
            self.assertIn('test-skill', formatted)
            self.assertIn('Test skill description', formatted)

    def test_package_creates_zip(self):
        """Test that package creates ZIP file with correct structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()

            # Create minimal skill structure
            (skill_dir / "SKILL.md").write_text("You are an expert assistant")
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "test.md").write_text("# Reference")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            # Package skill
            package_path = self.adaptor.package(skill_dir, output_dir)

            # Verify package was created
            self.assertTrue(package_path.exists())
            self.assertTrue(str(package_path).endswith('.zip'))
            self.assertIn('openai', package_path.name)

            # Verify package contents
            with zipfile.ZipFile(package_path, 'r') as zf:
                names = zf.namelist()
                self.assertIn('assistant_instructions.txt', names)
                self.assertIn('openai_metadata.json', names)
                # Should have vector store files
                self.assertTrue(any('vector_store_files' in name for name in names))

    def test_upload_missing_library(self):
        """Test upload when openai library is not installed"""
        with tempfile.NamedTemporaryFile(suffix='.zip') as tmp:
            # Simulate missing library by not mocking it
            result = self.adaptor.upload(Path(tmp.name), 'sk-test123')

            self.assertFalse(result['success'])
            self.assertIn('openai', result['message'])
            self.assertIn('not installed', result['message'])

    def test_upload_invalid_file(self):
        """Test upload with invalid file"""
        result = self.adaptor.upload(Path('/nonexistent/file.zip'), 'sk-test123')

        self.assertFalse(result['success'])
        self.assertIn('not found', result['message'].lower())

    def test_upload_wrong_format(self):
        """Test upload with wrong file format"""
        with tempfile.NamedTemporaryFile(suffix='.tar.gz') as tmp:
            result = self.adaptor.upload(Path(tmp.name), 'sk-test123')

            self.assertFalse(result['success'])
            self.assertIn('not a zip', result['message'].lower())

    @unittest.skip("Complex mocking - integration test needed with real API")
    def test_upload_success(self):
        """Test successful upload to OpenAI - skipped (needs real API for integration test)"""
        pass

    @unittest.skip("Complex mocking - integration test needed with real API")
    def test_enhance_success(self):
        """Test successful enhancement - skipped (needs real API for integration test)"""
        pass

    def test_enhance_missing_library(self):
        """Test enhance when openai library is not installed"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            refs_dir = skill_dir / "references"
            refs_dir.mkdir()
            (refs_dir / "test.md").write_text("Test")

            # Don't mock the module - it won't be available
            success = self.adaptor.enhance(skill_dir, 'sk-test123')

            self.assertFalse(success)

    def test_package_includes_instructions(self):
        """Test that packaged ZIP includes assistant instructions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()

            # Create SKILL.md
            skill_md_content = "You are an expert assistant for testing."
            (skill_dir / "SKILL.md").write_text(skill_md_content)

            # Create references
            refs_dir = skill_dir / "references"
            refs_dir.mkdir()
            (refs_dir / "guide.md").write_text("# User Guide")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            # Package
            package_path = self.adaptor.package(skill_dir, output_dir)

            # Verify contents
            with zipfile.ZipFile(package_path, 'r') as zf:
                # Read instructions
                instructions = zf.read('assistant_instructions.txt').decode('utf-8')
                self.assertEqual(instructions, skill_md_content)

                # Verify vector store file
                self.assertIn('vector_store_files/guide.md', zf.namelist())

                # Verify metadata
                metadata_content = zf.read('openai_metadata.json').decode('utf-8')
                import json
                metadata = json.loads(metadata_content)
                self.assertEqual(metadata['platform'], 'openai')
                self.assertEqual(metadata['name'], 'test-skill')
                self.assertIn('file_search', metadata['tools'])


if __name__ == '__main__':
    unittest.main()
