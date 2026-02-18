"""
Output Formatters

Convert unified Document structure to various output formats.
"""

from typing import Any

from .unified_structure import (
    Document,
    ContentBlock,
    ContentBlockType,
    AdmonitionType,
    ListType,
    Table,
)


class MarkdownFormatter:
    """Format Document as Markdown."""

    def __init__(self, options: dict[str, Any] = None):
        self.options = options or {}
        self.include_toc = self.options.get("include_toc", False)
        self.max_heading_level = self.options.get("max_heading_level", 6)
        self.code_block_style = self.options.get("code_block_style", "fenced")
        self.table_style = self.options.get("table_style", "github")

    def format(self, document: Document) -> str:
        """Convert document to markdown string."""
        parts = []

        # Title
        if document.title:
            parts.append(f"# {document.title}\n")

        # Metadata as YAML frontmatter
        if document.meta:
            parts.append(self._format_metadata(document.meta))

        # Table of contents
        if self.include_toc and document.headings:
            parts.append(self._format_toc(document.headings))

        # Content blocks
        for block in document.blocks:
            formatted = self._format_block(block)
            if formatted:
                parts.append(formatted)

        return "\n".join(parts)

    def _format_metadata(self, meta: dict) -> str:
        """Format metadata as YAML frontmatter."""
        lines = ["---"]
        for key, value in meta.items():
            if isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{key}: {value}")
        lines.append("---\n")
        return "\n".join(lines)

    def _format_toc(self, headings: list) -> str:
        """Format table of contents."""
        lines = ["## Table of Contents\n"]
        for h in headings:
            if h.level <= self.max_heading_level:
                indent = "  " * (h.level - 1)
                anchor = h.id or h.text.lower().replace(" ", "-")
                lines.append(f"{indent}- [{h.text}](#{anchor})")
        lines.append("")
        return "\n".join(lines)

    def _format_block(self, block: ContentBlock) -> str:
        """Format a single content block."""
        handlers = {
            ContentBlockType.HEADING: self._format_heading,
            ContentBlockType.PARAGRAPH: self._format_paragraph,
            ContentBlockType.CODE_BLOCK: self._format_code_block,
            ContentBlockType.TABLE: self._format_table,
            ContentBlockType.LIST: self._format_list,
            ContentBlockType.IMAGE: self._format_image,
            ContentBlockType.CROSS_REFERENCE: self._format_cross_ref,
            ContentBlockType.ADMONITION: self._format_admonition,
            ContentBlockType.DIRECTIVE: self._format_directive,
            ContentBlockType.FIELD_LIST: self._format_field_list,
            ContentBlockType.DEFINITION_LIST: self._format_definition_list,
            ContentBlockType.META: self._format_meta,
        }

        handler = handlers.get(block.type)
        if handler:
            return handler(block)

        # Default: return content as-is
        return block.content + "\n"

    def _format_heading(self, block: ContentBlock) -> str:
        """Format heading block."""
        heading_data = block.metadata.get("heading_data")
        if heading_data:
            level = min(heading_data.level, 6)
            text = heading_data.text
        else:
            level = block.metadata.get("level", 1)
            text = block.content

        if level > self.max_heading_level:
            return f"**{text}**\n"

        return f"{'#' * level} {text}\n"

    def _format_paragraph(self, block: ContentBlock) -> str:
        """Format paragraph block."""
        return block.content + "\n"

    def _format_code_block(self, block: ContentBlock) -> str:
        """Format code block."""
        code_data = block.metadata.get("code_data")

        if code_data:
            code = code_data.code
            lang = code_data.language or ""
        else:
            code = block.content
            lang = block.metadata.get("language", "")

        if self.code_block_style == "fenced":
            return f"```{lang}\n{code}\n```\n"
        else:
            # Indented style
            indented = "\n".join("    " + line for line in code.split("\n"))
            return indented + "\n"

    def _format_table(self, block: ContentBlock) -> str:
        """Format table block."""
        table_data = block.metadata.get("table_data")
        if not table_data:
            return ""

        return self._format_table_data(table_data)

    def _format_table_data(self, table: Table) -> str:
        """Format table data as markdown."""
        if not table.rows:
            return ""

        lines = []

        # Caption
        if table.caption:
            lines.append(f"**{table.caption}**\n")

        # Headers
        headers = table.headers or table.rows[0]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("|" + "|".join("---" for _ in headers) + "|")

        # Rows (skip first if used as headers)
        start_row = 0 if table.headers else 1
        for row in table.rows[start_row:]:
            # Pad row to match header count
            padded_row = row + [""] * (len(headers) - len(row))
            lines.append("| " + " | ".join(padded_row[: len(headers)]) + " |")

        lines.append("")
        return "\n".join(lines)

    def _format_list(self, block: ContentBlock) -> str:
        """Format list block."""
        list_type = block.metadata.get("list_type", ListType.BULLET)
        items = block.metadata.get("items", [])

        if not items:
            return block.content + "\n"

        lines = []
        for i, item in enumerate(items):
            prefix = f"{i + 1}." if list_type == ListType.NUMBERED else "-"
            lines.append(f"{prefix} {item}")

        lines.append("")
        return "\n".join(lines)

    def _format_image(self, block: ContentBlock) -> str:
        """Format image block."""
        image_data = block.metadata.get("image_data")
        if image_data:
            src = image_data.source
            alt = image_data.alt_text or ""
        else:
            src = block.metadata.get("src", "")
            alt = block.metadata.get("alt", "")

        return f"![{alt}]({src})\n"

    def _format_cross_ref(self, block: ContentBlock) -> str:
        """Format cross-reference block."""
        xref_data = block.metadata.get("xref_data")
        if xref_data:
            text = xref_data.text or xref_data.target
            target = xref_data.target
            return f"[{text}](#{target})\n"

        return block.content + "\n"

    def _format_admonition(self, block: ContentBlock) -> str:
        """Format admonition/callout block."""
        admonition_type = block.metadata.get("admonition_type", AdmonitionType.NOTE)

        # GitHub-style admonitions
        type_map = {
            AdmonitionType.NOTE: "NOTE",
            AdmonitionType.WARNING: "WARNING",
            AdmonitionType.TIP: "TIP",
            AdmonitionType.IMPORTANT: "IMPORTANT",
            AdmonitionType.CAUTION: "CAUTION",
        }

        type_str = type_map.get(admonition_type, "NOTE")
        content = block.content

        return f"> [!{type_str}]\n> {content.replace(chr(10), chr(10) + '> ')}\n"

    def _format_directive(self, block: ContentBlock) -> str:
        """Format directive block (RST-specific)."""
        directive_name = block.metadata.get("directive_name", "unknown")

        # Format as a blockquote with directive name
        content = block.content
        lines = [f"> **{directive_name}**"]
        for line in content.split("\n"):
            lines.append(f"> {line}")
        lines.append("")
        return "\n".join(lines)

    def _format_field_list(self, block: ContentBlock) -> str:
        """Format field list block."""
        fields = block.metadata.get("fields", [])
        if not fields:
            return block.content + "\n"

        lines = []
        for field in fields:
            if field.arg:
                lines.append(f"**{field.name}** (`{field.arg}`): {field.content}")
            else:
                lines.append(f"**{field.name}**: {field.content}")
        lines.append("")
        return "\n".join(lines)

    def _format_definition_list(self, block: ContentBlock) -> str:
        """Format definition list block."""
        items = block.metadata.get("items", [])
        if not items:
            return block.content + "\n"

        lines = []
        for item in items:
            if item.classifier:
                lines.append(f"**{item.term}** *({item.classifier})*")
            else:
                lines.append(f"**{item.term}**")
            lines.append(f": {item.definition}")
        lines.append("")
        return "\n".join(lines)

    def _format_meta(self, block: ContentBlock) -> str:
        """Format metadata block (usually filtered out)."""
        return ""  # Metadata goes in YAML frontmatter


class SkillFormatter:
    """Format Document for skill-seekers internal use."""

    def format(self, document: Document) -> dict[str, Any]:
        """Format document for skill output."""
        return {
            "title": document.title,
            "source_path": document.source_path,
            "format": document.format,
            "content_summary": self._extract_summary(document),
            "headings": [{"level": h.level, "text": h.text, "id": h.id} for h in document.headings],
            "code_samples": [
                {
                    "code": cb.code,
                    "language": cb.language,
                    "quality_score": cb.quality_score,
                    "confidence": cb.confidence,
                }
                for cb in document.code_blocks
            ],
            "tables": [
                {
                    "headers": t.headers,
                    "rows": t.rows,
                    "caption": t.caption,
                    "quality_score": self._score_table(t),
                }
                for t in document.tables
            ],
            "cross_references": [
                {
                    "type": xr.ref_type.value,
                    "target": xr.target,
                    "text": xr.text,
                    "resolved": xr.resolved,
                }
                for xr in document.internal_links + document.external_links
            ],
            "api_summary": document.get_api_summary(),
            "meta": document.meta,
            "extraction_stats": {
                "total_blocks": document.stats.total_blocks,
                "code_blocks": document.stats.code_blocks,
                "tables": document.stats.tables,
                "headings": document.stats.headings,
                "cross_references": document.stats.cross_references,
                "processing_time_ms": document.stats.processing_time_ms,
            },
        }

    def _extract_summary(self, document: Document, max_length: int = 500) -> str:
        """Extract a text summary from the document."""
        paragraphs = []
        for block in document.blocks:
            if block.type == ContentBlockType.PARAGRAPH:
                paragraphs.append(block.content)
                if len(" ".join(paragraphs)) > max_length:
                    break

        summary = " ".join(paragraphs)
        if len(summary) > max_length:
            summary = summary[: max_length - 3] + "..."

        return summary

    def _score_table(self, table: Table) -> float:
        """Quick table quality score."""
        if not table.rows:
            return 0.0

        score = 5.0
        if table.headers:
            score += 2.0
        if 2 <= len(table.rows) <= 50:
            score += 1.0

        return min(10.0, score)
