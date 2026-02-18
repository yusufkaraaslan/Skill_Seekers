"""
Enhanced RST (ReStructuredText) Parser

Parses RST files into unified Document structure.
Supports all RST constructs including:
- Headers (underline style)
- Code blocks (.. code-block::)
- Tables (simple, grid, list-table)
- Cross-references (:ref:, :class:, :meth:, etc.)
- Directives (note, warning, deprecated, etc.)
- Field lists (:param:, :returns:, :type:, etc.)
- Definition lists
- Substitutions
- Toctree

Optimized for Godot documentation parsing.
"""

import re
from typing import Any

from .base_parser import BaseParser
from .unified_structure import (
    Document,
    ContentBlock,
    ContentBlockType,
    CrossReference,
    CrossRefType,
    AdmonitionType,
    Heading,
    CodeBlock,
    Table,
    Field,
    DefinitionItem,
    Image,
    ListType,
)
from .quality_scorer import QualityScorer


class RstParser(BaseParser):
    """
    Parser for ReStructuredText documents.

    Handles standard RST as well as Godot-specific extensions.
    """

    # RST header underline characters (in order of level)
    HEADER_CHARS = ["=", "-", "~", "^", '"', "'", "`", ":", ".", "_", "*", "+", "#"]

    # Admonition directives
    ADMONITION_DIRECTIVES = {
        "note": AdmonitionType.NOTE,
        "warning": AdmonitionType.WARNING,
        "tip": AdmonitionType.TIP,
        "hint": AdmonitionType.HINT,
        "important": AdmonitionType.IMPORTANT,
        "caution": AdmonitionType.CAUTION,
        "danger": AdmonitionType.DANGER,
        "attention": AdmonitionType.ATTENTION,
        "error": AdmonitionType.ERROR,
        "deprecated": AdmonitionType.DEPRECATED,
        "versionadded": AdmonitionType.VERSIONADDED,
        "versionchanged": AdmonitionType.VERSIONCHANGED,
    }

    # Cross-reference patterns
    CROSS_REF_PATTERNS = [
        (r":ref:`([^`]+)`", CrossRefType.REF),
        (r":doc:`([^`]+)`", CrossRefType.DOC),
        (r":class:`([^`]+)`", CrossRefType.CLASS),
        (r":meth:`([^`]+)`", CrossRefType.METH),
        (r":func:`([^`]+)`", CrossRefType.FUNC),
        (r":attr:`([^`]+)`", CrossRefType.ATTR),
        (r":signal:`([^`]+)`", CrossRefType.SIGNAL),  # Godot
        (r":enum:`([^`]+)`", CrossRefType.ENUM),  # Godot
        (r":mod:`([^`]+)`", CrossRefType.MOD),
        (r":data:`([^`]+)`", CrossRefType.DATA),
        (r":exc:`([^`]+)`", CrossRefType.EXC),
    ]

    # Field list fields (common in docstrings)
    FIELD_NAMES = [
        "param",
        "parameter",
        "arg",
        "argument",
        "type",
        "vartype",
        "types",
        "returns",
        "return",
        "rtype",
        "returntype",
        "raises",
        "raise",
        "except",
        "exception",
        "yields",
        "yield",
        "ytype",
        "seealso",
        "see",
        "note",
        "warning",
        "todo",
        "deprecated",
        "versionadded",
        "versionchanged",
        "args",
        "kwargs",
        "keyword",
        "keywords",
    ]

    def __init__(self, options: dict[str, Any] | None = None):
        super().__init__(options)
        self.quality_scorer = QualityScorer()
        self._current_line = 0
        self._lines: list[str] = []
        self._substitutions: dict[str, str] = {}

    @property
    def format_name(self) -> str:
        return "restructuredtext"

    @property
    def supported_extensions(self) -> list[str]:
        return [".rst", ".rest"]

    def _detect_format(self, content: str) -> bool:
        """Detect if content is RST."""
        rst_indicators = [
            r"\n[=-~^]+\n",  # Underline headers
            r"\.\.\s+\w+::",  # Directives
            r":\w+:`[^`]+`",  # Cross-references
            r"\.\.\s+_`[^`]+`:",  # Targets
        ]
        return any(re.search(pattern, content) for pattern in rst_indicators)

    def _parse_content(self, content: str, source_path: str) -> Document:
        """Parse RST content into Document."""
        self._lines = content.split("\n")
        self._current_line = 0
        self._substitutions = {}

        document = Document(
            title="",
            format="rst",
            source_path=source_path,
        )

        # First pass: collect substitutions
        self._collect_substitutions()

        # Second pass: parse content
        self._current_line = 0
        while self._current_line < len(self._lines):
            block = self._parse_block()
            if block:
                document.blocks.append(block)
            self._current_line += 1

        # Extract title from first heading
        for block in document.blocks:
            if block.type == ContentBlockType.HEADING:
                heading_data = block.metadata.get("heading_data")
                if heading_data:
                    document.title = heading_data.text
                    break

        # Store substitutions
        document.substitutions = self._substitutions.copy()

        # Extract specialized content
        self._extract_specialized_content(document)

        return document

    def _collect_substitutions(self):
        """First pass: collect all substitution definitions."""
        pattern = re.compile(r"^\.\.\s+\|([^|]+)\|\s+replace::\s*(.+)$")
        for i, line in enumerate(self._lines):
            match = pattern.match(line)
            if match:
                name = match.group(1).strip()
                value = match.group(2).strip()
                self._substitutions[name] = value

    def _parse_block(self) -> ContentBlock | None:
        """Parse a single block at current position."""
        line = self._current_line
        if line >= len(self._lines):
            return None

        current = self._lines[line]
        stripped = current.strip()

        # Skip empty lines
        if not stripped:
            return None

        # Skip comments
        if stripped.startswith(".. ") and "::" not in stripped and not stripped.startswith(".. |"):
            # Check if it's a comment
            next_words = stripped[3:].split()
            if (
                not next_words
                or next_words[0] not in self.FIELD_NAMES + list(self.ADMONITION_DIRECTIVES.keys())
            ) and not any(c.isalpha() for c in stripped[3:]):
                return None

        # Header (underline style)
        if self._is_header(line):
            return self._parse_header()

        # Directive
        if stripped.startswith(".. "):
            return self._parse_directive()

        # Definition list
        if self._is_definition_list(line):
            return self._parse_definition_list()

        # Field list
        if self._is_field_list(line):
            return self._parse_field_list()

        # Bullet list
        if stripped.startswith(("- ", "* ", "+ ")):
            return self._parse_bullet_list()

        # Numbered list
        if re.match(r"^\d+\.\s", stripped):
            return self._parse_numbered_list()

        # Paragraph (default)
        return self._parse_paragraph()

    def _is_header(self, line: int) -> bool:
        """Check if current line is a header (has underline)."""
        if line + 1 >= len(self._lines):
            return False

        current = self._lines[line].strip()
        next_line = self._lines[line + 1].strip()

        if not current or not next_line:
            return False

        # Check if next line is all same character and a valid underline char
        if len(set(next_line)) != 1:
            return False

        char = next_line[0]
        if char not in self.HEADER_CHARS:
            return False

        # Underline should be roughly same length as text
        return len(next_line) >= len(current) - 2

    def _parse_header(self) -> ContentBlock:
        """Parse a header with underline."""
        text = self._lines[self._current_line].strip()
        underline = self._lines[self._current_line + 1].strip()

        char = underline[0]
        level = self.HEADER_CHARS.index(char) + 1 if char in self.HEADER_CHARS else 1

        # Create anchor ID
        anchor = text.lower().replace(" ", "-").replace("_", "-")
        anchor = re.sub(r"[^a-z0-9-]", "", anchor)

        heading = Heading(
            level=level,
            text=text,
            id=anchor,
            source_line=self._current_line + 1,
        )

        # Skip the underline line
        self._current_line += 1

        return ContentBlock(
            type=ContentBlockType.HEADING,
            content=text,
            metadata={"heading_data": heading},
            source_line=self._current_line,
        )

    def _parse_directive(self) -> ContentBlock:
        """Parse a directive block."""
        line = self._current_line
        current = self._lines[line].strip()

        # Extract directive name
        match = re.match(r"^\.\.\s+([\w\-]+)::\s*(.*)$", current)
        if not match:
            # Could be a comment or something else
            return self._parse_paragraph()

        directive_name = match.group(1)
        argument = match.group(2)

        # Collect directive content (indented lines)
        content_lines = []
        self._current_line += 1

        while self._current_line < len(self._lines):
            current_line = self._lines[self._current_line]

            # Check for end of directive (non-indented line or new directive)
            if current_line.strip() and not current_line.startswith(" "):
                self._current_line -= 1  # Back up, this line belongs to next block
                break

            # Collect content (remove common indentation)
            if current_line.startswith("   "):
                content_lines.append(current_line[3:])
            elif current_line.startswith("  "):
                content_lines.append(current_line[2:])
            elif current_line.startswith(" "):
                content_lines.append(current_line[1:])
            elif current_line.strip():
                content_lines.append(current_line)
            else:
                content_lines.append("")

            self._current_line += 1

        content = "\n".join(content_lines).strip()

        # Route to specific directive handler
        if directive_name in self.ADMONITION_DIRECTIVES:
            return self._parse_admonition_directive(directive_name, argument, content, line + 1)
        elif directive_name == "code-block":
            return self._parse_code_block_directive(argument, content, line + 1)
        elif directive_name == "table":
            return self._parse_table_directive(argument, content, line + 1)
        elif directive_name == "list-table":
            return self._parse_list_table_directive(argument, content, line + 1)
        elif directive_name == "toctree":
            return self._parse_toctree_directive(content, line + 1)
        elif directive_name == "image" or directive_name == "figure":
            return self._parse_image_directive(argument, content, line + 1)
        elif directive_name == "raw":
            return ContentBlock(
                type=ContentBlockType.RAW,
                content=content,
                metadata={"directive_name": directive_name, "format": argument},
                source_line=line + 1,
            )
        else:
            # Generic directive
            return ContentBlock(
                type=ContentBlockType.DIRECTIVE,
                content=content,
                metadata={"directive_name": directive_name, "argument": argument},
                source_line=line + 1,
            )

    def _parse_admonition_directive(
        self, name: str, argument: str, content: str, line: int
    ) -> ContentBlock:
        """Parse an admonition directive (note, warning, etc.)."""
        admonition_type = self.ADMONITION_DIRECTIVES.get(name, AdmonitionType.NOTE)

        full_content = argument
        if content:
            full_content += "\n" + content if full_content else content

        return ContentBlock(
            type=ContentBlockType.ADMONITION,
            content=full_content,
            metadata={
                "admonition_type": admonition_type,
                "directive_name": name,
            },
            source_line=line,
        )

    def _parse_code_block_directive(self, language: str, content: str, line: int) -> ContentBlock:
        """Parse a code-block directive."""
        lang = language.strip() or "text"

        # Score the code
        quality = self.quality_scorer.score_code_block(content, lang)
        detected_lang, confidence = self.quality_scorer.detect_language(content)

        # Use detected language if none specified and confidence is high
        if lang == "text" and confidence > 0.7:
            lang = detected_lang

        code_block = CodeBlock(
            code=content,
            language=lang,
            quality_score=quality,
            confidence=confidence,
            source_line=line,
        )

        return ContentBlock(
            type=ContentBlockType.CODE_BLOCK,
            content=content,
            metadata={
                "code_data": code_block,
                "language": lang,
            },
            source_line=line,
            quality_score=quality,
        )

    def _parse_table_directive(self, caption: str, content: str, line: int) -> ContentBlock:
        """Parse a table directive (simple or grid table)."""
        # Try to detect table type from content
        if "+--" in content or "+==" in content:
            table = self._parse_grid_table(content, caption, line)
        else:
            table = self._parse_simple_table(content, caption, line)

        quality = self.quality_scorer.score_table(table)

        return ContentBlock(
            type=ContentBlockType.TABLE,
            content=f"[Table: {caption}]" if caption else "[Table]",
            metadata={
                "table_data": table,
            },
            source_line=line,
            quality_score=quality,
        )

    def _parse_simple_table(self, content: str, caption: str | None, line: int) -> Table:
        """Parse a simple RST table (space-separated columns with = or - separators)."""
        lines = content.split("\n")
        rows = []
        headers = None
        separator_indices = []

        # Find separator lines (=== or ---)
        for i, line_text in enumerate(lines):
            stripped = line_text.strip()
            # Match separator lines that contain = or - but no alphanumeric chars
            if (
                stripped
                and re.match(r"^[\s=-]+$", stripped)
                and any(c in stripped for c in "=-")
                and re.search(r"={3,}|-{3,}", stripped)
            ):
                separator_indices.append(i)

        # Determine column boundaries from first separator
        col_boundaries = []
        if separator_indices:
            sep_line = lines[separator_indices[0]]
            # Find transitions between separator chars and spaces
            in_sep = True
            start = 0
            for j, char in enumerate(sep_line):
                if char in "= -":
                    if not in_sep:
                        col_boundaries.append((start, j))
                        in_sep = True
                else:
                    if in_sep:
                        start = j
                        in_sep = False
            if not in_sep:
                col_boundaries.append((start, len(sep_line)))

        # Parse data rows using column boundaries or whitespace splitting
        for i, line_text in enumerate(lines):
            stripped = line_text.strip()

            # Skip separator lines (handle both simple and grid table separators)
            if re.match(r"^[\s=-]+$", stripped) and any(c in stripped for c in "=-"):
                continue

            if not stripped:
                continue

            if "|" in line_text:
                # Pipe-delimited format
                cells = [cell.strip() for cell in line_text.split("|")]
                cells = [c for c in cells if c]
                # Skip if all cells look like separators
                if cells and not all(re.match(r"^[\s=-]+$", c) for c in cells):
                    rows.append(cells)
            elif col_boundaries:
                # Use column boundaries from separator
                cells = []
                for start, end in col_boundaries:
                    if end <= len(line_text):
                        cell = line_text[start:end].strip()
                        cells.append(cell)
                if any(cells):  # At least one non-empty cell
                    rows.append(cells)
            else:
                # Fallback: split by 2+ spaces
                cells = [cell.strip() for cell in re.split(r"\s{2,}", stripped)]
                cells = [c for c in cells if c]
                if cells:
                    rows.append(cells)

        # Determine headers from separator positions
        # In RST simple tables: separator, header, separator, data...
        if separator_indices and rows:
            first_sep = separator_indices[0]

            # Find first row index (first non-separator line after first separator)
            first_row_idx = None
            for i in range(len(lines)):
                if i > first_sep and lines[i].strip():
                    # Check if this is a separator
                    stripped = lines[i].strip()
                    is_sep = bool(
                        re.match(r"^[\s=-]+$", stripped)
                        and any(c in stripped for c in "=-")
                        and re.search(r"={3,}|-{3,}", stripped)
                    )
                    if not is_sep:
                        first_row_idx = i
                        break

            # Check if there's a separator after the first row (indicating header)
            if first_row_idx is not None:
                second_sep = None
                for sep_idx in separator_indices:
                    if sep_idx > first_row_idx:
                        second_sep = sep_idx
                        break

                if second_sep is not None:
                    # First row is headers
                    headers = rows[0]
                    rows = rows[1:]

        return Table(
            rows=rows,
            headers=headers,
            caption=caption,
            source_format="simple",
            source_line=line,
        )

    def _parse_grid_table(self, content: str, caption: str | None, line: int) -> Table:
        """Parse a grid RST table."""
        lines = content.split("\n")
        rows = []
        headers = None
        in_header = False

        for i, line_text in enumerate(lines):
            # Check for header separator (+=...=+)
            if re.match(r"^\+[=+]+\+$", line_text.strip()):
                in_header = True
                continue

            # Check for row separator (+-...-+)
            if re.match(r"^\+[-+]+\+$", line_text.strip()):
                in_header = False
                continue

            # Parse row
            if "|" in line_text:
                cells = []
                parts = line_text.split("|")[1:-1]  # Remove edges
                for part in parts:
                    cell = part.strip()
                    if cell:
                        cells.append(cell)
                if cells:
                    if in_header and headers is None:
                        headers = cells
                    else:
                        rows.append(cells)

        return Table(
            rows=rows,
            headers=headers,
            caption=caption,
            source_format="grid",
            source_line=line,
        )

    def _parse_list_table_directive(self, caption: str, content: str, line: int) -> ContentBlock:
        """Parse a list-table directive."""
        lines = content.split("\n")
        rows = []
        headers = None

        # Check for :header-rows: option
        header_rows = 0
        for line_text in lines:
            match = re.match(r"^:header-rows:\s*(\d+)", line_text.strip())
            if match:
                header_rows = int(match.group(1))
                break

        # Parse rows (lines starting with * )
        current_row = []
        for line_text in lines:
            stripped = line_text.strip()

            # New row
            if re.match(r"^\*\s+-", stripped):
                if current_row:
                    rows.append(current_row)
                current_row = []

            # Cell content
            if stripped.startswith("- "):
                cell = stripped[2:].strip()
                current_row.append(cell)

        if current_row:
            rows.append(current_row)

        # Extract headers
        if header_rows > 0 and rows:
            headers = rows[0]
            rows = rows[header_rows:]

        table = Table(
            rows=rows,
            headers=headers,
            caption=caption,
            source_format="list-table",
            source_line=line,
        )

        quality = self.quality_scorer.score_table(table)

        return ContentBlock(
            type=ContentBlockType.TABLE,
            content=f"[Table: {caption}]" if caption else "[Table]",
            metadata={"table_data": table},
            source_line=line,
            quality_score=quality,
        )

    def _parse_toctree_directive(self, content: str, line: int) -> ContentBlock:
        """Parse a toctree directive."""
        entries = []

        for line_text in content.split("\n"):
            stripped = line_text.strip()
            # Entries are simple lines or :hidden: etc options
            if stripped and not stripped.startswith(":"):
                entries.append(stripped)

        return ContentBlock(
            type=ContentBlockType.TOC_TREE,
            content=f"ToC: {', '.join(entries[:5])}..."
            if len(entries) > 5
            else f"ToC: {', '.join(entries)}",
            metadata={"entries": entries},
            source_line=line,
        )

    def _parse_image_directive(self, argument: str, content: str, line: int) -> ContentBlock:
        """Parse an image or figure directive."""
        # Extract options from content
        alt_text = None
        width = None
        height = None

        for line_text in content.split("\n"):
            stripped = line_text.strip()

            if stripped.startswith(":alt:"):
                alt_text = stripped[5:].strip()
            elif stripped.startswith(":width:"):
                width = stripped[7:].strip()
            elif stripped.startswith(":height:"):
                height = stripped[8:].strip()

        image = Image(
            source=argument,
            alt_text=alt_text,
            width=int(width) if width and width.isdigit() else None,
            height=int(height) if height and height.isdigit() else None,
            source_line=line,
        )

        return ContentBlock(
            type=ContentBlockType.IMAGE,
            content=argument,
            metadata={"image_data": image},
            source_line=line,
        )

    def _is_definition_list(self, line: int) -> bool:
        """Check if current line starts a definition list."""
        if line + 1 >= len(self._lines):
            return False

        current = self._lines[line].strip()
        next_line = self._lines[line + 1].strip()

        # Definition list: term followed by indented definition starting with :
        return next_line.startswith(": ") or (
            next_line and next_line[0].isspace() and ":" in current
        )

    def _parse_definition_list(self) -> ContentBlock:
        """Parse a definition list."""
        items = []
        start_line = self._current_line

        while self._current_line < len(self._lines):
            line = self._lines[self._current_line]
            stripped = line.strip()

            # End of definition list
            if not stripped:
                self._current_line += 1
                continue

            if not line.startswith(" ") and items:
                # New non-indented item, end of list
                self._current_line -= 1
                break

            # Check for term : classifier pattern (RST standard)
            match = re.match(r"^([^:]+)\s+:\s+(.+)$", stripped)
            if match:
                term = match.group(1).strip()
                classifier = match.group(2).strip()

                # Get definition (next indented lines)
                self._current_line += 1
                def_lines = []

                while self._current_line < len(self._lines):
                    def_line = self._lines[self._current_line]
                    if def_line.strip() and not def_line.startswith(" "):
                        break
                    if def_line.startswith("   "):
                        def_lines.append(def_line[3:])
                    elif def_line.startswith("  "):
                        def_lines.append(def_line[2:])
                    elif def_line.startswith(" "):
                        def_lines.append(def_line[1:])
                    self._current_line += 1

                definition = " ".join(def_lines).strip()

                items.append(
                    DefinitionItem(
                        term=term,
                        definition=definition,
                        classifier=classifier,
                        source_line=start_line + 1,
                    )
                )
            else:
                self._current_line += 1

        return ContentBlock(
            type=ContentBlockType.DEFINITION_LIST,
            content=f"{len(items)} definitions",
            metadata={"items": items},
            source_line=start_line + 1,
        )

    def _is_field_list(self, line: int) -> bool:
        """Check if current line starts a field list."""
        current = self._lines[line].strip()

        # Field list: :fieldname: or :fieldname arg:
        return re.match(r"^:(\w+)(\s+\w+)?:", current) is not None

    def _parse_field_list(self) -> ContentBlock:
        """Parse a field list."""
        fields = []
        start_line = self._current_line

        while self._current_line < len(self._lines):
            line = self._lines[self._current_line]
            stripped = line.strip()

            # End of field list
            if not stripped:
                self._current_line += 1
                continue

            if not line.startswith(":") and fields:
                break

            # Parse field
            match = re.match(r"^:(\w+)(?:\s+(\S+))?:(.*)$", stripped)
            if match:
                name = match.group(1)
                arg = match.group(2)
                content = match.group(3).strip()

                # Multi-line content (indented lines following)
                self._current_line += 1
                content_lines = [content] if content else []

                while self._current_line < len(self._lines):
                    cont_line = self._lines[self._current_line]
                    if cont_line.strip() and not cont_line.startswith(" "):
                        break
                    if cont_line.startswith("   "):
                        content_lines.append(cont_line[3:])
                    elif cont_line.startswith("  "):
                        content_lines.append(cont_line[2:])
                    elif cont_line.startswith(" "):
                        content_lines.append(cont_line[1:])
                    self._current_line += 1

                full_content = " ".join(content_lines).strip()

                fields.append(
                    Field(
                        name=name,
                        arg=arg,
                        content=full_content,
                        source_line=start_line + 1,
                    )
                )
            else:
                self._current_line += 1

        # Back up one line if we broke on a non-field
        if self._current_line < len(self._lines) and not self._lines[
            self._current_line
        ].strip().startswith(":"):
            self._current_line -= 1

        return ContentBlock(
            type=ContentBlockType.FIELD_LIST,
            content=f"{len(fields)} fields",
            metadata={"fields": fields},
            source_line=start_line + 1,
        )

    def _parse_bullet_list(self) -> ContentBlock:
        """Parse a bullet list."""
        items = []
        start_line = self._current_line

        while self._current_line < len(self._lines):
            line = self._lines[self._current_line]
            stripped = line.strip()

            if not stripped:
                self._current_line += 1
                continue

            if not stripped.startswith(("- ", "* ", "+ ")):
                self._current_line -= 1
                break

            item_text = stripped[2:]
            items.append(item_text)
            self._current_line += 1

        return ContentBlock(
            type=ContentBlockType.LIST,
            content=f"{len(items)} items",
            metadata={
                "list_type": ListType.BULLET,
                "items": items,
            },
            source_line=start_line + 1,
        )

    def _parse_numbered_list(self) -> ContentBlock:
        """Parse a numbered list."""
        items = []
        start_line = self._current_line

        while self._current_line < len(self._lines):
            line = self._lines[self._current_line]
            stripped = line.strip()

            if not stripped:
                self._current_line += 1
                continue

            match = re.match(r"^\d+\.\s+(.+)$", stripped)
            if not match:
                self._current_line -= 1
                break

            items.append(match.group(1))
            self._current_line += 1

        return ContentBlock(
            type=ContentBlockType.LIST,
            content=f"{len(items)} items",
            metadata={
                "list_type": ListType.NUMBERED,
                "items": items,
            },
            source_line=start_line + 1,
        )

    def _parse_paragraph(self) -> ContentBlock:
        """Parse a paragraph (default block type)."""
        lines = []
        start_line = self._current_line

        while self._current_line < len(self._lines):
            line = self._lines[self._current_line]
            stripped = line.strip()

            # End of paragraph
            if not stripped:
                break

            # Check for special constructs
            if stripped.startswith(".. ") or stripped.startswith(": "):
                break
            if self._is_header(self._current_line):
                break

            lines.append(line)
            self._current_line += 1

        raw_content = " ".join(lines).strip()

        # Extract cross-references from raw content before processing
        xrefs, ext_links = self._extract_xrefs_from_text(raw_content, start_line + 1)

        # Process inline markup
        content = self._process_inline_markup(raw_content)

        block = ContentBlock(
            type=ContentBlockType.PARAGRAPH,
            content=content,
            source_line=start_line + 1,
        )

        # Store extracted references in metadata
        if xrefs or ext_links:
            block.metadata["cross_references"] = xrefs
            block.metadata["external_links"] = ext_links

        return block

    def _process_inline_markup(self, text: str) -> str:
        """Process inline RST markup."""
        # Bold: **text** or *text*
        text = re.sub(r"\*\*([^*]+)\*\*", r"**\1**", text)

        # Italic: *text*
        text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"*\1*", text)

        # Inline code: ``text``
        text = re.sub(r"``([^`]+)``", r"`\1`", text)

        # Links: `text <url>`_ -> [text](url)
        text = re.sub(r"`([^<]+)<([^>]+)>`_", r"[\1](\2)", text)

        # Cross-references: :type:`target` -> [target]
        for pattern, ref_type in self.CROSS_REF_PATTERNS:
            text = re.sub(pattern, r"[\1]", text)

        # Substitutions: |name| -> value
        for name, value in self._substitutions.items():
            text = text.replace(f"|{name}|", value)

        return text

    def _extract_specialized_content(self, document: Document):
        """Extract specialized content lists from blocks."""
        for block in document.blocks:
            # Extract headings
            if block.type == ContentBlockType.HEADING:
                heading_data = block.metadata.get("heading_data")
                if heading_data:
                    document.headings.append(heading_data)

            # Extract code blocks
            elif block.type == ContentBlockType.CODE_BLOCK:
                code_data = block.metadata.get("code_data")
                if code_data:
                    document.code_blocks.append(code_data)

            # Extract tables
            elif block.type == ContentBlockType.TABLE:
                table_data = block.metadata.get("table_data")
                if table_data:
                    document.tables.append(table_data)

            # Extract cross-references from various sources
            elif block.type == ContentBlockType.CROSS_REFERENCE:
                xref_data = block.metadata.get("xref_data")
                if xref_data:
                    if xref_data.ref_type in (CrossRefType.REF, CrossRefType.DOC):
                        document.internal_links.append(xref_data)
                    else:
                        document.external_links.append(xref_data)

            # Extract field lists
            elif block.type == ContentBlockType.FIELD_LIST:
                fields = block.metadata.get("fields", [])
                if fields:
                    document.field_lists.append(fields)

            # Extract definition lists
            elif block.type == ContentBlockType.DEFINITION_LIST:
                items = block.metadata.get("items", [])
                if items:
                    document.definition_lists.append(items)

            # Extract ToC trees
            elif block.type == ContentBlockType.TOC_TREE:
                entries = block.metadata.get("entries", [])
                if entries:
                    document.toc_trees.append(entries)

            # Extract images
            elif block.type == ContentBlockType.IMAGE:
                image_data = block.metadata.get("image_data")
                if image_data:
                    document.images.append(image_data)

            # Extract cross-references and links from paragraphs
            elif block.type == ContentBlockType.PARAGRAPH:
                # Get pre-extracted references from metadata
                xrefs = block.metadata.get("cross_references", [])
                ext_links = block.metadata.get("external_links", [])
                document.internal_links.extend(xrefs)
                document.external_links.extend(ext_links)

    def _extract_xrefs_from_text(self, text: str, source_line: int | None) -> tuple[list, list]:
        """Extract cross-references and links from text."""
        xrefs = []
        external_links = []

        # Extract cross-references (:type:`target`)
        for pattern, ref_type in self.CROSS_REF_PATTERNS:
            for match in re.finditer(pattern, text):
                target = match.group(1)
                xref = CrossReference(
                    ref_type=ref_type,
                    target=target,
                    source_line=source_line,
                )
                xrefs.append(xref)

        # Extract external links (`text <url>`_)
        for match in re.finditer(r"`([^<]+)<([^>]+)>`_", text):
            link_text = match.group(1).strip()
            url = match.group(2).strip()
            xref = CrossReference(
                ref_type=CrossRefType.EXTERNAL,
                target=url,
                text=link_text,
                source_line=source_line,
            )
            external_links.append(xref)

        return xrefs, external_links
