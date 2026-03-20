"""
Tests for URL conversion logic (_convert_to_md_urls).
Covers bug fix for issue #277: URLs with anchor fragments causing 404 errors.

Updated: _convert_to_md_urls no longer blindly appends /index.html.md to non-.md URLs.
It now strips anchors, deduplicates, and preserves original URLs as-is.
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

        # All should have anchors stripped
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "https://example.com/docs/quick-start")
        self.assertEqual(result[1], "https://example.com/docs/api")
        self.assertEqual(result[2], "https://example.com/docs/guide")

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
        self.assertEqual(result[0], "https://example.com/docs/api")

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

    def test_non_md_urls_not_converted(self):
        """Test that non-.md URLs are NOT converted to /index.html.md (issue #277)"""
        urls = [
            "https://example.com/docs/getting-started",
            "https://example.com/docs/api-reference",
            "https://example.com/docs/tutorials",
        ]

        result = self.converter._convert_to_md_urls(urls)

        # Should preserve URLs as-is, NOT append /index.html.md
        self.assertEqual(len(result), 3)
        for url in result:
            self.assertNotIn("index.html.md", url, f"Should not append /index.html.md: {url}")

        self.assertEqual(result[0], "https://example.com/docs/getting-started")
        self.assertEqual(result[1], "https://example.com/docs/api-reference")
        self.assertEqual(result[2], "https://example.com/docs/tutorials")

    def test_does_not_match_md_in_path(self):
        """Test that URLs containing 'md' in path are preserved as-is"""
        urls = [
            "https://example.com/cmd-line",
            "https://example.com/AMD-processors",
            "https://example.com/metadata",
        ]

        result = self.converter._convert_to_md_urls(urls)

        # URLs with 'md' substring (not extension) should be preserved as-is
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "https://example.com/cmd-line")
        self.assertEqual(result[1], "https://example.com/AMD-processors")
        self.assertEqual(result[2], "https://example.com/metadata")

    def test_removes_trailing_slashes_for_dedup(self):
        """Test that trailing slash variants are deduplicated"""
        urls = [
            "https://example.com/docs/api/",
            "https://example.com/docs/api",
        ]

        result = self.converter._convert_to_md_urls(urls)

        # Should deduplicate (trailing slash vs no slash)
        self.assertEqual(len(result), 1)

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
        self.assertIn("https://example.com/docs/intro", result)
        self.assertIn("https://example.com/docs/api.md", result)
        self.assertIn("https://example.com/docs/guide", result)

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

        # Should NOT contain any URLs with anchor fragments
        for url in result:
            self.assertNotIn("#", url, f"URL should not contain anchor: {url}")

        # Should NOT contain /index.html.md
        for url in result:
            self.assertNotIn("index.html.md", url, f"Should not append /index.html.md: {url}")

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
        self.assertEqual(result[0], "https://example.com/docs/guide")

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
        self.assertEqual(result[0], "https://example.com/docs/a")
        self.assertEqual(result[1], "https://example.com/docs/b")
        self.assertEqual(result[2], "https://example.com/docs/c")

    def test_discord_docs_case(self):
        """Test the Discord docs case reported by @skeith in issue #277"""
        urls = [
            "https://docs.discord.com/developers/activities/building-an-activity",
            "https://docs.discord.com/developers/activities/design-patterns",
            "https://docs.discord.com/developers/components/overview",
            "https://docs.discord.com/developers/bots/getting-started#step-1",
        ]

        result = self.converter._convert_to_md_urls(urls)

        # No /index.html.md should be appended
        for url in result:
            self.assertNotIn("index.html.md", url, f"Should not append /index.html.md: {url}")
            self.assertNotIn("#", url, f"Should not contain anchor: {url}")

        self.assertEqual(len(result), 4)


class TestHasMdExtension(unittest.TestCase):
    """Test suite for _has_md_extension static method"""

    def test_md_extension(self):
        self.assertTrue(DocToSkillConverter._has_md_extension("https://example.com/page.md"))

    def test_md_with_query(self):
        self.assertTrue(DocToSkillConverter._has_md_extension("https://example.com/page.md?v=1"))

    def test_no_md_extension(self):
        self.assertFalse(DocToSkillConverter._has_md_extension("https://example.com/page"))

    def test_md_in_path_not_extension(self):
        """'cmd-line' contains 'md' but is not a .md extension"""
        self.assertFalse(DocToSkillConverter._has_md_extension("https://example.com/cmd-line"))

    def test_md_in_domain(self):
        """'.md' in domain should not match"""
        self.assertFalse(DocToSkillConverter._has_md_extension("https://docs.md.example.com/page"))

    def test_mdx_not_md(self):
        """.mdx is not .md"""
        self.assertFalse(DocToSkillConverter._has_md_extension("https://example.com/page.mdx"))

    def test_md_in_middle_of_path(self):
        """.md in middle of path should not match"""
        self.assertFalse(DocToSkillConverter._has_md_extension("https://example.com/page.md/subpage"))

    def test_index_html_md(self):
        self.assertTrue(DocToSkillConverter._has_md_extension("https://example.com/page/index.html.md"))


if __name__ == "__main__":
    unittest.main()
