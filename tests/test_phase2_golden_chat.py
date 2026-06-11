"""Golden-output tests for the chat scraper (Phase 2 port).

The golden trees under tests/golden/phase2/chat*/ were captured from the
PRE-DocumentSkillBuilder code; these tests prove the port is byte-identical.

Chat sections aren't heading+text shaped like EPUB/Word — they're
channel+date message groups — so the fixtures exercise chat's own build
paths: multi-channel categorization, single-channel topic-bucket
categorization, the single-category main.md fast path, message counts,
reactions embedded in text, code snippets (incl. >500 chars, empty
language → "unknown", user attribution), shared links (incl. >20
truncation), channel summaries, and the empty-export fallback.
"""

import copy
import re

import pytest

from tests.phase2_golden_utils import assert_matches_golden, build_snapshot

LONG_CODE = "def long_helper():\n" + "\n".join(f"    y{i} = {i}" for i in range(60))

# ── Multi-channel fixture (slack) ───────────────────────────────────────────

ENGINEERING_DAY1_TEXT = "\n\n".join(
    [
        "**alice** (2024-03-01T09:00:00): We hit an error and a bug in the deploy step",
        "  Reactions: :thumbsup: (2) :eyes: (1)",
        "**bob** (2024-03-01T09:05:00): Try this fix:\n```python\nprint('patched')\n```",
        "**alice** (2024-03-01T09:10:00): That fixed the crash, thanks!",
    ]
)

ENGINEERING_DAY2_TEXT = "\n\n".join(
    [
        "**alice** (2024-03-02T10:00:00): How do we install and setup docker here?",
        "**bob** (2024-03-02T10:15:00): Long helper below:\n```\n" + LONG_CODE + "\n```",
    ]
)

RANDOM_DAY1_TEXT = "**carol** (2024-03-01T12:00:00): Lunch at noon? See https://example.com/menu"

MULTI_CHANNEL_SECTIONS = [
    {
        "section_number": 1,
        "heading": "#engineering - 2024-03-01",
        "heading_level": "h2",
        "text": ENGINEERING_DAY1_TEXT,
        "headings": [],
        "code_samples": [
            {"code": "print('patched')", "language": "python", "quality_score": 7.0},
        ],
        "tables": [],
        "images": [],
        "channel": "engineering",
        "date": "2024-03-01",
        "message_count": 3,
    },
    {
        "section_number": 2,
        "heading": "#engineering - 2024-03-02",
        "heading_level": "h2",
        "text": ENGINEERING_DAY2_TEXT,
        "headings": [],
        "code_samples": [
            {"code": LONG_CODE, "language": "", "quality_score": 9.5},
        ],
        "tables": [],
        "images": [],
        "channel": "engineering",
        "date": "2024-03-02",
        "message_count": 2,
    },
    {
        "section_number": 3,
        "heading": "#random - 2024-03-01",
        "heading_level": "h2",
        "text": RANDOM_DAY1_TEXT,
        "headings": [],
        "code_samples": [],
        "tables": [],
        "images": [],
        "channel": "random",
        "date": "2024-03-01",
        "message_count": 1,
    },
]

# 21 links exercises the "... and N more links" truncation in SKILL.md
MULTI_CHANNEL_LINKS = [
    {
        "url": f"https://example.com/resource/{i}",
        "channel": "engineering" if i % 2 == 0 else "random",
        "user": "alice" if i % 2 == 0 else "carol",
        "timestamp": f"2024-03-01T09:{i:02d}:00",
        "context": f"see https://example.com/resource/{i} for details",
    }
    for i in range(21)
]

MULTI_CHANNEL_DATA = {
    "source": "fixtures/slack-export/",
    "platform": "slack",
    "metadata": {
        "total_messages": 6,
        "total_threads": 1,
        "total_code_snippets": 3,
        "total_links": 21,
        "unique_users": 3,
        "channels": ["engineering", "random"],
    },
    "total_sections": 3,
    "total_code_blocks": 3,
    "channel_summaries": {
        "engineering": {
            "message_count": 5,
            "unique_users": 2,
            "date_range": {
                "earliest": "2024-03-01T09:00:00",
                "latest": "2024-03-02T10:15:00",
            },
            "top_users": [
                {"user": "alice", "count": 3},
                {"user": "bob", "count": 2},
            ],
            "has_code": True,
        },
        "random": {
            "message_count": 1,
            "unique_users": 1,
            "date_range": {
                "earliest": "2024-03-01T12:00:00",
                "latest": "2024-03-01T12:00:00",
            },
            "top_users": [{"user": "carol", "count": 1}],
            "has_code": False,
        },
    },
    "code_snippets": [
        {
            "code": LONG_CODE,
            "language": "python",
            "quality_score": 9.5,
            "channel": "engineering",
            "user": "bob",
            "timestamp": "2024-03-02T10:15:00",
        },
        {
            "code": "print('patched')",
            "language": "python",
            "quality_score": 7.0,
            "channel": "engineering",
            "user": "bob",
            "timestamp": "2024-03-01T09:05:00",
        },
        {
            "code": "kubectl get pods",
            "language": "",
            "quality_score": 4.0,
            "channel": "engineering",
            "user": "alice",
            "timestamp": "2024-03-02T11:00:00",
        },
    ],
    "links": MULTI_CHANNEL_LINKS,
    "pages": MULTI_CHANNEL_SECTIONS,
}

# ── Single-channel fixture (discord) — topic-bucket categorization ──────────

TOPIC_SECTIONS = [
    {
        "section_number": 1,
        "heading": "#help - 2024-04-01",
        "heading_level": "h2",
        "text": "**dave** (2024-04-01T08:00:00): Got an error and a crash, traceback attached",
        "headings": [],
        "code_samples": [],
        "tables": [],
        "images": [],
        "channel": "help",
        "date": "2024-04-01",
        "message_count": 1,
    },
    {
        "section_number": 2,
        "heading": "#help - 2024-04-02",
        "heading_level": "h2",
        "text": "**erin** (2024-04-02T08:00:00): How do I install and setup the docker image?",
        "headings": [],
        "code_samples": [],
        "tables": [],
        "images": [],
        "channel": "help",
        "date": "2024-04-02",
        "message_count": 1,
    },
    {
        "section_number": 3,
        "heading": "#help - 2024-04-03",
        "heading_level": "h2",
        "text": "**dave** (2024-04-03T08:00:00): Happy Friday everyone!",
        "headings": [],
        "code_samples": [],
        "tables": [],
        "images": [],
        "channel": "help",
        "date": "2024-04-03",
        "message_count": 1,
    },
]

TOPIC_DATA = {
    "source": "fixtures/discord-export.json",
    "platform": "discord",
    "metadata": {
        "total_messages": 3,
        "total_threads": 0,
        "total_code_snippets": 0,
        "total_links": 0,
        "unique_users": 2,
        "channels": ["help"],
    },
    "total_sections": 3,
    "total_code_blocks": 0,
    "channel_summaries": {
        "help": {
            "message_count": 3,
            "unique_users": 2,
            "date_range": {
                "earliest": "2024-04-01T08:00:00",
                "latest": "2024-04-03T08:00:00",
            },
            "top_users": [
                {"user": "dave", "count": 2},
                {"user": "erin", "count": 1},
            ],
            "has_code": False,
        },
    },
    "code_snippets": [],
    "links": [],
    "pages": TOPIC_SECTIONS,
}

# ── Single-category fixture — no topic matches → general → main.md ──────────

SINGLE_CATEGORY_DATA = {
    "source": "fixtures/slack-export/",
    "platform": "slack",
    "metadata": {
        "total_messages": 1,
        "total_threads": 0,
        "total_code_snippets": 0,
        "total_links": 0,
        "unique_users": 1,
        "channels": ["general"],
    },
    "total_sections": 1,
    "total_code_blocks": 0,
    "channel_summaries": {
        "general": {
            "message_count": 1,
            "unique_users": 1,
            "date_range": {
                "earliest": "2024-05-01T10:00:00",
                "latest": "2024-05-01T10:00:00",
            },
            "top_users": [{"user": "frank", "count": 1}],
            "has_code": False,
        },
    },
    "code_snippets": [],
    "links": [],
    "pages": [
        {
            "section_number": 1,
            "heading": "#general - 2024-05-01",
            "heading_level": "h2",
            "text": "**frank** (2024-05-01T10:00:00): Welcome aboard!",
            "headings": [],
            "code_samples": [],
            "tables": [],
            "images": [],
            "channel": "general",
            "date": "2024-05-01",
            "message_count": 1,
        },
    ],
}

# ── Empty fixture — no messages extracted ────────────────────────────────────

EMPTY_DATA = {
    "source": "fixtures/empty-export/",
    "platform": "slack",
    "metadata": {
        "total_messages": 0,
        "total_threads": 0,
        "total_code_snippets": 0,
        "total_links": 0,
        "unique_users": 0,
        "channels": [],
    },
    "total_sections": 0,
    "total_code_blocks": 0,
    "channel_summaries": {},
    "code_snippets": [],
    "links": [],
    "pages": [],
}


def _make_converter(tmp_path, name, platform, extracted):
    from skill_seekers.cli.chat_scraper import ChatToSkillConverter

    converter = ChatToSkillConverter(
        {
            "name": name,
            "description": f"Use when testing the {name} golden build",
            "platform": platform,
            "output_dir": str(tmp_path / "skill"),
        }
    )
    converter.extracted_data = copy.deepcopy(extracted)
    return converter


def test_chat_multi_channel_matches_golden(tmp_path):
    """Two channels → channel-name categories with {key}_sN-sM.md filenames."""
    converter = _make_converter(tmp_path, "golden_chat", "slack", MULTI_CHANNEL_DATA)
    assert_matches_golden(build_snapshot(converter), "chat")


def test_chat_topic_buckets_match_golden(tmp_path):
    """Single channel → topic-bucket categories plus General Discussion."""
    converter = _make_converter(tmp_path, "golden_chat_topics", "discord", TOPIC_DATA)
    assert_matches_golden(build_snapshot(converter), "chat_topics")


def test_chat_single_category_matches_golden(tmp_path):
    """No topic matches → one 'general' category → main.md fast path."""
    converter = _make_converter(tmp_path, "golden_chat_single", "slack", SINGLE_CATEGORY_DATA)
    assert_matches_golden(build_snapshot(converter), "chat_single")


def test_chat_empty_matches_golden(tmp_path):
    """Empty export → 'content' fallback category and section_01.md filename."""
    converter = _make_converter(tmp_path, "golden_chat_empty", "slack", EMPTY_DATA)
    assert_matches_golden(build_snapshot(converter), "chat_empty")


@pytest.mark.parametrize(
    ("name", "platform", "data"),
    [
        ("golden_chat", "slack", MULTI_CHANNEL_DATA),
        ("golden_chat_topics", "discord", TOPIC_DATA),
        ("golden_chat_single", "slack", SINGLE_CATEGORY_DATA),
        ("golden_chat_empty", "slack", EMPTY_DATA),
    ],
)
def test_skill_md_reference_links_point_at_real_files(tmp_path, name, platform, data):
    """Every `references/...` link in SKILL.md must name a file that was
    actually written — the nav used to derive links from sanitized titles
    while the writer named files via _reference_filename (DOC-07 drift)."""
    converter = _make_converter(tmp_path, name, platform, data)
    snapshot = build_snapshot(converter)

    skill_md = snapshot["SKILL.md"].decode("utf-8")
    links = re.findall(r"`(references/[^`]+)`", skill_md)
    assert links, "SKILL.md should link at least references/index.md"
    missing = [link for link in links if link not in snapshot]
    assert not missing, f"SKILL.md links to nonexistent files: {missing}"
