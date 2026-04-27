#!/usr/bin/env python3
"""
UniSkillConfig Validator

Validates uni_skill_config format that supports multiple sources:
- documentation (website scraping)
- github (repository scraping)
- pdf (PDF document scraping)
- local (local codebase analysis)
- word (Word .docx document scraping)
- video (video transcript/visual extraction)
- epub (EPUB e-book extraction)
- jupyter (Jupyter Notebook extraction)
- html (local HTML file extraction)
- openapi (OpenAPI/Swagger spec extraction)
- asciidoc (AsciiDoc document extraction)
- pptx (PowerPoint presentation extraction)
- confluence (Confluence wiki extraction)
- notion (Notion page extraction)
- rss (RSS/Atom feed extraction)
- manpage (man page extraction)
- chat (Slack/Discord chat export extraction)

Legacy config format support removed in v2.11.0.
All configs must use unified format with 'sources' array.
"""

import json
import logging
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UniSkillConfigValidator:
    """
    Validates uni_skill_config format (legacy support removed in v2.11.0).
    """

    # Valid source types
    VALID_SOURCE_TYPES = {
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

    # Valid merge modes
    VALID_MERGE_MODES = {
        "rule-based",
        "ai-enhanced",
        "claude-enhanced",
    }  # claude-enhanced kept as alias

    # Valid code analysis depth levels
    VALID_DEPTH_LEVELS = {"surface", "deep", "full"}

    # Valid AI modes for C3.x enhancement
    VALID_AI_MODES = {"auto", "api", "local", "none"}

    def __init__(self, config_or_path: dict[str, Any] | str):
        """
        Initialize validator with config dict or file path.

        Args:
            config_or_path: Either a config dict or path to config JSON file
        """
        if isinstance(config_or_path, dict):
            self.config_path = None
            self.config = config_or_path
        else:
            self.config_path = config_or_path
            self.config = self._load_config()
        self.is_unified = True  # Always unified format now

    def _load_config(self) -> dict[str, Any]:
        """Load JSON config file."""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError as e:
            raise ValueError(f"Config file not found: {self.config_path}") from e
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}") from e

    def validate(self) -> bool:
        """
        Validate uni_skill_config format.

        Returns:
            True if valid

        Raises:
            ValueError if invalid with detailed error message
        """
        # Check if legacy format (no sources array)
        if "sources" not in self.config:
            raise ValueError(
                "\n❌ LEGACY CONFIG FORMAT DETECTED\n\n"
                "   Legacy config format was removed in v2.11.0.\n"
                "   All configs must now use unified format with 'sources' array.\n\n"
                "   OLD FORMAT (removed):\n"
                "   {\n"
                '     "name": "example",\n'
                '     "base_url": "https://..."\n'
                "   }\n\n"
                "   NEW FORMAT (required):\n"
                "   {\n"
                '     "name": "example",\n'
                '     "description": "...",\n'
                '     "sources": [\n'
                "       {\n"
                '         "type": "documentation",\n'
                '         "base_url": "https://..."\n'
                "       }\n"
                "     ]\n"
                "   }\n\n"
                "   📖 See: https://skillseekersweb.com/docs/config-format\n"
            )

        return self._validate_unified()

    def _validate_unified(self) -> bool:
        """Validate uni_skill_config format."""
        logger.info("Validating uni_skill_config format...")

        # Required top-level fields
        if "name" not in self.config:
            raise ValueError("Missing required field: 'name'")

        if "description" not in self.config:
            raise ValueError("Missing required field: 'description'")

        if "sources" not in self.config:
            raise ValueError("Missing required field: 'sources'")

        # Validate sources array
        sources = self.config["sources"]

        if not isinstance(sources, list):
            raise ValueError("'sources' must be an array")

        if len(sources) == 0:
            raise ValueError("'sources' array cannot be empty")

        # Validate merge_mode (optional)
        merge_mode = self.config.get("merge_mode", "rule-based")
        if merge_mode not in self.VALID_MERGE_MODES:
            raise ValueError(
                f"Invalid merge_mode: '{merge_mode}'. Must be one of {self.VALID_MERGE_MODES}"
            )

        # Validate marketplace_targets (optional)
        marketplace_targets = self.config.get("marketplace_targets")
        if marketplace_targets is not None:
            if not isinstance(marketplace_targets, list):
                raise ValueError("'marketplace_targets' must be an array")
            for i, mt in enumerate(marketplace_targets):
                if not isinstance(mt, dict):
                    raise ValueError(f"marketplace_targets[{i}]: must be an object")
                if "marketplace" not in mt:
                    raise ValueError(
                        f"marketplace_targets[{i}]: missing required field 'marketplace'"
                    )
                if not isinstance(mt["marketplace"], str):
                    raise ValueError(f"marketplace_targets[{i}]: 'marketplace' must be a string")

        # Validate each source
        for i, source in enumerate(sources):
            self._validate_source(source, i)

        logger.info(f"✅ Unified config valid: {len(sources)} sources")
        return True

    def _validate_source(self, source: dict[str, Any], index: int):
        """Validate individual source configuration."""
        # Check source has 'type' field
        if "type" not in source:
            raise ValueError(f"Source {index}: Missing required field 'type'")

        source_type = source["type"]

        if source_type not in self.VALID_SOURCE_TYPES:
            raise ValueError(
                f"Source {index}: Invalid type '{source_type}'. Must be one of {self.VALID_SOURCE_TYPES}"
            )

        # Type-specific validation
        if source_type == "documentation":
            self._validate_documentation_source(source, index)
        elif source_type == "github":
            self._validate_github_source(source, index)
        elif source_type == "pdf":
            self._validate_pdf_source(source, index)
        elif source_type == "local":
            self._validate_local_source(source, index)
        elif source_type == "word":
            self._validate_word_source(source, index)
        elif source_type == "video":
            self._validate_video_source(source, index)
        elif source_type == "epub":
            self._validate_epub_source(source, index)
        elif source_type == "jupyter":
            self._validate_jupyter_source(source, index)
        elif source_type == "html":
            self._validate_html_source(source, index)
        elif source_type == "openapi":
            self._validate_openapi_source(source, index)
        elif source_type == "asciidoc":
            self._validate_asciidoc_source(source, index)
        elif source_type == "pptx":
            self._validate_pptx_source(source, index)
        elif source_type == "confluence":
            self._validate_confluence_source(source, index)
        elif source_type == "notion":
            self._validate_notion_source(source, index)
        elif source_type == "rss":
            self._validate_rss_source(source, index)
        elif source_type == "manpage":
            self._validate_manpage_source(source, index)
        elif source_type == "chat":
            self._validate_chat_source(source, index)

    def _validate_documentation_source(self, source: dict[str, Any], index: int):
        """Validate documentation source configuration."""
        if "base_url" not in source:
            raise ValueError(f"Source {index} (documentation): Missing required field 'base_url'")

        # Optional but recommended fields
        if "selectors" not in source:
            logger.warning(
                f"Source {index} (documentation): No 'selectors' specified, using defaults"
            )

        if "max_pages" in source and not isinstance(source["max_pages"], int):
            raise ValueError(f"Source {index} (documentation): 'max_pages' must be an integer")

    def _validate_github_source(self, source: dict[str, Any], index: int):
        """Validate GitHub source configuration."""
        if "repo" not in source:
            raise ValueError(f"Source {index} (github): Missing required field 'repo'")

        # Validate repo format (owner/repo)
        repo = source["repo"]
        if "/" not in repo:
            raise ValueError(
                f"Source {index} (github): Invalid repo format '{repo}'. Must be 'owner/repo' (e.g., 'facebook/react')"
            )

        # Validate code_analysis_depth if specified
        if "code_analysis_depth" in source:
            depth = source["code_analysis_depth"]
            if depth not in self.VALID_DEPTH_LEVELS:
                raise ValueError(
                    f"Source {index} (github): Invalid code_analysis_depth '{depth}'. "
                    f"Must be one of {self.VALID_DEPTH_LEVELS}"
                )

        # Validate max_issues if specified
        if "max_issues" in source and not isinstance(source["max_issues"], int):
            raise ValueError(f"Source {index} (github): 'max_issues' must be an integer")

        # Validate issue_since if specified (ISO8601 date string)
        if "issue_since" in source:
            issue_since = source["issue_since"]
            if not isinstance(issue_since, str):
                raise ValueError(
                    f"Source {index} (github): 'issue_since' must be an ISO8601 date string"
                )
            from datetime import datetime

            since_str = issue_since[:-1] + "+00:00" if issue_since.endswith("Z") else issue_since
            try:
                datetime.fromisoformat(since_str)
            except ValueError as err:
                raise ValueError(
                    f"Source {index} (github): 'issue_since' is not a valid ISO8601 date: '{issue_since}'"
                ) from err

        # Validate issue_labels if specified
        if "issue_labels" in source:
            issue_labels = source["issue_labels"]
            if not isinstance(issue_labels, list) or not all(
                isinstance(label, str) for label in issue_labels
            ):
                raise ValueError(
                    f"Source {index} (github): 'issue_labels' must be a list of strings"
                )

        # Validate issue_state if specified
        if "issue_state" in source:
            valid_issue_states = {"open", "closed", "all"}
            if source["issue_state"] not in valid_issue_states:
                raise ValueError(
                    f"Source {index} (github): Invalid issue_state '{source['issue_state']}'. "
                    f"Must be one of {valid_issue_states}"
                )

        # Validate enable_codebase_analysis if specified (C3.5)
        if "enable_codebase_analysis" in source and not isinstance(
            source["enable_codebase_analysis"], bool
        ):
            raise ValueError(
                f"Source {index} (github): 'enable_codebase_analysis' must be a boolean"
            )

        # Validate ai_mode if specified (C3.5)
        if "ai_mode" in source:
            ai_mode = source["ai_mode"]
            if ai_mode not in self.VALID_AI_MODES:
                raise ValueError(
                    f"Source {index} (github): Invalid ai_mode '{ai_mode}'. Must be one of {self.VALID_AI_MODES}"
                )

    def _validate_pdf_source(self, source: dict[str, Any], index: int):
        """Validate PDF source configuration."""
        if "path" not in source:
            raise ValueError(f"Source {index} (pdf): Missing required field 'path'")

        # Check if file exists
        pdf_path = source["path"]
        if not Path(pdf_path).exists():
            logger.warning(f"Source {index} (pdf): File not found: {pdf_path}")

    def _validate_local_source(self, source: dict[str, Any], index: int):
        """Validate local codebase source configuration."""
        if "path" not in source:
            raise ValueError(f"Source {index} (local): Missing required field 'path'")

        # Check if directory exists
        local_path = source["path"]
        if not Path(local_path).exists():
            logger.warning(f"Source {index} (local): Directory not found: {local_path}")
        elif not Path(local_path).is_dir():
            raise ValueError(f"Source {index} (local): Path is not a directory: {local_path}")

        # Validate analysis_depth if provided
        if "analysis_depth" in source:
            depth = source["analysis_depth"]
            if depth not in self.VALID_DEPTH_LEVELS:
                raise ValueError(
                    f"Source {index} (local): Invalid analysis_depth '{depth}'. Must be one of {self.VALID_DEPTH_LEVELS}"
                )

        # Validate ai_mode if provided
        if "ai_mode" in source:
            ai_mode = source["ai_mode"]
            if ai_mode not in self.VALID_AI_MODES:
                raise ValueError(
                    f"Source {index} (local): Invalid ai_mode '{ai_mode}'. Must be one of {self.VALID_AI_MODES}"
                )

    def _validate_word_source(self, source: dict[str, Any], index: int):
        """Validate Word document (.docx) source configuration."""
        if "path" not in source:
            raise ValueError(f"Source {index} (word): Missing required field 'path'")
        word_path = source["path"]
        if not Path(word_path).exists():
            logger.warning(f"Source {index} (word): File not found: {word_path}")

    def _validate_video_source(self, source: dict[str, Any], index: int):
        """Validate video source configuration."""
        has_url = "url" in source
        has_path = "path" in source
        has_playlist = "playlist" in source
        if not has_url and not has_path and not has_playlist:
            raise ValueError(
                f"Source {index} (video): Missing required field 'url', 'path', or 'playlist'"
            )

    def _validate_epub_source(self, source: dict[str, Any], index: int):
        """Validate EPUB source configuration."""
        if "path" not in source:
            raise ValueError(f"Source {index} (epub): Missing required field 'path'")
        epub_path = source["path"]
        if not Path(epub_path).exists():
            logger.warning(f"Source {index} (epub): File not found: {epub_path}")

    def _validate_jupyter_source(self, source: dict[str, Any], index: int):
        """Validate Jupyter Notebook source configuration."""
        if "path" not in source:
            raise ValueError(f"Source {index} (jupyter): Missing required field 'path'")
        nb_path = source["path"]
        if not Path(nb_path).exists():
            logger.warning(f"Source {index} (jupyter): Path not found: {nb_path}")

    def _validate_html_source(self, source: dict[str, Any], index: int):
        """Validate local HTML source configuration."""
        if "path" not in source:
            raise ValueError(f"Source {index} (html): Missing required field 'path'")
        html_path = source["path"]
        if not Path(html_path).exists():
            logger.warning(f"Source {index} (html): Path not found: {html_path}")

    def _validate_openapi_source(self, source: dict[str, Any], index: int):
        """Validate OpenAPI/Swagger source configuration."""
        if "path" not in source and "url" not in source:
            raise ValueError(f"Source {index} (openapi): Missing required field 'path' or 'url'")
        if "path" in source and not Path(source["path"]).exists():
            logger.warning(f"Source {index} (openapi): File not found: {source['path']}")

    def _validate_asciidoc_source(self, source: dict[str, Any], index: int):
        """Validate AsciiDoc source configuration."""
        if "path" not in source:
            raise ValueError(f"Source {index} (asciidoc): Missing required field 'path'")
        adoc_path = source["path"]
        if not Path(adoc_path).exists():
            logger.warning(f"Source {index} (asciidoc): Path not found: {adoc_path}")

    def _validate_pptx_source(self, source: dict[str, Any], index: int):
        """Validate PowerPoint source configuration."""
        if "path" not in source:
            raise ValueError(f"Source {index} (pptx): Missing required field 'path'")
        pptx_path = source["path"]
        if not Path(pptx_path).exists():
            logger.warning(f"Source {index} (pptx): File not found: {pptx_path}")

    def _validate_confluence_source(self, source: dict[str, Any], index: int):
        """Validate Confluence source configuration."""
        has_url = "url" in source or "base_url" in source
        has_path = "path" in source
        if not has_url and not has_path:
            raise ValueError(
                f"Source {index} (confluence): Missing required field 'url'/'base_url' "
                f"(for API) or 'path' (for export)"
            )
        if has_url and "space_key" not in source and "path" not in source:
            logger.warning(f"Source {index} (confluence): No 'space_key' specified for API mode")

    def _validate_notion_source(self, source: dict[str, Any], index: int):
        """Validate Notion source configuration."""
        has_url = "url" in source or "database_id" in source or "page_id" in source
        has_path = "path" in source
        if not has_url and not has_path:
            raise ValueError(
                f"Source {index} (notion): Missing required field 'url'/'database_id'/'page_id' "
                f"(for API) or 'path' (for export)"
            )

    def _validate_rss_source(self, source: dict[str, Any], index: int):
        """Validate RSS/Atom feed source configuration."""
        if "url" not in source and "path" not in source:
            raise ValueError(f"Source {index} (rss): Missing required field 'url' or 'path'")

    def _validate_manpage_source(self, source: dict[str, Any], index: int):
        """Validate man page source configuration."""
        if "path" not in source and "names" not in source:
            raise ValueError(f"Source {index} (manpage): Missing required field 'path' or 'names'")
        if "path" in source and not Path(source["path"]).exists():
            logger.warning(f"Source {index} (manpage): Path not found: {source['path']}")

    def _validate_chat_source(self, source: dict[str, Any], index: int):
        """Validate Slack/Discord chat source configuration."""
        has_path = "path" in source
        has_api = "token" in source or "webhook_url" in source
        has_channel = "channel" in source or "channel_id" in source
        if not has_path and not has_api:
            raise ValueError(
                f"Source {index} (chat): Missing required field 'path' (for export) "
                f"or 'token' (for API)"
            )
        if has_api and not has_channel:
            logger.warning(
                f"Source {index} (chat): No 'channel' or 'channel_id' specified for API mode"
            )

    def get_sources_by_type(self, source_type: str) -> list[dict[str, Any]]:
        """
        Get all sources of a specific type.

        Args:
            source_type: Any valid source type string

        Returns:
            List of sources matching the type
        """
        sources = self.config["sources"]
        return [s for s in sources if s.get("type") == source_type]

    def has_multiple_sources(self) -> bool:
        """Check if config has multiple sources (requires merging)."""
        return len(self.config["sources"]) > 1

    def needs_api_merge(self) -> bool:
        """
        Check if config needs API merging.

        Returns True if both documentation and github sources exist
        with API extraction enabled.
        """
        if not self.has_multiple_sources():
            return False

        has_docs_api = any(
            s.get("type") == "documentation" and s.get("extract_api", True)
            for s in self.config["sources"]
        )

        has_github_code = any(
            s.get("type") == "github" and s.get("include_code", True)
            for s in self.config["sources"]
        )

        return has_docs_api and has_github_code


# Backward-compat alias
ConfigValidator = UniSkillConfigValidator


def validate_config(config_path: str) -> UniSkillConfigValidator:
    """
    Validate config file and return validator instance.

    Args:
        config_path: Path to config JSON file

    Returns:
        UniSkillConfigValidator instance

    Raises:
        ValueError if config is invalid
    """
    validator = UniSkillConfigValidator(config_path)
    validator.validate()
    return validator


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python config_validator.py <config.json>")
        sys.exit(1)

    config_file = sys.argv[1]

    try:
        validator = validate_config(config_file)

        print("\n✅ Config valid!")
        print(f"   Name: {validator.config.get('name')}")

        sources = validator.config["sources"]
        print(f"   Sources: {len(sources)}")
        for i, source in enumerate(sources):
            print(f"     {i + 1}. {source['type']}")

        if validator.needs_api_merge():
            merge_mode = validator.config.get("merge_mode", "rule-based")
            print(f"   ⚠️  API merge required (mode: {merge_mode})")

    except ValueError as e:
        print(f"\n❌ Config invalid: {e}")
        sys.exit(1)
