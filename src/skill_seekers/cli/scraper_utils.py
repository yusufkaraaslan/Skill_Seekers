"""
Shared helpers for the source-type scrapers.

Single home for small utilities that were copy-pasted across many
``*_scraper.py`` modules:

- ``score_code_quality``: a 0-10 heuristic for code blocks. Six scrapers had a
  byte-identical version and asciidoc a formatting-only variant; jupyter added
  notebook-specific rules (docstring/magic-line bonuses, all-magic penalty),
  now gated behind ``notebook_mode``.
- ``extract_table_from_html``: pull headers/rows from a BeautifulSoup ``<table>``
  (was byte-identical in the word and epub scrapers).
- ``reference_filename``: basename for a category's reference .md file (was
  near-identical in the word/pdf/epub/html/pptx/asciidoc/jupyter scrapers).
"""

import re


def reference_filename(
    pages: list[dict],
    section_num: int,
    total_sections: int,
    base_stem: str = "",
    *,
    number_key: str = "section_number",
    prefix: str = "s",
) -> str:
    """Basename of a category's reference file — the single source of truth
    shared by the file writer, index.md, and the SKILL.md nav, so the links
    can't drift from the actual filenames (DOC-07).

    Args:
        pages: The category's page/section dicts.
        section_num: 1-based category index (used for the empty fallback).
        total_sections: Total number of categories being written.
        base_stem: Source-file stem (e.g. ``Path(self.docx_path).stem``).
        number_key: Dict key holding each page's number (pdf uses
            ``"page_number"``; everything else ``"section_number"``).
        prefix: Range prefix in the filename (pdf uses ``"p"``).
    """
    if not pages:
        return f"section_{section_num:02d}.md"
    nums = [p.get(number_key, i + 1) for i, p in enumerate(pages)]
    if total_sections == 1:
        return f"{base_stem}.md" if base_stem else "main.md"
    base_name = base_stem or "section"
    return f"{base_name}_{prefix}{min(nums)}-{prefix}{max(nums)}.md"


def parse_leading_int(value, default: int = 0) -> int:
    """Parse the leading integer from a dimension-ish value, defensively.

    HTML/EPUB/Word width/height attributes can be ``"100%"``, ``"50px"``,
    ``""`` or ``None``; a bare ``int("100%")`` raises ``ValueError`` (crashing
    image extraction) or silently drops the image. Returns the leading integer
    (``"100%"`` -> 100, ``"50px"`` -> 50) or ``default`` when there's none
    (``"auto"``/``""``/``None`` -> ``default``).
    """
    if value is None:
        return default
    match = re.match(r"\s*(-?\d+)", str(value))
    return int(match.group(1)) if match else default


def score_code_quality(code: str, *, notebook_mode: bool = False) -> float:
    """Heuristic quality score for a code block (0.0-10.0).

    Scores on line count, definitions, imports, indentation and operators;
    short snippets are penalized. With ``notebook_mode=True`` (Jupyter), also
    rewards docstrings and ``%`` magic lines, and penalizes cells that are
    entirely ``%``/``!`` magic/shell lines.

    Args:
        code: Source code string.
        notebook_mode: Enable Jupyter-notebook-specific scoring rules.

    Returns:
        Quality score between 0.0 and 10.0.
    """
    if not code:
        return 0.0

    score = 5.0
    lines = code.strip().split("\n")
    line_count = len(lines)

    # More lines = more substantial
    if line_count >= 10:
        score += 2.0
    elif line_count >= 5:
        score += 1.0

    # Has function/class definitions
    if re.search(r"\b(def |class |function |func |fn )", code):
        score += 1.5

    # Has imports/require
    if re.search(r"\b(import |from .+ import|require\(|#include|using )", code):
        score += 0.5

    # Has indentation (structured code)
    if re.search(r"^    ", code, re.MULTILINE):
        score += 0.5

    # Has assignment, operators, or common code syntax
    if re.search(r"[=:{}()\[\]]", code):
        score += 0.3

    if notebook_mode:
        # Has a docstring
        if re.search(r'""".*?"""|\'\'\'.*?\'\'\'', code, re.DOTALL):
            score += 0.3
        # Has a magic line
        if re.search(r"^%", code, re.MULTILINE):
            score += 0.2

    # Very short snippets get penalized
    if len(code) < 30:
        score -= 2.0

    if notebook_mode:
        # Penalize cells that are entirely magic/shell commands
        non_magic = [ln for ln in lines if ln.strip() and not ln.strip().startswith(("%", "!"))]
        if line_count > 0 and not non_magic:
            score -= 1.0

    return min(10.0, max(0.0, score))


def extract_table_from_html(table_elem) -> dict | None:
    """Extract headers and rows from a BeautifulSoup <table> element."""
    headers = []
    rows = []

    # Try <thead> first for headers
    thead = table_elem.find("thead")
    if thead:
        header_row = thead.find("tr")
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]

    # Body rows. Prefer an explicit <tbody>; otherwise take rows directly under
    # the table but skip any that belong to <thead> — skipping STRUCTURALLY, not
    # by value, so a legitimate body row that merely duplicates the header text
    # isn't dropped.
    tbody = table_elem.find("tbody")
    if tbody is not None:
        body_rows = tbody.find_all("tr")
    else:
        body_rows = [r for r in table_elem.find_all("tr") if r.find_parent("thead") is None]
    for row in body_rows:
        cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
        if cells:
            rows.append(cells)

    # If no explicit thead, use first row as header
    if not headers and rows:
        headers = rows.pop(0)

    if not headers and not rows:
        return None

    return {"headers": headers, "rows": rows}
