"""ABOUTME: Downloads llms.txt files from documentation URLs with retry logic"""
"""ABOUTME: Validates markdown content and handles timeouts with exponential backoff"""

import requests
import time
from typing import Optional

class LlmsTxtDownloader:
    """Download llms.txt content from URLs with retry logic"""

    def __init__(self, url: str, timeout: int = 30, max_retries: int = 3):
        self.url = url
        self.timeout = timeout
        self.max_retries = max_retries

    def _is_markdown(self, content: str) -> bool:
        """
        Check if content looks like markdown.

        Returns:
            True if content contains markdown patterns
        """
        markdown_patterns = ['# ', '## ', '```', '- ', '* ', '`']
        return any(pattern in content for pattern in markdown_patterns)

    def download(self) -> Optional[str]:
        """
        Download llms.txt content with retry logic.

        Returns:
            String content or None if download fails
        """
        headers = {
            'User-Agent': 'Skill-Seekers-llms.txt-Reader/1.0'
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    self.url,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()

                content = response.text

                # Validate content is not empty
                if len(content) < 100:
                    print(f"⚠️  Content too short ({len(content)} chars), rejecting")
                    return None

                # Validate content looks like markdown
                if not self._is_markdown(content):
                    print(f"⚠️  Content doesn't look like markdown")
                    return None

                return content

            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    # Calculate exponential backoff delay: 1s, 2s, 4s, etc.
                    delay = 2 ** attempt
                    print(f"⚠️  Attempt {attempt + 1}/{self.max_retries} failed: {e}")
                    print(f"   Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    print(f"❌ Failed to download {self.url} after {self.max_retries} attempts: {e}")
                    return None

        return None
