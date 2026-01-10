#!/usr/bin/env python3
"""
Tests for Gemini adaptor
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import tarfile

from skill_seekers.cli.adaptors import get_adaptor
from skill_seekers.cli.adaptors.base import SkillMetadata


class TestGeminiAdaptor(unittest.TestCase):
    """Test Gemini adaptor functionality"""

    def setUp(self):
        """Set up test adaptor"""
        self.adaptor = get_adaptor('gemini')

    def test_platform_info(self):
        """Test platform identifiers"""
        self.assertEqual(self.adaptor.PLATFORM, 'gemini')
        self.assertEqual(self.adaptor.PLATFORM_NAME, 'Google Gemini')
        self.assertIsNotNone(self.adaptor.DEFAULT_API_ENDPOINT)

    def test_validate_api_key_valid(self):
        """Test valid Google API key"""
        self.assertTrue(self.adaptor.validate_api_key('AIzaSyABC123'))
        self.assertTrue(self.adaptor.validate_api_key('  AIzaSyTest  '))  # with whitespace

    def test_validate_api_key_invalid(self):
        """Test invalid API keys"""
        self.assertFalse(self.adaptor.validate_api_key('sk-ant-123'))  # Claude key
        self.assertFalse(self.adaptor.validate_api_key('invalid'))
        self.assertFalse(self.adaptor.validate_api_key(''))

    def test_get_env_var_name(self):
        """Test environment variable name"""
        self.assertEqual(self.adaptor.get_env_var_name(), 'GOOGLE_API_KEY')

    def test_supports_enhancement(self):
        """Test enhancement support"""
        self.assertTrue(self.adaptor.supports_enhancement())

    def test_format_skill_md_no_frontmatter(self):
        """Test that Gemini format has no YAML frontmatter"""
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
            # Should contain the content
            self.assertIn('test-skill', formatted.lower())
            self.assertIn('Test skill description', formatted)

    def test_package_creates_targz(self):
        """Test that package creates tar.gz file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()

            # Create minimal skill structure
            (skill_dir / "SKILL.md").write_text("# Test Skill")
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "test.md").write_text("# Reference")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            # Package skill
            package_path = self.adaptor.package(skill_dir, output_dir)

            # Verify package was created
            self.assertTrue(package_path.exists())
            self.assertTrue(str(package_path).endswith('.tar.gz'))
            self.assertIn('gemini', package_path.name)

            # Verify package contents
            with tarfile.open(package_path, 'r:gz') as tar:
                names = tar.getnames()
                self.assertIn('system_instructions.md', names)
                self.assertIn('gemini_metadata.json', names)
                # Should have references
                self.assertTrue(any('references' in name for name in names))

    @unittest.skip("Complex mocking - integration test needed with real API")
    def test_upload_success(self):
        """Test successful upload to Gemini - skipped (needs real API for integration test)"""
        pass

    def test_upload_missing_library(self):
        """Test upload when google-generativeai is not installed"""
        with tempfile.NamedTemporaryFile(suffix='.tar.gz') as tmp:
            # Simulate missing library by not mocking it
            result = self.adaptor.upload(Path(tmp.name), 'AIzaSyTest')

            self.assertFalse(result['success'])
            self.assertIn('google-generativeai', result['message'])
            self.assertIn('not installed', result['message'])

    def test_upload_invalid_file(self):
        """Test upload with invalid file"""
        result = self.adaptor.upload(Path('/nonexistent/file.tar.gz'), 'AIzaSyTest')

        self.assertFalse(result['success'])
        self.assertIn('not found', result['message'].lower())

    def test_upload_wrong_format(self):
        """Test upload with wrong file format"""
        with tempfile.NamedTemporaryFile(suffix='.zip') as tmp:
            result = self.adaptor.upload(Path(tmp.name), 'AIzaSyTest')

            self.assertFalse(result['success'])
            self.assertIn('not a tar.gz', result['message'].lower())

    @unittest.skip("Complex mocking - integration test needed with real API")
    def test_enhance_success(self):
        """Test successful enhancement - skipped (needs real API for integration test)"""
        pass

    def test_enhance_missing_library(self):
        """Test enhance when google-generativeai is not installed"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            refs_dir = skill_dir / "references"
            refs_dir.mkdir()
            (refs_dir / "test.md").write_text("Test")

            # Don't mock the module - it won't be available
            success = self.adaptor.enhance(skill_dir, 'AIzaSyTest')

            self.assertFalse(success)


if __name__ == '__main__':
    unittest.main()
