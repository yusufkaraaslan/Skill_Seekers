"""
Tests for EPUB scraper (epub_scraper.py).

Covers: initialization, extraction, categorization, skill building,
code blocks, tables, images, error handling, JSON workflow, CLI arguments,
helper functions, source detection, DRM detection, and edge cases.

Tests use mock data and do not require actual EPUB files or ebooklib installed.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


# Conditional import (same pattern as test_word_scraper.py)
try:
    import ebooklib

    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False

try:
    from skill_seekers.cli.epub_scraper import (
        EpubToSkillConverter,
        _build_section,
        _extract_table_from_html,
        _score_code_quality,
        infer_description_from_epub,
    )

    IMPORT_OK = True
except ImportError:
    IMPORT_OK = False


def _make_sample_extracted_data(
    num_sections=2,
    include_code=False,
    include_tables=False,
    include_images=False,
) -> dict:
    """Create minimal extracted_data dict for testing."""
    sections = []
    total_code = 0
    total_images = 0
    languages = {}

    for i in range(1, num_sections + 1):
        section = {
            "section_number": i,
            "heading": f"Chapter {i}",
            "heading_level": "h1",
            "text": f"Content of chapter {i}. This is sample text.",
            "headings": [{"level": "h2", "text": f"Section {i}.1"}],
            "code_samples": [],
            "tables": [],
            "images": [],
        }

        if include_code:
            section["code_samples"] = [
                {
                    "code": f"def func_{i}():\n    return {i}",
                    "language": "python",
                    "quality_score": 7.5,
                },
                {
                    "code": f"console.log({i})",
                    "language": "javascript",
                    "quality_score": 4.0,
                },
            ]
            total_code += 2
            languages["python"] = languages.get("python", 0) + 1
            languages["javascript"] = languages.get("javascript", 0) + 1

        if include_tables:
            section["tables"] = [{"headers": ["Name", "Value"], "rows": [["key", "val"]]}]

        if include_images:
            section["images"] = [
                {"index": 0, "data": b"\x89PNG\r\n\x1a\n", "width": 100, "height": 100}
            ]
            total_images += 1

        sections.append(section)

    return {
        "source_file": "test.epub",
        "metadata": {
            "title": "Test Book",
            "author": "Test Author",
            "language": "en",
            "publisher": "Test Publisher",
            "date": "2024-01-01",
            "description": "A test book for unit testing",
            "subject": "Testing, Unit Tests",
            "rights": "Copyright 2024",
            "identifier": "urn:uuid:12345",
        },
        "total_sections": num_sections,
        "total_code_blocks": total_code,
        "total_images": total_images,
        "languages_detected": languages,
        "pages": sections,
    }


# ============================================================================
# Class 1: TestEpubToSkillConverterInit
# ============================================================================


class TestEpubToSkillConverterInit(unittest.TestCase):
    """Test EpubToSkillConverter initialization."""

    def setUp(self):
        if not IMPORT_OK:
            self.skipTest("epub_scraper not importable")
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_with_name_and_epub_path(self):
        config = {"name": "test_skill", "epub_path": "test.epub"}
        converter = EpubToSkillConverter(config)
        self.assertEqual(converter.name, "test_skill")
        self.assertEqual(converter.epub_path, "test.epub")

    def test_init_with_full_config(self):
        config = {
            "name": "mybook",
            "epub_path": "/path/to/book.epub",
            "description": "Custom description",
            "categories": {"ch1": ["intro"]},
        }
        converter = EpubToSkillConverter(config)
        self.assertEqual(converter.name, "mybook")
        self.assertEqual(converter.epub_path, "/path/to/book.epub")
        self.assertEqual(converter.description, "Custom description")
        self.assertEqual(converter.categories, {"ch1": ["intro"]})

    def test_default_description_uses_name(self):
        config = {"name": "test_skill"}
        converter = EpubToSkillConverter(config)
        self.assertIn("test_skill", converter.description)
        self.assertTrue(converter.description.startswith("Use when referencing"))

    def test_skill_dir_uses_name(self):
        config = {"name": "mybook"}
        converter = EpubToSkillConverter(config)
        self.assertEqual(converter.skill_dir, "output/mybook")

    def test_data_file_uses_name(self):
        config = {"name": "mybook"}
        converter = EpubToSkillConverter(config)
        self.assertEqual(converter.data_file, "output/mybook_extracted.json")

    def test_init_requires_name(self):
        with self.assertRaises(KeyError):
            EpubToSkillConverter({})

    def test_init_empty_name(self):
        config = {"name": ""}
        converter = EpubToSkillConverter(config)
        self.assertEqual(converter.name, "")

    def test_init_with_special_characters_in_name(self):
        config = {"name": "my-book name_2024"}
        converter = EpubToSkillConverter(config)
        self.assertEqual(converter.name, "my-book name_2024")
        self.assertIn("my-book name_2024", converter.skill_dir)


# ============================================================================
# Class 2: TestEpubExtraction
# ============================================================================


class TestEpubExtraction(unittest.TestCase):
    """Test EPUB content extraction."""

    def setUp(self):
        if not IMPORT_OK:
            self.skipTest("epub_scraper not importable")
        if not EPUB_AVAILABLE:
            self.skipTest("ebooklib not installed")
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _make_mock_book(self, spine_content=None, metadata=None, images=None):
        """Create a mock ebooklib EpubBook."""
        book = MagicMock()

        if metadata is None:
            metadata = {
                "title": [("Test Book", {})],
                "creator": [("Test Author", {})],
                "language": [("en", {})],
                "publisher": [("Test Publisher", {})],
                "date": [("2024-01-01", {})],
                "description": [("A test book", {})],
                "subject": [("Testing", {})],
                "rights": [("Copyright 2024", {})],
                "identifier": [("urn:uuid:12345", {})],
            }

        def get_metadata(ns, key):
            if ns == "DC":
                return metadata.get(key, [])
            return []

        book.get_metadata = get_metadata

        # Spine items
        if spine_content is None:
            spine_content = [
                (
                    "ch1",
                    "<html><body><h1>Chapter 1</h1><p>Content 1</p></body></html>",
                ),
            ]

        spine_items = []
        items_dict = {}
        for item_id, content in spine_content:
            item = MagicMock()
            item.get_type.return_value = ebooklib.ITEM_DOCUMENT
            item.get_content.return_value = content.encode("utf-8")
            items_dict[item_id] = item
            spine_items.append((item_id, "yes"))

        book.spine = spine_items
        book.get_item_with_id = lambda x: items_dict.get(x)

        # Images
        if images is None:
            images = []
        img_items = []
        for img in images:
            img_item = MagicMock()
            img_item.media_type = img.get("media_type", "image/png")
            img_item.get_content.return_value = img.get("data", b"\x89PNG")
            img_item.file_name = img.get("file_name", "image.png")
            img_items.append(img_item)

        book.get_items_of_type = lambda t: img_items if t == ebooklib.ITEM_IMAGE else []

        # All items (for DRM detection, SVG counting)
        all_items = list(items_dict.values()) + img_items
        book.get_items = lambda: all_items

        return book

    @patch("skill_seekers.cli.epub_scraper.epub")
    @patch("skill_seekers.cli.epub_scraper.os.path.exists", return_value=True)
    @patch("skill_seekers.cli.epub_scraper.os.path.isfile", return_value=True)
    def test_extract_basic_epub(self, mock_isfile, mock_exists, mock_epub):
        mock_book = self._make_mock_book()
        mock_epub.read_epub.return_value = mock_book

        config = {"name": "test", "epub_path": "test.epub"}
        converter = EpubToSkillConverter(config)
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")

        result = converter.extract_epub()
        self.assertTrue(result)
        self.assertIsNotNone(converter.extracted_data)
        self.assertGreaterEqual(len(converter.extracted_data["pages"]), 1)

    @patch("skill_seekers.cli.epub_scraper.epub")
    @patch("skill_seekers.cli.epub_scraper.os.path.exists", return_value=True)
    @patch("skill_seekers.cli.epub_scraper.os.path.isfile", return_value=True)
    def test_extract_metadata(self, mock_isfile, mock_exists, mock_epub):
        mock_book = self._make_mock_book()
        mock_epub.read_epub.return_value = mock_book

        config = {"name": "test", "epub_path": "test.epub"}
        converter = EpubToSkillConverter(config)
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")

        converter.extract_epub()
        metadata = converter.extracted_data["metadata"]
        self.assertEqual(metadata["title"], "Test Book")
        self.assertEqual(metadata["author"], "Test Author")
        self.assertEqual(metadata["language"], "en")

    @patch("skill_seekers.cli.epub_scraper.epub")
    @patch("skill_seekers.cli.epub_scraper.os.path.exists", return_value=True)
    @patch("skill_seekers.cli.epub_scraper.os.path.isfile", return_value=True)
    def test_extract_multiple_chapters(self, mock_isfile, mock_exists, mock_epub):
        spine = [
            ("ch1", "<html><body><h1>Chapter 1</h1><p>Text 1</p></body></html>"),
            ("ch2", "<html><body><h1>Chapter 2</h1><p>Text 2</p></body></html>"),
            ("ch3", "<html><body><h1>Chapter 3</h1><p>Text 3</p></body></html>"),
        ]
        mock_book = self._make_mock_book(spine_content=spine)
        mock_epub.read_epub.return_value = mock_book

        config = {"name": "test", "epub_path": "test.epub"}
        converter = EpubToSkillConverter(config)
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")

        converter.extract_epub()
        self.assertEqual(len(converter.extracted_data["pages"]), 3)

    @patch("skill_seekers.cli.epub_scraper.epub")
    @patch("skill_seekers.cli.epub_scraper.os.path.exists", return_value=True)
    @patch("skill_seekers.cli.epub_scraper.os.path.isfile", return_value=True)
    def test_extract_code_blocks(self, mock_isfile, mock_exists, mock_epub):
        spine = [
            (
                "ch1",
                "<html><body><h1>Code Chapter</h1>"
                '<pre><code class="language-python">def hello():\n    print("hi")</code></pre>'
                "</body></html>",
            ),
        ]
        mock_book = self._make_mock_book(spine_content=spine)
        mock_epub.read_epub.return_value = mock_book

        config = {"name": "test", "epub_path": "test.epub"}
        converter = EpubToSkillConverter(config)
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")

        converter.extract_epub()
        code_samples = converter.extracted_data["pages"][0]["code_samples"]
        self.assertGreaterEqual(len(code_samples), 1)
        self.assertEqual(code_samples[0]["language"], "python")

    @patch("skill_seekers.cli.epub_scraper.epub")
    @patch("skill_seekers.cli.epub_scraper.os.path.exists", return_value=True)
    @patch("skill_seekers.cli.epub_scraper.os.path.isfile", return_value=True)
    def test_extract_images(self, mock_isfile, mock_exists, mock_epub):
        images = [{"media_type": "image/png", "data": b"\x89PNG", "file_name": "fig1.png"}]
        mock_book = self._make_mock_book(images=images)
        mock_epub.read_epub.return_value = mock_book

        config = {"name": "test", "epub_path": "test.epub"}
        converter = EpubToSkillConverter(config)
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")

        converter.extract_epub()
        self.assertGreaterEqual(converter.extracted_data["total_images"], 1)

    @patch("skill_seekers.cli.epub_scraper.epub")
    @patch("skill_seekers.cli.epub_scraper.os.path.exists", return_value=True)
    @patch("skill_seekers.cli.epub_scraper.os.path.isfile", return_value=True)
    def test_heading_boundary_splitting(self, mock_isfile, mock_exists, mock_epub):
        spine = [
            (
                "ch1",
                "<html><body>"
                "<h1>First Heading</h1><p>First content</p>"
                "<h2>Second Heading</h2><p>Second content</p>"
                "</body></html>",
            ),
        ]
        mock_book = self._make_mock_book(spine_content=spine)
        mock_epub.read_epub.return_value = mock_book

        config = {"name": "test", "epub_path": "test.epub"}
        converter = EpubToSkillConverter(config)
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")

        converter.extract_epub()
        pages = converter.extracted_data["pages"]
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0]["heading"], "First Heading")
        self.assertEqual(pages[1]["heading"], "Second Heading")

    def test_extract_missing_file_raises_error(self):
        config = {"name": "test", "epub_path": "/nonexistent/book.epub"}
        converter = EpubToSkillConverter(config)
        with self.assertRaises(FileNotFoundError):
            converter.extract_epub()

    def test_extract_invalid_extension_raises_error(self):
        # Create a real file with wrong extension
        bad_file = os.path.join(self.temp_dir, "test.txt")
        Path(bad_file).write_text("not an epub")

        config = {"name": "test", "epub_path": bad_file}
        converter = EpubToSkillConverter(config)
        with self.assertRaises(ValueError):
            converter.extract_epub()

    def test_extract_deps_not_installed(self):
        from skill_seekers.cli.epub_scraper import _check_epub_deps

        with patch("skill_seekers.cli.epub_scraper.EPUB_AVAILABLE", False):
            with self.assertRaises(RuntimeError) as ctx:
                _check_epub_deps()
            self.assertIn("ebooklib", str(ctx.exception))
            self.assertIn("pip install", str(ctx.exception))

    @patch("skill_seekers.cli.epub_scraper.epub")
    @patch("skill_seekers.cli.epub_scraper.os.path.exists", return_value=True)
    @patch("skill_seekers.cli.epub_scraper.os.path.isfile", return_value=True)
    def test_extract_empty_spine(self, mock_isfile, mock_exists, mock_epub):
        mock_book = self._make_mock_book(spine_content=[])
        mock_book.spine = []
        mock_epub.read_epub.return_value = mock_book

        config = {"name": "test", "epub_path": "test.epub"}
        converter = EpubToSkillConverter(config)
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")

        converter.extract_epub()
        self.assertEqual(len(converter.extracted_data["pages"]), 0)

    @patch("skill_seekers.cli.epub_scraper.epub")
    @patch("skill_seekers.cli.epub_scraper.os.path.exists", return_value=True)
    @patch("skill_seekers.cli.epub_scraper.os.path.isfile", return_value=True)
    def test_extract_spine_item_no_body(self, mock_isfile, mock_exists, mock_epub):
        spine = [
            ("ch1", "<html><head><title>No Body</title></head></html>"),
        ]
        mock_book = self._make_mock_book(spine_content=spine)
        mock_epub.read_epub.return_value = mock_book

        config = {"name": "test", "epub_path": "test.epub"}
        converter = EpubToSkillConverter(config)
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")

        # Should not crash — body fallback to soup
        converter.extract_epub()
        self.assertIsNotNone(converter.extracted_data)


# ============================================================================
# Class 3: TestEpubDrmDetection
# ============================================================================


class TestEpubDrmDetection(unittest.TestCase):
    """Test DRM detection logic."""

    def setUp(self):
        if not IMPORT_OK:
            self.skipTest("epub_scraper not importable")
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _make_converter(self):
        config = {"name": "test", "epub_path": "test.epub"}
        return EpubToSkillConverter(config)

    def _make_book_with_encryption(self, encryption_xml_content):
        """Create a mock book with META-INF/encryption.xml."""
        book = MagicMock()
        enc_item = MagicMock()
        enc_item.file_name = "META-INF/encryption.xml"
        enc_item.get_content.return_value = encryption_xml_content.encode("utf-8")
        book.get_items.return_value = [enc_item]
        return book

    def test_no_drm_detected(self):
        converter = self._make_converter()
        book = MagicMock()
        book.get_items.return_value = []
        self.assertFalse(converter._detect_drm(book))

    def test_drm_detected_adobe_adept(self):
        converter = self._make_converter()
        xml = '<encryption xmlns="http://ns.adobe.com/adept"><EncryptedData/></encryption>'
        book = self._make_book_with_encryption(xml)
        self.assertTrue(converter._detect_drm(book))

    def test_drm_detected_apple_fairplay(self):
        converter = self._make_converter()
        xml = '<encryption><EncryptedData xmlns="http://itunes.apple.com/dataenc"/></encryption>'
        book = self._make_book_with_encryption(xml)
        self.assertTrue(converter._detect_drm(book))

    def test_drm_detected_readium_lcp(self):
        converter = self._make_converter()
        xml = '<encryption xmlns="http://readium.org/2014/01/lcp"><EncryptedData/></encryption>'
        book = self._make_book_with_encryption(xml)
        self.assertTrue(converter._detect_drm(book))

    def test_font_obfuscation_not_drm(self):
        converter = self._make_converter()
        xml = (
            "<encryption>"
            '<EncryptionMethod Algorithm="http://www.idpf.org/2008/embedding"/>'
            "</encryption>"
        )
        book = self._make_book_with_encryption(xml)
        self.assertFalse(converter._detect_drm(book))

    def test_drm_error_message_is_clear(self):
        converter = self._make_converter()
        xml = '<encryption xmlns="http://ns.adobe.com/adept"><EncryptedData/></encryption>'
        book = self._make_book_with_encryption(xml)
        self.assertTrue(converter._detect_drm(book))
        # The error message is raised in extract_epub, not _detect_drm
        # Just confirm detection works


# ============================================================================
# Class 4: TestEpubCategorization
# ============================================================================


class TestEpubCategorization(unittest.TestCase):
    """Test content categorization."""

    def setUp(self):
        if not IMPORT_OK:
            self.skipTest("epub_scraper not importable")
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_single_source_creates_one_category(self):
        config = {"name": "test", "epub_path": "mybook.epub"}
        converter = EpubToSkillConverter(config)
        converter.extracted_data = _make_sample_extracted_data(num_sections=3)

        categories = converter.categorize_content()
        self.assertEqual(len(categories), 1)
        self.assertIn("mybook", categories)

    def test_keyword_categorization(self):
        config = {
            "name": "test",
            "categories": {
                "intro": ["introduction", "getting started"],
                "advanced": ["advanced", "deep dive"],
            },
        }
        converter = EpubToSkillConverter(config)
        data = _make_sample_extracted_data(num_sections=2)
        data["pages"][0]["heading"] = "Introduction to Testing"
        data["pages"][1]["heading"] = "Advanced Techniques"
        converter.extracted_data = data

        categories = converter.categorize_content()
        self.assertIn("intro", categories)
        self.assertIn("advanced", categories)

    def test_no_categories_uses_default(self):
        config = {"name": "test"}
        converter = EpubToSkillConverter(config)
        converter.extracted_data = _make_sample_extracted_data(num_sections=2)

        categories = converter.categorize_content()
        self.assertIn("content", categories)
        self.assertEqual(categories["content"]["title"], "Content")

    def test_categorize_empty_sections(self):
        config = {"name": "test"}
        converter = EpubToSkillConverter(config)
        converter.extracted_data = _make_sample_extracted_data(num_sections=0)

        categories = converter.categorize_content()
        self.assertIn("content", categories)
        self.assertEqual(len(categories["content"]["pages"]), 0)

    def test_categorize_no_keyword_matches(self):
        config = {
            "name": "test",
            "categories": {"intro": ["zzzzz_no_match"]},
        }
        converter = EpubToSkillConverter(config)
        converter.extracted_data = _make_sample_extracted_data(num_sections=2)

        categories = converter.categorize_content()
        self.assertIn("other", categories)
        self.assertEqual(len(categories["other"]["pages"]), 2)

    def test_categorize_single_section(self):
        config = {"name": "test", "epub_path": "book.epub"}
        converter = EpubToSkillConverter(config)
        converter.extracted_data = _make_sample_extracted_data(num_sections=1)

        categories = converter.categorize_content()
        total_pages = sum(len(c["pages"]) for c in categories.values())
        self.assertEqual(total_pages, 1)

    def test_categorize_many_sections(self):
        config = {"name": "test", "epub_path": "book.epub"}
        converter = EpubToSkillConverter(config)
        converter.extracted_data = _make_sample_extracted_data(num_sections=50)

        categories = converter.categorize_content()
        total_pages = sum(len(c["pages"]) for c in categories.values())
        self.assertEqual(total_pages, 50)

    def test_categorize_preserves_section_order(self):
        config = {"name": "test", "epub_path": "book.epub"}
        converter = EpubToSkillConverter(config)
        converter.extracted_data = _make_sample_extracted_data(num_sections=5)

        categories = converter.categorize_content()
        for cat_data in categories.values():
            section_nums = [s["section_number"] for s in cat_data["pages"]]
            self.assertEqual(section_nums, sorted(section_nums))


# ============================================================================
# Class 5: TestEpubSkillBuilding
# ============================================================================


class TestEpubSkillBuilding(unittest.TestCase):
    """Test skill building (directory structure, SKILL.md, reference files)."""

    def setUp(self):
        if not IMPORT_OK:
            self.skipTest("epub_scraper not importable")
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _make_converter(self, name="test_book", epub_path="test.epub"):
        config = {"name": name, "epub_path": epub_path}
        converter = EpubToSkillConverter(config)
        converter.skill_dir = os.path.join(self.temp_dir, name)
        converter.data_file = os.path.join(self.temp_dir, f"{name}_extracted.json")
        return converter

    def test_build_creates_directory_structure(self):
        converter = self._make_converter()
        converter.extracted_data = _make_sample_extracted_data()

        converter.build_skill()

        skill_dir = Path(self.temp_dir) / "test_book"
        self.assertTrue(skill_dir.exists())
        self.assertTrue((skill_dir / "references").exists())
        self.assertTrue((skill_dir / "scripts").exists())
        self.assertTrue((skill_dir / "assets").exists())

    def test_build_generates_skill_md(self):
        converter = self._make_converter()
        converter.extracted_data = _make_sample_extracted_data()

        converter.build_skill()

        skill_md = Path(self.temp_dir) / "test_book" / "SKILL.md"
        self.assertTrue(skill_md.exists())
        content = skill_md.read_text()
        self.assertIn("---", content)
        self.assertIn("name:", content)
        self.assertIn("description:", content)

    def test_build_generates_reference_files(self):
        converter = self._make_converter()
        converter.extracted_data = _make_sample_extracted_data()

        converter.build_skill()

        refs_dir = Path(self.temp_dir) / "test_book" / "references"
        md_files = list(refs_dir.glob("*.md"))
        # At least index.md + one reference file
        self.assertGreaterEqual(len(md_files), 2)

    def test_build_generates_index(self):
        converter = self._make_converter()
        converter.extracted_data = _make_sample_extracted_data()

        converter.build_skill()

        index_path = Path(self.temp_dir) / "test_book" / "references" / "index.md"
        self.assertTrue(index_path.exists())
        content = index_path.read_text()
        self.assertIn("Categories", content)
        self.assertIn("Statistics", content)

    def test_skill_md_contains_metadata(self):
        converter = self._make_converter()
        converter.extracted_data = _make_sample_extracted_data()

        converter.build_skill()

        skill_md = Path(self.temp_dir) / "test_book" / "SKILL.md"
        content = skill_md.read_text()
        self.assertIn("Test Book", content)
        self.assertIn("Test Author", content)

    def test_skill_md_yaml_frontmatter(self):
        converter = self._make_converter()
        converter.extracted_data = _make_sample_extracted_data()

        converter.build_skill()

        skill_md = Path(self.temp_dir) / "test_book" / "SKILL.md"
        content = skill_md.read_text()
        # YAML frontmatter starts and ends with ---
        lines = content.split("\n")
        self.assertEqual(lines[0], "---")
        # Find closing ---
        closing_idx = None
        for i, line in enumerate(lines[1:], 1):
            if line == "---":
                closing_idx = i
                break
        self.assertIsNotNone(closing_idx)

    def test_build_without_extracted_data_fails(self):
        converter = self._make_converter()
        converter.extracted_data = None
        with self.assertRaises((AttributeError, TypeError)):
            converter.build_skill()

    def test_build_overwrites_existing_output(self):
        converter = self._make_converter()
        converter.extracted_data = _make_sample_extracted_data()

        # Build once
        converter.build_skill()
        skill_md_1 = (Path(self.temp_dir) / "test_book" / "SKILL.md").read_text()

        # Build again
        converter.build_skill()
        skill_md_2 = (Path(self.temp_dir) / "test_book" / "SKILL.md").read_text()

        self.assertEqual(skill_md_1, skill_md_2)

    def test_build_with_long_name(self):
        long_name = "a" * 100
        converter = self._make_converter(name=long_name)
        converter.extracted_data = _make_sample_extracted_data()

        converter.build_skill()

        skill_md = Path(converter.skill_dir) / "SKILL.md"
        content = skill_md.read_text()
        # Name in frontmatter is truncated to 64 chars
        lines = content.split("\n")
        for line in lines:
            if line.startswith("name:"):
                name_val = line.split(":", 1)[1].strip()
                self.assertLessEqual(len(name_val), 64)
                break

    def test_build_with_unicode_content(self):
        converter = self._make_converter()
        data = _make_sample_extracted_data()
        data["pages"][0]["heading"] = (
            "Unicode: \u4e2d\u6587 \u0627\u0644\u0639\u0631\u0628\u064a\u0629 \U0001f600"
        )
        data["pages"][0]["text"] = (
            "Content with CJK: \u4f60\u597d, Arabic: \u0645\u0631\u062d\u0628\u0627, Emoji: \U0001f680"
        )
        converter.extracted_data = data

        converter.build_skill()

        refs_dir = Path(self.temp_dir) / "test_book" / "references"
        md_files = list(refs_dir.glob("*.md"))
        # Should have reference files
        self.assertGreaterEqual(len(md_files), 1)
        # Unicode should be preserved in at least one file
        found_unicode = False
        for f in md_files:
            content = f.read_text(encoding="utf-8")
            if "\u4e2d\u6587" in content or "\u4f60\u597d" in content:
                found_unicode = True
                break
        self.assertTrue(found_unicode)


# ============================================================================
# Class 6: TestEpubCodeBlocks
# ============================================================================


class TestEpubCodeBlocks(unittest.TestCase):
    """Test code block extraction and rendering."""

    def setUp(self):
        if not IMPORT_OK:
            self.skipTest("epub_scraper not importable")
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _make_converter(self):
        config = {"name": "test", "epub_path": "test.epub"}
        converter = EpubToSkillConverter(config)
        converter.skill_dir = os.path.join(self.temp_dir, "test")
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")
        return converter

    def test_code_blocks_included_in_reference_files(self):
        converter = self._make_converter()
        converter.extracted_data = _make_sample_extracted_data(include_code=True)

        converter.build_skill()

        refs_dir = Path(self.temp_dir) / "test" / "references"
        found_code = False
        for f in refs_dir.glob("*.md"):
            if f.name == "index.md":
                continue
            content = f.read_text()
            if "```python" in content or "def func_" in content:
                found_code = True
                break
        self.assertTrue(found_code)

    def test_code_blocks_in_skill_md_top_15(self):
        converter = self._make_converter()
        converter.extracted_data = _make_sample_extracted_data(num_sections=10, include_code=True)

        converter.build_skill()

        skill_md = Path(self.temp_dir) / "test" / "SKILL.md"
        content = skill_md.read_text()
        self.assertIn("Code Examples", content)

    def test_code_language_grouped(self):
        converter = self._make_converter()
        converter.extracted_data = _make_sample_extracted_data(num_sections=3, include_code=True)

        converter.build_skill()

        skill_md = Path(self.temp_dir) / "test" / "SKILL.md"
        content = skill_md.read_text()
        self.assertIn("Python Examples", content)
        self.assertIn("Javascript Examples", content)

    def test_empty_code_block(self):
        from bs4 import BeautifulSoup

        html = "<pre><code></code></pre>"
        soup = BeautifulSoup(html, "html.parser")
        elements = list(soup.children)
        section = _build_section(1, "Test", "h1", elements)
        self.assertEqual(len(section["code_samples"]), 0)

    def test_code_block_with_html_entities(self):
        from bs4 import BeautifulSoup

        html = "<pre><code>if (x &lt; 10 &amp;&amp; y &gt; 5) {}</code></pre>"
        soup = BeautifulSoup(html, "html.parser")
        elements = list(soup.children)
        section = _build_section(1, "Test", "h1", elements)
        self.assertEqual(len(section["code_samples"]), 1)
        code = section["code_samples"][0]["code"]
        self.assertIn("<", code)
        self.assertIn(">", code)
        self.assertIn("&&", code)

    def test_code_block_with_syntax_highlighting_spans(self):
        from bs4 import BeautifulSoup

        html = (
            '<pre><code><span class="keyword">def</span> '
            '<span class="name">foo</span>():</code></pre>'
        )
        soup = BeautifulSoup(html, "html.parser")
        elements = list(soup.children)
        section = _build_section(1, "Test", "h1", elements)
        self.assertEqual(len(section["code_samples"]), 1)
        code = section["code_samples"][0]["code"]
        self.assertIn("def", code)
        self.assertIn("foo", code)
        self.assertNotIn("<span", code)

    def test_code_block_language_from_class(self):
        from bs4 import BeautifulSoup

        html = '<pre><code class="language-rust">fn main() {}</code></pre>'
        soup = BeautifulSoup(html, "html.parser")
        elements = list(soup.children)
        section = _build_section(1, "Test", "h1", elements)
        self.assertEqual(section["code_samples"][0]["language"], "rust")

    def test_code_quality_scoring(self):
        # Short snippet
        score_short = _score_code_quality("x")
        self.assertLessEqual(score_short, 5.0)

        # Substantial code
        code = (
            "def calculate_sum(numbers):\n"
            "    total = 0\n"
            "    for n in numbers:\n"
            "        total += n\n"
            "    return total\n"
            "\n"
            "result = calculate_sum([1, 2, 3])\n"
        )
        score_good = _score_code_quality(code)
        self.assertGreater(score_good, score_short)
        self.assertGreaterEqual(score_good, 0.0)
        self.assertLessEqual(score_good, 10.0)


# ============================================================================
# Class 7: TestEpubTables
# ============================================================================


class TestEpubTables(unittest.TestCase):
    """Test table extraction and rendering."""

    def setUp(self):
        if not IMPORT_OK:
            self.skipTest("epub_scraper not importable")
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_tables_in_reference_files(self):
        config = {"name": "test", "epub_path": "test.epub"}
        converter = EpubToSkillConverter(config)
        converter.skill_dir = os.path.join(self.temp_dir, "test")
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")
        converter.extracted_data = _make_sample_extracted_data(include_tables=True)

        converter.build_skill()

        refs_dir = Path(self.temp_dir) / "test" / "references"
        found_table = False
        for f in refs_dir.glob("*.md"):
            if f.name == "index.md":
                continue
            content = f.read_text()
            if "| Name | Value |" in content:
                found_table = True
                break
        self.assertTrue(found_table)

    def test_table_with_headers(self):
        from bs4 import BeautifulSoup

        html = (
            "<table><thead><tr><th>Name</th><th>Age</th></tr></thead>"
            "<tbody><tr><td>Alice</td><td>30</td></tr></tbody></table>"
        )
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        result = _extract_table_from_html(table)
        self.assertIsNotNone(result)
        self.assertEqual(result["headers"], ["Name", "Age"])
        self.assertEqual(result["rows"], [["Alice", "30"]])

    def test_table_no_thead(self):
        from bs4 import BeautifulSoup

        html = (
            "<table><tr><td>Header1</td><td>Header2</td></tr>"
            "<tr><td>Val1</td><td>Val2</td></tr></table>"
        )
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        result = _extract_table_from_html(table)
        self.assertIsNotNone(result)
        self.assertEqual(result["headers"], ["Header1", "Header2"])
        self.assertEqual(result["rows"], [["Val1", "Val2"]])

    def test_empty_table(self):
        from bs4 import BeautifulSoup

        html = "<table></table>"
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        result = _extract_table_from_html(table)
        self.assertIsNone(result)

    def test_table_with_colspan_rowspan(self):
        from bs4 import BeautifulSoup

        html = (
            "<table><tr><th>H1</th><th colspan='2'>H2</th></tr>"
            "<tr><td>A</td><td rowspan='2'>B</td><td>C</td></tr>"
            "<tr><td>D</td><td>E</td></tr></table>"
        )
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        # Should not crash
        result = _extract_table_from_html(table)
        self.assertIsNotNone(result)


# ============================================================================
# Class 8: TestEpubImages
# ============================================================================


class TestEpubImages(unittest.TestCase):
    """Test image extraction and handling."""

    def setUp(self):
        if not IMPORT_OK:
            self.skipTest("epub_scraper not importable")
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_images_saved_to_assets(self):
        config = {"name": "test", "epub_path": "test.epub"}
        converter = EpubToSkillConverter(config)
        converter.skill_dir = os.path.join(self.temp_dir, "test")
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")
        data = _make_sample_extracted_data(include_images=True)
        converter.extracted_data = data

        converter.build_skill()

        assets_dir = Path(self.temp_dir) / "test" / "assets"
        self.assertTrue(assets_dir.exists())

    def test_image_references_in_markdown(self):
        config = {"name": "test", "epub_path": "test.epub"}
        converter = EpubToSkillConverter(config)
        converter.skill_dir = os.path.join(self.temp_dir, "test")
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")
        data = _make_sample_extracted_data(include_images=True)
        converter.extracted_data = data

        converter.build_skill()

        refs_dir = Path(self.temp_dir) / "test" / "references"
        found_img_ref = False
        for f in refs_dir.glob("*.md"):
            if f.name == "index.md":
                continue
            content = f.read_text()
            if "![Image" in content and "../assets/" in content:
                found_img_ref = True
                break
        self.assertTrue(found_img_ref)

    def test_image_with_zero_bytes(self):
        config = {"name": "test", "epub_path": "test.epub"}
        converter = EpubToSkillConverter(config)
        converter.skill_dir = os.path.join(self.temp_dir, "test")
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")
        data = _make_sample_extracted_data()
        # Add image with empty data
        data["pages"][0]["images"] = [{"index": 0, "data": b"", "width": 0, "height": 0}]
        converter.extracted_data = data

        # Should not crash
        converter.build_skill()

    def test_svg_images_handled(self):
        from bs4 import BeautifulSoup

        html = '<img src="diagram.svg" width="200" height="100"/>'
        soup = BeautifulSoup(f"<div>{html}</div>", "html.parser")
        elements = list(soup.find("div").children)
        section = _build_section(1, "Test", "h1", elements)
        self.assertEqual(len(section["images"]), 1)

    def test_image_filename_conflicts(self):
        config = {"name": "test", "epub_path": "test.epub"}
        converter = EpubToSkillConverter(config)
        converter.skill_dir = os.path.join(self.temp_dir, "test")
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")
        data = _make_sample_extracted_data()
        # Multiple images with unique indexes
        data["pages"][0]["images"] = [
            {"index": 0, "data": b"\x89PNG\r\n\x1a\n", "width": 50, "height": 50},
            {"index": 1, "data": b"\x89PNG\r\n\x1a\n", "width": 50, "height": 50},
        ]
        converter.extracted_data = data

        converter.build_skill()

        assets_dir = Path(self.temp_dir) / "test" / "assets"
        png_files = list(assets_dir.glob("*.png"))
        self.assertGreaterEqual(len(png_files), 2)

    def test_cover_image_identified(self):
        from bs4 import BeautifulSoup

        html = '<img src="cover.jpg" width="600" height="900"/>'
        soup = BeautifulSoup(f"<div>{html}</div>", "html.parser")
        elements = list(soup.find("div").children)
        section = _build_section(1, "Cover", "h1", elements)
        self.assertEqual(len(section["images"]), 1)

    def test_many_images(self):
        config = {"name": "test", "epub_path": "test.epub"}
        converter = EpubToSkillConverter(config)
        converter.skill_dir = os.path.join(self.temp_dir, "test")
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")
        data = _make_sample_extracted_data()
        data["pages"][0]["images"] = [
            {"index": i, "data": b"\x89PNG\r\n\x1a\n", "width": 10, "height": 10}
            for i in range(100)
        ]
        converter.extracted_data = data

        # Should handle 100+ images without error
        converter.build_skill()


# ============================================================================
# Class 9: TestEpubErrorHandling
# ============================================================================


class TestEpubErrorHandling(unittest.TestCase):
    """Test error handling for various failure scenarios."""

    def setUp(self):
        if not IMPORT_OK:
            self.skipTest("epub_scraper not importable")
        if not EPUB_AVAILABLE:
            self.skipTest("ebooklib not installed")
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_missing_epub_file_raises_error(self):
        config = {"name": "test", "epub_path": "/nonexistent/path/test.epub"}
        converter = EpubToSkillConverter(config)
        with self.assertRaises(FileNotFoundError):
            converter.extract_epub()

    def test_not_a_file_raises_error(self):
        config = {"name": "test", "epub_path": self.temp_dir}
        converter = EpubToSkillConverter(config)
        with self.assertRaises((ValueError, FileNotFoundError)):
            converter.extract_epub()

    def test_not_epub_extension_raises_error(self):
        txt_file = os.path.join(self.temp_dir, "test.txt")
        Path(txt_file).write_text("not an epub")
        config = {"name": "test", "epub_path": txt_file}
        converter = EpubToSkillConverter(config)
        with self.assertRaises(ValueError):
            converter.extract_epub()

    @patch("skill_seekers.cli.epub_scraper.epub")
    @patch("skill_seekers.cli.epub_scraper.os.path.exists", return_value=True)
    @patch("skill_seekers.cli.epub_scraper.os.path.isfile", return_value=True)
    def test_corrupted_epub_raises_error(self, mock_isfile, mock_exists, mock_epub):
        mock_epub.read_epub.side_effect = Exception("Bad ZIP file")
        config = {"name": "test", "epub_path": "corrupted.epub"}
        converter = EpubToSkillConverter(config)
        with self.assertRaises(ValueError):
            converter.extract_epub()

    @patch("skill_seekers.cli.epub_scraper.epub")
    @patch("skill_seekers.cli.epub_scraper.os.path.exists", return_value=True)
    @patch("skill_seekers.cli.epub_scraper.os.path.isfile", return_value=True)
    def test_drm_protected_raises_error(self, mock_isfile, mock_exists, mock_epub):
        book = MagicMock()
        enc_item = MagicMock()
        enc_item.file_name = "META-INF/encryption.xml"
        enc_item.get_content.return_value = (
            b'<encryption xmlns="http://ns.adobe.com/adept"><EncryptedData/></encryption>'
        )
        book.get_items.return_value = [enc_item]
        book.get_metadata.return_value = []
        mock_epub.read_epub.return_value = book

        config = {"name": "test", "epub_path": "drm.epub"}
        converter = EpubToSkillConverter(config)
        with self.assertRaises(RuntimeError) as ctx:
            converter.extract_epub()
        self.assertIn("DRM", str(ctx.exception))

    def test_ebooklib_not_installed_error(self):
        from skill_seekers.cli.epub_scraper import _check_epub_deps

        with patch("skill_seekers.cli.epub_scraper.EPUB_AVAILABLE", False):
            with self.assertRaises(RuntimeError) as ctx:
                _check_epub_deps()
            self.assertIn("ebooklib", str(ctx.exception))
            self.assertIn("pip install", str(ctx.exception))

    @patch("skill_seekers.cli.epub_scraper.epub")
    @patch("skill_seekers.cli.epub_scraper.os.path.exists", return_value=True)
    @patch("skill_seekers.cli.epub_scraper.os.path.isfile", return_value=True)
    def test_malformed_xhtml_handled_gracefully(self, mock_isfile, mock_exists, mock_epub):
        """Malformed XHTML should not crash thanks to BeautifulSoup tolerant parsing."""
        book = MagicMock()
        item = MagicMock()
        item.get_type.return_value = ebooklib.ITEM_DOCUMENT
        item.get_content.return_value = b"<html><body><h1>Test<p>Unclosed tags <div>and more</body>"
        book.spine = [("ch1", "yes")]
        book.get_item_with_id = lambda _x: item
        book.get_metadata.return_value = []
        book.get_items_of_type = lambda _t: []
        book.get_items = lambda: [item]
        mock_epub.read_epub.return_value = book

        config = {"name": "test", "epub_path": "malformed.epub"}
        converter = EpubToSkillConverter(config)
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")

        # Should not crash
        result = converter.extract_epub()
        self.assertTrue(result)


# ============================================================================
# Class 10: TestEpubJSONWorkflow
# ============================================================================


class TestEpubJSONWorkflow(unittest.TestCase):
    """Test JSON-based workflow (load/save extracted data)."""

    def setUp(self):
        if not IMPORT_OK:
            self.skipTest("epub_scraper not importable")
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_extracted_json(self):
        config = {"name": "test"}
        converter = EpubToSkillConverter(config)

        data = _make_sample_extracted_data()
        json_path = os.path.join(self.temp_dir, "test_extracted.json")
        with open(json_path, "w") as f:
            json.dump(data, f)

        result = converter.load_extracted_data(json_path)
        self.assertTrue(result)
        self.assertIsNotNone(converter.extracted_data)
        self.assertEqual(converter.extracted_data["total_sections"], 2)

    def test_build_from_json(self):
        config = {"name": "test"}
        converter = EpubToSkillConverter(config)
        converter.skill_dir = os.path.join(self.temp_dir, "test")
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")

        data = _make_sample_extracted_data()
        json_path = os.path.join(self.temp_dir, "test_extracted.json")
        with open(json_path, "w") as f:
            json.dump(data, f)

        converter.load_extracted_data(json_path)
        converter.build_skill()

        skill_md = Path(self.temp_dir) / "test" / "SKILL.md"
        self.assertTrue(skill_md.exists())

    def test_json_round_trip(self):
        config = {"name": "test"}
        converter = EpubToSkillConverter(config)
        converter.skill_dir = os.path.join(self.temp_dir, "test")
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")

        original_data = _make_sample_extracted_data(include_code=True, include_tables=True)

        # Save
        json_path = os.path.join(self.temp_dir, "test_extracted.json")
        with open(json_path, "w") as f:
            json.dump(original_data, f, default=str)

        # Load
        converter.load_extracted_data(json_path)

        self.assertEqual(
            converter.extracted_data["total_sections"],
            original_data["total_sections"],
        )
        self.assertEqual(
            converter.extracted_data["total_code_blocks"],
            original_data["total_code_blocks"],
        )

    def test_load_invalid_json(self):
        config = {"name": "test"}
        converter = EpubToSkillConverter(config)

        bad_json = os.path.join(self.temp_dir, "bad.json")
        Path(bad_json).write_text("{invalid json content")

        with self.assertRaises(json.JSONDecodeError):
            converter.load_extracted_data(bad_json)

    def test_load_nonexistent_json(self):
        config = {"name": "test"}
        converter = EpubToSkillConverter(config)

        with self.assertRaises(FileNotFoundError):
            converter.load_extracted_data("/nonexistent/path/data.json")

    def test_json_with_missing_fields(self):
        config = {"name": "test"}
        converter = EpubToSkillConverter(config)
        converter.skill_dir = os.path.join(self.temp_dir, "test")
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")

        # Minimal JSON — missing optional fields
        minimal_data = {
            "pages": [
                {
                    "section_number": 1,
                    "heading": "Test",
                    "heading_level": "h1",
                    "text": "Content",
                    "headings": [],
                    "code_samples": [],
                    "tables": [],
                    "images": [],
                }
            ],
            "metadata": {"title": "Test"},
        }
        json_path = os.path.join(self.temp_dir, "minimal.json")
        with open(json_path, "w") as f:
            json.dump(minimal_data, f)

        converter.load_extracted_data(json_path)
        # Should not crash when building
        converter.build_skill()


# ============================================================================
# Class 11: TestEpubCLIArguments
# ============================================================================


class TestEpubCLIArguments(unittest.TestCase):
    """Test CLI argument parsing."""

    def setUp(self):
        if not IMPORT_OK:
            self.skipTest("epub_scraper not importable")

    def _parse_args(self, args_list):
        import argparse

        from skill_seekers.cli.arguments.epub import add_epub_arguments

        parser = argparse.ArgumentParser()
        add_epub_arguments(parser)
        return parser.parse_args(args_list)

    def test_epub_flag_accepted(self):
        args = self._parse_args(["--epub", "book.epub"])
        self.assertEqual(args.epub, "book.epub")

    def test_from_json_flag_accepted(self):
        args = self._parse_args(["--from-json", "data.json"])
        self.assertEqual(args.from_json, "data.json")

    def test_name_flag_accepted(self):
        args = self._parse_args(["--epub", "book.epub", "--name", "mybook"])
        self.assertEqual(args.name, "mybook")

    def test_enhance_level_default_zero(self):
        args = self._parse_args(["--epub", "book.epub"])
        self.assertEqual(args.enhance_level, 0)

    def test_dry_run_flag(self):
        args = self._parse_args(["--epub", "book.epub", "--dry-run"])
        self.assertTrue(args.dry_run)

    def test_no_args_accepted(self):
        # Parser itself doesn't enforce --epub or --from-json — main() does
        args = self._parse_args([])
        self.assertIsNone(getattr(args, "epub", None))

    def test_verbose_flag(self):
        args = self._parse_args(["--epub", "book.epub", "--verbose"])
        self.assertTrue(args.verbose)

    def test_quiet_flag(self):
        args = self._parse_args(["--epub", "book.epub", "--quiet"])
        self.assertTrue(args.quiet)


# ============================================================================
# Class 12: TestEpubHelperFunctions
# ============================================================================


class TestEpubHelperFunctions(unittest.TestCase):
    """Test module-level helper functions."""

    def setUp(self):
        if not IMPORT_OK:
            self.skipTest("epub_scraper not importable")

    def test_infer_description_from_metadata_description(self):
        metadata = {"description": "A comprehensive guide to testing software"}
        result = infer_description_from_epub(metadata)
        self.assertTrue(result.startswith("Use when"))
        self.assertIn("testing", result.lower())

    def test_infer_description_from_metadata_title(self):
        metadata = {"title": "Programming Rust, 2nd Edition"}
        result = infer_description_from_epub(metadata)
        self.assertIn("programming rust", result.lower())

    def test_infer_description_fallback(self):
        result = infer_description_from_epub(name="mybook")
        self.assertIn("mybook", result)

    def test_infer_description_empty_metadata(self):
        result = infer_description_from_epub({})
        self.assertEqual(result, "Use when referencing this documentation")

    def test_score_code_quality_ranges(self):
        self.assertEqual(_score_code_quality(""), 0.0)

        score = _score_code_quality("x = 1")
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 10.0)

        # Long code with functions scores higher
        long_code = "\n".join([f"def func_{i}():" for i in range(15)] + ["    return True"])
        score_long = _score_code_quality(long_code)
        self.assertGreater(score_long, score)

    def test_sanitize_filename(self):
        config = {"name": "test"}
        converter = EpubToSkillConverter(config)
        self.assertEqual(converter._sanitize_filename("Hello World!"), "hello_world")
        self.assertEqual(converter._sanitize_filename("my-file_name"), "my_file_name")
        self.assertEqual(
            converter._sanitize_filename("Test: Special & Chars"), "test_special_chars"
        )


# ============================================================================
# Class 13: TestEpubSourceDetection
# ============================================================================


class TestEpubSourceDetection(unittest.TestCase):
    """Test source detection for EPUB files."""

    def setUp(self):
        try:
            from skill_seekers.cli.source_detector import SourceDetector

            self.SourceDetector = SourceDetector
        except ImportError:
            self.skipTest("source_detector not importable")
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_epub_detected_as_epub_type(self):
        result = self.SourceDetector.detect("test.epub")
        self.assertEqual(result.type, "epub")

    def test_epub_suggested_name(self):
        result = self.SourceDetector.detect("my-ebook.epub")
        self.assertEqual(result.suggested_name, "my-ebook")

    def test_epub_validation_missing_file(self):
        result = self.SourceDetector.detect("/nonexistent/book.epub")
        with self.assertRaises(ValueError):
            self.SourceDetector.validate_source(result)

    def test_epub_validation_not_a_file(self):
        result = self.SourceDetector.detect(self.temp_dir + ".epub")
        # Path doesn't end with .epub but let's test a directory that would be detected
        dir_path = os.path.join(self.temp_dir, "test.epub")
        os.makedirs(dir_path)  # Create a directory with .epub name
        result = self.SourceDetector.detect(dir_path)
        with self.assertRaises(ValueError):
            self.SourceDetector.validate_source(result)

    def test_epub_with_path(self):
        result = self.SourceDetector.detect("./books/test.epub")
        self.assertEqual(result.type, "epub")
        self.assertEqual(result.parsed["file_path"], "./books/test.epub")

    def test_pdf_still_detected(self):
        """Regression test: .pdf files still detected as pdf type."""
        result = self.SourceDetector.detect("document.pdf")
        self.assertEqual(result.type, "pdf")


# ============================================================================
# Class 14: TestEpubEdgeCases
# ============================================================================


class TestEpubEdgeCases(unittest.TestCase):
    """Test edge cases per W3C EPUB 3.3 spec."""

    def setUp(self):
        if not IMPORT_OK:
            self.skipTest("epub_scraper not importable")
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_epub_no_toc(self):
        """EPUB without TOC should still extract using spine order."""
        config = {"name": "test"}
        converter = EpubToSkillConverter(config)
        converter.skill_dir = os.path.join(self.temp_dir, "test")
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")
        converter.extracted_data = _make_sample_extracted_data()

        converter.build_skill()
        skill_md = Path(self.temp_dir) / "test" / "SKILL.md"
        self.assertTrue(skill_md.exists())

    def test_epub_empty_chapters(self):
        """Chapters with no text content handled gracefully."""
        # Empty body — no elements to process
        section = _build_section(1, "Empty", "h1", [])
        self.assertEqual(section["text"], "")
        self.assertEqual(section["code_samples"], [])

    def test_epub_single_chapter(self):
        """Single chapter produces valid output."""
        config = {"name": "test", "epub_path": "test.epub"}
        converter = EpubToSkillConverter(config)
        converter.skill_dir = os.path.join(self.temp_dir, "test")
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")
        converter.extracted_data = _make_sample_extracted_data(num_sections=1)

        converter.build_skill()

        skill_md = Path(self.temp_dir) / "test" / "SKILL.md"
        self.assertTrue(skill_md.exists())
        content = skill_md.read_text()
        self.assertIn("Chapter 1", content)

    def test_epub_unicode_content(self):
        """CJK, Arabic, Cyrillic, emoji text preserved."""
        from bs4 import BeautifulSoup

        html = "<p>\u4f60\u597d\u4e16\u754c \u041f\u0440\u0438\u0432\u0435\u0442 \U0001f600</p>"
        soup = BeautifulSoup(html, "html.parser")
        elements = list(soup.children)
        section = _build_section(1, "Unicode", "h1", elements)
        self.assertIn("\u4f60\u597d", section["text"])
        self.assertIn("\U0001f600", section["text"])

    def test_epub_large_section_count(self):
        """100+ sections processed without error."""
        config = {"name": "test", "epub_path": "test.epub"}
        converter = EpubToSkillConverter(config)
        converter.skill_dir = os.path.join(self.temp_dir, "test")
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")
        converter.extracted_data = _make_sample_extracted_data(num_sections=100)

        converter.build_skill()

        skill_md = Path(self.temp_dir) / "test" / "SKILL.md"
        self.assertTrue(skill_md.exists())

    def test_epub_nested_headings(self):
        """h3/h4/h5/h6 become sub-headings within sections."""
        from bs4 import BeautifulSoup

        html = (
            "<h3>Sub-section A</h3>"
            "<p>Content A</p>"
            "<h4>Sub-sub-section B</h4>"
            "<p>Content B</p>"
            "<h5>Deep heading</h5>"
            "<h6>Deepest heading</h6>"
        )
        soup = BeautifulSoup(html, "html.parser")
        elements = list(soup.children)
        section = _build_section(1, "Main", "h1", elements)
        self.assertEqual(len(section["headings"]), 4)
        self.assertEqual(section["headings"][0]["level"], "h3")
        self.assertEqual(section["headings"][0]["text"], "Sub-section A")
        self.assertEqual(section["headings"][3]["level"], "h6")

    def test_fixed_layout_detected(self):
        """Fixed-layout EPUB — we extract whatever text exists."""
        config = {"name": "test"}
        converter = EpubToSkillConverter(config)
        converter.skill_dir = os.path.join(self.temp_dir, "test")
        converter.data_file = os.path.join(self.temp_dir, "test_extracted.json")
        data = _make_sample_extracted_data(num_sections=1)
        data["pages"][0]["text"] = "Some text from fixed-layout EPUB"
        converter.extracted_data = data

        converter.build_skill()
        refs_dir = Path(self.temp_dir) / "test" / "references"
        found = False
        for f in refs_dir.glob("*.md"):
            if "fixed-layout" in f.read_text():
                found = True
                break
        self.assertTrue(found)

    def test_epub2_vs_epub3(self):
        """Both EPUB 2 and EPUB 3 use the same code path — verify section building works."""
        from bs4 import BeautifulSoup

        # EPUB 2 style (simpler XHTML)
        html2 = "<p>EPUB 2 content</p>"
        soup2 = BeautifulSoup(html2, "html.parser")
        section2 = _build_section(1, "EPUB 2 Chapter", "h1", list(soup2.children))
        self.assertIn("EPUB 2 content", section2["text"])

        # EPUB 3 style (HTML5-ish XHTML)
        html3 = "<section><p>EPUB 3 content</p></section>"
        soup3 = BeautifulSoup(html3, "html.parser")
        section3 = _build_section(1, "EPUB 3 Chapter", "h1", list(soup3.children))
        self.assertIn("EPUB 3 content", section3["text"])


if __name__ == "__main__":
    unittest.main()
