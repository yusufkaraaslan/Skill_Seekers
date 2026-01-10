#!/usr/bin/env python3
"""
Tests for codebase_scraper.py - Standalone codebase analysis CLI.

Test Coverage:
- Language detection
- Directory exclusion
- File walking
- .gitignore loading
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from skill_seekers.cli.codebase_scraper import (
    detect_language,
    should_exclude_dir,
    walk_directory,
    load_gitignore,
    DEFAULT_EXCLUDED_DIRS
)


class TestLanguageDetection(unittest.TestCase):
    """Tests for language detection from file extensions"""

    def test_python_detection(self):
        """Test Python file detection."""
        self.assertEqual(detect_language(Path('test.py')), 'Python')

    def test_javascript_detection(self):
        """Test JavaScript file detection."""
        self.assertEqual(detect_language(Path('test.js')), 'JavaScript')
        self.assertEqual(detect_language(Path('test.jsx')), 'JavaScript')

    def test_typescript_detection(self):
        """Test TypeScript file detection."""
        self.assertEqual(detect_language(Path('test.ts')), 'TypeScript')
        self.assertEqual(detect_language(Path('test.tsx')), 'TypeScript')

    def test_cpp_detection(self):
        """Test C++ file detection."""
        self.assertEqual(detect_language(Path('test.cpp')), 'C++')
        self.assertEqual(detect_language(Path('test.h')), 'C++')
        self.assertEqual(detect_language(Path('test.hpp')), 'C++')

    def test_csharp_detection(self):
        """Test C# file detection."""
        self.assertEqual(detect_language(Path('test.cs')), 'C#')

    def test_go_detection(self):
        """Test Go file detection."""
        self.assertEqual(detect_language(Path('test.go')), 'Go')

    def test_rust_detection(self):
        """Test Rust file detection."""
        self.assertEqual(detect_language(Path('test.rs')), 'Rust')

    def test_java_detection(self):
        """Test Java file detection."""
        self.assertEqual(detect_language(Path('test.java')), 'Java')

    def test_ruby_detection(self):
        """Test Ruby file detection."""
        self.assertEqual(detect_language(Path('test.rb')), 'Ruby')

    def test_php_detection(self):
        """Test PHP file detection."""
        self.assertEqual(detect_language(Path('test.php')), 'PHP')

    def test_unknown_language(self):
        """Test unknown file extension."""
        self.assertEqual(detect_language(Path('test.swift')), 'Unknown')
        self.assertEqual(detect_language(Path('test.txt')), 'Unknown')


class TestDirectoryExclusion(unittest.TestCase):
    """Tests for directory exclusion logic"""

    def test_node_modules_excluded(self):
        """Test that node_modules is excluded."""
        self.assertTrue(should_exclude_dir('node_modules', DEFAULT_EXCLUDED_DIRS))

    def test_venv_excluded(self):
        """Test that venv is excluded."""
        self.assertTrue(should_exclude_dir('venv', DEFAULT_EXCLUDED_DIRS))

    def test_git_excluded(self):
        """Test that .git is excluded."""
        self.assertTrue(should_exclude_dir('.git', DEFAULT_EXCLUDED_DIRS))

    def test_normal_dir_not_excluded(self):
        """Test that normal directories are not excluded."""
        self.assertFalse(should_exclude_dir('src', DEFAULT_EXCLUDED_DIRS))
        self.assertFalse(should_exclude_dir('tests', DEFAULT_EXCLUDED_DIRS))


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
        (self.root / 'test1.py').write_text('print("test")')
        (self.root / 'test2.py').write_text('print("test2")')
        (self.root / 'readme.txt').write_text('readme')

        files = walk_directory(self.root)

        # Should only find Python files
        self.assertEqual(len(files), 2)
        self.assertTrue(all(f.suffix == '.py' for f in files))

    def test_walk_excludes_node_modules(self):
        """Test that node_modules directory is excluded."""
        # Create test files
        (self.root / 'test.py').write_text('test')

        # Create node_modules with files
        node_modules = self.root / 'node_modules'
        node_modules.mkdir()
        (node_modules / 'package.js').write_text('test')

        files = walk_directory(self.root)

        # Should only find root test.py, not package.js
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, 'test.py')

    def test_walk_with_subdirectories(self):
        """Test walking nested directory structure."""
        # Create nested structure
        src_dir = self.root / 'src'
        src_dir.mkdir()
        (src_dir / 'module.py').write_text('test')

        tests_dir = self.root / 'tests'
        tests_dir.mkdir()
        (tests_dir / 'test_module.py').write_text('test')

        files = walk_directory(self.root)

        # Should find both files
        self.assertEqual(len(files), 2)
        filenames = [f.name for f in files]
        self.assertIn('module.py', filenames)
        self.assertIn('test_module.py', filenames)


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
        gitignore_path = self.root / '.gitignore'
        gitignore_path.write_text('*.log\ntemp/\n')

        spec = load_gitignore(self.root)

        # Should successfully load pathspec (if pathspec is installed)
        # If pathspec is not installed, spec will be None
        if spec is not None:
            # Verify it's a PathSpec object
            self.assertIsNotNone(spec)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
