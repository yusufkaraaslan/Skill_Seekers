"""
Unified Document Structure

This module defines the standardized document model that all parsers output.
Whether parsing RST, Markdown, PDF, or HTML, the result is a Document object
with a consistent structure.
"""

from dataclasses import dataclass, field
from typing import Any
from enum import Enum


class ContentBlockType(Enum):
    """Standardized content block types across all formats."""

    HEADING = "heading"
    PARAGRAPH = "paragraph"
    CODE_BLOCK = "code_block"
    TABLE = "table"
    LIST = "list"
    IMAGE = "image"
    CROSS_REFERENCE = "cross_reference"
    DIRECTIVE = "directive"
    FIELD_LIST = "field_list"
    DEFINITION_LIST = "definition_list"
    ADMONITION = "admonition"  # notes, warnings, tips, etc.
    META = "meta"  # metadata fields
    SUBSTITUTION = "substitution"  # RST |variable|
    TOC_TREE = "toc_tree"  # RST .. toctree::
    COMMENT = "comment"  # Comments (usually filtered out)
    RAW = "raw"  # Raw content that doesn't fit other types


class CrossRefType(Enum):
    """Types of cross-references (mainly RST but useful for others)."""

    REF = "ref"  # :ref:`label`
    DOC = "doc"  # :doc:`path`
    CLASS = "class"  # :class:`ClassName`
    METH = "meth"  # :meth:`method_name`
    FUNC = "func"  # :func:`function_name`
    ATTR = "attr"  # :attr:`attribute_name`
    SIGNAL = "signal"  # Godot-specific: :signal:`signal_name`
    ENUM = "enum"  # Godot-specific: :enum:`EnumName`
    MOD = "mod"  # :mod:`module_name`
    DATA = "data"  # :data:`data_name`
    EXC = "exc"  # :exc:`ExceptionName`
    INTERNAL = "internal"  # Internal link (#anchor)
    EXTERNAL = "external"  # External URL


class AdmonitionType(Enum):
    """Types of admonitions/callouts."""

    NOTE = "note"
    WARNING = "warning"
    TIP = "tip"
    IMPORTANT = "important"
    CAUTION = "caution"
    DANGER = "danger"
    ATTENTION = "attention"
    HINT = "hint"
    ERROR = "error"
    DEPRECATED = "deprecated"  # RST-specific
    VERSIONADDED = "versionadded"  # RST-specific
    VERSIONCHANGED = "versionchanged"  # RST-specific


class ListType(Enum):
    """Types of lists."""

    BULLET = "bullet"
    NUMBERED = "numbered"
    DEFINITION = "definition"  # Term/definition pairs


@dataclass
class Heading:
    """A document heading/section title."""

    level: int  # 1-6 for h1-h6, or 1+ for RST underline levels
    text: str
    id: str | None = None  # Anchor ID
    source_line: int | None = None


@dataclass
class CodeBlock:
    """A code block with metadata."""

    code: str
    language: str | None = None
    quality_score: float | None = None  # 0-10
    confidence: float | None = None  # Language detection confidence
    is_valid: bool | None = None  # Syntax validation result
    validation_issues: list[str] = field(default_factory=list)
    source_line: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Table:
    """A table with rows and cells."""

    rows: list[list[str]]  # 2D array of cell content
    headers: list[str] | None = None
    caption: str | None = None
    col_widths: list[int] | None = None
    source_format: str = "unknown"  # 'simple', 'grid', 'list-table', 'markdown', 'pdf'
    source_line: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def num_rows(self) -> int:
        return len(self.rows)

    @property
    def num_cols(self) -> int:
        if self.rows:
            return max(len(row) for row in self.rows)
        return 0


@dataclass
class CrossReference:
    """A cross-reference link."""

    ref_type: CrossRefType
    target: str  # Target ID, URL, or path
    text: str | None = None  # Display text (if different from target)
    source_line: int | None = None
    resolved: bool = False  # Whether target was resolved


@dataclass
class Field:
    """A field in a field list (RST :param:, :returns:, etc.)."""

    name: str  # Field name (e.g., 'param', 'returns', 'type')
    arg: str | None = None  # Field argument (e.g., parameter name)
    content: str = ""  # Field content
    source_line: int | None = None


@dataclass
class DefinitionItem:
    """A definition list item (term + definition)."""

    term: str
    definition: str
    classifier: str | None = None  # RST classifier (term : classifier)
    source_line: int | None = None


@dataclass
class Image:
    """An image reference or embedded image."""

    source: str  # URL, path, or base64 data
    alt_text: str | None = None
    width: int | None = None
    height: int | None = None
    is_embedded: bool = False  # True if data is embedded
    source_line: int | None = None


@dataclass
class ContentBlock:
    """Universal content block - used by ALL parsers."""

    type: ContentBlockType
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    source_line: int | None = None
    quality_score: float | None = None  # 0-10

    # Type-specific data (stored in metadata for flexibility)
    # For CODE_BLOCK: 'code_data' -> CodeBlock
    # For TABLE: 'table_data' -> Table
    # For CROSS_REFERENCE: 'xref_data' -> CrossReference
    # For ADMONITION: 'admonition_type' -> AdmonitionType
    # For LIST: 'list_type' -> ListType, 'items' -> list
    # For HEADING: 'heading_data' -> Heading
    # For IMAGE: 'image_data' -> Image


@dataclass
class ExtractionStats:
    """Statistics about document extraction."""

    total_blocks: int = 0
    code_blocks: int = 0
    tables: int = 0
    headings: int = 0
    cross_references: int = 0
    images: int = 0
    warnings: list[str] = field(default_factory=list)
    processing_time_ms: float | None = None


@dataclass
class Document:
    """
    Unified document structure - output of ALL parsers.

    This class provides a standardized representation of document content
    regardless of the source format (RST, Markdown, PDF, HTML).
    """

    title: str = ""
    format: str = ""  # 'markdown', 'rst', 'pdf', 'html', 'unknown'
    source_path: str = ""

    # Core content as blocks
    blocks: list[ContentBlock] = field(default_factory=list)

    # Navigation/Structure (derived from blocks for convenience)
    headings: list[Heading] = field(default_factory=list)
    sections: list[dict] = field(default_factory=list)  # Hierarchical structure

    # References
    internal_links: list[CrossReference] = field(default_factory=list)
    external_links: list[CrossReference] = field(default_factory=list)

    # Specialized content (also in blocks, but extracted for easy access)
    code_blocks: list[CodeBlock] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    images: list[Image] = field(default_factory=list)

    # RST-specific (may be empty for other formats)
    field_lists: list[list[Field]] = field(default_factory=list)
    definition_lists: list[list[DefinitionItem]] = field(default_factory=list)
    substitutions: dict[str, str] = field(default_factory=dict)
    toc_trees: list[list[str]] = field(default_factory=list)

    # Metadata
    meta: dict[str, Any] = field(default_factory=dict)

    # Extraction info
    stats: ExtractionStats = field(default_factory=ExtractionStats)

    def to_markdown(self, options: dict | None = None) -> str:
        """
        Convert unified structure to markdown output.

        Args:
            options: Optional formatting options
                - include_toc: bool = False
                - max_heading_level: int = 6
                - code_block_style: str = 'fenced'  # or 'indented'
                - table_style: str = 'github'  # or 'simple'

        Returns:
            Markdown-formatted string
        """
        from .formatters import MarkdownFormatter

        formatter = MarkdownFormatter(options or {})
        return formatter.format(self)

    def to_skill_format(self) -> dict[str, Any]:
        """
        Convert to skill-seekers internal format.

        Returns:
            Dictionary compatible with existing skill-seekers pipelines
        """
        return {
            "title": self.title,
            "source_path": self.source_path,
            "format": self.format,
            "content": self._extract_content_text(),
            "headings": [{"level": h.level, "text": h.text, "id": h.id} for h in self.headings],
            "code_samples": [
                {
                    "code": cb.code,
                    "language": cb.language,
                    "quality_score": cb.quality_score,
                }
                for cb in self.code_blocks
            ],
            "tables": [
                {
                    "headers": t.headers,
                    "rows": t.rows,
                    "caption": t.caption,
                }
                for t in self.tables
            ],
            "cross_references": [
                {
                    "type": xr.ref_type.value,
                    "target": xr.target,
                    "text": xr.text,
                }
                for xr in self.internal_links + self.external_links
            ],
            "meta": self.meta,
            "stats": {
                "total_blocks": self.stats.total_blocks,
                "code_blocks": self.stats.code_blocks,
                "tables": self.stats.tables,
                "headings": self.stats.headings,
            },
        }

    def _extract_content_text(self) -> str:
        """Extract plain text content from paragraphs."""
        paragraphs = []
        for block in self.blocks:
            if block.type == ContentBlockType.PARAGRAPH:
                paragraphs.append(block.content)
        return "\n\n".join(paragraphs)

    def get_section_content(self, heading_text: str) -> list[ContentBlock]:
        """
        Get all content blocks under a specific section heading.

        Args:
            heading_text: The section heading to find

        Returns:
            List of ContentBlock objects in that section
        """
        result = []
        in_section = False
        section_level = None

        for block in self.blocks:
            if block.type == ContentBlockType.HEADING:
                heading_data = block.metadata.get("heading_data")
                if heading_data and heading_data.text == heading_text:
                    in_section = True
                    section_level = heading_data.level
                    continue
                elif in_section and heading_data.level <= section_level:
                    # New section at same or higher level
                    break

            if in_section:
                result.append(block)

        return result

    def find_blocks_by_type(self, block_type: ContentBlockType) -> list[ContentBlock]:
        """Find all blocks of a specific type."""
        return [b for b in self.blocks if b.type == block_type]

    def find_code_by_language(self, language: str) -> list[CodeBlock]:
        """Find all code blocks in a specific language."""
        return [cb for cb in self.code_blocks if cb.language == language]

    def find_tables_by_caption(self, pattern: str) -> list[Table]:
        """Find tables with captions matching a pattern."""
        import re

        return [t for t in self.tables if t.caption and re.search(pattern, t.caption, re.I)]

    def get_api_summary(self) -> dict[str, Any]:
        """
        Extract API summary if this is API documentation.

        Returns:
            Dictionary with 'properties', 'methods', 'signals', etc.
        """
        # Look for tables with specific captions (Godot-style)
        properties_table = None
        methods_table = None
        signals_table = None

        for table in self.tables:
            if table.caption:
                cap_lower = table.caption.lower()
                if "property" in cap_lower:
                    properties_table = table
                elif "method" in cap_lower:
                    methods_table = table
                elif "signal" in cap_lower:
                    signals_table = table

        return {
            "properties": self._parse_api_table(properties_table) if properties_table else [],
            "methods": self._parse_api_table(methods_table) if methods_table else [],
            "signals": self._parse_api_table(signals_table) if signals_table else [],
        }

    def _parse_api_table(self, table: Table | None) -> list[dict]:
        """Parse an API table into structured data."""
        if not table or not table.rows:
            return []

        results = []
        headers = table.headers or []

        for row in table.rows:
            if len(row) >= 2:
                item = {"name": row[0]}
                for i, header in enumerate(headers[1:], 1):
                    if i < len(row):
                        item[header.lower().replace(" ", "_")] = row[i]
                results.append(item)

        return results


def merge_documents(docs: list[Document]) -> Document:
    """
    Merge multiple documents into one.

    Useful for combining multiple source files into a single skill.
    """
    if not docs:
        return Document()

    merged = Document(
        title=docs[0].title,
        format=docs[0].format,
        source_path="merged",
    )

    for doc in docs:
        merged.blocks.extend(doc.blocks)
        merged.headings.extend(doc.headings)
        merged.internal_links.extend(doc.internal_links)
        merged.external_links.extend(doc.external_links)
        merged.code_blocks.extend(doc.code_blocks)
        merged.tables.extend(doc.tables)
        merged.images.extend(doc.images)
        merged.field_lists.extend(doc.field_lists)
        merged.definition_lists.extend(doc.definition_lists)
        merged.toc_trees.extend(doc.toc_trees)
        merged.meta.update(doc.meta)

    # Merge stats
    merged.stats.total_blocks = sum(d.stats.total_blocks for d in docs)
    merged.stats.code_blocks = sum(d.stats.code_blocks for d in docs)
    merged.stats.tables = sum(d.stats.tables for d in docs)
    merged.stats.headings = sum(d.stats.headings for d in docs)
    merged.stats.cross_references = sum(d.stats.cross_references for d in docs)

    return merged
