#!/usr/bin/env python3
"""
Tests for v3.2.0 new source type integration points.

Covers source detection, config validation, generic merge, CLI wiring,
and source validation for the 10 new source types: jupyter, html, openapi,
asciidoc, pptx, rss, manpage, confluence, notion, chat.
"""

import os
import textwrap

import pytest

from skill_seekers.cli.config_validator import ConfigValidator
from skill_seekers.cli.source_detector import SourceDetector, SourceInfo
from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder


# ---------------------------------------------------------------------------
# 1. SourceDetector — new type detection
# ---------------------------------------------------------------------------


class TestSourceDetectorNewTypes:
    """Test that SourceDetector.detect() maps new extensions to correct types."""

    # -- Jupyter --
    def test_detect_ipynb(self):
        """Test .ipynb → jupyter detection."""
        info = SourceDetector.detect("analysis.ipynb")
        assert info.type == "jupyter"
        assert info.parsed["file_path"] == "analysis.ipynb"
        assert info.suggested_name == "analysis"

    # -- HTML --
    def test_detect_html_extension(self):
        """Test .html → html detection."""
        info = SourceDetector.detect("page.html")
        assert info.type == "html"
        assert info.parsed["file_path"] == "page.html"

    def test_detect_htm_extension(self):
        """Test .htm → html detection."""
        info = SourceDetector.detect("index.HTM")
        assert info.type == "html"
        assert info.parsed["file_path"] == "index.HTM"

    # -- PowerPoint --
    def test_detect_pptx(self):
        """Test .pptx → pptx detection."""
        info = SourceDetector.detect("slides.pptx")
        assert info.type == "pptx"
        assert info.parsed["file_path"] == "slides.pptx"
        assert info.suggested_name == "slides"

    # -- AsciiDoc --
    def test_detect_adoc(self):
        """Test .adoc → asciidoc detection."""
        info = SourceDetector.detect("manual.adoc")
        assert info.type == "asciidoc"
        assert info.parsed["file_path"] == "manual.adoc"

    def test_detect_asciidoc_extension(self):
        """Test .asciidoc → asciidoc detection."""
        info = SourceDetector.detect("guide.ASCIIDOC")
        assert info.type == "asciidoc"
        assert info.parsed["file_path"] == "guide.ASCIIDOC"

    # -- Man pages --
    def test_detect_man_extension(self):
        """Test .man → manpage detection."""
        info = SourceDetector.detect("curl.man")
        assert info.type == "manpage"
        assert info.parsed["file_path"] == "curl.man"

    @pytest.mark.parametrize("section", range(1, 9))
    def test_detect_man_sections(self, section):
        """Test .1 through .8 → manpage for simple basenames."""
        filename = f"git.{section}"
        info = SourceDetector.detect(filename)
        assert info.type == "manpage", f"{filename} should detect as manpage"
        assert info.suggested_name == "git"

    def test_man_section_with_dotted_basename_not_detected(self):
        """Test that 'access.log.1' is NOT detected as a man page.

        The heuristic checks that the basename (without extension) has no dots.
        """
        # This should fall through to web/domain detection (has a dot, not a path)
        info = SourceDetector.detect("access.log.1")
        # access.log.1 has a dot in the basename-without-ext ("access.log"),
        # so it should NOT be detected as manpage.  It falls through to the
        # domain inference branch because it contains a dot and doesn't start
        # with '/'.
        assert info.type != "manpage"

    # -- RSS/Atom --
    def test_detect_rss_extension(self):
        """Test .rss → rss detection."""
        info = SourceDetector.detect("feed.rss")
        assert info.type == "rss"
        assert info.parsed["file_path"] == "feed.rss"

    def test_detect_atom_extension(self):
        """Test .atom → rss detection."""
        info = SourceDetector.detect("updates.atom")
        assert info.type == "rss"
        assert info.parsed["file_path"] == "updates.atom"

    def test_xml_not_detected_as_rss(self):
        """Test .xml is NOT detected as rss (too generic).

        The fix ensures .xml files do not get incorrectly classified as RSS feeds.
        """
        # .xml has no special handling — it will fall through to domain inference
        # or raise ValueError depending on contents.  Either way, it must not
        # be classified as "rss".
        info = SourceDetector.detect("data.xml")
        assert info.type != "rss"

    # -- OpenAPI --
    def test_yaml_with_openapi_content_detected(self, tmp_path):
        """Test .yaml with 'openapi:' key → openapi detection."""
        spec = tmp_path / "petstore.yaml"
        spec.write_text(
            textwrap.dedent("""\
                openapi: "3.0.0"
                info:
                  title: Petstore
                  version: "1.0.0"
                paths: {}
            """)
        )
        info = SourceDetector.detect(str(spec))
        assert info.type == "openapi"
        assert info.parsed["file_path"] == str(spec)
        assert info.suggested_name == "petstore"

    def test_yaml_with_swagger_content_detected(self, tmp_path):
        """Test .yaml with 'swagger:' key → openapi detection."""
        spec = tmp_path / "legacy.yml"
        spec.write_text(
            textwrap.dedent("""\
                swagger: "2.0"
                info:
                  title: Legacy API
                basePath: /v1
            """)
        )
        info = SourceDetector.detect(str(spec))
        assert info.type == "openapi"

    def test_yaml_without_openapi_not_detected(self, tmp_path):
        """Test .yaml without OpenAPI content is NOT detected as openapi.

        When the YAML file doesn't contain openapi/swagger keys the detector
        skips OpenAPI and falls through.  For an absolute path it will raise
        ValueError (cannot determine type), which still confirms it was NOT
        classified as openapi.
        """
        plain = tmp_path / "config.yaml"
        plain.write_text("name: my-project\nversion: 1.0\n")
        # Absolute path falls through to ValueError (no matching type).
        # Either way, it must NOT be "openapi".
        try:
            info = SourceDetector.detect(str(plain))
            assert info.type != "openapi"
        except ValueError:
            # Raised because source type cannot be determined — this is fine,
            # the important thing is it was not classified as openapi.
            pass

    def test_looks_like_openapi_returns_false_for_missing_file(self):
        """Test _looks_like_openapi returns False for non-existent file."""
        assert SourceDetector._looks_like_openapi("/nonexistent/spec.yaml") is False

    def test_looks_like_openapi_json_key_format(self, tmp_path):
        """Test _looks_like_openapi detects JSON-style keys (quoted)."""
        spec = tmp_path / "api.yaml"
        spec.write_text('"openapi": "3.0.0"\n')
        assert SourceDetector._looks_like_openapi(str(spec)) is True


# ---------------------------------------------------------------------------
# 2. ConfigValidator — new source type validation
# ---------------------------------------------------------------------------


class TestConfigValidatorNewTypes:
    """Test ConfigValidator VALID_SOURCE_TYPES and per-type validation."""

    # All 17 expected types
    EXPECTED_TYPES = {
        "documentation",
        "github",
        "pdf",
        "local",
        "word",
        "video",
        "epub",
        "jupyter",
        "html",
        "openapi",
        "asciidoc",
        "pptx",
        "confluence",
        "notion",
        "rss",
        "manpage",
        "chat",
    }

    def test_all_17_types_present(self):
        """Test that VALID_SOURCE_TYPES contains all 17 types."""
        assert ConfigValidator.VALID_SOURCE_TYPES == self.EXPECTED_TYPES

    def test_unknown_type_rejected(self):
        """Test that an unknown source type is rejected during validation."""
        config = {
            "name": "test",
            "description": "test",
            "sources": [{"type": "foobar"}],
        }
        validator = ConfigValidator(config)
        with pytest.raises(ValueError, match="Invalid type 'foobar'"):
            validator.validate()

    # --- Per-type required-field validation ---

    def _make_config(self, source: dict) -> dict:
        """Helper: wrap a source dict in a valid config structure."""
        return {
            "name": "test",
            "description": "test",
            "sources": [source],
        }

    def test_epub_requires_path(self):
        """Test epub source validation requires 'path'."""
        config = self._make_config({"type": "epub"})
        validator = ConfigValidator(config)
        with pytest.raises(ValueError, match="Missing required field 'path'"):
            validator.validate()

    def test_jupyter_requires_path(self):
        """Test jupyter source validation requires 'path'."""
        config = self._make_config({"type": "jupyter"})
        validator = ConfigValidator(config)
        with pytest.raises(ValueError, match="Missing required field 'path'"):
            validator.validate()

    def test_html_requires_path(self):
        """Test html source validation requires 'path'."""
        config = self._make_config({"type": "html"})
        validator = ConfigValidator(config)
        with pytest.raises(ValueError, match="Missing required field 'path'"):
            validator.validate()

    def test_openapi_requires_path_or_url(self):
        """Test openapi source validation requires 'path' or 'url'."""
        config = self._make_config({"type": "openapi"})
        validator = ConfigValidator(config)
        with pytest.raises(ValueError, match="Missing required field 'path' or 'url'"):
            validator.validate()

    def test_openapi_accepts_url(self):
        """Test openapi source passes validation with 'url'."""
        config = self._make_config({"type": "openapi", "url": "https://example.com/spec.yaml"})
        validator = ConfigValidator(config)
        assert validator.validate() is True

    def test_pptx_requires_path(self):
        """Test pptx source validation requires 'path'."""
        config = self._make_config({"type": "pptx"})
        validator = ConfigValidator(config)
        with pytest.raises(ValueError, match="Missing required field 'path'"):
            validator.validate()

    def test_asciidoc_requires_path(self):
        """Test asciidoc source validation requires 'path'."""
        config = self._make_config({"type": "asciidoc"})
        validator = ConfigValidator(config)
        with pytest.raises(ValueError, match="Missing required field 'path'"):
            validator.validate()

    def test_confluence_requires_url_or_path(self):
        """Test confluence requires 'url'/'base_url' or 'path'."""
        config = self._make_config({"type": "confluence"})
        validator = ConfigValidator(config)
        with pytest.raises(ValueError, match="Missing required field"):
            validator.validate()

    def test_confluence_accepts_base_url(self):
        """Test confluence passes with base_url + space_key."""
        config = self._make_config(
            {
                "type": "confluence",
                "base_url": "https://wiki.example.com",
                "space_key": "DEV",
            }
        )
        validator = ConfigValidator(config)
        assert validator.validate() is True

    def test_confluence_accepts_path(self):
        """Test confluence passes with export path."""
        config = self._make_config({"type": "confluence", "path": "/exports/wiki"})
        validator = ConfigValidator(config)
        assert validator.validate() is True

    def test_notion_requires_url_or_path(self):
        """Test notion requires 'url'/'database_id'/'page_id' or 'path'."""
        config = self._make_config({"type": "notion"})
        validator = ConfigValidator(config)
        with pytest.raises(ValueError, match="Missing required field"):
            validator.validate()

    def test_notion_accepts_page_id(self):
        """Test notion passes with page_id."""
        config = self._make_config({"type": "notion", "page_id": "abc123"})
        validator = ConfigValidator(config)
        assert validator.validate() is True

    def test_notion_accepts_database_id(self):
        """Test notion passes with database_id."""
        config = self._make_config({"type": "notion", "database_id": "db-456"})
        validator = ConfigValidator(config)
        assert validator.validate() is True

    def test_rss_requires_url_or_path(self):
        """Test rss source validation requires 'url' or 'path'."""
        config = self._make_config({"type": "rss"})
        validator = ConfigValidator(config)
        with pytest.raises(ValueError, match="Missing required field 'url' or 'path'"):
            validator.validate()

    def test_rss_accepts_url(self):
        """Test rss passes with url."""
        config = self._make_config({"type": "rss", "url": "https://blog.example.com/feed.xml"})
        validator = ConfigValidator(config)
        assert validator.validate() is True

    def test_manpage_requires_path_or_names(self):
        """Test manpage source validation requires 'path' or 'names'."""
        config = self._make_config({"type": "manpage"})
        validator = ConfigValidator(config)
        with pytest.raises(ValueError, match="Missing required field 'path' or 'names'"):
            validator.validate()

    def test_manpage_accepts_names(self):
        """Test manpage passes with 'names' list."""
        config = self._make_config({"type": "manpage", "names": ["git", "curl"]})
        validator = ConfigValidator(config)
        assert validator.validate() is True

    def test_chat_requires_path_or_token(self):
        """Test chat source validation requires 'path' or 'token'."""
        config = self._make_config({"type": "chat"})
        validator = ConfigValidator(config)
        with pytest.raises(ValueError, match="Missing required field 'path'.*or 'token'"):
            validator.validate()

    def test_chat_accepts_path(self):
        """Test chat passes with export path."""
        config = self._make_config({"type": "chat", "path": "/exports/slack"})
        validator = ConfigValidator(config)
        assert validator.validate() is True

    def test_chat_accepts_token_with_channel(self):
        """Test chat passes with API token + channel."""
        config = self._make_config(
            {
                "type": "chat",
                "token": "xoxb-fake",
                "channel": "#general",
            }
        )
        validator = ConfigValidator(config)
        assert validator.validate() is True


# ---------------------------------------------------------------------------
# 3. UnifiedSkillBuilder — generic merge system
# ---------------------------------------------------------------------------


class TestUnifiedSkillBuilderGenericMerge:
    """Test _generic_merge, _append_extra_sources, and _SOURCE_LABELS."""

    def _make_builder(self, tmp_path) -> UnifiedSkillBuilder:
        """Create a minimal builder instance for testing."""
        config = {
            "name": "test_project",
            "description": "A test project for merge testing",
            "sources": [
                {"type": "jupyter", "path": "nb.ipynb"},
                {"type": "rss", "url": "https://example.com/feed.rss"},
            ],
        }
        scraped_data: dict = {}
        builder = UnifiedSkillBuilder(
            config=config,
            scraped_data=scraped_data,
            cache_dir=str(tmp_path / "cache"),
        )
        # Override skill_dir to use tmp_path
        builder.skill_dir = str(tmp_path / "output" / "test_project")
        os.makedirs(builder.skill_dir, exist_ok=True)
        os.makedirs(os.path.join(builder.skill_dir, "references"), exist_ok=True)
        return builder

    def test_generic_merge_produces_valid_markdown(self, tmp_path):
        """Test _generic_merge with two source types produces markdown."""
        builder = self._make_builder(tmp_path)
        skill_mds = {
            "jupyter": "## When to Use\n\nFor data analysis.\n\n## Quick Reference\n\nImport pandas.",
            "rss": "## When to Use\n\nFor feed monitoring.\n\n## Feed Items\n\nLatest entries.",
        }
        result = builder._generic_merge(skill_mds)

        # Must be non-empty markdown
        assert len(result) > 100
        # Must contain the project title
        assert "Test Project" in result

    def test_generic_merge_includes_yaml_frontmatter(self, tmp_path):
        """Test _generic_merge includes YAML frontmatter."""
        builder = self._make_builder(tmp_path)
        skill_mds = {
            "html": "## Overview\n\nHTML content here.",
        }
        result = builder._generic_merge(skill_mds)

        assert result.startswith("---\n")
        assert "name: test-project" in result
        assert "description: A test project" in result

    def test_generic_merge_attributes_content_to_sources(self, tmp_path):
        """Test _generic_merge attributes content to correct source labels."""
        builder = self._make_builder(tmp_path)
        skill_mds = {
            "jupyter": "## Overview\n\nNotebook content.",
            "pptx": "## Overview\n\nSlide content.",
        }
        result = builder._generic_merge(skill_mds)

        # Check source labels appear
        assert "Jupyter Notebook" in result
        assert "PowerPoint Presentation" in result

    def test_generic_merge_single_source_section(self, tmp_path):
        """Test section unique to one source has 'From <Label>' attribution."""
        builder = self._make_builder(tmp_path)
        skill_mds = {
            "manpage": "## Synopsis\n\ngit [options]",
        }
        result = builder._generic_merge(skill_mds)

        assert "*From Man Page*" in result
        assert "## Synopsis" in result

    def test_generic_merge_multi_source_section(self, tmp_path):
        """Test section shared by multiple sources gets sub-headings per source."""
        builder = self._make_builder(tmp_path)
        skill_mds = {
            "asciidoc": "## Quick Reference\n\nAsciiDoc quick ref.",
            "html": "## Quick Reference\n\nHTML quick ref.",
        }
        result = builder._generic_merge(skill_mds)

        # Both sources should be attributed under the shared section
        assert "### From AsciiDoc Document" in result
        assert "### From HTML Document" in result

    def test_generic_merge_footer(self, tmp_path):
        """Test _generic_merge ends with the standard footer."""
        builder = self._make_builder(tmp_path)
        skill_mds = {
            "rss": "## Feeds\n\nSome feeds.",
        }
        result = builder._generic_merge(skill_mds)
        assert "Generated by Skill Seeker" in result

    def test_generic_merge_merged_from_line(self, tmp_path):
        """Test _generic_merge includes 'Merged from:' with correct labels."""
        builder = self._make_builder(tmp_path)
        skill_mds = {
            "confluence": "## Pages\n\nWiki pages.",
            "notion": "## Databases\n\nNotion DBs.",
        }
        result = builder._generic_merge(skill_mds)

        assert "*Merged from: Confluence Wiki, Notion Page*" in result

    def test_append_extra_sources_adds_sections(self, tmp_path):
        """Test _append_extra_sources adds new sections to base content."""
        builder = self._make_builder(tmp_path)
        base_content = "# Test\n\nIntro.\n\n## Main Section\n\nContent.\n\n---\n\n*Footer*\n"
        skill_mds = {
            "epub": "## Chapters\n\nChapter list.\n\n## Key Concepts\n\nConcept A.",
        }
        result = builder._append_extra_sources(base_content, skill_mds, {"epub"})

        # The extra source content should be inserted before the footer separator
        assert "EPUB E-book Content" in result
        assert "Chapters" in result
        assert "Key Concepts" in result
        # Original content should still be present
        assert "# Test" in result
        assert "## Main Section" in result

    def test_append_extra_sources_preserves_footer(self, tmp_path):
        """Test _append_extra_sources keeps the footer intact."""
        builder = self._make_builder(tmp_path)
        base_content = "# Test\n\n---\n\n*Footer*\n"
        skill_mds = {
            "chat": "## Messages\n\nChat history.",
        }
        result = builder._append_extra_sources(base_content, skill_mds, {"chat"})

        assert "*Footer*" in result

    def test_source_labels_has_all_17_types(self):
        """Test _SOURCE_LABELS has entries for all 17 source types."""
        expected = {
            "documentation",
            "github",
            "pdf",
            "word",
            "epub",
            "video",
            "local",
            "jupyter",
            "html",
            "openapi",
            "asciidoc",
            "pptx",
            "confluence",
            "notion",
            "rss",
            "manpage",
            "chat",
        }
        assert set(UnifiedSkillBuilder._SOURCE_LABELS.keys()) == expected

    def test_source_labels_values_are_nonempty_strings(self):
        """Test all _SOURCE_LABELS values are non-empty strings."""
        for key, label in UnifiedSkillBuilder._SOURCE_LABELS.items():
            assert isinstance(label, str), f"Label for '{key}' is not a string"
            assert len(label) > 0, f"Label for '{key}' is empty"


# ---------------------------------------------------------------------------
# 4. New source types accessible via 'create' command
# ---------------------------------------------------------------------------
# Individual scraper CLI commands (jupyter, html, etc.) were removed in the
# Grand Unification refactor.  All 17 source types are now accessed via
# `skill-seekers create`.  The routing is tested in TestCreateCommandRouting.


# ---------------------------------------------------------------------------
# 5. SourceDetector.validate_source — new types
# ---------------------------------------------------------------------------


class TestSourceDetectorValidation:
    """Test validate_source for new file-based source types."""

    def test_validation_passes_for_existing_jupyter(self, tmp_path):
        """Test validation passes for an existing .ipynb file."""
        nb = tmp_path / "test.ipynb"
        nb.write_text('{"cells": []}')

        info = SourceInfo(
            type="jupyter",
            parsed={"file_path": str(nb)},
            suggested_name="test",
            raw_input=str(nb),
        )
        # Should not raise
        SourceDetector.validate_source(info)

    def test_validation_raises_for_nonexistent_jupyter(self):
        """Test validation raises ValueError for non-existent file."""
        info = SourceInfo(
            type="jupyter",
            parsed={"file_path": "/nonexistent/notebook.ipynb"},
            suggested_name="notebook",
            raw_input="/nonexistent/notebook.ipynb",
        )
        with pytest.raises(ValueError, match="does not exist"):
            SourceDetector.validate_source(info)

    def test_validation_passes_for_existing_html(self, tmp_path):
        """Test validation passes for an existing .html file."""
        html = tmp_path / "page.html"
        html.write_text("<html></html>")

        info = SourceInfo(
            type="html",
            parsed={"file_path": str(html)},
            suggested_name="page",
            raw_input=str(html),
        )
        SourceDetector.validate_source(info)

    def test_validation_raises_for_nonexistent_pptx(self):
        """Test validation raises ValueError for non-existent pptx."""
        info = SourceInfo(
            type="pptx",
            parsed={"file_path": "/nonexistent/slides.pptx"},
            suggested_name="slides",
            raw_input="/nonexistent/slides.pptx",
        )
        with pytest.raises(ValueError, match="does not exist"):
            SourceDetector.validate_source(info)

    def test_validation_passes_for_existing_openapi(self, tmp_path):
        """Test validation passes for an existing OpenAPI spec file."""
        spec = tmp_path / "api.yaml"
        spec.write_text("openapi: '3.0.0'\n")

        info = SourceInfo(
            type="openapi",
            parsed={"file_path": str(spec)},
            suggested_name="api",
            raw_input=str(spec),
        )
        SourceDetector.validate_source(info)

    def test_validation_raises_for_nonexistent_asciidoc(self):
        """Test validation raises ValueError for non-existent asciidoc."""
        info = SourceInfo(
            type="asciidoc",
            parsed={"file_path": "/nonexistent/doc.adoc"},
            suggested_name="doc",
            raw_input="/nonexistent/doc.adoc",
        )
        with pytest.raises(ValueError, match="does not exist"):
            SourceDetector.validate_source(info)

    def test_validation_raises_for_nonexistent_manpage(self):
        """Test validation raises ValueError for non-existent manpage."""
        info = SourceInfo(
            type="manpage",
            parsed={"file_path": "/nonexistent/git.1"},
            suggested_name="git",
            raw_input="/nonexistent/git.1",
        )
        with pytest.raises(ValueError, match="does not exist"):
            SourceDetector.validate_source(info)

    def test_validation_passes_for_existing_manpage(self, tmp_path):
        """Test validation passes for an existing man page file."""
        man = tmp_path / "curl.1"
        man.write_text(".TH CURL 1\n")

        info = SourceInfo(
            type="manpage",
            parsed={"file_path": str(man)},
            suggested_name="curl",
            raw_input=str(man),
        )
        SourceDetector.validate_source(info)

    def test_rss_url_validation_no_file_check(self):
        """Test rss validation passes for URL-based source (no file check)."""
        info = SourceInfo(
            type="rss",
            parsed={"url": "https://example.com/feed.rss"},
            suggested_name="feed",
            raw_input="https://example.com/feed.rss",
        )
        # rss validation only checks file if file_path is present; URL should pass
        SourceDetector.validate_source(info)

    def test_rss_validation_raises_for_nonexistent_file(self):
        """Test rss validation raises for non-existent local file."""
        info = SourceInfo(
            type="rss",
            parsed={"file_path": "/nonexistent/feed.rss"},
            suggested_name="feed",
            raw_input="/nonexistent/feed.rss",
        )
        with pytest.raises(ValueError, match="does not exist"):
            SourceDetector.validate_source(info)

    def test_rss_validation_passes_for_existing_file(self, tmp_path):
        """Test rss validation passes for an existing .rss file."""
        rss = tmp_path / "feed.rss"
        rss.write_text("<rss></rss>")

        info = SourceInfo(
            type="rss",
            parsed={"file_path": str(rss)},
            suggested_name="feed",
            raw_input=str(rss),
        )
        SourceDetector.validate_source(info)

    def test_validation_passes_for_directory_types(self, tmp_path):
        """Test validation passes when source is a directory (e.g., html dir)."""
        html_dir = tmp_path / "pages"
        html_dir.mkdir()

        info = SourceInfo(
            type="html",
            parsed={"file_path": str(html_dir)},
            suggested_name="pages",
            raw_input=str(html_dir),
        )
        # The validator allows directories for these types (isfile or isdir)
        SourceDetector.validate_source(info)


# ---------------------------------------------------------------------------
# 6. CreateCommand._route_generic coverage
# ---------------------------------------------------------------------------


class TestCreateCommandRouting:
    """Test that CreateCommand uses get_converter for all source types."""

    NEW_SOURCE_TYPES = [
        "jupyter",
        "html",
        "openapi",
        "asciidoc",
        "pptx",
        "rss",
        "manpage",
        "confluence",
        "notion",
        "chat",
    ]

    def test_get_converter_handles_all_new_types(self):
        """Test get_converter returns a converter for each new source type."""
        from skill_seekers.cli.skill_converter import get_converter

        for source_type in self.NEW_SOURCE_TYPES:
            # get_converter should not raise for known types
            # (it may raise ImportError for missing optional deps, which is OK)
            try:
                converter_cls = get_converter(source_type, {"name": "test"})
                assert converter_cls is not None, f"get_converter returned None for '{source_type}'"
            except ImportError:
                # Optional dependency not installed - that's fine
                pass

    def test_route_to_scraper_uses_get_converter(self):
        """Test _route_to_scraper delegates to get_converter (not per-type branches)."""
        import inspect

        source = inspect.getsource(
            __import__(
                "skill_seekers.cli.create_command",
                fromlist=["CreateCommand"],
            ).CreateCommand._route_to_scraper
        )
        assert "get_converter" in source, (
            "_route_to_scraper should use get_converter for unified routing"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
