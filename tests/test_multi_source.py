"""
Tests for multi-source support in unified scraper and skill builder.

Tests the following functionality:
1. Multiple sources of same type in unified_scraper (list structure)
2. Source counters and unique naming
3. Per-source reference directory generation in unified_skill_builder
4. Multiple documentation sources handling
5. Multiple GitHub repositories handling
"""

import os
import shutil
import tempfile
import unittest


class TestUnifiedScraperDataStructure(unittest.TestCase):
    """Test scraped_data list structure in unified_scraper."""

    def test_scraped_data_uses_list_structure(self):
        """Test that scraped_data uses list for each source type."""
        from skill_seekers.cli.unified_scraper import UnifiedScraper

        config = {
            "name": "test_multi",
            "description": "Test skill",
            "sources": [{"type": "documentation", "base_url": "https://example.com"}],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            original_dir = os.getcwd()
            try:
                os.chdir(temp_dir)
                scraper = UnifiedScraper(config)

                self.assertIsInstance(scraper.scraped_data["documentation"], list)
                self.assertIsInstance(scraper.scraped_data["github"], list)
                self.assertIsInstance(scraper.scraped_data["pdf"], list)
            finally:
                os.chdir(original_dir)

    def test_source_counters_initialized_to_zero(self):
        """Test that source counters start at zero."""
        from skill_seekers.cli.unified_scraper import UnifiedScraper

        config = {
            "name": "test_counters",
            "description": "Test skill",
            "sources": [{"type": "documentation", "base_url": "https://example.com"}],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            original_dir = os.getcwd()
            try:
                os.chdir(temp_dir)
                scraper = UnifiedScraper(config)

                self.assertEqual(scraper._source_counters["documentation"], 0)
                self.assertEqual(scraper._source_counters["github"], 0)
                self.assertEqual(scraper._source_counters["pdf"], 0)
            finally:
                os.chdir(original_dir)

    def test_empty_lists_initially(self):
        """Test that source lists are empty initially."""
        from skill_seekers.cli.unified_scraper import UnifiedScraper

        config = {
            "name": "test_empty",
            "description": "Test skill",
            "sources": [{"type": "documentation", "base_url": "https://example.com"}],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            original_dir = os.getcwd()
            try:
                os.chdir(temp_dir)
                scraper = UnifiedScraper(config)

                self.assertEqual(len(scraper.scraped_data["documentation"]), 0)
                self.assertEqual(len(scraper.scraped_data["github"]), 0)
                self.assertEqual(len(scraper.scraped_data["pdf"]), 0)
            finally:
                os.chdir(original_dir)


class TestUnifiedSkillBuilderDocsReferences(unittest.TestCase):
    """Test documentation reference generation for multiple sources."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_dir)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_creates_subdirectory_per_source(self):
        """Test that each doc source gets its own subdirectory."""
        from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder

        # Create mock refs directories
        refs_dir1 = os.path.join(self.temp_dir, "refs1")
        refs_dir2 = os.path.join(self.temp_dir, "refs2")
        os.makedirs(refs_dir1)
        os.makedirs(refs_dir2)

        config = {"name": "test_docs_refs", "description": "Test", "sources": []}

        scraped_data = {
            "documentation": [
                {
                    "source_id": "source_a",
                    "base_url": "https://a.com",
                    "total_pages": 5,
                    "refs_dir": refs_dir1,
                },
                {
                    "source_id": "source_b",
                    "base_url": "https://b.com",
                    "total_pages": 3,
                    "refs_dir": refs_dir2,
                },
            ],
            "github": [],
            "pdf": [],
        }

        builder = UnifiedSkillBuilder(config, scraped_data)
        builder._generate_docs_references(scraped_data["documentation"])

        docs_dir = os.path.join(builder.skill_dir, "references", "documentation")
        self.assertTrue(os.path.exists(os.path.join(docs_dir, "source_a")))
        self.assertTrue(os.path.exists(os.path.join(docs_dir, "source_b")))

    def test_creates_index_per_source(self):
        """Test that each source subdirectory has its own index.md."""
        from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder

        refs_dir = os.path.join(self.temp_dir, "refs")
        os.makedirs(refs_dir)

        config = {"name": "test_source_index", "description": "Test", "sources": []}

        scraped_data = {
            "documentation": [
                {
                    "source_id": "my_source",
                    "base_url": "https://example.com",
                    "total_pages": 10,
                    "refs_dir": refs_dir,
                }
            ],
            "github": [],
            "pdf": [],
        }

        builder = UnifiedSkillBuilder(config, scraped_data)
        builder._generate_docs_references(scraped_data["documentation"])

        source_index = os.path.join(
            builder.skill_dir, "references", "documentation", "my_source", "index.md"
        )
        self.assertTrue(os.path.exists(source_index))

        with open(source_index) as f:
            content = f.read()
            self.assertIn("my_source", content)
            self.assertIn("https://example.com", content)

    def test_creates_main_index_listing_all_sources(self):
        """Test that main index.md lists all documentation sources."""
        from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder

        refs_dir1 = os.path.join(self.temp_dir, "refs1")
        refs_dir2 = os.path.join(self.temp_dir, "refs2")
        os.makedirs(refs_dir1)
        os.makedirs(refs_dir2)

        config = {"name": "test_main_index", "description": "Test", "sources": []}

        scraped_data = {
            "documentation": [
                {
                    "source_id": "docs_one",
                    "base_url": "https://one.com",
                    "total_pages": 10,
                    "refs_dir": refs_dir1,
                },
                {
                    "source_id": "docs_two",
                    "base_url": "https://two.com",
                    "total_pages": 20,
                    "refs_dir": refs_dir2,
                },
            ],
            "github": [],
            "pdf": [],
        }

        builder = UnifiedSkillBuilder(config, scraped_data)
        builder._generate_docs_references(scraped_data["documentation"])

        main_index = os.path.join(builder.skill_dir, "references", "documentation", "index.md")
        self.assertTrue(os.path.exists(main_index))

        with open(main_index) as f:
            content = f.read()
            self.assertIn("docs_one", content)
            self.assertIn("docs_two", content)
            self.assertIn("2 documentation sources", content)

    def test_copies_reference_files_to_source_dir(self):
        """Test that reference files are copied to source subdirectory."""
        from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder

        refs_dir = os.path.join(self.temp_dir, "refs")
        os.makedirs(refs_dir)

        # Create mock reference files
        with open(os.path.join(refs_dir, "api.md"), "w") as f:
            f.write("# API Reference")
        with open(os.path.join(refs_dir, "guide.md"), "w") as f:
            f.write("# User Guide")

        config = {"name": "test_copy_refs", "description": "Test", "sources": []}

        scraped_data = {
            "documentation": [
                {
                    "source_id": "test_source",
                    "base_url": "https://test.com",
                    "total_pages": 5,
                    "refs_dir": refs_dir,
                }
            ],
            "github": [],
            "pdf": [],
        }

        builder = UnifiedSkillBuilder(config, scraped_data)
        builder._generate_docs_references(scraped_data["documentation"])

        source_dir = os.path.join(builder.skill_dir, "references", "documentation", "test_source")
        self.assertTrue(os.path.exists(os.path.join(source_dir, "api.md")))
        self.assertTrue(os.path.exists(os.path.join(source_dir, "guide.md")))

    def test_single_docs_source_creates_top_level_compatibility_references(self):
        """Docs-only unified skills should expose flat references for easier browsing and scoring."""
        from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder

        refs_dir = os.path.join(self.temp_dir, "refs")
        os.makedirs(refs_dir)

        with open(os.path.join(refs_dir, "api.md"), "w") as f:
            f.write("# API Reference")
        with open(os.path.join(refs_dir, "getting_started.md"), "w") as f:
            f.write("# Getting Started")

        config = {"name": "docs_only_skill", "description": "Test", "sources": []}
        scraped_data = {
            "documentation": [
                {
                    "source_id": "docs_source",
                    "base_url": "https://docs.example.com",
                    "total_pages": 2,
                    "refs_dir": refs_dir,
                }
            ],
            "github": [],
            "pdf": [],
        }

        builder = UnifiedSkillBuilder(config, scraped_data)
        builder._generate_docs_references(scraped_data["documentation"])

        top_level_refs = os.path.join(builder.skill_dir, "references")
        self.assertTrue(os.path.exists(os.path.join(top_level_refs, "api.md")))
        self.assertTrue(os.path.exists(os.path.join(top_level_refs, "getting_started.md")))


class TestUnifiedSkillBuilderGitHubReferences(unittest.TestCase):
    """Test GitHub reference generation for multiple repositories."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_dir)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_creates_subdirectory_per_repo(self):
        """Test that each GitHub repo gets its own subdirectory."""
        from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder

        config = {"name": "test_github_refs", "description": "Test", "sources": []}

        scraped_data = {
            "documentation": [],
            "github": [
                {
                    "repo": "org/repo1",
                    "repo_id": "org_repo1",
                    "data": {"readme": "# Repo 1", "issues": [], "releases": [], "repo_info": {}},
                },
                {
                    "repo": "org/repo2",
                    "repo_id": "org_repo2",
                    "data": {"readme": "# Repo 2", "issues": [], "releases": [], "repo_info": {}},
                },
            ],
            "pdf": [],
        }

        builder = UnifiedSkillBuilder(config, scraped_data)
        builder._generate_github_references(scraped_data["github"])

        github_dir = os.path.join(builder.skill_dir, "references", "github")
        self.assertTrue(os.path.exists(os.path.join(github_dir, "org_repo1")))
        self.assertTrue(os.path.exists(os.path.join(github_dir, "org_repo2")))

    def test_creates_readme_per_repo(self):
        """Test that README.md is created for each repo."""
        from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder

        config = {"name": "test_readme", "description": "Test", "sources": []}

        scraped_data = {
            "documentation": [],
            "github": [
                {
                    "repo": "test/myrepo",
                    "repo_id": "test_myrepo",
                    "data": {
                        "readme": "# My Repository\n\nDescription here.",
                        "issues": [],
                        "releases": [],
                        "repo_info": {},
                    },
                }
            ],
            "pdf": [],
        }

        builder = UnifiedSkillBuilder(config, scraped_data)
        builder._generate_github_references(scraped_data["github"])

        readme_path = os.path.join(
            builder.skill_dir, "references", "github", "test_myrepo", "README.md"
        )
        self.assertTrue(os.path.exists(readme_path))

        with open(readme_path) as f:
            content = f.read()
            self.assertIn("test/myrepo", content)

    def test_creates_issues_file_when_issues_exist(self):
        """Test that issues.md is created when repo has issues."""
        from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder

        config = {"name": "test_issues", "description": "Test", "sources": []}

        scraped_data = {
            "documentation": [],
            "github": [
                {
                    "repo": "test/repo",
                    "repo_id": "test_repo",
                    "data": {
                        "readme": "# Repo",
                        "issues": [
                            {
                                "number": 1,
                                "title": "Bug report",
                                "state": "open",
                                "labels": ["bug"],
                                "url": "https://github.com/test/repo/issues/1",
                            },
                            {
                                "number": 2,
                                "title": "Feature request",
                                "state": "closed",
                                "labels": ["enhancement"],
                                "url": "https://github.com/test/repo/issues/2",
                            },
                        ],
                        "releases": [],
                        "repo_info": {},
                    },
                }
            ],
            "pdf": [],
        }

        builder = UnifiedSkillBuilder(config, scraped_data)
        builder._generate_github_references(scraped_data["github"])

        issues_path = os.path.join(
            builder.skill_dir, "references", "github", "test_repo", "issues.md"
        )
        self.assertTrue(os.path.exists(issues_path))

        with open(issues_path) as f:
            content = f.read()
            self.assertIn("Bug report", content)
            self.assertIn("Feature request", content)

    def test_creates_main_index_listing_all_repos(self):
        """Test that main index.md lists all GitHub repositories."""
        from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder

        config = {"name": "test_github_index", "description": "Test", "sources": []}

        scraped_data = {
            "documentation": [],
            "github": [
                {
                    "repo": "org/first",
                    "repo_id": "org_first",
                    "data": {
                        "readme": "#",
                        "issues": [],
                        "releases": [],
                        "repo_info": {"stars": 100},
                    },
                },
                {
                    "repo": "org/second",
                    "repo_id": "org_second",
                    "data": {
                        "readme": "#",
                        "issues": [],
                        "releases": [],
                        "repo_info": {"stars": 50},
                    },
                },
            ],
            "pdf": [],
        }

        builder = UnifiedSkillBuilder(config, scraped_data)
        builder._generate_github_references(scraped_data["github"])

        main_index = os.path.join(builder.skill_dir, "references", "github", "index.md")
        self.assertTrue(os.path.exists(main_index))

        with open(main_index) as f:
            content = f.read()
            self.assertIn("org/first", content)
            self.assertIn("org/second", content)
            self.assertIn("2 GitHub repositories", content)


class TestUnifiedSkillBuilderPdfReferences(unittest.TestCase):
    """Test PDF reference generation for multiple sources."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_dir)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_creates_pdf_index_with_count(self):
        """Test that PDF index shows correct document count."""
        from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder

        config = {"name": "test_pdf", "description": "Test", "sources": []}

        scraped_data = {
            "documentation": [],
            "github": [],
            "pdf": [
                {"path": "/path/to/doc1.pdf"},
                {"path": "/path/to/doc2.pdf"},
                {"path": "/path/to/doc3.pdf"},
            ],
        }

        builder = UnifiedSkillBuilder(config, scraped_data)
        builder._generate_pdf_references(scraped_data["pdf"])

        pdf_index = os.path.join(builder.skill_dir, "references", "pdf", "index.md")
        self.assertTrue(os.path.exists(pdf_index))

        with open(pdf_index) as f:
            content = f.read()
            self.assertIn("3 PDF document", content)


class TestCodebaseAnalysisIndex(unittest.TestCase):
    """Issue #362: SKILL.md must link to a real codebase_analysis target.

    Per-source ARCHITECTURE.md files live at
    ``references/codebase_analysis/{source_id}/ARCHITECTURE.md``, but four
    call sites historically linked to ``references/codebase_analysis/
    ARCHITECTURE.md`` (no source_id). That link was always broken once the
    layout became per-source-namespaced.

    The fix: generate a top-level ``references/codebase_analysis/index.md``
    aggregating all sources, and route every SKILL.md link through it.
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _run_build(self, sources_local):
        from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder

        config = {"name": "issue-362", "description": "Test"}
        scraped_data = {
            "documentation": [],
            "github": [],
            "pdf": [],
            "local": sources_local,
        }
        builder = UnifiedSkillBuilder(config, scraped_data)
        builder.build()
        return builder

    def test_index_md_lists_each_local_source(self):
        sample_patterns = [
            {
                "file_path": "/x/foo.py",
                "patterns": [
                    {"pattern_type": "Singleton", "confidence": 0.88, "indicators": ["__instance"]}
                ],
            }
        ]
        builder = self._run_build(
            [
                {
                    "source_id": "issue-362_local_0_repo_a",
                    "name": "repo_a",
                    "patterns": sample_patterns,
                },
                {
                    "source_id": "issue-362_local_1_repo_b",
                    "name": "repo_b",
                    "patterns": sample_patterns,
                },
            ]
        )

        index_path = os.path.join(builder.skill_dir, "references", "codebase_analysis", "index.md")
        self.assertTrue(os.path.isfile(index_path), "codebase_analysis/index.md must be created")

        with open(index_path) as f:
            content = f.read()
        self.assertIn("issue-362_local_0_repo_a", content)
        self.assertIn("issue-362_local_1_repo_b", content)
        self.assertIn("issue-362_local_0_repo_a/ARCHITECTURE.md", content)
        self.assertIn("issue-362_local_0_repo_a/patterns/", content)

    def test_skill_md_link_resolves_to_real_file(self):
        """The SKILL.md link to codebase_analysis must resolve on disk."""
        sample_patterns = [
            {
                "file_path": "/x/foo.py",
                "patterns": [
                    {"pattern_type": "Singleton", "confidence": 0.88, "indicators": ["__instance"]}
                ],
            }
        ]
        builder = self._run_build(
            [
                {
                    "source_id": "issue-362_local_0_repo",
                    "name": "repo",
                    "patterns": sample_patterns,
                },
            ]
        )

        skill_md = os.path.join(builder.skill_dir, "SKILL.md")
        with open(skill_md) as f:
            content = f.read()

        import re

        targets = re.findall(r"references/codebase_analysis/[^\s`)]+", content)
        self.assertTrue(targets, "SKILL.md must mention a codebase_analysis link")

        for target in targets:
            full = os.path.join(builder.skill_dir, target)
            self.assertTrue(
                os.path.exists(full),
                f"SKILL.md links to {target!r} but file does not exist on disk",
            )

    def test_no_index_when_no_codebase_data(self):
        """No C3.x output → no index file written."""
        builder = self._run_build([])  # no local sources at all
        index_path = os.path.join(builder.skill_dir, "references", "codebase_analysis", "index.md")
        self.assertFalse(os.path.exists(index_path))


if __name__ == "__main__":
    unittest.main()
