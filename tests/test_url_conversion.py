"""
Tests for URL conversion logic (_convert_to_md_urls).
Covers bug fix for issue #277: URLs with anchor fragments causing 404 errors.
"""

import unittest

from skill_seekers.cli.doc_scraper import DocToSkillConverter


class TestConvertToMdUrls(unittest.TestCase):
    """Test suite for _convert_to_md_urls method"""

    def setUp(self):
        """Set up test converter instance"""
        config = {
            "name": "test",
            "description": "Test",
            "base_url": "https://example.com/docs/",
            "selectors": {"main_content": "article"},
        }
        self.converter = DocToSkillConverter(config, dry_run=True)

    def test_strips_anchor_fragments(self):
        """Test that anchor fragments (#anchor) are properly stripped from URLs"""
        urls = [
            "https://example.com/docs/quick-start#synchronous-initialization",
            "https://example.com/docs/api#methods",
            "https://example.com/docs/guide#installation",
        ]

        result = self.converter._convert_to_md_urls(urls)

        # All should be converted without anchor fragments
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "https://example.com/docs/quick-start/index.html.md")
        self.assertEqual(result[1], "https://example.com/docs/api/index.html.md")
        self.assertEqual(result[2], "https://example.com/docs/guide/index.html.md")

    def test_deduplicates_multiple_anchors_same_url(self):
        """Test that multiple anchors on the same URL are deduplicated"""
        urls = [
            "https://example.com/docs/api#method1",
            "https://example.com/docs/api#method2",
            "https://example.com/docs/api#method3",
            "https://example.com/docs/api",  # Same URL without anchor
        ]

        result = self.converter._convert_to_md_urls(urls)

        # Should only have one entry for the base URL
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "https://example.com/docs/api/index.html.md")

    def test_preserves_md_extension_urls(self):
        """Test that URLs already ending with .md are preserved"""
        urls = [
            "https://example.com/docs/guide.md",
            "https://example.com/docs/readme.md",
            "https://example.com/docs/api-reference.md",
        ]

        result = self.converter._convert_to_md_urls(urls)

        # Should preserve .md URLs without modification
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "https://example.com/docs/guide.md")
        self.assertEqual(result[1], "https://example.com/docs/readme.md")
        self.assertEqual(result[2], "https://example.com/docs/api-reference.md")

    def test_md_extension_with_anchor_fragments(self):
        """Test that .md URLs with anchors are handled correctly"""
        urls = [
            "https://example.com/docs/guide.md#introduction",
            "https://example.com/docs/guide.md#advanced",
            "https://example.com/docs/api.md#methods",
        ]

        result = self.converter._convert_to_md_urls(urls)

        # Should strip anchors but preserve .md extension
        self.assertEqual(len(result), 2)  # guide.md deduplicated
        self.assertIn("https://example.com/docs/guide.md", result)
        self.assertIn("https://example.com/docs/api.md", result)

    def test_does_not_match_md_in_path(self):
        """Test that URLs containing 'md' in path (but not ending with .md) are converted"""
        urls = [
            "https://example.com/cmd-line",
            "https://example.com/AMD-processors",
            "https://example.com/metadata",
        ]

        result = self.converter._convert_to_md_urls(urls)

        # All should be converted since they don't END with .md
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "https://example.com/cmd-line/index.html.md")
        self.assertEqual(result[1], "https://example.com/AMD-processors/index.html.md")
        self.assertEqual(result[2], "https://example.com/metadata/index.html.md")

    def test_removes_trailing_slashes(self):
        """Test that trailing slashes are removed before appending /index.html.md"""
        urls = [
            "https://example.com/docs/api/",
            "https://example.com/docs/guide//",
            "https://example.com/docs/reference",
        ]

        result = self.converter._convert_to_md_urls(urls)

        # All should have proper /index.html.md without double slashes
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "https://example.com/docs/api/index.html.md")
        self.assertEqual(result[1], "https://example.com/docs/guide/index.html.md")
        self.assertEqual(result[2], "https://example.com/docs/reference/index.html.md")

    def test_mixed_urls_with_and_without_anchors(self):
        """Test mixed URLs with various formats"""
        urls = [
            "https://example.com/docs/intro",
            "https://example.com/docs/intro#getting-started",
            "https://example.com/docs/api.md",
            "https://example.com/docs/api.md#methods",
            "https://example.com/docs/guide#section1",
            "https://example.com/docs/guide",
        ]

        result = self.converter._convert_to_md_urls(urls)

        # Should deduplicate to 3 unique base URLs
        self.assertEqual(len(result), 3)
        self.assertIn("https://example.com/docs/intro/index.html.md", result)
        self.assertIn("https://example.com/docs/api.md", result)
        self.assertIn("https://example.com/docs/guide/index.html.md", result)

    def test_empty_url_list(self):
        """Test that empty URL list returns empty result"""
        urls = []
        result = self.converter._convert_to_md_urls(urls)
        self.assertEqual(len(result), 0)
        self.assertEqual(result, [])

    def test_real_world_mikro_orm_case(self):
        """Test the exact URLs from issue #277 (MikroORM case)"""
        urls = [
            "https://mikro-orm.io/docs/quick-start",
            "https://mikro-orm.io/docs/quick-start#synchronous-initialization",
            "https://mikro-orm.io/docs/propagation",
            "https://mikro-orm.io/docs/defining-entities#formulas",
            "https://mikro-orm.io/docs/defining-entities#postgresql-native-enums",
        ]

        result = self.converter._convert_to_md_urls(urls)

        # Should deduplicate to 3 unique base URLs
        self.assertEqual(len(result), 3)
        self.assertIn("https://mikro-orm.io/docs/quick-start/index.html.md", result)
        self.assertIn("https://mikro-orm.io/docs/propagation/index.html.md", result)
        self.assertIn("https://mikro-orm.io/docs/defining-entities/index.html.md", result)

        # Should NOT contain any URLs with anchor fragments
        for url in result:
            self.assertNotIn("#", url, f"URL should not contain anchor: {url}")

    def test_preserves_query_parameters(self):
        """Test that query parameters are preserved (only anchors stripped)"""
        urls = [
            "https://example.com/docs/search?q=test",
            "https://example.com/docs/search?q=test#results",
            "https://example.com/docs/api?version=2",
        ]

        result = self.converter._convert_to_md_urls(urls)

        # Query parameters should be preserved, anchors stripped
        self.assertEqual(len(result), 2)  # search deduplicated
        # Note: Query parameters might not be ideal for .md conversion,
        # but they should be preserved if present
        self.assertTrue(
            any("?q=test" in url for url in result),
            "Query parameter should be preserved",
        )
        self.assertTrue(
            any("?version=2" in url for url in result),
            "Query parameter should be preserved",
        )

    def test_complex_anchor_formats(self):
        """Test various anchor formats (encoded, with dashes, etc.)"""
        urls = [
            "https://example.com/docs/guide#section-one",
            "https://example.com/docs/guide#section_two",
            "https://example.com/docs/guide#section%20three",
            "https://example.com/docs/guide#123",
        ]

        result = self.converter._convert_to_md_urls(urls)

        # All should deduplicate to single base URL
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "https://example.com/docs/guide/index.html.md")

    def test_url_order_preservation(self):
        """Test that first occurrence of base URL is preserved"""
        urls = [
            "https://example.com/docs/a",
            "https://example.com/docs/b#anchor",
            "https://example.com/docs/c",
            "https://example.com/docs/a#different-anchor",  # Duplicate base
        ]

        result = self.converter._convert_to_md_urls(urls)

        # Should have 3 unique URLs, first occurrence preserved
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "https://example.com/docs/a/index.html.md")
        self.assertEqual(result[1], "https://example.com/docs/b/index.html.md")
        self.assertEqual(result[2], "https://example.com/docs/c/index.html.md")


if __name__ == "__main__":
    unittest.main()
