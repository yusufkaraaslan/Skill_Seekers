#!/usr/bin/env python3
"""
Jupyter Notebook (.ipynb) to Skill Converter

Converts Jupyter Notebooks into skills.
Uses nbformat for notebook parsing, extracts markdown prose, code cells with
outputs, kernel metadata, and cell-level tags.

Supports both single .ipynb files and directories containing multiple notebooks.

Usage:
    skill-seekers jupyter --notebook notebook.ipynb --name myskill
    skill-seekers jupyter --notebook ./notebooks/ --name myskill
    skill-seekers jupyter --from-json notebook_extracted.json
"""

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path

# Optional dependency guard
try:
    import nbformat

    JUPYTER_AVAILABLE = True
except ImportError:
    JUPYTER_AVAILABLE = False

logger = logging.getLogger(__name__)

# Import pattern categories for code analysis
_IMPORT_PATTERNS: dict[str, list[re.Pattern]] = {
    "python": [
        re.compile(r"^\s*import\s+([\w.]+)", re.MULTILINE),
        re.compile(r"^\s*from\s+([\w.]+)\s+import", re.MULTILINE),
    ],
    "r": [
        re.compile(r"^\s*library\(([\w.]+)\)", re.MULTILINE),
        re.compile(r"^\s*require\(([\w.]+)\)", re.MULTILINE),
    ],
    "julia": [
        re.compile(r"^\s*using\s+([\w.]+)", re.MULTILINE),
        re.compile(r"^\s*import\s+([\w.]+)", re.MULTILINE),
    ],
    "javascript": [
        re.compile(
            r"""^\s*(?:const|let|var)\s+\w+\s*=\s*require\(['"]([\w./@-]+)['"]\)""", re.MULTILINE
        ),
        re.compile(r"""^\s*import\s+.*?\s+from\s+['"]([\w./@-]+)['"]""", re.MULTILINE),
    ],
    "scala": [re.compile(r"^\s*import\s+([\w.]+)", re.MULTILINE)],
}

# Topic keywords used for content categorization
_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "data_loading": [
        "read_csv",
        "read_json",
        "read_excel",
        "read_sql",
        "load_data",
        "open(",
        "pd.read",
        "fetch",
        "download",
        "dataset",
    ],
    "data_cleaning": [
        "dropna",
        "fillna",
        "replace",
        "strip",
        "clean",
        "preprocess",
        "missing",
        "null",
        "nan",
        "duplicate",
        "rename",
    ],
    "visualization": [
        "plot",
        "plt.",
        "figure",
        "ax.",
        "chart",
        "graph",
        "histogram",
        "scatter",
        "seaborn",
        "sns.",
        "bokeh",
        "plotly",
        "matplotlib",
    ],
    "modeling": [
        "fit",
        "predict",
        "train",
        "model",
        "classifier",
        "regressor",
        "sklearn",
        "tensorflow",
        "torch",
        "keras",
        "xgboost",
    ],
    "evaluation": [
        "accuracy",
        "precision",
        "recall",
        "f1",
        "score",
        "metric",
        "confusion_matrix",
        "roc",
        "auc",
        "loss",
        "evaluate",
    ],
    "feature_engineering": [
        "feature",
        "transform",
        "encode",
        "scale",
        "normalize",
        "one_hot",
        "label_encode",
        "polynomial",
        "pca",
    ],
    "setup": [
        "install",
        "pip",
        "conda",
        "import",
        "config",
        "setup",
        "environment",
        "version",
        "requirements",
    ],
    "analysis": [
        "describe",
        "info",
        "shape",
        "head",
        "tail",
        "summary",
        "statistics",
        "correlation",
        "groupby",
        "aggregate",
    ],
}


def _check_jupyter_deps():
    """Raise RuntimeError if nbformat is not installed."""
    if not JUPYTER_AVAILABLE:
        raise RuntimeError(
            "nbformat is required for Jupyter Notebook support.\n"
            'Install with: pip install "skill-seekers[jupyter]"\n'
            "Or: pip install nbformat"
        )


def infer_description_from_notebook(metadata: dict | None = None, name: str = "") -> str:
    """Infer skill description from notebook metadata.

    Args:
        metadata: Notebook-level metadata dict (kernelspec, language_info, etc.)
        name: Skill name for fallback

    Returns:
        Description string suitable for "Use when..." format
    """
    if metadata:
        lang_info = metadata.get("language_info", {})
        lang_name = lang_info.get("name", "") if isinstance(lang_info, dict) else ""
        title = metadata.get("title", "")
        if title and len(title) > 10:
            return f"Use when working with {title.lower()}"
        kernelspec = metadata.get("kernelspec", {})
        display_name = kernelspec.get("display_name", "") if isinstance(kernelspec, dict) else ""
        if display_name and len(display_name) > 3 and lang_name:
            return f"Use when working with {lang_name} notebooks ({display_name} kernel)"
        if lang_name:
            return f"Use when working with {lang_name} notebook content"
    return (
        f"Use when referencing {name} notebook documentation"
        if name
        else "Use when referencing this notebook documentation"
    )


class JupyterToSkillConverter:
    """Convert Jupyter Notebook (.ipynb) to skill."""

    def __init__(self, config: dict):
        self.config = config
        self.name = config["name"]
        self.notebook_path = config.get("notebook_path", "")
        self.description = (
            config.get("description") or f"Use when referencing {self.name} notebook documentation"
        )
        self.skill_dir = f"output/{self.name}"
        self.data_file = f"output/{self.name}_extracted.json"
        self.categories = config.get("categories", {})
        self.extracted_data: dict | None = None

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------

    def extract_notebook(self) -> bool:
        """Extract content from Jupyter Notebook file(s).

        Reads .ipynb via nbformat v4, extracts markdown/code/raw cells,
        detects language from kernel metadata, extracts imports, scores quality.
        Saves intermediate JSON to {name}_extracted.json. Returns True on success.
        """
        _check_jupyter_deps()
        print(f"\n🔍 Extracting from Jupyter Notebook: {self.notebook_path}")

        path = Path(self.notebook_path)
        if not path.exists():
            raise FileNotFoundError(f"Notebook path not found: {self.notebook_path}")

        notebook_files = self._collect_notebook_files(path)
        if not notebook_files:
            raise ValueError(
                f"No .ipynb files found at: {self.notebook_path}\n"
                "Provide a path to a .ipynb file or directory containing notebooks."
            )
        print(f"   Found {len(notebook_files)} notebook(s)")

        all_sections: list[dict] = []
        combined_metadata: dict = {}
        total_code_blocks = total_markdown_cells = total_raw_cells = 0
        languages_detected: dict[str, int] = {}
        all_imports: list[str] = []
        section_number = 0

        for nb_file in notebook_files:
            try:
                nb_data = self._parse_single_notebook(nb_file)
            except Exception as e:
                logger.warning("Failed to parse notebook %s: %s", nb_file, e)
                print(f"   ⚠️  Skipping {nb_file.name}: {e}")
                continue

            if not combined_metadata:
                combined_metadata = nb_data["metadata"]
            nb_lang = nb_data["language"]
            if nb_lang:
                languages_detected[nb_lang] = (
                    languages_detected.get(nb_lang, 0) + nb_data["code_cell_count"]
                )
            for section in nb_data["sections"]:
                section_number += 1
                section["section_number"] = section_number
                section["source_notebook"] = nb_file.name
            all_sections.extend(nb_data["sections"])
            total_code_blocks += nb_data["code_cell_count"]
            total_markdown_cells += nb_data["markdown_cell_count"]
            total_raw_cells += nb_data["raw_cell_count"]
            all_imports.extend(nb_data["imports"])
            print(
                f"   📓 {nb_file.name}: {nb_data['code_cell_count']} code, "
                f"{nb_data['markdown_cell_count']} markdown, {nb_data['raw_cell_count']} raw cells"
            )

        if not self.config.get("description"):
            self.description = infer_description_from_notebook(combined_metadata, self.name)

        # Detect languages via LanguageDetector for unlabelled code cells
        try:
            from skill_seekers.cli.language_detector import LanguageDetector

            detector = LanguageDetector(min_confidence=0.15)
        except ImportError:
            detector = None
        if detector:
            for section in all_sections:
                for cs in section.get("code_samples", []):
                    if not cs.get("language") and cs.get("code"):
                        lang, conf = detector.detect_from_code(cs["code"])
                        if lang and conf >= 0.3:
                            cs["language"] = lang
                            languages_detected[lang] = languages_detected.get(lang, 0) + 1

        result_data = {
            "source_file": str(self.notebook_path),
            "metadata": combined_metadata,
            "total_sections": len(all_sections),
            "total_code_blocks": total_code_blocks,
            "total_markdown_cells": total_markdown_cells,
            "total_raw_cells": total_raw_cells,
            "total_notebooks": len(notebook_files),
            "languages_detected": languages_detected,
            "imports": sorted(set(all_imports)),
            "pages": all_sections,
        }
        os.makedirs(os.path.dirname(self.data_file) or ".", exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n💾 Saved extracted data to: {self.data_file}")
        self.extracted_data = result_data
        print(
            f"✅ Extracted {len(all_sections)} sections, "
            f"{total_code_blocks} code blocks, {total_markdown_cells} markdown cells"
        )
        return True

    def _collect_notebook_files(self, path: Path) -> list[Path]:
        """Collect .ipynb files from a path (single file or directory)."""
        if path.is_file():
            if not path.name.endswith(".ipynb"):
                raise ValueError(f"Not a Jupyter Notebook (expected .ipynb): {path}")
            return [path]
        if path.is_dir():
            notebooks = sorted(path.glob("**/*.ipynb"))
            return [nb for nb in notebooks if ".ipynb_checkpoints" not in str(nb)]
        raise ValueError(f"Path is not a file or directory: {path}")

    def _parse_single_notebook(self, nb_path: Path) -> dict:
        """Parse a single .ipynb file and return structured data."""
        with open(nb_path, encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=4)
        metadata = dict(nb.metadata) if nb.metadata else {}
        language = self._detect_language(metadata)
        sections: list[dict] = []
        code_cell_count = markdown_cell_count = raw_cell_count = 0
        imports: list[str] = []

        for cell_index, cell in enumerate(nb.cells):
            cell_type = cell.get("cell_type", "")
            source = cell.get("source", "")
            tags = dict(cell.get("metadata", {})).get("tags", [])

            if cell_type == "markdown":
                markdown_cell_count += 1
                sections.extend(self._parse_markdown_cell(source, cell_index, tags, nb_path.name))
            elif cell_type == "code":
                code_cell_count += 1
                sections.append(
                    self._parse_code_cell(cell, cell_index, language, tags, nb_path.name)
                )
                imports.extend(self._extract_imports(source, language))
            elif cell_type == "raw":
                raw_cell_count += 1
                sections.append(self._parse_raw_cell(source, cell_index, tags, nb_path.name))

        return {
            "metadata": metadata,
            "language": language,
            "sections": sections,
            "code_cell_count": code_cell_count,
            "markdown_cell_count": markdown_cell_count,
            "raw_cell_count": raw_cell_count,
            "imports": imports,
        }

    def _parse_markdown_cell(
        self, source: str, cell_index: int, tags: list[str], notebook_name: str
    ) -> list[dict]:
        """Parse a markdown cell, splitting by heading boundaries."""
        if not source.strip():
            return []
        lines = source.split("\n")
        sections: list[dict] = []
        current_heading = current_heading_level = ""
        current_lines: list[str] = []

        for line in lines:
            heading_match = re.match(r"^(#{1,6})\s+(.+)", line)
            if heading_match:
                if current_heading or current_lines:
                    sections.append(
                        self._build_markdown_section(
                            current_heading,
                            current_heading_level,
                            current_lines,
                            cell_index,
                            tags,
                            notebook_name,
                        )
                    )
                current_heading = heading_match.group(2).strip()
                current_heading_level = f"h{len(heading_match.group(1))}"
                current_lines = []
            else:
                current_lines.append(line)

        if current_heading or current_lines:
            sections.append(
                self._build_markdown_section(
                    current_heading,
                    current_heading_level,
                    current_lines,
                    cell_index,
                    tags,
                    notebook_name,
                )
            )
        return sections

    def _build_markdown_section(
        self,
        heading: str,
        heading_level: str,
        lines: list[str],
        cell_index: int,
        tags: list[str],
        notebook_name: str,
    ) -> dict:
        """Build a section dict from parsed markdown content."""
        text = "\n".join(lines).strip()
        code_samples = []
        code_block_pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
        for match in code_block_pattern.finditer(text):
            lang, code = match.group(1) or "", match.group(2).strip()
            if code:
                code_samples.append(
                    {
                        "code": code,
                        "language": lang,
                        "quality_score": _score_code_quality(code),
                    }
                )
        prose_text = code_block_pattern.sub("", text).strip()
        sub_headings = []
        for line in lines:
            sub_match = re.match(r"^(#{3,6})\s+(.+)", line)
            if sub_match:
                sub_text = sub_match.group(2).strip()
                if sub_text:
                    sub_headings.append({"level": f"h{len(sub_match.group(1))}", "text": sub_text})
        return {
            "section_number": 0,
            "heading": heading,
            "heading_level": heading_level or "h1",
            "text": prose_text,
            "headings": sub_headings,
            "code_samples": code_samples,
            "tables": [],
            "images": [],
            "cell_type": "markdown",
            "cell_index": cell_index,
            "tags": tags,
            "source_notebook": notebook_name,
        }

    def _parse_code_cell(
        self, cell: dict, cell_index: int, language: str, tags: list[str], notebook_name: str
    ) -> dict:
        """Parse a code cell including source and outputs."""
        source = cell.get("source", "")
        execution_count = cell.get("execution_count")
        code_samples = []
        if source.strip():
            code_samples.append(
                {
                    "code": source.strip(),
                    "language": language,
                    "quality_score": _score_code_quality(source),
                    "execution_count": execution_count,
                }
            )
        output_texts: list[str] = []
        output_errors: list[str] = []
        output_display: list[dict] = []
        for output in cell.get("outputs", []):
            output_type = output.get("output_type", "")
            if output_type == "stream":
                stream_text = output.get("text", "")
                if isinstance(stream_text, list):
                    stream_text = "".join(stream_text)
                if output.get("name", "stdout") == "stderr":
                    output_errors.append(stream_text)
                else:
                    output_texts.append(stream_text)
            elif output_type in ("execute_result", "display_data"):
                data = output.get("data", {})
                text_plain = data.get("text/plain", "")
                if isinstance(text_plain, list):
                    text_plain = "".join(text_plain)
                if text_plain:
                    output_texts.append(text_plain)
                for mime in ("text/html", "image/png", "image/svg+xml"):
                    if mime in data:
                        output_display.append({"mime_type": mime, "has_data": True})
            elif output_type == "error":
                ename, evalue = output.get("ename", "Error"), output.get("evalue", "")
                error_msg = f"{ename}: {evalue}"
                tb = output.get("traceback", [])
                if tb:
                    clean_tb = [re.sub(r"\x1b\[[0-9;]*m", "", line) for line in tb]
                    error_msg += "\n" + "\n".join(clean_tb)
                output_errors.append(error_msg)

        return {
            "section_number": 0,
            "heading": self._infer_code_heading(source, execution_count),
            "heading_level": "h3",
            "text": "\n".join(output_texts).strip() if output_texts else "",
            "headings": [],
            "code_samples": code_samples,
            "tables": [],
            "images": [],
            "cell_type": "code",
            "cell_index": cell_index,
            "tags": tags,
            "source_notebook": notebook_name,
            "execution_count": execution_count,
            "output_text": "\n".join(output_texts).strip(),
            "output_errors": output_errors,
            "output_display": output_display,
        }

    def _parse_raw_cell(
        self, source: str, cell_index: int, tags: list[str], notebook_name: str
    ) -> dict:
        """Parse a raw cell (unrendered text)."""
        return {
            "section_number": 0,
            "heading": "",
            "heading_level": "h3",
            "text": source.strip(),
            "headings": [],
            "code_samples": [],
            "tables": [],
            "images": [],
            "cell_type": "raw",
            "cell_index": cell_index,
            "tags": tags,
            "source_notebook": notebook_name,
        }

    def _infer_code_heading(self, source: str, execution_count: int | None) -> str:
        """Infer a descriptive heading for a code cell from first meaningful line."""
        if not source.strip():
            return f"Code Cell [{execution_count or '?'}]"
        first_line = source.strip().split("\n")[0].strip()
        comment_match = re.match(r"^#\s+(.+)", first_line)
        if comment_match:
            heading = comment_match.group(1).strip()
            return heading[:77] + "..." if len(heading) > 80 else heading
        def_match = re.match(r"^(?:def|class|async\s+def)\s+(\w+)", first_line)
        if def_match:
            return f"Define: {def_match.group(1)}"
        assign_match = re.match(r"^(\w+)\s*=", first_line)
        if assign_match and len(assign_match.group(1)) > 1:
            return f"Assign: {assign_match.group(1)}"
        magic_match = re.match(r"^(%+\w+)", first_line)
        if magic_match:
            return f"Magic: {magic_match.group(1)}"
        if first_line.startswith("!"):
            cmd = first_line[1:].strip().split()[0] if first_line[1:].strip() else "shell"
            return f"Shell: {cmd}"
        prefix = f"[{execution_count}]" if execution_count else ""
        return f"Code Cell {prefix}".strip()

    def _detect_language(self, metadata: dict) -> str:
        """Detect programming language from notebook kernel metadata."""
        kernelspec = metadata.get("kernelspec", {})
        if isinstance(kernelspec, dict):
            kernel_lang = kernelspec.get("language", "")
            if kernel_lang:
                return kernel_lang.lower()
            kernel_name = kernelspec.get("name", "")
            if kernel_name:
                name_lower = kernel_name.lower()
                for keyword, lang in [
                    ("python", "python"),
                    ("julia", "julia"),
                    ("scala", "scala"),
                    ("rust", "rust"),
                ]:
                    if keyword in name_lower:
                        return lang
                if name_lower in ("ir", "r"):
                    return "r"
                if "javascript" in name_lower or "node" in name_lower:
                    return "javascript"
                if "csharp" in name_lower or "dotnet" in name_lower:
                    return "csharp"
        lang_info = metadata.get("language_info", {})
        if isinstance(lang_info, dict):
            lang_name = lang_info.get("name", "")
            if lang_name:
                return lang_name.lower()
        return ""

    def _extract_imports(self, source: str, language: str) -> list[str]:
        """Extract import/library statements from code source."""
        if not source.strip():
            return []
        imports: list[str] = []
        lang_key = language.lower() if language else "python"
        patterns = _IMPORT_PATTERNS.get(lang_key, _IMPORT_PATTERNS.get("python", []))
        for pattern in patterns:
            for match in pattern.finditer(source):
                module_name = match.group(1).strip()
                if module_name and module_name not in imports:
                    imports.append(module_name)
        return imports

    # ------------------------------------------------------------------
    # Load / Categorize / Build
    # ------------------------------------------------------------------

    def load_extracted_data(self, json_path: str) -> bool:
        """Load previously extracted data from JSON."""
        print(f"\n📂 Loading extracted data from: {json_path}")
        with open(json_path, encoding="utf-8") as f:
            self.extracted_data = json.load(f)
        total = self.extracted_data.get("total_sections", len(self.extracted_data.get("pages", [])))
        print(f"✅ Loaded {total} sections")
        return True

    def categorize_content(self) -> dict[str, dict]:
        """Categorize sections based on cell type and topic keywords."""
        print("\n📋 Categorizing content...")
        categorized: dict[str, dict] = {}
        sections = self.extracted_data.get("pages", [])

        # Single notebook — use basename as category
        if self.notebook_path and Path(self.notebook_path).is_file():
            nb_basename = Path(self.notebook_path).stem
            categorized[self._sanitize_filename(nb_basename)] = {
                "title": nb_basename,
                "pages": sections,
            }
            print(f"✅ Created 1 category (single notebook source)")
            print(f"   - {nb_basename}: {len(sections)} sections")
            return categorized

        # Custom keyword-based categories
        if self.categories:
            first_value = next(iter(self.categories.values()), None)
            if isinstance(first_value, list) and first_value and isinstance(first_value[0], dict):
                for cat_key, pages in self.categories.items():
                    categorized[cat_key] = {
                        "title": cat_key.replace("_", " ").title(),
                        "pages": pages,
                    }
            else:
                for cat_key in self.categories:
                    categorized[cat_key] = {
                        "title": cat_key.replace("_", " ").title(),
                        "pages": [],
                    }
                for section in sections:
                    combined = self._section_text(section)
                    scores = {}
                    for cat_key, keywords in self.categories.items():
                        if isinstance(keywords, list):
                            score = sum(
                                1
                                for kw in keywords
                                if isinstance(kw, str) and kw.lower() in combined
                            )
                        else:
                            score = 0
                        if score > 0:
                            scores[cat_key] = score
                    if scores:
                        categorized[max(scores, key=scores.get)]["pages"].append(section)
                    else:
                        categorized.setdefault("other", {"title": "Other", "pages": []})
                        categorized["other"]["pages"].append(section)
            self._print_categories(categorized)
            return categorized

        # Auto-categorize by topic keywords
        topic_buckets: dict[str, list[dict]] = {}
        uncategorized: list[dict] = []
        for section in sections:
            combined = self._section_text(section)
            matched_topic, best_score = "", 0
            for topic, keywords in _TOPIC_KEYWORDS.items():
                score = sum(1 for kw in keywords if kw.lower() in combined)
                if score > best_score:
                    best_score, matched_topic = score, topic
            if matched_topic and best_score >= 2:
                topic_buckets.setdefault(matched_topic, []).append(section)
            else:
                uncategorized.append(section)
        for topic, pages in sorted(topic_buckets.items()):
            categorized[topic] = {"title": topic.replace("_", " ").title(), "pages": pages}
        if uncategorized:
            categorized["other"] = {"title": "Other", "pages": uncategorized}
        if not categorized:
            categorized["content"] = {"title": "Content", "pages": sections}
        self._print_categories(categorized)
        return categorized

    def _section_text(self, section: dict) -> str:
        """Combine section text, heading, and code into a single lowercase string."""
        text = section.get("text", "").lower()
        heading = section.get("heading", "").lower()
        code = " ".join(cs.get("code", "").lower() for cs in section.get("code_samples", []))
        return f"{text} {heading} {code}"

    def _print_categories(self, categorized: dict[str, dict]) -> None:
        print(f"✅ Created {len(categorized)} categories")
        for cat_data in categorized.values():
            print(f"   - {cat_data['title']}: {len(cat_data['pages'])} sections")

    def build_skill(self) -> None:
        """Build complete skill directory structure."""
        print(f"\n🏗️  Building skill: {self.name}")
        os.makedirs(f"{self.skill_dir}/references", exist_ok=True)
        os.makedirs(f"{self.skill_dir}/scripts", exist_ok=True)
        os.makedirs(f"{self.skill_dir}/assets", exist_ok=True)

        categorized = self.categorize_content()
        print("\n📝 Generating reference files...")
        total_categories = len(categorized)
        for section_num, (cat_key, cat_data) in enumerate(categorized.items(), 1):
            self._generate_reference_file(cat_key, cat_data, section_num, total_categories)
        self._generate_index(categorized)
        self._generate_skill_md(categorized)
        print(f"\n✅ Skill built successfully: {self.skill_dir}/")
        print(f"\n📦 Next step: Package with: skill-seekers package {self.skill_dir}/")

    # ------------------------------------------------------------------
    # Private generation methods
    # ------------------------------------------------------------------

    def _nb_basename(self) -> str:
        """Return the notebook stem if notebook_path points to a single file."""
        if self.notebook_path and Path(self.notebook_path).is_file():
            return Path(self.notebook_path).stem
        return ""

    def _ref_filename(self, sections: list[dict], section_num: int, total_sections: int) -> str:
        """Determine the reference file path for a category."""
        nb_base = self._nb_basename()
        if sections:
            sec_nums = [s.get("section_number", i + 1) for i, s in enumerate(sections)]
            if total_sections == 1:
                name = nb_base if nb_base else "main"
                return f"{self.skill_dir}/references/{name}.md"
            sec_range = f"s{min(sec_nums)}-s{max(sec_nums)}"
            base = nb_base or "section"
            return f"{self.skill_dir}/references/{base}_{sec_range}.md"
        return f"{self.skill_dir}/references/section_{section_num:02d}.md"

    def _generate_reference_file(
        self, _cat_key: str, cat_data: dict, section_num: int, total_sections: int
    ) -> None:
        """Generate a reference markdown file for a category."""
        sections = cat_data["pages"]
        filename = self._ref_filename(sections, section_num, total_sections)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {cat_data['title']}\n\n")
            for section in sections:
                sec_num = section.get("section_number", "?")
                heading = section.get("heading", "")
                heading_level = section.get("heading_level", "h1")
                cell_type = section.get("cell_type", "markdown")

                f.write(f"---\n\n**📄 Source: Section {sec_num}**")
                if cell_type == "code":
                    ec = section.get("execution_count")
                    f.write(f" (Code Cell{f' [In {ec}]' if ec else ''})")
                elif cell_type == "raw":
                    f.write(" (Raw Cell)")
                f.write("\n\n")

                if heading:
                    md_lvl = (
                        "#" * (int(heading_level[1]) + 1) if heading_level.startswith("h") else "##"
                    )
                    f.write(f"{md_lvl} {heading}\n\n")
                for sub in section.get("headings", []):
                    sl, st = sub.get("level", "h3"), sub.get("text", "")
                    if st:
                        smd = "#" * (int(sl[1]) + 1) if sl.startswith("h") else "###"
                        f.write(f"{smd} {st}\n\n")
                if section.get("text"):
                    f.write(f"{section['text']}\n\n")
                for code in section.get("code_samples", []):
                    ec = code.get("execution_count")
                    if ec:
                        f.write(f"**In [{ec}]:**\n\n")
                    f.write(f"```{code.get('language', '')}\n{code['code']}\n```\n\n")
                if section.get("output_text"):
                    f.write(f"**Output:**\n\n```\n{section['output_text']}\n```\n\n")
                for err in section.get("output_errors", []):
                    f.write(f"**Errors:**\n\n```\n{err}\n```\n\n")
                disp = section.get("output_display", [])
                if disp:
                    mimes = [d.get("mime_type", "") for d in disp]
                    f.write(f"*Rich output: {', '.join(mimes)}*\n\n")
                for table in section.get("tables", []):
                    headers, rows = table.get("headers", []), table.get("rows", [])
                    if headers:
                        f.write("| " + " | ".join(str(h) for h in headers) + " |\n")
                        f.write("| " + " | ".join("---" for _ in headers) + " |\n")
                    for row in rows:
                        f.write("| " + " | ".join(str(c) for c in row) + " |\n")
                    f.write("\n")
                tags = section.get("tags", [])
                if tags:
                    f.write(f"*Tags: {', '.join(str(t) for t in tags)}*\n\n")
                f.write("---\n\n")
        print(f"   Generated: {filename}")

    def _generate_index(self, categorized: dict[str, dict]) -> None:
        """Generate reference index file."""
        filename = f"{self.skill_dir}/references/index.md"
        nb_base = self._nb_basename()
        total_cats = len(categorized)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {self.name.title()} Notebook Reference\n\n## Categories\n\n")
            for section_num, (_ck, cd) in enumerate(categorized.items(), 1):
                pages = cd["pages"]
                count = len(pages)
                if pages:
                    snums = [s.get("section_number", i + 1) for i, s in enumerate(pages)]
                    rng = f"Sections {min(snums)}-{max(snums)}"
                    if total_cats == 1:
                        link = f"{nb_base}.md" if nb_base else "main.md"
                    else:
                        base = nb_base or "section"
                        link = f"{base}_s{min(snums)}-s{max(snums)}.md"
                else:
                    link, rng = f"section_{section_num:02d}.md", "N/A"
                f.write(f"- [{cd['title']}]({link}) ({count} sections, {rng})\n")

            f.write("\n## Statistics\n\n")
            ed = self.extracted_data
            f.write(f"- Total sections: {ed.get('total_sections', 0)}\n")
            f.write(f"- Code cells: {ed.get('total_code_blocks', 0)}\n")
            f.write(f"- Markdown cells: {ed.get('total_markdown_cells', 0)}\n")
            f.write(f"- Raw cells: {ed.get('total_raw_cells', 0)}\n")
            f.write(f"- Notebooks: {ed.get('total_notebooks', 1)}\n")

            meta = ed.get("metadata", {})
            ks = meta.get("kernelspec", {})
            if isinstance(ks, dict) and ks.get("display_name"):
                f.write(f"- Kernel: {ks['display_name']}\n")
            li = meta.get("language_info", {})
            if isinstance(li, dict) and li.get("version"):
                f.write(f"- Language version: {li.get('name', '')} {li['version']}\n")

            imports = ed.get("imports", [])
            if imports:
                f.write(f"\n## Imported Packages ({len(imports)})\n\n")
                for imp in imports[:30]:
                    f.write(f"- `{imp}`\n")
                if len(imports) > 30:
                    f.write(f"- ... and {len(imports) - 30} more\n")
        print(f"   Generated: {filename}")

    def _generate_skill_md(self, categorized: dict[str, dict]) -> None:
        """Generate main SKILL.md file."""
        filename = f"{self.skill_dir}/SKILL.md"
        skill_name = self.name.lower().replace("_", "-").replace(" ", "-")[:64]
        desc = self.description[:1024]
        ed = self.extracted_data

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"---\nname: {skill_name}\ndescription: {desc}\n---\n\n")
            f.write(f"# {self.name.title()} Notebook Skill\n\n{self.description}\n\n")

            # Notebook metadata
            meta = ed.get("metadata", {})
            ks = meta.get("kernelspec", {})
            li = meta.get("language_info", {})
            has_ks = isinstance(ks, dict) and ks.get("display_name")
            has_li = isinstance(li, dict) and li.get("name")
            if has_ks or has_li:
                f.write("## 📋 Notebook Information\n\n")
                if has_ks:
                    f.write(f"**Kernel:** {ks['display_name']}\n\n")
                if has_li:
                    ver = li.get("version", "")
                    f.write(f"**Language:** {li['name']}{' ' + ver if ver else ''}\n\n")

            f.write("## 💡 When to Use This Skill\n\nUse this skill when you need to:\n")
            f.write(f"- Understand {self.name} concepts and analysis workflow\n")
            f.write("- Reference code examples and their outputs\n")
            f.write("- Reproduce data analysis or computation steps\n")
            f.write("- Review methodology, visualizations, and results\n")
            f.write("- Find library usage patterns and best practices\n\n")

            total_sections = ed.get("total_sections", 0)
            f.write(f"## 📖 Section Overview\n\n**Total Sections:** {total_sections}\n\n")
            f.write("**Content Breakdown:**\n\n")
            for cd in categorized.values():
                f.write(f"- **{cd['title']}**: {len(cd['pages'])} sections\n")
            f.write("\n")

            f.write(self._format_key_concepts())

            imports = ed.get("imports", [])
            if imports:
                f.write(f"## 📦 Dependencies\n\n*{len(imports)} package(s) imported*\n\n")
                for imp in imports[:20]:
                    f.write(f"- `{imp}`\n")
                if len(imports) > 20:
                    f.write(f"- ... and {len(imports) - 20} more\n")
                f.write("\n")

            f.write("## ⚡ Quick Reference\n\n")
            f.write(self._format_patterns_from_content())

            # Top code examples
            all_code: list[dict] = []
            for section in ed.get("pages", []):
                all_code.extend(section.get("code_samples", []))
            all_code.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
            top_code = all_code[:15]
            if top_code:
                f.write("## 📝 Code Examples\n\n*High-quality code cells from notebook*\n\n")
                by_lang: dict[str, list] = {}
                for c in top_code:
                    by_lang.setdefault(c.get("language", "unknown"), []).append(c)
                for lang in sorted(by_lang):
                    examples = by_lang[lang]
                    f.write(f"### {lang.title()} Examples ({len(examples)})\n\n")
                    for i, c in enumerate(examples[:5], 1):
                        quality = c.get("quality_score", 0)
                        ec = c.get("execution_count")
                        label = f"In [{ec}]" if ec else f"Example {i}"
                        code_text = c.get("code", "")
                        f.write(f"**{label}** (Quality: {quality:.1f}/10):\n\n```{lang}\n")
                        f.write(code_text[:500] + ("\n..." if len(code_text) > 500 else ""))
                        f.write("\n```\n\n")

            f.write("## 📊 Notebook Statistics\n\n")
            f.write(f"- **Total Sections**: {total_sections}\n")
            f.write(f"- **Code Cells**: {ed.get('total_code_blocks', 0)}\n")
            f.write(f"- **Markdown Cells**: {ed.get('total_markdown_cells', 0)}\n")
            f.write(f"- **Raw Cells**: {ed.get('total_raw_cells', 0)}\n")
            f.write(f"- **Notebooks**: {ed.get('total_notebooks', 1)}\n")
            langs = ed.get("languages_detected", {})
            if langs:
                f.write(f"- **Programming Languages**: {len(langs)}\n\n")
                f.write("**Language Breakdown:**\n\n")
                for lang, count in sorted(langs.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- {lang}: {count} code cells\n")
                f.write("\n")

            f.write("## 🗺️ Navigation\n\n**Reference Files:**\n\n")
            for cd in categorized.values():
                cat_file = self._sanitize_filename(cd["title"])
                f.write(f"- `references/{cat_file}.md` - {cd['title']}\n")
            f.write("\nSee `references/index.md` for complete notebook structure.\n\n")
            f.write("---\n\n**Generated by Skill Seeker** | Jupyter Notebook Scraper\n")

        with open(filename, encoding="utf-8") as f:
            line_count = len(f.read().split("\n"))
        print(f"   Generated: {filename} ({line_count} lines)")

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------

    def _format_key_concepts(self) -> str:
        """Extract key concepts from markdown headings across all sections."""
        all_headings: list[tuple[str, str]] = []
        for section in self.extracted_data.get("pages", []):
            heading = section.get("heading", "").strip()
            level = section.get("heading_level", "h1")
            if heading and len(heading) > 3 and section.get("cell_type") == "markdown":
                all_headings.append((level, heading))
            for sub in section.get("headings", []):
                st = sub.get("text", "").strip()
                if st and len(st) > 3:
                    all_headings.append((sub.get("level", "h3"), st))
        if not all_headings:
            return ""
        content = "## 🔑 Key Concepts\n\n*Main topics covered in this notebook*\n\n"
        h1s = [text for lvl, text in all_headings if lvl == "h1"]
        h2s = [text for lvl, text in all_headings if lvl == "h2"]
        if h1s:
            content += "**Major Topics:**\n\n" + "".join(f"- {h}\n" for h in h1s[:10]) + "\n"
        if h2s:
            content += "**Subtopics:**\n\n" + "".join(f"- {h}\n" for h in h2s[:15]) + "\n"
        return content

    def _format_patterns_from_content(self) -> str:
        """Extract common patterns from text content headings."""
        pattern_keywords = [
            "getting started",
            "installation",
            "configuration",
            "usage",
            "api",
            "examples",
            "tutorial",
            "guide",
            "best practices",
            "troubleshooting",
            "faq",
            "data loading",
            "preprocessing",
            "modeling",
            "evaluation",
            "results",
            "conclusion",
            "summary",
        ]
        patterns: list[dict] = []
        for section in self.extracted_data.get("pages", []):
            heading_text = section.get("heading", "").lower()
            sec_num = section.get("section_number", 0)
            for kw in pattern_keywords:
                if kw in heading_text:
                    patterns.append(
                        {
                            "type": kw.title(),
                            "heading": section.get("heading", ""),
                            "section": sec_num,
                        }
                    )
                    break
        if not patterns:
            return "*See reference files for detailed content*\n\n"
        content = "*Common documentation patterns found:*\n\n"
        by_type: dict[str, list] = {}
        for p in patterns:
            by_type.setdefault(p["type"], []).append(p)
        for ptype in sorted(by_type):
            items = by_type[ptype]
            content += f"**{ptype}** ({len(items)} sections):\n"
            for item in items[:3]:
                content += f"- {item['heading']} (section {item['section']})\n"
            content += "\n"
        return content

    def _sanitize_filename(self, name: str) -> str:
        """Convert string to safe filename."""
        safe = re.sub(r"[^\w\s-]", "", name.lower())
        return re.sub(r"[-\s]+", "_", safe)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _score_code_quality(code: str) -> float:
    """Simple quality heuristic for code blocks (0–10 scale)."""
    if not code:
        return 0.0
    score = 5.0
    lines = code.strip().split("\n")
    line_count = len(lines)
    if line_count >= 10:
        score += 2.0
    elif line_count >= 5:
        score += 1.0
    if re.search(r"\b(def |class |function |func |fn )", code):
        score += 1.5
    if re.search(r"\b(import |from .+ import|require\(|#include|using )", code):
        score += 0.5
    if re.search(r"^    ", code, re.MULTILINE):
        score += 0.5
    if re.search(r"[=:{}()\[\]]", code):
        score += 0.3
    if re.search(r'""".*?"""|\'\'\'.*?\'\'\'', code, re.DOTALL):
        score += 0.3
    if re.search(r"^%", code, re.MULTILINE):
        score += 0.2
    if len(code) < 30:
        score -= 2.0
    non_magic = [ln for ln in lines if ln.strip() and not ln.strip().startswith(("%", "!"))]
    if line_count > 0 and not non_magic:
        score -= 1.0
    return min(10.0, max(0.0, score))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """Standalone CLI entry point for the Jupyter Notebook scraper."""
    from .arguments.jupyter import add_jupyter_arguments
    from skill_seekers.cli.execution_context import ExecutionContext

    # Try to get context first (new path)
    try:
        ctx = ExecutionContext.get()
        args = None  # Signal to use context
    except RuntimeError:
        # Fallback: parse argv (backward compatibility)
        parser = argparse.ArgumentParser(
            description="Convert Jupyter Notebook (.ipynb) to skill",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        add_jupyter_arguments(parser)
        args = parser.parse_args()

        # Initialize context for downstream
        ExecutionContext.initialize(args=args)
        ctx = ExecutionContext.get()

    # Set logging level from behavior args
    if args:
        if getattr(args, "quiet", False):
            logging.getLogger().setLevel(logging.WARNING)
        elif getattr(args, "verbose", False):
            logging.getLogger().setLevel(logging.DEBUG)

    # Dry run check
    if ctx.output.dry_run or (args and getattr(args, "dry_run", False)):
        source = (
            (args and (getattr(args, "notebook", None) or getattr(args, "from_json", None)))
            or ctx.output.name
            or "(none)"
        )
        print(f"\n{'=' * 60}")
        print("DRY RUN: Jupyter Notebook Extraction")
        print(f"{'=' * 60}")
        print(f"Source:         {source}")
        print(f"Name:           {ctx.output.name or '(auto-detect)'}")
        print(f"Enhance level:  {ctx.enhancement.level}")
        print(f"\n✅ Dry run complete")
        return 0

    # Validate inputs
    has_input = (
        (args and (getattr(args, "notebook", None) or getattr(args, "from_json", None)))
        or (ctx.output.name)  # Context provides name for output
    )
    if not has_input:
        if args:
            parser.error("Must specify --notebook or --from-json")
        else:
            print("Error: No input source provided", file=sys.stderr)
            sys.exit(1)

    # Build from JSON workflow
    if args and getattr(args, "from_json", None):
        name = Path(args.from_json).stem.replace("_extracted", "")
        config = {
            "name": getattr(args, "name", None) or name,
            "description": getattr(args, "description", None)
            or f"Use when referencing {name} notebook documentation",
        }
        try:
            converter = JupyterToSkillConverter(config)
            converter.load_extracted_data(args.from_json)
            converter.build_skill()
        except Exception as e:
            print(f"\n❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
        return 0

    # Direct notebook mode - build config from ctx or args
    if args is None:
        # Using ExecutionContext
        if not ctx.output.name:
            print("Error: Must specify --name when using ExecutionContext", file=sys.stderr)
            sys.exit(1)
        config = {
            "name": ctx.output.name,
            "notebook_path": "",  # Must be provided via other means when using context
            "description": f"Use when referencing {ctx.output.name} notebook documentation",
        }
    else:
        # Using args
        if not getattr(args, "name", None):
            nb_path = Path(args.notebook)
            args.name = nb_path.stem if nb_path.is_file() else (nb_path.name or "notebooks")

        config = {
            "name": args.name,
            "notebook_path": args.notebook,
            "description": getattr(args, "description", None),
        }

    try:
        converter = JupyterToSkillConverter(config)
        if not converter.extract_notebook():
            print("\n❌ Notebook extraction failed - see error above", file=sys.stderr)
            sys.exit(1)
        converter.build_skill()

        from skill_seekers.cli.workflow_runner import run_workflows

        workflow_executed, workflow_names = run_workflows(args if args else argparse.Namespace())
        workflow_name = ", ".join(workflow_names) if workflow_names else None

        enhance_level = ctx.enhancement.level if ctx.enhancement.enabled else 0
        if args and getattr(args, "enhance_level", 0) > 0 and not ctx.enhancement.enabled:
            enhance_level = args.enhance_level

        if enhance_level > 0:
            api_key = ctx.enhancement.api_key or os.environ.get("ANTHROPIC_API_KEY")
            mode = "API" if api_key else "LOCAL"
            print("\n" + "=" * 80)
            print(f"🤖 Traditional AI Enhancement ({mode} mode, level {enhance_level})")
            print("=" * 80)
            if workflow_executed:
                print(f"   Running after workflow: {workflow_name}")
                print(
                    "   (Workflow provides specialized analysis, "
                    "enhancement provides general improvements)"
                )
            print("")
            skill_dir = converter.skill_dir
            if api_key:
                try:
                    from skill_seekers.cli.enhance_skill import enhance_skill_md

                    enhance_skill_md(skill_dir, api_key)
                    print("✅ API enhancement complete!")
                except ImportError:
                    print("❌ API enhancement not available. Falling back to LOCAL mode...")
                    from skill_seekers.cli.enhance_skill_local import LocalSkillEnhancer

                    agent = ctx.enhancement.agent
                    agent_cmd = ctx.enhancement.agent_cmd
                    enhancer = LocalSkillEnhancer(Path(skill_dir), agent=agent, agent_cmd=agent_cmd)
                    enhancer.run(headless=True)
                    print("✅ Local enhancement complete!")
            else:
                from skill_seekers.cli.enhance_skill_local import LocalSkillEnhancer

                agent = ctx.enhancement.agent
                agent_cmd = ctx.enhancement.agent_cmd
                enhancer = LocalSkillEnhancer(Path(skill_dir), agent=agent, agent_cmd=agent_cmd)
                enhancer.run(headless=True)
                print("✅ Local enhancement complete!")

    except RuntimeError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during Jupyter processing: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())
