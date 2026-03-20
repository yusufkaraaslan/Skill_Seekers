"""
Real-world integration test for Issue #277: URL conversion bug with anchor fragments
and blind /index.html.md appending.

Tests the exact MikroORM and Discord cases reported in the issue.
Updated: _convert_to_md_urls no longer appends /index.html.md to non-.md URLs.
"""

import unittest
from unittest.mock import MagicMock, patch

from skill_seekers.cli.doc_scraper import DocToSkillConverter


class TestIssue277RealWorld(unittest.TestCase):
    """Integration test for Issue #277 using real MikroORM URLs"""

    def setUp(self):
        """Set up test converter with MikroORM-like configuration"""
        self.config = {
            "name": "MikroORM",
            "description": "ORM",
            "base_url": "https://mikro-orm.io/docs/",
            "selectors": {"main_content": "article"},
            "url_patterns": {
                "include": ["/docs"],
                "exclude": [],
            },
        }
        self.converter = DocToSkillConverter(self.config, dry_run=True)

    def test_mikro_orm_urls_from_issue_277(self):
        """Test the exact URLs that caused 404 errors in issue #277"""
        urls_from_llms_txt = [
            "https://mikro-orm.io/docs/",
            "https://mikro-orm.io/docs/reference.md",
            "https://mikro-orm.io/docs/quick-start#synchronous-initialization",
            "https://mikro-orm.io/docs/repositories.md#custom-repository",
            "https://mikro-orm.io/docs/propagation",
            "https://mikro-orm.io/docs/defining-entities.md#check-constraints",
            "https://mikro-orm.io/docs/defining-entities#formulas",
            "https://mikro-orm.io/docs/defining-entities#postgresql-native-enums",
        ]

        result = self.converter._convert_to_md_urls(urls_from_llms_txt)

        # Verify no malformed URLs with anchor fragments
        for url in result:
            self.assertNotIn("#", url, f"URL should not contain anchor: {url}")
            # No /index.html.md should be appended to non-.md URLs
            if not url.endswith(".md"):
                self.assertNotIn(
                    "index.html.md", url, f"Should not append /index.html.md: {url}"
                )

        # .md URLs preserved, non-.md URLs preserved as-is, anchors deduplicated
        self.assertIn("https://mikro-orm.io/docs/reference.md", result)
        self.assertIn("https://mikro-orm.io/docs/repositories.md", result)
        self.assertIn("https://mikro-orm.io/docs/defining-entities.md", result)
        self.assertIn("https://mikro-orm.io/docs/quick-start", result)
        self.assertIn("https://mikro-orm.io/docs/propagation", result)

    def test_no_404_causing_urls_generated(self):
        """Verify that no URLs matching the 404 error pattern are generated"""
        problematic_patterns = [
            "#synchronous-initialization/index.html.md",
            "#formulas/index.html.md",
            "#postgresql-native-enums/index.html.md",
            "#custom-repository/index.html.md",
            "#check-constraints/index.html.md",
        ]

        urls = [
            "https://mikro-orm.io/docs/quick-start#synchronous-initialization",
            "https://mikro-orm.io/docs/defining-entities#formulas",
            "https://mikro-orm.io/docs/defining-entities#postgresql-native-enums",
            "https://mikro-orm.io/docs/repositories.md#custom-repository",
            "https://mikro-orm.io/docs/defining-entities.md#check-constraints",
        ]

        result = self.converter._convert_to_md_urls(urls)

        # Verify NONE of the problematic patterns exist
        for url in result:
            for pattern in problematic_patterns:
                self.assertNotIn(
                    pattern,
                    url,
                    f"URL '{url}' contains problematic pattern '{pattern}' that causes 404",
                )

    def test_no_blind_index_html_md_appending(self):
        """Verify non-.md URLs don't get /index.html.md appended (core fix)"""
        urls = [
            "https://mikro-orm.io/docs/quick-start",
            "https://mikro-orm.io/docs/propagation",
            "https://mikro-orm.io/docs/filters",
        ]

        result = self.converter._convert_to_md_urls(urls)

        self.assertEqual(len(result), 3)
        for url in result:
            self.assertNotIn(
                "/index.html.md",
                url,
                f"Should not blindly append /index.html.md: {url}",
            )

        self.assertEqual(result[0], "https://mikro-orm.io/docs/quick-start")
        self.assertEqual(result[1], "https://mikro-orm.io/docs/propagation")
        self.assertEqual(result[2], "https://mikro-orm.io/docs/filters")

    def test_deduplication_prevents_multiple_requests(self):
        """Verify that multiple anchors on same page don't create duplicate requests"""
        urls_with_multiple_anchors = [
            "https://mikro-orm.io/docs/defining-entities#formulas",
            "https://mikro-orm.io/docs/defining-entities#postgresql-native-enums",
            "https://mikro-orm.io/docs/defining-entities#indexes",
            "https://mikro-orm.io/docs/defining-entities#check-constraints",
        ]

        result = self.converter._convert_to_md_urls(urls_with_multiple_anchors)

        # Should deduplicate to single URL
        self.assertEqual(
            len(result),
            1,
            "Multiple anchors on same page should deduplicate to single request",
        )
        self.assertEqual(result[0], "https://mikro-orm.io/docs/defining-entities")

    def test_md_files_with_anchors_preserved(self):
        """Test that .md files with anchors are handled correctly"""
        urls = [
            "https://mikro-orm.io/docs/repositories.md#custom-repository",
            "https://mikro-orm.io/docs/defining-entities.md#check-constraints",
            "https://mikro-orm.io/docs/inheritance-mapping.md#single-table-inheritance",
        ]

        result = self.converter._convert_to_md_urls(urls)

        # Should preserve .md extension, strip anchors, deduplicate
        self.assertEqual(len(result), 3)
        self.assertIn("https://mikro-orm.io/docs/repositories.md", result)
        self.assertIn("https://mikro-orm.io/docs/defining-entities.md", result)
        self.assertIn("https://mikro-orm.io/docs/inheritance-mapping.md", result)

        # Verify no anchors in results
        for url in result:
            self.assertNotIn("#", url, "Result should not contain anchor fragments")

    @patch("skill_seekers.cli.doc_scraper.requests.get")
    def test_real_scraping_scenario_no_404s(self, mock_get):
        """
        Integration test: Simulate real scraping scenario with llms.txt URLs.
        Verify that the converted URLs would not cause 404 errors.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
# MikroORM Documentation
https://mikro-orm.io/docs/quick-start
https://mikro-orm.io/docs/quick-start#synchronous-initialization
https://mikro-orm.io/docs/propagation
https://mikro-orm.io/docs/defining-entities#formulas
"""
        mock_get.return_value = mock_response

        urls_from_llms = [
            "https://mikro-orm.io/docs/quick-start",
            "https://mikro-orm.io/docs/quick-start#synchronous-initialization",
            "https://mikro-orm.io/docs/propagation",
            "https://mikro-orm.io/docs/defining-entities#formulas",
        ]

        converted_urls = self.converter._convert_to_md_urls(urls_from_llms)

        self.assertTrue(len(converted_urls) > 0)

        for url in converted_urls:
            # Should not contain # anywhere
            self.assertRegex(
                url,
                r"^https://[^#]+$",
                f"URL should not contain anchor fragments: {url}",
            )
            # Should NOT have /index.html.md appended
            if not url.endswith(".md"):
                self.assertNotIn(
                    "index.html.md",
                    url,
                    f"Should not append /index.html.md: {url}",
                )

    def test_issue_277_error_message_urls(self):
        """
        Test the exact URLs that appeared in error messages from the issue report.
        These were the actual 404-causing URLs that need to be fixed.
        """
        error_urls_with_anchors = [
            "https://mikro-orm.io/docs/quick-start#synchronous-initialization/index.html.md",
            "https://mikro-orm.io/docs/defining-entities#formulas/index.html.md",
            "https://mikro-orm.io/docs/defining-entities#postgresql-native-enums/index.html.md",
        ]

        input_urls = [
            "https://mikro-orm.io/docs/quick-start#synchronous-initialization",
            "https://mikro-orm.io/docs/propagation",
            "https://mikro-orm.io/docs/defining-entities#formulas",
            "https://mikro-orm.io/docs/defining-entities#postgresql-native-enums",
        ]

        result = self.converter._convert_to_md_urls(input_urls)

        # Verify NONE of the malformed error URLs are generated
        for error_url in error_urls_with_anchors:
            self.assertNotIn(
                error_url,
                result,
                f"Should not generate the 404-causing URL: {error_url}",
            )

        # Verify correct URLs are generated
        self.assertIn("https://mikro-orm.io/docs/quick-start", result)
        self.assertIn("https://mikro-orm.io/docs/propagation", result)
        self.assertIn("https://mikro-orm.io/docs/defining-entities", result)


class TestIssue277DiscordDocs(unittest.TestCase):
    """Test for Discord docs case reported by @skeith"""

    def setUp(self):
        self.config = {
            "name": "DiscordDocs",
            "description": "Discord API Documentation",
            "base_url": "https://docs.discord.com/",
            "selectors": {"main_content": "article"},
        }
        self.converter = DocToSkillConverter(self.config, dry_run=True)

    def test_discord_docs_no_index_html_md(self):
        """Discord docs don't serve .md files - no /index.html.md should be appended"""
        urls = [
            "https://docs.discord.com/developers/activities/building-an-activity",
            "https://docs.discord.com/developers/activities/design-patterns",
            "https://docs.discord.com/developers/components/overview",
            "https://docs.discord.com/developers/bots/getting-started",
        ]

        result = self.converter._convert_to_md_urls(urls)

        self.assertEqual(len(result), 4)
        for url in result:
            self.assertNotIn(
                "index.html.md",
                url,
                f"Discord docs should not get /index.html.md appended: {url}",
            )

    def test_discord_docs_md_urls_preserved(self):
        """Discord llms.txt has .md URLs that should be preserved"""
        urls = [
            "https://docs.discord.com/developers/activities/building-an-activity.md",
            "https://docs.discord.com/developers/components/overview.md",
            "https://docs.discord.com/developers/change-log.md",
        ]

        result = self.converter._convert_to_md_urls(urls)

        self.assertEqual(len(result), 3)
        self.assertEqual(
            result[0],
            "https://docs.discord.com/developers/activities/building-an-activity.md",
        )

    def test_discord_docs_mixed_urls(self):
        """Mix of .md and non-.md URLs from Discord docs"""
        urls = [
            "https://docs.discord.com/developers/activities/building-an-activity.md",
            "https://docs.discord.com/developers/overview",
            "https://docs.discord.com/developers/overview#quick-start",
            "https://docs.discord.com/developers/bots/getting-started.md#step-1",
        ]

        result = self.converter._convert_to_md_urls(urls)

        # .md URLs preserved, non-.md as-is, anchors stripped & deduped
        self.assertEqual(len(result), 3)
        self.assertIn(
            "https://docs.discord.com/developers/activities/building-an-activity.md",
            result,
        )
        self.assertIn("https://docs.discord.com/developers/overview", result)
        self.assertIn(
            "https://docs.discord.com/developers/bots/getting-started.md",
            result,
        )


if __name__ == "__main__":
    unittest.main()
