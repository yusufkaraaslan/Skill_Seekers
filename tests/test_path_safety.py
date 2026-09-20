"""Tests for the shared single-path-segment validator (CWE-22, #462)."""

from __future__ import annotations

import pytest

from skill_seekers.services.path_safety import validate_path_segment


@pytest.mark.parametrize(
    "name", ["react", "spine-unity", "my_skill_v2", "skill.v1", "temp_react", "0day", "A.b-c_d"]
)
def test_accepts_ordinary_slugs(name):
    assert validate_path_segment(name, label="config name") == name


@pytest.mark.parametrize(
    "name",
    [
        "",
        " ",
        ".",
        "..",
        ".git",
        ".hidden",
        "a..b",
        "../outside",
        "x/../y",
        "nested/source",
        "nested\\source",  # single backslash
        "/absolute",
        "C:\\cache",  # drive prefix + single backslash
        "C:",
        "a\x00b",  # embedded NUL
        "sp ace",
        "tab\tname",
        "ünïcode",
        None,
        42,
    ],
)
def test_rejects_anything_that_is_not_one_safe_segment(name):
    with pytest.raises(ValueError, match="single path segment"):
        validate_path_segment(name, label="config name")


def test_error_message_names_the_label_and_value():
    with pytest.raises(ValueError, match="Invalid workflow name '../x'"):
        validate_path_segment("../x", label="workflow name")


def test_existing_validators_delegate_to_the_shared_one():
    """One definition: workflow, config-publisher and marketplace checks agree with git's."""
    from skill_seekers.mcp.tools.workflow_tools import _validate_name
    from skill_seekers.services.git_repo import validate_path_segment as via_git
    from skill_seekers.services.marketplace_publisher import MarketplacePublisher

    assert via_git is validate_path_segment
    for bad in (".git", "a\x00b", "../x"):
        with pytest.raises(ValueError):
            _validate_name(bad)
        with pytest.raises(ValueError):
            MarketplacePublisher._validate_skill_name(bad)
