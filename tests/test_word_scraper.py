#!/usr/bin/env python3
"""
Tests for Word Document Scraper (cli/word_scraper.py)

Tests cover:
- Config-based initialization
- Direct DOCX path conversion
- JSON-based workflow
- Skill structure generation
- Categorization
- Code blocks handling
- Tables handling
- Image handling
- Error handling
- CLI argument parsing
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

try:
    import mammoth  # noqa: F401
    import docx as python_docx  # noqa: F401

    WORD_AVAILABLE = True
except ImportError:
    WORD_AVAILABLE = False


def _make_sample_extracted_data(
    num_sections=2, include_code=False, include_tables=False, include_images=False
):
    """Helper to build a minimal extracted_data dict for testing."""
    mock_image_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    pages = []
    for i in range(1, num_sections + 1):
        section = {
            "section_number": i,
            "heading": f"Section {i}",
            "heading_level": "h1",
            "text": f"Content for section {i}.",
            "headings": [],
            "code_samples": [],
            "tables": [],
            "images": [],
        }
        if include_code:
            section["code_samples"] = [
                {
                    "code": f"def hello_{i}():\n    return 'world'",
                    "language": "python",
                    "quality_score": 7.5,
                }
            ]
        if include_tables:
            section["tables"] = [
                {"headers": ["Col A", "Col B"], "rows": [["val1", "val2"], ["val3", "val4"]]}
            ]
        if include_images:
            section["images"] = [{"index": 0, "data": mock_image_bytes, "width": 100, "height": 80}]
        pages.append(section)

    return {
        "source_file": "test.docx",
        "metadata": {
            "title": "Test Doc",
            "author": "Test Author",
            "created": "",
            "modified": "",
            "subject": "",
        },
        "total_sections": num_sections,
        "total_code_blocks": num_sections if include_code else 0,
        "total_images": num_sections if include_images else 0,
        "languages_detected": {"python": num_sections} if include_code else {},
        "pages": pages,
    }


class TestWordToSkillConverterInit(unittest.TestCase):
    """Test WordToSkillConverter initialization and basic functionality."""

    def setUp(self):
        if not WORD_AVAILABLE:
            self.skipTest("mammoth and python-docx not installed")
        from skill_seekers.cli.word_scraper import WordToSkillConverter

        self.WordToSkillConverter = WordToSkillConverter
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if hasattr(self, "temp_dir"):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_with_name_and_docx_path(self):
        """Test initialization with name and docx path."""
        config = {"name": "test_skill", "docx_path": "test.docx"}
        converter = self.WordToSkillConverter(config)
        self.assertEqual(converter.name, "test_skill")
        self.assertEqual(converter.docx_path, "test.docx")

    def test_init_with_full_config(self):
        """Test initialization with full config."""
        config = {
            "name": "my_skill",
            "docx_path": "docs/api.docx",
            "description": "API documentation skill",
        }
        converter = self.WordToSkillConverter(config)
        self.assertEqual(converter.name, "my_skill")
        self.assertEqual(converter.description, "API documentation skill")

    def test_init_requires_name(self):
        """Test that missing 'name' field raises an error."""
        with self.assertRaises((KeyError, TypeError)):
            self.WordToSkillConverter({})

    def test_default_description_uses_name(self):
        """Test that default description is generated from name."""
        config = {"name": "my_api", "docx_path": "api.docx"}
        converter = self.WordToSkillConverter(config)
        self.assertIn("my_api", converter.description)

    def test_skill_dir_uses_name(self):
        """Test that skill_dir is derived from name."""
        config = {"name": "my_skill", "docx_path": "test.docx"}
        converter = self.WordToSkillConverter(config)
        self.assertIn("my_skill", converter.skill_dir)

    def test_name_auto_detected_from_filename(self):
        """Test name can be extracted from filename via infer_description_from_word."""
        from skill_seekers.cli.word_scraper import infer_description_from_word

        desc = infer_description_from_word({}, name="my_doc")
        self.assertIn("my_doc", desc)


class TestWordCategorization(unittest.TestCase):
    """Test content categorization functionality."""

    def setUp(self):
        if not WORD_AVAILABLE:
            self.skipTest("mammoth and python-docx not installed")
        from skill_seekers.cli.word_scraper import WordToSkillConverter

        self.WordToSkillConverter = WordToSkillConverter
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_single_docx_creates_single_category(self):
        """With docx_path set, categorize_content creates a single category."""
        config = {"name": "test", "docx_path": "test.docx"}
        converter = self.WordToSkillConverter(config)
        converter.extracted_data = _make_sample_extracted_data(num_sections=3)

        categories = converter.categorize_content()

        self.assertEqual(len(categories), 1)
        # Category key is sanitized docx basename
        self.assertIn("test", categories)
        self.assertEqual(len(categories["test"]["pages"]), 3)

    def test_keyword_based_categorization(self):
        """Test keyword-based categorization without docx_path."""
        config = {
            "name": "test",
            "docx_path": "",
            "categories": {
                "api": ["api", "reference"],
                "guide": ["getting started", "tutorial"],
            },
        }
        converter = self.WordToSkillConverter(config)
        converter.docx_path = ""
        converter.extracted_data = {
            "pages": [
                {
                    "section_number": 1,
                    "heading": "API Reference",
                    "text": "api reference docs",
                    "code_samples": [],
                    "tables": [],
                    "images": [],
                },
                {
                    "section_number": 2,
                    "heading": "Getting Started",
                    "text": "getting started guide",
                    "code_samples": [],
                    "tables": [],
                    "images": [],
                },
            ]
        }

        categories = converter.categorize_content()
        self.assertIsInstance(categories, dict)
        self.assertGreater(len(categories), 0)

    def test_fallback_to_content_category(self):
        """Without docx_path and no categories config, uses 'content' category."""
        config = {"name": "test", "docx_path": ""}
        converter = self.WordToSkillConverter(config)
        converter.docx_path = ""
        converter.extracted_data = _make_sample_extracted_data(num_sections=1)

        categories = converter.categorize_content()
        self.assertIsInstance(categories, dict)
        self.assertGreater(len(categories), 0)


class TestWordSkillBuilding(unittest.TestCase):
    """Test skill structure generation."""

    def setUp(self):
        if not WORD_AVAILABLE:
            self.skipTest("mammoth and python-docx not installed")
        from skill_seekers.cli.word_scraper import WordToSkillConverter

        self.WordToSkillConverter = WordToSkillConverter
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_build_skill_creates_directory_structure(self):
        """build_skill creates required directory structure."""
        config = {"name": "test_skill", "docx_path": "test.docx"}
        converter = self.WordToSkillConverter(config)
        converter.skill_dir = str(Path(self.temp_dir) / "test_skill")
        converter.extracted_data = _make_sample_extracted_data()

        converter.build_skill()

        skill_dir = Path(self.temp_dir) / "test_skill"
        self.assertTrue(skill_dir.exists())
        self.assertTrue((skill_dir / "references").exists())
        self.assertTrue((skill_dir / "scripts").exists())
        self.assertTrue((skill_dir / "assets").exists())

    def test_build_skill_creates_skill_md(self):
        """build_skill creates SKILL.md with correct content."""
        config = {
            "name": "test_skill",
            "docx_path": "test.docx",
            "description": "Test description for docs",
        }
        converter = self.WordToSkillConverter(config)
        converter.skill_dir = str(Path(self.temp_dir) / "test_skill")
        converter.extracted_data = _make_sample_extracted_data()

        converter.build_skill()

        skill_md = Path(self.temp_dir) / "test_skill" / "SKILL.md"
        self.assertTrue(skill_md.exists())

        content = skill_md.read_text()
        self.assertIn("test_skill", content)
        self.assertIn("Test description for docs", content)

    def test_build_skill_creates_reference_files(self):
        """build_skill creates reference markdown files."""
        config = {"name": "test_skill", "docx_path": "test.docx"}
        converter = self.WordToSkillConverter(config)
        converter.skill_dir = str(Path(self.temp_dir) / "test_skill")
        converter.extracted_data = _make_sample_extracted_data(num_sections=2)

        converter.build_skill()

        refs_dir = Path(self.temp_dir) / "test_skill" / "references"
        # Single-source: named after docx basename
        self.assertTrue((refs_dir / "test.md").exists())
        self.assertTrue((refs_dir / "index.md").exists())

    def test_skill_md_has_yaml_frontmatter(self):
        """SKILL.md starts with valid YAML frontmatter."""
        config = {"name": "myskill", "docx_path": "doc.docx"}
        converter = self.WordToSkillConverter(config)
        converter.skill_dir = str(Path(self.temp_dir) / "myskill")
        converter.extracted_data = _make_sample_extracted_data()

        converter.build_skill()

        skill_md = Path(self.temp_dir) / "myskill" / "SKILL.md"
        content = skill_md.read_text()
        self.assertTrue(content.startswith("---\n"))
        self.assertIn("name:", content)
        self.assertIn("description:", content)

    def test_skill_md_includes_section_overview(self):
        """SKILL.md includes a Section Overview."""
        config = {"name": "test_skill", "docx_path": "test.docx"}
        converter = self.WordToSkillConverter(config)
        converter.skill_dir = str(Path(self.temp_dir) / "test_skill")
        converter.extracted_data = _make_sample_extracted_data(num_sections=3)

        converter.build_skill()

        skill_md = Path(self.temp_dir) / "test_skill" / "SKILL.md"
        content = skill_md.read_text()
        self.assertIn("Section Overview", content)
        self.assertIn("Total Sections", content)


class TestWordCodeBlocks(unittest.TestCase):
    """Test code block extraction and inclusion."""

    def setUp(self):
        if not WORD_AVAILABLE:
            self.skipTest("mammoth and python-docx not installed")
        from skill_seekers.cli.word_scraper import WordToSkillConverter

        self.WordToSkillConverter = WordToSkillConverter
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_code_blocks_included_in_references(self):
        """Code blocks are included in reference files."""
        config = {"name": "test_skill", "docx_path": "test.docx"}
        converter = self.WordToSkillConverter(config)
        converter.skill_dir = str(Path(self.temp_dir) / "test_skill")
        converter.extracted_data = _make_sample_extracted_data(include_code=True)

        converter.build_skill()

        ref_file = Path(self.temp_dir) / "test_skill" / "references" / "test.md"
        content = ref_file.read_text()
        self.assertIn("```python", content)
        self.assertIn("def hello_", content)

    def test_code_examples_in_skill_md(self):
        """SKILL.md includes code examples section when code is present."""
        config = {"name": "test_skill", "docx_path": "test.docx"}
        converter = self.WordToSkillConverter(config)
        converter.skill_dir = str(Path(self.temp_dir) / "test_skill")
        converter.extracted_data = _make_sample_extracted_data(include_code=True)

        converter.build_skill()

        skill_md = Path(self.temp_dir) / "test_skill" / "SKILL.md"
        content = skill_md.read_text()
        self.assertIn("Code Examples", content)

    def test_language_detected_in_statistics(self):
        """Language statistics are included in SKILL.md."""
        config = {"name": "test_skill", "docx_path": "test.docx"}
        converter = self.WordToSkillConverter(config)
        converter.skill_dir = str(Path(self.temp_dir) / "test_skill")
        converter.extracted_data = _make_sample_extracted_data(include_code=True)

        converter.build_skill()

        skill_md = Path(self.temp_dir) / "test_skill" / "SKILL.md"
        content = skill_md.read_text()
        self.assertIn("python", content)


class TestWordTables(unittest.TestCase):
    """Test table extraction and rendering."""

    def setUp(self):
        if not WORD_AVAILABLE:
            self.skipTest("mammoth and python-docx not installed")
        from skill_seekers.cli.word_scraper import WordToSkillConverter

        self.WordToSkillConverter = WordToSkillConverter
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_tables_rendered_in_references(self):
        """Tables are rendered as markdown tables in reference files."""
        config = {"name": "test_skill", "docx_path": "test.docx"}
        converter = self.WordToSkillConverter(config)
        converter.skill_dir = str(Path(self.temp_dir) / "test_skill")
        converter.extracted_data = _make_sample_extracted_data(include_tables=True)

        converter.build_skill()

        ref_file = Path(self.temp_dir) / "test_skill" / "references" / "test.md"
        content = ref_file.read_text()
        # Markdown table syntax
        self.assertIn("| Col A |", content)
        self.assertIn("| --- |", content)

    def test_table_summary_in_skill_md(self):
        """Table summary section appears in SKILL.md when tables exist."""
        config = {"name": "test_skill", "docx_path": "test.docx"}
        converter = self.WordToSkillConverter(config)
        converter.skill_dir = str(Path(self.temp_dir) / "test_skill")
        converter.extracted_data = _make_sample_extracted_data(include_tables=True)

        converter.build_skill()

        skill_md = Path(self.temp_dir) / "test_skill" / "SKILL.md"
        content = skill_md.read_text()
        self.assertIn("Table Summary", content)


class TestWordImages(unittest.TestCase):
    """Test image extraction and handling."""

    def setUp(self):
        if not WORD_AVAILABLE:
            self.skipTest("mammoth and python-docx not installed")
        from skill_seekers.cli.word_scraper import WordToSkillConverter

        self.WordToSkillConverter = WordToSkillConverter
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_images_saved_to_assets(self):
        """Images are saved to the assets/ directory."""
        config = {"name": "test_skill", "docx_path": "test.docx"}
        converter = self.WordToSkillConverter(config)
        converter.skill_dir = str(Path(self.temp_dir) / "test_skill")
        converter.extracted_data = _make_sample_extracted_data(include_images=True)

        converter.build_skill()

        assets_dir = Path(self.temp_dir) / "test_skill" / "assets"
        png_files = list(assets_dir.glob("*.png"))
        self.assertGreater(len(png_files), 0)

    def test_image_references_in_markdown(self):
        """Images are referenced with markdown syntax in reference files."""
        config = {"name": "test_skill", "docx_path": "test.docx"}
        converter = self.WordToSkillConverter(config)
        converter.skill_dir = str(Path(self.temp_dir) / "test_skill")
        converter.extracted_data = _make_sample_extracted_data(include_images=True)

        converter.build_skill()

        ref_file = Path(self.temp_dir) / "test_skill" / "references" / "test.md"
        content = ref_file.read_text()
        self.assertIn("![", content)
        self.assertIn("../assets/", content)


class TestWordErrorHandling(unittest.TestCase):
    """Test error handling for invalid inputs."""

    def setUp(self):
        if not WORD_AVAILABLE:
            self.skipTest("mammoth and python-docx not installed")
        from skill_seekers.cli.word_scraper import WordToSkillConverter

        self.WordToSkillConverter = WordToSkillConverter
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_missing_docx_file_raises_error(self):
        """extract_docx raises FileNotFoundError for missing file."""
        config = {"name": "test", "docx_path": "/nonexistent/path/test.docx"}
        converter = self.WordToSkillConverter(config)
        with self.assertRaises((FileNotFoundError, RuntimeError)):
            converter.extract_docx()

    def test_invalid_config_raises_error(self):
        """Non-dict config raises TypeError or AttributeError."""
        with self.assertRaises((TypeError, AttributeError)):
            self.WordToSkillConverter("invalid string")

    def test_missing_name_raises_key_error(self):
        """Config without 'name' raises KeyError."""
        with self.assertRaises((KeyError, TypeError)):
            self.WordToSkillConverter({"docx_path": "test.docx"})

    def test_non_docx_file_raises_value_error(self):
        """extract_docx raises ValueError for non-.docx files."""
        # Create a real file with wrong extension
        txt_path = os.path.join(self.temp_dir, "test.txt")
        with open(txt_path, "w") as f:
            f.write("not a docx")
        config = {"name": "test", "docx_path": txt_path}
        converter = self.WordToSkillConverter(config)
        with self.assertRaises(ValueError):
            converter.extract_docx()

    def test_doc_file_raises_value_error(self):
        """extract_docx raises ValueError for .doc (old Word format)."""
        doc_path = os.path.join(self.temp_dir, "test.doc")
        with open(doc_path, "w") as f:
            f.write("not a docx")
        config = {"name": "test", "docx_path": doc_path}
        converter = self.WordToSkillConverter(config)
        with self.assertRaises(ValueError):
            converter.extract_docx()

    def test_no_extension_file_raises_value_error(self):
        """extract_docx raises ValueError for file with no extension."""
        no_ext_path = os.path.join(self.temp_dir, "document")
        with open(no_ext_path, "w") as f:
            f.write("not a docx")
        config = {"name": "test", "docx_path": no_ext_path}
        converter = self.WordToSkillConverter(config)
        with self.assertRaises(ValueError):
            converter.extract_docx()


class TestWordJSONWorkflow(unittest.TestCase):
    """Test building skills from extracted JSON."""

    def setUp(self):
        if not WORD_AVAILABLE:
            self.skipTest("mammoth and python-docx not installed")
        from skill_seekers.cli.word_scraper import WordToSkillConverter

        self.WordToSkillConverter = WordToSkillConverter
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_from_json(self):
        """load_extracted_data loads the JSON correctly."""
        extracted_data = _make_sample_extracted_data(num_sections=3)
        json_path = Path(self.temp_dir) / "extracted.json"
        json_path.write_text(json.dumps(extracted_data, indent=2))

        config = {"name": "test_skill", "docx_path": "test.docx"}
        converter = self.WordToSkillConverter(config)
        converter.load_extracted_data(str(json_path))

        self.assertEqual(converter.extracted_data["total_sections"], 3)
        self.assertEqual(len(converter.extracted_data["pages"]), 3)

    def test_build_from_json_without_extraction(self):
        """JSON workflow skips extract_docx() and goes directly to build."""
        extracted_data = _make_sample_extracted_data(num_sections=2)
        json_path = Path(self.temp_dir) / "extracted.json"
        json_path.write_text(json.dumps(extracted_data))

        config = {"name": "test_skill", "docx_path": "test.docx"}
        converter = self.WordToSkillConverter(config)
        converter.load_extracted_data(str(json_path))

        self.assertIsNotNone(converter.extracted_data)
        self.assertEqual(len(converter.extracted_data["pages"]), 2)

    def test_skill_built_from_json_has_skill_md(self):
        """build_skill() works after load_extracted_data()."""
        extracted_data = _make_sample_extracted_data(num_sections=2)
        json_path = Path(self.temp_dir) / "extracted.json"
        json_path.write_text(json.dumps(extracted_data))

        config = {"name": "test_skill", "docx_path": "test.docx"}
        converter = self.WordToSkillConverter(config)
        converter.skill_dir = str(Path(self.temp_dir) / "test_skill")
        converter.load_extracted_data(str(json_path))
        converter.build_skill()

        skill_md = Path(self.temp_dir) / "test_skill" / "SKILL.md"
        self.assertTrue(skill_md.exists())


class TestWordCLIArguments(unittest.TestCase):
    """Test word subcommand CLI argument parsing via the main CLI."""

    def setUp(self):
        import sys
        from pathlib import Path as P

        sys.path.insert(0, str(P(__file__).parent.parent / "src"))
        from skill_seekers.cli.main import create_parser

        self.parser = create_parser()

    def test_docx_argument_accepted(self):
        """--docx flag is accepted for the word subcommand."""
        args = self.parser.parse_args(["word", "--docx", "test.docx"])
        self.assertEqual(args.docx, "test.docx")

    def test_api_key_accepted(self):
        """--api-key is accepted for word subcommand."""
        args = self.parser.parse_args(["word", "--docx", "test.docx", "--api-key", "sk-ant-test"])
        self.assertEqual(args.api_key, "sk-ant-test")

    def test_enhance_level_accepted(self):
        """--enhance-level is accepted for word subcommand."""
        args = self.parser.parse_args(["word", "--docx", "test.docx", "--enhance-level", "1"])
        self.assertEqual(args.enhance_level, 1)

    def test_enhance_workflow_accepted(self):
        """--enhance-workflow is accepted and stores a list."""
        args = self.parser.parse_args(
            ["word", "--docx", "test.docx", "--enhance-workflow", "minimal"]
        )
        self.assertEqual(args.enhance_workflow, ["minimal"])

    def test_workflow_dry_run_accepted(self):
        """--workflow-dry-run is accepted."""
        args = self.parser.parse_args(["word", "--docx", "test.docx", "--workflow-dry-run"])
        self.assertTrue(args.workflow_dry_run)

    def test_dry_run_accepted(self):
        """--dry-run is accepted for word subcommand."""
        args = self.parser.parse_args(["word", "--docx", "test.docx", "--dry-run"])
        self.assertTrue(args.dry_run)

    def test_from_json_accepted(self):
        """--from-json is accepted."""
        args = self.parser.parse_args(["word", "--from-json", "data.json"])
        self.assertEqual(args.from_json, "data.json")

    def test_name_accepted(self):
        """--name is accepted."""
        args = self.parser.parse_args(["word", "--docx", "test.docx", "--name", "myskill"])
        self.assertEqual(args.name, "myskill")


class TestWordHelperFunctions(unittest.TestCase):
    """Test module-level helper functions."""

    def setUp(self):
        if not WORD_AVAILABLE:
            self.skipTest("mammoth and python-docx not installed")

    def test_build_section_basic(self):
        """_build_section returns a well-formed dict."""
        from skill_seekers.cli.word_scraper import _build_section
        from bs4 import BeautifulSoup

        html = "<p>Hello world.</p><p>Second paragraph.</p>"
        soup = BeautifulSoup(html, "html.parser")
        elements = list(soup.children)

        section = _build_section(1, "Intro", "h1", elements, None)

        self.assertEqual(section["section_number"], 1)
        self.assertEqual(section["heading"], "Intro")
        self.assertEqual(section["heading_level"], "h1")
        self.assertIn("Hello world", section["text"])

    def test_extract_table_from_html(self):
        """_extract_table_from_html extracts headers and rows."""
        from skill_seekers.cli.word_scraper import _extract_table_from_html
        from bs4 import BeautifulSoup

        html = """
        <table>
          <thead><tr><th>Name</th><th>Value</th></tr></thead>
          <tbody>
            <tr><td>foo</td><td>1</td></tr>
            <tr><td>bar</td><td>2</td></tr>
          </tbody>
        </table>"""
        soup = BeautifulSoup(html, "html.parser")
        table_elem = soup.find("table")

        result = _extract_table_from_html(table_elem)

        self.assertIsNotNone(result)
        self.assertEqual(result["headers"], ["Name", "Value"])
        self.assertEqual(len(result["rows"]), 2)
        self.assertIn(["foo", "1"], result["rows"])

    def test_score_code_quality_basic(self):
        """_score_code_quality returns a score in [0, 10]."""
        from skill_seekers.cli.word_scraper import _score_code_quality

        score = _score_code_quality("def foo():\n    return 'bar'\n")
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 10.0)

    def test_score_code_quality_empty(self):
        """_score_code_quality returns 0.0 for empty code."""
        from skill_seekers.cli.word_scraper import _score_code_quality

        self.assertEqual(_score_code_quality(""), 0.0)

    def test_infer_description_from_word_subject(self):
        """infer_description_from_word uses subject field when available."""
        from skill_seekers.cli.word_scraper import infer_description_from_word

        metadata = {"title": "Some Doc", "subject": "Writing API documentation for REST services"}
        desc = infer_description_from_word(metadata, "api_docs")
        self.assertIn("writing api documentation", desc.lower())

    def test_infer_description_from_word_fallback(self):
        """infer_description_from_word falls back to name."""
        from skill_seekers.cli.word_scraper import infer_description_from_word

        desc = infer_description_from_word({}, name="myskill")
        self.assertIn("myskill", desc)


class TestWordSourceDetection(unittest.TestCase):
    """Test .docx source detection in SourceDetector."""

    def test_docx_detected_as_word_type(self):
        """SourceDetector.detect() returns type='word' for .docx files."""
        from skill_seekers.cli.source_detector import SourceDetector

        # Use a path that ends in .docx (doesn't need to exist for detection)
        source_info = SourceDetector.detect("/tmp/test_document.docx")
        self.assertEqual(source_info.type, "word")
        self.assertEqual(source_info.parsed["file_path"], "/tmp/test_document.docx")
        self.assertEqual(source_info.suggested_name, "test_document")

    def test_docx_validation_missing_file(self):
        """validate_source raises ValueError for missing .docx file."""
        from skill_seekers.cli.source_detector import SourceDetector

        source_info = SourceDetector.detect("/tmp/nonexistent_12345.docx")
        with self.assertRaises(ValueError) as ctx:
            SourceDetector.validate_source(source_info)
        self.assertIn("does not exist", str(ctx.exception))

    def test_pdf_still_detected(self):
        """Existing PDF detection is unaffected by Word support."""
        from skill_seekers.cli.source_detector import SourceDetector

        source_info = SourceDetector.detect("/tmp/test.pdf")
        self.assertEqual(source_info.type, "pdf")


if __name__ == "__main__":
    unittest.main()
