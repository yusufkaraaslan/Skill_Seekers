# Unified Document Parsers Architecture

## Overview

The Unified Document Parser system provides a standardized interface for extracting structured content from multiple document formats (RST, Markdown, PDF). It replaces format-specific extraction logic with a common data model and extensible parser framework.

## Architecture Goals

1. **Standardization**: All parsers output the same `Document` structure
2. **Extensibility**: Easy to add new formats (HTML, AsciiDoc, etc.)
3. **Quality**: Built-in quality scoring for extracted content
4. **Backward Compatibility**: Legacy parsers remain functional during migration

## Core Components

### 1. Data Model Layer

**File**: `src/skill_seekers/cli/parsers/extractors/unified_structure.py`

```
┌─────────────────────────────────────────────────────────────┐
│                      Document                                │
├─────────────────────────────────────────────────────────────┤
│  title: str                                                  │
│  format: str                                                 │
│  source_path: str                                            │
├─────────────────────────────────────────────────────────────┤
│  blocks: List[ContentBlock]         # All content blocks    │
│  headings: List[Heading]            # Extracted from blocks │
│  code_blocks: List[CodeBlock]       # Extracted from blocks │
│  tables: List[Table]                # Extracted from blocks │
│  images: List[Image]                # Extracted from blocks │
├─────────────────────────────────────────────────────────────┤
│  internal_links: List[CrossReference]  # :ref:, #anchor     │
│  external_links: List[CrossReference]  # URLs               │
├─────────────────────────────────────────────────────────────┤
│  meta: Dict[str, Any]               # Frontmatter, metadata │
│  stats: ExtractionStats             # Processing metrics    │
└─────────────────────────────────────────────────────────────┘
```

#### ContentBlock

The universal content container:

```python
@dataclass
class ContentBlock:
    type: ContentBlockType      # HEADING, PARAGRAPH, CODE_BLOCK, etc.
    content: str                # Raw text content
    metadata: Dict[str, Any]    # Type-specific data
    source_line: Optional[int]  # Line number in source
    quality_score: Optional[float]  # 0-10 quality rating
```

**ContentBlockType Enum**:
- `HEADING` - Section titles
- `PARAGRAPH` - Text content
- `CODE_BLOCK` - Code snippets
- `TABLE` - Tabular data
- `LIST` - Bullet/numbered lists
- `IMAGE` - Image references
- `CROSS_REFERENCE` - Internal links
- `DIRECTIVE` - RST directives
- `FIELD_LIST` - Parameter documentation
- `DEFINITION_LIST` - Term/definition pairs
- `ADMONITION` - Notes, warnings, tips
- `META` - Metadata fields

#### Specialized Data Classes

**Table**:
```python
@dataclass
class Table:
    rows: List[List[str]]       # 2D cell array
    headers: Optional[List[str]]
    caption: Optional[str]
    source_format: str          # 'simple', 'grid', 'list-table'
```

**CodeBlock**:
```python
@dataclass
class CodeBlock:
    code: str
    language: Optional[str]
    quality_score: Optional[float]
    confidence: Optional[float]  # Language detection confidence
    is_valid: Optional[bool]     # Syntax validation
```

**CrossReference**:
```python
@dataclass
class CrossReference:
    ref_type: CrossRefType      # REF, DOC, CLASS, METH, etc.
    target: str                 # Target ID/URL
    text: Optional[str]         # Display text
```

### 2. Parser Interface Layer

**File**: `src/skill_seekers/cli/parsers/extractors/base_parser.py`

```
┌─────────────────────────────────────────────────────────────┐
│                    BaseParser (Abstract)                     │
├─────────────────────────────────────────────────────────────┤
│  + format_name: str                                          │
│  + supported_extensions: List[str]                           │
├─────────────────────────────────────────────────────────────┤
│  + parse(source) -> ParseResult                              │
│  + parse_file(path) -> ParseResult                           │
│  + parse_string(content) -> ParseResult                      │
│  # _parse_content(content, path) -> Document                 │
│  # _detect_format(content) -> bool                           │
└─────────────────────────────────────────────────────────────┘
```

**ParseResult**:
```python
@dataclass
class ParseResult:
    document: Optional[Document]
    success: bool
    errors: List[str]
    warnings: List[str]
```

### 3. Parser Implementations

#### RST Parser

**File**: `src/skill_seekers/cli/parsers/extractors/rst_parser.py`

**Supported Constructs**:
- Headers (underline style: `====`, `----`)
- Code blocks (`.. code-block:: language`)
- Tables (simple, grid, list-table)
- Cross-references (`:ref:`, `:class:`, `:meth:`, `:func:`, `:attr:`)
- Directives (`.. note::`, `.. warning::`, `.. deprecated::`)
- Field lists (`:param:`, `:returns:`, `:type:`)
- Definition lists
- Substitutions (`|name|`)
- Toctree (`.. toctree::`)

**Parsing Strategy**:
1. First pass: Collect substitution definitions
2. Second pass: Parse block-level constructs
3. Post-process: Extract specialized content lists

#### Markdown Parser

**File**: `src/skill_seekers/cli/parsers/extractors/markdown_parser.py`

**Supported Constructs**:
- Headers (ATX: `#`, Setext: underline)
- Code blocks (fenced: ```` ``` ````)
- Tables (GitHub-flavored)
- Lists (bullet, numbered)
- Admonitions (GitHub-style: `> [!NOTE]`)
- Images and links
- Frontmatter (YAML metadata)

#### PDF Parser (Future)

**Status**: Not yet migrated to unified structure

### 4. Quality Scoring Layer

**File**: `src/skill_seekers/cli/parsers/extractors/quality_scorer.py`

**Code Quality Factors**:
- Language detection confidence
- Code length appropriateness
- Line count
- Keyword density
- Syntax pattern matching
- Bracket balance

**Table Quality Factors**:
- Has headers
- Consistent column count
- Reasonable size
- Non-empty cells
- Has caption

### 5. Output Formatter Layer

**File**: `src/skill_seekers/cli/parsers/extractors/formatters.py`

**MarkdownFormatter**:
- Converts Document to Markdown
- Handles all ContentBlockType variants
- Configurable options (TOC, max heading level, etc.)

**SkillFormatter**:
- Converts Document to skill-seekers internal format
- Compatible with existing skill pipelines

## Integration Points

### 1. Codebase Scraper

**File**: `src/skill_seekers/cli/codebase_scraper.py`

```python
# Enhanced RST extraction
def extract_rst_structure(content: str) -> dict:
    parser = RstParser()
    result = parser.parse_string(content)
    if result.success:
        return result.document.to_legacy_format()
    # Fallback to legacy parser
```

### 2. Doc Scraper

**File**: `src/skill_seekers/cli/doc_scraper.py`

```python
# Enhanced Markdown extraction
def _extract_markdown_content(self, content, url):
    parser = MarkdownParser()
    result = parser.parse_string(content, url)
    if result.success:
        doc = result.document
        return {
            "title": doc.title,
            "headings": [...],
            "code_samples": [...],
            "_enhanced": True,
        }
    # Fallback to legacy extraction
```

## Usage Patterns

### Basic Parsing

```python
from skill_seekers.cli.parsers.extractors import RstParser

parser = RstParser()
result = parser.parse_file("docs/class_node.rst")

if result.success:
    doc = result.document
    print(f"Title: {doc.title}")
    print(f"Tables: {len(doc.tables)}")
```

### Auto-Detection

```python
from skill_seekers.cli.parsers.extractors import parse_document

result = parse_document("file.rst")  # Auto-detects format
# or
result = parse_document(content, format_hint="rst")
```

### Format Conversion

```python
# To Markdown
markdown = doc.to_markdown()

# To Skill format
skill_data = doc.to_skill_format()

# To legacy format (backward compatibility)
legacy = doc.to_skill_format()  # Compatible with old structure
```

### API Documentation Extraction

```python
# Extract structured API info
api_summary = doc.get_api_summary()
# Returns:
# {
#   "properties": [{"name": "position", "type": "Vector2", ...}],
#   "methods": [{"name": "_ready", "returns": "void", ...}],
#   "signals": [{"name": "ready", ...}]
# }
```

## Extending the System

### Adding a New Parser

1. **Create parser class**:
```python
class HtmlParser(BaseParser):
    @property
    def format_name(self) -> str:
        return "html"
    
    @property
    def supported_extensions(self) -> list[str]:
        return [".html", ".htm"]
    
    def _parse_content(self, content: str, source_path: str) -> Document:
        # Parse HTML to Document
        pass
```

2. **Register in `__init__.py`**:
```python
from .html_parser import HtmlParser

__all__ = [..., "HtmlParser"]
```

3. **Add tests**:
```python
def test_html_parser():
    parser = HtmlParser()
    result = parser.parse_string("<h1>Title</h1>")
    assert result.document.title == "Title"
```

## Testing Strategy

### Unit Tests

Test individual parsers with various constructs:
- `test_rst_parser.py` - RST-specific features
- `test_markdown_parser.py` - Markdown-specific features
- `test_quality_scorer.py` - Quality scoring

### Integration Tests

Test integration with existing scrapers:
- `test_codebase_scraper.py` - RST file processing
- `test_doc_scraper.py` - Markdown web content

### Backward Compatibility Tests

Verify new parsers match old output:
- Same field names in output dicts
- Same content extraction (plus more)
- Legacy fallback works

## Performance Considerations

### Current Performance

- RST Parser: ~1-2ms per 1000 lines
- Markdown Parser: ~1ms per 1000 lines
- Quality Scoring: Adds ~10% overhead

### Optimization Opportunities

1. **Caching**: Cache parsed documents by hash
2. **Parallel Processing**: Parse multiple files concurrently
3. **Lazy Evaluation**: Only extract requested content types

## Migration Guide

### From Legacy Parsers

**Before**:
```python
from skill_seekers.cli.codebase_scraper import extract_rst_structure

structure = extract_rst_structure(content)
```

**After**:
```python
from skill_seekers.cli.parsers.extractors import RstParser

parser = RstParser()
result = parser.parse_string(content)
structure = result.document.to_skill_format()
```

### Backward Compatibility

The enhanced `extract_rst_structure()` function:
1. Tries unified parser first
2. Falls back to legacy parser on failure
3. Returns same dict structure

## Future Enhancements

1. **PDF Parser**: Migrate to unified structure
2. **HTML Parser**: Add for web documentation
3. **Caching Layer**: Redis/disk cache for parsed docs
4. **Streaming**: Parse large files incrementally
5. **Validation**: JSON Schema validation for output

---

**Last Updated**: 2026-02-15
**Version**: 1.0.0
