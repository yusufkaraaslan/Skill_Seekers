"""ABOUTME: Parses llms.txt markdown content into structured page data"""
"""ABOUTME: Extracts titles, content, code samples, and headings from markdown"""

import re
from typing import List, Dict
from urllib.parse import urljoin

class LlmsTxtParser:
    """Parse llms.txt markdown content into page structures"""

    def __init__(self, content: str, base_url: str = None):
        self.content = content
        self.base_url = base_url

    def extract_urls(self) -> List[str]:
        """
        Extract all URLs from the llms.txt content.

        Supports both markdown-style links [text](url) and bare URLs.
        Resolves relative URLs using base_url if provided.
        Filters out malformed URLs with invalid anchor patterns.

        Returns:
            List of unique, cleaned URLs found in the content.
            Returns empty list if no valid URLs found.

        Note:
            - Markdown links: [Getting Started](./docs/guide.md)
            - Bare URLs: https://example.com/api.md
            - Relative paths resolved with base_url
            - Invalid anchors (#section/path.md) are stripped
        """
        urls = set()

        # Match markdown links: [text](url)
        md_links = re.findall(r'\[([^\]]*)\]\(([^)]+)\)', self.content)
        for _, url in md_links:
            if url.startswith('http'):
                clean_url = self._clean_url(url)
                if clean_url:
                    urls.add(clean_url)
            elif self.base_url and not url.startswith('#'):
                clean_url = self._clean_url(urljoin(self.base_url, url))
                if clean_url:
                    urls.add(clean_url)

        # Match bare URLs
        bare_urls = re.findall(r'https?://[^\s\)\]<>"\']+', self.content)
        for url in bare_urls:
            # Clean trailing punctuation
            url = url.rstrip('.,;:')
            clean_url = self._clean_url(url)
            if clean_url:
                urls.add(clean_url)

        return list(urls)

    def _clean_url(self, url: str) -> str:
        """
        Clean and validate URL, removing invalid anchor patterns.

        Detects and strips malformed anchors that contain path separators.
        Valid: https://example.com/page.md#section
        Invalid: https://example.com/page#section/index.html.md

        Args:
            url: URL to clean (absolute or relative)

        Returns:
            Cleaned URL with malformed anchors stripped.
            Returns base URL if anchor contains '/' (malformed).
            Returns original URL if anchor is valid or no anchor present.

        Example:
            >>> parser._clean_url("https://ex.com/page#sec/path.md")
            "https://ex.com/page"
            >>> parser._clean_url("https://ex.com/page.md#section")
            "https://ex.com/page.md#section"
        """
        # Skip URLs with path after anchor (e.g., #section/index.html.md)
        # These are malformed and return duplicate HTML content
        if '#' in url:
            anchor_pos = url.index('#')
            after_anchor = url[anchor_pos + 1:]
            # If there's a path separator after anchor, it's invalid
            if '/' in after_anchor:
                # Extract the base URL without the malformed anchor
                return url[:anchor_pos]
        return url

    def parse(self) -> List[Dict]:
        """
        Parse markdown content into page structures.

        Returns:
            List of page dicts with title, content, code_samples, headings
        """
        pages = []

        # Split by h1 headers (# Title)
        sections = re.split(r'\n# ', self.content)

        for section in sections:
            if not section.strip():
                continue

            # First line is title
            lines = section.split('\n')
            title = lines[0].strip('#').strip()

            # Parse content
            page = self._parse_section('\n'.join(lines[1:]), title)
            pages.append(page)

        return pages

    def _parse_section(self, content: str, title: str) -> Dict:
        """Parse a single section into page structure"""
        page = {
            'title': title,
            'content': '',
            'code_samples': [],
            'headings': [],
            'url': f'llms-txt#{title.lower().replace(" ", "-")}',
            'links': []
        }

        # Extract code blocks
        code_blocks = re.findall(r'```(\w+)?\n(.*?)```', content, re.DOTALL)
        for lang, code in code_blocks:
            page['code_samples'].append({
                'code': code.strip(),
                'language': lang or 'unknown'
            })

        # Extract h2/h3 headings
        headings = re.findall(r'^(#{2,3})\s+(.+)$', content, re.MULTILINE)
        for level_markers, text in headings:
            page['headings'].append({
                'level': f'h{len(level_markers)}',
                'text': text.strip(),
                'id': text.lower().replace(' ', '-')
            })

        # Remove code blocks from content for plain text
        content_no_code = re.sub(r'```.*?```', '', content, flags=re.DOTALL)

        # Extract paragraphs
        paragraphs = [p.strip() for p in content_no_code.split('\n\n') if len(p.strip()) > 20]
        page['content'] = '\n\n'.join(paragraphs)

        return page
