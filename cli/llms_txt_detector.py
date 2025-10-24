# ABOUTME: Detects and validates llms.txt file availability at documentation URLs
# ABOUTME: Supports llms-full.txt, llms.txt, and llms-small.txt variants

import requests
from typing import Optional, Dict

class LlmsTxtDetector:
    """Detect llms.txt files at documentation URLs"""

    VARIANTS = [
        ('llms-full.txt', 'full'),
        ('llms.txt', 'standard'),
        ('llms-small.txt', 'small')
    ]

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    def detect(self) -> Optional[Dict[str, str]]:
        """
        Detect available llms.txt variant.

        Returns:
            Dict with 'url' and 'variant' keys, or None if not found
        """
        for filename, variant in self.VARIANTS:
            # Try at base URL root
            url = f"{self.base_url.split('/docs')[0]}/{filename}"

            if self._check_url_exists(url):
                return {'url': url, 'variant': variant}

        return None

    def _check_url_exists(self, url: str) -> bool:
        """Check if URL returns 200 status"""
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            return response.status_code == 200
        except requests.RequestException:
            return False
