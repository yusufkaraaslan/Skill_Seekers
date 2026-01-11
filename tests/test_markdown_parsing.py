"""
Tests for Markdown parsing and BFS URL crawling features.

Tests the following functionality:
1. Markdown file content extraction (_extract_markdown_content)
2. HTML fallback when .md URL returns HTML (_extract_html_as_markdown)
3. URL extraction from llms.txt (extract_urls, _clean_url)
4. Empty/short content filtering in save_page
"""

import unittest
import tempfile
import os
import shutil


class TestMarkdownContentExtraction(unittest.TestCase):
    """Test Markdown file parsing in doc_scraper."""

    def setUp(self):
        """Set up test fixtures."""
        from skill_seekers.cli.doc_scraper import DocToSkillConverter

        self.config = {
            'name': 'test_md_parsing',
            'base_url': 'https://example.com',
            'selectors': {},
            'url_patterns': {'include': [], 'exclude': []},
            'categories': {}
        }
        self.converter = DocToSkillConverter(self.config)

    def tearDown(self):
        """Clean up output directory."""
        output_dir = f"output/{self.config['name']}_data"
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)

    def test_extract_title_from_h1(self):
        """Test extracting title from first h1."""
        content = "# My Documentation Title\n\nSome content here."
        result = self.converter._extract_markdown_content(content, "https://example.com/test.md")
        self.assertEqual(result['title'], "My Documentation Title")

    def test_extract_headings_h2_to_h6(self):
        """Test extracting h2-h6 headings (not h1)."""
        content = """# Title

## Section One
### Subsection A
#### Deep Section
##### Deeper
###### Deepest

Content here.
"""
        result = self.converter._extract_markdown_content(content, "https://example.com/test.md")
        # Should have 5 headings (h2-h6), not h1
        self.assertEqual(len(result['headings']), 5)
        self.assertEqual(result['headings'][0]['level'], 'h2')
        self.assertEqual(result['headings'][0]['text'], 'Section One')

    def test_extract_code_blocks_with_language(self):
        """Test extracting code blocks with language tags."""
        content = """# API Guide

```python
def hello():
    return "Hello, World!"
```

Some explanation.

```javascript
const greet = () => console.log("Hi");
```

```
plain code without language
```
"""
        result = self.converter._extract_markdown_content(content, "https://example.com/test.md")
        self.assertEqual(len(result['code_samples']), 3)
        self.assertEqual(result['code_samples'][0]['language'], 'python')
        self.assertEqual(result['code_samples'][1]['language'], 'javascript')
        self.assertEqual(result['code_samples'][2]['language'], 'unknown')

    def test_extract_markdown_links_only_md_files(self):
        """Test that only .md links are extracted."""
        content = """# Links

- [Markdown Doc](./guide.md)
- [Another MD](https://example.com/api.md)
- [HTML Page](./page.html)
- [External](https://google.com)
"""
        result = self.converter._extract_markdown_content(content, "https://example.com/docs/test.md")
        # Should only include .md links
        md_links = [l for l in result['links'] if '.md' in l]
        self.assertEqual(len(md_links), len(result['links']))

    def test_extract_content_paragraphs(self):
        """Test extracting paragraph content."""
        content = """# Title

This is a paragraph with enough content to pass the minimum length filter.

Short.

Another paragraph that should be included in the final content output.
"""
        result = self.converter._extract_markdown_content(content, "https://example.com/test.md")
        self.assertIn("paragraph with enough content", result['content'])
        self.assertNotIn("Short.", result['content'])

    def test_detect_html_in_md_url(self):
        """Test that HTML content is detected when .md URL returns HTML."""
        html_content = "<!DOCTYPE html><html><head><title>Page</title></head><body><h1>Hello</h1></body></html>"
        result = self.converter._extract_markdown_content(html_content, "https://example.com/test.md")
        self.assertEqual(result['title'], "Page")


class TestHtmlAsMarkdownExtraction(unittest.TestCase):
    """Test HTML to markdown-like extraction."""

    def setUp(self):
        """Set up test fixtures."""
        from skill_seekers.cli.doc_scraper import DocToSkillConverter

        self.config = {
            'name': 'test_html_fallback',
            'base_url': 'https://example.com',
            'selectors': {},
            'url_patterns': {'include': [], 'exclude': []},
            'categories': {}
        }
        self.converter = DocToSkillConverter(self.config)

    def tearDown(self):
        """Clean up output directory."""
        output_dir = f"output/{self.config['name']}_data"
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)

    def test_extract_title_from_html(self):
        """Test extracting title from HTML title tag."""
        html = "<html><head><title>My Page Title</title></head><body></body></html>"
        result = self.converter._extract_html_as_markdown(html, "https://example.com/test.md")
        self.assertEqual(result['title'], "My Page Title")

    def test_find_main_content_area(self):
        """Test finding main content from various selectors."""
        html = """
        <html><body>
            <nav>Navigation</nav>
            <main>
                <h1>Main Content</h1>
                <p>This is the main content area with enough text to pass filters.</p>
            </main>
            <footer>Footer</footer>
        </body></html>
        """
        result = self.converter._extract_html_as_markdown(html, "https://example.com/test.md")
        self.assertIn("main content area", result['content'].lower())

    def test_extract_code_blocks_from_html(self):
        """Test extracting code blocks from HTML pre/code tags."""
        html = """
        <html><body>
            <main>
                <pre><code class="language-python">print("hello")</code></pre>
            </main>
        </body></html>
        """
        result = self.converter._extract_html_as_markdown(html, "https://example.com/test.md")
        self.assertTrue(len(result['code_samples']) > 0)

    def test_fallback_to_body_when_no_main(self):
        """Test fallback to body when no main/article element."""
        html = """
        <html><body>
            <div>
                <h2>Section</h2>
                <p>Content in body without main element, long enough to pass filter.</p>
            </div>
        </body></html>
        """
        result = self.converter._extract_html_as_markdown(html, "https://example.com/test.md")
        self.assertTrue(len(result['headings']) > 0 or len(result['content']) > 0)


class TestLlmsTxtUrlExtraction(unittest.TestCase):
    """Test URL extraction from llms.txt content."""

    def test_extract_markdown_style_links(self):
        """Test extracting [text](url) style links."""
        from skill_seekers.cli.llms_txt_parser import LlmsTxtParser

        content = """
# Documentation Index

- [Getting Started](https://docs.example.com/start.md)
- [API Reference](https://docs.example.com/api/index.md)
- [Advanced Guide](https://docs.example.com/advanced.md)
"""
        parser = LlmsTxtParser(content, base_url="https://docs.example.com")
        urls = parser.extract_urls()

        self.assertIn("https://docs.example.com/start.md", urls)
        self.assertIn("https://docs.example.com/api/index.md", urls)
        self.assertIn("https://docs.example.com/advanced.md", urls)

    def test_extract_bare_urls(self):
        """Test extracting bare URLs without markdown syntax."""
        from skill_seekers.cli.llms_txt_parser import LlmsTxtParser

        content = """
Documentation: https://example.com/docs/guide.md
API: https://example.com/api/reference.md
"""
        parser = LlmsTxtParser(content)
        urls = parser.extract_urls()

        self.assertIn("https://example.com/docs/guide.md", urls)
        self.assertIn("https://example.com/api/reference.md", urls)

    def test_resolve_relative_urls(self):
        """Test resolving relative URLs with base_url."""
        from skill_seekers.cli.llms_txt_parser import LlmsTxtParser

        content = """
- [Local Doc](./docs/guide.md)
- [Parent](../api/ref.md)
"""
        parser = LlmsTxtParser(content, base_url="https://example.com/learn/")
        urls = parser.extract_urls()

        # Should resolve relative paths
        self.assertTrue(any("docs/guide.md" in url for url in urls))

    def test_clean_url_invalid_anchor_pattern(self):
        """Test cleaning URLs with invalid anchor patterns."""
        from skill_seekers.cli.llms_txt_parser import LlmsTxtParser

        parser = LlmsTxtParser("", base_url="https://example.com")

        # Invalid: path after anchor
        result = parser._clean_url("https://example.com/page#section/index.html.md")
        self.assertEqual(result, "https://example.com/page")

    def test_clean_url_valid_anchor(self):
        """Test that valid anchors are preserved."""
        from skill_seekers.cli.llms_txt_parser import LlmsTxtParser

        parser = LlmsTxtParser("", base_url="https://example.com")

        # Valid anchor should be unchanged
        result = parser._clean_url("https://example.com/page.md#section")
        self.assertEqual(result, "https://example.com/page.md#section")

    def test_clean_url_no_anchor(self):
        """Test that URLs without anchors are unchanged."""
        from skill_seekers.cli.llms_txt_parser import LlmsTxtParser

        parser = LlmsTxtParser("", base_url="https://example.com")

        result = parser._clean_url("https://example.com/docs/guide.md")
        self.assertEqual(result, "https://example.com/docs/guide.md")

    def test_deduplicate_urls(self):
        """Test that duplicate URLs are removed."""
        from skill_seekers.cli.llms_txt_parser import LlmsTxtParser

        content = """
- [Doc 1](https://example.com/doc.md)
- [Doc 2](https://example.com/doc.md)
https://example.com/doc.md
"""
        parser = LlmsTxtParser(content)
        urls = parser.extract_urls()

        # Should only have one instance
        count = sum(1 for u in urls if u == "https://example.com/doc.md")
        self.assertEqual(count, 1)


class TestSavePageContentFiltering(unittest.TestCase):
    """Test content filtering in save_page."""

    def setUp(self):
        """Set up test fixtures."""
        from skill_seekers.cli.doc_scraper import DocToSkillConverter

        self.config = {
            'name': 'test_save_filter',
            'base_url': 'https://example.com',
            'selectors': {},
            'url_patterns': {'include': [], 'exclude': []},
            'categories': {}
        }
        self.converter = DocToSkillConverter(self.config)

    def tearDown(self):
        """Clean up output directory."""
        output_dir = f"output/{self.config['name']}_data"
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)

    def test_skip_empty_content(self):
        """Test that pages with empty content are skipped."""
        page = {
            'url': 'https://example.com/empty',
            'title': 'Empty Page',
            'content': '',
            'headings': [],
            'code_samples': []
        }

        self.converter.save_page(page)

        pages_dir = os.path.join(self.converter.data_dir, 'pages')
        if os.path.exists(pages_dir):
            self.assertEqual(len(os.listdir(pages_dir)), 0)

    def test_skip_short_content_under_50_chars(self):
        """Test that pages with content < 50 chars are skipped."""
        page = {
            'url': 'https://example.com/short',
            'title': 'Short',
            'content': 'This is too short.',  # 18 chars
            'headings': [],
            'code_samples': []
        }

        self.converter.save_page(page)

        pages_dir = os.path.join(self.converter.data_dir, 'pages')
        if os.path.exists(pages_dir):
            self.assertEqual(len(os.listdir(pages_dir)), 0)

    def test_save_content_over_50_chars(self):
        """Test that pages with content >= 50 chars are saved."""
        page = {
            'url': 'https://example.com/valid',
            'title': 'Valid Page',
            'content': 'A' * 60,  # 60 chars, should pass
            'headings': [],
            'code_samples': []
        }

        self.converter.save_page(page)

        pages_dir = os.path.join(self.converter.data_dir, 'pages')
        self.assertTrue(os.path.exists(pages_dir))
        self.assertEqual(len(os.listdir(pages_dir)), 1)


if __name__ == '__main__':
    unittest.main()
