"""Tests for the opt-in SQLite reference-search index."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from skill_seekers.cli.skill_indexer import build_index, write_search_script


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
