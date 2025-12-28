#!/usr/bin/env python3
"""
Tests for Markdown adaptor
"""

import unittest
from pathlib import Path
import tempfile
import zipfile

from skill_seekers.cli.adaptors import get_adaptor
from skill_seekers.cli.adaptors.base import SkillMetadata


class TestMarkdownAdaptor(unittest.TestCase):
    """Test Markdown adaptor functionality"""

    def setUp(self):
        """Set up test adaptor"""
        self.adaptor = get_adaptor('markdown')

    def test_platform_info(self):
        """Test platform identifiers"""
        self.assertEqual(self.adaptor.PLATFORM, 'markdown')
        self.assertEqual(self.adaptor.PLATFORM_NAME, 'Generic Markdown (Universal)')
        self.assertIsNone(self.adaptor.DEFAULT_API_ENDPOINT)

    def test_validate_api_key(self):
        """Test that markdown export doesn't use API keys"""
        # Any key should return False (no keys needed)
        self.assertFalse(self.adaptor.validate_api_key('sk-ant-123'))
        self.assertFalse(self.adaptor.validate_api_key('AIzaSyABC123'))
        self.assertFalse(self.adaptor.validate_api_key('any-key'))
        self.assertFalse(self.adaptor.validate_api_key(''))

    def test_get_env_var_name(self):
        """Test environment variable name"""
        self.assertEqual(self.adaptor.get_env_var_name(), '')

    def test_supports_enhancement(self):
        """Test enhancement support"""
        self.assertFalse(self.adaptor.supports_enhancement())

    def test_enhance_returns_false(self):
        """Test that enhance always returns False"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            refs_dir = skill_dir / "references"
            refs_dir.mkdir()
            (refs_dir / "test.md").write_text("Test content")

            success = self.adaptor.enhance(skill_dir, 'not-used')
            self.assertFalse(success)

    def test_format_skill_md_no_frontmatter(self):
        """Test that markdown format has no YAML frontmatter"""
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
            # Should contain the skill name and description
            self.assertIn('test-skill', formatted.lower())
            self.assertIn('Test skill description', formatted)

    def test_package_creates_zip(self):
        """Test that package creates ZIP file with correct structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()

            # Create minimal skill structure
            (skill_dir / "SKILL.md").write_text("# Test Skill Documentation")
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "guide.md").write_text("# User Guide")
            (skill_dir / "references" / "api.md").write_text("# API Reference")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            # Package skill
            package_path = self.adaptor.package(skill_dir, output_dir)

            # Verify package was created
            self.assertTrue(package_path.exists())
            self.assertTrue(str(package_path).endswith('.zip'))
            self.assertIn('markdown', package_path.name)

            # Verify package contents
            with zipfile.ZipFile(package_path, 'r') as zf:
                names = zf.namelist()

                # Should have README.md (from SKILL.md)
                self.assertIn('README.md', names)

                # Should have metadata.json
                self.assertIn('metadata.json', names)

                # Should have DOCUMENTATION.md (combined)
                self.assertIn('DOCUMENTATION.md', names)

                # Should have reference files
                self.assertIn('references/guide.md', names)
                self.assertIn('references/api.md', names)

    def test_package_readme_content(self):
        """Test that README.md contains SKILL.md content"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()

            skill_md_content = "# Test Skill\n\nThis is test documentation."
            (skill_dir / "SKILL.md").write_text(skill_md_content)
            (skill_dir / "references").mkdir()

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            package_path = self.adaptor.package(skill_dir, output_dir)

            # Verify README.md content
            with zipfile.ZipFile(package_path, 'r') as zf:
                readme_content = zf.read('README.md').decode('utf-8')
                self.assertEqual(readme_content, skill_md_content)

    def test_package_combined_documentation(self):
        """Test that DOCUMENTATION.md combines all references"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()

            # Create SKILL.md
            (skill_dir / "SKILL.md").write_text("# Main Skill")

            # Create references
            refs_dir = skill_dir / "references"
            refs_dir.mkdir()
            (refs_dir / "guide.md").write_text("# Guide Content")
            (refs_dir / "api.md").write_text("# API Content")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            package_path = self.adaptor.package(skill_dir, output_dir)

            # Verify DOCUMENTATION.md contains combined content
            with zipfile.ZipFile(package_path, 'r') as zf:
                doc_content = zf.read('DOCUMENTATION.md').decode('utf-8')

                # Should contain main skill content
                self.assertIn('Main Skill', doc_content)

                # Should contain reference content
                self.assertIn('Guide Content', doc_content)
                self.assertIn('API Content', doc_content)

                # Should have separators
                self.assertIn('---', doc_content)

    def test_package_metadata(self):
        """Test that metadata.json is correct"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()

            (skill_dir / "SKILL.md").write_text("# Test")
            (skill_dir / "references").mkdir()

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            package_path = self.adaptor.package(skill_dir, output_dir)

            # Verify metadata
            with zipfile.ZipFile(package_path, 'r') as zf:
                import json
                metadata_content = zf.read('metadata.json').decode('utf-8')
                metadata = json.loads(metadata_content)

                self.assertEqual(metadata['platform'], 'markdown')
                self.assertEqual(metadata['name'], 'test-skill')
                self.assertEqual(metadata['format'], 'universal_markdown')
                self.assertIn('created_with', metadata)

    def test_upload_not_supported(self):
        """Test that upload returns appropriate message"""
        with tempfile.NamedTemporaryFile(suffix='.zip') as tmp:
            result = self.adaptor.upload(Path(tmp.name), 'not-used')

            self.assertFalse(result['success'])
            self.assertIsNone(result['skill_id'])
            self.assertIn('not support', result['message'].lower())
            # URL should point to local file
            self.assertIn(tmp.name, result['url'])

    def test_package_output_filename(self):
        """Test that package creates correct filename"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "my-framework"
            skill_dir.mkdir()

            (skill_dir / "SKILL.md").write_text("# Test")
            (skill_dir / "references").mkdir()

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            package_path = self.adaptor.package(skill_dir, output_dir)

            # Should include skill name and 'markdown' suffix
            self.assertTrue(package_path.name.startswith('my-framework'))
            self.assertIn('markdown', package_path.name)
            self.assertTrue(package_path.name.endswith('.zip'))


if __name__ == '__main__':
    unittest.main()
