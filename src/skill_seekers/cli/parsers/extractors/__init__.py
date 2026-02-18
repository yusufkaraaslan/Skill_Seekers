"""
Document extractors for unified parsing.

This module provides format-specific parsers that all output
a standardized Document structure.

Usage:
    from skill_seekers.cli.parsers.extractors import RstParser, MarkdownParser

    # Parse RST file
    parser = RstParser()
    result = parser.parse_file("docs/class_node.rst")

    if result.success:
        doc = result.document
        print(f"Title: {doc.title}")
        print(f"Tables: {len(doc.tables)}")
        print(f"Code blocks: {len(doc.code_blocks)}")

        # Convert to markdown
        markdown = doc.to_markdown()

        # Convert to skill format
        skill_data = doc.to_skill_format()

Available Parsers:
    - RstParser: ReStructuredText (.rst, .rest)
    - MarkdownParser: Markdown (.md, .markdown)

Auto-Detection:
    from skill_seekers.cli.parsers.extractors import parse_document

    # Automatically detects format
    result = parse_document("file.rst")
"""

from .unified_structure import (
    ContentBlock,
    ContentBlockType,
    Document,
    CrossRefType,
    AdmonitionType,
    ListType,
    Table,
    CodeBlock,
    Heading,
    Field,
    DefinitionItem,
    Image,
    CrossReference,
    ExtractionStats,
    merge_documents,
)
from .base_parser import BaseParser, ParseResult, get_parser_for_file, parse_document
from .rst_parser import RstParser
from .markdown_parser import MarkdownParser
from .pdf_parser import PdfParser
from .quality_scorer import QualityScorer
from .formatters import MarkdownFormatter, SkillFormatter

__version__ = "1.0.0"

__all__ = [
    # Version
    "__version__",
    # Data structures
    "ContentBlock",
    "ContentBlockType",
    "Document",
    "CrossRefType",
    "AdmonitionType",
    "ListType",
    "Table",
    "CodeBlock",
    "Heading",
    "Field",
    "DefinitionItem",
    "Image",
    "CrossReference",
    "ExtractionStats",
    # Parser base
    "BaseParser",
    "ParseResult",
    # Concrete parsers
    "RstParser",
    "MarkdownParser",
    "PdfParser",
    # Utilities
    "QualityScorer",
    "MarkdownFormatter",
    "SkillFormatter",
    "get_parser_for_file",
    "parse_document",
    "merge_documents",
]
