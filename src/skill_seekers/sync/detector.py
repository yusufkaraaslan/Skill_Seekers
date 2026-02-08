"""
Change detection for documentation pages.
"""

import hashlib
import difflib
from datetime import datetime
import requests

from .models import PageChange, ChangeType, ChangeReport


class ChangeDetector:
    """
    Detects changes in documentation pages.

    Uses multiple strategies:
    1. Content hashing (SHA-256)
    2. Last-Modified headers
    3. ETag headers
    4. Content diffing

    Examples:
        detector = ChangeDetector()

        # Check single page
        change = detector.check_page(
            url="https://react.dev/learn",
            old_hash="abc123"
        )

        # Generate diff
        diff = detector.generate_diff(old_content, new_content)

        # Check multiple pages
        changes = detector.check_pages(urls, previous_state)
    """

    def __init__(self, timeout: int = 30):
        """
        Initialize change detector.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout

    def compute_hash(self, content: str) -> str:
        """
        Compute SHA-256 hash of content.

        Args:
            content: Page content

        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def fetch_page(self, url: str) -> tuple[str, dict[str, str]]:
        """
        Fetch page content and metadata.

        Args:
            url: Page URL

        Returns:
            Tuple of (content, metadata)
            metadata includes: last-modified, etag, content-type

        Raises:
            requests.RequestException: If fetch fails
        """
        response = requests.get(
            url, timeout=self.timeout, headers={"User-Agent": "SkillSeekers-Sync/1.0"}
        )
        response.raise_for_status()

        metadata = {
            "last-modified": response.headers.get("Last-Modified"),
            "etag": response.headers.get("ETag"),
            "content-type": response.headers.get("Content-Type"),
            "content-length": response.headers.get("Content-Length"),
        }

        return response.text, metadata

    def check_page(
        self,
        url: str,
        old_hash: str | None = None,
        generate_diff: bool = False,
        old_content: str | None = None,
    ) -> PageChange:
        """
        Check if page has changed.

        Args:
            url: Page URL
            old_hash: Previous content hash
            generate_diff: Whether to generate diff
            old_content: Previous content (for diff generation)

        Returns:
            PageChange object

        Raises:
            requests.RequestException: If fetch fails
        """
        try:
            content, metadata = self.fetch_page(url)
            new_hash = self.compute_hash(content)

            # Determine change type
            if old_hash is None:
                change_type = ChangeType.ADDED
            elif old_hash == new_hash:
                change_type = ChangeType.UNCHANGED
            else:
                change_type = ChangeType.MODIFIED

            # Generate diff if requested
            diff = None
            if generate_diff and old_content and change_type == ChangeType.MODIFIED:
                diff = self.generate_diff(old_content, content)

            return PageChange(
                url=url,
                change_type=change_type,
                old_hash=old_hash,
                new_hash=new_hash,
                diff=diff,
                detected_at=datetime.utcnow(),
            )

        except requests.RequestException:
            # Page might be deleted or temporarily unavailable
            return PageChange(
                url=url,
                change_type=ChangeType.DELETED,
                old_hash=old_hash,
                new_hash=None,
                detected_at=datetime.utcnow(),
            )

    def check_pages(
        self, urls: list[str], previous_hashes: dict[str, str], generate_diffs: bool = False
    ) -> ChangeReport:
        """
        Check multiple pages for changes.

        Args:
            urls: List of URLs to check
            previous_hashes: URL -> hash mapping from previous state
            generate_diffs: Whether to generate diffs

        Returns:
            ChangeReport with all detected changes
        """
        added = []
        modified = []
        deleted = []
        unchanged_count = 0

        # Check each URL
        checked_urls = set()
        for url in urls:
            checked_urls.add(url)
            old_hash = previous_hashes.get(url)

            change = self.check_page(url, old_hash, generate_diff=generate_diffs)

            if change.change_type == ChangeType.ADDED:
                added.append(change)
            elif change.change_type == ChangeType.MODIFIED:
                modified.append(change)
            elif change.change_type == ChangeType.UNCHANGED:
                unchanged_count += 1

        # Check for deleted pages (in previous state but not in current)
        for url, old_hash in previous_hashes.items():
            if url not in checked_urls:
                deleted.append(
                    PageChange(
                        url=url,
                        change_type=ChangeType.DELETED,
                        old_hash=old_hash,
                        new_hash=None,
                        detected_at=datetime.utcnow(),
                    )
                )

        return ChangeReport(
            skill_name="unknown",  # To be set by caller
            total_pages=len(urls),
            added=added,
            modified=modified,
            deleted=deleted,
            unchanged=unchanged_count,
            checked_at=datetime.utcnow(),
        )

    def generate_diff(self, old_content: str, new_content: str) -> str:
        """
        Generate unified diff between old and new content.

        Args:
            old_content: Original content
            new_content: New content

        Returns:
            Unified diff string
        """
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        diff = difflib.unified_diff(old_lines, new_lines, fromfile="old", tofile="new", lineterm="")

        return "".join(diff)

    def generate_summary_diff(self, old_content: str, new_content: str) -> str:
        """
        Generate human-readable diff summary.

        Args:
            old_content: Original content
            new_content: New content

        Returns:
            Summary string with added/removed line counts
        """
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()

        diff = difflib.unified_diff(old_lines, new_lines)
        diff_lines = list(diff)

        added = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
        removed = sum(
            1 for line in diff_lines if line.startswith("-") and not line.startswith("---")
        )

        return f"+{added} -{removed} lines"

    def check_header_changes(
        self, url: str, old_modified: str | None = None, old_etag: str | None = None
    ) -> bool:
        """
        Quick check using HTTP headers (no content download).

        Args:
            url: Page URL
            old_modified: Previous Last-Modified header
            old_etag: Previous ETag header

        Returns:
            True if headers indicate change, False otherwise
        """
        try:
            # Use HEAD request for efficiency
            response = requests.head(
                url, timeout=self.timeout, headers={"User-Agent": "SkillSeekers-Sync/1.0"}
            )
            response.raise_for_status()

            new_modified = response.headers.get("Last-Modified")
            new_etag = response.headers.get("ETag")

            # Check if headers indicate change
            if old_modified and new_modified and old_modified != new_modified:
                return True

            return bool(old_etag and new_etag and old_etag != new_etag)

        except requests.RequestException:
            # If HEAD request fails, assume change (will be verified with GET)
            return True

    def batch_check_headers(
        self, urls: list[str], previous_metadata: dict[str, dict[str, str]]
    ) -> list[str]:
        """
        Batch check URLs using headers only.

        Args:
            urls: URLs to check
            previous_metadata: URL -> metadata mapping

        Returns:
            List of URLs that likely changed
        """
        changed_urls = []

        for url in urls:
            old_meta = previous_metadata.get(url, {})
            old_modified = old_meta.get("last-modified")
            old_etag = old_meta.get("etag")

            if self.check_header_changes(url, old_modified, old_etag):
                changed_urls.append(url)

        return changed_urls
