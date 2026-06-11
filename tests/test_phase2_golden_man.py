"""Golden-output tests for the man page scraper (Phase 2 port).

The golden trees under tests/golden/phase2/man*/ were captured from the
PRE-DocumentSkillBuilder code; these tests prove the port is byte-identical.

Three goldens cover the categorization paths:
- "man": prefix grouping (git-* pages collapse into one category) with
  multi-category numbered reference filenames.
- "man_kw": explicit keyword categories plus the "other" fallback bucket.
- "man_single": single man page → single category, unnumbered filename.

The fixture exercises every generation branch: section label present/absent,
title == name (skipped) vs distinct, missing synopsis, >3000-char description
truncation, >200-char option description truncation (and the >120-char
SKILL.md variant), prose-only examples, SEE ALSO refs, extra sections with
and without >1500-char truncation, empty extra sections (skipped).
"""

import copy

from tests.phase2_golden_utils import assert_matches_golden, build_snapshot

LONG_DESCRIPTION = "Long description sentence about commit diffing output. " * 60  # >3000
LONG_NOTES = "Implementation note about rename detection. " * 40  # >1500
LONG_OPT_DESC = (
    "Limit the number of commits to output, interacting subtly with pathspec "
    "filtering, history simplification, and the --follow option in ways that "
    "require a description well over two hundred characters to explain fully."
)

PAGES = [
    {
        "name": "git-log",
        "section": 1,
        "title": "git-log - Show commit logs",
        "synopsis": "git log [<options>] [<revision-range>] [[--] <path>...]",
        "description": "Shows the commit logs. List commits reachable from the given revs.",
        "sections": {
            "NAME": "git-log - Show commit logs",
            "SYNOPSIS": "git log [<options>] [<revision-range>] [[--] <path>...]",
            "DESCRIPTION": "Shows the commit logs. List commits reachable from the given revs.",
            "OPTIONS": "-p\n    Generate patch output.",
            "EXAMPLES": "git log -3",
            "SEE ALSO": "git-diff(1), gitk(1)",
            "ENVIRONMENT": "GIT_PAGER controls the pager used for output.",
            "BUGS": "   ",  # whitespace-only → skipped extra section
        },
        "options": [
            {"flag": "-p", "description": "Generate patch output."},
            {"flag": "--max-count=<number>", "description": LONG_OPT_DESC},
        ],
        "examples": [
            {"description": "Show the last three commits", "command": "git log -3"},
            {"description": "Prose-only example with no command", "command": ""},
        ],
        "see_also": ["git-diff", "gitk"],
        "raw_text": "GIT-LOG(1) raw text",
    },
    {
        "name": "git-diff",
        "section": 1,
        "title": "git-diff - Show changes between commits",
        "synopsis": "git diff [<options>] [<commit>] [--] [<path>...]",
        "description": LONG_DESCRIPTION,
        "sections": {"NOTES": LONG_NOTES},
        "options": [],
        "examples": [],
        "see_also": ["git-log"],
        "raw_text": "GIT-DIFF(1) raw text",
    },
    {
        "name": "curl",
        "section": None,  # no section label anywhere
        "title": "curl",  # equals name → bold title line skipped
        "synopsis": "",  # skipped in reference + quick command reference
        "description": "Transfer a URL using one of the supported protocols.",
        "sections": {},
        "options": [{"flag": "-s, --silent", "description": "Silent mode."}],
        "examples": [{"description": "Fetch a page", "command": "curl https://example.com"}],
        "see_also": [],
        "raw_text": "CURL(1) raw text",
    },
]


def _extracted_data(pages: list[dict]) -> dict:
    see_also_all: list[str] = []
    for page in pages:
        see_also_all.extend(page.get("see_also", []))
    return {
        "source": "man command",
        "total_pages": len(pages),
        "total_options": sum(len(p["options"]) for p in pages),
        "total_examples": sum(len(p["examples"]) for p in pages),
        "see_also": sorted(set(see_also_all)),
        "pages": copy.deepcopy(pages),
    }


def _converter(tmp_path, name: str, extra_config: dict | None = None):
    from skill_seekers.cli.man_scraper import ManPageToSkillConverter

    config = {
        "name": name,
        "description": "Use when testing the man golden build",
        "man_names": ["git-log", "git-diff", "curl"],
        "output_dir": str(tmp_path / "skill"),
    }
    config.update(extra_config or {})
    return ManPageToSkillConverter(config)


def test_man_prefix_grouping_matches_golden(tmp_path):
    """No categories → auto prefix grouping (git-* → git, curl → curl)."""
    converter = _converter(tmp_path, "golden_man")
    converter.extracted_data = _extracted_data(PAGES)
    assert_matches_golden(build_snapshot(converter), "man")


def test_man_keyword_categorization_matches_golden(tmp_path):
    """Explicit keyword categories; curl matches nothing → 'other' bucket."""
    converter = _converter(
        tmp_path,
        "golden_man_kw",
        {"categories": {"version_control": ["commit", "diff"]}},
    )
    converter.extracted_data = _extracted_data(PAGES)
    assert_matches_golden(build_snapshot(converter), "man_kw")


def test_man_single_page_matches_golden(tmp_path):
    """One page → single category and unnumbered reference filename."""
    converter = _converter(
        tmp_path,
        "golden_man_single",
        {"man_names": ["curl"]},
    )
    converter.extracted_data = _extracted_data([PAGES[2]])
    assert_matches_golden(build_snapshot(converter), "man_single")
