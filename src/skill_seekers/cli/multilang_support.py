#!/usr/bin/env python3
"""
Multi-language Documentation Support

Provides language detection, multi-language structure handling,
and translation-ready format generation.
"""

import re
from pathlib import Path
from dataclasses import dataclass
import json


@dataclass
class LanguageInfo:
    """Language information for a document."""

    code: str  # ISO 639-1 code (e.g., 'en', 'es', 'zh')
    name: str  # Full name (e.g., 'English', 'Spanish', 'Chinese')
    confidence: float  # Detection confidence (0.0-1.0)
    script: str | None = None  # Script type (e.g., 'Latin', 'Cyrillic')


@dataclass
class TranslationStatus:
    """Translation status for a document."""

    source_language: str
    target_languages: list[str]
    translated_languages: set[str]
    missing_languages: set[str]
    completeness: float  # Percentage (0.0-1.0)


class LanguageDetector:
    """
    Detect document language using heuristics.

    Uses character patterns, common words, and script detection.
    """

    # Common word patterns by language
    LANGUAGE_PATTERNS = {
        "en": [
            r"\b(the|and|is|are|in|to|of|for|with|on|at|by|from)\b",
            r"\b(this|that|these|those|what|which|who|where|when)\b",
        ],
        "es": [
            r"\b(el|la|los|las|de|en|y|a|es|por|para|con|su)\b",
            r"\b(que|no|un|una|como|más|pero|muy|todo|ya)\b",
        ],
        "fr": [
            r"\b(le|la|les|de|et|en|un|une|pour|dans|que|sur|avec)\b",
            r"\b(est|sont|ce|qui|plus|ne|pas|nous|vous|tout)\b",
        ],
        "de": [
            r"\b(der|die|das|und|in|zu|den|von|ist|mit|für|auf)\b",
            r"\b(ein|eine|nicht|sich|auch|werden|an|als|ich|sie)\b",
        ],
        "zh": [
            r"[\u4e00-\u9fff]",  # Chinese characters
            r"(的|了|和|是|在|有|我|他|不|这)",
        ],
        "ja": [
            r"[\u3040-\u309f]",  # Hiragana
            r"[\u30a0-\u30ff]",  # Katakana
            r"[\u4e00-\u9faf]",  # Kanji
        ],
        "ko": [
            r"[\uac00-\ud7af]",  # Hangul
            r"(의|가|이|은|들|는|좀|잘|께|을)",
        ],
        "ru": [
            r"[\u0400-\u04ff]",  # Cyrillic
            r"\b(и|в|не|на|с|что|он|по|а|как|это|все)\b",
        ],
        "pt": [
            r"\b(o|a|de|e|do|da|em|um|para|é|com|não|os|as)\b",
            r"\b(que|se|mais|por|dos|das|como|mas|uma|ou)\b",
        ],
        "it": [
            r"\b(il|la|di|e|a|da|in|che|per|un|una|non|del)\b",
            r"\b(con|alla|della|al|nel|sono|come|più|ma|dei)\b",
        ],
        "ar": [
            r"[\u0600-\u06ff]",  # Arabic
            r"(في|من|على|إلى|هذا|ما|أن|كان|هو|التي)",
        ],
    }

    # Language names
    LANGUAGE_NAMES = {
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "ru": "Russian",
        "pt": "Portuguese",
        "it": "Italian",
        "ar": "Arabic",
    }

    # Script types
    SCRIPTS = {
        "en": "Latin",
        "es": "Latin",
        "fr": "Latin",
        "de": "Latin",
        "pt": "Latin",
        "it": "Latin",
        "zh": "Han",
        "ja": "Japanese",
        "ko": "Hangul",
        "ru": "Cyrillic",
        "ar": "Arabic",
    }

    def detect(self, text: str, sample_size: int = 2000) -> LanguageInfo:
        """
        Detect language of text.

        Args:
            text: Text to analyze
            sample_size: Number of characters to sample

        Returns:
            LanguageInfo with detected language
        """
        if not text.strip():
            return LanguageInfo("en", "English", 0.0)

        # Sample text for efficiency
        sample = text[:sample_size].lower()

        # Score each language
        scores = {}
        for lang_code, patterns in self.LANGUAGE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, sample, re.IGNORECASE))
                score += matches

            scores[lang_code] = score

        # Find best match
        if not scores or max(scores.values()) == 0:
            # Default to English
            return LanguageInfo("en", "English", 0.1)

        best_lang = max(scores, key=scores.get)
        total_score = sum(scores.values())
        confidence = scores[best_lang] / total_score if total_score > 0 else 0.0

        return LanguageInfo(
            code=best_lang,
            name=self.LANGUAGE_NAMES.get(best_lang, best_lang.upper()),
            confidence=min(confidence, 1.0),
            script=self.SCRIPTS.get(best_lang),
        )

    def detect_from_filename(self, filename: str) -> str | None:
        """
        Detect language from filename pattern.

        Supports patterns like:
        - file.en.md
        - file_en.md
        - en/file.md
        - file-en.md

        Args:
            filename: Filename to analyze

        Returns:
            ISO 639-1 language code or None
        """
        # Pattern: file.en.md
        match = re.search(r"\.([a-z]{2})\.md$", filename)
        if match and match.group(1) in self.LANGUAGE_NAMES:
            return match.group(1)

        # Pattern: file_en.md or file-en.md
        match = re.search(r"[_-]([a-z]{2})\.md$", filename)
        if match and match.group(1) in self.LANGUAGE_NAMES:
            return match.group(1)

        return None


class MultiLanguageManager:
    """
    Manages multi-language documentation structure.

    Organizes documents by language and tracks translations.
    """

    def __init__(self):
        """Initialize multi-language manager."""
        self.detector = LanguageDetector()
        self.documents: dict[str, list[dict]] = {}  # lang_code -> [docs]
        self.primary_language: str | None = None

    def add_document(
        self,
        file_path: str,
        content: str,
        metadata: dict | None = None,
        force_language: str | None = None,
    ) -> None:
        """
        Add document with language detection.

        Args:
            file_path: Path to document
            content: Document content
            metadata: Additional metadata
            force_language: Override language detection
        """
        # Detect language
        if force_language:
            lang_code = force_language
            lang_info = LanguageInfo(
                code=lang_code,
                name=self.detector.LANGUAGE_NAMES.get(lang_code, lang_code.upper()),
                confidence=1.0,
                script=self.detector.SCRIPTS.get(lang_code),
            )
        else:
            # Try filename pattern first
            filename_lang = self.detector.detect_from_filename(file_path)
            if filename_lang:
                lang_code = filename_lang
                lang_info = LanguageInfo(
                    code=lang_code,
                    name=self.detector.LANGUAGE_NAMES.get(lang_code, lang_code.upper()),
                    confidence=0.95,
                    script=self.detector.SCRIPTS.get(lang_code),
                )
            else:
                # Detect from content
                lang_info = self.detector.detect(content)
                lang_code = lang_info.code

        # Set primary language (first added or most common)
        if self.primary_language is None:
            self.primary_language = lang_code

        # Store document
        if lang_code not in self.documents:
            self.documents[lang_code] = []

        doc = {
            "file_path": file_path,
            "content": content,
            "language": lang_info.code,
            "language_name": lang_info.name,
            "confidence": lang_info.confidence,
            "script": lang_info.script,
            "metadata": metadata or {},
        }

        self.documents[lang_code].append(doc)

    def get_languages(self) -> list[str]:
        """Get list of detected languages."""
        return sorted(self.documents.keys())

    def get_document_count(self, language: str | None = None) -> int:
        """
        Get document count for a language.

        Args:
            language: Language code (None for all)

        Returns:
            Number of documents
        """
        if language:
            return len(self.documents.get(language, []))
        return sum(len(docs) for docs in self.documents.values())

    def get_translation_status(self, base_language: str | None = None) -> TranslationStatus:
        """
        Get translation status.

        Args:
            base_language: Base language (None for primary)

        Returns:
            Translation status summary
        """
        base_lang = base_language or self.primary_language or "en"

        all_languages = set(self.documents.keys())
        base_count = self.get_document_count(base_lang)

        if base_count == 0:
            return TranslationStatus(
                source_language=base_lang,
                target_languages=[],
                translated_languages=set(),
                missing_languages=set(),
                completeness=0.0,
            )

        # Check which languages have translations
        translated = set()
        for lang in all_languages:
            if lang != base_lang and self.get_document_count(lang) > 0:
                translated.add(lang)

        # Commonly expected languages for completeness
        expected_languages = {"en", "es", "fr", "de", "zh", "ja"}
        missing = expected_languages - all_languages

        completeness = len(all_languages) / len(expected_languages)

        return TranslationStatus(
            source_language=base_lang,
            target_languages=list(all_languages - {base_lang}),
            translated_languages=translated,
            missing_languages=missing,
            completeness=min(completeness, 1.0),
        )

    def export_by_language(self, output_dir: Path) -> dict[str, Path]:
        """
        Export documents organized by language.

        Args:
            output_dir: Output directory

        Returns:
            Dictionary mapping language codes to output paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        exports = {}

        for lang_code, docs in self.documents.items():
            lang_file = output_dir / f"documents_{lang_code}.json"

            export_data = {
                "language": lang_code,
                "language_name": self.detector.LANGUAGE_NAMES.get(lang_code, lang_code.upper()),
                "document_count": len(docs),
                "documents": docs,
            }

            lang_file.write_text(json.dumps(export_data, indent=2, ensure_ascii=False))
            exports[lang_code] = lang_file

        return exports

    def generate_translation_report(self) -> str:
        """
        Generate human-readable translation report.

        Returns:
            Formatted report string
        """
        lines = ["=" * 60]
        lines.append("MULTI-LANGUAGE DOCUMENTATION REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Summary
        languages = self.get_languages()
        total_docs = self.get_document_count()

        lines.append("📊 Summary:")
        lines.append(f"   Languages: {len(languages)}")
        lines.append(f"   Total documents: {total_docs}")
        lines.append(f"   Primary language: {self.primary_language or 'Unknown'}")
        lines.append("")

        # Language breakdown
        lines.append("🌍 Language Breakdown:")
        for lang in languages:
            count = self.get_document_count(lang)
            lang_name = self.detector.LANGUAGE_NAMES.get(lang, lang.upper())
            percentage = (count / total_docs * 100) if total_docs > 0 else 0
            lines.append(f"   {lang_name} ({lang}): {count} docs ({percentage:.1f}%)")
        lines.append("")

        # Translation status
        status = self.get_translation_status()
        lines.append("📝 Translation Status:")
        lines.append(f"   Source: {status.source_language}")
        lines.append(f"   Translated to: {', '.join(status.translated_languages) or 'None'}")
        lines.append(f"   Completeness: {status.completeness * 100:.1f}%")

        if status.missing_languages:
            lines.append(f"   Missing: {', '.join(sorted(status.missing_languages))}")
        lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)


def main():
    """CLI entry point for multi-language support."""
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Manage multi-language skill documents")
    parser.add_argument("skill_dir", help="Path to skill directory")
    parser.add_argument("--detect", action="store_true", help="Detect languages in skill")
    parser.add_argument("--report", action="store_true", help="Generate translation report")
    parser.add_argument("--export", help="Export by language to specified directory")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir)
    if not skill_dir.exists():
        print(f"❌ Error: Directory not found: {skill_dir}")
        return 1

    manager = MultiLanguageManager()

    # Load skill documents
    print("📥 Loading skill documents...")
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        manager.add_document(
            "SKILL.md", skill_md.read_text(encoding="utf-8"), {"category": "overview"}
        )

    # Load reference files
    refs_dir = skill_dir / "references"
    if refs_dir.exists():
        for ref_file in refs_dir.glob("*.md"):
            manager.add_document(
                ref_file.name, ref_file.read_text(encoding="utf-8"), {"category": ref_file.stem}
            )

    # Detect languages
    if args.detect:
        languages = manager.get_languages()
        print(f"\n🌍 Detected languages: {', '.join(languages)}")
        for lang in languages:
            count = manager.get_document_count(lang)
            print(f"   {lang}: {count} documents")

    # Generate report
    if args.report:
        print(manager.generate_translation_report())

    # Export by language
    if args.export:
        output_dir = Path(args.export)
        output_dir.mkdir(parents=True, exist_ok=True)
        exports = manager.export_by_language(output_dir)
        print(f"\n✅ Exported {len(exports)} language files:")
        for lang, path in exports.items():
            print(f"   {lang}: {path}")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
