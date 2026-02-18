"""
Base Parser Interface

All document parsers (RST, Markdown, PDF) inherit from BaseParser
and implement the same interface for consistent usage.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import time
import logging

from .unified_structure import Document

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    """Result of parsing a document."""

    document: Document | None = None
    success: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_ok(self) -> bool:
        """Check if parsing succeeded."""
        return self.success and self.document is not None


class BaseParser(ABC):
    """
    Abstract base class for all document parsers.

    Implementations:
    - RstParser: ReStructuredText documents
    - MarkdownParser: Markdown documents
    - PdfParser: PDF documents
    - HtmlParser: HTML documents (future)
    """

    def __init__(self, options: dict[str, Any] | None = None):
        """
        Initialize parser with options.

        Args:
            options: Parser-specific options
                Common options:
                - include_comments: bool = False
                - extract_metadata: bool = True
                - quality_scoring: bool = True
                - max_file_size_mb: float = 50.0
                - encoding: str = 'utf-8'
        """
        self.options = options or {}
        self._include_comments = self.options.get("include_comments", False)
        self._extract_metadata = self.options.get("extract_metadata", True)
        self._quality_scoring = self.options.get("quality_scoring", True)
        self._max_file_size = self.options.get("max_file_size_mb", 50.0) * 1024 * 1024
        self._encoding = self.options.get("encoding", "utf-8")

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return the format name this parser handles."""
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Return list of supported file extensions."""
        pass

    def can_parse(self, source: str | Path) -> bool:
        """
        Check if this parser can handle the given source.

        Args:
            source: File path or content string

        Returns:
            True if this parser can handle the source
        """
        if isinstance(source, (str, Path)):
            path = Path(source)
            if path.exists() and path.suffix.lower() in self.supported_extensions:
                return True
            # Try content-based detection
            try:
                content = self._read_source(source)
                return self._detect_format(content)
            except Exception:
                return False
        return False

    def parse(self, source: str | Path) -> ParseResult:
        """
        Parse a document from file path or content string.

        Args:
            source: File path (str/Path) or content string

        Returns:
            ParseResult with document or error info
        """
        start_time = time.time()
        result = ParseResult()

        try:
            # Read source
            content, source_path = self._read_source_with_path(source)

            # Check file size
            if len(content.encode(self._encoding)) > self._max_file_size:
                result.errors.append(f"File too large: {source_path}")
                return result

            # Validate format
            if not self._detect_format(content):
                result.warnings.append(f"Content may not be valid {self.format_name}")

            # Parse content
            document = self._parse_content(content, source_path)

            # Post-process
            document = self._post_process(document)

            # Record stats
            processing_time = (time.time() - start_time) * 1000
            if document.stats:
                document.stats.processing_time_ms = processing_time

            result.document = document
            result.success = True
            result.warnings.extend(document.stats.warnings)

        except Exception as e:
            result.errors.append(f"Parse error: {str(e)}")
            logger.exception(f"Error parsing {source}")

        return result

    def parse_file(self, path: str | Path) -> ParseResult:
        """Parse a file from path."""
        return self.parse(path)

    def parse_string(self, content: str, source_path: str = "<string>") -> ParseResult:
        """Parse content from string."""

        # Create a wrapper that looks like a path
        class StringSource:
            def __init__(self, content: str, path: str):
                self._content = content
                self._path = path

            def read_text(self, encoding: str = "utf-8") -> str:
                return self._content

            def exists(self) -> bool:
                return True

            def __str__(self):
                return self._path

        source = StringSource(content, source_path)
        result = self.parse(source)
        if result.document:
            result.document.source_path = source_path
        return result

    @abstractmethod
    def _parse_content(self, content: str, source_path: str) -> Document:
        """
        Parse content string into Document.

        Args:
            content: Raw content to parse
            source_path: Original source path (for reference)

        Returns:
            Parsed Document
        """
        pass

    @abstractmethod
    def _detect_format(self, content: str) -> bool:
        """
        Detect if content matches this parser's format.

        Args:
            content: Content to check

        Returns:
            True if content appears to be this format
        """
        pass

    def _read_source(self, source: str | Path) -> str:
        """Read content from source."""
        content, _ = self._read_source_with_path(source)
        return content

    def _read_source_with_path(self, source: str | Path) -> tuple[str, str]:
        """Read content and return with path."""
        if isinstance(source, str):
            # Check if it's a path or content
            path = Path(source)
            if path.exists():
                return path.read_text(encoding=self._encoding), str(path)
            else:
                # It's content
                return source, "<string>"
        elif isinstance(source, Path):
            return source.read_text(encoding=self._encoding), str(source)
        else:
            # Assume it's a file-like object
            return source.read_text(encoding=self._encoding), str(source)

    def _post_process(self, document: Document) -> Document:
        """
        Post-process document after parsing.

        Override to add cross-references, validate, etc.
        """
        # Build heading list from blocks
        if not document.headings:
            document.headings = self._extract_headings(document)

        # Extract code blocks from blocks
        if not document.code_blocks:
            document.code_blocks = self._extract_code_blocks(document)

        # Extract tables from blocks
        if not document.tables:
            document.tables = self._extract_tables(document)

        # Update stats
        document.stats.total_blocks = len(document.blocks)
        document.stats.code_blocks = len(document.code_blocks)
        document.stats.tables = len(document.tables)
        document.stats.headings = len(document.headings)
        document.stats.cross_references = len(document.internal_links) + len(
            document.external_links
        )

        return document

    def _extract_headings(self, document: Document) -> list:
        """Extract headings from content blocks."""
        from .unified_structure import ContentBlockType

        headings = []
        for block in document.blocks:
            if block.type == ContentBlockType.HEADING:
                heading_data = block.metadata.get("heading_data")
                if heading_data:
                    headings.append(heading_data)
        return headings

    def _extract_code_blocks(self, document: Document) -> list:
        """Extract code blocks from content blocks."""
        code_blocks = []
        for block in document.blocks:
            if block.metadata.get("code_data"):
                code_blocks.append(block.metadata["code_data"])
        return code_blocks

    def _extract_tables(self, document: Document) -> list:
        """Extract tables from content blocks."""
        tables = []
        for block in document.blocks:
            if block.metadata.get("table_data"):
                tables.append(block.metadata["table_data"])
        return tables

    def _create_quality_scorer(self):
        """Create a quality scorer if enabled."""
        if self._quality_scoring:
            from .quality_scorer import QualityScorer

            return QualityScorer()
        return None


def get_parser_for_file(path: str | Path) -> BaseParser | None:
    """
    Get the appropriate parser for a file.

    Args:
        path: File path

    Returns:
        Appropriate parser instance or None
    """
    path = Path(path)
    suffix = path.suffix.lower()

    # Try RST parser
    from .rst_parser import RstParser

    rst_parser = RstParser()
    if suffix in rst_parser.supported_extensions:
        return rst_parser

    # Try Markdown parser
    from .markdown_parser import MarkdownParser

    md_parser = MarkdownParser()
    if suffix in md_parser.supported_extensions:
        return md_parser

    # Could add PDF, HTML parsers here

    return None


def parse_document(source: str | Path, format_hint: str | None = None) -> ParseResult:
    """
    Parse a document, auto-detecting the format.

    Args:
        source: File path or content string
        format_hint: Optional format hint ('rst', 'markdown', etc.)

    Returns:
        ParseResult
    """
    # Use format hint if provided
    if format_hint:
        if format_hint.lower() in ("rst", "rest", "restructuredtext"):
            from .rst_parser import RstParser

            return RstParser().parse(source)
        elif format_hint.lower() in ("md", "markdown"):
            from .markdown_parser import MarkdownParser

            return MarkdownParser().parse(source)

    # Auto-detect from file extension
    parser = get_parser_for_file(source)
    if parser:
        return parser.parse(source)

    # Try content-based detection
    content = source if isinstance(source, str) else Path(source).read_text()

    # Check for RST indicators
    rst_indicators = [".. ", "::\n", ":ref:`", ".. toctree::", ".. code-block::"]
    if any(ind in content for ind in rst_indicators):
        from .rst_parser import RstParser

        return RstParser().parse_string(content)

    # Default to Markdown
    from .markdown_parser import MarkdownParser

    return MarkdownParser().parse_string(content)
