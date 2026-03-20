"""
E2E test for Issue #277 - Discord docs case reported by @skeith.

This test hits the REAL Discord docs llms.txt and verifies that
no /index.html.md URLs are generated. No mocks.

Requires network access. Marked as integration test.
"""

import os
import shutil
import unittest

import pytest

from skill_seekers.cli.doc_scraper import DocToSkillConverter
from skill_seekers.cli.llms_txt_detector import LlmsTxtDetector
from skill_seekers.cli.llms_txt_downloader import LlmsTxtDownloader
from skill_seekers.cli.llms_txt_parser import LlmsTxtParser


@pytest.mark.integration
class TestIssue277DiscordDocsE2E(unittest.TestCase):
    """E2E: Reproduce @skeith's report with real Discord docs."""

    def setUp(self):
        self.base_url = "https://docs.discord.com/"
        self.config = {
            "name": "DiscordDocsE2E",
            "description": "Discord API Documentation",
            "base_url": self.base_url,
            "selectors": {"main_content": "article"},
            "url_patterns": {"include": ["/developers"], "exclude": []},
        }
        self.output_dir = f"output/{self.config['name']}_data"

    def tearDown(self):
        # Clean up any output created
        for path in [self.output_dir, f"output/{self.config['name']}"]:
            if os.path.exists(path):
                shutil.rmtree(path)

    def test_discord_llms_txt_exists(self):
        """Verify Discord docs has llms.txt (precondition for the bug)."""
        detector = LlmsTxtDetector(self.base_url)
        variants = detector.detect_all()
        self.assertTrue(
            len(variants) > 0,
            "Discord docs should have at least one llms.txt variant",
        )

    def test_discord_llms_txt_urls_no_index_html_md(self):
        """Core test: URLs extracted from Discord llms.txt must NOT get /index.html.md appended."""
        # Step 1: Detect llms.txt
        detector = LlmsTxtDetector(self.base_url)
        variants = detector.detect_all()
        self.assertTrue(len(variants) > 0, "No llms.txt found at docs.discord.com")

        # Step 2: Download the largest variant (same logic as doc_scraper)
        downloaded = {}
        for variant_info in variants:
            downloader = LlmsTxtDownloader(variant_info["url"])
            content = downloader.download()
            if content:
                downloaded[variant_info["variant"]] = content

        self.assertTrue(len(downloaded) > 0, "Failed to download any llms.txt variant")

        largest_content = max(downloaded.values(), key=len)

        # Step 3: Parse URLs from llms.txt
        parser = LlmsTxtParser(largest_content, self.base_url)
        extracted_urls = parser.extract_urls()
        self.assertTrue(
            len(extracted_urls) > 0,
            "No URLs extracted from Discord llms.txt",
        )

        # Step 4: Run _convert_to_md_urls (the function that was causing 404s)
        converter = DocToSkillConverter(self.config, dry_run=True)
        converted_urls = converter._convert_to_md_urls(extracted_urls)

        # Step 5: Verify NO /index.html.md was blindly appended
        bad_urls = [u for u in converted_urls if "/index.html.md" in u]
        self.assertEqual(
            len(bad_urls),
            0,
            f"Found {len(bad_urls)} URLs with /index.html.md appended "
            f"(would cause 404s):\n"
            + "\n".join(bad_urls[:10]),
        )

        # Step 6: Verify no anchor fragments leaked through
        anchor_urls = [u for u in converted_urls if "#" in u]
        self.assertEqual(
            len(anchor_urls),
            0,
            f"Found {len(anchor_urls)} URLs with anchor fragments:\n"
            + "\n".join(anchor_urls[:10]),
        )

        # Step 7: Verify we got a reasonable number of URLs
        self.assertGreater(
            len(converted_urls),
            10,
            "Expected at least 10 unique URLs from Discord docs",
        )

    def test_discord_full_pipeline_no_404_urls(self):
        """Full pipeline: detector -> downloader -> parser -> converter -> queue.

        Simulates what `skill-seekers create https://docs.discord.com` does,
        without actually scraping pages.
        """
        converter = DocToSkillConverter(self.config, dry_run=True)

        # Run _try_llms_txt which calls _convert_to_md_urls internally
        os.makedirs(os.path.join(converter.skill_dir, "references"), exist_ok=True)
        os.makedirs(os.path.join(converter.data_dir, "pages"), exist_ok=True)
        result = converter._try_llms_txt()

        # _try_llms_txt returns False when it populates pending_urls for BFS
        # (True means it parsed content directly, no BFS needed)
        if not result:
            # Check every URL in the queue
            for url in converter.pending_urls:
                self.assertNotIn(
                    "/index.html.md",
                    url,
                    f"Queue contains 404-causing URL: {url}",
                )
                self.assertNotIn(
                    "#",
                    url,
                    f"Queue contains URL with anchor fragment: {url}",
                )

            self.assertGreater(
                len(converter.pending_urls),
                0,
                "Pipeline should have queued URLs for crawling",
            )


if __name__ == "__main__":
    unittest.main()
