"""
PDF Parser for Unified Document Structure

Wraps PDFExtractor to provide unified Document output.
"""

from pathlib import Path
from typing import Any

from .base_parser import BaseParser, ParseResult
from .quality_scorer import QualityScorer
from .unified_structure import (
    CodeBlock,
    ContentBlock,
    ContentBlockType,
    Document,
    Heading,
    Image,
    Table,
)

# Import PDFExtractor
try:
    from skill_seekers.cli.pdf_extractor_poc import PDFExtractor
except ImportError:
    # Fallback for relative import
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from pdf_extractor_poc import PDFExtractor


class PdfParser(BaseParser):
    """
    Parser for PDF documents.

    Wraps the existing PDFExtractor to provide unified Document output
    while maintaining all PDF-specific features (OCR, image extraction,
    table extraction, etc.).
    """

    def __init__(self, options: dict[str, Any] | None = None):
        super().__init__(options)
        self.pdf_options = {
            "verbose": self.options.get("verbose", False),
            "chunk_size": self.options.get("chunk_size", 10),
            "min_quality": self.options.get("min_quality", 0.0),
            "extract_images": self.options.get("extract_images", False),
            "image_dir": self.options.get("image_dir"),
            "min_image_size": self.options.get("min_image_size", 100),
            "use_ocr": self.options.get("use_ocr", False),
            "password": self.options.get("password"),
            "extract_tables": self.options.get("extract_tables", True),
            "parallel": self.options.get("parallel", False),
            "max_workers": self.options.get("max_workers"),
        }
        self.quality_scorer = QualityScorer()

    @property
    def format_name(self) -> str:
        return "pdf"

    @property
    def supported_extensions(self) -> list[str]:
        return [".pdf"]

    def _detect_format(self, content: str) -> bool:
        """Detect if content is PDF (by checking for PDF header)."""
        return content.startswith("%PDF")

    def _parse_content(self, content: str, source_path: str) -> Document:
        """
        Parse PDF content into Document.

        Note: For PDF, we need the file path, not content string.
        This method is mainly for API compatibility.
        """
        # For PDF, we need to use parse_file
        raise NotImplementedError("PDF parsing requires file path. Use parse_file() instead.")

    def parse_file(self, path: str | Path) -> ParseResult:
        """
        Parse a PDF file.

        Args:
            path: Path to PDF file

        Returns:
            ParseResult with Document or error info
        """
        result = ParseResult()
        path = Path(path)

        if not path.exists():
            result.errors.append(f"File not found: {path}")
            return result

        if path.suffix.lower() != ".pdf":
            result.errors.append(f"Not a PDF file: {path}")
            return result

        try:
            # Create PDFExtractor with options
            extractor = PDFExtractor(
                str(path),
                verbose=self.pdf_options["verbose"],
                chunk_size=self.pdf_options["chunk_size"],
                min_quality=self.pdf_options["min_quality"],
                extract_images=self.pdf_options["extract_images"],
                image_dir=self.pdf_options["image_dir"],
                min_image_size=self.pdf_options["min_image_size"],
                use_ocr=self.pdf_options["use_ocr"],
                password=self.pdf_options["password"],
                extract_tables=self.pdf_options["extract_tables"],
                parallel=self.pdf_options["parallel"],
                max_workers=self.pdf_options["max_workers"],
            )

            # Extract all content
            extraction_result = extractor.extract_all()

            if not extraction_result:
                result.errors.append("PDF extraction failed")
                return result

            # Convert to unified Document
            document = self._convert_to_document(extraction_result, str(path))

            result.document = document
            result.success = True
            result.warnings.extend(document.stats.warnings)

        except Exception as e:
            result.errors.append(f"PDF parse error: {str(e)}")

        return result

    def _convert_to_document(self, extraction_result: dict, source_path: str) -> Document:
        """Convert PDFExtractor result to unified Document."""
        document = Document(
            title=Path(source_path).stem,
            format="pdf",
            source_path=source_path,
        )

        # Extract metadata from PDF info
        if "metadata" in extraction_result:
            meta = extraction_result["metadata"]
            document.title = meta.get("title", document.title)
            document.meta["author"] = meta.get("author")
            document.meta["subject"] = meta.get("subject")
            document.meta["creator"] = meta.get("creator")
            document.meta["creation_date"] = meta.get("creationDate")
            document.meta["modification_date"] = meta.get("modDate")

        # Process pages
        pages = extraction_result.get("pages", [])

        for page_num, page_data in enumerate(pages):
            # Add page heading
            page_heading = f"Page {page_num + 1}"
            if page_data.get("headings"):
                page_heading = page_data["headings"][0].get("text", page_heading)

            document.blocks.append(
                ContentBlock(
                    type=ContentBlockType.HEADING,
                    content=page_heading,
                    metadata={
                        "heading_data": Heading(
                            level=2,
                            text=page_heading,
                            source_line=page_num + 1,
                        )
                    },
                    source_line=page_num + 1,
                )
            )

            # Add page text as paragraph
            if page_data.get("text"):
                document.blocks.append(
                    ContentBlock(
                        type=ContentBlockType.PARAGRAPH,
                        content=page_data["text"],
                        source_line=page_num + 1,
                    )
                )

            # Convert code blocks
            for code_data in page_data.get("code_samples", []):
                code_block = CodeBlock(
                    code=code_data["code"],
                    language=code_data.get("language", "unknown"),
                    quality_score=code_data.get("quality_score"),
                    confidence=code_data.get("confidence"),
                    is_valid=code_data.get("is_valid"),
                    source_line=page_num + 1,
                )
                document.code_blocks.append(code_block)

                document.blocks.append(
                    ContentBlock(
                        type=ContentBlockType.CODE_BLOCK,
                        content=code_data["code"],
                        metadata={
                            "code_data": code_block,
                            "language": code_data.get("language", "unknown"),
                        },
                        source_line=page_num + 1,
                        quality_score=code_data.get("quality_score"),
                    )
                )

            # Convert tables
            for table_data in page_data.get("tables", []):
                table = Table(
                    rows=table_data.get("rows", []),
                    headers=table_data.get("headers"),
                    caption=f"Table from page {page_num + 1}",
                    source_format="pdf",
                    source_line=page_num + 1,
                )
                document.tables.append(table)

                quality = self.quality_scorer.score_table(table)
                document.blocks.append(
                    ContentBlock(
                        type=ContentBlockType.TABLE,
                        content=f"[Table from page {page_num + 1}]",
                        metadata={"table_data": table},
                        source_line=page_num + 1,
                        quality_score=quality,
                    )
                )

            # Convert images
            for img_data in page_data.get("extracted_images", []):
                image = Image(
                    source=img_data.get("path", ""),
                    alt_text=f"Image from page {page_num + 1}",
                    width=img_data.get("width"),
                    height=img_data.get("height"),
                    source_line=page_num + 1,
                )
                document.images.append(image)

            # Extract headings
            for heading_data in page_data.get("headings", []):
                heading = Heading(
                    level=int(heading_data.get("level", "h2")[1]),
                    text=heading_data.get("text", ""),
                    id=heading_data.get("id", ""),
                    source_line=page_num + 1,
                )
                document.headings.append(heading)

        # Set stats
        document.stats.total_blocks = len(document.blocks)
        document.stats.code_blocks = len(document.code_blocks)
        document.stats.tables = len(document.tables)
        document.stats.headings = len(document.headings)

        return document

    def parse(self, source: str | Path) -> ParseResult:
        """
        Parse PDF from source.

        For PDF files, source should be a file path.
        """
        if isinstance(source, str) and Path(source).exists():
            return self.parse_file(source)
        elif isinstance(source, Path):
            return self.parse_file(source)
        else:
            result = ParseResult()
            result.errors.append("PDF parsing requires a file path")
            return result
