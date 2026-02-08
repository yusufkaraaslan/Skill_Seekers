#!/usr/bin/env python3
"""
Tests for multi-language documentation support.

Validates:
- Language detection (content and filename)
- Multi-language organization
- Translation status tracking
- Language filtering
- Export by language
"""

import pytest
from pathlib import Path
import sys
import tempfile
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from skill_seekers.cli.multilang_support import LanguageDetector, MultiLanguageManager


def test_detect_english():
    """Test English language detection."""
    detector = LanguageDetector()

    text = "This is an English document. It contains common English words."
    lang_info = detector.detect(text)

    assert lang_info.code == "en"
    assert lang_info.name == "English"
    assert lang_info.confidence > 0.0


def test_detect_spanish():
    """Test Spanish language detection."""
    detector = LanguageDetector()

    text = "Este es un documento en español. Contiene palabras comunes en español."
    lang_info = detector.detect(text)

    assert lang_info.code == "es"
    assert lang_info.name == "Spanish"


def test_detect_french():
    """Test French language detection."""
    detector = LanguageDetector()

    text = "Ceci est un document en français. Il contient des mots français communs."
    lang_info = detector.detect(text)

    assert lang_info.code == "fr"
    assert lang_info.name == "French"


def test_detect_german():
    """Test German language detection."""
    detector = LanguageDetector()

    text = "Dies ist ein deutsches Dokument. Es enthält übliche deutsche Wörter."
    lang_info = detector.detect(text)

    assert lang_info.code == "de"
    assert lang_info.name == "German"


def test_detect_chinese():
    """Test Chinese language detection."""
    detector = LanguageDetector()

    text = "这是一个中文文档。它包含常见的中文字符。"
    lang_info = detector.detect(text)

    assert lang_info.code == "zh"
    assert lang_info.name == "Chinese"


def test_detect_from_filename_dot_pattern():
    """Test language detection from filename (file.en.md pattern)."""
    detector = LanguageDetector()

    assert detector.detect_from_filename("README.en.md") == "en"
    assert detector.detect_from_filename("guide.es.md") == "es"
    assert detector.detect_from_filename("doc.fr.md") == "fr"


def test_detect_from_filename_underscore_pattern():
    """Test language detection from filename (file_en.md pattern)."""
    detector = LanguageDetector()

    assert detector.detect_from_filename("README_en.md") == "en"
    assert detector.detect_from_filename("guide_es.md") == "es"


def test_detect_from_filename_dash_pattern():
    """Test language detection from filename (file-en.md pattern)."""
    detector = LanguageDetector()

    assert detector.detect_from_filename("README-en.md") == "en"
    assert detector.detect_from_filename("guide-es.md") == "es"


def test_detect_from_filename_no_match():
    """Test filename with no language pattern."""
    detector = LanguageDetector()

    assert detector.detect_from_filename("README.md") is None
    assert detector.detect_from_filename("guide.txt") is None


def test_add_document_single_language():
    """Test adding documents in single language."""
    manager = MultiLanguageManager()

    manager.add_document("README.md", "This is an English document.", {"category": "overview"})

    assert len(manager.get_languages()) == 1
    assert "en" in manager.get_languages()
    assert manager.get_document_count("en") == 1


def test_add_document_multiple_languages():
    """Test adding documents in multiple languages."""
    manager = MultiLanguageManager()

    manager.add_document("README.md", "This is English.", {})
    manager.add_document("README.es.md", "Esto es español.", {})
    manager.add_document("README.fr.md", "Ceci est français.", {})

    assert len(manager.get_languages()) == 3
    assert "en" in manager.get_languages()
    assert "es" in manager.get_languages()
    assert "fr" in manager.get_languages()


def test_force_language():
    """Test forcing language override."""
    manager = MultiLanguageManager()

    # Force Spanish despite English content
    manager.add_document("file.md", "This is actually English content.", {}, force_language="es")

    assert "es" in manager.get_languages()
    assert manager.get_document_count("es") == 1


def test_filename_language_priority():
    """Test filename pattern takes priority over content detection."""
    manager = MultiLanguageManager()

    # Filename says Spanish, but content is English
    manager.add_document("guide.es.md", "This is English content.", {})

    # Should use filename language
    assert "es" in manager.get_languages()


def test_document_count_all():
    """Test total document count."""
    manager = MultiLanguageManager()

    manager.add_document("file1.md", "English doc 1", {})
    manager.add_document("file2.md", "English doc 2", {})
    manager.add_document("file3.es.md", "Spanish doc", {})

    assert manager.get_document_count() == 3
    assert manager.get_document_count("en") == 2
    assert manager.get_document_count("es") == 1


def test_primary_language():
    """Test primary language is set correctly."""
    manager = MultiLanguageManager()

    manager.add_document("file1.md", "First English doc", {})
    manager.add_document("file2.es.md", "Spanish doc", {})

    # Primary should be first added
    assert manager.primary_language == "en"


def test_translation_status():
    """Test translation status tracking."""
    manager = MultiLanguageManager()

    manager.add_document("README.md", "English doc", {})
    manager.add_document("README.es.md", "Spanish doc", {})
    manager.add_document("README.fr.md", "French doc", {})

    status = manager.get_translation_status()

    assert status.source_language == "en"
    assert "es" in status.translated_languages
    assert "fr" in status.translated_languages
    assert len(status.translated_languages) == 2


def test_export_by_language():
    """Test exporting documents by language."""
    manager = MultiLanguageManager()

    manager.add_document("file1.md", "English content", {})
    manager.add_document("file2.es.md", "Spanish content", {})

    with tempfile.TemporaryDirectory() as tmpdir:
        exports = manager.export_by_language(Path(tmpdir))

        assert len(exports) == 2
        assert "en" in exports
        assert "es" in exports

        # Check files exist
        assert exports["en"].exists()
        assert exports["es"].exists()

        # Check content
        en_data = json.loads(exports["en"].read_text())
        assert en_data["language"] == "en"
        assert en_data["document_count"] == 1


def test_translation_report_generation():
    """Test translation report generation."""
    manager = MultiLanguageManager()

    manager.add_document("file1.md", "English doc", {})
    manager.add_document("file2.es.md", "Spanish doc", {})

    report = manager.generate_translation_report()

    assert "MULTI-LANGUAGE DOCUMENTATION REPORT" in report
    assert "Languages: 2" in report
    assert "English (en)" in report
    assert "Spanish (es)" in report


def test_empty_manager():
    """Test manager with no documents."""
    manager = MultiLanguageManager()

    assert len(manager.get_languages()) == 0
    assert manager.get_document_count() == 0
    assert manager.primary_language is None


def test_script_detection():
    """Test script type detection."""
    detector = LanguageDetector()

    # English uses Latin script
    en_info = detector.detect("This is English")
    assert en_info.script == "Latin"

    # Chinese uses Han script
    zh_info = detector.detect("这是中文")
    assert zh_info.script == "Han"


def test_confidence_scoring():
    """Test confidence scoring."""
    detector = LanguageDetector()

    # Strong English signal
    strong_en = "The quick brown fox jumps over the lazy dog. This is clearly English."
    lang_info = detector.detect(strong_en)

    assert lang_info.code == "en"
    assert lang_info.confidence > 0.3  # Should have decent confidence


def test_metadata_preservation():
    """Test metadata is preserved."""
    manager = MultiLanguageManager()

    metadata = {"category": "guide", "version": "1.0"}
    manager.add_document("file.md", "English content", metadata)

    docs = manager.documents["en"]
    assert len(docs) == 1
    assert docs[0]["metadata"] == metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
