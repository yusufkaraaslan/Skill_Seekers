"""
Real-world integration test for Issue #277: URL conversion bug with anchor fragments.
Tests the exact MikroORM case that was reported in the issue.
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
        # These are the actual problematic URLs from the bug report
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
            self.assertNotIn(
                "#synchronous-initialization/index.html.md",
                url,
                "Should not append /index.html.md after anchor fragments",
            )
            self.assertNotIn(
                "#formulas/index.html.md",
                url,
                "Should not append /index.html.md after anchor fragments",
            )
            self.assertNotIn(
                "#postgresql-native-enums/index.html.md",
                url,
                "Should not append /index.html.md after anchor fragments",
            )

        # Verify correct transformed URLs

        # Check that we got the expected number of unique URLs
        # Note: defining-entities has both .md and non-.md versions, so we have 2 entries for it
        self.assertEqual(
            len(result),
            7,
            f"Should have 7 unique base URLs after deduplication, got {len(result)}",
        )

        # Verify specific URLs that were causing 404s are now correct
        self.assertIn(
            "https://mikro-orm.io/docs/quick-start/index.html.md",
            result,
            "quick-start URL should be correctly transformed",
        )
        self.assertIn(
            "https://mikro-orm.io/docs/propagation/index.html.md",
            result,
            "propagation URL should be correctly transformed",
        )
        self.assertIn(
            "https://mikro-orm.io/docs/defining-entities.md",
            result,
            "defining-entities.md should preserve .md extension",
        )

    def test_no_404_causing_urls_generated(self):
        """Verify that no URLs matching the 404 error pattern are generated"""
        # The exact 404-causing URL pattern from the issue
        problematic_patterns = [
            "/index.html.md#",  # /index.html.md should never come after #
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

    def test_deduplication_prevents_multiple_requests(self):
        """Verify that multiple anchors on same page don't create duplicate requests"""
        # From the issue: These should all map to the same base URL
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
        self.assertEqual(
            result[0],
            "https://mikro-orm.io/docs/defining-entities/index.html.md",
        )

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
        # Mock response for llms.txt content
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

        # Simulate the llms.txt parsing flow
        urls_from_llms = [
            "https://mikro-orm.io/docs/quick-start",
            "https://mikro-orm.io/docs/quick-start#synchronous-initialization",
            "https://mikro-orm.io/docs/propagation",
            "https://mikro-orm.io/docs/defining-entities#formulas",
        ]

        # Convert URLs (this is what happens in _try_llms_txt_v2)
        converted_urls = self.converter._convert_to_md_urls(urls_from_llms)

        # Verify converted URLs are valid
        # In real scenario, these would be added to pending_urls and scraped
        self.assertTrue(len(converted_urls) > 0, "Should generate at least one URL to scrape")

        # Verify no URLs would cause 404 (no anchors in middle of path)
        for url in converted_urls:
            # Check URL structure is valid
            self.assertRegex(
                url,
                r"^https://[^#]+$",  # Should not contain # anywhere
                f"URL should not contain anchor fragments: {url}",
            )

            # Verify the problematic pattern from the issue doesn't exist
            self.assertNotRegex(
                url,
                r"#[^/]+/index\.html\.md",
                f"URL should not have /index.html.md after anchor: {url}",
            )

    def test_issue_277_error_message_urls(self):
        """
        Test the exact URLs that appeared in error messages from the issue report.
        These were the actual 404-causing URLs that need to be fixed.
        """
        # These are the MALFORMED URLs that caused 404 errors (with anchors in the middle)
        error_urls_with_anchors = [
            "https://mikro-orm.io/docs/quick-start#synchronous-initialization/index.html.md",
            "https://mikro-orm.io/docs/defining-entities#formulas/index.html.md",
            "https://mikro-orm.io/docs/defining-entities#postgresql-native-enums/index.html.md",
        ]

        # Extract the input URLs that would have generated these errors
        input_urls = [
            "https://mikro-orm.io/docs/quick-start#synchronous-initialization",
            "https://mikro-orm.io/docs/propagation",
            "https://mikro-orm.io/docs/defining-entities#formulas",
            "https://mikro-orm.io/docs/defining-entities#postgresql-native-enums",
        ]

        result = self.converter._convert_to_md_urls(input_urls)

        # Verify NONE of the malformed error URLs (with anchors) are generated
        for error_url in error_urls_with_anchors:
            self.assertNotIn(
                error_url,
                result,
                f"Should not generate the 404-causing URL: {error_url}",
            )

        # Verify correct URLs are generated instead
        correct_urls = [
            "https://mikro-orm.io/docs/quick-start/index.html.md",
            "https://mikro-orm.io/docs/propagation/index.html.md",
            "https://mikro-orm.io/docs/defining-entities/index.html.md",
        ]

        for correct_url in correct_urls:
            self.assertIn(
                correct_url,
                result,
                f"Should generate the correct URL: {correct_url}",
            )


if __name__ == "__main__":
    unittest.main()
