#!/usr/bin/env python3
"""
Test suite for doc_scraper core features
Tests URL validation, language detection, pattern extraction, and categorization
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock
from bs4 import BeautifulSoup

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli.doc_scraper import DocToSkillConverter


class TestURLValidation(unittest.TestCase):
    """Test URL validation logic"""

    def setUp(self):
        """Set up test converter"""
        self.config = {
            'name': 'test',
            'base_url': 'https://docs.example.com/',
            'url_patterns': {
                'include': ['/guide/', '/api/'],
                'exclude': ['/blog/', '/about/']
            },
            'selectors': {
                'main_content': 'article',
                'title': 'h1',
                'code_blocks': 'pre code'
            },
            'rate_limit': 0.1,
            'max_pages': 10
        }
        self.converter = DocToSkillConverter(self.config, dry_run=True)

    def test_valid_url_with_include_pattern(self):
        """Test URL matching include pattern"""
        url = 'https://docs.example.com/guide/getting-started'
        self.assertTrue(self.converter.is_valid_url(url))

    def test_valid_url_with_api_pattern(self):
        """Test URL matching API pattern"""
        url = 'https://docs.example.com/api/reference'
        self.assertTrue(self.converter.is_valid_url(url))

    def test_invalid_url_with_exclude_pattern(self):
        """Test URL matching exclude pattern"""
        url = 'https://docs.example.com/blog/announcement'
        self.assertFalse(self.converter.is_valid_url(url))

    def test_invalid_url_different_domain(self):
        """Test URL from different domain"""
        url = 'https://other-site.com/guide/tutorial'
        self.assertFalse(self.converter.is_valid_url(url))

    def test_invalid_url_no_include_match(self):
        """Test URL not matching any include pattern"""
        url = 'https://docs.example.com/download/installer'
        self.assertFalse(self.converter.is_valid_url(url))

    def test_url_validation_no_patterns(self):
        """Test URL validation with no include/exclude patterns"""
        config = {
            'name': 'test',
            'base_url': 'https://docs.example.com/',
            'url_patterns': {
                'include': [],
                'exclude': []
            },
            'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre'},
            'rate_limit': 0.1,
            'max_pages': 10
        }
        converter = DocToSkillConverter(config, dry_run=True)

        # Should accept any URL under base_url
        self.assertTrue(converter.is_valid_url('https://docs.example.com/anything'))
        self.assertFalse(converter.is_valid_url('https://other.com/anything'))


class TestLanguageDetection(unittest.TestCase):
    """Test language detection from code blocks"""

    def setUp(self):
        """Set up test converter"""
        config = {
            'name': 'test',
            'base_url': 'https://example.com/',
            'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre'},
            'rate_limit': 0.1,
            'max_pages': 10
        }
        self.converter = DocToSkillConverter(config, dry_run=True)

    def test_detect_language_from_class(self):
        """Test language detection from CSS class"""
        html = '<code class="language-python">print("hello")</code>'
        elem = BeautifulSoup(html, 'html.parser').find('code')
        lang = self.converter.detect_language(elem, 'print("hello")')
        self.assertEqual(lang, 'python')

    def test_detect_language_from_lang_class(self):
        """Test language detection from lang- prefix"""
        html = '<code class="lang-javascript">console.log("hello")</code>'
        elem = BeautifulSoup(html, 'html.parser').find('code')
        lang = self.converter.detect_language(elem, 'console.log("hello")')
        self.assertEqual(lang, 'javascript')

    def test_detect_language_from_parent(self):
        """Test language detection from parent pre element"""
        html = '<pre class="language-cpp"><code>int main() {}</code></pre>'
        elem = BeautifulSoup(html, 'html.parser').find('code')
        lang = self.converter.detect_language(elem, 'int main() {}')
        self.assertEqual(lang, 'cpp')

    def test_detect_python_from_heuristics(self):
        """Test Python detection from code content"""
        html = '<code>import os\nfrom pathlib import Path</code>'
        elem = BeautifulSoup(html, 'html.parser').find('code')
        code = elem.get_text()
        lang = self.converter.detect_language(elem, code)
        self.assertEqual(lang, 'python')

    def test_detect_python_from_def(self):
        """Test Python detection from def keyword"""
        html = '<code>def my_function():\n    pass</code>'
        elem = BeautifulSoup(html, 'html.parser').find('code')
        code = elem.get_text()
        lang = self.converter.detect_language(elem, code)
        self.assertEqual(lang, 'python')

    def test_detect_javascript_from_const(self):
        """Test JavaScript detection from const keyword"""
        html = '<code>const myVar = 10;</code>'
        elem = BeautifulSoup(html, 'html.parser').find('code')
        code = elem.get_text()
        lang = self.converter.detect_language(elem, code)
        self.assertEqual(lang, 'javascript')

    def test_detect_javascript_from_arrow(self):
        """Test JavaScript detection from arrow function"""
        html = '<code>const add = (a, b) => a + b;</code>'
        elem = BeautifulSoup(html, 'html.parser').find('code')
        code = elem.get_text()
        lang = self.converter.detect_language(elem, code)
        self.assertEqual(lang, 'javascript')

    def test_detect_gdscript(self):
        """Test GDScript detection"""
        html = '<code>func _ready():\n    var x = 5</code>'
        elem = BeautifulSoup(html, 'html.parser').find('code')
        code = elem.get_text()
        lang = self.converter.detect_language(elem, code)
        self.assertEqual(lang, 'gdscript')

    def test_detect_cpp(self):
        """Test C++ detection"""
        html = '<code>#include <iostream>\nint main() { return 0; }</code>'
        elem = BeautifulSoup(html, 'html.parser').find('code')
        code = elem.get_text()
        lang = self.converter.detect_language(elem, code)
        self.assertEqual(lang, 'cpp')

    def test_detect_unknown(self):
        """Test unknown language detection"""
        html = '<code>some random text without clear indicators</code>'
        elem = BeautifulSoup(html, 'html.parser').find('code')
        code = elem.get_text()
        lang = self.converter.detect_language(elem, code)
        self.assertEqual(lang, 'unknown')


class TestPatternExtraction(unittest.TestCase):
    """Test pattern extraction from documentation"""

    def setUp(self):
        """Set up test converter"""
        config = {
            'name': 'test',
            'base_url': 'https://example.com/',
            'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre'},
            'rate_limit': 0.1,
            'max_pages': 10
        }
        self.converter = DocToSkillConverter(config, dry_run=True)

    def test_extract_pattern_with_example_marker(self):
        """Test pattern extraction with 'Example:' marker"""
        html = '''
        <article>
            <p>Example: Here's how to use it</p>
            <pre><code>print("hello")</code></pre>
        </article>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        main = soup.find('article')
        patterns = self.converter.extract_patterns(main, [])

        self.assertGreater(len(patterns), 0)
        self.assertIn('example', patterns[0]['description'].lower())

    def test_extract_pattern_with_usage_marker(self):
        """Test pattern extraction with 'Usage:' marker"""
        html = '''
        <article>
            <p>Usage: Call this function like so</p>
            <pre><code>my_function(arg)</code></pre>
        </article>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        main = soup.find('article')
        patterns = self.converter.extract_patterns(main, [])

        self.assertGreater(len(patterns), 0)
        self.assertIn('usage', patterns[0]['description'].lower())

    def test_extract_pattern_limit(self):
        """Test pattern extraction limits to 5 patterns"""
        html = '<article>'
        for i in range(10):
            html += f'<p>Example {i}: Test</p><pre><code>code_{i}</code></pre>'
        html += '</article>'

        soup = BeautifulSoup(html, 'html.parser')
        main = soup.find('article')
        patterns = self.converter.extract_patterns(main, [])

        self.assertLessEqual(len(patterns), 5, "Should limit to 5 patterns max")


class TestCategorization(unittest.TestCase):
    """Test smart categorization logic"""

    def setUp(self):
        """Set up test converter"""
        config = {
            'name': 'test',
            'base_url': 'https://example.com/',
            'categories': {
                'getting_started': ['intro', 'tutorial', 'getting-started'],
                'api': ['api', 'reference', 'class'],
                'guides': ['guide', 'how-to']
            },
            'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre'},
            'rate_limit': 0.1,
            'max_pages': 10
        }
        self.converter = DocToSkillConverter(config, dry_run=True)

    def test_categorize_by_url(self):
        """Test categorization based on URL"""
        pages = [{
            'url': 'https://example.com/api/reference',
            'title': 'Some Title',
            'content': 'Some content'
        }]
        categories = self.converter.smart_categorize(pages)

        # Should categorize to 'api' based on URL containing 'api'
        self.assertIn('api', categories)
        self.assertEqual(len(categories['api']), 1)

    def test_categorize_by_title(self):
        """Test categorization based on title"""
        pages = [{
            'url': 'https://example.com/docs/page',
            'title': 'API Reference Documentation',
            'content': 'Some content'
        }]
        categories = self.converter.smart_categorize(pages)

        self.assertIn('api', categories)
        self.assertEqual(len(categories['api']), 1)

    def test_categorize_by_content(self):
        """Test categorization based on content (lower priority)"""
        pages = [{
            'url': 'https://example.com/docs/page',
            'title': 'Some Page',
            'content': 'This is a tutorial for beginners. An intro to the system.'
        }]
        categories = self.converter.smart_categorize(pages)

        # Should categorize based on 'tutorial' and 'intro' in content
        self.assertIn('getting_started', categories)

    def test_categorize_to_other(self):
        """Test pages that don't match any category go to 'other'"""
        pages = [{
            'url': 'https://example.com/random/page',
            'title': 'Random Page',
            'content': 'Random content with no keywords'
        }]
        categories = self.converter.smart_categorize(pages)

        self.assertIn('other', categories)
        self.assertEqual(len(categories['other']), 1)

    def test_empty_categories_removed(self):
        """Test empty categories are removed"""
        pages = [{
            'url': 'https://example.com/api/reference',
            'title': 'API Reference',
            'content': 'API documentation'
        }]
        categories = self.converter.smart_categorize(pages)

        # Only 'api' should exist, not empty 'guides' or 'getting_started'
        # (categories with no pages are removed)
        self.assertIn('api', categories)
        self.assertNotIn('guides', categories)


class TestTextCleaning(unittest.TestCase):
    """Test text cleaning utility"""

    def setUp(self):
        """Set up test converter"""
        config = {
            'name': 'test',
            'base_url': 'https://example.com/',
            'selectors': {'main_content': 'article', 'title': 'h1', 'code_blocks': 'pre'},
            'rate_limit': 0.1,
            'max_pages': 10
        }
        self.converter = DocToSkillConverter(config, dry_run=True)

    def test_clean_multiple_spaces(self):
        """Test cleaning multiple spaces"""
        text = "Hello    world     test"
        cleaned = self.converter.clean_text(text)
        self.assertEqual(cleaned, "Hello world test")

    def test_clean_newlines(self):
        """Test cleaning newlines"""
        text = "Hello\n\nworld\ntest"
        cleaned = self.converter.clean_text(text)
        self.assertEqual(cleaned, "Hello world test")

    def test_clean_tabs(self):
        """Test cleaning tabs"""
        text = "Hello\t\tworld\ttest"
        cleaned = self.converter.clean_text(text)
        self.assertEqual(cleaned, "Hello world test")

    def test_clean_strip_whitespace(self):
        """Test stripping leading/trailing whitespace"""
        text = "   Hello world   "
        cleaned = self.converter.clean_text(text)
        self.assertEqual(cleaned, "Hello world")


if __name__ == '__main__':
    unittest.main()
