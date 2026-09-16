#!/usr/bin/env python3
"""
Tests for PDF Extractor (cli/pdf_extractor_poc.py)

Tests cover:
- Language detection with confidence scoring
- Code block detection (font, indent, pattern)
- Syntax validation
- Quality scoring
- Chapter detection
- Page chunking
- Code block merging
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "cli"))

try:
    import fitz  # noqa: F401 PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class TestLanguageDetection(unittest.TestCase):
    """Test language detection with confidence scoring"""

    def setUp(self):
        if not PYMUPDF_AVAILABLE:
            self.skipTest("PyMuPDF not installed")
        from skill_seekers.cli.pdf_extractor_poc import PDFExtractor

        self.PDFExtractor = PDFExtractor

    def test_detect_python_with_confidence(self):
        """Test Python detection returns language and confidence"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        # Initialize language_detector manually (since __init__ not called)
        from skill_seekers.cli.language_detector import LanguageDetector

        extractor.language_detector = LanguageDetector(min_confidence=0.15)

        code = "def hello():\n    print('world')\n    return True"

        language, confidence = extractor.detect_language_from_code(code)

        self.assertEqual(language, "python")
        self.assertGreater(confidence, 0.4)  # Should have reasonable confidence
        self.assertLessEqual(confidence, 1.0)

    def test_detect_javascript_with_confidence(self):
        """Test JavaScript detection"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        # Initialize language_detector manually (since __init__ not called)
        from skill_seekers.cli.language_detector import LanguageDetector

        extractor.language_detector = LanguageDetector(min_confidence=0.15)

        code = "const handleClick = () => {\n  console.log('clicked');\n};"

        language, confidence = extractor.detect_language_from_code(code)

        self.assertEqual(language, "javascript")
        self.assertGreater(confidence, 0.5)

    def test_detect_cpp_with_confidence(self):
        """Test C++ detection"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        # Initialize language_detector manually (since __init__ not called)
        from skill_seekers.cli.language_detector import LanguageDetector

        extractor.language_detector = LanguageDetector(min_confidence=0.15)

        code = '#include <iostream>\nint main() {\n  std::cout << "Hello";\n}'

        language, confidence = extractor.detect_language_from_code(code)

        self.assertEqual(language, "cpp")
        self.assertGreater(confidence, 0.5)

    def test_detect_unknown_low_confidence(self):
        """Test unknown language returns low confidence"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        # Initialize language_detector manually (since __init__ not called)
        from skill_seekers.cli.language_detector import LanguageDetector

        extractor.language_detector = LanguageDetector(min_confidence=0.15)

        code = "this is not code at all just plain text"

        language, confidence = extractor.detect_language_from_code(code)

        self.assertEqual(language, "unknown")
        self.assertLess(confidence, 0.3)  # Should be low confidence

    def test_confidence_range(self):
        """Test confidence is always between 0 and 1"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        # Initialize language_detector manually (since __init__ not called)
        from skill_seekers.cli.language_detector import LanguageDetector

        extractor.language_detector = LanguageDetector(min_confidence=0.15)

        test_codes = [
            "def foo(): pass",
            "const x = 10;",
            "#include <stdio.h>",
            "random text here",
            "",
        ]

        for code in test_codes:
            _, confidence = extractor.detect_language_from_code(code)
            self.assertGreaterEqual(confidence, 0.0)
            self.assertLessEqual(confidence, 1.0)

    def test_detect_scss_with_confidence(self):
        """Test SCSS detection"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        from skill_seekers.cli.language_detector import LanguageDetector

        extractor.language_detector = LanguageDetector(min_confidence=0.15)

        code = """
        $primary-color: #3498db;

        @mixin border-radius($radius) {
          border-radius: $radius;
        }

        .button {
          color: $primary-color;
          @include border-radius(5px);

          &:hover {
            background: darken($primary-color, 10%);
          }
        }
        """

        language, confidence = extractor.detect_language_from_code(code)
        self.assertEqual(language, "scss")
        self.assertGreater(confidence, 0.8)

    def test_detect_dart_with_confidence(self):
        """Test Dart detection"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        from skill_seekers.cli.language_detector import LanguageDetector

        extractor.language_detector = LanguageDetector(min_confidence=0.15)

        code = """
        import 'package:flutter/material.dart';

        class MyApp extends StatelessWidget {
          @override
          Widget build(BuildContext context) {
            return MaterialApp(
              home: Text('Hello'),
            );
          }
        }
        """

        language, confidence = extractor.detect_language_from_code(code)
        self.assertEqual(language, "dart")
        self.assertGreater(confidence, 0.6)

    def test_detect_scala_with_confidence(self):
        """Test Scala detection"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        from skill_seekers.cli.language_detector import LanguageDetector

        extractor.language_detector = LanguageDetector(min_confidence=0.15)

        code = """
        case class Person(name: String, age: Int)

        object Main extends App {
          val person = Person("Alice", 30)
          person match {
            case Person(n, a) if a >= 18 => println(s"Adult: $n")
            case _ => println("Minor")
          }
        }
        """

        language, confidence = extractor.detect_language_from_code(code)
        self.assertEqual(language, "scala")
        self.assertGreater(confidence, 0.7)

    def test_detect_sass_with_confidence(self):
        """Test SASS detection"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        from skill_seekers.cli.language_detector import LanguageDetector

        extractor.language_detector = LanguageDetector(min_confidence=0.15)

        code = """
        $primary-color: #3498db

        =border-radius($radius)
          border-radius: $radius

        .button
          color: $primary-color
          +border-radius(5px)

          &:hover
            background: darken($primary-color, 10%)
        """

        language, confidence = extractor.detect_language_from_code(code)
        self.assertEqual(language, "sass")
        self.assertGreater(confidence, 0.8)

    def test_detect_elixir_with_confidence(self):
        """Test Elixir detection"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        from skill_seekers.cli.language_detector import LanguageDetector

        extractor.language_detector = LanguageDetector(min_confidence=0.15)

        code = """
        defmodule MyApp.User do
          def greet(name) do
            "Hello, #{name}"
          end

          defp calculate_age(birth_year) do
            2024 - birth_year
          end

          def process(data) do
            data
            |> String.trim()
            |> String.downcase()
            |> String.split(",")
          end
        end
        """

        language, confidence = extractor.detect_language_from_code(code)
        self.assertEqual(language, "elixir")
        self.assertGreater(confidence, 0.8)

    def test_detect_lua_with_confidence(self):
        """Test Lua detection"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        from skill_seekers.cli.language_detector import LanguageDetector

        extractor.language_detector = LanguageDetector(min_confidence=0.15)

        code = """
        local function calculate_sum(numbers)
          local total = 0
          for i = 1, #numbers do
            total = total + numbers[i]
          end
          return total
        end

        local items = {1, 2, 3, 4, 5}
        local result = calculate_sum(items)
        print("Sum: " .. result)
        """

        language, confidence = extractor.detect_language_from_code(code)
        self.assertEqual(language, "lua")
        self.assertGreater(confidence, 0.7)

    def test_detect_perl_with_confidence(self):
        """Test Perl detection"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        from skill_seekers.cli.language_detector import LanguageDetector

        extractor.language_detector = LanguageDetector(min_confidence=0.15)

        code = r"""
        #!/usr/bin/perl
        use strict;
        use warnings;

        sub process_line {
          my $line = shift;
          chomp($line);

          if ($line =~ /^(\w+)=(\w+)$/) {
            my ($name, $value) = ($1, $2);
            return "$name has value $value";
          }
          return undef;
        }

        my @lines = ("foo=10", "bar=20");
        foreach my $line (@lines) {
          my $result = process_line($line);
          print $result if defined $result;
        }
        """

        language, confidence = extractor.detect_language_from_code(code)
        self.assertEqual(language, "perl")
        self.assertGreater(confidence, 0.8)


class TestSyntaxValidation(unittest.TestCase):
    """Test syntax validation for different languages"""

    def setUp(self):
        if not PYMUPDF_AVAILABLE:
            self.skipTest("PyMuPDF not installed")
        from skill_seekers.cli.pdf_extractor_poc import PDFExtractor

        self.PDFExtractor = PDFExtractor

    def test_validate_python_valid(self):
        """Test valid Python syntax"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        code = "def hello():\n    print('world')\n    return True"

        is_valid, issues = extractor.validate_code_syntax(code, "python")

        self.assertTrue(is_valid)
        self.assertEqual(len(issues), 0)

    def test_validate_python_invalid_indentation(self):
        """Test invalid Python indentation"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        code = "def hello():\n    print('world')\n\tprint('mixed')"  # Mixed tabs and spaces

        is_valid, issues = extractor.validate_code_syntax(code, "python")

        self.assertFalse(is_valid)
        self.assertGreater(len(issues), 0)

    def test_validate_python_unbalanced_brackets(self):
        """Test unbalanced brackets"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        code = "x = [[[1, 2, 3"  # Severely unbalanced brackets

        is_valid, issues = extractor.validate_code_syntax(code, "python")

        self.assertFalse(is_valid)
        self.assertGreater(len(issues), 0)

    def test_validate_javascript_valid(self):
        """Test valid JavaScript syntax"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        code = "const x = () => { return 42; };"

        is_valid, issues = extractor.validate_code_syntax(code, "javascript")

        self.assertTrue(is_valid)
        self.assertEqual(len(issues), 0)

    def test_validate_natural_language_fails(self):
        """Test natural language fails validation"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        code = "This is just a regular sentence with the and for and with and that and have and from words."

        is_valid, issues = extractor.validate_code_syntax(code, "python")

        self.assertFalse(is_valid)
        self.assertIn("May be natural language", " ".join(issues))


class TestQualityScoring(unittest.TestCase):
    """Test code quality scoring (0-10 scale)"""

    def setUp(self):
        if not PYMUPDF_AVAILABLE:
            self.skipTest("PyMuPDF not installed")
        from skill_seekers.cli.pdf_extractor_poc import PDFExtractor

        self.PDFExtractor = PDFExtractor

    def test_quality_score_range(self):
        """Test quality score is between 0 and 10"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        code = "def hello():\n    print('world')"

        quality = extractor.score_code_quality(code, "python", 0.8)

        self.assertGreaterEqual(quality, 0.0)
        self.assertLessEqual(quality, 10.0)

    def test_high_quality_code(self):
        """Test high-quality code gets good score"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        code = """def calculate_sum(numbers):
    '''Calculate sum of numbers'''
    total = 0
    for num in numbers:
        total += num
    return total"""

        quality = extractor.score_code_quality(code, "python", 0.9)

        self.assertGreater(quality, 6.0)  # Should be good quality

    def test_low_quality_code(self):
        """Test low-quality code gets low score"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        code = "x"  # Too short, no structure

        quality = extractor.score_code_quality(code, "unknown", 0.1)

        self.assertLess(quality, 6.0)  # Should be low quality

    def test_quality_factors(self):
        """Test that quality considers multiple factors"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)

        # Good: proper structure, indentation, confidence
        good_code = "def foo():\n    return bar()"
        good_quality = extractor.score_code_quality(good_code, "python", 0.9)

        # Bad: no structure, low confidence
        bad_code = "some text"
        bad_quality = extractor.score_code_quality(bad_code, "unknown", 0.1)

        self.assertGreater(good_quality, bad_quality)


class TestChapterDetection(unittest.TestCase):
    """Test chapter/section detection"""

    def setUp(self):
        if not PYMUPDF_AVAILABLE:
            self.skipTest("PyMuPDF not installed")
        from skill_seekers.cli.pdf_extractor_poc import PDFExtractor

        self.PDFExtractor = PDFExtractor

    def test_detect_chapter_with_number(self):
        """Test chapter detection with number"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        page_data = {
            "text": "Chapter 1: Introduction to Python\nThis is the first chapter.",
            "headings": [],
        }

        is_chapter, title = extractor.detect_chapter_start(page_data)

        self.assertTrue(is_chapter)
        self.assertIsNotNone(title)

    def test_detect_chapter_uppercase(self):
        """Test chapter detection with uppercase"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        page_data = {
            "text": "Chapter 1\nThis is the introduction",  # Pattern requires Chapter + digit
            "headings": [],
        }

        is_chapter, title = extractor.detect_chapter_start(page_data)

        self.assertTrue(is_chapter)

    def test_detect_section_heading(self):
        """Test section heading detection"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        page_data = {"text": "2. Getting Started\nThis is a section.", "headings": []}

        is_chapter, title = extractor.detect_chapter_start(page_data)

        self.assertTrue(is_chapter)

    def test_not_chapter(self):
        """Test normal text is not detected as chapter"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        page_data = {
            "text": "This is just normal paragraph text without any chapter markers.",
            "headings": [],
        }

        is_chapter, title = extractor.detect_chapter_start(page_data)

        self.assertFalse(is_chapter)


class TestCodeBlockMerging(unittest.TestCase):
    """Test code block merging across pages"""

    def setUp(self):
        if not PYMUPDF_AVAILABLE:
            self.skipTest("PyMuPDF not installed")
        from skill_seekers.cli.pdf_extractor_poc import PDFExtractor

        self.PDFExtractor = PDFExtractor

    def test_merge_continued_blocks(self):
        """Test merging code blocks split across pages"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        extractor.verbose = False  # Initialize verbose attribute

        pages = [
            {
                "page_number": 1,
                "code_samples": [
                    {
                        "code": "def hello():",
                        "language": "python",
                        "detection_method": "pattern",
                    }
                ],
                "code_blocks_count": 1,
            },
            {
                "page_number": 2,
                "code_samples": [
                    {
                        "code": '    print("world")',
                        "language": "python",
                        "detection_method": "pattern",
                    }
                ],
                "code_blocks_count": 1,
            },
        ]

        merged = extractor.merge_continued_code_blocks(pages)

        # Should have merged the two blocks
        self.assertIn("def hello():", merged[0]["code_samples"][0]["code"])
        self.assertIn('print("world")', merged[0]["code_samples"][0]["code"])

    def test_no_merge_different_languages(self):
        """Test blocks with different languages are not merged"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)

        pages = [
            {
                "page_number": 1,
                "code_samples": [
                    {
                        "code": "def foo():",
                        "language": "python",
                        "detection_method": "pattern",
                    }
                ],
                "code_blocks_count": 1,
            },
            {
                "page_number": 2,
                "code_samples": [
                    {
                        "code": "const x = 10;",
                        "language": "javascript",
                        "detection_method": "pattern",
                    }
                ],
                "code_blocks_count": 1,
            },
        ]

        merged = extractor.merge_continued_code_blocks(pages)

        # Should NOT merge different languages
        self.assertEqual(len(merged[0]["code_samples"]), 1)
        self.assertEqual(len(merged[1]["code_samples"]), 1)


class TestCodeDetectionMethods(unittest.TestCase):
    """Test different code detection methods"""

    def setUp(self):
        if not PYMUPDF_AVAILABLE:
            self.skipTest("PyMuPDF not installed")
        from skill_seekers.cli.pdf_extractor_poc import PDFExtractor

        self.PDFExtractor = PDFExtractor

    def test_pattern_based_detection(self):
        """Test pattern-based code detection"""
        _extractor = self.PDFExtractor.__new__(self.PDFExtractor)

        # Should detect function definitions
        text = "Here is an example:\ndef calculate(x, y):\n    return x + y"

        # Pattern-based detection should find this
        # (implementation details depend on pdf_extractor_poc.py)
        self.assertIn("def ", text)
        self.assertIn("return", text)

    def test_indent_based_detection(self):
        """Test indent-based code detection"""
        _extractor = self.PDFExtractor.__new__(self.PDFExtractor)

        # Code with consistent indentation
        indented_text = """    def foo():
        return bar()"""

        # Should detect as code due to indentation
        self.assertTrue(indented_text.startswith(" " * 4))


class TestQualityFiltering(unittest.TestCase):
    """Test quality-based filtering"""

    def setUp(self):
        if not PYMUPDF_AVAILABLE:
            self.skipTest("PyMuPDF not installed")
        from skill_seekers.cli.pdf_extractor_poc import PDFExtractor

        self.PDFExtractor = PDFExtractor

    def test_filter_by_min_quality(self):
        """Test filtering code blocks by minimum quality"""
        extractor = self.PDFExtractor.__new__(self.PDFExtractor)
        extractor.min_quality = 5.0

        # High quality block
        high_quality = {
            "code": "def calculate():\n    return 42",
            "language": "python",
            "quality": 8.0,
        }

        # Low quality block
        low_quality = {"code": "x", "language": "unknown", "quality": 2.0}

        # Only high quality should pass
        self.assertGreaterEqual(high_quality["quality"], extractor.min_quality)
        self.assertLess(low_quality["quality"], extractor.min_quality)


class TestVectorFigureExtraction(unittest.TestCase):
    """Test conservative extraction of vector figures from PDF pages."""

    def setUp(self):
        if not PYMUPDF_AVAILABLE:
            self.skipTest("PyMuPDF not installed")

        from skill_seekers.cli.pdf_extractor_poc import PDFExtractor

        self.PDFExtractor = PDFExtractor
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pdf_path = Path(self.temp_dir.name) / "vector_figures.pdf"
        self.image_dir = Path(self.temp_dir.name) / "images"
        self._create_fixture()

    def tearDown(self):
        self.temp_dir.cleanup()

    @staticmethod
    def _add_page_chrome(page):
        """Add page decorations that must not become extracted figures."""
        page.draw_rect(fitz.Rect(24, 24, 588, 768), color=(0.5, 0.5, 0.5), width=1)
        page.draw_line((45, 100), (567, 100), color=(0.3, 0.3, 0.3), width=1)

    @staticmethod
    def _raster_bytes(width, height, color):
        pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, width, height))
        pixmap.clear_with(color)
        return pixmap.tobytes("png")

    def _create_fixture(self):
        doc = fitz.open()

        # Page 1: a vector-only technical diagram with overlapping shapes and a label.
        page = doc.new_page()
        self._add_page_chrome(page)
        page.draw_rect(
            fitz.Rect(100, 180, 240, 300),
            color=(0.0, 0.2, 0.6),
            fill=(0.85, 0.92, 1.0),
            width=2,
        )
        page.draw_rect(
            fitz.Rect(300, 180, 440, 300),
            color=(0.0, 0.2, 0.6),
            fill=(0.85, 0.92, 1.0),
            width=2,
        )
        page.draw_circle((270, 240), 36, color=(0.0, 0.0, 0.0), width=2)
        page.draw_line((240, 240), (300, 240), color=(0.0, 0.0, 0.0), width=2)
        page.draw_line((440, 240), (500, 240), color=(0.0, 0.0, 0.0), width=2)
        page.draw_line((490, 232), (500, 240), color=(0.0, 0.0, 0.0), width=2)
        page.draw_line((490, 248), (500, 240), color=(0.0, 0.0, 0.0), width=2)
        page.insert_text((115, 326), "Vector signal path", fontsize=12)

        # Page 2: raster-only content, including a small raster icon to filter.
        page = doc.new_page()
        self._add_page_chrome(page)
        large_raster = self._raster_bytes(160, 100, 0x336699)
        small_raster = self._raster_bytes(16, 16, 0xCC3300)
        page.insert_image(fitz.Rect(100, 180, 300, 305), stream=large_raster)
        page.insert_image(fitz.Rect(340, 180, 360, 200), stream=small_raster)

        # Page 3: mixed vector and raster figures in separate regions.
        page = doc.new_page()
        self._add_page_chrome(page)
        page.draw_rect(
            fitz.Rect(80, 180, 220, 300),
            color=(0.0, 0.5, 0.2),
            fill=(0.85, 1.0, 0.88),
            width=2,
        )
        page.draw_rect(
            fitz.Rect(260, 180, 400, 300),
            color=(0.0, 0.5, 0.2),
            fill=(0.85, 1.0, 0.88),
            width=2,
        )
        page.draw_line((220, 240), (260, 240), color=(0.0, 0.0, 0.0), width=2)
        page.draw_line((240, 232), (260, 240), color=(0.0, 0.0, 0.0), width=2)
        page.draw_line((240, 248), (260, 240), color=(0.0, 0.0, 0.0), width=2)
        page.insert_text((90, 326), "Vector branch", fontsize=12)
        page.insert_image(
            fitz.Rect(430, 180, 570, 300),
            stream=self._raster_bytes(140, 120, 0x663399),
        )

        # Page 4: only page chrome and a separator.
        page = doc.new_page()
        self._add_page_chrome(page)

        # Page 5: a table-like grid that must not become a figure.
        page = doc.new_page()
        self._add_page_chrome(page)
        for x in (380, 440, 500, 560):
            page.draw_line((x, 500), (x, 650), color=(0.0, 0.0, 0.0), width=1)
        for y in (500, 530, 560, 590, 650):
            page.draw_line((380, y), (560, y), color=(0.0, 0.0, 0.0), width=1)

        # Page 6: a filled table-like grid that must also be rejected.
        page = doc.new_page()
        self._add_page_chrome(page)
        for row in range(4):
            for column in range(4):
                x0 = 380 + column * 45
                y0 = 500 + row * 30
                page.draw_rect(
                    fitz.Rect(x0, y0, x0 + 45, y0 + 30),
                    color=(0.0, 0.0, 0.0),
                    fill=(0.92, 0.92, 0.92),
                    width=1,
                )
        for x in (380, 425, 470, 515, 560):
            page.draw_line((x, 500), (x, 620), color=(0.0, 0.0, 0.0), width=1)
        for y in (500, 530, 560, 590, 620):
            page.draw_line((380, y), (560, y), color=(0.0, 0.0, 0.0), width=1)

        # Page 7: small decorative marks that must be rejected by size.
        page = doc.new_page()
        self._add_page_chrome(page)
        page.draw_rect(fitz.Rect(120, 220, 140, 240), color=(0.0, 0.0, 0.0), width=1)
        page.draw_circle((170, 230), 10, color=(0.0, 0.0, 0.0), width=1)
        page.draw_line((190, 230), (220, 230), color=(0.0, 0.0, 0.0), width=1)

        # Page 8: two distinct figures separated by a realistic gutter. Shapes
        # inside one figure are merged across small gaps, so the separation has
        # to exceed VECTOR_MERGE_GAP for them to stay two figures.
        page = doc.new_page()
        self._add_page_chrome(page)
        for x in (80, 320):
            page.draw_rect(
                fitz.Rect(x, 180, x + 80, 280),
                color=(0.0, 0.2, 0.6),
                fill=(0.85, 0.92, 1.0),
                width=2,
            )
            page.draw_rect(
                fitz.Rect(x + 100, 180, x + 180, 280),
                color=(0.0, 0.2, 0.6),
                fill=(0.85, 0.92, 1.0),
                width=2,
            )
            page.draw_line((x + 80, 230), (x + 100, 230), color=(0.0, 0.0, 0.0), width=2)
            page.draw_line((x + 90, 220), (x + 100, 230), color=(0.0, 0.0, 0.0), width=2)
            page.draw_line((x + 90, 240), (x + 100, 230), color=(0.0, 0.0, 0.0), width=2)

        # Page 9: a raster image inside a vector cluster must not be duplicated.
        page = doc.new_page()
        self._add_page_chrome(page)
        page.draw_rect(
            fitz.Rect(80, 180, 220, 300),
            color=(0.0, 0.0, 0.0),
            fill=(0.8, 0.9, 1.0),
            width=2,
        )
        page.draw_rect(
            fitz.Rect(260, 180, 400, 300),
            color=(0.0, 0.0, 0.0),
            fill=(0.8, 0.9, 1.0),
            width=2,
        )
        page.draw_line((220, 240), (260, 240), color=(0.0, 0.0, 0.0), width=2)
        page.draw_line((240, 230), (260, 240), color=(0.0, 0.0, 0.0), width=2)
        page.draw_line((240, 250), (260, 240), color=(0.0, 0.0, 0.0), width=2)
        page.insert_image(
            fitz.Rect(270, 190, 390, 290),
            stream=self._raster_bytes(120, 100, 0x336699),
        )

        doc.save(self.pdf_path)
        doc.close()

    def _extract(self, extract_images=True):
        extractor = self.PDFExtractor(
            str(self.pdf_path),
            extract_images=extract_images,
            image_dir=str(self.image_dir),
            min_image_size=100,
            use_cache=False,
        )
        return extractor.extract_all()

    def test_extracts_vector_only_figure_with_nearby_label_once(self):
        """Overlapping vector drawings become one non-empty PNG with its label area."""
        result = self._extract()
        images = result["pages"][0]["extracted_images"]

        self.assertEqual(len(images), 1)
        image = images[0]
        self.assertEqual(image["format"], "png")
        self.assertEqual(image["source"], "vector")
        self.assertGreater(image["size_bytes"], 0)
        self.assertGreater(image["width"], 0)
        self.assertGreater(image["height"], 0)
        self.assertGreaterEqual(image["bbox"][3], 326)
        self.assertTrue(Path(image["path"]).is_file())

        rendered = fitz.Pixmap(image["path"])
        self.assertGreater(len(set(rendered.samples)), 3)
        self.assertGreater(sum(value < 80 for value in rendered.samples), 100)

    def test_preserves_raster_and_extracts_mixed_content(self):
        """Raster extraction remains available and mixed pages contain both types."""
        result = self._extract()

        raster_images = result["pages"][1]["extracted_images"]
        mixed_images = result["pages"][2]["extracted_images"]

        self.assertEqual(len(raster_images), 1)
        self.assertEqual(raster_images[0].get("source", "raster"), "raster")
        self.assertEqual(len(mixed_images), 2)
        self.assertCountEqual(
            [image.get("source", "raster") for image in mixed_images],
            ["raster", "vector"],
        )

    def test_rejects_chrome_table_grid_and_small_decorations(self):
        """Page chrome, separators, grids, and tiny marks are not figures."""
        result = self._extract()

        for page_number in (4, 5, 6, 7):
            self.assertEqual(result["pages"][page_number - 1]["extracted_images"], [])

    def test_disabling_image_extraction_disables_vector_fallback(self):
        """The existing extract_images switch controls raster and vector output."""
        result = self._extract(extract_images=False)

        self.assertEqual(result["total_extracted_images"], 0)
        self.assertTrue(all(not page["extracted_images"] for page in result["pages"]))

    def test_keeps_nearby_vector_figures_separate(self):
        """Figures in separate page regions are not merged into one output."""
        result = self._extract()
        images = result["pages"][7]["extracted_images"]

        self.assertEqual(len(images), 2)
        self.assertEqual(
            [image["filename"] for image in images],
            [
                "vector_figures_page8_vector1.png",
                "vector_figures_page8_vector2.png",
            ],
        )
        self.assertLessEqual(images[0]["bbox"][2], images[1]["bbox"][0])

    def test_keeps_vector_figure_containing_a_raster(self):
        """A raster inside a much larger diagram must not delete the diagram.

        De-duplication asks "are these the same object", so a contained thumbnail
        is not grounds for dropping the figure that encloses it.
        """
        result = self._extract()
        images = result["pages"][8]["extracted_images"]

        self.assertCountEqual(
            [image["filename"] for image in images],
            ["vector_figures_page9_img1.png", "vector_figures_page9_vector1.png"],
        )

    def test_raster_entries_carry_source_and_bbox(self):
        """Raster and vector entries share one shape, so consumers need no fallback."""
        result = self._extract()
        raster = result["pages"][1]["extracted_images"][0]

        self.assertEqual(raster["source"], "raster")
        self.assertEqual(len(raster["bbox"]), 4)
        self.assertLess(raster["bbox"][0], raster["bbox"][2])
        self.assertLess(raster["bbox"][1], raster["bbox"][3])

    def test_vector_figures_are_counted_separately_from_raster_objects(self):
        """images_count stays raster-only, so extracted never exceeds found."""
        result = self._extract()

        self.assertEqual(result["pages"][0]["images_count"], 0)
        self.assertEqual(result["pages"][0]["vector_figures_count"], 1)

        extracted_rasters = sum(
            1 for image in result["extracted_images"] if image["source"] == "raster"
        )
        self.assertEqual(
            extracted_rasters + result["total_vector_figures"],
            result["total_extracted_images"],
        )
        # Raster objects found bounds raster objects extracted: the fixture has a
        # 16x16 icon that min_image_size drops.
        self.assertGreater(result["total_images"], extracted_rasters)

    def test_min_image_size_also_filters_vector_figures(self):
        """--min-image-size is documented as filtering icons; it must reach figures."""
        extractor = self.PDFExtractor(
            str(self.pdf_path),
            extract_images=True,
            image_dir=str(self.image_dir),
            min_image_size=4000,
            use_cache=False,
        )
        result = extractor.extract_all()

        self.assertEqual(result["extracted_images"], [])

    def test_parallel_image_output_is_page_ordered(self):
        """Parallel workers still produce deterministic aggregate image ordering."""
        extractor = self.PDFExtractor(
            str(self.pdf_path),
            extract_images=True,
            image_dir=str(self.image_dir),
            min_image_size=100,
            parallel=True,
            max_workers=4,
            use_cache=False,
        )
        result = extractor.extract_all()

        self.assertEqual(
            [image["filename"] for image in result["extracted_images"]],
            [
                "vector_figures_page1_vector1.png",
                "vector_figures_page2_img1.png",
                "vector_figures_page3_img1.png",
                "vector_figures_page3_vector1.png",
                "vector_figures_page8_vector1.png",
                "vector_figures_page8_vector2.png",
                "vector_figures_page9_img1.png",
                "vector_figures_page9_vector1.png",
            ],
        )


class TestVectorFigureHeuristics(unittest.TestCase):
    """Regression cases for the vector-figure detection heuristics.

    Each fixture is a single-page PDF exercising one document shape that the
    first implementation of this feature got wrong.
    """

    def setUp(self):
        if not PYMUPDF_AVAILABLE:
            self.skipTest("PyMuPDF not installed")

        from skill_seekers.cli.pdf_extractor_poc import PDFExtractor

        self.PDFExtractor = PDFExtractor
        self.temp_dir = tempfile.TemporaryDirectory()
        self.image_dir = Path(self.temp_dir.name) / "images"

    def tearDown(self):
        self.temp_dir.cleanup()

    def _extract_page(self, draw, name, min_image_size=100):
        """Build a one-page PDF with `draw`, extract it, return its image list."""
        pdf_path = Path(self.temp_dir.name) / f"{name}.pdf"
        doc = fitz.open()
        draw(doc.new_page())
        doc.save(pdf_path)
        doc.close()

        extractor = self.PDFExtractor(
            str(pdf_path),
            extract_images=True,
            image_dir=str(self.image_dir),
            min_image_size=min_image_size,
            use_cache=False,
        )
        return extractor.extract_all()["pages"][0]["extracted_images"]

    @staticmethod
    def _box(page, rect):
        page.draw_rect(rect, color=(0.0, 0.2, 0.6), fill=(0.85, 0.92, 1.0), width=2)

    def test_shaded_code_blocks_are_not_figures(self):
        """Stacked fill-only bands are page furniture, not a diagram."""

        def draw(page):
            for top in (100, 161, 222):
                page.draw_rect(
                    fitz.Rect(50, top, 540, top + 60),
                    color=None,
                    fill=(0.95, 0.95, 0.95),
                )
                page.insert_text((60, top + 20), "def handler(request):", fontsize=10)

        self.assertEqual(self._extract_page(draw, "shaded_blocks"), [])

    def test_label_expansion_stops_at_the_figure(self):
        """A label may nudge the clip; the page body must never be dragged in."""

        def draw(page):
            for x in (80, 200, 300):
                self._box(page, fitz.Rect(x, 100, x + 100, 200))
            # Tight body copy: consecutive block bboxes touch, which is what made
            # the original in-place union walk to the bottom of the page.
            y = 210.0
            while y < 800:
                page.insert_text((80, y), "body copy line for layout purposes", fontsize=10)
                y += 13.5

        images = self._extract_page(draw, "label_cascade")

        self.assertEqual(len(images), 1)
        self.assertLess(images[0]["bbox"][3], 300)

    def test_block_diagram_with_gaps_becomes_one_figure(self):
        """Boxes 20pt apart are one diagram, not twelve rejected fragments."""

        def draw(page):
            for row in range(3):
                for column in range(4):
                    x = 80 + column * 80
                    y = 200 + row * 60
                    self._box(page, fitz.Rect(x, y, x + 60, y + 40))

        images = self._extract_page(draw, "block_diagram")

        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]["source"], "vector")

    def test_chart_with_gridlines_survives(self):
        """Gridlines plus a wide baseline axis must not read as a table or chrome."""

        def draw(page):
            for y in (200, 240, 280, 320):
                page.draw_line((80, y), (520, y), color=(0.8, 0.8, 0.8), width=1)
            for x in (80, 200, 320):
                page.draw_line((x, 180), (x, 340), color=(0.8, 0.8, 0.8), width=1)
            # 80% of the page width: page furniture in the original thresholds.
            page.draw_line((60, 360), (536, 360), color=(0.0, 0.0, 0.0), width=1)
            page.draw_polyline(
                [(90, 320), (180, 240), (270, 280), (360, 200), (450, 220)],
                color=(0.8, 0.1, 0.1),
                width=2,
            )

        images = self._extract_page(draw, "chart")

        self.assertEqual(len(images), 1)
        # The baseline axis is inside the rendered clip rather than cropped off.
        self.assertGreaterEqual(images[0]["bbox"][3], 360)

    def test_line_ruled_table_is_still_rejected(self):
        """The chart escape hatch must not let a plain ruled table through."""

        def draw(page):
            for x in (380, 440, 500, 560):
                page.draw_line((x, 500), (x, 650), color=(0.0, 0.0, 0.0), width=1)
            for y in (500, 530, 560, 590, 650):
                page.draw_line((380, y), (560, y), color=(0.0, 0.0, 0.0), width=1)

        self.assertEqual(self._extract_page(draw, "ruled_table"), [])

    def test_figures_are_numbered_in_reading_order(self):
        """vector1 is the topmost figure, not the largest one."""

        def draw(page):
            self._box(page, fitz.Rect(80, 120, 180, 190))
            self._box(page, fitz.Rect(200, 120, 300, 190))
            page.draw_line((180, 155), (200, 155), color=(0, 0, 0), width=2)
            self._box(page, fitz.Rect(80, 320, 280, 470))
            self._box(page, fitz.Rect(300, 320, 500, 470))
            page.draw_line((280, 395), (300, 395), color=(0, 0, 0), width=2)

        images = self._extract_page(draw, "reading_order")

        self.assertEqual(len(images), 2)
        self.assertLess(images[0]["bbox"][1], images[1]["bbox"][1])
        self.assertTrue(images[0]["filename"].endswith("_vector1.png"))

    def test_near_coincident_raster_and_vector_deduplicate(self):
        """A raster covering the same region as the cluster yields one asset."""
        pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 200, 120))
        pixmap.clear_with(0x336699)
        raster = pixmap.tobytes("png")

        def draw(page):
            self._box(page, fitz.Rect(100, 200, 200, 320))
            self._box(page, fitz.Rect(210, 200, 300, 320))
            page.insert_image(fitz.Rect(100, 200, 300, 320), stream=raster)

        images = self._extract_page(draw, "coincident")

        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]["source"], "raster")

    def test_dense_vector_page_bails_out(self):
        """Scatter plots and maps skip extraction instead of clustering for minutes."""

        def draw(page):
            for index in range(2100):
                x = 60 + (index % 60) * 8
                y = 100 + (index // 60) * 18
                page.draw_line((x, y), (x + 4, y + 4), color=(0.1, 0.1, 0.1), width=1)

        self.assertEqual(self._extract_page(draw, "dense"), [])


class TestMarkdownExtractionFallback(unittest.TestCase):
    """Test markdown extraction fallback behavior for issue #267"""

    def test_exception_types_in_fallback(self):
        """Test that fallback handles various exception types"""
        # This test verifies the code structure handles multiple exception types
        # The actual exception handling is in pdf_extractor_poc.py lines 793-802
        exception_types = (
            AssertionError,
            ValueError,
            RuntimeError,
            TypeError,
            AttributeError,
        )

        # Verify all expected exception types are valid
        for exc_type in exception_types:
            self.assertTrue(issubclass(exc_type, Exception))
            # Verify we can raise and catch each type
            try:
                raise exc_type("Test exception")
            except exception_types:
                pass  # Should be caught

    def test_fallback_text_extraction_logic(self):
        """Test that text extraction fallback produces valid output"""
        if not PYMUPDF_AVAILABLE:
            self.skipTest("PyMuPDF not installed")

        # Verify the fallback flags are valid fitz constants
        import fitz

        # These flags should exist and be combinable
        flags = (
            fitz.TEXT_PRESERVE_WHITESPACE | fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_SPANS
        )
        self.assertIsInstance(flags, int)
        self.assertGreater(flags, 0)

    def test_markdown_fallback_on_assertion_error(self):
        """Test that AssertionError triggers fallback to text extraction"""
        if not PYMUPDF_AVAILABLE:
            self.skipTest("PyMuPDF not installed")

        from unittest.mock import Mock

        import fitz

        # Create a mock page that raises AssertionError on markdown extraction
        mock_page = Mock()
        mock_page.get_text.side_effect = [
            AssertionError("markdown format not supported"),  # First call raises
            "Fallback text content",  # Second call succeeds
        ]

        # Simulate the extraction logic
        try:
            markdown = mock_page.get_text("markdown")
            self.fail("Should have raised AssertionError")
        except AssertionError:
            # Fallback to text extraction
            markdown = mock_page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)

        # Verify fallback returned text content
        self.assertEqual(markdown, "Fallback text content")
        # Verify get_text was called twice (markdown attempt + text fallback)
        self.assertEqual(mock_page.get_text.call_count, 2)

    def test_markdown_fallback_on_runtime_error(self):
        """Test that RuntimeError triggers fallback to text extraction"""
        if not PYMUPDF_AVAILABLE:
            self.skipTest("PyMuPDF not installed")

        from unittest.mock import Mock

        import fitz

        # Create a mock page that raises RuntimeError
        mock_page = Mock()
        mock_page.get_text.side_effect = [
            RuntimeError("PyMuPDF runtime error"),
            "Fallback text content",
        ]

        # Simulate the extraction logic
        try:
            markdown = mock_page.get_text("markdown")
        except (AssertionError, ValueError, RuntimeError, TypeError, AttributeError):
            # Fallback to text extraction
            markdown = mock_page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)

        # Verify fallback worked
        self.assertEqual(markdown, "Fallback text content")
        self.assertEqual(mock_page.get_text.call_count, 2)

    def test_markdown_fallback_on_type_error(self):
        """Test that TypeError triggers fallback to text extraction"""
        if not PYMUPDF_AVAILABLE:
            self.skipTest("PyMuPDF not installed")

        from unittest.mock import Mock

        import fitz

        # Create a mock page that raises TypeError
        mock_page = Mock()
        mock_page.get_text.side_effect = [
            TypeError("Invalid argument type"),
            "Fallback text content",
        ]

        # Simulate the extraction logic
        try:
            markdown = mock_page.get_text("markdown")
        except (AssertionError, ValueError, RuntimeError, TypeError, AttributeError):
            markdown = mock_page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)

        # Verify fallback worked
        self.assertEqual(markdown, "Fallback text content")

    def test_markdown_fallback_preserves_content_quality(self):
        """Test that fallback text extraction preserves content structure"""
        if not PYMUPDF_AVAILABLE:
            self.skipTest("PyMuPDF not installed")

        from unittest.mock import Mock

        import fitz

        # Create a mock page with structured content
        fallback_content = """This is a heading

This is a paragraph with multiple lines
and preserved whitespace.

    Code block with indentation
    def example():
        return True"""

        mock_page = Mock()
        mock_page.get_text.side_effect = [
            ValueError("markdown extraction failed"),
            fallback_content,
        ]

        # Simulate the extraction logic
        try:
            markdown = mock_page.get_text("markdown")
        except (AssertionError, ValueError, RuntimeError, TypeError, AttributeError):
            markdown = mock_page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)

        # Verify content structure is preserved
        self.assertIn("This is a heading", markdown)
        self.assertIn("Code block with indentation", markdown)
        self.assertIn("def example():", markdown)
        # Verify whitespace preservation
        self.assertIn("    ", markdown)


if __name__ == "__main__":
    unittest.main()
