#!/usr/bin/env python3
"""
PDF Text Extractor - Complete Feature Set (Tasks B1.2 + B1.3 + B1.4 + B1.5 + Priority 2 & 3)

Extracts text, code blocks, and images from PDF documentation files.
Uses PyMuPDF (fitz) for fast, high-quality extraction.

Features:
    - Text and markdown extraction
    - Code block detection (font, indent, pattern)
    - Language detection with confidence scoring (19+ languages) (B1.4)
    - Syntax validation and quality scoring (B1.4)
    - Quality statistics and filtering (B1.4)
    - Image extraction to files (B1.5)
    - Image filtering by size (B1.5)
    - Page chunking and chapter detection (B1.3)
    - Code block merging across pages (B1.3)

Advanced Features (Priority 2 & 3):
    - OCR support for scanned PDFs (requires pytesseract) (Priority 2)
    - Password-protected PDF support (Priority 2)
    - Table extraction (Priority 2)
    - Parallel page processing (Priority 3)
    - Caching of expensive operations (Priority 3)

Usage:
    # Basic extraction
    python3 pdf_extractor_poc.py input.pdf
    python3 pdf_extractor_poc.py input.pdf --output output.json
    python3 pdf_extractor_poc.py input.pdf --verbose

    # Quality filtering
    python3 pdf_extractor_poc.py input.pdf --min-quality 5.0

    # Image extraction
    python3 pdf_extractor_poc.py input.pdf --extract-images
    python3 pdf_extractor_poc.py input.pdf --extract-images --image-dir images/

    # Advanced features
    python3 pdf_extractor_poc.py scanned.pdf --ocr
    python3 pdf_extractor_poc.py encrypted.pdf --password mypassword
    python3 pdf_extractor_poc.py input.pdf --extract-tables
    python3 pdf_extractor_poc.py large.pdf --parallel --workers 8

Example:
    python3 pdf_extractor_poc.py docs/manual.pdf -o output.json -v \
        --pdf-pages-per-chunk 15 --min-quality 6.0 --extract-images \
        --extract-tables --parallel
"""

import argparse
import json
import os
import re
import sys
import threading
from pathlib import Path

# Import unified language detector
from skill_seekers.cli.language_detector import LanguageDetector

# Check if PyMuPDF is installed
try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF not installed")
    print("Install with: pip install PyMuPDF")
    sys.exit(1)

# Optional dependencies for advanced features
try:
    import pytesseract
    from PIL import Image

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import concurrent.futures

    CONCURRENT_AVAILABLE = True
except ImportError:
    CONCURRENT_AVAILABLE = False


class PDFExtractor:
    """Extract text and code from PDF documentation"""

    VECTOR_FIGURE_MIN_WIDTH = 70
    VECTOR_FIGURE_MIN_HEIGHT = 55
    VECTOR_FIGURE_MARGIN = 20
    # A label may nudge each side of the clip by at most this much, so a text
    # block touching the margin can never drag the page body into the figure.
    VECTOR_LABEL_MAX_GROWTH = 60
    # PyMuPDF's own default. A tighter value splits ordinary block diagrams.
    VECTOR_CLUSTER_TOLERANCE = 3
    # Clusters closer than this belong to one figure; diagram shapes typically
    # sit 10-40pt apart and arrive from cluster_drawings() as separate rects.
    VECTOR_MERGE_GAP = 24
    # Dense scatter plots, maps and CAD exports: clustering costs minutes per
    # page and never yields a usable figure, so bail out before paying for it.
    VECTOR_MAX_DRAWINGS = 2000
    VECTOR_MAX_CLUSTERS = 400
    # Spatial-index cell size (points) for cluster/drawing bucketing.
    VECTOR_GRID_CELL = 64
    # Raster and vector regions are the same object above this IoU.
    VECTOR_RASTER_DUPLICATE_IOU = 0.75

    def __init__(
        self,
        pdf_path,
        verbose=False,
        chunk_size=10,
        min_quality=0.0,
        extract_images=False,
        image_dir=None,
        min_image_size=100,
        use_ocr=False,
        password=None,
        extract_tables=False,
        parallel=False,
        max_workers=None,
        use_cache=True,
    ):
        self.pdf_path = pdf_path
        self.verbose = verbose
        self.chunk_size = chunk_size  # Pages per chunk (0 = no chunking)
        self.min_quality = min_quality  # Minimum quality score (0-10)
        self.extract_images = extract_images  # Extract images to files (NEW in B1.5)
        self.image_dir = image_dir  # Directory to save images (NEW in B1.5)
        self.min_image_size = min_image_size  # Minimum image dimension (NEW in B1.5)

        # Advanced features (Priority 2 & 3)
        self.use_ocr = use_ocr  # OCR for scanned PDFs (Priority 2)
        self.password = password  # Password for encrypted PDFs (Priority 2)
        self.extract_tables = extract_tables  # Extract tables (Priority 2)
        self.parallel = parallel  # Parallel processing (Priority 3)
        self.max_workers = max_workers or os.cpu_count()  # Worker threads (Priority 3)
        self.use_cache = use_cache  # Cache expensive operations (Priority 3)

        self.doc = None
        self.pages = []
        self.chapters = []  # Detected chapters/sections
        self.extracted_images = []  # List of extracted image info (NEW in B1.5)
        # Guards the appends made while extracting a page. These appends are what
        # populate extracted_images for callers that drive extract_images_from_page
        # directly; extract_all() ignores them and rebuilds the list from
        # self.pages so the aggregate is page-ordered rather than worker-ordered.
        self._image_lock = threading.Lock()
        self._cache = {}  # Cache for expensive operations (Priority 3)

        # Language detection
        self.language_detector = LanguageDetector(min_confidence=0.15)

    def log(self, message):
        """Print message if verbose mode enabled"""
        if self.verbose:
            print(message)

    def extract_text_with_ocr(self, page):
        """
        Extract text from scanned PDF page using OCR (Priority 2).
        Falls back to regular text extraction if OCR is not available.

        Args:
            page: PyMuPDF page object

        Returns:
            str: Extracted text
        """
        # Try regular text extraction first
        text = page.get_text("text").strip()

        # If page has very little text, it might be scanned
        if len(text) < 50 and self.use_ocr:
            if not TESSERACT_AVAILABLE:
                self.log("⚠️  OCR requested but pytesseract not installed")
                self.log("   Install with: pip install pytesseract Pillow")
                return text

            try:
                # Render page as image
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Run OCR
                ocr_text = pytesseract.image_to_string(img)
                self.log(f"   OCR extracted {len(ocr_text)} chars (was {len(text)})")
                return ocr_text if len(ocr_text) > len(text) else text

            except Exception as e:
                self.log(f"   OCR failed: {e}")
                return text

        return text

    def extract_tables_from_page(self, page):
        """
        Extract tables from PDF page (Priority 2).
        Uses PyMuPDF's table detection.

        Args:
            page: PyMuPDF page object

        Returns:
            list: List of extracted tables as dicts
        """
        if not self.extract_tables:
            return []

        tables = []
        try:
            # PyMuPDF table extraction
            tabs = page.find_tables()
            for idx, tab in enumerate(tabs.tables):
                table_data = {
                    "table_index": idx,
                    "rows": tab.extract(),
                    "bbox": tab.bbox,
                    "row_count": len(tab.extract()),
                    "col_count": len(tab.extract()[0]) if tab.extract() else 0,
                }
                tables.append(table_data)
                self.log(
                    f"   Found table {idx}: {table_data['row_count']}x{table_data['col_count']}"
                )

        except Exception as e:
            self.log(f"   Table extraction failed: {e}")

        return tables

    def get_cached(self, key):
        """
        Get cached value (Priority 3).

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.use_cache:
            return None
        return self._cache.get(key)

    def set_cached(self, key, value):
        """
        Set cached value (Priority 3).

        Args:
            key: Cache key
            value: Value to cache
        """
        if self.use_cache:
            self._cache[key] = value

    def detect_language_from_code(self, code):
        """
        Detect programming language from code content using patterns.
        Enhanced in B1.4 with confidence scoring.

        UPDATED: Now uses shared LanguageDetector with 20+ languages

        Returns (language, confidence) tuple
        """
        return self.language_detector.detect_from_code(code)

    def validate_code_syntax(self, code, language):
        """
        Validate code syntax (basic checks).
        Enhanced in B1.4 with syntax validation.

        Returns (is_valid, issues) tuple
        """
        issues = []

        # Common syntax checks
        if not code.strip():
            return False, ["Empty code block"]

        # Language-specific validation
        if language == "python":
            # Check indentation consistency
            lines = code.split("\n")
            indent_chars = set()
            for line in lines:
                if line.startswith(" "):
                    indent_chars.add("space")
                elif line.startswith("\t"):
                    indent_chars.add("tab")

            if len(indent_chars) > 1:
                issues.append("Mixed tabs and spaces")

            # Check for unclosed brackets/parens
            open_count = code.count("(") + code.count("[") + code.count("{")
            close_count = code.count(")") + code.count("]") + code.count("}")
            if abs(open_count - close_count) > 2:  # Allow small mismatch
                issues.append("Unbalanced brackets")

        elif language in ["javascript", "java", "cpp", "c", "csharp", "go"]:
            # Check for balanced braces
            open_braces = code.count("{")
            close_braces = code.count("}")
            if abs(open_braces - close_braces) > 1:
                issues.append("Unbalanced braces")

        elif language == "json":
            # Try to parse JSON
            try:
                json.loads(code)
            except (json.JSONDecodeError, ValueError) as e:
                issues.append(f"Invalid JSON syntax: {str(e)[:50]}")

        # General checks
        # Check if code looks like natural language (too many common words)
        common_words = ["the", "and", "for", "with", "this", "that", "have", "from"]
        word_count = sum(1 for word in common_words if word in code.lower())
        if word_count > 5 and len(code.split()) < 50:
            issues.append("May be natural language, not code")

        # Check code/comment ratio
        comment_lines = sum(
            1 for line in code.split("\n") if line.strip().startswith(("#", "//", "/*", "*", "--"))
        )
        total_lines = len([line for line in code.split("\n") if line.strip()])
        if total_lines > 0 and comment_lines / total_lines > 0.7:
            issues.append("Mostly comments")

        return len(issues) == 0, issues

    def score_code_quality(self, code, language, confidence):
        """
        Score the quality/usefulness of detected code block.
        New in B1.4.

        Returns quality score (0-10)
        """
        score = 5.0  # Start with neutral score

        # Factor 1: Language detection confidence
        score += confidence * 2.0

        # Factor 2: Code length (not too short, not too long)
        code_length = len(code.strip())
        if 20 <= code_length <= 500:
            score += 1.0
        elif 500 < code_length <= 2000:
            score += 0.5
        elif code_length < 10:
            score -= 2.0

        # Factor 3: Number of lines
        lines = [line for line in code.split("\n") if line.strip()]
        if 2 <= len(lines) <= 50:
            score += 1.0
        elif len(lines) > 100:
            score -= 1.0

        # Factor 4: Has function/class definitions
        if re.search(r"\b(def|function|class|func|fn|public class)\b", code):
            score += 1.5

        # Factor 5: Has meaningful variable names (not just x, y, i)
        meaningful_vars = re.findall(r"\b[a-z_][a-z0-9_]{3,}\b", code.lower())
        if len(meaningful_vars) >= 2:
            score += 1.0

        # Factor 6: Syntax validation
        is_valid, issues = self.validate_code_syntax(code, language)
        if is_valid:
            score += 1.0
        else:
            score -= len(issues) * 0.5

        # Clamp score to 0-10 range
        return max(0, min(10, score))

    def detect_code_blocks_by_font(self, page):
        """
        Detect code blocks by analyzing font properties.
        Monospace fonts typically indicate code.

        Returns list of detected code blocks with metadata.
        """
        code_blocks = []
        blocks = page.get_text("dict")["blocks"]

        monospace_fonts = ["courier", "mono", "consolas", "menlo", "monaco", "dejavu"]

        current_code = []
        current_font = None

        for block in blocks:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                for span in line["spans"]:
                    font = span["font"].lower()
                    text = span["text"]

                    # Check if font is monospace
                    is_monospace = any(mf in font for mf in monospace_fonts)

                    if is_monospace:
                        # Accumulate code text
                        current_code.append(text)
                        current_font = span["font"]
                    else:
                        # End of code block
                        if current_code:
                            code_text = "".join(current_code).strip()
                            if len(code_text) > 10:  # Minimum code length
                                lang, confidence = self.detect_language_from_code(code_text)
                                quality = self.score_code_quality(code_text, lang, confidence)
                                is_valid, issues = self.validate_code_syntax(code_text, lang)

                                code_blocks.append(
                                    {
                                        "code": code_text,
                                        "language": lang,
                                        "confidence": confidence,
                                        "quality_score": quality,
                                        "is_valid": is_valid,
                                        "validation_issues": issues if not is_valid else [],
                                        "font": current_font,
                                        "detection_method": "font",
                                    }
                                )
                            current_code = []
                            current_font = None

        # Handle final code block
        if current_code:
            code_text = "".join(current_code).strip()
            if len(code_text) > 10:
                lang, confidence = self.detect_language_from_code(code_text)
                quality = self.score_code_quality(code_text, lang, confidence)
                is_valid, issues = self.validate_code_syntax(code_text, lang)

                code_blocks.append(
                    {
                        "code": code_text,
                        "language": lang,
                        "confidence": confidence,
                        "quality_score": quality,
                        "is_valid": is_valid,
                        "validation_issues": issues if not is_valid else [],
                        "font": current_font,
                        "detection_method": "font",
                    }
                )

        return code_blocks

    def detect_code_blocks_by_indent(self, text):
        """
        Detect code blocks by indentation patterns.
        Code often has consistent indentation.

        Returns list of detected code blocks.
        """
        code_blocks = []
        lines = text.split("\n")
        current_block = []
        indent_pattern = None

        for line in lines:
            # Check for indentation (4 spaces or tab)
            if line.startswith("    ") or line.startswith("\t"):
                # Start or continue code block
                if not indent_pattern:
                    indent_pattern = line[:4] if line.startswith("    ") else "\t"
                current_block.append(line)
            else:
                # End of code block
                if current_block and len(current_block) >= 2:  # At least 2 lines
                    code_text = "\n".join(current_block).strip()
                    if len(code_text) > 20:  # Minimum code length
                        lang, confidence = self.detect_language_from_code(code_text)
                        quality = self.score_code_quality(code_text, lang, confidence)
                        is_valid, issues = self.validate_code_syntax(code_text, lang)

                        code_blocks.append(
                            {
                                "code": code_text,
                                "language": lang,
                                "confidence": confidence,
                                "quality_score": quality,
                                "is_valid": is_valid,
                                "validation_issues": issues if not is_valid else [],
                                "detection_method": "indent",
                            }
                        )
                current_block = []
                indent_pattern = None

        # Handle final block
        if current_block and len(current_block) >= 2:
            code_text = "\n".join(current_block).strip()
            if len(code_text) > 20:
                lang, confidence = self.detect_language_from_code(code_text)
                quality = self.score_code_quality(code_text, lang, confidence)
                is_valid, issues = self.validate_code_syntax(code_text, lang)

                code_blocks.append(
                    {
                        "code": code_text,
                        "language": lang,
                        "confidence": confidence,
                        "quality_score": quality,
                        "is_valid": is_valid,
                        "validation_issues": issues if not is_valid else [],
                        "detection_method": "indent",
                    }
                )

        return code_blocks

    def detect_code_blocks_by_pattern(self, text):
        """
        Detect code blocks by common code patterns (keywords, syntax).

        Returns list of detected code snippets.
        """
        code_blocks = []

        # Common code patterns that span multiple lines
        patterns = [
            # Function definitions
            (
                r"((?:def|function|func|fn|public|private)\s+\w+\s*\([^)]*\)\s*[{:]?[^}]*[}]?)",
                "function",
            ),
            # Class definitions
            (r"(class\s+\w+[^{]*\{[^}]*\})", "class"),
            # Import statements block
            (
                r"((?:import|require|use|include)[^\n]+(?:\n(?:import|require|use|include)[^\n]+)*)",
                "imports",
            ),
        ]

        for pattern, block_type in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                code_text = match.group(1).strip()
                if len(code_text) > 15:
                    lang, confidence = self.detect_language_from_code(code_text)
                    quality = self.score_code_quality(code_text, lang, confidence)
                    is_valid, issues = self.validate_code_syntax(code_text, lang)

                    code_blocks.append(
                        {
                            "code": code_text,
                            "language": lang,
                            "confidence": confidence,
                            "quality_score": quality,
                            "is_valid": is_valid,
                            "validation_issues": issues if not is_valid else [],
                            "detection_method": "pattern",
                            "pattern_type": block_type,
                        }
                    )

        return code_blocks

    def detect_chapter_start(self, page_data):
        """
        Detect if a page starts a new chapter/section.

        Returns (is_chapter_start, chapter_title) tuple.
        """
        headings = page_data.get("headings", [])

        # Check for h1 or h2 at start of page
        if headings:
            first_heading = headings[0]
            # H1 headings are strong indicators of chapters
            if first_heading["level"] in ["h1", "h2"]:
                return True, first_heading["text"]

        # Check for specific chapter markers in text
        text = page_data.get("text", "")
        first_line = text.split("\n")[0] if text else ""

        chapter_patterns = [
            r"^Chapter\s+\d+",
            r"^Part\s+\d+",
            r"^Section\s+\d+",
            r"^\d+\.\s+[A-Z]",  # "1. Introduction"
        ]

        for pattern in chapter_patterns:
            if re.match(pattern, first_line, re.IGNORECASE):
                return True, first_line.strip()

        return False, None

    def merge_continued_code_blocks(self, pages):
        """
        Merge code blocks that are split across pages.

        Detects when a code block at the end of one page continues
        on the next page.
        """
        for i in range(len(pages) - 1):
            current_page = pages[i]
            next_page = pages[i + 1]

            # Check if current page has code blocks
            if not current_page["code_samples"]:
                continue

            # Get last code block of current page
            last_code = current_page["code_samples"][-1]

            # Check if next page starts with code
            if not next_page["code_samples"]:
                continue

            first_next_code = next_page["code_samples"][0]

            # Same language and detection method = likely continuation
            if (
                last_code["language"] == first_next_code["language"]
                and last_code["detection_method"] == first_next_code["detection_method"]
            ):
                # Only merge when the block looks genuinely UNFINISHED. The old
                # `any([not endswith("}"), not endswith(";"), ...])` was true for
                # almost every snippet (a block can't end with both } and ;), so
                # it merged unrelated adjacent blocks. Require a real continuation
                # token (trailing comma/backslash, or an unbalanced bracket).
                last_code_text = last_code["code"].rstrip()
                opens = sum(last_code_text.count(c) for c in "({[")
                closes = sum(last_code_text.count(c) for c in ")}]")
                is_incomplete = (
                    # trailing continuation/operator, or a block-opener colon
                    # (e.g. `def f():` whose body continues on the next page)
                    last_code_text.endswith((",", "\\", "+", "(", "[", "{", "=", ":"))
                    or opens > closes
                )

                if is_incomplete:
                    # Merge the code blocks
                    merged_code = last_code["code"] + "\n" + first_next_code["code"]
                    last_code["code"] = merged_code
                    last_code["merged_from_next_page"] = True

                    # Remove the first code block from next page and keep BOTH
                    # pages' counts consistent with their code_samples lists
                    # (the next-page count was decremented but the current page's
                    # was never updated).
                    next_page["code_samples"].pop(0)
                    current_page["code_blocks_count"] = len(current_page["code_samples"])
                    next_page["code_blocks_count"] = len(next_page["code_samples"])

                    self.log(f"  Merged code block from page {i + 1} to {i + 2}")

        return pages

    def create_chunks(self, pages):
        """
        Create chunks of pages for better organization.

        Returns array of chunks, each containing:
        - chunk_number
        - start_page, end_page
        - pages (array)
        - chapter_title (if detected)
        """
        if self.chunk_size == 0:
            # No chunking - return all pages as one chunk
            return [
                {
                    "chunk_number": 1,
                    "start_page": 1,
                    "end_page": len(pages),
                    "pages": pages,
                    "chapter_title": None,
                }
            ]

        chunks = []
        current_chunk = []
        chunk_start = 0
        current_chapter = None

        for i, page in enumerate(pages):
            # Check if this page starts a new chapter
            is_chapter, chapter_title = self.detect_chapter_start(page)

            if is_chapter and current_chunk:
                # Save current chunk before starting new one
                chunks.append(
                    {
                        "chunk_number": len(chunks) + 1,
                        "start_page": chunk_start + 1,
                        "end_page": i,
                        "pages": current_chunk,
                        "chapter_title": current_chapter,
                    }
                )
                current_chunk = []
                chunk_start = i
                current_chapter = chapter_title

            if not current_chapter and is_chapter:
                current_chapter = chapter_title

            current_chunk.append(page)

            # Check if chunk size reached (but don't break chapters)
            if not is_chapter and len(current_chunk) >= self.chunk_size:
                chunks.append(
                    {
                        "chunk_number": len(chunks) + 1,
                        "start_page": chunk_start + 1,
                        "end_page": i + 1,
                        "pages": current_chunk,
                        "chapter_title": current_chapter,
                    }
                )
                current_chunk = []
                chunk_start = i + 1
                current_chapter = None

        # Add remaining pages as final chunk
        if current_chunk:
            chunks.append(
                {
                    "chunk_number": len(chunks) + 1,
                    "start_page": chunk_start + 1,
                    "end_page": len(pages),
                    "pages": current_chunk,
                    "chapter_title": current_chapter,
                }
            )

        return chunks

    def extract_images_from_page(self, page, page_num):
        """
        Extract images from a PDF page and save to disk (NEW in B1.5).

        Returns list of extracted image metadata.
        """
        if not self.extract_images:
            # Just count images, don't extract
            return []

        extracted = []
        image_list = page.get_images()
        image_boxes = self._raster_bboxes_by_xref(page)
        extracted_xrefs = set()

        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]  # Image XREF number
                base_image = self.doc.extract_image(xref)

                if not base_image:
                    continue

                image_bytes = base_image["image"]
                image_ext = base_image["ext"]  # png, jpeg, etc.
                width = base_image.get("width", 0)
                height = base_image.get("height", 0)

                # Filter out small images (icons, bullets, etc.)
                if width < self.min_image_size or height < self.min_image_size:
                    self.log(f"    Skipping small image: {width}x{height}")
                    continue

                # Generate filename
                pdf_basename = Path(self.pdf_path).stem
                image_filename = f"{pdf_basename}_page{page_num + 1}_img{img_index + 1}.{image_ext}"

                # Save image
                image_path = Path(self.image_dir) / image_filename
                image_path.parent.mkdir(parents=True, exist_ok=True)

                with open(image_path, "wb") as f:
                    f.write(image_bytes)

                # Store metadata
                image_info = {
                    "filename": image_filename,
                    "path": str(image_path),
                    "page_number": page_num + 1,
                    "width": width,
                    "height": height,
                    "format": image_ext,
                    "size_bytes": len(image_bytes),
                    "xref": xref,
                    # Kept in step with the vector entries below so every item in
                    # extracted_images has the same shape.
                    "source": "raster",
                    "bbox": image_boxes.get(xref),
                }

                extracted.append(image_info)
                extracted_xrefs.add(xref)
                with self._image_lock:
                    self.extracted_images.append(image_info)
                self.log(f"    Extracted image: {image_filename} ({width}x{height})")

            except Exception as e:
                self.log(f"    Error extracting image {img_index}: {e}")
                continue

        try:
            extracted.extend(self.extract_vector_images_from_page(page, page_num, extracted_xrefs))
        except Exception as e:
            # Vector extraction is an optional fallback; never lose raster output
            # because a malformed drawing or render fails.
            self.log(f"    Error extracting vector figures: {e}")
        return extracted

    @staticmethod
    def _rect_overlap_ratio(first, second):
        """Return intersection area as a ratio of the smaller rectangle."""
        intersection = fitz.Rect(
            max(first.x0, second.x0),
            max(first.y0, second.y0),
            min(first.x1, second.x1),
            min(first.y1, second.y1),
        )
        if intersection.width <= 0 or intersection.height <= 0:
            return 0.0

        smaller_area = min(first.get_area(), second.get_area())
        return intersection.get_area() / smaller_area if smaller_area else 0.0

    @staticmethod
    def _rect_iou(first, second):
        """Return intersection over union: a symmetric "same object" measure.

        Used for raster/vector de-duplication. _rect_overlap_ratio divides by the
        smaller rectangle, so a contained thumbnail scores 1.0 and would suppress
        the entire figure enclosing it.
        """
        intersection = fitz.Rect(
            max(first.x0, second.x0),
            max(first.y0, second.y0),
            min(first.x1, second.x1),
            min(first.y1, second.y1),
        )
        if intersection.width <= 0 or intersection.height <= 0:
            return 0.0

        overlap = intersection.get_area()
        union = first.get_area() + second.get_area() - overlap
        return overlap / union if union else 0.0

    @staticmethod
    def _union_rect(first, second):
        """Union two rectangles, keeping degenerate ones.

        fitz.Rect.__or__ silently ignores empty rectangles, which is wrong here:
        a ruled table's gridlines are exactly zero-width and zero-height rects,
        so unioning with `|` collapses their bounding box to nothing.
        """
        if first is None:
            return fitz.Rect(second)
        return fitz.Rect(
            min(first.x0, second.x0),
            min(first.y0, second.y0),
            max(first.x1, second.x1),
            max(first.y1, second.y1),
        )

    @staticmethod
    def _rect_gap(first, second):
        """Edge-to-edge distance between two rectangles (0 when they touch)."""
        horizontal = max(first.x0 - second.x1, second.x0 - first.x1, 0)
        vertical = max(first.y0 - second.y1, second.y0 - first.y1, 0)
        return max(horizontal, vertical)

    @staticmethod
    def _grid_keys(rect, cell):
        """Yield the integer grid cells a rectangle touches."""
        for x in range(int(rect.x0 // cell), int(rect.x1 // cell) + 1):
            for y in range(int(rect.y0 // cell), int(rect.y1 // cell) + 1):
                yield (x, y)

    @staticmethod
    def _is_page_decoration(rect, page_rect):
        """Reject page frames and separator rules.

        Deliberately near-full-bleed: this runs per drawing before clustering, so
        a looser threshold strips a chart's baseline axis or a figure's own border
        and then fragments the figure it belonged to.
        """
        if rect.width >= page_rect.width * 0.85 and rect.height >= page_rect.height * 0.85:
            return True

        is_horizontal_rule = rect.width >= page_rect.width * 0.9 and rect.height <= 3
        is_vertical_rule = rect.height >= page_rect.height * 0.9 and rect.width <= 3
        return is_horizontal_rule or is_vertical_rule

    @staticmethod
    def _is_axis_aligned_rectish(drawing):
        """True when a drawing is built only from rectangles and axis-parallel lines."""
        items = drawing.get("items") or ()
        for item in items:
            operator = item[0]
            if operator == "re":
                continue
            if operator == "l":
                start, end = item[1], item[2]
                if abs(start.x - end.x) <= 1 or abs(start.y - end.y) <= 1:
                    continue
            return False
        return True

    @staticmethod
    def _is_block_background(drawing, page_rect):
        """True for wide fill-only bands: code-block, callout and admonition shading.

        These satisfy the "several drawings, several fills" test below, so without
        this an ordinary docs PDF emits a PNG of its own shaded code blocks.
        """
        if drawing.get("type") != "f" or drawing.get("fill") is None:
            return False

        rect = fitz.Rect(drawing["rect"])
        return rect.width >= page_rect.width * 0.6 and rect.height >= 20

    @classmethod
    def _is_table_grid(cls, drawings, region=None):
        """Reject line-ruled tables without discarding charts or diagrams.

        A table is a lattice of thin rules that spans its own bounding box and
        holds nothing but axis-aligned cells. A chart with gridlines has a curved
        or diagonal data path, and a diagram that merely contains a small legend
        table has rules covering only a fraction of the cluster.
        """
        vertical = 0
        horizontal = 0
        rules = None
        others = []
        for drawing in drawings:
            rect = fitz.Rect(drawing["rect"])
            if rect.width <= 3 and rect.height >= 20:
                vertical += 1
            elif rect.height <= 3 and rect.width >= 20:
                horizontal += 1
            else:
                others.append(drawing)
                continue
            rules = cls._union_rect(rules, rect)

        if vertical < 3 or horizontal < 3:
            return False

        if not all(cls._is_axis_aligned_rectish(drawing) for drawing in others):
            return False

        if region is not None and rules is not None and region.get_area() > 0:
            return rules.get_area() / region.get_area() >= 0.6
        return True

    def _vector_region_is_meaningful(self, rect, drawings, page_rect):
        """Apply conservative size and structure checks to a drawing cluster."""
        if rect.width < self.VECTOR_FIGURE_MIN_WIDTH or rect.height < self.VECTOR_FIGURE_MIN_HEIGHT:
            return False

        content = [
            drawing for drawing in drawings if not self._is_block_background(drawing, page_rect)
        ]
        if not content or self._is_table_grid(content, rect):
            return False

        # A figure is either several shapes or one complex path, which is how
        # most SVG-derived charts and logos land in a PDF.
        complex_path = any(len(drawing.get("items") or ()) >= 8 for drawing in content)
        if len(content) < 3 and not complex_path:
            return False

        filled = sum(1 for drawing in content if drawing.get("fill") is not None)
        stroked = sum(1 for drawing in content if drawing.get("type") in {"s", "fs"})
        return filled >= 2 or stroked >= 5 or complex_path

    def _expand_vector_region(self, page, rect, text_blocks=None):
        """Add a small margin and pull in labels that touch it.

        Overlap is tested against the fixed margin rect, never against the growing
        result: unioning in place makes each newly included block touch the next
        one, which walks the clip down the entire page in tight layouts.
        """
        page_rect = page.rect
        margin = self.VECTOR_FIGURE_MARGIN
        base = fitz.Rect(
            max(page_rect.x0, rect.x0 - margin),
            max(page_rect.y0, rect.y0 - margin),
            min(page_rect.x1, rect.x1 + margin),
            min(page_rect.y1, rect.y1 + margin),
        )

        if text_blocks is None:
            try:
                text_blocks = page.get_text("blocks")
            except (AttributeError, RuntimeError, ValueError):
                text_blocks = []

        expanded = fitz.Rect(base)
        for block in text_blocks:
            if len(block) < 7 or block[6] != 0:
                continue
            text_rect = fitz.Rect(block[:4])
            if self._rect_overlap_ratio(base, text_rect) > 0:
                expanded = self._union_rect(expanded, text_rect)

        growth = self.VECTOR_LABEL_MAX_GROWTH
        return fitz.Rect(
            max(page_rect.x0, base.x0 - growth, expanded.x0),
            max(page_rect.y0, base.y0 - growth, expanded.y0),
            min(page_rect.x1, base.x1 + growth, expanded.x1),
            min(page_rect.y1, base.y1 + growth, expanded.y1),
        )

    @staticmethod
    def _separate_vector_clip(clip, region, obstacles):
        """Keep label margins from crossing into a neighbour.

        `obstacles` holds the sibling figure regions plus any raster written as its
        own asset, so a nearby screenshot is not baked into this PNG as well.
        """
        for other in obstacles:
            if other is region:
                continue

            if region.x1 <= other.x0 and clip.x1 > other.x0:
                clip = fitz.Rect(
                    clip.x0,
                    clip.y0,
                    min(clip.x1, (region.x1 + other.x0) / 2),
                    clip.y1,
                )
            elif region.x0 >= other.x1 and clip.x0 < other.x1:
                clip = fitz.Rect(
                    max(clip.x0, (other.x1 + region.x0) / 2),
                    clip.y0,
                    clip.x1,
                    clip.y1,
                )
            elif region.y1 <= other.y0 and clip.y1 > other.y0:
                clip = fitz.Rect(
                    clip.x0,
                    clip.y0,
                    clip.x1,
                    min(clip.y1, (region.y1 + other.y0) / 2),
                )
            elif region.y0 >= other.y1 and clip.y0 < other.y1:
                clip = fitz.Rect(
                    clip.x0,
                    max(clip.y0, (other.y1 + region.y0) / 2),
                    clip.x1,
                    clip.y1,
                )

        return clip

    @staticmethod
    def _raster_bboxes_by_xref(page):
        """Map image xref to its page bbox, so raster entries carry a `bbox` too."""
        boxes = {}
        try:
            for image in page.get_image_info(xrefs=True):
                rect = fitz.Rect(image["bbox"])
                boxes[image.get("xref")] = [rect.x0, rect.y0, rect.x1, rect.y1]
        except (AttributeError, KeyError, RuntimeError, TypeError, ValueError):
            pass
        return boxes

    def _raster_rects(self, page, raster_xrefs=None):
        """Bounding boxes of rasters that were actually written as their own asset.

        An image whose extract_image() raised is skipped by the raster loop, so its
        box must not suppress an overlapping vector figure either — otherwise the
        content is lost from both paths.
        """
        rects = []
        try:
            for image in page.get_image_info(xrefs=True):
                if raster_xrefs is not None and image.get("xref") not in raster_xrefs:
                    continue
                if (
                    image.get("width", 0) >= self.min_image_size
                    and image.get("height", 0) >= self.min_image_size
                ):
                    rects.append(fitz.Rect(image["bbox"]))
        except (AttributeError, RuntimeError, TypeError, ValueError):
            pass
        return rects

    @classmethod
    def _merge_nearby_regions(cls, rects, gap, cell):
        """Union clusters separated by less than `gap`.

        cluster_drawings() groups near-touching geometry only, so a block diagram
        whose boxes sit 20pt apart arrives as one cluster per box and every one of
        them is then rejected as too small. Merging restores the figure first.
        """
        parent = list(range(len(rects)))

        def find(position):
            while parent[position] != position:
                parent[position] = parent[parent[position]]
                position = parent[position]
            return position

        index: dict[tuple[int, int], list[int]] = {}
        for position, rect in enumerate(rects):
            padded = fitz.Rect(rect.x0 - gap, rect.y0 - gap, rect.x1 + gap, rect.y1 + gap)
            for key in cls._grid_keys(padded, cell):
                index.setdefault(key, []).append(position)

        for bucket in index.values():
            for offset, first in enumerate(bucket):
                for second in bucket[offset + 1 :]:
                    if find(first) == find(second):
                        continue
                    if cls._rect_gap(rects[first], rects[second]) <= gap:
                        parent[find(first)] = find(second)

        groups: dict[int, fitz.Rect] = {}
        for position, rect in enumerate(rects):
            root = find(position)
            groups[root] = cls._union_rect(groups.get(root), rect)
        return list(groups.values())

    def _cluster_members(self, cluster_rects, drawings):
        """Map each cluster to the drawings it covers, via a coarse grid index.

        The naive form is O(clusters x drawings): a 3000-path page produces ~1700
        clusters and spends ~50s there. Bucketing cluster rects by grid cell means
        each drawing only tests the handful of clusters sharing one of its cells.
        """
        cell = self.VECTOR_GRID_CELL
        index: dict[tuple[int, int], list[int]] = {}
        for position, rect in enumerate(cluster_rects):
            for key in self._grid_keys(rect, cell):
                index.setdefault(key, []).append(position)

        members: list[list[dict]] = [[] for _ in cluster_rects]
        for drawing in drawings:
            drawing_rect = fitz.Rect(drawing["rect"])
            seen = set()
            for key in self._grid_keys(drawing_rect, cell):
                for position in index.get(key, ()):
                    if position in seen:
                        continue
                    seen.add(position)
                    cluster_rect = cluster_rects[position]
                    if self._rect_overlap_ratio(
                        cluster_rect, drawing_rect
                    ) > 0 or cluster_rect.contains(drawing_rect):
                        members[position].append(drawing)
        return members

    def extract_vector_images_from_page(self, page, page_num, raster_xrefs=None):
        """Render meaningful vector drawing clusters as PNG assets."""
        try:
            drawings = page.get_drawings()
        except (AttributeError, RuntimeError, ValueError):
            return []

        if len(drawings) > self.VECTOR_MAX_DRAWINGS:
            self.log(
                f"    Skipping vector extraction: {len(drawings)} drawings exceeds "
                f"VECTOR_MAX_DRAWINGS={self.VECTOR_MAX_DRAWINGS}"
            )
            return []

        page_rect = page.rect
        filtered_drawings = [
            drawing
            for drawing in drawings
            if not self._is_page_decoration(fitz.Rect(drawing["rect"]), page_rect)
        ]
        if not filtered_drawings or not hasattr(page, "cluster_drawings"):
            return []

        try:
            clusters = page.cluster_drawings(
                drawings=filtered_drawings,
                x_tolerance=self.VECTOR_CLUSTER_TOLERANCE,
                y_tolerance=self.VECTOR_CLUSTER_TOLERANCE,
            )
        except (AttributeError, RuntimeError, TypeError, ValueError):
            return []

        if len(clusters) > self.VECTOR_MAX_CLUSTERS:
            self.log(
                f"    Skipping vector extraction: {len(clusters)} clusters exceeds "
                f"VECTOR_MAX_CLUSTERS={self.VECTOR_MAX_CLUSTERS}"
            )
            return []

        cluster_rects = self._merge_nearby_regions(
            [fitz.Rect(cluster) for cluster in clusters],
            self.VECTOR_MERGE_GAP,
            self.VECTOR_GRID_CELL,
        )
        raster_rects = self._raster_rects(page, raster_xrefs)

        candidates = []
        members_by_cluster = self._cluster_members(cluster_rects, filtered_drawings)
        for rect, members in zip(cluster_rects, members_by_cluster, strict=True):
            if not self._vector_region_is_meaningful(rect, members, page_rect):
                continue
            if any(
                self._rect_iou(rect, raster_rect) >= self.VECTOR_RASTER_DUPLICATE_IOU
                for raster_rect in raster_rects
            ):
                continue
            candidates.append(rect)

        # Keep the largest region when merging leaves nested or overlapping rects.
        regions: list[fitz.Rect] = []
        for rect in sorted(
            candidates,
            key=lambda candidate: (
                -candidate.get_area(),
                candidate.y0,
                candidate.x0,
                candidate.y1,
                candidate.x1,
            ),
        ):
            if any(self._rect_overlap_ratio(rect, existing) >= 0.75 for existing in regions):
                continue
            regions.append(rect)

        # Emit in reading order: pdf_scraper renders extracted_images in list order,
        # and the vectorN suffix is only meaningful if it follows the page.
        regions.sort(key=lambda rect: (rect.y0, rect.x0))

        extracted: list[dict] = []
        pdf_basename = Path(self.pdf_path).stem
        text_blocks = []
        if regions:
            try:
                text_blocks = page.get_text("blocks")
            except (AttributeError, RuntimeError, ValueError):
                text_blocks = []

        for rect in regions:
            clip = self._expand_vector_region(page, rect, text_blocks)
            obstacles = [other for other in regions if other is not rect]
            obstacles.extend(
                raster_rect
                for raster_rect in raster_rects
                if self._rect_overlap_ratio(rect, raster_rect) <= 0
            )
            clip = self._separate_vector_clip(clip, rect, obstacles)
            try:
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=clip, alpha=False)
                image_bytes = pixmap.tobytes("png")
                width, height = pixmap.width, pixmap.height
            except (RuntimeError, ValueError):
                continue
            # Release the render buffer before the next clip; under --parallel every
            # worker thread is holding one of these at the same time.
            pixmap = None

            # Honour --min-image-size here too, on the same pixel basis the raster
            # path uses. Without it the flag silently does nothing for figures.
            if width < self.min_image_size or height < self.min_image_size:
                self.log(f"    Skipping small vector figure: {width}x{height}")
                continue

            image_filename = f"{pdf_basename}_page{page_num + 1}_vector{len(extracted) + 1}.png"
            image_path = Path(self.image_dir) / image_filename
            image_path.parent.mkdir(parents=True, exist_ok=True)
            with open(image_path, "wb") as image_file:
                image_file.write(image_bytes)

            image_info = {
                "filename": image_filename,
                "path": str(image_path),
                "page_number": page_num + 1,
                "width": width,
                "height": height,
                "format": "png",
                "size_bytes": len(image_bytes),
                "xref": None,
                "source": "vector",
                "bbox": [clip.x0, clip.y0, clip.x1, clip.y1],
            }
            extracted.append(image_info)
            with self._image_lock:
                self.extracted_images.append(image_info)
            self.log(f"    Extracted vector figure: {image_filename} ({width}x{height})")

        return extracted

    def extract_page(self, page_num):
        """
        Extract content from a single PDF page.

        Returns dict with page content, code blocks, and metadata.
        """
        # Check cache first (Priority 3)
        cache_key = f"page_{page_num}"
        cached = self.get_cached(cache_key)
        if cached is not None:
            self.log(f"  Page {page_num + 1}: Using cached data")
            return cached

        page = self.doc.load_page(page_num)

        # Extract plain text (with OCR if enabled - Priority 2)
        text = self.extract_text_with_ocr(page) if self.use_ocr else page.get_text("text")

        # Extract markdown (better structure preservation)
        # Use "text" format with layout info for PyMuDF 1.24+
        try:
            markdown = page.get_text("markdown")
        except (AssertionError, ValueError, RuntimeError, TypeError, AttributeError):
            # Fallback to text format for incompatible PyMuPDF versions
            # Some versions don't support "markdown" format or have internal errors
            markdown = page.get_text(
                "text",
                flags=fitz.TEXT_PRESERVE_WHITESPACE
                | fitz.TEXT_PRESERVE_LIGATURES
                | fitz.TEXT_PRESERVE_SPANS,
            )

        # Extract tables (Priority 2)
        tables = self.extract_tables_from_page(page)

        # Get page images (for diagrams)
        images = page.get_images()

        # Extract images to files (NEW in B1.5)
        extracted_images = self.extract_images_from_page(page, page_num)

        # Detect code blocks using multiple methods
        font_code_blocks = self.detect_code_blocks_by_font(page)
        indent_code_blocks = self.detect_code_blocks_by_indent(text)
        pattern_code_blocks = self.detect_code_blocks_by_pattern(text)

        # Merge and deduplicate code blocks
        all_code_blocks = font_code_blocks + indent_code_blocks + pattern_code_blocks

        # Simple deduplication by code content
        unique_code = {}
        for block in all_code_blocks:
            code_hash = hash(block["code"])
            if code_hash not in unique_code:
                unique_code[code_hash] = block
            else:
                # Keep the one with higher quality score
                if block["quality_score"] > unique_code[code_hash]["quality_score"]:
                    unique_code[code_hash] = block

        code_samples = list(unique_code.values())

        # Filter by minimum quality (NEW in B1.4)
        if self.min_quality > 0:
            code_samples_before = len(code_samples)
            code_samples = [c for c in code_samples if c["quality_score"] >= self.min_quality]
            filtered_count = code_samples_before - len(code_samples)
            if filtered_count > 0:
                self.log(
                    f"  Filtered out {filtered_count} low-quality code blocks (min_quality={self.min_quality})"
                )

        # Sort by quality score (highest first)
        code_samples.sort(key=lambda x: x["quality_score"], reverse=True)

        # Extract headings from markdown
        headings = []
        for line in markdown.split("\n"):
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                text = line.lstrip("#").strip()
                if text:
                    headings.append({"level": f"h{level}", "text": text})

        page_data = {
            "page_number": page_num + 1,  # 1-indexed for humans
            "text": text.strip(),
            "markdown": markdown.strip(),
            "headings": headings,
            "code_samples": code_samples,
            # Raster image objects present on the page. Vector figures have no
            # image object, so they are counted separately rather than folded in
            # here — total_images feeds the generated skill's statistics.
            "images_count": len(images),
            "vector_figures_count": sum(
                1 for image in extracted_images if image.get("source") == "vector"
            ),
            "extracted_images": extracted_images,  # NEW in B1.5
            "tables": tables,  # NEW in Priority 2
            "char_count": len(text),
            "code_blocks_count": len(code_samples),
            "tables_count": len(tables),  # NEW in Priority 2
        }

        # Cache the result (Priority 3)
        self.set_cached(cache_key, page_data)

        self.log(
            f"  Page {page_num + 1}: {len(text)} chars, {len(code_samples)} code blocks, {len(headings)} headings, {len(extracted_images)} images, {len(tables)} tables"
        )

        return page_data

    def extract_all(self):
        """
        Extract content from all pages of the PDF.
        Enhanced with password support and parallel processing.

        Returns dict with metadata and pages array.
        """
        print(f"\n📄 Extracting from: {self.pdf_path}")

        # Open PDF (with password support - Priority 2)
        try:
            self.doc = fitz.open(self.pdf_path)

            # Handle encrypted PDFs (Priority 2)
            if self.doc.is_encrypted:
                if self.password:
                    print("   🔐 PDF is encrypted, trying password...")
                    if self.doc.authenticate(self.password):
                        print("   ✅ Password accepted")
                    else:
                        print("   ❌ Invalid password")
                        return None
                else:
                    print("   ❌ PDF is encrypted but no password provided")
                    print("   Use --password option to provide password")
                    return None

        except Exception as e:
            print(f"❌ Error opening PDF: {e}")
            return None

        print(f"   Pages: {len(self.doc)}")
        print(f"   Metadata: {self.doc.metadata}")

        # Set up image directory (NEW in B1.5)
        if self.extract_images and not self.image_dir:
            pdf_basename = Path(self.pdf_path).stem
            self.image_dir = f"output/{pdf_basename}_images"
            print(f"   Image directory: {self.image_dir}")

        # Show feature status
        if self.use_ocr:
            status = (
                "✅ enabled" if TESSERACT_AVAILABLE else "⚠️  not available (install pytesseract)"
            )
            print(f"   OCR: {status}")
        if self.extract_tables:
            print("   Table extraction: ✅ enabled")
        if self.parallel:
            status = "✅ enabled" if CONCURRENT_AVAILABLE else "⚠️  not available"
            print(f"   Parallel processing: {status} ({self.max_workers} workers)")
        if self.use_cache:
            print("   Caching: ✅ enabled")

        print("")

        # Extract each page (with parallel processing - Priority 3)
        if self.parallel and CONCURRENT_AVAILABLE and len(self.doc) > 5:
            print(
                f"🚀 Extracting {len(self.doc)} pages in parallel ({self.max_workers} workers)..."
            )
            import contextvars

            # Propagate contextvars into worker threads (threads don't inherit
            # them), so per-call state like the MCP log-capture token survives.
            _caller_ctx = contextvars.copy_context()
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                page_numbers = list(range(len(self.doc)))
                self.pages = list(
                    executor.map(
                        lambda n: _caller_ctx.copy().run(self.extract_page, n), page_numbers
                    )
                )
        else:
            # Sequential extraction
            for page_num in range(len(self.doc)):
                page_data = self.extract_page(page_num)
                self.pages.append(page_data)

        # Rebuild the aggregate from page-ordered results so parallel extraction
        # cannot expose worker completion order or shared-list mutations.
        self.extracted_images = [
            image for page in self.pages for image in page.get("extracted_images", [])
        ]

        # Merge code blocks that span across pages
        self.log("\n🔗 Merging code blocks across pages...")
        self.pages = self.merge_continued_code_blocks(self.pages)

        # Create chunks
        self.log(f"\n📦 Creating chunks (chunk_size={self.chunk_size})...")
        chunks = self.create_chunks(self.pages)

        # Build summary
        total_chars = sum(p["char_count"] for p in self.pages)
        total_code_blocks = sum(p["code_blocks_count"] for p in self.pages)
        total_headings = sum(len(p["headings"]) for p in self.pages)
        total_images = sum(p["images_count"] for p in self.pages)
        total_vector_figures = sum(p.get("vector_figures_count", 0) for p in self.pages)
        total_tables = sum(p["tables_count"] for p in self.pages)  # NEW in Priority 2

        # Detect languages used
        languages = {}
        all_code_blocks_list = []
        for page in self.pages:
            for code in page["code_samples"]:
                lang = code["language"]
                languages[lang] = languages.get(lang, 0) + 1
                all_code_blocks_list.append(code)

        # Calculate quality statistics (NEW in B1.4)
        quality_stats = {}
        if all_code_blocks_list:
            quality_scores = [c["quality_score"] for c in all_code_blocks_list]
            confidences = [c["confidence"] for c in all_code_blocks_list]
            valid_count = sum(1 for c in all_code_blocks_list if c["is_valid"])

            quality_stats = {
                "average_quality": sum(quality_scores) / len(quality_scores),
                "average_confidence": sum(confidences) / len(confidences),
                "valid_code_blocks": valid_count,
                "invalid_code_blocks": total_code_blocks - valid_count,
                "validation_rate": valid_count / total_code_blocks if total_code_blocks > 0 else 0,
                "high_quality_blocks": sum(1 for s in quality_scores if s >= 7.0),
                "medium_quality_blocks": sum(1 for s in quality_scores if 4.0 <= s < 7.0),
                "low_quality_blocks": sum(1 for s in quality_scores if s < 4.0),
            }

        # Extract chapter information
        chapters = []
        for chunk in chunks:
            if chunk["chapter_title"]:
                chapters.append(
                    {
                        "title": chunk["chapter_title"],
                        "start_page": chunk["start_page"],
                        "end_page": chunk["end_page"],
                    }
                )

        result = {
            "source_file": self.pdf_path,
            "metadata": self.doc.metadata,
            "total_pages": len(self.doc),
            "total_chars": total_chars,
            "total_code_blocks": total_code_blocks,
            "total_headings": total_headings,
            "total_images": total_images,
            "total_vector_figures": total_vector_figures,
            "total_extracted_images": len(self.extracted_images),  # NEW in B1.5
            "total_tables": total_tables,  # NEW in Priority 2
            "image_directory": self.image_dir if self.extract_images else None,  # NEW in B1.5
            "extracted_images": self.extracted_images,  # NEW in B1.5
            "total_chunks": len(chunks),
            "chapters": chapters,
            "languages_detected": languages,
            "quality_statistics": quality_stats,  # NEW in B1.4
            "chunks": chunks,
            "pages": self.pages,  # Still include all pages for compatibility
        }

        # Close document
        self.doc.close()

        print("\n✅ Extraction complete:")
        print(f"   Total characters: {total_chars:,}")
        print(f"   Code blocks found: {total_code_blocks}")
        print(f"   Headings found: {total_headings}")
        print(f"   Raster images found: {total_images}")
        if total_vector_figures:
            print(f"   Vector figures found: {total_vector_figures}")
        if self.extract_images:
            print(f"   Images extracted: {len(self.extracted_images)}")
            if self.image_dir:
                print(f"   Image directory: {self.image_dir}")
        if self.extract_tables:
            print(f"   Tables found: {total_tables}")
        print(f"   Chunks created: {len(chunks)}")
        print(f"   Chapters detected: {len(chapters)}")
        print(f"   Languages detected: {', '.join(languages.keys())}")

        # Print quality statistics (NEW in B1.4)
        if quality_stats:
            print("\n📊 Code Quality Statistics:")
            print(f"   Average quality: {quality_stats['average_quality']:.1f}/10")
            print(f"   Average confidence: {quality_stats['average_confidence']:.1%}")
            print(
                f"   Valid code blocks: {quality_stats['valid_code_blocks']}/{total_code_blocks} ({quality_stats['validation_rate']:.1%})"
            )
            print(f"   High quality (7+): {quality_stats['high_quality_blocks']}")
            print(f"   Medium quality (4-7): {quality_stats['medium_quality_blocks']}")
            print(f"   Low quality (<4): {quality_stats['low_quality_blocks']}")

        return result


def main():
    parser = argparse.ArgumentParser(
        description="Extract text and code blocks from PDF documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract from PDF
  python3 pdf_extractor_poc.py input.pdf

  # Save to JSON file
  python3 pdf_extractor_poc.py input.pdf --output result.json

  # Verbose mode
  python3 pdf_extractor_poc.py input.pdf --verbose

  # Extract and save
  python3 pdf_extractor_poc.py docs/python.pdf -o python_extracted.json -v
        """,
    )

    parser.add_argument("pdf_file", help="Path to PDF file to extract")
    parser.add_argument("-o", "--output", help="Output JSON file path (default: print to stdout)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument(
        "--pdf-pages-per-chunk",
        type=int,
        default=10,
        help="Pages per chunk (0 = no chunking, default: 10)",
    )
    parser.add_argument(
        "--no-merge", action="store_true", help="Disable merging code blocks across pages"
    )
    parser.add_argument(
        "--min-quality",
        type=float,
        default=0.0,
        help="Minimum code quality score (0-10, default: 0 = no filtering)",
    )
    parser.add_argument(
        "--extract-images", action="store_true", help="Extract images to files (NEW in B1.5)"
    )
    parser.add_argument(
        "--image-dir",
        type=str,
        default=None,
        help="Directory to save extracted images (default: output/{pdf_name}_images)",
    )
    parser.add_argument(
        "--min-image-size",
        type=int,
        default=100,
        help="Minimum image dimension in pixels (filters icons, default: 100)",
    )

    # Advanced features (Priority 2 & 3)
    parser.add_argument(
        "--ocr", action="store_true", help="Use OCR for scanned PDFs (requires pytesseract)"
    )
    parser.add_argument("--password", type=str, default=None, help="Password for encrypted PDF")
    parser.add_argument(
        "--extract-tables", action="store_true", help="Extract tables from PDF (Priority 2)"
    )
    parser.add_argument(
        "--parallel", action="store_true", help="Process pages in parallel (Priority 3)"
    )
    parser.add_argument(
        "--workers", type=int, default=None, help="Number of parallel workers (default: CPU count)"
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="Disable caching of expensive operations"
    )

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.pdf_file):
        print(f"❌ Error: File not found: {args.pdf_file}")
        sys.exit(1)

    if not args.pdf_file.lower().endswith(".pdf"):
        print("⚠️  Warning: File does not have .pdf extension")

    # Extract
    extractor = PDFExtractor(
        args.pdf_file,
        verbose=args.verbose,
        chunk_size=args.pdf_pages_per_chunk,
        min_quality=args.min_quality,
        extract_images=args.extract_images,
        image_dir=args.image_dir,
        min_image_size=args.min_image_size,
        # Advanced features (Priority 2 & 3)
        use_ocr=args.ocr,
        password=args.password,
        extract_tables=args.extract_tables,
        parallel=args.parallel,
        max_workers=args.workers,
        use_cache=not args.no_cache,
    )
    result = extractor.extract_all()

    if result is None:
        sys.exit(1)

    # Output
    if args.output:
        # Save to file
        with open(args.output, "w", encoding="utf-8") as f:
            if args.pretty:
                json.dump(result, f, indent=2, ensure_ascii=False)
            else:
                json.dump(result, f, ensure_ascii=False)
        print(f"\n💾 Saved to: {args.output}")
    else:
        # Print to stdout
        if args.pretty:
            print("\n" + json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
