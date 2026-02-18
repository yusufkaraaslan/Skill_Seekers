"""
Enhanced Markdown Parser

Parses Markdown files into unified Document structure.
Supports:
- Headers (# style and underline)
- Code blocks (fenced and indented)
- Tables (GitHub-flavored)
- Lists (bullet and numbered)
- Links and images
- Admonitions/callouts (GitHub-style)
- Frontmatter metadata (YAML)
- Blockquotes
- Horizontal rules

Enhanced with quality scoring and table support.
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
    Image,
    ListType,
)
from .quality_scorer import QualityScorer


class MarkdownParser(BaseParser):
    """
    Parser for Markdown documents.

    Supports standard Markdown and GitHub-flavored Markdown (GFM).
    """

    # Admonition types for GitHub-style callouts
    ADMONITION_TYPES = {
        "note": AdmonitionType.NOTE,
        "warning": AdmonitionType.WARNING,
        "tip": AdmonitionType.TIP,
        "hint": AdmonitionType.HINT,
        "important": AdmonitionType.IMPORTANT,
        "caution": AdmonitionType.CAUTION,
        "danger": AdmonitionType.DANGER,
        "attention": AdmonitionType.ATTENTION,
    }

    def __init__(self, options: dict[str, Any] | None = None):
        super().__init__(options)
        self.quality_scorer = QualityScorer()
        self._lines: list[str] = []
        self._current_line = 0

    @property
    def format_name(self) -> str:
        return "markdown"

    @property
    def supported_extensions(self) -> list[str]:
        return [".md", ".markdown", ".mdown", ".mkd"]

    def _detect_format(self, content: str) -> bool:
        """Detect if content is Markdown."""
        md_indicators = [
            r"^#{1,6}\s+\S",  # ATX headers
            r"^\[.*?\]\(.*?\)",  # Links
            r"^```",  # Code fences
            r"^\|.+\|",  # Tables
            r"^\s*[-*+]\s+\S",  # Lists
            r"^>\s+\S",  # Blockquotes
        ]
        return any(re.search(pattern, content, re.MULTILINE) for pattern in md_indicators)

    def _parse_content(self, content: str, source_path: str) -> Document:
        """Parse Markdown content into Document."""
        self._lines = content.split("\n")
        self._current_line = 0

        document = Document(
            title="",
            format="markdown",
            source_path=source_path,
        )

        # Parse frontmatter if present
        frontmatter = self._parse_frontmatter()
        if frontmatter:
            document.meta.update(frontmatter)

        # Parse content blocks
        while self._current_line < len(self._lines):
            block = self._parse_block()
            if block:
                document.blocks.append(block)
            self._current_line += 1

        # Extract title from first h1 or frontmatter
        if document.meta.get("title"):
            document.title = document.meta["title"]
        else:
            for block in document.blocks:
                if block.type == ContentBlockType.HEADING:
                    heading_data = block.metadata.get("heading_data")
                    if heading_data and heading_data.level == 1:
                        document.title = heading_data.text
                        break

        # Extract specialized content
        self._extract_specialized_content(document)

        return document

    def _parse_frontmatter(self) -> dict | None:
        """Parse YAML frontmatter if present."""
        if self._current_line >= len(self._lines):
            return None

        first_line = self._lines[self._current_line].strip()
        if first_line != "---":
            return None

        # Find closing ---
        end_line = None
        for i in range(self._current_line + 1, len(self._lines)):
            if self._lines[i].strip() == "---":
                end_line = i
                break

        if end_line is None:
            return None

        # Extract frontmatter content
        frontmatter_lines = self._lines[self._current_line + 1 : end_line]
        "\n".join(frontmatter_lines)

        # Simple key: value parsing (not full YAML)
        meta = {}
        current_key = None
        current_value = []

        for line in frontmatter_lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Check for new key
            match = re.match(r"^(\w+):\s*(.*)$", stripped)
            if match:
                # Save previous key
                if current_key:
                    meta[current_key] = "\n".join(current_value).strip()

                current_key = match.group(1)
                value = match.group(2)

                # Handle inline value
                if value:
                    # Check if it's a list
                    if value.startswith("[") and value.endswith("]"):
                        # Parse list
                        items = [item.strip().strip("\"'") for item in value[1:-1].split(",")]
                        meta[current_key] = items
                    else:
                        current_value = [value]
                else:
                    current_value = []
            elif current_key and stripped.startswith("- "):
                # List item
                if current_key not in meta:
                    meta[current_key] = []
                if not isinstance(meta[current_key], list):
                    meta[current_key] = [meta[current_key]]
                meta[current_key].append(stripped[2:].strip().strip("\"'"))
            elif current_key:
                current_value.append(stripped)

        # Save last key
        if current_key:
            meta[current_key] = "\n".join(current_value).strip()

        # Advance past frontmatter
        self._current_line = end_line + 1

        return meta

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

        # Skip HTML comments
        if stripped.startswith("<!--"):
            return self._parse_html_comment()

        # ATX Headers
        if stripped.startswith("#"):
            return self._parse_atx_header()

        # Setext headers (underline style)
        if self._is_setext_header(line):
            return self._parse_setext_header()

        # Code fence
        if stripped.startswith("```"):
            return self._parse_code_fence()

        # Indented code block
        if current.startswith("    ") or current.startswith("\t"):
            return self._parse_indented_code()

        # Table
        if "|" in stripped and self._is_table(line):
            return self._parse_table()

        # Blockquote (check for admonition)
        if stripped.startswith(">"):
            return self._parse_blockquote()

        # Horizontal rule
        if re.match(r"^[\-*_]{3,}\s*$", stripped):
            return self._parse_horizontal_rule()

        # List
        list_type = self._detect_list_type(stripped)
        if list_type:
            return self._parse_list(list_type)

        # Paragraph (default)
        return self._parse_paragraph()

    def _is_setext_header(self, line: int) -> bool:
        """Check if current line is a Setext header."""
        if line + 1 >= len(self._lines):
            return False

        current = self._lines[line].strip()
        next_line = self._lines[line + 1].strip()

        if not current or not next_line:
            return False

        # H1: ===, H2: ---
        return re.match(r"^[=-]+$", next_line) is not None

    def _parse_atx_header(self) -> ContentBlock:
        """Parse ATX style header (# Header)."""
        line = self._lines[self._current_line]
        match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())

        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            # Remove trailing hashes
            text = re.sub(r"\s+#+$", "", text)

            anchor = self._create_anchor(text)

            heading = Heading(
                level=level,
                text=text,
                id=anchor,
                source_line=self._current_line + 1,
            )

            return ContentBlock(
                type=ContentBlockType.HEADING,
                content=text,
                metadata={"heading_data": heading},
                source_line=self._current_line + 1,
            )

        return self._parse_paragraph()

    def _parse_setext_header(self) -> ContentBlock:
        """Parse Setext style header (underline)."""
        text = self._lines[self._current_line].strip()
        underline = self._lines[self._current_line + 1].strip()

        level = 1 if underline[0] == "=" else 2
        anchor = self._create_anchor(text)

        heading = Heading(
            level=level,
            text=text,
            id=anchor,
            source_line=self._current_line + 1,
        )

        # Skip underline
        self._current_line += 1

        return ContentBlock(
            type=ContentBlockType.HEADING,
            content=text,
            metadata={"heading_data": heading},
            source_line=self._current_line,
        )

    def _parse_code_fence(self) -> ContentBlock:
        """Parse fenced code block."""
        line = self._lines[self._current_line]
        match = re.match(r"^```(\w+)?\s*$", line.strip())
        language = match.group(1) if match else None

        start_line = self._current_line
        self._current_line += 1

        code_lines = []
        while self._current_line < len(self._lines):
            current_line = self._lines[self._current_line]
            if current_line.strip() == "```":
                break
            code_lines.append(current_line)
            self._current_line += 1

        code = "\n".join(code_lines)

        # Detect language if not specified
        detected_lang, confidence = self.quality_scorer.detect_language(code)
        if not language and confidence > 0.6:
            language = detected_lang
        elif not language:
            language = "text"

        # Score code quality
        quality = self.quality_scorer.score_code_block(code, language)

        code_block = CodeBlock(
            code=code,
            language=language,
            quality_score=quality,
            confidence=confidence if language == detected_lang else 1.0,
            source_line=start_line + 1,
        )

        return ContentBlock(
            type=ContentBlockType.CODE_BLOCK,
            content=code,
            metadata={
                "code_data": code_block,
                "language": language,
            },
            source_line=start_line + 1,
            quality_score=quality,
        )

    def _parse_indented_code(self) -> ContentBlock:
        """Parse indented code block."""
        code_lines = []
        start_line = self._current_line

        while self._current_line < len(self._lines):
            line = self._lines[self._current_line]
            if not line.strip():
                code_lines.append("")
                self._current_line += 1
                continue

            if line.startswith("    "):
                code_lines.append(line[4:])
            elif line.startswith("\t"):
                code_lines.append(line[1:])
            else:
                self._current_line -= 1
                break

            self._current_line += 1

        code = "\n".join(code_lines).rstrip()

        # Detect language
        detected_lang, confidence = self.quality_scorer.detect_language(code)
        quality = self.quality_scorer.score_code_block(code, detected_lang)

        code_block = CodeBlock(
            code=code,
            language=detected_lang if confidence > 0.6 else "text",
            quality_score=quality,
            confidence=confidence,
            source_line=start_line + 1,
        )

        return ContentBlock(
            type=ContentBlockType.CODE_BLOCK,
            content=code,
            metadata={
                "code_data": code_block,
                "language": detected_lang,
            },
            source_line=start_line + 1,
            quality_score=quality,
        )

    def _is_table(self, line: int) -> bool:
        """Check if current position is a table."""
        if line + 1 >= len(self._lines):
            return False

        current = self._lines[line].strip()
        next_line = self._lines[line + 1].strip()

        # Check for table separator line
        return bool(re.match(r"^[\|:-]+$", next_line) and "|" in current)

    def _parse_table(self) -> ContentBlock:
        """Parse a GFM table."""
        rows = []
        headers = None
        start_line = self._current_line

        # Parse header row
        header_line = self._lines[self._current_line].strip()
        headers = [cell.strip() for cell in header_line.split("|")]
        headers = [h for h in headers if h]  # Remove empty
        self._current_line += 1

        # Skip separator line (|:--:| etc.)
        if self._current_line < len(self._lines):
            self._current_line += 1

        # Parse data rows
        while self._current_line < len(self._lines):
            line = self._lines[self._current_line].strip()

            if not line or "|" not in line:
                self._current_line -= 1
                break

            cells = [cell.strip() for cell in line.split("|")]
            cells = [c for c in cells if c]
            if cells:
                rows.append(cells)

            self._current_line += 1

        table = Table(
            rows=rows,
            headers=headers,
            caption=None,
            source_format="markdown",
            source_line=start_line + 1,
        )

        quality = self.quality_scorer.score_table(table)

        return ContentBlock(
            type=ContentBlockType.TABLE,
            content=f"[Table: {len(rows)} rows]",
            metadata={"table_data": table},
            source_line=start_line + 1,
            quality_score=quality,
        )

    def _parse_blockquote(self) -> ContentBlock:
        """Parse a blockquote, checking for admonitions."""
        lines = []
        start_line = self._current_line
        admonition_type = None
        admonition_content = []

        while self._current_line < len(self._lines):
            line = self._lines[self._current_line]
            stripped = line.strip()

            if not stripped.startswith(">"):
                self._current_line -= 1
                break

            # Remove > prefix
            content = line[1:].strip() if line.startswith("> ") else line[1:].strip()

            # Check for GitHub-style admonition: > [!NOTE]
            admonition_match = re.match(r"^\[!([\w]+)\]\s*(.*)$", content)
            if admonition_match and not admonition_type:
                type_name = admonition_match.group(1).lower()
                admonition_type = self.ADMONITION_TYPES.get(type_name)
                remaining = admonition_match.group(2)
                if remaining:
                    admonition_content.append(remaining)
            elif admonition_type:
                admonition_content.append(content)
            else:
                lines.append(content)

            self._current_line += 1

        # Return as admonition if detected
        if admonition_type:
            return ContentBlock(
                type=ContentBlockType.ADMONITION,
                content="\n".join(admonition_content),
                metadata={"admonition_type": admonition_type},
                source_line=start_line + 1,
            )

        # Regular blockquote
        content = "\n".join(lines)
        return ContentBlock(
            type=ContentBlockType.RAW,
            content=f"> {content}",
            metadata={"block_type": "blockquote"},
            source_line=start_line + 1,
        )

    def _parse_html_comment(self) -> ContentBlock | None:
        """Parse HTML comment (usually skip)."""
        content_lines = []

        while self._current_line < len(self._lines):
            line = self._lines[self._current_line]
            content_lines.append(line)

            if "-->" in line:
                break

            self._current_line += 1

        # Skip comments in output (could optionally include)
        return None

    def _parse_horizontal_rule(self) -> ContentBlock:
        """Parse horizontal rule."""
        return ContentBlock(
            type=ContentBlockType.RAW,
            content="---",
            metadata={"element": "horizontal_rule"},
            source_line=self._current_line + 1,
        )

    def _detect_list_type(self, stripped: str) -> ListType | None:
        """Detect if line starts a list and which type."""
        if re.match(r"^[-*+]\s+", stripped):
            return ListType.BULLET
        if re.match(r"^\d+\.\s+", stripped):
            return ListType.NUMBERED
        return None

    def _parse_list(self, list_type: ListType) -> ContentBlock:
        """Parse a list."""
        items = []
        start_line = self._current_line

        while self._current_line < len(self._lines):
            line = self._lines[self._current_line]
            stripped = line.strip()

            if not stripped:
                self._current_line += 1
                continue

            # Check if still in list
            if list_type == ListType.BULLET:
                match = re.match(r"^[-*+]\s+(.+)$", stripped)
                if not match:
                    self._current_line -= 1
                    break
                items.append(match.group(1))
            else:  # NUMBERED
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
                "list_type": list_type,
                "items": items,
            },
            source_line=start_line + 1,
        )

    def _parse_paragraph(self) -> ContentBlock:
        """Parse a paragraph."""
        lines = []
        start_line = self._current_line

        while self._current_line < len(self._lines):
            line = self._lines[self._current_line]
            stripped = line.strip()

            # End of paragraph
            if not stripped:
                break

            # Check for block-level elements
            if stripped.startswith("#"):
                break
            if stripped.startswith("```"):
                break
            if stripped.startswith(">"):
                break
            if stripped.startswith("---") or stripped.startswith("***"):
                break
            if stripped.startswith("|") and self._is_table(self._current_line):
                break
            if self._detect_list_type(stripped):
                break
            if self._is_setext_header(self._current_line):
                break

            lines.append(stripped)
            self._current_line += 1

        content = " ".join(lines)

        # Process inline elements
        content = self._process_inline(content)

        return ContentBlock(
            type=ContentBlockType.PARAGRAPH,
            content=content,
            source_line=start_line + 1,
        )

    def _process_inline(self, text: str) -> str:
        """Process inline Markdown elements."""
        # Links [text](url)
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"[\1](\2)", text)

        # Images ![alt](url)
        text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"![\1](\2)", text)

        # Code `code`
        text = re.sub(r"`([^`]+)`", r"`\1`", text)

        # Bold **text** or __text__
        text = re.sub(r"\*\*([^*]+)\*\*", r"**\1**", text)
        text = re.sub(r"__([^_]+)__", r"**\1**", text)

        # Italic *text* or _text_
        text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"*\1*", text)
        text = re.sub(r"(?<!_)_([^_]+)_(?!_)", r"*\1*", text)

        # Strikethrough ~~text~~
        text = re.sub(r"~~([^~]+)~~", r"~~\1~~", text)

        return text

    def _create_anchor(self, text: str) -> str:
        """Create URL anchor from heading text."""
        anchor = text.lower()
        anchor = re.sub(r"[^\w\s-]", "", anchor)
        anchor = anchor.replace(" ", "-")
        anchor = re.sub(r"-+", "-", anchor)
        return anchor.strip("-")

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

            # Extract images from paragraphs (simplified)
            elif block.type == ContentBlockType.PARAGRAPH:
                content = block.content
                img_matches = re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", content)
                for alt, src in img_matches:
                    image = Image(
                        source=src,
                        alt_text=alt,
                        source_line=block.source_line,
                    )
                    document.images.append(image)

                # Extract links
                link_matches = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
                for text, url in link_matches:
                    # Determine if internal or external
                    if url.startswith("#"):
                        ref_type = CrossRefType.INTERNAL
                    elif url.startswith("http"):
                        ref_type = CrossRefType.EXTERNAL
                    else:
                        ref_type = CrossRefType.INTERNAL

                    xref = CrossReference(
                        ref_type=ref_type,
                        target=url,
                        text=text,
                        source_line=block.source_line,
                    )

                    if ref_type == CrossRefType.EXTERNAL:
                        document.external_links.append(xref)
                    else:
                        document.internal_links.append(xref)
