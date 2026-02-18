#!/usr/bin/env python3
"""
Test script for unified document parsers.

Tests RST and Markdown parsers with various constructs.
"""

import sys

sys.path.insert(0, "src")

import pytest

from skill_seekers.cli.parsers.extractors import (
    ContentBlockType,
    CrossRefType,
    MarkdownParser,
    RstParser,
    Table,
    parse_document,
)


class TestRstParser:
    """Test RST parser with comprehensive example."""

    @pytest.fixture
    def rst_content(self):
        return """
Node
====

Brief description of the Node class.

.. classref:: Node

The Node class is the base class for all scene objects.

Properties
----------

.. table:: Properties

   ============= =========== ============
   Property      Type        Default
   ============= =========== ============
   position      Vector2     (0, 0)
   rotation      float       0.0
   scale         Vector2     (1, 1)
   visible       bool        true
   ============= =========== ============

Methods
-------

.. list-table:: Methods
   :header-rows: 1

   * - Method
     - Returns
     - Description
   * - _ready()
     - void
     - Called when node enters tree
   * - _process(delta)
     - void
     - Called every frame

Signals
-------

.. table:: Signals

   ============= ===========
   Signal        Description
   ============= ===========
   ready         Emitted when ready
   tree_exiting  Emitted when exiting
   ============= ===========

Code Examples
-------------

Basic usage:

.. code-block:: gdscript

    extends Node

    func _ready():
        print("Hello, World!")
        position = Vector2(100, 100)

See also :ref:`Object<class_Object>` and :class:`RefCounted`.

.. note::

   This is an important note about using Node.

.. warning::

   Be careful with memory management!

:param parent: The parent node in the tree
:returns: A new Node instance
:rtype: Node

See the :doc:`../tutorial` for more information.

Visit `Godot Engine <https://godotengine.org>`_ for updates.

|version| |bitfield|

.. |version| replace:: v4.0
.. |bitfield| replace:: BitField
"""

    @pytest.fixture
    def parsed_doc(self, rst_content):
        parser = RstParser()
        result = parser.parse_string(rst_content, "test_class.rst")
        assert result.success, f"Parsing failed: {result.errors}"
        return result.document

    def test_parsing_success(self, parsed_doc):
        """Test that parsing succeeds."""
        assert parsed_doc is not None
        assert parsed_doc.format == "rst"

    def test_title_extraction(self, parsed_doc):
        """Test title extraction from first heading."""
        assert parsed_doc.title == "Node"

    def test_headings_count(self, parsed_doc):
        """Test that all headings are extracted."""
        assert len(parsed_doc.headings) == 5

    def test_heading_levels(self, parsed_doc):
        """Test heading levels are correct."""
        assert parsed_doc.headings[0].level == 1
        assert parsed_doc.headings[0].text == "Node"
        assert parsed_doc.headings[1].level == 2
        assert parsed_doc.headings[1].text == "Properties"

    def test_tables_count(self, parsed_doc):
        """Test that tables are extracted."""
        assert len(parsed_doc.tables) == 3

    def test_table_headers(self, parsed_doc):
        """Test table headers are correctly extracted."""
        # Properties table should have headers
        properties_table = parsed_doc.tables[0]
        assert properties_table.caption == "Properties"
        assert properties_table.headers is not None
        assert "Property" in properties_table.headers
        assert "Type" in properties_table.headers
        assert "Default" in properties_table.headers

    def test_table_rows(self, parsed_doc):
        """Test table rows are extracted."""
        properties_table = parsed_doc.tables[0]
        assert properties_table.num_rows >= 4  # position, rotation, scale, visible

    def test_code_blocks_count(self, parsed_doc):
        """Test code blocks extraction."""
        assert len(parsed_doc.code_blocks) == 1

    def test_code_block_language(self, parsed_doc):
        """Test code block language detection."""
        code_block = parsed_doc.code_blocks[0]
        assert code_block.language == "gdscript"

    def test_code_block_quality(self, parsed_doc):
        """Test code block quality scoring."""
        code_block = parsed_doc.code_blocks[0]
        assert code_block.quality_score is not None
        assert code_block.quality_score > 5.0

    def test_cross_references(self, parsed_doc):
        """Test cross-references extraction."""
        assert len(parsed_doc.internal_links) >= 3

    def test_cross_reference_types(self, parsed_doc):
        """Test cross-reference types."""
        ref_types = {x.ref_type for x in parsed_doc.internal_links}
        assert CrossRefType.REF in ref_types
        assert CrossRefType.CLASS in ref_types
        assert CrossRefType.DOC in ref_types

    def test_admonitions(self, parsed_doc):
        """Test admonition extraction."""
        admonitions = [b for b in parsed_doc.blocks if b.type == ContentBlockType.ADMONITION]
        assert len(admonitions) == 2

    def test_field_lists(self, parsed_doc):
        """Test field list extraction."""
        assert len(parsed_doc.field_lists) == 1

    def test_substitutions(self, parsed_doc):
        """Test substitution extraction."""
        assert len(parsed_doc.substitutions) == 2
        assert "version" in parsed_doc.substitutions
        assert parsed_doc.substitutions["version"] == "v4.0"

    def test_to_markdown(self, parsed_doc):
        """Test markdown conversion."""
        markdown = parsed_doc.to_markdown()
        assert len(markdown) > 0
        assert "# Node" in markdown

    def test_to_skill_format(self, parsed_doc):
        """Test skill format conversion."""
        skill_data = parsed_doc.to_skill_format()
        assert "title" in skill_data
        assert "code_samples" in skill_data
        assert "tables" in skill_data
        assert "cross_references" in skill_data


class TestMarkdownParser:
    """Test Markdown parser."""

    @pytest.fixture
    def md_content(self):
        return """---
title: Test Document
description: A test markdown file
---

# Main Heading

This is a paragraph with **bold** and *italic* text.

## Subheading

Here's some `inline code` and a link to [Google](https://google.com).

### Code Example

```python
def hello_world():
    print("Hello, World!")
    return True
```

### Table

| Name | Type | Description |
|------|------|-------------|
| id   | int  | Unique ID   |
| name | str  | Item name   |
| active | bool | Is active |

> [!NOTE]
> This is an important note.

> [!WARNING]
> Be careful!

## List Example

- Item 1
- Item 2
  - Nested item
- Item 3

1. First
2. Second
3. Third

## Image

![Alt text](image.png)
"""

    @pytest.fixture
    def parsed_doc(self, md_content):
        parser = MarkdownParser()
        result = parser.parse_string(md_content, "test.md")
        assert result.success, f"Parsing failed: {result.errors}"
        return result.document

    def test_parsing_success(self, parsed_doc):
        """Test that parsing succeeds."""
        assert parsed_doc is not None
        assert parsed_doc.format == "markdown"

    def test_frontmatter_metadata(self, parsed_doc):
        """Test frontmatter metadata extraction."""
        assert parsed_doc.meta.get("title") == "Test Document"
        assert parsed_doc.meta.get("description") == "A test markdown file"

    def test_title_from_frontmatter(self, parsed_doc):
        """Test title extraction from frontmatter."""
        assert parsed_doc.title == "Test Document"

    def test_headings_count(self, parsed_doc):
        """Test headings extraction."""
        assert len(parsed_doc.headings) == 6

    def test_heading_levels(self, parsed_doc):
        """Test heading levels."""
        assert parsed_doc.headings[0].level == 1
        assert parsed_doc.headings[0].text == "Main Heading"

    def test_tables_count(self, parsed_doc):
        """Test table extraction."""
        assert len(parsed_doc.tables) == 1

    def test_table_structure(self, parsed_doc):
        """Test table structure."""
        table = parsed_doc.tables[0]
        assert table.num_cols == 3
        assert table.num_rows == 3
        assert "Name" in table.headers
        assert "Type" in table.headers
        assert "Description" in table.headers

    def test_code_blocks_count(self, parsed_doc):
        """Test code block extraction."""
        assert len(parsed_doc.code_blocks) == 1

    def test_code_block_language(self, parsed_doc):
        """Test code block language."""
        code_block = parsed_doc.code_blocks[0]
        assert code_block.language == "python"

    def test_code_block_quality(self, parsed_doc):
        """Test code block quality scoring."""
        code_block = parsed_doc.code_blocks[0]
        assert code_block.quality_score is not None
        assert code_block.quality_score >= 8.0

    def test_admonitions(self, parsed_doc):
        """Test admonition extraction."""
        admonitions = [b for b in parsed_doc.blocks if b.type == ContentBlockType.ADMONITION]
        assert len(admonitions) == 2

    def test_images_count(self, parsed_doc):
        """Test image extraction."""
        assert len(parsed_doc.images) == 1

    def test_image_source(self, parsed_doc):
        """Test image source."""
        assert parsed_doc.images[0].source == "image.png"

    def test_external_links(self, parsed_doc):
        """Test external link extraction."""
        assert len(parsed_doc.external_links) == 1
        assert parsed_doc.external_links[0].target == "https://google.com"


class TestAutoDetection:
    """Test auto-detection of format."""

    def test_rst_detection(self):
        """Test RST format auto-detection."""
        rst = """
Title
=====

.. code-block:: python

    print("hello")

:ref:`target`
"""
        result = parse_document(rst)
        assert result.success
        assert result.document.format == "rst"

    def test_markdown_detection(self):
        """Test Markdown format auto-detection."""
        md = """
# Title

```python
print("hello")
```

[link](http://example.com)
"""
        result = parse_document(md)
        assert result.success
        assert result.document.format == "markdown"


class TestQualityScorer:
    """Test quality scoring."""

    def test_good_python_code_score(self):
        """Test quality score for good Python code."""
        from skill_seekers.cli.parsers.extractors import QualityScorer

        scorer = QualityScorer()
        good_code = """
def calculate_average(numbers):
    \"\"\"Calculate the average of a list of numbers.\"\"\""
    if not numbers:
        return 0
    total = sum(numbers)
    return total / len(numbers)
"""
        score = scorer.score_code_block(good_code, "python")
        assert score > 7.0

    def test_empty_code_score(self):
        """Test quality score for empty code."""
        from skill_seekers.cli.parsers.extractors import QualityScorer

        scorer = QualityScorer()
        score = scorer.score_code_block("", "python")
        assert score == 0.0

    def test_good_table_score(self):
        """Test quality score for good table."""
        from skill_seekers.cli.parsers.extractors import QualityScorer

        scorer = QualityScorer()
        good_table = Table(
            rows=[["1", "2", "3"], ["4", "5", "6"]],
            headers=["A", "B", "C"],
            caption="Good Table",
        )
        score = scorer.score_table(good_table)
        assert score > 6.0

    def test_language_detection(self):
        """Test language detection."""
        from skill_seekers.cli.parsers.extractors import QualityScorer

        scorer = QualityScorer()
        python_code = "def foo():\n    return 42"
        lang, confidence = scorer.detect_language(python_code)
        assert lang == "python"
        assert confidence > 0.5
