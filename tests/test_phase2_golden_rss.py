"""Golden-output tests for the RSS scraper (Phase 2 port).

The golden trees under tests/golden/phase2/rss*/ were captured from the
PRE-DocumentSkillBuilder code; these tests prove the port is byte-identical.

RSS extracted_data is article-shaped (not section-shaped), so the fixtures
exercise the rss-specific build paths: tag categorization with normalized-key
dedup, the "uncategorized" bucket, the empty-sanitization "unnamed" fallback,
the empty-feed "all_articles" fallback, summary truncation (>200 chars),
inline content vs summary, full_text, feed description truncation (>300
chars), >50 tags overflow, author counts, date range, and followed_links
Yes/No statistics.
"""

import copy

from tests.phase2_golden_utils import assert_matches_golden, build_snapshot

LONG_SUMMARY = (
    "This is a deliberately long summary that keeps going well past the two "
    "hundred character truncation threshold used by the recent-articles block "
    "of SKILL.md so that the shortened form with a trailing ellipsis is "
    "exercised by the golden tree comparison here."
)

LONG_FEED_DESCRIPTION = (
    "A feed description that is intentionally longer than the three hundred "
    "character limit applied in the Feed Information block of SKILL.md. " * 4
)

ARTICLES = [
    {
        # Overlapping normalized category keys ("Dev Ops" and "dev-ops" both
        # sanitize to "dev_ops") exercise the duplicate-article guard.
        "id": "urn:article:1",
        "title": "Continuous Delivery in Practice",
        "link": "https://example.com/posts/cd-in-practice",
        "summary": LONG_SUMMARY,
        "content": "Inline feed content that differs from the summary text.",
        "published": "Mon, 01 Jan 2024 10:00:00 GMT",
        "published_iso": "2024-01-01T10:00:00",
        "author": "Jane Doe",
        "categories": ["Dev Ops", "dev-ops"],
    },
    {
        # content == summary exercises the skipped "### Content" branch.
        "id": "urn:article:2",
        "title": "Typing Tips for Python",
        "link": "https://example.com/posts/typing-tips",
        "summary": "Short notes on gradual typing.",
        "content": "Short notes on gradual typing.",
        "published": "Fri, 15 Mar 2024 08:30:00 GMT",
        "published_iso": "2024-03-15T08:30:00",
        "author": "John Roe",
        "categories": ["Python"],
    },
    {
        # No categories -> "uncategorized" bucket; no link/published/author
        # metadata lines; has scraped full_text.
        "id": "urn:article:3",
        "title": "An Uncategorized Note",
        "link": "",
        "summary": "A note without tags.",
        "content": "",
        "published": "",
        "published_iso": "",
        "author": "Jane Doe",
        "categories": [],
        "full_text": "# Scraped Heading\n\nFull article text fetched from the page.",
    },
    {
        # Category of only symbols sanitizes to "" -> "unnamed" filename.
        "id": "urn:article:4",
        "title": "Symbols Only",
        "link": "https://example.com/posts/symbols",
        "summary": "",
        "content": "",
        "published": "Sat, 10 Feb 2024 12:00:00 GMT",
        "published_iso": "2024-02-10T12:00:00",
        "author": "",
        "categories": ["★★★"],
    },
]

# 55 tags exercise the ">50 ... and N more" overflow in the Tags section.
ALL_CATEGORIES = sorted(
    {"Dev Ops", "dev-ops", "Python", "★★★"} | {f"tag{i:02d}" for i in range(51)}
)


def _extracted_data() -> dict:
    return {
        "source": "https://example.com/feed.xml",
        "feed_type": "RSS 2.0",
        "feed_metadata": {
            "title": "Example Engineering Blog",
            "description": LONG_FEED_DESCRIPTION,
            "link": "https://example.com",
            "language": "en-us",
            "author": "Example Team",
            "published": "Mon, 01 Jan 2024 10:00:00 GMT",
            "generator": "ExampleCMS 2.0",
            "image_url": "https://example.com/logo.png",
            "rights": "© Example Inc.",
        },
        "total_articles": len(ARTICLES),
        "followed_links": True,
        "all_categories": ALL_CATEGORIES,
        "articles": copy.deepcopy(ARTICLES),
    }


def test_rss_build_matches_golden(tmp_path):
    from skill_seekers.cli.rss_scraper import RssToSkillConverter

    converter = RssToSkillConverter(
        {
            "name": "golden_rss",
            "description": "Use when testing the rss golden build",
            "feed_url": "https://example.com/feed.xml",
            "output_dir": str(tmp_path / "skill"),
        }
    )
    converter.extracted_data = _extracted_data()
    assert_matches_golden(build_snapshot(converter), "rss")


def test_rss_empty_feed_matches_golden(tmp_path):
    """No articles -> the all_articles fallback category and 'No' statistics."""
    from skill_seekers.cli.rss_scraper import RssToSkillConverter

    converter = RssToSkillConverter(
        {
            "name": "golden_rss_empty",
            "description": "Use when testing the empty rss golden build",
            "feed_url": "https://example.com/atom.xml",
            "output_dir": str(tmp_path / "skill"),
        }
    )
    converter.extracted_data = {
        "source": "https://example.com/atom.xml",
        "feed_type": "Atom",
        "feed_metadata": {
            "title": "Quiet Feed",
            "description": "A feed with no entries yet.",
            "link": "https://example.com/quiet",
            "language": "",
            "author": "",
            "published": "",
            "generator": "",
            "image_url": "",
            "rights": "",
        },
        "total_articles": 0,
        "followed_links": False,
        "all_categories": [],
        "articles": [],
    }
    assert_matches_golden(build_snapshot(converter), "rss_empty")
