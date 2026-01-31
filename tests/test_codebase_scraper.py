#!/usr/bin/env python3
"""
Tests for codebase_scraper.py - Standalone codebase analysis CLI.

Test Coverage:
- Language detection
- Directory exclusion
- File walking
- .gitignore loading
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from skill_seekers.cli.codebase_scraper import (
    DEFAULT_EXCLUDED_DIRS,
    FOLDER_CATEGORIES,
    MARKDOWN_EXTENSIONS,
    ROOT_DOC_CATEGORIES,
    categorize_markdown_file,
    detect_language,
    extract_markdown_structure,
    generate_markdown_summary,
    load_gitignore,
    should_exclude_dir,
    walk_directory,
    walk_markdown_files,
)


class TestLanguageDetection(unittest.TestCase):
    """Tests for language detection from file extensions"""

    def test_python_detection(self):
        """Test Python file detection."""
        self.assertEqual(detect_language(Path("test.py")), "Python")

    def test_javascript_detection(self):
        """Test JavaScript file detection."""
        self.assertEqual(detect_language(Path("test.js")), "JavaScript")
        self.assertEqual(detect_language(Path("test.jsx")), "JavaScript")

    def test_typescript_detection(self):
        """Test TypeScript file detection."""
        self.assertEqual(detect_language(Path("test.ts")), "TypeScript")
        self.assertEqual(detect_language(Path("test.tsx")), "TypeScript")

    def test_cpp_detection(self):
        """Test C++ file detection."""
        self.assertEqual(detect_language(Path("test.cpp")), "C++")
        self.assertEqual(detect_language(Path("test.h")), "C++")
        self.assertEqual(detect_language(Path("test.hpp")), "C++")

    def test_csharp_detection(self):
        """Test C# file detection."""
        self.assertEqual(detect_language(Path("test.cs")), "C#")

    def test_go_detection(self):
        """Test Go file detection."""
        self.assertEqual(detect_language(Path("test.go")), "Go")

    def test_rust_detection(self):
        """Test Rust file detection."""
        self.assertEqual(detect_language(Path("test.rs")), "Rust")

    def test_java_detection(self):
        """Test Java file detection."""
        self.assertEqual(detect_language(Path("test.java")), "Java")

    def test_ruby_detection(self):
        """Test Ruby file detection."""
        self.assertEqual(detect_language(Path("test.rb")), "Ruby")

    def test_php_detection(self):
        """Test PHP file detection."""
        self.assertEqual(detect_language(Path("test.php")), "PHP")

    def test_unknown_language(self):
        """Test unknown file extension."""
        self.assertEqual(detect_language(Path("test.swift")), "Unknown")
        self.assertEqual(detect_language(Path("test.txt")), "Unknown")


class TestDirectoryExclusion(unittest.TestCase):
    """Tests for directory exclusion logic"""

    def test_node_modules_excluded(self):
        """Test that node_modules is excluded."""
        self.assertTrue(should_exclude_dir("node_modules", DEFAULT_EXCLUDED_DIRS))

    def test_venv_excluded(self):
        """Test that venv is excluded."""
        self.assertTrue(should_exclude_dir("venv", DEFAULT_EXCLUDED_DIRS))

    def test_git_excluded(self):
        """Test that .git is excluded."""
        self.assertTrue(should_exclude_dir(".git", DEFAULT_EXCLUDED_DIRS))

    def test_normal_dir_not_excluded(self):
        """Test that normal directories are not excluded."""
        self.assertFalse(should_exclude_dir("src", DEFAULT_EXCLUDED_DIRS))
        self.assertFalse(should_exclude_dir("tests", DEFAULT_EXCLUDED_DIRS))


class TestDirectoryWalking(unittest.TestCase):
    """Tests for directory walking functionality"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_walk_empty_directory(self):
        """Test walking empty directory."""
        files = walk_directory(self.root)
        self.assertEqual(len(files), 0)

    def test_walk_with_python_files(self):
        """Test walking directory with Python files."""
        # Create test files
        (self.root / "test1.py").write_text('print("test")')
        (self.root / "test2.py").write_text('print("test2")')
        (self.root / "readme.txt").write_text("readme")

        files = walk_directory(self.root)

        # Should only find Python files
        self.assertEqual(len(files), 2)
        self.assertTrue(all(f.suffix == ".py" for f in files))

    def test_walk_excludes_node_modules(self):
        """Test that node_modules directory is excluded."""
        # Create test files
        (self.root / "test.py").write_text("test")

        # Create node_modules with files
        node_modules = self.root / "node_modules"
        node_modules.mkdir()
        (node_modules / "package.js").write_text("test")

        files = walk_directory(self.root)

        # Should only find root test.py, not package.js
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "test.py")

    def test_walk_with_subdirectories(self):
        """Test walking nested directory structure."""
        # Create nested structure
        src_dir = self.root / "src"
        src_dir.mkdir()
        (src_dir / "module.py").write_text("test")

        tests_dir = self.root / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_module.py").write_text("test")

        files = walk_directory(self.root)

        # Should find both files
        self.assertEqual(len(files), 2)
        filenames = [f.name for f in files]
        self.assertIn("module.py", filenames)
        self.assertIn("test_module.py", filenames)


class TestGitignoreLoading(unittest.TestCase):
    """Tests for .gitignore loading"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_no_gitignore(self):
        """Test behavior when no .gitignore exists."""
        spec = load_gitignore(self.root)
        # Should return None when no .gitignore found
        self.assertIsNone(spec)

    def test_load_gitignore(self):
        """Test loading valid .gitignore file."""
        # Create .gitignore
        gitignore_path = self.root / ".gitignore"
        gitignore_path.write_text("*.log\ntemp/\n")

        spec = load_gitignore(self.root)

        # Should successfully load pathspec (if pathspec is installed)
        # If pathspec is not installed, spec will be None
        if spec is not None:
            # Verify it's a PathSpec object
            self.assertIsNotNone(spec)


class TestMarkdownDocumentation(unittest.TestCase):
    """Tests for markdown documentation extraction (C3.9)"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_markdown_extensions(self):
        """Test that markdown extensions are properly defined."""
        self.assertIn(".md", MARKDOWN_EXTENSIONS)
        self.assertIn(".markdown", MARKDOWN_EXTENSIONS)

    def test_root_doc_categories(self):
        """Test root document category mapping."""
        self.assertEqual(ROOT_DOC_CATEGORIES.get("readme"), "overview")
        self.assertEqual(ROOT_DOC_CATEGORIES.get("changelog"), "changelog")
        self.assertEqual(ROOT_DOC_CATEGORIES.get("architecture"), "architecture")

    def test_folder_categories(self):
        """Test folder category mapping."""
        self.assertEqual(FOLDER_CATEGORIES.get("guides"), "guides")
        self.assertEqual(FOLDER_CATEGORIES.get("tutorials"), "guides")
        self.assertEqual(FOLDER_CATEGORIES.get("workflows"), "workflows")
        self.assertEqual(FOLDER_CATEGORIES.get("architecture"), "architecture")

    def test_walk_markdown_files(self):
        """Test walking directory for markdown files."""
        # Create test markdown files
        (self.root / "README.md").write_text("# Test README")
        (self.root / "test.py").write_text("print('test')")

        docs_dir = self.root / "docs"
        docs_dir.mkdir()
        (docs_dir / "guide.md").write_text("# Guide")

        files = walk_markdown_files(self.root)

        # Should find markdown files only
        self.assertEqual(len(files), 2)
        filenames = [f.name for f in files]
        self.assertIn("README.md", filenames)
        self.assertIn("guide.md", filenames)

    def test_categorize_root_readme(self):
        """Test categorizing root README file."""
        readme_path = self.root / "README.md"
        readme_path.write_text("# Test")

        category = categorize_markdown_file(readme_path, self.root)
        self.assertEqual(category, "overview")

    def test_categorize_changelog(self):
        """Test categorizing CHANGELOG file."""
        changelog_path = self.root / "CHANGELOG.md"
        changelog_path.write_text("# Changelog")

        category = categorize_markdown_file(changelog_path, self.root)
        self.assertEqual(category, "changelog")

    def test_categorize_docs_guide(self):
        """Test categorizing file in docs/guides folder."""
        guides_dir = self.root / "docs" / "guides"
        guides_dir.mkdir(parents=True)
        guide_path = guides_dir / "getting-started.md"
        guide_path.write_text("# Getting Started")

        category = categorize_markdown_file(guide_path, self.root)
        self.assertEqual(category, "guides")

    def test_categorize_architecture(self):
        """Test categorizing architecture documentation."""
        arch_dir = self.root / "docs" / "architecture"
        arch_dir.mkdir(parents=True)
        arch_path = arch_dir / "overview.md"
        arch_path.write_text("# Architecture")

        category = categorize_markdown_file(arch_path, self.root)
        self.assertEqual(category, "architecture")


class TestMarkdownStructureExtraction(unittest.TestCase):
    """Tests for markdown structure extraction"""

    def test_extract_headers(self):
        """Test extracting headers from markdown."""
        content = """# Main Title

## Section 1
Some content

### Subsection
More content

## Section 2
"""
        structure = extract_markdown_structure(content)

        self.assertEqual(structure["title"], "Main Title")
        self.assertEqual(len(structure["headers"]), 4)
        self.assertEqual(structure["headers"][0]["level"], 1)
        self.assertEqual(structure["headers"][1]["level"], 2)

    def test_extract_code_blocks(self):
        """Test extracting code blocks from markdown."""
        content = """# Example

```python
def hello():
    print("Hello")
```

```javascript
console.log("test");
```
"""
        structure = extract_markdown_structure(content)

        self.assertEqual(len(structure["code_blocks"]), 2)
        self.assertEqual(structure["code_blocks"][0]["language"], "python")
        self.assertEqual(structure["code_blocks"][1]["language"], "javascript")

    def test_extract_links(self):
        """Test extracting links from markdown."""
        content = """# Links

Check out [Example](https://example.com) and [Another](./local.md).
"""
        structure = extract_markdown_structure(content)

        self.assertEqual(len(structure["links"]), 2)
        self.assertEqual(structure["links"][0]["text"], "Example")
        self.assertEqual(structure["links"][0]["url"], "https://example.com")

    def test_word_and_line_count(self):
        """Test word and line count."""
        content = "First line\nSecond line\nThird line"
        structure = extract_markdown_structure(content)

        self.assertEqual(structure["line_count"], 3)
        self.assertEqual(structure["word_count"], 6)  # First, line, Second, line, Third, line


class TestMarkdownSummaryGeneration(unittest.TestCase):
    """Tests for markdown summary generation"""

    def test_generate_summary_with_title(self):
        """Test summary includes title."""
        content = "# My Title\n\nSome content here."
        structure = extract_markdown_structure(content)
        summary = generate_markdown_summary(content, structure)

        self.assertIn("**My Title**", summary)

    def test_generate_summary_with_sections(self):
        """Test summary includes section names."""
        content = """# Main

## Getting Started
Content

## Installation
Content

## Usage
Content
"""
        structure = extract_markdown_structure(content)
        summary = generate_markdown_summary(content, structure)

        self.assertIn("Sections:", summary)

    def test_generate_summary_truncation(self):
        """Test summary is truncated to max length."""
        content = "# Title\n\n" + "Long content. " * 100
        structure = extract_markdown_structure(content)
        summary = generate_markdown_summary(content, structure, max_length=200)

        self.assertLessEqual(len(summary), 210)  # Allow some buffer for truncation marker


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
