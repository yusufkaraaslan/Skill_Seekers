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

    def test_copies_each_pdf_reference_tree_without_name_collisions(self):
        """Unified PDF output preserves every source's readable references and assets."""
        from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder

        first_skill_dir = os.path.join(self.temp_dir, "first")
        second_skill_dir = os.path.join(self.temp_dir, "second")
        first_refs = os.path.join(first_skill_dir, "references")
        second_refs = os.path.join(second_skill_dir, "references")
        first_assets = os.path.join(first_skill_dir, "assets")
        second_assets = os.path.join(second_skill_dir, "assets")
        for path in [first_refs, second_refs, first_assets, second_assets]:
            os.makedirs(path)

        with open(os.path.join(first_refs, "content.md"), "w") as f:
            f.write("FIRST SENTINEL\n\n![first](../assets/cover.png)\n")
        with open(os.path.join(second_refs, "content.md"), "w") as f:
            f.write("SECOND SENTINEL\n\n![second](../assets/cover.png)\n")
        with open(os.path.join(first_assets, "cover.png"), "wb") as f:
            f.write(b"first image")
        with open(os.path.join(second_assets, "cover.png"), "wb") as f:
            f.write(b"second image")

        config = {"name": "test_pdf_refs", "description": "Test", "sources": []}
        scraped_data = {
            "documentation": [],
            "github": [],
            "pdf": [
                {"pdf_id": "book_one", "idx": 0, "refs_dir": first_refs},
                {"pdf_id": "book_two", "idx": 1, "refs_dir": second_refs},
            ],
        }

        builder = UnifiedSkillBuilder(config, scraped_data)
        builder._generate_pdf_references(scraped_data["pdf"])

        pdf_dir = os.path.join(builder.skill_dir, "references", "pdf")
        first_output = os.path.join(pdf_dir, "0_book_one")
        second_output = os.path.join(pdf_dir, "1_book_two")
        with open(os.path.join(first_output, "references", "content.md")) as f:
            self.assertIn("FIRST SENTINEL", f.read())
        with open(os.path.join(second_output, "references", "content.md")) as f:
            self.assertIn("SECOND SENTINEL", f.read())
        self.assertTrue(os.path.exists(os.path.join(first_output, "assets", "cover.png")))
        self.assertTrue(os.path.exists(os.path.join(second_output, "assets", "cover.png")))

        with open(os.path.join(pdf_dir, "index.md")) as f:
            index = f.read()
        self.assertIn("0_book_one/references/content.md", index)
        self.assertIn("1_book_two/references/content.md", index)

    def test_rebuild_removes_references_for_deleted_pdf_source(self):
        """Rebuilding cannot leave removed source content available to enhancers."""
        from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder

        first_refs = os.path.join(self.temp_dir, "first", "references")
        second_refs = os.path.join(self.temp_dir, "second", "references")
        os.makedirs(first_refs)
        os.makedirs(second_refs)
        for refs_dir in [first_refs, second_refs]:
            with open(os.path.join(refs_dir, "content.md"), "w") as f:
                f.write("content")

        config = {"name": "test_pdf_rebuild", "description": "Test", "sources": []}
        scraped_data = {
            "documentation": [],
            "github": [],
            "pdf": [
                {"pdf_id": "keep", "idx": 0, "refs_dir": first_refs},
                {"pdf_id": "remove", "idx": 1, "refs_dir": second_refs},
            ],
        }
        builder = UnifiedSkillBuilder(config, scraped_data)
        builder._generate_pdf_references(scraped_data["pdf"])

        pdf_dir = os.path.join(builder.skill_dir, "references", "pdf")
        self.assertTrue(os.path.isdir(os.path.join(pdf_dir, "1_remove")))

        builder._generate_pdf_references(scraped_data["pdf"][:1])

        self.assertFalse(os.path.exists(os.path.join(pdf_dir, "1_remove")))

    def test_rebuild_removes_pdf_directory_when_source_type_is_deleted(self):
        """A source type removed from config cannot survive in the final references."""
        from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder

        refs_dir = os.path.join(self.temp_dir, "pdf_source", "references")
        os.makedirs(refs_dir)
        with open(os.path.join(refs_dir, "content.md"), "w") as f:
            f.write("content")

        config = {"name": "test_pdf_type_removal", "description": "Test", "sources": []}
        scraped_data = {
            "documentation": [],
            "github": [],
            "pdf": [{"pdf_id": "manual", "idx": 0, "refs_dir": refs_dir}],
        }
        builder = UnifiedSkillBuilder(config, scraped_data)
        builder._generate_references()

        pdf_dir = os.path.join(builder.skill_dir, "references", "pdf")
        self.assertTrue(os.path.isdir(pdf_dir))
        builder.scraped_data["pdf"] = []

        builder._generate_references()

        self.assertFalse(os.path.exists(pdf_dir))


class TestUnifiedSkillBuilderGenericReferences(unittest.TestCase):
    """Test readable reference preservation for converter-backed source types."""

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

    def test_copies_epub_markdown_references_and_keeps_raw_data(self):
        """EPUB references remain readable while the legacy data JSON stays available."""
        from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder

        source_dir = os.path.join(self.temp_dir, "epub_source")
        refs_dir = os.path.join(source_dir, "references")
        os.makedirs(refs_dir)
        with open(os.path.join(refs_dir, "chapter.md"), "w") as f:
            f.write("EPUB SENTINEL")

        data_file = os.path.join(self.temp_dir, "epub.json")
        with open(data_file, "w") as f:
            f.write('{"chapters": []}')

        config = {"name": "test_epub_refs", "description": "Test", "sources": []}
        scraped_data = {
            "documentation": [],
            "github": [],
            "pdf": [],
            "epub": [
                {
                    "epub_id": "handbook",
                    "idx": 0,
                    "refs_dir": refs_dir,
                    "data_file": data_file,
                    "data": {},
                }
            ],
        }

        builder = UnifiedSkillBuilder(config, scraped_data)
        builder._generate_generic_references("epub", scraped_data["epub"])

        epub_dir = os.path.join(builder.skill_dir, "references", "epub")
        copied_reference = os.path.join(epub_dir, "0_handbook", "references", "chapter.md")
        with open(copied_reference) as f:
            self.assertEqual(f.read(), "EPUB SENTINEL")
        self.assertTrue(os.path.exists(os.path.join(epub_dir, "handbook_data.json")))

        with open(os.path.join(epub_dir, "index.md")) as f:
            index = f.read()
        self.assertIn("0_handbook/references/chapter.md", index)

    def test_rebuild_removes_stale_namespace_when_references_disappear(self):
        """A missing cache tree cannot leak references left by an earlier build."""
        from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder

        refs_dir = os.path.join(self.temp_dir, "epub_source", "references")
        os.makedirs(refs_dir)
        with open(os.path.join(refs_dir, "chapter.md"), "w") as f:
            f.write("stale content")

        config = {"name": "test_epub_rebuild", "description": "Test", "sources": []}
        source = {"epub_id": "handbook", "idx": 0, "refs_dir": refs_dir, "data": {}}
        builder = UnifiedSkillBuilder(config, {"epub": [source]})
        builder._generate_generic_references("epub", [source])

        namespace = os.path.join(builder.skill_dir, "references", "epub", "0_handbook")
        self.assertTrue(os.path.isdir(namespace))
        shutil.rmtree(refs_dir)

        builder._generate_generic_references("epub", [source])

        self.assertFalse(os.path.exists(namespace))

    def test_copies_video_frames_next_to_readable_references(self):
        """Visual video Markdown keeps its ../frames links valid after unification."""
        from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder

        source_dir = os.path.join(self.temp_dir, "video_source")
        refs_dir = os.path.join(source_dir, "references")
        frames_dir = os.path.join(source_dir, "frames")
        os.makedirs(refs_dir)
        os.makedirs(frames_dir)
        with open(os.path.join(refs_dir, "transcript.md"), "w") as f:
            f.write("![frame](../frames/frame.jpg)")
        with open(os.path.join(frames_dir, "frame.jpg"), "wb") as f:
            f.write(b"video frame")

        config = {"name": "test_video_refs", "description": "Test", "sources": []}
        source = {"video_id": "demo", "idx": 0, "refs_dir": refs_dir, "data": {}}
        builder = UnifiedSkillBuilder(config, {"video": [source]})
        builder._generate_generic_references("video", [source])

        output_dir = os.path.join(builder.skill_dir, "references", "video", "0_demo")
        with open(os.path.join(output_dir, "references", "transcript.md")) as f:
            self.assertIn("../frames/frame.jpg", f.read())
        with open(os.path.join(output_dir, "frames", "frame.jpg"), "rb") as f:
            self.assertEqual(f.read(), b"video frame")


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
