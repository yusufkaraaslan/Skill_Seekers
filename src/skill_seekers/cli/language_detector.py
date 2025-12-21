#!/usr/bin/env python3
"""
Unified Language Detection for Code Blocks

Provides confidence-based language detection for documentation scrapers.
Supports 20+ programming languages with weighted pattern matching.

Author: Skill Seekers Project
"""

import re
from typing import Optional, Tuple, Dict, List


# Comprehensive language patterns with weighted confidence scoring
# Weight 5: Unique identifiers (highly specific)
# Weight 4: Strong indicators
# Weight 3: Common patterns
# Weight 2: Moderate indicators
# Weight 1: Weak indicators

LANGUAGE_PATTERNS: Dict[str, List[Tuple[str, int]]] = {
    # ===== PRIORITY 1: Unity C# (Critical - User's Primary Issue) =====
    'csharp': [
        # Unity-specific patterns (weight 4-5, CRITICAL)
        (r'\busing\s+UnityEngine', 5),
        (r'\bMonoBehaviour\b', 5),
        (r'\bGameObject\b', 4),
        (r'\bTransform\b', 4),
        (r'\bVector[23]\b', 3),
        (r'\bQuaternion\b', 3),
        (r'\bvoid\s+Start\s*\(\)', 4),
        (r'\bvoid\s+Update\s*\(\)', 4),
        (r'\bvoid\s+Awake\s*\(\)', 4),
        (r'\bvoid\s+OnEnable\s*\(\)', 3),
        (r'\bvoid\s+OnDisable\s*\(\)', 3),
        (r'\bvoid\s+FixedUpdate\s*\(\)', 4),
        (r'\bvoid\s+LateUpdate\s*\(\)', 4),
        (r'\bvoid\s+OnCollisionEnter', 4),
        (r'\bvoid\s+OnTriggerEnter', 4),
        (r'\bIEnumerator\b', 4),
        (r'\bStartCoroutine\s*\(', 4),
        (r'\byield\s+return\s+new\s+WaitForSeconds', 4),
        (r'\byield\s+return\s+null', 3),
        (r'\byield\s+return', 4),
        (r'\[SerializeField\]', 4),
        (r'\[RequireComponent', 4),
        (r'\[Header\(', 3),
        (r'\[Range\(', 3),
        (r'\bTime\.deltaTime\b', 4),
        (r'\bInput\.Get', 4),
        (r'\bRigidbody\b', 3),
        (r'\bCollider\b', 3),
        (r'\bRenderer\b', 3),
        (r'\bGetComponent<', 3),

        # Basic C# patterns (weight 2-4)
        (r'\bnamespace\s+\w+', 3),
        (r'\busing\s+System', 3),
        (r'\bConsole\.WriteLine', 4),  # C#-specific output
        (r'\bConsole\.Write', 3),
        (r'\bpublic\s+class\s+\w+', 4),  # Increased to match Java weight
        (r'\bprivate\s+class\s+\w+', 3),
        (r'\binternal\s+class\s+\w+', 4),  # C#-specific modifier
        (r'\bstring\s+\w+\s*[;=]', 2),  # C#-specific lowercase string
        (r'\bprivate\s+\w+\s+\w+\s*;', 2),  # Private fields (common in both C# and Java)
        (r'\{\s*get;\s*set;\s*\}', 3),  # Auto properties
        (r'\{\s*get;\s*private\s+set;\s*\}', 3),
        (r'\{\s*get\s*=>\s*', 2),  # Expression properties
        (r'\bpublic\s+static\s+void\s+', 2),

        # Modern C# patterns (weight 2)
        (r'\bfrom\s+\w+\s+in\s+', 2),  # LINQ
        (r'\.Where\s*\(', 2),
        (r'\.Select\s*\(', 2),
        (r'\basync\s+Task', 2),
        (r'\bawait\s+', 2),
        (r'\bvar\s+\w+\s*=', 1),
    ],

    # ===== PRIORITY 2: Frontend Languages =====
    'typescript': [
        # TypeScript-specific (weight 4-5)
        (r'\binterface\s+\w+\s*\{', 5),
        (r'\btype\s+\w+\s*=', 4),
        (r':\s*\w+\s*=', 3),  # Type annotation
        (r':\s*\w+\[\]', 3),  # Array type
        (r'<[\w,\s]+>', 2),  # Generic type
        (r'\bas\s+\w+', 2),  # Type assertion
        (r'\benum\s+\w+\s*\{', 4),
        (r'\bimplements\s+\w+', 3),
        (r'\bexport\s+interface', 4),
        (r'\bexport\s+type', 4),

        # Also has JS patterns (weight 1)
        (r'\bconst\s+\w+\s*=', 1),
        (r'\blet\s+\w+\s*=', 1),
        (r'=>', 1),
    ],

    'javascript': [
        (r'\bfunction\s+\w+\s*\(', 3),
        (r'\bconst\s+\w+\s*=', 2),
        (r'\blet\s+\w+\s*=', 2),
        (r'=>', 2),  # Arrow function
        (r'\bconsole\.log', 2),
        (r'\bvar\s+\w+\s*=', 1),
        (r'\.then\s*\(', 2),  # Promise
        (r'\.catch\s*\(', 2),  # Promise
        (r'\basync\s+function', 3),
        (r'\bawait\s+', 2),
        (r'require\s*\(', 2),  # CommonJS
        (r'\bexport\s+default', 2),  # ES6
        (r'\bexport\s+const', 2),
    ],

    'jsx': [
        # JSX patterns (weight 4-5)
        (r'<\w+\s+[^>]*>', 4),  # JSX tag with attributes
        (r'<\w+\s*/>', 4),  # Self-closing tag
        (r'className=', 3),  # React className
        (r'onClick=', 3),  # React event
        (r'\brender\s*\(\s*\)\s*\{', 4),  # React render
        (r'\buseState\s*\(', 4),  # React hook
        (r'\buseEffect\s*\(', 4),  # React hook
        (r'\buseRef\s*\(', 3),
        (r'\buseCallback\s*\(', 3),
        (r'\buseMemo\s*\(', 3),

        # Also has JS patterns
        (r'\bconst\s+\w+\s*=', 1),
        (r'=>', 1),
    ],

    'tsx': [
        # TSX = TypeScript + JSX (weight 5)
        (r'<\w+\s+[^>]*>', 3),  # JSX tag
        (r':\s*React\.\w+', 5),  # React types
        (r'interface\s+\w+Props', 5),  # Props interface
        (r'\bFunctionComponent<', 4),
        (r'\bReact\.FC<', 4),
        (r'\buseState<', 4),  # Typed hook
        (r'\buseRef<', 3),

        # Also has TS patterns
        (r'\binterface\s+\w+', 2),
        (r'\btype\s+\w+\s*=', 2),
    ],

    'vue': [
        # Vue SFC patterns (weight 4-5)
        (r'<template>', 5),
        (r'<script>', 3),
        (r'<style\s+scoped>', 4),
        (r'\bexport\s+default\s*\{', 3),
        (r'\bdata\s*\(\s*\)\s*\{', 4),  # Vue 2
        (r'\bcomputed\s*:', 3),
        (r'\bmethods\s*:', 3),
        (r'\bsetup\s*\(', 4),  # Vue 3 Composition
        (r'\bref\s*\(', 4),  # Vue 3
        (r'\breactive\s*\(', 4),  # Vue 3
        (r'v-bind:', 3),
        (r'v-for=', 3),
        (r'v-if=', 3),
        (r'v-model=', 3),
    ],

    # ===== PRIORITY 3: Backend Languages =====
    'java': [
        (r'\bpublic\s+class\s+\w+', 4),
        (r'\bprivate\s+\w+\s+\w+', 2),
        (r'\bSystem\.out\.println', 3),
        (r'\bpublic\s+static\s+void\s+main', 4),
        (r'\bpublic\s+\w+\s+\w+\s*\(', 2),
        (r'@Override', 3),
        (r'@Autowired', 3),  # Spring
        (r'@Service', 3),  # Spring
        (r'@RestController', 3),  # Spring
        (r'@GetMapping', 3),  # Spring
        (r'@PostMapping', 3),  # Spring
        (r'\bimport\s+java\.', 2),
        (r'\bextends\s+\w+', 2),
    ],

    'go': [
        (r'\bfunc\s+\w+\s*\(', 3),
        (r'\bpackage\s+\w+', 4),
        (r':=', 3),  # Short declaration
        (r'\bfmt\.Print', 2),
        (r'\bfunc\s+\(.*\)\s+\w+\s*\(', 4),  # Method
        (r'\bdefer\s+', 3),
        (r'\bgo\s+\w+\s*\(', 3),  # Goroutine
        (r'\bchan\s+', 3),  # Channel
        (r'\binterface\{\}', 2),  # Empty interface
        (r'\bfunc\s+main\s*\(\)', 4),
    ],

    'rust': [
        (r'\bfn\s+\w+\s*\(', 4),
        (r'\blet\s+mut\s+\w+', 3),
        (r'\bprintln!', 3),
        (r'\bimpl\s+\w+', 3),
        (r'\buse\s+\w+::', 3),
        (r'\bpub\s+fn\s+', 3),
        (r'\bmatch\s+\w+\s*\{', 3),
        (r'\bSome\(', 2),
        (r'\bNone\b', 2),
        (r'\bResult<', 3),
        (r'\bOption<', 3),
        (r'&str\b', 2),
        (r'\bfn\s+main\s*\(\)', 4),
    ],

    'php': [
        (r'<\?php', 5),
        (r'\$\w+\s*=', 2),
        (r'\bfunction\s+\w+\s*\(', 2),
        (r'\bpublic\s+function', 3),
        (r'\bprivate\s+function', 3),
        (r'\bclass\s+\w+', 3),
        (r'\bnamespace\s+\w+', 3),
        (r'\buse\s+\w+\\', 2),
        (r'->', 2),  # Object operator
        (r'::', 1),  # Static operator
    ],

    # ===== PRIORITY 4: System/Data Languages =====
    'python': [
        (r'\bdef\s+\w+\s*\(', 3),
        (r'\bimport\s+\w+', 2),
        (r'\bclass\s+\w+:', 3),
        (r'\bfrom\s+\w+\s+import', 2),
        (r':\s*$', 1),  # Lines ending with :
        (r'@\w+', 2),  # Decorator
        (r'\bself\.\w+', 2),
        (r'\b__init__\s*\(', 3),
        (r'\basync\s+def\s+', 3),
        (r'\bawait\s+', 2),
        (r'\bprint\s*\(', 1),
    ],

    'r': [
        (r'<-', 4),  # Assignment operator
        (r'\bfunction\s*\(', 2),
        (r'\blibrary\s*\(', 3),
        (r'\bggplot\s*\(', 4),  # ggplot2
        (r'\bdata\.frame\s*\(', 3),
        (r'\%>\%', 4),  # Pipe operator
        (r'\bsummary\s*\(', 2),
        (r'\bread\.csv\s*\(', 3),
    ],

    'julia': [
        (r'\bfunction\s+\w+\s*\(', 3),
        (r'\bend\b', 2),
        (r'\busing\s+\w+', 3),
        (r'::', 2),  # Type annotation
        (r'\bmodule\s+\w+', 3),
        (r'\babstract\s+type', 3),
        (r'\bstruct\s+\w+', 3),
    ],

    'sql': [
        (r'\bSELECT\s+', 4),
        (r'\bFROM\s+', 3),
        (r'\bWHERE\s+', 2),
        (r'\bINSERT\s+INTO', 4),
        (r'\bCREATE\s+TABLE', 4),
        (r'\bJOIN\s+', 3),
        (r'\bGROUP\s+BY', 3),
        (r'\bORDER\s+BY', 3),
        (r'\bUPDATE\s+', 3),
        (r'\bDELETE\s+FROM', 3),
    ],

    # ===== Additional Languages =====
    'cpp': [
        (r'#include\s*<', 4),
        (r'\bstd::', 3),
        (r'\bnamespace\s+\w+', 3),
        (r'\bcout\s*<<', 3),
        (r'\bvoid\s+\w+\s*\(', 2),
        (r'\bint\s+main\s*\(', 4),
        (r'->', 2),  # Pointer
    ],

    'c': [
        (r'#include\s*<', 4),
        (r'\bprintf\s*\(', 3),
        (r'\bint\s+main\s*\(', 4),
        (r'\bvoid\s+\w+\s*\(', 2),
        (r'\bstruct\s+\w+', 3),
    ],

    'gdscript': [
        (r'\bfunc\s+\w+\s*\(', 3),
        (r'\bvar\s+\w+\s*=', 3),
        (r'\bextends\s+\w+', 4),
        (r'\b_ready\s*\(', 4),
        (r'\b_process\s*\(', 4),
    ],

    # ===== Markup/Config Languages =====
    'html': [
        (r'<!DOCTYPE\s+html>', 5),
        (r'<html', 4),
        (r'<head>', 3),
        (r'<body>', 3),
        (r'<div', 2),
        (r'<span', 2),
        (r'<script', 2),
    ],

    'css': [
        (r'\{\s*[\w-]+\s*:', 3),
        (r'@media', 3),
        (r'\.[\w-]+\s*\{', 2),
        (r'#[\w-]+\s*\{', 2),
        (r'@import', 2),
    ],

    'json': [
        (r'^\s*\{', 3),
        (r'^\s*\[', 3),
        (r'"\w+"\s*:', 3),
        (r':\s*["\d\[\{]', 2),
    ],

    'yaml': [
        (r'^\w+:', 3),
        (r'^\s+-\s+\w+', 2),
        (r'---', 2),
        (r'^\s+\w+:', 2),
    ],

    'xml': [
        (r'<\?xml', 5),
        (r'<\w+\s+\w+=', 2),
        (r'<\w+>', 1),
        (r'</\w+>', 1),
    ],

    'markdown': [
        (r'^#+\s+', 3),
        (r'^\*\*\w+\*\*', 2),
        (r'^\s*[-*]\s+', 2),
        (r'\[.*\]\(.*\)', 2),
    ],

    'bash': [
        (r'#!/bin/bash', 5),
        (r'#!/bin/sh', 5),
        (r'\becho\s+', 2),
        (r'\$\{?\w+\}?', 2),
        (r'\bif\s+\[', 2),
        (r'\bfor\s+\w+\s+in', 2),
    ],

    'shell': [
        (r'#!/bin/bash', 5),
        (r'#!/bin/sh', 5),
        (r'\becho\s+', 2),
        (r'\$\{?\w+\}?', 2),
    ],

    'powershell': [
        (r'\$\w+\s*=', 2),
        (r'Get-\w+', 3),
        (r'Set-\w+', 3),
        (r'\bWrite-Host\s+', 2),
    ],
}


# Known language list for CSS class detection
KNOWN_LANGUAGES = [
    "javascript", "java", "xml", "html", "python", "bash", "cpp", "typescript",
    "go", "rust", "php", "ruby", "swift", "kotlin", "csharp", "c", "sql",
    "yaml", "json", "markdown", "css", "scss", "sass", "jsx", "tsx", "vue",
    "shell", "powershell", "r", "scala", "dart", "perl", "lua", "elixir",
    "julia", "gdscript",
]


class LanguageDetector:
    """
    Unified confidence-based language detection for code blocks.

    Supports 20+ programming languages with weighted pattern matching.
    Uses two-stage detection:
    1. CSS class extraction (high confidence = 1.0)
    2. Pattern-based heuristics with confidence scoring (0.0-1.0)

    Example:
        detector = LanguageDetector(min_confidence=0.3)
        lang, confidence = detector.detect_from_html(elem, code)

        if confidence >= 0.7:
            print(f"High confidence: {lang}")
        elif confidence >= 0.5:
            print(f"Medium confidence: {lang}")
        else:
            print(f"Low confidence: {lang}")
    """

    def __init__(self, min_confidence: float = 0.15):
        """
        Initialize language detector.

        Args:
            min_confidence: Minimum confidence threshold (0-1)
                          0.3 = low, 0.5 = medium, 0.7 = high
        """
        self.min_confidence = min_confidence
        self._pattern_cache: Dict[str, List[Tuple[re.Pattern, int]]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns and cache them for performance"""
        for lang, patterns in LANGUAGE_PATTERNS.items():
            self._pattern_cache[lang] = [
                (re.compile(pattern, re.IGNORECASE | re.MULTILINE), weight)
                for pattern, weight in patterns
            ]

    def detect_from_html(self, elem, code: str) -> Tuple[str, float]:
        """
        Detect language from HTML element with CSS classes + code content.

        Args:
            elem: BeautifulSoup element with 'class' attribute
            code: Code content string

        Returns:
            Tuple of (language, confidence) where confidence is 0.0-1.0
        """
        # Tier 1: CSS classes (confidence 1.0)
        if elem:
            css_lang = self.extract_language_from_classes(elem.get('class', []))
            if css_lang:
                return css_lang, 1.0

            # Check parent pre element
            parent = elem.parent
            if parent and parent.name == 'pre':
                css_lang = self.extract_language_from_classes(parent.get('class', []))
                if css_lang:
                    return css_lang, 1.0

        # Tier 2: Pattern matching
        return self.detect_from_code(code)

    def detect_from_code(self, code: str) -> Tuple[str, float]:
        """
        Detect language from code content only (for PDFs, GitHub files).

        Args:
            code: Code content string

        Returns:
            Tuple of (language, confidence) where confidence is 0.0-1.0
        """
        # Edge case: code too short
        if len(code.strip()) < 10:
            return 'unknown', 0.0

        # Calculate confidence scores for all languages
        scores = self._calculate_confidence(code)

        if not scores:
            return 'unknown', 0.0

        # Get language with highest score
        best_lang = max(scores.items(), key=lambda x: x[1])
        lang, confidence = best_lang

        # Apply minimum confidence threshold
        if confidence < self.min_confidence:
            return 'unknown', 0.0

        return lang, confidence

    def extract_language_from_classes(self, classes: List[str]) -> Optional[str]:
        """
        Extract language from CSS class list.

        Supports patterns:
        - language-*  (e.g., language-python)
        - lang-*      (e.g., lang-javascript)
        - brush: *    (e.g., brush: java)
        - Bare names  (e.g., python, java)

        Args:
            classes: List of CSS class names

        Returns:
            Language string or None if not found
        """
        if not classes:
            return None

        for cls in classes:
            # Handle brush: pattern
            if 'brush:' in cls:
                parts = cls.split('brush:')
                if len(parts) > 1:
                    lang = parts[1].strip().lower()
                    if lang in KNOWN_LANGUAGES:
                        return lang

            # Handle language- prefix
            if cls.startswith('language-'):
                lang = cls[9:].lower()
                if lang in KNOWN_LANGUAGES:
                    return lang

            # Handle lang- prefix
            if cls.startswith('lang-'):
                lang = cls[5:].lower()
                if lang in KNOWN_LANGUAGES:
                    return lang

            # Handle bare class name
            if cls.lower() in KNOWN_LANGUAGES:
                return cls.lower()

        return None

    def _calculate_confidence(self, code: str) -> Dict[str, float]:
        """
        Calculate weighted confidence scores for all languages.

        Args:
            code: Code content string

        Returns:
            Dictionary mapping language names to confidence scores (0.0-1.0)
        """
        scores: Dict[str, float] = {}

        for lang, compiled_patterns in self._pattern_cache.items():
            total_score = 0

            for pattern, weight in compiled_patterns:
                if pattern.search(code):
                    total_score += weight

            if total_score > 0:
                # Normalize score to 0-1 range
                # Score of 10+ = 1.0 confidence
                confidence = min(total_score / 10.0, 1.0)
                scores[lang] = confidence

        return scores
