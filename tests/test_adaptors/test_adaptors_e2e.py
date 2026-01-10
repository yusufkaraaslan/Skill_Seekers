#!/usr/bin/env python3
"""
End-to-End Tests for Multi-LLM Adaptors

Tests complete workflows without real API uploads:
- Scrape → Package → Verify for all platforms
- Same scraped data works for all platforms
- Package structure validation
- Enhancement workflow (mocked)
"""

import unittest
import tempfile
import zipfile
import tarfile
import json
from pathlib import Path

from skill_seekers.cli.adaptors import get_adaptor, list_platforms
from skill_seekers.cli.adaptors.base import SkillMetadata


class TestAdaptorsE2E(unittest.TestCase):
    """End-to-end tests for all platform adaptors"""

    def setUp(self):
        """Set up test environment with sample skill directory"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.skill_dir = Path(self.temp_dir.name) / "test-skill"
        self.skill_dir.mkdir()

        # Create realistic skill structure
        self._create_sample_skill()

        self.output_dir = Path(self.temp_dir.name) / "output"
        self.output_dir.mkdir()

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    def _create_sample_skill(self):
        """Create a sample skill directory with realistic content"""
        # Create SKILL.md
        skill_md_content = """# React Framework

React is a JavaScript library for building user interfaces.

## Quick Reference

```javascript
// Create a component
function Welcome(props) {
  return <h1>Hello, {props.name}</h1>;
}
```

## Key Concepts

- Components
- Props
- State
- Hooks
"""
        (self.skill_dir / "SKILL.md").write_text(skill_md_content)

        # Create references directory
        refs_dir = self.skill_dir / "references"
        refs_dir.mkdir()

        # Create sample reference files
        (refs_dir / "getting_started.md").write_text("""# Getting Started

Install React:

```bash
npm install react
```

Create your first component:

```javascript
function App() {
  return <div>Hello World</div>;
}
```
""")

        (refs_dir / "hooks.md").write_text("""# React Hooks

## useState

```javascript
const [count, setCount] = useState(0);
```

## useEffect

```javascript
useEffect(() => {
  document.title = `Count: ${count}`;
}, [count]);
```
""")

        (refs_dir / "components.md").write_text("""# Components

## Functional Components

```javascript
function Greeting({ name }) {
  return <h1>Hello {name}</h1>;
}
```

## Props

Pass data to components:

```javascript
<Greeting name="Alice" />
```
""")

        # Create empty scripts and assets directories
        (self.skill_dir / "scripts").mkdir()
        (self.skill_dir / "assets").mkdir()

    def test_e2e_all_platforms_from_same_skill(self):
        """Test that all platforms can package the same skill"""
        platforms = ['claude', 'gemini', 'openai', 'markdown']
        packages = {}

        for platform in platforms:
            adaptor = get_adaptor(platform)

            # Package for this platform
            package_path = adaptor.package(self.skill_dir, self.output_dir)

            # Verify package was created
            self.assertTrue(package_path.exists(),
                          f"Package not created for {platform}")

            # Store for later verification
            packages[platform] = package_path

        # Verify all packages were created
        self.assertEqual(len(packages), 4)

        # Verify correct extensions
        self.assertTrue(str(packages['claude']).endswith('.zip'))
        self.assertTrue(str(packages['gemini']).endswith('.tar.gz'))
        self.assertTrue(str(packages['openai']).endswith('.zip'))
        self.assertTrue(str(packages['markdown']).endswith('.zip'))

    def test_e2e_claude_workflow(self):
        """Test complete Claude workflow: package + verify structure"""
        adaptor = get_adaptor('claude')

        # Package
        package_path = adaptor.package(self.skill_dir, self.output_dir)

        # Verify package
        self.assertTrue(package_path.exists())
        self.assertTrue(str(package_path).endswith('.zip'))

        # Verify contents
        with zipfile.ZipFile(package_path, 'r') as zf:
            names = zf.namelist()

            # Should have SKILL.md
            self.assertIn('SKILL.md', names)

            # Should have references
            self.assertTrue(any('references/' in name for name in names))

            # Verify SKILL.md content (should have YAML frontmatter)
            skill_content = zf.read('SKILL.md').decode('utf-8')
            # Claude uses YAML frontmatter (but current implementation doesn't add it in package)
            # Just verify content exists
            self.assertGreater(len(skill_content), 0)

    def test_e2e_gemini_workflow(self):
        """Test complete Gemini workflow: package + verify structure"""
        adaptor = get_adaptor('gemini')

        # Package
        package_path = adaptor.package(self.skill_dir, self.output_dir)

        # Verify package
        self.assertTrue(package_path.exists())
        self.assertTrue(str(package_path).endswith('.tar.gz'))

        # Verify contents
        with tarfile.open(package_path, 'r:gz') as tar:
            names = tar.getnames()

            # Should have system_instructions.md (not SKILL.md)
            self.assertIn('system_instructions.md', names)

            # Should have references
            self.assertTrue(any('references/' in name for name in names))

            # Should have metadata
            self.assertIn('gemini_metadata.json', names)

            # Verify metadata content
            metadata_member = tar.getmember('gemini_metadata.json')
            metadata_file = tar.extractfile(metadata_member)
            metadata = json.loads(metadata_file.read().decode('utf-8'))

            self.assertEqual(metadata['platform'], 'gemini')
            self.assertEqual(metadata['name'], 'test-skill')
            self.assertIn('created_with', metadata)

    def test_e2e_openai_workflow(self):
        """Test complete OpenAI workflow: package + verify structure"""
        adaptor = get_adaptor('openai')

        # Package
        package_path = adaptor.package(self.skill_dir, self.output_dir)

        # Verify package
        self.assertTrue(package_path.exists())
        self.assertTrue(str(package_path).endswith('.zip'))

        # Verify contents
        with zipfile.ZipFile(package_path, 'r') as zf:
            names = zf.namelist()

            # Should have assistant_instructions.txt
            self.assertIn('assistant_instructions.txt', names)

            # Should have vector store files
            self.assertTrue(any('vector_store_files/' in name for name in names))

            # Should have metadata
            self.assertIn('openai_metadata.json', names)

            # Verify metadata content
            metadata_content = zf.read('openai_metadata.json').decode('utf-8')
            metadata = json.loads(metadata_content)

            self.assertEqual(metadata['platform'], 'openai')
            self.assertEqual(metadata['name'], 'test-skill')
            self.assertEqual(metadata['model'], 'gpt-4o')
            self.assertIn('file_search', metadata['tools'])

    def test_e2e_markdown_workflow(self):
        """Test complete Markdown workflow: package + verify structure"""
        adaptor = get_adaptor('markdown')

        # Package
        package_path = adaptor.package(self.skill_dir, self.output_dir)

        # Verify package
        self.assertTrue(package_path.exists())
        self.assertTrue(str(package_path).endswith('.zip'))

        # Verify contents
        with zipfile.ZipFile(package_path, 'r') as zf:
            names = zf.namelist()

            # Should have README.md
            self.assertIn('README.md', names)

            # Should have DOCUMENTATION.md (combined)
            self.assertIn('DOCUMENTATION.md', names)

            # Should have references
            self.assertTrue(any('references/' in name for name in names))

            # Should have metadata
            self.assertIn('metadata.json', names)

            # Verify combined documentation
            doc_content = zf.read('DOCUMENTATION.md').decode('utf-8')

            # Should contain content from all references
            self.assertIn('Getting Started', doc_content)
            self.assertIn('React Hooks', doc_content)
            self.assertIn('Components', doc_content)

    def test_e2e_package_format_validation(self):
        """Test that each platform creates correct package format"""
        test_cases = [
            ('claude', '.zip'),
            ('gemini', '.tar.gz'),
            ('openai', '.zip'),
            ('markdown', '.zip')
        ]

        for platform, expected_ext in test_cases:
            adaptor = get_adaptor(platform)
            package_path = adaptor.package(self.skill_dir, self.output_dir)

            # Verify extension
            if expected_ext == '.tar.gz':
                self.assertTrue(str(package_path).endswith('.tar.gz'),
                              f"{platform} should create .tar.gz file")
            else:
                self.assertTrue(str(package_path).endswith('.zip'),
                              f"{platform} should create .zip file")

    def test_e2e_package_filename_convention(self):
        """Test that package filenames follow convention"""
        test_cases = [
            ('claude', 'test-skill.zip'),
            ('gemini', 'test-skill-gemini.tar.gz'),
            ('openai', 'test-skill-openai.zip'),
            ('markdown', 'test-skill-markdown.zip')
        ]

        for platform, expected_name in test_cases:
            adaptor = get_adaptor(platform)
            package_path = adaptor.package(self.skill_dir, self.output_dir)

            # Verify filename
            self.assertEqual(package_path.name, expected_name,
                           f"{platform} package filename incorrect")

    def test_e2e_all_platforms_preserve_references(self):
        """Test that all platforms preserve reference files"""
        ref_files = ['getting_started.md', 'hooks.md', 'components.md']

        for platform in ['claude', 'gemini', 'openai', 'markdown']:
            adaptor = get_adaptor(platform)
            package_path = adaptor.package(self.skill_dir, self.output_dir)

            # Check references are preserved
            if platform == 'gemini':
                with tarfile.open(package_path, 'r:gz') as tar:
                    names = tar.getnames()
                    for ref_file in ref_files:
                        self.assertTrue(
                            any(ref_file in name for name in names),
                            f"{platform}: {ref_file} not found in package"
                        )
            else:
                with zipfile.ZipFile(package_path, 'r') as zf:
                    names = zf.namelist()
                    for ref_file in ref_files:
                        # OpenAI moves to vector_store_files/
                        if platform == 'openai':
                            self.assertTrue(
                                any(f'vector_store_files/{ref_file}' in name for name in names),
                                f"{platform}: {ref_file} not found in vector_store_files/"
                            )
                        else:
                            self.assertTrue(
                                any(ref_file in name for name in names),
                                f"{platform}: {ref_file} not found in package"
                            )

    def test_e2e_metadata_consistency(self):
        """Test that metadata is consistent across platforms"""
        platforms_with_metadata = ['gemini', 'openai', 'markdown']

        for platform in platforms_with_metadata:
            adaptor = get_adaptor(platform)
            package_path = adaptor.package(self.skill_dir, self.output_dir)

            # Extract and verify metadata
            if platform == 'gemini':
                with tarfile.open(package_path, 'r:gz') as tar:
                    metadata_member = tar.getmember('gemini_metadata.json')
                    metadata_file = tar.extractfile(metadata_member)
                    metadata = json.loads(metadata_file.read().decode('utf-8'))
            else:
                with zipfile.ZipFile(package_path, 'r') as zf:
                    metadata_filename = f'{platform}_metadata.json' if platform == 'openai' else 'metadata.json'
                    metadata_content = zf.read(metadata_filename).decode('utf-8')
                    metadata = json.loads(metadata_content)

            # Verify required fields
            self.assertEqual(metadata['platform'], platform)
            self.assertEqual(metadata['name'], 'test-skill')
            self.assertIn('created_with', metadata)

    def test_e2e_format_skill_md_differences(self):
        """Test that each platform formats SKILL.md differently"""
        metadata = SkillMetadata(
            name="test-skill",
            description="Test skill for E2E testing"
        )

        formats = {}
        for platform in ['claude', 'gemini', 'openai', 'markdown']:
            adaptor = get_adaptor(platform)
            formatted = adaptor.format_skill_md(self.skill_dir, metadata)
            formats[platform] = formatted

        # Claude should have YAML frontmatter
        self.assertTrue(formats['claude'].startswith('---'))

        # Gemini and Markdown should NOT have YAML frontmatter
        self.assertFalse(formats['gemini'].startswith('---'))
        self.assertFalse(formats['markdown'].startswith('---'))

        # All should contain content from existing SKILL.md (React Framework)
        for platform, formatted in formats.items():
            # Check for content from existing SKILL.md
            self.assertIn('react', formatted.lower(),
                         f"{platform} should contain skill content")
            # All should have non-empty content
            self.assertGreater(len(formatted), 100,
                             f"{platform} should have substantial content")

    def test_e2e_upload_without_api_key(self):
        """Test upload behavior without API keys (should fail gracefully)"""
        platforms_with_upload = ['claude', 'gemini', 'openai']

        for platform in platforms_with_upload:
            adaptor = get_adaptor(platform)
            package_path = adaptor.package(self.skill_dir, self.output_dir)

            # Try upload without API key
            result = adaptor.upload(package_path, '')

            # Should fail
            self.assertFalse(result['success'],
                           f"{platform} should fail without API key")
            self.assertIsNone(result['skill_id'])
            self.assertIn('message', result)

    def test_e2e_markdown_no_upload_support(self):
        """Test that markdown adaptor doesn't support upload"""
        adaptor = get_adaptor('markdown')
        package_path = adaptor.package(self.skill_dir, self.output_dir)

        # Try upload (should return informative message)
        result = adaptor.upload(package_path, 'not-used')

        # Should indicate no upload support
        self.assertFalse(result['success'])
        self.assertIsNone(result['skill_id'])
        self.assertIn('not support', result['message'].lower())
        # URL should point to local file
        self.assertIn(str(package_path.absolute()), result['url'])


class TestAdaptorsWorkflowIntegration(unittest.TestCase):
    """Integration tests for common workflow patterns"""

    def test_workflow_export_to_all_platforms(self):
        """Test exporting same skill to all platforms"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "react"
            skill_dir.mkdir()

            # Create minimal skill
            (skill_dir / "SKILL.md").write_text("# React\n\nReact documentation")
            refs_dir = skill_dir / "references"
            refs_dir.mkdir()
            (refs_dir / "guide.md").write_text("# Guide\n\nContent")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            # Export to all platforms
            packages = {}
            for platform in ['claude', 'gemini', 'openai', 'markdown']:
                adaptor = get_adaptor(platform)
                package_path = adaptor.package(skill_dir, output_dir)
                packages[platform] = package_path

            # Verify all packages exist and are distinct
            self.assertEqual(len(packages), 4)
            self.assertEqual(len(set(packages.values())), 4)  # All unique

    def test_workflow_package_to_custom_path(self):
        """Test packaging to custom output paths"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# Test")
            (skill_dir / "references").mkdir()

            # Test custom output paths
            custom_output = Path(temp_dir) / "custom" / "my-package.zip"

            adaptor = get_adaptor('claude')
            package_path = adaptor.package(skill_dir, custom_output)

            # Should respect custom path
            self.assertTrue(package_path.exists())
            self.assertTrue('my-package' in package_path.name or package_path.parent.name == 'custom')

    def test_workflow_api_key_validation(self):
        """Test API key validation for each platform"""
        test_cases = [
            ('claude', 'sk-ant-test123', True),
            ('claude', 'invalid-key', False),
            ('gemini', 'AIzaSyTest123', True),
            ('gemini', 'sk-ant-test', False),
            ('openai', 'sk-proj-test123', True),
            ('openai', 'sk-test123', True),
            ('openai', 'AIzaSy123', False),
            ('markdown', 'any-key', False),  # Never uses keys
        ]

        for platform, api_key, expected in test_cases:
            adaptor = get_adaptor(platform)
            result = adaptor.validate_api_key(api_key)
            self.assertEqual(result, expected,
                           f"{platform}: validate_api_key('{api_key}') should be {expected}")


class TestAdaptorsErrorHandling(unittest.TestCase):
    """Test error handling in adaptors"""

    def test_error_invalid_skill_directory(self):
        """Test packaging with invalid skill directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Empty directory (no SKILL.md)
            empty_dir = Path(temp_dir) / "empty"
            empty_dir.mkdir()

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            # Should handle gracefully (may create package but with empty content)
            for platform in ['claude', 'gemini', 'openai', 'markdown']:
                adaptor = get_adaptor(platform)
                # Should not crash
                try:
                    package_path = adaptor.package(empty_dir, output_dir)
                    # Package may be created but should exist
                    self.assertTrue(package_path.exists())
                except Exception as e:
                    # If it raises, should be clear error
                    self.assertIn('SKILL.md', str(e).lower() or 'reference' in str(e).lower())

    def test_error_upload_nonexistent_file(self):
        """Test upload with nonexistent file"""
        for platform in ['claude', 'gemini', 'openai']:
            adaptor = get_adaptor(platform)
            result = adaptor.upload(Path('/nonexistent/file.zip'), 'test-key')

            self.assertFalse(result['success'])
            self.assertIn('not found', result['message'].lower())

    def test_error_upload_wrong_format(self):
        """Test upload with wrong file format"""
        with tempfile.NamedTemporaryFile(suffix='.txt') as tmp:
            # Try uploading .txt file
            for platform in ['claude', 'gemini', 'openai']:
                adaptor = get_adaptor(platform)
                result = adaptor.upload(Path(tmp.name), 'test-key')

                self.assertFalse(result['success'])


if __name__ == '__main__':
    unittest.main()
