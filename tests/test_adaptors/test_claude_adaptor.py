#!/usr/bin/env python3
"""
Tests for Claude adaptor (refactored from existing code)
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import zipfile
import json

from skill_seekers.cli.adaptors import get_adaptor
from skill_seekers.cli.adaptors.base import SkillMetadata


class TestClaudeAdaptor(unittest.TestCase):
    """Test Claude adaptor functionality"""

    def setUp(self):
        """Set up test adaptor"""
        self.adaptor = get_adaptor('claude')

    def test_platform_info(self):
        """Test platform identifiers"""
        self.assertEqual(self.adaptor.PLATFORM, 'claude')
        self.assertIn('Claude', self.adaptor.PLATFORM_NAME)
        self.assertIsNotNone(self.adaptor.DEFAULT_API_ENDPOINT)
        self.assertIn('anthropic.com', self.adaptor.DEFAULT_API_ENDPOINT)

    def test_validate_api_key_valid(self):
        """Test valid Claude API keys"""
        self.assertTrue(self.adaptor.validate_api_key('sk-ant-abc123'))
        self.assertTrue(self.adaptor.validate_api_key('sk-ant-api03-test'))
        self.assertTrue(self.adaptor.validate_api_key('  sk-ant-test  '))  # with whitespace

    def test_validate_api_key_invalid(self):
        """Test invalid API keys"""
        self.assertFalse(self.adaptor.validate_api_key('AIzaSyABC123'))  # Gemini key
        self.assertFalse(self.adaptor.validate_api_key('sk-proj-123'))  # OpenAI key (proj)
        self.assertFalse(self.adaptor.validate_api_key('invalid'))
        self.assertFalse(self.adaptor.validate_api_key(''))
        self.assertFalse(self.adaptor.validate_api_key('sk-test'))  # Missing 'ant'

    def test_get_env_var_name(self):
        """Test environment variable name"""
        self.assertEqual(self.adaptor.get_env_var_name(), 'ANTHROPIC_API_KEY')

    def test_supports_enhancement(self):
        """Test enhancement support"""
        self.assertTrue(self.adaptor.supports_enhancement())

    def test_format_skill_md_with_frontmatter(self):
        """Test that Claude format includes YAML frontmatter"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)

            # Create minimal skill structure
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "test.md").write_text("# Test content")

            metadata = SkillMetadata(
                name="test-skill",
                description="Test skill description",
                version="1.0.0"
            )

            formatted = self.adaptor.format_skill_md(skill_dir, metadata)

            # Should start with YAML frontmatter
            self.assertTrue(formatted.startswith('---'))
            # Should contain metadata fields
            self.assertIn('name:', formatted)
            self.assertIn('description:', formatted)
            self.assertIn('version:', formatted)
            # Should have closing delimiter
            self.assertTrue('---' in formatted[3:])  # Second occurrence

    def test_format_skill_md_with_existing_content(self):
        """Test that existing SKILL.md content is preserved"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)

            # Create SKILL.md with existing content
            existing_content = """# Existing Documentation

This is existing skill content that should be preserved.

## Features
- Feature 1
- Feature 2
"""
            (skill_dir / "SKILL.md").write_text(existing_content)
            (skill_dir / "references").mkdir()

            metadata = SkillMetadata(
                name="test-skill",
                description="Test description"
            )

            formatted = self.adaptor.format_skill_md(skill_dir, metadata)

            # Should contain existing content
            self.assertIn('Existing Documentation', formatted)
            self.assertIn('Feature 1', formatted)

    def test_package_creates_zip(self):
        """Test that package creates ZIP file with correct structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()

            # Create minimal skill structure
            (skill_dir / "SKILL.md").write_text("# Test Skill")
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "test.md").write_text("# Reference")
            (skill_dir / "scripts").mkdir()
            (skill_dir / "assets").mkdir()

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            # Package skill
            package_path = self.adaptor.package(skill_dir, output_dir)

            # Verify package was created
            self.assertTrue(package_path.exists())
            self.assertTrue(str(package_path).endswith('.zip'))
            # Should NOT have platform suffix (Claude is default)
            self.assertEqual(package_path.name, 'test-skill.zip')

            # Verify package contents
            with zipfile.ZipFile(package_path, 'r') as zf:
                names = zf.namelist()
                self.assertIn('SKILL.md', names)
                self.assertTrue(any('references/' in name for name in names))

    def test_package_excludes_backup_files(self):
        """Test that backup files are excluded from package"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()

            # Create skill with backup file
            (skill_dir / "SKILL.md").write_text("# Test")
            (skill_dir / "SKILL.md.backup").write_text("# Old version")
            (skill_dir / "references").mkdir()

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            package_path = self.adaptor.package(skill_dir, output_dir)

            # Verify backup is excluded
            with zipfile.ZipFile(package_path, 'r') as zf:
                names = zf.namelist()
                self.assertNotIn('SKILL.md.backup', names)

    @patch('requests.post')
    def test_upload_success(self, mock_post):
        """Test successful upload to Claude"""
        with tempfile.NamedTemporaryFile(suffix='.zip') as tmp:
            # Mock successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'id': 'skill_abc123'}
            mock_post.return_value = mock_response

            result = self.adaptor.upload(Path(tmp.name), 'sk-ant-test123')

            self.assertTrue(result['success'])
            self.assertEqual(result['skill_id'], 'skill_abc123')
            self.assertIn('claude.ai', result['url'])

            # Verify correct API call
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            self.assertIn('anthropic.com', call_args[0][0])
            self.assertEqual(call_args[1]['headers']['x-api-key'], 'sk-ant-test123')

    @patch('requests.post')
    def test_upload_failure(self, mock_post):
        """Test failed upload to Claude"""
        with tempfile.NamedTemporaryFile(suffix='.zip') as tmp:
            # Mock failed response
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = 'Invalid skill format'
            mock_post.return_value = mock_response

            result = self.adaptor.upload(Path(tmp.name), 'sk-ant-test123')

            self.assertFalse(result['success'])
            self.assertIsNone(result['skill_id'])
            self.assertIn('Invalid skill format', result['message'])

    def test_upload_invalid_file(self):
        """Test upload with invalid file"""
        result = self.adaptor.upload(Path('/nonexistent/file.zip'), 'sk-ant-test123')

        self.assertFalse(result['success'])
        self.assertIn('not found', result['message'].lower())

    def test_upload_wrong_format(self):
        """Test upload with wrong file format"""
        with tempfile.NamedTemporaryFile(suffix='.tar.gz') as tmp:
            result = self.adaptor.upload(Path(tmp.name), 'sk-ant-test123')

            self.assertFalse(result['success'])
            self.assertIn('not a zip', result['message'].lower())

    @unittest.skip("Complex mocking - integration test needed with real API")
    def test_enhance_success(self):
        """Test successful enhancement - skipped (needs real API for integration test)"""
        pass

    def test_package_with_custom_output_path(self):
        """Test packaging to custom output path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "my-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# Test")
            (skill_dir / "references").mkdir()

            # Custom output path
            custom_output = Path(temp_dir) / "custom" / "my-package.zip"

            package_path = self.adaptor.package(skill_dir, custom_output)

            self.assertTrue(package_path.exists())
            # Should respect custom naming if provided
            self.assertTrue('my-package' in package_path.name or package_path.parent.name == 'custom')

    def test_package_to_directory(self):
        """Test packaging to directory (should auto-name)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "react"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# React")
            (skill_dir / "references").mkdir()

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            # Pass directory as output
            package_path = self.adaptor.package(skill_dir, output_dir)

            self.assertTrue(package_path.exists())
            self.assertEqual(package_path.name, 'react.zip')
            self.assertEqual(package_path.parent, output_dir)


class TestClaudeAdaptorEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""

    def setUp(self):
        """Set up test adaptor"""
        self.adaptor = get_adaptor('claude')

    def test_format_with_minimal_metadata(self):
        """Test formatting with only required metadata fields"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            (skill_dir / "references").mkdir()

            metadata = SkillMetadata(
                name="minimal",
                description="Minimal skill"
                # No version, author, tags
            )

            formatted = self.adaptor.format_skill_md(skill_dir, metadata)

            # Should still create valid output
            self.assertIn('---', formatted)
            self.assertIn('minimal', formatted)

    def test_format_with_special_characters_in_name(self):
        """Test formatting with special characters in skill name"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            (skill_dir / "references").mkdir()

            metadata = SkillMetadata(
                name="test-skill_v2.0",
                description="Skill with special chars"
            )

            formatted = self.adaptor.format_skill_md(skill_dir, metadata)

            # Should handle special characters
            self.assertIn('test-skill_v2.0', formatted)

    def test_api_key_validation_edge_cases(self):
        """Test API key validation with edge cases"""
        # Empty string
        self.assertFalse(self.adaptor.validate_api_key(''))

        # Only whitespace
        self.assertFalse(self.adaptor.validate_api_key('   '))

        # Correct prefix but very short
        self.assertTrue(self.adaptor.validate_api_key('sk-ant-x'))

        # Case sensitive
        self.assertFalse(self.adaptor.validate_api_key('SK-ANT-TEST'))

    def test_upload_with_network_error(self):
        """Test upload with network errors"""
        with tempfile.NamedTemporaryFile(suffix='.zip') as tmp:
            with patch('requests.post') as mock_post:
                # Simulate network error
                mock_post.side_effect = Exception("Network error")

                result = self.adaptor.upload(Path(tmp.name), 'sk-ant-test')

                self.assertFalse(result['success'])
                self.assertIn('Network error', result['message'])


if __name__ == '__main__':
    unittest.main()
