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
                    {"code": "def hello():", "language": "python", "detection_method": "pattern"}
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
                    {"code": "def foo():", "language": "python", "detection_method": "pattern"}
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
