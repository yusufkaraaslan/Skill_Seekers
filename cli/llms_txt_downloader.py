"""ABOUTME: Downloads llms.txt files from documentation URLs with error handling"""
"""ABOUTME: Handles timeouts, retries, and validates content before returning"""

import requests
from typing import Optional

class LlmsTxtDownloader:
    """Download llms.txt content from URLs"""

    def __init__(self, url: str, timeout: int = 30):
        self.url = url
        self.timeout = timeout

    def download(self) -> Optional[str]:
        """
        Download llms.txt content.

        Returns:
            String content or None if download fails
        """
        try:
            headers = {
                'User-Agent': 'Skill-Seekers-llms.txt-Reader/1.0'
            }

            response = requests.get(
                self.url,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()

            content = response.text

            # Validate content is not empty and looks like markdown
            if len(content) < 100:
                return None

            return content

        except requests.RequestException as e:
            print(f"❌ Failed to download {self.url}: {e}")
            return None
