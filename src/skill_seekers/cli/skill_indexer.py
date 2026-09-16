"""Build a lightweight, portable search index for generated skills.

The generated query script deliberately depends only on :mod:`sqlite3`, so an
agent can search a skill without having Skill Seekers installed.  The feature
is opt-in because SQLite database bytes are not stable across SQLite versions.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import sqlite3
from pathlib import Path


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)(?:\s+#+)?\s*$", re.MULTILINE)
_CODE_FENCE_RE = re.compile(r"^```([^\s`]*)", re.MULTILINE)


@dataclass(frozen=True)
class IndexBuildResult:
    """Stable facts about one completed index build."""

    index_path: Path
    section_count: int
    fts_enabled: bool


def build_index(skill_dir: Path) -> IndexBuildResult:
    """Build ``scripts/index.db`` from the skill's rendered references.

    Reference files are processed in sorted order and sections retain their
    source order.  Consumers needing reproducibility should compare table rows,
    not raw database bytes, because SQLite file layout varies by library build.
    """
    skill_dir = Path(skill_dir)
    references_dir = skill_dir / "references"
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    index_path = scripts_dir / "index.db"

    if index_path.exists():
        index_path.unlink()

    connection = sqlite3.connect(index_path)
    try:
        _create_schema(connection)
        fts_enabled = _create_fts_table(connection)
        section_count = 0
        if references_dir.exists():
            for reference_path in sorted(references_dir.rglob("*.md")):
                relative_path = reference_path.relative_to(skill_dir).as_posix()
                text = reference_path.read_text(encoding="utf-8", errors="replace")
                for section in _split_sections(relative_path, text):
                    cursor = connection.execute(
                        """
                        INSERT INTO sections(file, heading, anchor, category, kind, code_langs)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            section.file,
                            section.heading,
                            section.anchor,
                            section.category,
                            section.kind,
                            section.code_langs,
                        ),
                    )
                    section_id = cursor.lastrowid
                    connection.execute(
                        "INSERT INTO section_content(id, heading, content) VALUES (?, ?, ?)",
                        (section_id, section.heading, section.content),
                    )
                    if fts_enabled:
                        connection.execute(
                            "INSERT INTO sections_fts(rowid, heading, content) VALUES (?, ?, ?)",
                            (section_id, section.heading, section.content),
                        )
                    section_count += 1
        connection.commit()
    finally:
        connection.close()

    return IndexBuildResult(index_path, section_count, fts_enabled)


def append_search_instruction(skill_dir: Path) -> None:
    """Append the opt-in search-first guidance to a generated ``SKILL.md``."""
    skill_path = Path(skill_dir) / "SKILL.md"
    if not skill_path.exists():
        return

    instruction = (
        "\n\n## Search reference documentation\n\n"
        "Before reading a reference file wholesale, search the generated index for "
        "confirmed hits:\n\n"
        '```bash\npython3 scripts/search.py "your query" --limit 5\n```\n\n'
        "Read only the returned `file#anchor` sections that apply to the task. "
        "Use `--category` to narrow results or `--json` for machine-readable output.\n"
    )
    content = skill_path.read_text(encoding="utf-8")
    if "## Search reference documentation" not in content:
        skill_path.write_text(content.rstrip() + instruction, encoding="utf-8")


def write_search_script(skill_dir: Path) -> Path:
    """Write the self-contained, stdlib-only query script into ``scripts/``."""
    skill_dir = Path(skill_dir)
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    script_path = scripts_dir / "search.py"
    script_path.write_text(_SEARCH_SCRIPT, encoding="utf-8")
    append_search_instruction(skill_dir)
    return script_path


def _create_schema(connection: sqlite3.Connection) -> None:
    """Create stable metadata and content tables used by both search modes."""
    connection.executescript(
        """
        CREATE TABLE sections (
            id INTEGER PRIMARY KEY,
            file TEXT NOT NULL,
            heading TEXT NOT NULL,
            anchor TEXT NOT NULL,
            category TEXT NOT NULL,
            kind TEXT NOT NULL,
            code_langs TEXT NOT NULL
        );
        CREATE TABLE section_content (
            id INTEGER PRIMARY KEY REFERENCES sections(id),
            heading TEXT NOT NULL,
            content TEXT NOT NULL
        );
        """
    )


def _create_fts_table(connection: sqlite3.Connection) -> bool:
    """Create the FTS5 table, retaining portable ``LIKE`` search if unavailable."""
    try:
        connection.execute("CREATE VIRTUAL TABLE sections_fts USING fts5(heading, content)")
    except sqlite3.OperationalError:
        return False
    return True


@dataclass(frozen=True)
class _Section:
    file: str
    heading: str
    anchor: str
    category: str
    kind: str
    code_langs: str
    content: str


def _split_sections(relative_path: str, text: str) -> list[_Section]:
    """Split one rendered markdown file on headings and preserve valid anchors."""
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return []

    reference_path = Path(relative_path).relative_to("references")
    category = reference_path.parent.as_posix() if reference_path.parent != Path(".") else "general"
    kind = Path(relative_path).stem
    seen_anchors: dict[str, int] = {}
    sections: list[_Section] = []
    for index, match in enumerate(matches):
        heading = match.group(2).strip()
        base_anchor = _anchor_for(heading)
        count = seen_anchors.get(base_anchor, 0)
        seen_anchors[base_anchor] = count + 1
        anchor = base_anchor if count == 0 else f"{base_anchor}-{count}"
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        content = text[match.start() : end].strip()
        languages = sorted(
            {language.lower() for language in _CODE_FENCE_RE.findall(content) if language}
        )
        sections.append(
            _Section(
                file=relative_path,
                heading=heading,
                anchor=anchor,
                category=category,
                kind=kind,
                code_langs=",".join(languages),
                content=content,
            )
        )
    return sections


def _anchor_for(heading: str) -> str:
    """Return a GitHub-compatible anchor for ordinary generated headings."""
    normalized = heading.strip().lower()
    normalized = re.sub(r"[^\w\s-]", "", normalized, flags=re.UNICODE)
    normalized = re.sub(r"[\s-]+", "-", normalized, flags=re.UNICODE)
    return normalized.strip("-") or "section"


_SEARCH_SCRIPT = r'''#!/usr/bin/env python3
"""Search the generated Skill Seekers reference index with Python's stdlib."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search indexed skill reference markdown")
    parser.add_argument("query", help="Words to search for")
    parser.add_argument("--category", help="Restrict results to a reference directory")
    parser.add_argument("--limit", type=int, default=5, help="Maximum results (default: 5)")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON results")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limit < 1:
        print("--limit must be at least 1", file=sys.stderr)
        return 2

    database = Path(__file__).with_name("index.db")
    if not database.exists():
        print("Search index not found. Rebuild this skill with --index.", file=sys.stderr)
        return 1

    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        results = search(connection, args.query, args.category, args.limit)
    finally:
        connection.close()

    if args.as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0
    for result in results:
        print(f"{result['file']}#{result['anchor']}  (score {result['score']:.2f})")
        print(f"  {result['snippet']}")
    return 0


def search(connection: sqlite3.Connection, query: str, category: str | None, limit: int) -> list[dict]:
    tokens = re.findall(r"[\w]+", query, flags=re.UNICODE)
    if not tokens:
        return []
    try:
        return _fts_search(connection, tokens, category, limit)
    except sqlite3.OperationalError:
        return _like_search(connection, tokens, category, limit)


def _fts_search(connection: sqlite3.Connection, tokens: list[str], category: str | None, limit: int) -> list[dict]:
    match_query = " AND ".join(tokens)
    category_clause = " AND sections.category = ?" if category else ""
    parameters: list[object] = [match_query]
    if category:
        parameters.append(category)
    parameters.append(limit)
    rows = connection.execute(
        f"""
        SELECT sections.file, sections.anchor, sections.heading, sections.category,
               -bm25(sections_fts) AS score,
               snippet(sections_fts, 1, '[', ']', '…', 16) AS snippet
        FROM sections_fts
        JOIN sections ON sections.id = sections_fts.rowid
        WHERE sections_fts MATCH ?{category_clause}
        ORDER BY score DESC, sections.file, sections.id
        LIMIT ?
        """,
        parameters,
    ).fetchall()
    return [dict(row) for row in rows]


def _like_search(connection: sqlite3.Connection, tokens: list[str], category: str | None, limit: int) -> list[dict]:
    clauses = " AND ".join("lower(section_content.content) LIKE ?" for _ in tokens)
    parameters: list[object] = [f"%{token.lower()}%" for token in tokens]
    if category:
        clauses += " AND sections.category = ?"
        parameters.append(category)
    rows = connection.execute(
        f"""
        SELECT sections.file, sections.anchor, sections.heading, sections.category,
               section_content.content
        FROM sections
        JOIN section_content ON section_content.id = sections.id
        WHERE {clauses}
        ORDER BY sections.file, sections.id
        """,
        parameters,
    ).fetchall()
    results = []
    for row in rows:
        content = row["content"]
        score = sum(content.lower().count(token.lower()) for token in tokens)
        results.append({
            "file": row["file"],
            "anchor": row["anchor"],
            "heading": row["heading"],
            "category": row["category"],
            "score": float(score),
            "snippet": _snippet(content, tokens),
        })
    return sorted(results, key=lambda result: (-result["score"], result["file"], result["anchor"]))[:limit]


def _snippet(content: str, tokens: list[str]) -> str:
    match = re.search("|".join(re.escape(token) for token in tokens), content, flags=re.IGNORECASE)
    start = max(0, (match.start() if match else 0) - 60)
    excerpt = " ".join(content[start : start + 180].split())
    return re.sub("(" + "|".join(re.escape(token) for token in tokens) + ")", r"[\1]", excerpt, flags=re.IGNORECASE)


if __name__ == "__main__":
    raise SystemExit(main())
'''
