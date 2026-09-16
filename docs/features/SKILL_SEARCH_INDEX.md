# Skill search index

Skill Seekers can optionally add a lightweight SQLite index to a generated
skill. The index helps an agent find relevant reference sections before reading
large Markdown files in full.

## Enable it

Pass the --index flag to any create command:

    skill-seekers create https://docs.example.com --output output/example --index

For a unified configuration, set the top-level index key:

    {
      "name": "example",
      "index": true,
      "sources": []
    }

The option is off by default. Existing generated skill files remain unchanged
unless it is enabled.

## Generated files

When enabled, Skill Seekers writes scripts/index.db (SQLite metadata and
full-text search index) and scripts/search.py (a self-contained Python 3 query
script). It also adds a short search-first instruction to the generated
SKILL.md. The script uses only Python's standard library, so it does not need a
Skill Seekers installation at use time.

## Query a skill

    python3 scripts/search.py "connect signal" --limit 5
    python3 scripts/search.py "timeout" --category network
    python3 scripts/search.py "authentication token" --json

Results include a file#anchor pointer, a relevance score, and a short snippet.
Read the returned sections only after confirming that they apply to the task.

The indexer splits rendered references/*.md files at headings. It stores stable
metadata for each section (file, heading, anchor, category, kind, and
code_langs) plus searchable heading and content text. Files are processed in
sorted order; compare table rows rather than raw SQLite bytes when checking
reproducibility across different SQLite versions.

## Compatibility

The indexer prefers SQLite FTS5 and ranks matches with BM25. Python builds
without FTS5 still generate an index and use deterministic LIKE matching in the
query script. Vector-database targets continue to use their existing retrieval
paths.
