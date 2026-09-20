"""Tests for the opt-in SQLite reference-search index."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from skill_seekers.cli.skill_indexer import (
    _anchor_for,
    _split_sections,
    build_index,
    index_skill,
    write_search_script,
)


def _write_skill(skill_dir: Path) -> None:
    (skill_dir / "references" / "network").mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: example\n---\n\nUse the references.\n")
    (skill_dir / "references" / "api.md").write_text(
        "# Connecting Signals\n\nUse node.connect(signal, callable) to subscribe.\n\n"
        "## Disconnecting\n\nDisconnect when the object is no longer needed.\n",
        encoding="utf-8",
    )
    (skill_dir / "references" / "network" / "http.md").write_text(
        "# HTTP Requests\n\nrequest(url)\n\nUse a timeout for every request.\n",
        encoding="utf-8",
    )


def _row_dump(database: Path) -> list[tuple]:
    with sqlite3.connect(database) as connection:
        return connection.execute(
            "SELECT file, heading, anchor, category, kind, code_langs FROM sections ORDER BY id"
        ).fetchall()


def test_build_index_records_heading_sections_and_stable_row_order(tmp_path: Path) -> None:
    """The index keeps sorted file order, anchors, categories, and code metadata."""
    skill_dir = tmp_path / "skill"
    _write_skill(skill_dir)

    first = build_index(skill_dir)
    first_rows = _row_dump(first.index_path)
    second = build_index(skill_dir)

    assert first.section_count == 3
    assert first_rows == _row_dump(second.index_path)
    assert first_rows == [
        ("references/api.md", "Connecting Signals", "connecting-signals", "general", "api", ""),
        ("references/api.md", "Disconnecting", "disconnecting", "general", "api", ""),
        ("references/network/http.md", "HTTP Requests", "http-requests", "network", "http", ""),
    ]


def test_generated_search_script_returns_ranked_anchor_pointers_and_json(tmp_path: Path) -> None:
    """The self-contained script queries the index without importing the package."""
    skill_dir = tmp_path / "skill"
    _write_skill(skill_dir)
    build_index(skill_dir)
    search_script = write_search_script(skill_dir)

    result = subprocess.run(
        [sys.executable, search_script, "connect signal", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )

    hits = json.loads(result.stdout)
    assert hits[0]["file"] == "references/api.md"
    assert hits[0]["anchor"] == "connecting-signals"
    assert "connect" in hits[0]["snippet"].lower()
    assert "## Search reference documentation" in (skill_dir / "SKILL.md").read_text()


def test_generated_search_script_falls_back_to_like_when_fts_is_unavailable(
    tmp_path: Path, monkeypatch
) -> None:
    """A skill remains queryable on Python builds that omit SQLite FTS5."""
    skill_dir = tmp_path / "skill"
    _write_skill(skill_dir)
    monkeypatch.setattr("skill_seekers.cli.skill_indexer._create_fts_table", lambda _: False)
    result = build_index(skill_dir)
    search_script = write_search_script(skill_dir)

    assert not result.fts_enabled
    output = subprocess.run(
        [sys.executable, search_script, "timeout", "--category", "network"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "references/network/http.md#http-requests" in output


def test_search_instruction_is_idempotent(tmp_path: Path) -> None:
    """Rebuilding an index does not append duplicate guidance to SKILL.md."""
    skill_dir = tmp_path / "skill"
    _write_skill(skill_dir)

    build_index(skill_dir)
    write_search_script(skill_dir)
    build_index(skill_dir)
    write_search_script(skill_dir)

    assert (skill_dir / "SKILL.md").read_text().count("## Search reference documentation") == 1


def test_headings_inside_code_fences_are_not_sections() -> None:
    """`# comment` lines in bash/python blocks must not fragment the real section."""
    text = (
        "# Install\n\n```bash\n# update packages first\nsudo apt update\n```\n\n"
        "~~~python\n# compute\nx = 1\n~~~\n\n## Usage\n\ntext\n"
    )
    sections = _split_sections("references/guide.md", text)
    assert [s.heading for s in sections] == ["Install", "Usage"]
    assert sections[0].code_langs == "bash,python"
    assert "sudo apt update" in sections[0].content


def test_anchors_follow_github_rules() -> None:
    assert _anchor_for("Foo -- Bar") == "foo----bar"
    assert _anchor_for("Node  Types") == "node--types"
    assert _anchor_for("get_node(path)") == "get_nodepath"
    assert _anchor_for("Über Ärger") == "über-ärger"
    assert _anchor_for("???") == "section"


def test_table_of_contents_pages_are_not_indexed(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    _write_skill(skill_dir)
    (skill_dir / "references" / "index.md").write_text("# Index\n\n- [api](api.md)\n")
    (skill_dir / "references" / "network" / "index.md").write_text("# Network index\n")

    result = build_index(skill_dir)

    assert result.section_count == 3
    assert all(row[0] != "references/index.md" for row in _row_dump(result.index_path))


def test_index_skill_skips_script_and_instruction_when_nothing_is_indexable(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    (skill_dir / "references").mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: empty\n---\n")

    result = index_skill(skill_dir)

    assert result.section_count == 0
    assert not (skill_dir / "scripts" / "index.db").exists()
    assert not (skill_dir / "scripts" / "search.py").exists()
    assert "Search reference documentation" not in (skill_dir / "SKILL.md").read_text()


def test_index_skill_installs_everything_when_indexable(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    _write_skill(skill_dir)

    result = index_skill(skill_dir)

    assert result.section_count == 3
    assert (skill_dir / "scripts" / "search.py").exists()
    assert "## Search reference documentation" in (skill_dir / "SKILL.md").read_text()


def test_fts_operator_words_are_plain_terms(tmp_path: Path) -> None:
    """Bare NOT / OR / AND / NEAR are FTS5 operators; the script must quote tokens."""
    skill_dir = tmp_path / "skill"
    (skill_dir / "references").mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: ops\n---\n")
    (skill_dir / "references" / "errors.md").write_text(
        "# Errors\n\nIf the connection was not found, retry or abort and log it.\n"
    )
    result = build_index(skill_dir)
    assert result.fts_enabled, "FTS5 required for this test"
    search_script = write_search_script(skill_dir)

    # Every operator word here also occurs as a plain word in the text, so a
    # hit proves it was matched as a term (a syntax error would return []).
    for query in ("NOT found", "connection OR retry", "abort AND log", "NEAR misses AND found"):
        proc = subprocess.run(
            [sys.executable, search_script, query, "--json"],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stderr
        hits = json.loads(proc.stdout)
        expected = [] if "misses" in query else ["errors"]
        assert [h["anchor"] for h in hits] == expected, query


def test_like_fallback_matches_literally_and_case_folds(tmp_path: Path, monkeypatch) -> None:
    """Underscore is not a wildcard and non-ASCII case folds, unlike SQL LIKE/lower()."""
    skill_dir = tmp_path / "skill"
    (skill_dir / "references").mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: like\n---\n")
    (skill_dir / "references" / "a.md").write_text(
        "# Nodes\n\nCall get_node(path).\n\n# Dashes\n\nUse get-node here.\n\n# Umlaut\n\nÜber alles.\n"
    )
    monkeypatch.setattr("skill_seekers.cli.skill_indexer._create_fts_table", lambda _: False)
    build_index(skill_dir)
    search_script = write_search_script(skill_dir)

    def anchors(query: str) -> list[str]:
        out = subprocess.run(
            [sys.executable, search_script, query, "--json"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        return [h["anchor"] for h in json.loads(out)]

    assert anchors("get_node") == ["nodes"]
    assert anchors("über") == ["umlaut"]
