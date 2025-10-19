#!/usr/bin/env python3
"""
Integration tests for doc_scraper
Tests complete workflows and dry-run mode
"""

import sys
import os
import unittest
import json
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli.doc_scraper import DocToSkillConverter, load_config, validate_config


class TestDryRunMode(unittest.TestCase):
    """Test dry-run mode functionality"""

    def setUp(self):
        """Set up test configuration"""
        self.config = {
            'name': 'test-dry-run',
            'base_url': 'https://example.com/',
            'selectors': {
                'main_content': 'article',
                'title': 'h1',
                'code_blocks': 'pre code'
            },
            'url_patterns': {
                'include': [],
                'exclude': []
            },
            'rate_limit': 0.1,
            'max_pages': 10
        }

    def test_dry_run_no_directories_created(self):
        """Test that dry-run mode doesn't create directories"""
        converter = DocToSkillConverter(self.config, dry_run=True)

        # Check directories were NOT created
        data_dir = Path(f"output/{self.config['name']}_data")
        skill_dir = Path(f"output/{self.config['name']}")

        self.assertFalse(data_dir.exists(), "Dry-run should not create data directory")
        self.assertFalse(skill_dir.exists(), "Dry-run should not create skill directory")

    def test_dry_run_flag_set(self):
        """Test that dry_run flag is properly set"""
        converter = DocToSkillConverter(self.config, dry_run=True)
        self.assertTrue(converter.dry_run)

        converter_normal = DocToSkillConverter(self.config, dry_run=False)
        self.assertFalse(converter_normal.dry_run)

        # Clean up
        shutil.rmtree(f"output/{self.config['name']}_data", ignore_errors=True)
        shutil.rmtree(f"output/{self.config['name']}", ignore_errors=True)

    def test_normal_mode_creates_directories(self):
        """Test that normal mode creates directories"""
        converter = DocToSkillConverter(self.config, dry_run=False)

        # Check directories WERE created
        data_dir = Path(f"output/{self.config['name']}_data")
        skill_dir = Path(f"output/{self.config['name']}")

        self.assertTrue(data_dir.exists(), "Normal mode should create data directory")
        self.assertTrue(skill_dir.exists(), "Normal mode should create skill directory")

        # Clean up
        shutil.rmtree(data_dir, ignore_errors=True)
        shutil.rmtree(skill_dir, ignore_errors=True)


class TestConfigLoading(unittest.TestCase):
    """Test configuration loading and validation"""

    def setUp(self):
        """Set up temporary directory for test configs"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_valid_config(self):
        """Test loading a valid configuration file"""
        config_data = {
            'name': 'test-config',
            'base_url': 'https://example.com/',
            'selectors': {
                'main_content': 'article',
                'title': 'h1',
                'code_blocks': 'pre code'
            },
            'rate_limit': 0.5,
            'max_pages': 100
        }

        config_path = Path(self.temp_dir) / 'test.json'
        with open(config_path, 'w') as f:
            json.dump(config_data, f)

        loaded_config = load_config(str(config_path))
        self.assertEqual(loaded_config['name'], 'test-config')
        self.assertEqual(loaded_config['base_url'], 'https://example.com/')

    def test_load_invalid_json(self):
        """Test loading an invalid JSON file"""
        config_path = Path(self.temp_dir) / 'invalid.json'
        with open(config_path, 'w') as f:
            f.write('{ invalid json }')

        with self.assertRaises(SystemExit):
            load_config(str(config_path))

    def test_load_nonexistent_file(self):
        """Test loading a nonexistent file"""
        config_path = Path(self.temp_dir) / 'nonexistent.json'

        with self.assertRaises(SystemExit):
            load_config(str(config_path))

    def test_load_config_with_validation_errors(self):
        """Test loading a config with validation errors"""
        config_data = {
            'name': 'invalid@name',  # Invalid name
            'base_url': 'example.com'  # Missing protocol
        }

        config_path = Path(self.temp_dir) / 'invalid_config.json'
        with open(config_path, 'w') as f:
            json.dump(config_data, f)

        with self.assertRaises(SystemExit):
            load_config(str(config_path))


class TestRealConfigFiles(unittest.TestCase):
    """Test that real config files in the repository are valid"""

    def test_godot_config(self):
        """Test Godot config is valid"""
        config_path = 'configs/godot.json'
        if os.path.exists(config_path):
            config = load_config(config_path)
            errors, _ = validate_config(config)
            self.assertEqual(len(errors), 0, f"Godot config should be valid, got errors: {errors}")

    def test_react_config(self):
        """Test React config is valid"""
        config_path = 'configs/react.json'
        if os.path.exists(config_path):
            config = load_config(config_path)
            errors, _ = validate_config(config)
            self.assertEqual(len(errors), 0, f"React config should be valid, got errors: {errors}")

    def test_vue_config(self):
        """Test Vue config is valid"""
        config_path = 'configs/vue.json'
        if os.path.exists(config_path):
            config = load_config(config_path)
            errors, _ = validate_config(config)
            self.assertEqual(len(errors), 0, f"Vue config should be valid, got errors: {errors}")

    def test_django_config(self):
        """Test Django config is valid"""
        config_path = 'configs/django.json'
        if os.path.exists(config_path):
            config = load_config(config_path)
            errors, _ = validate_config(config)
            self.assertEqual(len(errors), 0, f"Django config should be valid, got errors: {errors}")

    def test_fastapi_config(self):
        """Test FastAPI config is valid"""
        config_path = 'configs/fastapi.json'
        if os.path.exists(config_path):
            config = load_config(config_path)
            errors, _ = validate_config(config)
            self.assertEqual(len(errors), 0, f"FastAPI config should be valid, got errors: {errors}")

    def test_steam_economy_config(self):
        """Test Steam Economy config is valid"""
        config_path = 'configs/steam-economy-complete.json'
        if os.path.exists(config_path):
            config = load_config(config_path)
            errors, _ = validate_config(config)
            self.assertEqual(len(errors), 0, f"Steam Economy config should be valid, got errors: {errors}")


class TestURLProcessing(unittest.TestCase):
    """Test URL processing and validation"""

    def test_url_normalization(self):
        """Test URL normalization in converter"""
        config = {
            'name': 'test',
            'base_url': 'https://example.com/',
            'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre'},
            'url_patterns': {'include': [], 'exclude': []},
            'rate_limit': 0.1,
            'max_pages': 10
        }
        converter = DocToSkillConverter(config, dry_run=True)

        # Base URL should be stored correctly
        self.assertEqual(converter.base_url, 'https://example.com/')

    def test_start_urls_fallback(self):
        """Test that start_urls defaults to base_url"""
        config = {
            'name': 'test',
            'base_url': 'https://example.com/',
            'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre'},
            'rate_limit': 0.1,
            'max_pages': 10
        }
        converter = DocToSkillConverter(config, dry_run=True)

        # Should have base_url in pending_urls
        self.assertEqual(len(converter.pending_urls), 1)
        self.assertEqual(converter.pending_urls[0], 'https://example.com/')

    def test_multiple_start_urls(self):
        """Test multiple start URLs"""
        config = {
            'name': 'test',
            'base_url': 'https://example.com/',
            'start_urls': [
                'https://example.com/guide/',
                'https://example.com/api/',
                'https://example.com/tutorial/'
            ],
            'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre'},
            'rate_limit': 0.1,
            'max_pages': 10
        }
        converter = DocToSkillConverter(config, dry_run=True)

        # Should have all start URLs in pending_urls
        self.assertEqual(len(converter.pending_urls), 3)


class TestContentExtraction(unittest.TestCase):
    """Test content extraction functionality"""

    def setUp(self):
        """Set up test converter"""
        config = {
            'name': 'test',
            'base_url': 'https://example.com/',
            'selectors': {
                'main_content': 'article',
                'title': 'h1',
                'code_blocks': 'pre code'
            },
            'rate_limit': 0.1,
            'max_pages': 10
        }
        self.converter = DocToSkillConverter(config, dry_run=True)

    def test_extract_empty_content(self):
        """Test extracting from empty HTML"""
        from bs4 import BeautifulSoup
        html = '<html><body></body></html>'
        soup = BeautifulSoup(html, 'html.parser')

        page = self.converter.extract_content(soup, 'https://example.com/test')

        self.assertEqual(page['url'], 'https://example.com/test')
        self.assertEqual(page['title'], '')
        self.assertEqual(page['content'], '')
        self.assertEqual(len(page['code_samples']), 0)

    def test_extract_basic_content(self):
        """Test extracting basic content"""
        from bs4 import BeautifulSoup
        html = '''
        <html>
        <head><title>Test Page</title></head>
        <body>
            <article>
                <h1>Page Title</h1>
                <p>This is some content.</p>
                <p>This is more content with sufficient length to be included.</p>
                <pre><code class="language-python">print("hello")</code></pre>
            </article>
        </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        page = self.converter.extract_content(soup, 'https://example.com/test')

        self.assertEqual(page['url'], 'https://example.com/test')
        self.assertIn('Page Title', page['title'])
        self.assertIn('content', page['content'].lower())
        self.assertGreater(len(page['code_samples']), 0)
        self.assertEqual(page['code_samples'][0]['language'], 'python')


if __name__ == '__main__':
    unittest.main()
