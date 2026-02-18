"""
Quality Scoring for Document Content

Provides consistent quality scoring across all parsers for:
- Code blocks (syntax, structure, patterns)
- Tables (completeness, formatting)
- Content blocks (readability, structure)
"""

import re

from .unified_structure import Table, ContentBlock


class QualityScorer:
    """Score the quality of extracted content."""

    # Language patterns for detection and validation
    LANGUAGE_PATTERNS = {
        "python": {
            "keywords": ["def ", "class ", "import ", "from ", "return ", "if ", "for ", "while"],
            "syntax_checks": [
                (r":\s*$", "colon_ending"),  # Python uses colons for blocks
                (r"def\s+\w+\s*\([^)]*\)\s*:", "function_def"),
                (r"class\s+\w+", "class_def"),
            ],
        },
        "javascript": {
            "keywords": ["function", "const ", "let ", "var ", "=>", "return ", "if(", "for("],
            "syntax_checks": [
                (r"function\s+\w+\s*\(", "function_def"),
                (r"const\s+\w+\s*=", "const_decl"),
                (r"=>", "arrow_function"),
            ],
        },
        "typescript": {
            "keywords": ["interface ", "type ", ": string", ": number", ": boolean", "implements"],
            "syntax_checks": [
                (r"interface\s+\w+", "interface_def"),
                (r":\s*(string|number|boolean|any)", "type_annotation"),
            ],
        },
        "java": {
            "keywords": ["public ", "private ", "class ", "void ", "String ", "int ", "return "],
            "syntax_checks": [
                (r"public\s+class\s+\w+", "class_def"),
                (r"public\s+\w+\s+\w+\s*\(", "method_def"),
            ],
        },
        "cpp": {
            "keywords": [
                "#include",
                "using namespace",
                "std::",
                "cout",
                "cin",
                "public:",
                "private:",
            ],
            "syntax_checks": [
                (r'#include\s*[<"]', "include"),
                (r"std::", "std_namespace"),
            ],
        },
        "csharp": {
            "keywords": ["namespace ", "public class", "private ", "void ", "string ", "int "],
            "syntax_checks": [
                (r"namespace\s+\w+", "namespace"),
                (r"public\s+class\s+\w+", "class_def"),
            ],
        },
        "go": {
            "keywords": ["package ", "func ", "import ", "return ", "if ", "for ", "range "],
            "syntax_checks": [
                (r"func\s+\w+\s*\(", "function_def"),
                (r"package\s+\w+", "package_decl"),
            ],
        },
        "rust": {
            "keywords": ["fn ", "let ", "mut ", "impl ", "struct ", "enum ", "match ", "use "],
            "syntax_checks": [
                (r"fn\s+\w+\s*\(", "function_def"),
                (r"impl\s+\w+", "impl_block"),
            ],
        },
        "gdscript": {  # Godot
            "keywords": [
                "extends ",
                "class_name ",
                "func ",
                "var ",
                "const ",
                "signal ",
                "export",
                "onready",
            ],
            "syntax_checks": [
                (r"extends\s+\w+", "extends"),
                (r"func\s+_\w+", "built_in_method"),
                (r"signal\s+\w+", "signal_def"),
                (r"@export", "export_annotation"),
            ],
        },
        "yaml": {
            "keywords": [],
            "syntax_checks": [
                (r"^\w+:\s*", "key_value"),
                (r"^-\s+\w+", "list_item"),
            ],
        },
        "json": {
            "keywords": [],
            "syntax_checks": [
                (r'["\']\w+["\']\s*:', "key_value"),
                (r"\{[^}]*\}", "object"),
                (r"\[[^\]]*\]", "array"),
            ],
        },
        "xml": {
            "keywords": [],
            "syntax_checks": [
                (r"<\w+[^>]*>", "opening_tag"),
                (r"</\w+>", "closing_tag"),
            ],
        },
        "sql": {
            "keywords": [
                "SELECT",
                "FROM",
                "WHERE",
                "INSERT",
                "UPDATE",
                "DELETE",
                "CREATE",
                "TABLE",
            ],
            "syntax_checks": [
                (r"SELECT\s+.+\s+FROM", "select_statement"),
                (r"CREATE\s+TABLE", "create_table"),
            ],
        },
        "bash": {
            "keywords": ["#!/bin/", "echo ", "if [", "then", "fi", "for ", "do", "done"],
            "syntax_checks": [
                (r"#!/bin/\w+", "shebang"),
                (r"\$\w+", "variable"),
            ],
        },
    }

    def score_code_block(self, code: str, language: str | None = None) -> float:
        """
        Score a code block for quality (0-10).

        Args:
            code: The code content
            language: Detected or specified language

        Returns:
            Quality score from 0-10
        """
        score = 5.0  # Start neutral

        if not code or not code.strip():
            return 0.0

        code = code.strip()
        lines = [line for line in code.split("\n") if line.strip()]

        # Factor 1: Length appropriateness
        code_len = len(code)
        if 50 <= code_len <= 1000:
            score += 1.0
        elif code_len > 2000:
            score -= 1.0  # Too long
        elif code_len < 20:
            score -= 2.0  # Too short

        # Factor 2: Line count
        if 3 <= len(lines) <= 50:
            score += 1.0
        elif len(lines) > 100:
            score -= 0.5

        # Factor 3: Language-specific validation
        if language and language in self.LANGUAGE_PATTERNS:
            lang_patterns = self.LANGUAGE_PATTERNS[language]

            # Check for keywords
            keyword_matches = sum(1 for kw in lang_patterns["keywords"] if kw in code)
            if keyword_matches >= 2:
                score += 1.0

            # Check for syntax patterns
            syntax_matches = sum(
                1
                for pattern, _ in lang_patterns["syntax_checks"]
                if re.search(pattern, code, re.MULTILINE)
            )
            if syntax_matches >= 1:
                score += 1.0

        # Factor 4: Structural quality
        # Check for function/class definitions
        if re.search(r"\b(def|function|func|fn|class|public class)\b", code):
            score += 1.5

        # Check for meaningful variable names (not just x, y, i)
        meaningful_vars = re.findall(r"\b[a-z_][a-z0-9_]{3,}\b", code.lower())
        if len(meaningful_vars) >= 3:
            score += 0.5

        # Factor 5: Syntax validation (generic)
        is_valid, issues = self._validate_syntax(code, language)
        if is_valid:
            score += 1.0
        else:
            score -= len(issues) * 0.3

        # Factor 6: Comment/code ratio
        comment_lines = sum(
            1 for line in lines if line.strip().startswith(("#", "//", "/*", "*", "--", "<!--"))
        )
        if len(lines) > 0:
            comment_ratio = comment_lines / len(lines)
            if 0.1 <= comment_ratio <= 0.4:
                score += 0.5  # Good comment ratio
            elif comment_ratio > 0.6:
                score -= 1.0  # Too many comments

        # Clamp to 0-10
        return max(0.0, min(10.0, score))

    def _validate_syntax(self, code: str, language: str | None) -> tuple[bool, list[str]]:
        """Basic syntax validation."""
        issues = []

        # Check for balanced braces/brackets
        pairs = [("{", "}"), ("[", "]"), ("(", ")")]
        for open_char, close_char in pairs:
            open_count = code.count(open_char)
            close_count = code.count(close_char)
            if abs(open_count - close_count) > 2:
                issues.append(f"Unbalanced {open_char}{close_char}")

        # Check for common natural language indicators
        common_words = ["the", "and", "for", "with", "this", "that", "have", "from", "they"]
        word_count = sum(1 for word in common_words if f" {word} " in code.lower())
        if word_count > 5 and len(code.split()) < 100:
            issues.append("May be natural language")

        # Language-specific checks
        if language == "python":
            # Check for mixed indentation
            indent_chars = set()
            for line in code.split("\n"):
                if line.startswith(" "):
                    indent_chars.add("space")
                elif line.startswith("\t"):
                    indent_chars.add("tab")
            if len(indent_chars) > 1:
                issues.append("Mixed tabs and spaces")

        elif language == "json":
            try:
                import json

                json.loads(code)
            except Exception as e:
                issues.append(f"Invalid JSON: {str(e)[:50]}")

        return len(issues) == 0, issues

    def score_table(self, table: Table) -> float:
        """
        Score a table for quality (0-10).

        Args:
            table: The table to score

        Returns:
            Quality score from 0-10
        """
        score = 5.0

        # Factor 1: Has headers
        if table.headers:
            score += 1.0

        # Factor 2: Consistent column count
        if table.rows:
            col_counts = [len(row) for row in table.rows]
            if len(set(col_counts)) == 1:
                score += 1.0  # Consistent
            else:
                score -= 1.0  # Inconsistent

        # Factor 3: Reasonable size
        if 2 <= table.num_rows <= 100:
            score += 0.5
        elif table.num_rows > 500:
            score -= 0.5

        if 2 <= table.num_cols <= 10:
            score += 0.5
        elif table.num_cols > 20:
            score -= 0.5

        # Factor 4: Non-empty cells
        if table.rows:
            total_cells = sum(len(row) for row in table.rows)
            empty_cells = sum(1 for row in table.rows for cell in row if not cell.strip())
            if total_cells > 0:
                empty_ratio = empty_cells / total_cells
                if empty_ratio < 0.1:
                    score += 1.0
                elif empty_ratio > 0.5:
                    score -= 1.0

        # Factor 5: Has caption (good for API docs)
        if table.caption:
            score += 0.5

        return max(0.0, min(10.0, score))

    def score_content_block(self, block: ContentBlock) -> float:
        """Score a generic content block."""
        score = 5.0
        content = block.content

        if not content:
            return 0.0

        # Length check
        if len(content) < 10:
            score -= 2.0
        elif len(content) > 1000:
            score += 0.5

        # Structure check
        if "." in content:  # Has sentences
            score += 0.5
        if content[0].isupper():  # Starts with capital
            score += 0.5

        return max(0.0, min(10.0, score))

    def detect_language(self, code: str) -> tuple[str, float]:
        """
        Detect programming language from code.

        Returns:
            Tuple of (language, confidence)
        """
        code = code.strip()
        if not code:
            return "unknown", 0.0

        scores = {}

        for lang, patterns in self.LANGUAGE_PATTERNS.items():
            score = 0.0

            # Check keywords
            keyword_hits = sum(1 for kw in patterns["keywords"] if kw in code)
            score += keyword_hits * 0.5

            # Check syntax patterns
            for pattern, _ in patterns["syntax_checks"]:
                if re.search(pattern, code, re.MULTILINE):
                    score += 1.0

            scores[lang] = score

        if not scores:
            return "unknown", 0.0

        best_lang = max(scores, key=scores.get)
        best_score = scores[best_lang]

        # Normalize confidence
        confidence = min(1.0, best_score / 5) if best_score >= 3 else best_score / 10

        return best_lang, confidence
