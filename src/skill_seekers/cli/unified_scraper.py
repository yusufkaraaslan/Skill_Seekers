#!/usr/bin/env python3
"""
Unified Multi-Source Scraper

Orchestrates scraping from multiple sources (documentation, GitHub, PDF),
detects conflicts, merges intelligently, and builds unified skills.

This is the main entry point for unified config workflow.

Usage:
    skill-seekers unified --config configs/godot_unified.json
    skill-seekers unified --config configs/react_unified.json --merge-mode ai-enhanced
"""

import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

# Import validators and scrapers
try:
    from skill_seekers.cli.agent_client import get_default_timeout
    from skill_seekers.cli.config_validator import validate_config
    from skill_seekers.cli.conflict_detector import ConflictDetector
    from skill_seekers.cli.defaults import DEFAULTS
    from skill_seekers.cli.merge_sources import AIEnhancedMerger, RuleBasedMerger
    from skill_seekers.cli.skill_converter import SkillConverter
    from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

logger = logging.getLogger(__name__)


class UnifiedScraper(SkillConverter):
    """
    Orchestrates multi-source scraping and merging.

    Main workflow:
    1. Load and validate unified config
    2. Scrape all sources (docs, GitHub, PDF)
    3. Detect conflicts between sources
    4. Merge intelligently (rule-based or AI-enhanced)
    5. Build unified skill
    """

    SOURCE_TYPE = "config"

    # Source type → handler method name. Resolved via getattr at dispatch time
    # so instance-level monkeypatching (used by tests) still works.
    SOURCE_DISPATCH: dict[str, str] = {
        "documentation": "_scrape_documentation",
        "github": "_scrape_github",
        "pdf": "_scrape_pdf",
        "word": "_scrape_word",
        "video": "_scrape_video",
        "local": "_scrape_local",
        "epub": "_scrape_epub",
        "jupyter": "_scrape_jupyter",
        "html": "_scrape_html",
        "openapi": "_scrape_openapi",
        "asciidoc": "_scrape_asciidoc",
        "pptx": "_scrape_pptx",
        "confluence": "_scrape_confluence",
        "notion": "_scrape_notion",
        "rss": "_scrape_rss",
        "manpage": "_scrape_manpage",
        "chat": "_scrape_chat",
    }

    def __init__(
        self,
        config: dict[str, Any] | str,
        merge_mode: str | None = None,
        output_dir: str | None = None,
        dry_run: bool = False,
    ):
        """
        Initialize unified scraper.

        Args:
            config: Either the factory-shaped dict used by get_converter()
                ({"config_path": ..., "merge_mode": ..., "output_dir": ...,
                "dry_run": ...} — only "config_path" is required), or the
                legacy positional value: a path to the unified config JSON
                (or the already-loaded unified config dict itself).
            merge_mode: Override config merge_mode ('rule-based' or 'claude-enhanced')
            output_dir: Override output directory (CLI --output); wins over the
                config file's "output_dir"
            dry_run: Preview the sources that would be scraped without scraping,
                writing output, or creating directories
        """
        if isinstance(config, dict) and "config_path" in config:
            # Factory-shaped dict (get_converter("config", {...})). Explicit
            # keyword arguments win over the dict's values.
            merge_mode = merge_mode or config.get("merge_mode")
            output_dir = output_dir or config.get("output_dir")
            dry_run = dry_run or bool(config.get("dry_run"))
            config_path = config["config_path"]
        else:
            # Legacy positional: a config path str (or raw unified config dict).
            config_path = config
        super().__init__({"name": "unified", "config_path": config_path})
        self.config_path = config_path
        self.dry_run = dry_run

        # Validate and load config
        logger.info(f"Loading config: {config_path}")
        self.validator = validate_config(config_path)
        self.config = self.validator.config

        # Determine merge mode (normalize claude-enhanced → ai-enhanced for backward compat)
        raw_mode = merge_mode or self.config.get("merge_mode", "rule-based")
        self.merge_mode = "ai-enhanced" if raw_mode == "claude-enhanced" else raw_mode
        logger.info(f"Merge mode: {self.merge_mode}")

        # Storage for scraped data - use lists to support multiple sources of same type
        self.scraped_data = {
            "documentation": [],  # List of doc sources
            "github": [],  # List of github sources
            "pdf": [],  # List of pdf sources
            "word": [],  # List of word sources
            "video": [],  # List of video sources
            "local": [],  # List of local sources (docs or code)
            "epub": [],  # List of epub sources
            "jupyter": [],  # List of Jupyter notebook sources
            "html": [],  # List of local HTML sources
            "openapi": [],  # List of OpenAPI/Swagger spec sources
            "asciidoc": [],  # List of AsciiDoc sources
            "pptx": [],  # List of PowerPoint sources
            "confluence": [],  # List of Confluence wiki sources
            "notion": [],  # List of Notion page sources
            "rss": [],  # List of RSS/Atom feed sources
            "manpage": [],  # List of man page sources
            "chat": [],  # List of Slack/Discord chat sources
        }

        # Track source index for unique naming (multi-source support)
        self._source_counters = {
            "documentation": 0,
            "github": 0,
            "pdf": 0,
            "word": 0,
            "video": 0,
            "local": 0,
            "epub": 0,
            "jupyter": 0,
            "html": 0,
            "openapi": 0,
            "asciidoc": 0,
            "pptx": 0,
            "confluence": 0,
            "notion": 0,
            "rss": 0,
            "manpage": 0,
            "chat": 0,
        }

        # Output paths - cleaner organization
        self.name = self.config["name"]
        # Honor --output: explicit CLI value wins over config["output_dir"].
        self.output_dir = self.resolve_skill_dir(
            {"output_dir": output_dir or self.config.get("output_dir")}, self.name
        )
        # Write the resolved value back so build-phase consumers of the raw
        # config (UnifiedSkillBuilder re-resolves skill_dir from
        # config["output_dir"]) honor the CLI --output override instead of
        # falling back to the config file's value / output/<name>.
        self.config["output_dir"] = self.output_dir

        # Use hidden cache directory for intermediate files
        self.cache_dir = f".skillseeker-cache/{self.name}"
        self.sources_dir = f"{self.cache_dir}/sources"
        self.data_dir = f"{self.cache_dir}/data"
        self.repos_dir = f"{self.cache_dir}/repos"
        self.logs_dir = f"{self.cache_dir}/logs"

        # A dry run must not touch the filesystem.
        if not self.dry_run:
            # Create directories
            os.makedirs(self.output_dir, exist_ok=True)
            os.makedirs(self.sources_dir, exist_ok=True)
            os.makedirs(self.data_dir, exist_ok=True)
            os.makedirs(self.repos_dir, exist_ok=True)
            os.makedirs(self.logs_dir, exist_ok=True)

            # Setup file logging
            self._setup_logging()

    def _setup_logging(self):
        """Setup file logging for this scraping session."""
        from datetime import datetime

        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = f"{self.logs_dir}/unified_{timestamp}.log"

        # Add file handler to root logger
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)

        # Add to root logger
        logging.getLogger().addHandler(file_handler)

        logger.info(f"📝 Logging to: {log_file}")
        logger.info(f"🗂️  Cache directory: {self.cache_dir}")

    @staticmethod
    def _enrich_docs_json(docs_json: dict, data_file_path: str) -> dict:
        """Enrich docs summary with page content from individual page files.

        summary.json only has {title, url} per page; full content lives in pages/*.json.
        ConflictDetector needs content to extract APIs, so we load page files and convert
        to the dict format {url: page_data} that the detector's dict branch understands.
        """
        pages = docs_json.get("pages", [])
        if not isinstance(pages, list) or not pages or "content" in pages[0]:
            return docs_json

        pages_dir = os.path.join(os.path.dirname(data_file_path), "pages")
        if not os.path.isdir(pages_dir):
            return docs_json

        enriched_pages = {}
        for page_file in os.listdir(pages_dir):
            if page_file.endswith(".json"):
                try:
                    with open(os.path.join(pages_dir, page_file), encoding="utf-8") as pf:
                        page_data = json.load(pf)
                    url = page_data.get("url", "")
                    if url:
                        enriched_pages[url] = page_data
                except (json.JSONDecodeError, OSError):
                    continue

        if enriched_pages:
            docs_json = {**docs_json, "pages": enriched_pages}
            logger.info(
                f"Enriched docs data with {len(enriched_pages)} page files for API extraction"
            )

        return docs_json

    @staticmethod
    def _cache_slug(value: Any, fallback: str) -> str:
        """Create a stable path-safe slug for cache directory names."""
        raw = str(value or fallback).strip().lower()
        slug = "".join(ch if ch.isalnum() else "_" for ch in raw).strip("_")
        while "__" in slug:
            slug = slug.replace("__", "_")
        return slug[:80] or fallback

    def _documentation_source_name(self, idx: int, source: dict[str, Any]) -> str:
        """Return the cache/source name for a documentation source."""
        docs_count = sum(
            1 for item in self.config.get("sources", []) if item["type"] == "documentation"
        )
        if docs_count <= 1:
            return f"{self.name}_docs"

        slug = self._cache_slug(source.get("name") or source.get("base_url"), f"source_{idx}")
        return f"{self.name}_docs_{idx}_{slug}"

    def scrape_all_sources(self):
        """
        Scrape all configured sources.

        Routes to appropriate scraper based on source type.
        """
        logger.info("=" * 60)
        logger.info("PHASE 1: Scraping all sources")
        logger.info("=" * 60)

        sources = self.config.get("sources", [])

        for i, source in enumerate(sources):
            source_type = source["type"]
            logger.info(f"\n[{i + 1}/{len(sources)}] Scraping {source_type} source...")

            try:
                handler_name = self.SOURCE_DISPATCH.get(source_type)
                if handler_name is not None:
                    getattr(self, handler_name)(source)
                else:
                    logger.warning(f"Unknown source type: {source_type}")
            except Exception as e:
                logger.error(f"Error scraping {source_type}: {e}")
                logger.info("Continuing with other sources...")

        # Count items actually scraped, not the number of bucket types (always
        # ~17). Returns the total so run() can detect a total failure.
        scraped_count = sum(len(v) for v in self.scraped_data.values())
        logger.info(f"\n✅ Scraped {scraped_count} source item(s) successfully")
        return scraped_count

    # Bespoke (not routed through _scrape_with_converter): documentation uses the
    # function-based scrape_documentation() entry point with an ExecutionContext
    # override and a return-code contract (non-zero → log + abort this source),
    # not the converter-instance extract()/build_skill() flow.
    def _scrape_documentation(self, source: dict[str, Any]):
        """Scrape documentation website."""
        idx = self._source_counters["documentation"]
        self._source_counters["documentation"] += 1
        source_name = self._documentation_source_name(idx, source)

        # Create temporary config for doc scraper in unified format
        # (doc_scraper's ConfigValidator requires "sources" key)
        doc_source = {
            "type": "documentation",
            "base_url": source["base_url"],
            "display_name": self.name,
            "description": source.get(
                "description", self.config.get("description", f"Documentation for {self.name}")
            ),
            "selectors": source.get("selectors", {}),
            "url_patterns": source.get("url_patterns", {}),
            "categories": source.get("categories", {}),
            "rate_limit": source.get("rate_limit", DEFAULTS["scraping"]["rate_limit"]),
            "max_pages": source.get("max_pages", DEFAULTS["scraping"]["max_pages"]),
        }

        if "version" in source or self.config.get("version"):
            doc_source["version"] = source.get("version", self.config.get("version", ""))

        if "doc_version" in source or self.config.get("doc_version"):
            doc_source["doc_version"] = source.get(
                "doc_version", self.config.get("doc_version", "")
            )

        # Pass through llms.txt settings (so unified configs behave the same as doc_scraper configs)
        if "llms_txt_url" in source:
            doc_source["llms_txt_url"] = source["llms_txt_url"]

        if "skip_llms_txt" in source:
            doc_source["skip_llms_txt"] = source["skip_llms_txt"]

        # Optional: support overriding start URLs
        if "start_urls" in source:
            doc_source["start_urls"] = source["start_urls"]

        # Pass through browser rendering settings
        if source.get("browser"):
            doc_source["browser"] = True
        if "browser_wait_until" in source:
            doc_source["browser_wait_until"] = source["browser_wait_until"]
        if "browser_extra_wait" in source:
            doc_source["browser_extra_wait"] = source["browser_extra_wait"]

        doc_config = {
            "name": source_name,
            "display_name": self.name,
            "description": source.get(
                "description", self.config.get("description", f"Documentation for {self.name}")
            ),
            "base_url": source["base_url"],
            "browser": source.get("browser", DEFAULTS["scraping"]["browser"]),
            "browser_wait_until": source.get(
                "browser_wait_until", DEFAULTS["scraping"]["browser_wait_until"]
            ),
            "browser_extra_wait": source.get(
                "browser_extra_wait", DEFAULTS["scraping"]["browser_extra_wait"]
            ),
            "sources": [doc_source],
        }

        if "version" in source or self.config.get("version"):
            doc_config["version"] = source.get("version", self.config.get("version", ""))

        if "doc_version" in source or self.config.get("doc_version"):
            doc_config["doc_version"] = source.get(
                "doc_version", self.config.get("doc_version", "")
            )

        # Run doc_scraper directly (no subprocess needed with ExecutionContext)
        logger.info(f"Scraping documentation from {source['base_url']}")

        # Support "browser": true in source config for JavaScript SPA sites
        if source.get("browser", False):
            doc_config["browser"] = True
            logger.info("  🌐 Browser mode enabled (JavaScript rendering via Playwright)")

        # Write the sub-skill directly into the cache (no output/ staging, no move).
        # Clean any stale copy first so re-runs start fresh.
        docs_skill_dir = os.path.join(self.sources_dir, doc_config["name"])
        for stale in (docs_skill_dir, f"{docs_skill_dir}_data"):
            if os.path.exists(stale):
                shutil.rmtree(stale)
        doc_config["output_dir"] = docs_skill_dir

        # Import and call directly
        try:
            from skill_seekers.cli.doc_scraper import scrape_documentation
            from skill_seekers.cli.execution_context import ExecutionContext

            # Create child context with doc-specific overrides
            doc_ctx = ExecutionContext.get().override(
                output__name=doc_config["name"],
                scraping__max_pages=source.get("max_pages", DEFAULTS["scraping"]["max_pages"]),
            )

            with doc_ctx:
                result = scrape_documentation(
                    config=doc_config,
                    ctx=ExecutionContext.get(),
                )

            if result != 0:
                logger.error(f"Documentation scraping failed with return code {result}")
                return

        except Exception as e:
            logger.error(f"Documentation scraping failed: {e}")
            import traceback

            logger.debug(f"Traceback: {traceback.format_exc()}")
            return

        # Load scraped data — the sub-converter wrote straight into the cache.
        docs_data_file = f"{docs_skill_dir}_data/summary.json"

        if os.path.exists(docs_data_file):
            with open(docs_data_file, encoding="utf-8") as f:
                summary = json.load(f)

            # Append to documentation list (multi-source support)
            self.scraped_data["documentation"].append(
                {
                    "source_id": doc_config["name"],
                    "base_url": source["base_url"],
                    "pages": summary.get("pages", []),
                    "total_pages": summary.get("total_pages", 0),
                    "data_file": docs_data_file,
                    "refs_dir": os.path.join(docs_skill_dir, "references"),
                }
            )

            logger.info(f"✅ Documentation: {summary.get('total_pages', 0)} pages scraped")
        else:
            logger.warning("Documentation data file not found")

    def _clone_github_repo(self, repo_name: str, idx: int = 0) -> str | None:
        """
        Clone GitHub repository to cache directory for C3.x analysis.
        Reuses existing clone if already present.

        Args:
            repo_name: GitHub repo in format "owner/repo"
            idx: Source index for unique naming when multiple repos

        Returns:
            Path to cloned repo, or None if clone failed
        """
        # Clone to cache repos folder for future reuse
        repo_dir_name = f"{idx}_{repo_name.replace('/', '_')}"  # e.g., 0_encode_httpx
        clone_path = os.path.join(self.repos_dir, repo_dir_name)

        # Check if already cloned
        if os.path.exists(clone_path) and os.path.isdir(os.path.join(clone_path, ".git")):
            logger.info(f"♻️  Found existing repository clone: {clone_path}")
            logger.info("   Reusing for C3.x analysis (skip re-cloning)")
            return clone_path

        # repos_dir already created in __init__

        # Clone repo (full clone, not shallow - for complete analysis)
        repo_url = f"https://github.com/{repo_name}.git"
        logger.info(f"🔄 Cloning repository for C3.x analysis: {repo_url}")
        logger.info(f"   → {clone_path}")
        logger.info("   💾 Clone will be saved for future reuse")

        try:
            result = subprocess.run(
                ["git", "clone", repo_url, clone_path],
                capture_output=True,
                text=True,
                timeout=get_default_timeout(),  # default 45 min, configurable via SKILL_SEEKER_ENHANCE_TIMEOUT
            )

            if result.returncode == 0:
                logger.info("✅ Repository cloned successfully")
                logger.info(f"   📁 Saved to: {clone_path}")
                return clone_path
            else:
                logger.error(f"❌ Git clone failed: {result.stderr}")
                # Clean up failed clone
                if os.path.exists(clone_path):
                    shutil.rmtree(clone_path)
                return None

        except subprocess.TimeoutExpired:
            logger.error("❌ Git clone timed out after 10 minutes")
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path)
            return None
        except Exception as e:
            logger.error(f"❌ Git clone failed: {e}")
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path)
            return None

    # Bespoke (not routed through _scrape_with_converter): github needs repo
    # cloning, optional C3.x codebase analysis, and a dual-write of the scraped
    # data (unified cache file + the converter's own *_github_data.json) before
    # a separate GitHubToSkillConverter builds the standalone skill.
    def _scrape_github(self, source: dict[str, Any]):
        """Scrape GitHub repository."""
        try:
            from skill_seekers.cli.github_scraper import GitHubScraper
        except ImportError:
            logger.error("github_scraper.py not found")
            return

        # Multi-source support: Get unique index for this GitHub source
        idx = self._source_counters["github"]
        self._source_counters["github"] += 1

        # Extract repo identifier for unique naming
        repo = source["repo"]
        repo_id = repo.replace("/", "_")

        # Check if we need to clone for C3.x analysis
        enable_codebase_analysis = source.get("enable_codebase_analysis", True)
        local_repo_path = source.get("local_repo_path")
        cloned_repo_path = None

        # Auto-clone if C3.x analysis is enabled but no local path provided
        if enable_codebase_analysis and not local_repo_path:
            logger.info("🔬 C3.x codebase analysis enabled - cloning repository...")
            cloned_repo_path = self._clone_github_repo(repo, idx=idx)
            if cloned_repo_path:
                local_repo_path = cloned_repo_path
                logger.info(f"✅ Using cloned repo for C3.x analysis: {local_repo_path}")
            else:
                logger.warning("⚠️  Failed to clone repo - C3.x analysis will be skipped")
                enable_codebase_analysis = False

        # Create config for GitHub scraper
        github_config = {
            "repo": repo,
            "name": f"{self.name}_github_{idx}_{repo_id}",
            "github_token": source.get("github_token"),
            "include_issues": source.get("include_issues", True),
            "max_issues": source.get("max_issues", 100),
            "include_changelog": source.get("include_changelog", True),
            "include_releases": source.get("include_releases", True),
            "include_code": source.get("include_code", True),
            "code_analysis_depth": source.get("code_analysis_depth", "surface"),
            "file_patterns": source.get("file_patterns", []),
            "language": source.get("language", ""),
            "local_repo_path": local_repo_path,  # Use cloned path if available
        }

        # Pass directory exclusions if specified (optional)
        if "exclude_dirs" in source:
            github_config["exclude_dirs"] = source["exclude_dirs"]
        if "exclude_dirs_additional" in source:
            github_config["exclude_dirs_additional"] = source["exclude_dirs_additional"]

        # Write the GitHub sub-skill + its data file straight into the cache
        # (no output/ staging, no move). Clean any stale copy first.
        github_skill_dir = os.path.join(self.sources_dir, github_config["name"])
        github_converter_data = f"{github_skill_dir}_github_data.json"
        if os.path.isdir(github_skill_dir):
            shutil.rmtree(github_skill_dir)
        if os.path.exists(github_converter_data):
            os.remove(github_converter_data)
        github_config["output_dir"] = github_skill_dir

        # Scrape
        logger.info(f"Scraping GitHub repository: {source['repo']}")
        scraper = GitHubScraper(github_config)
        github_data = scraper.scrape()

        # Run C3.x codebase analysis if enabled and local_repo_path available
        if enable_codebase_analysis and local_repo_path:
            logger.info("🔬 Running C3.x codebase analysis...")
            try:
                c3_data = self._run_c3_analysis(local_repo_path, source)
                if c3_data:
                    github_data["c3_analysis"] = c3_data
                    logger.info("✅ C3.x analysis complete")
                else:
                    logger.warning("⚠️  C3.x analysis returned no data")
            except Exception as e:
                logger.warning(f"⚠️  C3.x analysis failed: {e}")
                import traceback

                logger.debug(f"Traceback: {traceback.format_exc()}")
                # Continue without C3.x data - graceful degradation

        # Note: We keep the cloned repo in output/ for future reuse
        if cloned_repo_path:
            logger.info(f"📁 Repository clone saved for future use: {cloned_repo_path}")

        # Save data to unified location with unique filename
        github_data_file = os.path.join(self.data_dir, f"github_data_{idx}_{repo_id}.json")
        with open(github_data_file, "w", encoding="utf-8") as f:
            json.dump(github_data, f, indent=2, ensure_ascii=False)

        # ALSO save to the location GitHubToSkillConverter expects (its data_file
        # is "{skill_dir}_github_data.json"), now written straight into the cache.
        with open(github_converter_data, "w", encoding="utf-8") as f:
            json.dump(github_data, f, indent=2, ensure_ascii=False)

        # Append to list instead of overwriting (multi-source support)
        self.scraped_data["github"].append(
            {
                "repo": repo,
                "repo_id": repo_id,
                "idx": idx,
                "data": github_data,
                "data_file": github_data_file,
            }
        )

        # Build standalone SKILL.md for synthesis using GitHubToSkillConverter.
        # github_config["output_dir"] points into the cache, so the converter
        # writes its skill there directly (no output/ staging, no move).
        try:
            from skill_seekers.cli.github_scraper import GitHubToSkillConverter

            converter = GitHubToSkillConverter(config=github_config)
            converter.build_skill()
            logger.info("✅ GitHub: Standalone SKILL.md created")
        except Exception as e:
            logger.warning(f"⚠️  Failed to build standalone GitHub SKILL.md: {e}")

        logger.info("✅ GitHub: Repository scraped successfully")

    def _scrape_with_converter(
        self,
        *,
        bucket: str,
        converter_type: str,
        config: dict[str, Any],
        record: dict[str, Any],
        cache_stem: str,
        label: str,
        fail_label: str | None = None,
        summary_key: str,
        summary_noun: str,
    ) -> None:
        """Shared engine for single-file/source converter types.

        Runs the mechanically identical scrape flow used by the 13 simple
        source types (pdf, word, epub, jupyter, html, openapi, asciidoc,
        pptx, confluence, notion, rss, manpage, chat):

        1. Build the converter via get_converter() and extract content
        2. Load the extracted data from converter.data_file
        3. Copy the data file into the unified cache (data_dir)
        4. Append the per-type record (+ data/data_file) to scraped_data[bucket]
        5. Build the standalone sub-skill — the unified build consumes the
           sub-skill references from the cache, so build_skill() must stay

        The thin per-type wrappers own everything type-specific: counter
        increment, id resolution, config dict, record keys, and log wording.

        Args:
            bucket: scraped_data / _source_counters key (e.g. "pdf")
            converter_type: CONVERTER_REGISTRY key for get_converter()
            config: fully-built converter config (name already includes idx/id)
            record: per-type scraped_data keys (ids + idx); data/data_file added
            cache_stem: cache filename without .json (e.g. "pdf_data_0_manual")
            label: display label for log lines (e.g. "PDF")
            fail_label: label used in the build-failure warning (defaults to label)
            summary_key: data key counted in the final summary line
            summary_noun: noun used in the final summary line
        """
        from skill_seekers.cli.skill_converter import get_converter

        source_skill_dir = os.path.join(self.sources_dir, config["name"])
        if os.path.isdir(source_skill_dir):
            shutil.rmtree(source_skill_dir)
        config = {**config, "output_dir": source_skill_dir}
        converter = get_converter(converter_type, config)

        # Extract content (each converter's extract() delegates to its
        # type-specific extract_*() implementation)
        converter.extract()

        # Load extracted data from file
        data_file = converter.data_file
        with open(data_file, encoding="utf-8") as f:
            data = json.load(f)

        # Copy data file to cache
        cache_data_file = os.path.join(self.data_dir, f"{cache_stem}.json")
        shutil.copy(data_file, cache_data_file)

        # Append to list instead of overwriting (multi-source support)
        self.scraped_data[bucket].append({**record, "data": data, "data_file": cache_data_file})

        # Build standalone SKILL.md for synthesis
        try:
            converter.build_skill()
            logger.info(f"✅ {label}: Standalone SKILL.md created")
        except Exception as e:
            logger.warning(f"⚠️  Failed to build standalone {fail_label or label} SKILL.md: {e}")

        logger.info(f"✅ {label}: {len(data.get(summary_key, []))} {summary_noun} extracted")

    def _scrape_pdf(self, source: dict[str, Any]):
        """Scrape PDF document."""
        # Multi-source support: Get unique index for this PDF source
        idx = self._source_counters["pdf"]
        self._source_counters["pdf"] += 1

        # Extract PDF identifier for unique naming (filename without extension)
        pdf_path = source["path"]
        pdf_id = os.path.splitext(os.path.basename(pdf_path))[0]

        logger.info(f"Scraping PDF: {source['path']}")
        self._scrape_with_converter(
            bucket="pdf",
            converter_type="pdf",
            config={
                "name": f"{self.name}_pdf_{idx}_{pdf_id}",
                "pdf_path": source["path"],  # Fixed: use pdf_path instead of pdf
                "description": f"{source.get('name', pdf_id)} documentation",
                "extract_tables": source.get("extract_tables", True),
                "ocr": source.get("ocr", False),
                "password": source.get("password"),
            },
            record={"pdf_path": pdf_path, "pdf_id": pdf_id, "idx": idx},
            cache_stem=f"pdf_data_{idx}_{pdf_id}",
            label="PDF",
            summary_key="pages",
            summary_noun="pages",
        )

    def _scrape_word(self, source: dict[str, Any]):
        """Scrape Word document (.docx)."""
        # Multi-source support: Get unique index for this Word source
        idx = self._source_counters["word"]
        self._source_counters["word"] += 1

        # Extract Word identifier for unique naming (filename without extension)
        docx_path = source["path"]
        docx_id = os.path.splitext(os.path.basename(docx_path))[0]

        logger.info(f"Scraping Word document: {source['path']}")
        self._scrape_with_converter(
            bucket="word",
            converter_type="word",
            config={
                "name": f"{self.name}_word_{idx}_{docx_id}",
                "docx_path": source["path"],
                "description": f"{source.get('name', docx_id)} documentation",
            },
            record={
                "docx_path": docx_path,
                "docx_id": docx_id,
                "word_id": docx_id,  # Alias for generic reference generation
                "idx": idx,
            },
            cache_stem=f"word_data_{idx}_{docx_id}",
            label="Word",
            summary_key="pages",
            summary_noun="sections",
        )

    def _scrape_video(self, source: dict[str, Any]):
        """Scrape video source (YouTube, local file, etc.)."""
        try:
            from skill_seekers.cli.video_scraper import VideoToSkillConverter
        except ImportError as e:
            logger.error(
                f"Video scraper dependencies not installed: {e}\n"
                "  Install with: pip install skill-seekers[video]\n"
                "  For visual extraction (frame analysis, OCR): pip install skill-seekers[video-full]"
            )
            return

        # Multi-source support: Get unique index for this video source
        idx = self._source_counters["video"]
        self._source_counters["video"] += 1

        # Determine video identifier
        video_url = source.get("url", "")
        video_id = video_url or source.get("path", f"video_{idx}")

        # Create config for video scraper
        video_config = {
            "name": f"{self.name}_video_{idx}",
            "url": source.get("url"),
            "video_file": source.get("path"),
            "playlist": source.get("playlist"),
            "description": source.get("description", ""),
            "languages": ",".join(source.get("languages", ["en"])),
            "visual": source.get("visual_extraction", False),
            "whisper_model": source.get("whisper_model", "base"),
        }

        video_skill_dir = os.path.join(self.sources_dir, video_config["name"])
        if os.path.isdir(video_skill_dir):
            shutil.rmtree(video_skill_dir)
        video_config["output_dir"] = video_skill_dir

        # Process video
        logger.info(f"Scraping video: {video_id}")
        converter = VideoToSkillConverter(video_config)

        try:
            # Use the public SkillConverter interface; extract() runs process(),
            # which stores its VideoScraperResult on converter.result.
            converter.extract()
            result = converter.result
            converter.save_extracted_data()

            cache_data_file = os.path.join(self.data_dir, f"video_data_{idx}.json")
            shutil.copy(converter.data_file, cache_data_file)

            # Append to list
            self.scraped_data["video"].append(
                {
                    "video_id": video_id,
                    "idx": idx,
                    "data": result.to_dict(),
                    "data_file": cache_data_file,
                }
            )

            # Build standalone SKILL.md for synthesis
            converter.build_skill()
            logger.info("✅ Video: Standalone SKILL.md created")

            logger.info(
                f"✅ Video: {len(result.videos)} videos, {result.total_segments} segments extracted"
            )
        except Exception as e:
            logger.error(f"Failed to process video source: {e}")

    # Bespoke (not routed through _scrape_with_converter): local uses the
    # function-based analyze_codebase() (no converter instance, no data_file),
    # then assembles its scraped_data record from the many analysis output files.
    def _scrape_local(self, source: dict[str, Any]):
        """
        Scrape local directory (documentation files or source code).

        Handles both:
        - Local documentation files (RST, Markdown, etc.)
        - Local source code for C3.x analysis
        """
        try:
            from skill_seekers.cli.codebase_scraper import analyze_codebase
        except ImportError:
            logger.error("codebase_scraper.py not found")
            return

        # Multi-source support: Get unique index for this local source
        idx = self._source_counters.get("local", 0)
        self._source_counters["local"] = idx + 1

        # Extract path and create identifier
        local_path = source["path"]
        path_id = os.path.basename(local_path.rstrip("/"))
        source_name = source.get("name", path_id)

        logger.info(f"Analyzing local directory: {local_path}")

        # Create temp output dir for local source analysis
        temp_output = Path(self.data_dir) / f"local_analysis_{idx}_{path_id}"
        temp_output.mkdir(parents=True, exist_ok=True)

        try:
            # Map source config to analyze_codebase parameters
            analysis_depth = source.get("analysis_depth", "deep")
            languages = source.get("languages")
            file_patterns = source.get("file_patterns")
            # Note: skip_patterns is not supported by analyze_codebase()
            # It's a config validator field but not used in codebase analysis

            # Map feature flags (default all ON for unified configs)
            build_api_reference = source.get("api_reference", True)
            build_dependency_graph = source.get("dependency_graph", True)
            detect_patterns = source.get("extract_patterns", True)
            extract_test_examples = source.get("extract_tests", True)
            build_how_to_guides = source.get("how_to_guides", True)
            extract_config_patterns = source.get("extract_config", True)
            extract_docs = source.get("extract_docs", True)
            # Note: Signal flow analysis is automatic for Godot projects (C3.10)

            # AI enhancement settings (CLI --enhance-level overrides per-source config)
            cli_args = getattr(self, "_cli_args", None)
            cli_enhance_level = (
                getattr(cli_args, "enhance_level", None) if cli_args is not None else None
            )
            enhance_level = (
                cli_enhance_level
                if cli_enhance_level is not None
                else source.get("enhance_level", 0)
            )

            # Run codebase analysis
            logger.info(f"   Analysis depth: {analysis_depth}")
            if languages:
                logger.info(f"   Languages: {', '.join(languages)}")
            if file_patterns:
                logger.info(f"   File patterns: {', '.join(file_patterns)}")

            analyze_codebase(
                directory=Path(local_path),
                output_dir=temp_output,
                depth=analysis_depth,
                languages=languages,
                file_patterns=file_patterns,
                build_api_reference=build_api_reference,
                extract_comments=False,  # Not needed for unified configs
                build_dependency_graph=build_dependency_graph,
                detect_patterns=detect_patterns,
                extract_test_examples=extract_test_examples,
                build_how_to_guides=build_how_to_guides,
                extract_config_patterns=extract_config_patterns,
                extract_docs=extract_docs,
                enhance_level=enhance_level,
            )

            # Load analysis outputs into memory.
            # _generate_references() moves dirs into references/ and deletes originals.
            refs = temp_output / "references"
            local_data = {
                "source_id": f"{self.name}_local_{idx}_{path_id}",
                "path": local_path,
                "name": source_name,
                "description": source.get("description", f"Local analysis of {path_id}"),
                "weight": source.get("weight", 1.0),
                "patterns": self._load_json_fallback(
                    refs / "patterns" / "all_patterns.json",
                    temp_output / "patterns" / "all_patterns.json",
                ),
                "test_examples": self._load_json_fallback(
                    refs / "test_examples" / "test_examples.json",
                    temp_output / "test_examples" / "test_examples.json",
                ),
                "how_to_guides": self._load_guide_collection(refs / "tutorials")
                or self._load_guide_collection(temp_output / "tutorials"),
                "config_patterns": self._load_json_fallback(
                    refs / "config_patterns" / "config_patterns.json",
                    temp_output / "config_patterns" / "config_patterns.json",
                ),
                "architecture": self._load_json_fallback(
                    refs / "architecture" / "architectural_patterns.json",
                    temp_output / "architecture" / "architectural_patterns.json",
                ),
                "api_reference": self._load_api_reference(refs / "api_reference")
                or self._load_api_reference(temp_output / "api_reference"),
                "dependency_graph": self._load_json_fallback(
                    refs / "dependencies" / "dependency_graph.json",
                    temp_output / "dependencies" / "dependency_graph.json",
                ),
            }

            # Handle signal flow analysis for Godot projects (C3.10)
            # Signal analysis is automatic for Godot files
            signal_flow_file = temp_output / "signals" / "signal_flow.json"
            if signal_flow_file.exists():
                local_data["signal_flow"] = self._load_json(signal_flow_file)
                logger.info("✅ Signal flow analysis included (Godot)")

            # Load SKILL.md if it exists
            skill_md_path = temp_output / "SKILL.md"
            if skill_md_path.exists():
                local_data["skill_md"] = skill_md_path.read_text(encoding="utf-8")
                logger.info(f"✅ Local: SKILL.md loaded ({len(local_data['skill_md'])} chars)")

            # Save local data to cache
            local_data_file = os.path.join(self.data_dir, f"local_data_{idx}_{path_id}.json")
            with open(local_data_file, "w", encoding="utf-8") as f:
                # Don't save skill_md in JSON (too large), keep it in local_data dict
                json_data = {k: v for k, v in local_data.items() if k != "skill_md"}
                json.dump(json_data, f, indent=2, ensure_ascii=False)

            # Move SKILL.md to cache if it exists
            skill_cache_dir = os.path.join(self.sources_dir, f"local_{idx}_{path_id}")
            os.makedirs(skill_cache_dir, exist_ok=True)
            if skill_md_path.exists():
                shutil.copy(skill_md_path, os.path.join(skill_cache_dir, "SKILL.md"))

            # Append to local sources list
            self.scraped_data["local"].append(local_data)

            logger.info(f"✅ Local: Analysis complete for {path_id}")

        except Exception as e:
            logger.error(f"❌ Local analysis failed: {e}")
            import traceback

            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise

    # ------------------------------------------------------------------
    # New source type handlers (v3.2.0+)
    # ------------------------------------------------------------------

    def _scrape_epub(self, source: dict[str, Any]):
        """Scrape EPUB e-book (.epub)."""
        idx = self._source_counters["epub"]
        self._source_counters["epub"] += 1

        epub_path = source["path"]
        epub_id = os.path.splitext(os.path.basename(epub_path))[0]

        logger.info(f"Scraping EPUB: {source['path']}")
        self._scrape_with_converter(
            bucket="epub",
            converter_type="epub",
            config={
                "name": f"{self.name}_epub_{idx}_{epub_id}",
                "epub_path": source["path"],
                "description": source.get("description", f"{epub_id} e-book"),
            },
            record={"epub_path": epub_path, "epub_id": epub_id, "idx": idx},
            cache_stem=f"epub_data_{idx}_{epub_id}",
            label="EPUB",
            summary_key="chapters",
            summary_noun="chapters",
        )

    def _scrape_jupyter(self, source: dict[str, Any]):
        """Scrape Jupyter Notebook (.ipynb)."""
        idx = self._source_counters["jupyter"]
        self._source_counters["jupyter"] += 1

        nb_path = source["path"]
        nb_id = os.path.splitext(os.path.basename(nb_path))[0]

        logger.info(f"Scraping Jupyter Notebook: {source['path']}")
        self._scrape_with_converter(
            bucket="jupyter",
            converter_type="jupyter",
            config={
                "name": f"{self.name}_jupyter_{idx}_{nb_id}",
                "notebook_path": source["path"],
                "description": source.get("description", f"{nb_id} notebook"),
            },
            record={"notebook_path": nb_path, "notebook_id": nb_id, "idx": idx},
            cache_stem=f"jupyter_data_{idx}_{nb_id}",
            label="Jupyter",
            summary_key="cells",
            summary_noun="cells",
        )

    def _scrape_html(self, source: dict[str, Any]):
        """Scrape local HTML file(s)."""
        idx = self._source_counters["html"]
        self._source_counters["html"] += 1

        html_path = source["path"]
        html_id = os.path.splitext(os.path.basename(html_path.rstrip("/")))[0]

        logger.info(f"Scraping local HTML: {source['path']}")
        self._scrape_with_converter(
            bucket="html",
            converter_type="html",
            config={
                "name": f"{self.name}_html_{idx}_{html_id}",
                "html_path": source["path"],
                "description": source.get("description", f"{html_id} HTML content"),
            },
            record={"html_path": html_path, "html_id": html_id, "idx": idx},
            cache_stem=f"html_data_{idx}_{html_id}",
            label="HTML",
            summary_key="pages",
            summary_noun="pages",
        )

    def _scrape_openapi(self, source: dict[str, Any]):
        """Scrape OpenAPI/Swagger specification."""
        idx = self._source_counters["openapi"]
        self._source_counters["openapi"] += 1

        spec_path = source.get("path", source.get("url", ""))
        spec_id = os.path.splitext(os.path.basename(spec_path))[0] if spec_path else f"spec_{idx}"

        logger.info(f"Scraping OpenAPI spec: {spec_path}")
        self._scrape_with_converter(
            bucket="openapi",
            converter_type="openapi",
            config={
                "name": f"{self.name}_openapi_{idx}_{spec_id}",
                "spec_path": source.get("path"),
                "spec_url": source.get("url"),
                "description": source.get("description", f"{spec_id} API spec"),
            },
            record={"spec_path": spec_path, "spec_id": spec_id, "idx": idx},
            cache_stem=f"openapi_data_{idx}_{spec_id}",
            label="OpenAPI",
            summary_key="endpoints",
            summary_noun="endpoints",
        )

    def _scrape_asciidoc(self, source: dict[str, Any]):
        """Scrape AsciiDoc document(s)."""
        idx = self._source_counters["asciidoc"]
        self._source_counters["asciidoc"] += 1

        adoc_path = source["path"]
        adoc_id = os.path.splitext(os.path.basename(adoc_path.rstrip("/")))[0]

        logger.info(f"Scraping AsciiDoc: {source['path']}")
        self._scrape_with_converter(
            bucket="asciidoc",
            converter_type="asciidoc",
            config={
                "name": f"{self.name}_asciidoc_{idx}_{adoc_id}",
                "asciidoc_path": source["path"],
                "description": source.get("description", f"{adoc_id} AsciiDoc content"),
            },
            record={"asciidoc_path": adoc_path, "asciidoc_id": adoc_id, "idx": idx},
            cache_stem=f"asciidoc_data_{idx}_{adoc_id}",
            label="AsciiDoc",
            summary_key="sections",
            summary_noun="sections",
        )

    def _scrape_pptx(self, source: dict[str, Any]):
        """Scrape PowerPoint presentation (.pptx)."""
        idx = self._source_counters["pptx"]
        self._source_counters["pptx"] += 1

        pptx_path = source["path"]
        pptx_id = os.path.splitext(os.path.basename(pptx_path))[0]

        logger.info(f"Scraping PowerPoint: {source['path']}")
        self._scrape_with_converter(
            bucket="pptx",
            converter_type="pptx",
            config={
                "name": f"{self.name}_pptx_{idx}_{pptx_id}",
                "pptx_path": source["path"],
                "description": source.get("description", f"{pptx_id} presentation"),
            },
            record={"pptx_path": pptx_path, "pptx_id": pptx_id, "idx": idx},
            cache_stem=f"pptx_data_{idx}_{pptx_id}",
            label="PowerPoint",
            summary_key="slides",
            summary_noun="slides",
        )

    def _scrape_confluence(self, source: dict[str, Any]):
        """Scrape Confluence wiki (API or exported HTML/XML)."""
        idx = self._source_counters["confluence"]
        self._source_counters["confluence"] += 1

        source_id = source.get("space_key", source.get("path", f"confluence_{idx}"))
        if isinstance(source_id, str) and "/" in source_id:
            source_id = os.path.basename(source_id.rstrip("/"))

        logger.info(f"Scraping Confluence: {source_id}")
        self._scrape_with_converter(
            bucket="confluence",
            converter_type="confluence",
            config={
                "name": f"{self.name}_confluence_{idx}_{source_id}",
                "base_url": source.get("base_url", source.get("url")),
                "space_key": source.get("space_key"),
                "export_path": source.get("path"),
                "username": source.get("username"),
                "token": source.get("token"),
                "description": source.get("description", f"{source_id} Confluence content"),
                "max_pages": source.get("max_pages", DEFAULTS["scraping"]["max_pages"]),
            },
            record={"source_id": source_id, "idx": idx},
            cache_stem=f"confluence_data_{idx}_{source_id}",
            label="Confluence",
            summary_key="pages",
            summary_noun="pages",
        )

    def _scrape_notion(self, source: dict[str, Any]):
        """Scrape Notion pages (API or exported Markdown)."""
        idx = self._source_counters["notion"]
        self._source_counters["notion"] += 1

        source_id = source.get(
            "database_id", source.get("page_id", source.get("path", f"notion_{idx}"))
        )
        if isinstance(source_id, str) and "/" in source_id:
            source_id = os.path.basename(source_id.rstrip("/"))

        logger.info(f"Scraping Notion: {source_id}")
        self._scrape_with_converter(
            bucket="notion",
            converter_type="notion",
            config={
                "name": f"{self.name}_notion_{idx}_{source_id}",
                "database_id": source.get("database_id"),
                "page_id": source.get("page_id"),
                "export_path": source.get("path"),
                "token": source.get("token"),
                "description": source.get("description", f"{source_id} Notion content"),
                "max_pages": source.get("max_pages", DEFAULTS["scraping"]["max_pages"]),
            },
            record={"source_id": source_id, "idx": idx},
            cache_stem=f"notion_data_{idx}_{source_id}",
            label="Notion",
            summary_key="pages",
            summary_noun="pages",
        )

    def _scrape_rss(self, source: dict[str, Any]):
        """Scrape RSS/Atom feed (with optional full article scraping)."""
        idx = self._source_counters["rss"]
        self._source_counters["rss"] += 1

        feed_url = source.get("url", source.get("path", ""))
        feed_id = feed_url.split("/")[-1].split(".")[0] if feed_url else f"feed_{idx}"

        logger.info(f"Scraping RSS/Atom feed: {feed_url}")
        self._scrape_with_converter(
            bucket="rss",
            converter_type="rss",
            config={
                "name": f"{self.name}_rss_{idx}_{feed_id}",
                "feed_url": source.get("url"),
                "feed_path": source.get("path"),
                "follow_links": source.get("follow_links", True),
                "max_articles": source.get("max_articles", 50),
                "description": source.get("description", f"{feed_id} RSS/Atom feed"),
            },
            record={"feed_url": feed_url, "feed_id": feed_id, "idx": idx},
            cache_stem=f"rss_data_{idx}_{feed_id}",
            label="RSS",
            summary_key="articles",
            summary_noun="articles",
        )

    def _scrape_manpage(self, source: dict[str, Any]):
        """Scrape man page(s)."""
        idx = self._source_counters["manpage"]
        self._source_counters["manpage"] += 1

        man_names = source.get("names", [])
        man_path = source.get("path", "")
        man_id = man_names[0] if man_names else os.path.basename(man_path.rstrip("/"))

        logger.info(f"Scraping man pages: {man_id}")
        self._scrape_with_converter(
            bucket="manpage",
            converter_type="manpage",
            config={
                "name": f"{self.name}_manpage_{idx}_{man_id}",
                "man_names": man_names,
                "man_path": man_path,
                "sections": source.get("sections", []),
                "description": source.get("description", f"{man_id} man pages"),
            },
            record={"man_id": man_id, "idx": idx},
            cache_stem=f"manpage_data_{idx}_{man_id}",
            label="Man pages",
            fail_label="man page",
            summary_key="pages",
            summary_noun="man pages",
        )

    def _scrape_chat(self, source: dict[str, Any]):
        """Scrape Slack/Discord chat export or API."""
        idx = self._source_counters["chat"]
        self._source_counters["chat"] += 1

        export_path = source.get("path", "")
        channel = source.get("channel", source.get("channel_id", ""))
        chat_id = channel or os.path.basename(export_path.rstrip("/")) or f"chat_{idx}"

        logger.info(f"Scraping chat: {chat_id}")
        self._scrape_with_converter(
            bucket="chat",
            converter_type="chat",
            config={
                "name": f"{self.name}_chat_{idx}_{chat_id}",
                "export_path": source.get("path"),
                "platform": source.get("platform", "slack"),
                "token": source.get("token"),
                "channel": channel,
                "max_messages": source.get("max_messages", 10000),
                "description": source.get("description", f"{chat_id} chat export"),
            },
            record={"chat_id": chat_id, "platform": source.get("platform", "slack"), "idx": idx},
            cache_stem=f"chat_data_{idx}_{chat_id}",
            label="Chat",
            fail_label="chat",
            summary_key="messages",
            summary_noun="messages",
        )

    def _reset_cached_source_state(self) -> None:
        """Reset per-source state before rebuilding it from cached files."""
        self.scraped_data = {source_type: [] for source_type in self.SOURCE_DISPATCH}
        self._source_counters = dict.fromkeys(self.SOURCE_DISPATCH, 0)

    def _next_source_index(self, source_type: str) -> int:
        """Return and increment the cached source index for a source type."""
        idx = self._source_counters[source_type]
        self._source_counters[source_type] = idx + 1
        return idx

    @staticmethod
    def _read_required_json(file_path: str) -> Any:
        """Read a required cached JSON file, raising a clear error if absent."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                "skip_scrape is set but cached data is missing at "
                f"{file_path}. Run once without skip_scrape to populate the cache."
            )
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    def _append_cached_data_source(
        self, bucket: str, cache_stem: str, record: dict[str, Any]
    ) -> None:
        """Load a cached data/<cache_stem>.json payload into scraped_data."""
        data_file = os.path.join(self.data_dir, f"{cache_stem}.json")
        data = self._read_required_json(data_file)
        self.scraped_data[bucket].append({**record, "data": data, "data_file": data_file})

    def _load_cached_sources(self) -> int:
        """Reload unified scraped_data from prior .skillseeker-cache outputs."""
        logger.info("=" * 60)
        logger.info("PHASE 1: Loading cached source data (skip_scrape)")
        logger.info("=" * 60)

        self._reset_cached_source_state()
        sources = self.config.get("sources", [])
        loader_names = {
            "documentation": "_load_cached_documentation",
            "github": "_load_cached_github",
            "pdf": "_load_cached_pdf",
            "word": "_load_cached_word",
            "video": "_load_cached_video",
            "local": "_load_cached_local",
            "epub": "_load_cached_epub",
            "jupyter": "_load_cached_jupyter",
            "html": "_load_cached_html",
            "openapi": "_load_cached_openapi",
            "asciidoc": "_load_cached_asciidoc",
            "pptx": "_load_cached_pptx",
            "confluence": "_load_cached_confluence",
            "notion": "_load_cached_notion",
            "rss": "_load_cached_rss",
            "manpage": "_load_cached_manpage",
            "chat": "_load_cached_chat",
        }

        for i, source in enumerate(sources):
            source_type = source["type"]
            logger.info(f"\n[{i + 1}/{len(sources)}] Loading cached {source_type} source...")
            loader_name = loader_names.get(source_type)
            if loader_name is None:
                logger.warning(f"Unknown source type: {source_type}")
                continue
            getattr(self, loader_name)(source)

        loaded_count = sum(len(v) for v in self.scraped_data.values())
        logger.info(f"\n✅ Loaded {loaded_count} cached source item(s) successfully")
        return loaded_count

    def _load_cached_documentation(self, source: dict[str, Any]) -> None:
        """Load cached documentation summary written by _scrape_documentation()."""
        idx = self._next_source_index("documentation")
        source_name = self._documentation_source_name(idx, source)
        docs_skill_dir = os.path.join(self.sources_dir, source_name)
        docs_data_file = f"{docs_skill_dir}_data/summary.json"
        summary = self._read_required_json(docs_data_file)

        self.scraped_data["documentation"].append(
            {
                "source_id": source_name,
                "base_url": source["base_url"],
                "pages": summary.get("pages", []),
                "total_pages": summary.get("total_pages", 0),
                "data_file": docs_data_file,
                "refs_dir": os.path.join(docs_skill_dir, "references"),
            }
        )

    def _load_cached_github(self, source: dict[str, Any]) -> None:
        """Load cached GitHub scraper data."""
        idx = self._next_source_index("github")
        repo = source["repo"]
        repo_id = repo.replace("/", "_")
        self._append_cached_data_source(
            "github",
            f"github_data_{idx}_{repo_id}",
            {"repo": repo, "repo_id": repo_id, "idx": idx},
        )

    def _load_cached_pdf(self, source: dict[str, Any]) -> None:
        """Load cached PDF scraper data."""
        idx = self._next_source_index("pdf")
        pdf_path = source["path"]
        pdf_id = os.path.splitext(os.path.basename(pdf_path))[0]
        self._append_cached_data_source(
            "pdf",
            f"pdf_data_{idx}_{pdf_id}",
            {"pdf_path": pdf_path, "pdf_id": pdf_id, "idx": idx},
        )

    def _load_cached_word(self, source: dict[str, Any]) -> None:
        """Load cached Word scraper data."""
        idx = self._next_source_index("word")
        docx_path = source["path"]
        docx_id = os.path.splitext(os.path.basename(docx_path))[0]
        self._append_cached_data_source(
            "word",
            f"word_data_{idx}_{docx_id}",
            {
                "docx_path": docx_path,
                "docx_id": docx_id,
                "word_id": docx_id,
                "idx": idx,
            },
        )

    def _load_cached_video(self, source: dict[str, Any]) -> None:
        """Load cached video data."""
        idx = self._next_source_index("video")
        video_url = source.get("url", "")
        video_id = video_url or source.get("path", f"video_{idx}")
        data_file = os.path.join(self.data_dir, f"video_data_{idx}.json")
        data = self._read_required_json(data_file)
        self.scraped_data["video"].append(
            {"video_id": video_id, "idx": idx, "data": data, "data_file": data_file}
        )

    def _load_cached_local(self, source: dict[str, Any]) -> None:
        """Load cached local codebase analysis data."""
        idx = self._next_source_index("local")
        local_path = source["path"]
        path_id = os.path.basename(local_path.rstrip("/"))
        source_name = source.get("name", path_id)
        data_file = os.path.join(self.data_dir, f"local_data_{idx}_{path_id}.json")
        local_data = self._read_required_json(data_file)
        local_data.update(
            {
                "source_id": f"{self.name}_local_{idx}_{path_id}",
                "path": local_path,
                "name": source_name,
                "description": source.get("description", f"Local analysis of {path_id}"),
                "weight": source.get("weight", 1.0),
            }
        )

        skill_md_path = Path(self.sources_dir) / f"local_{idx}_{path_id}" / "SKILL.md"
        if skill_md_path.exists():
            local_data["skill_md"] = skill_md_path.read_text(encoding="utf-8")

        self.scraped_data["local"].append(local_data)

    def _load_cached_epub(self, source: dict[str, Any]) -> None:
        """Load cached EPUB scraper data."""
        idx = self._next_source_index("epub")
        epub_path = source["path"]
        epub_id = os.path.splitext(os.path.basename(epub_path))[0]
        self._append_cached_data_source(
            "epub",
            f"epub_data_{idx}_{epub_id}",
            {"epub_path": epub_path, "epub_id": epub_id, "idx": idx},
        )

    def _load_cached_jupyter(self, source: dict[str, Any]) -> None:
        """Load cached Jupyter scraper data."""
        idx = self._next_source_index("jupyter")
        nb_path = source["path"]
        nb_id = os.path.splitext(os.path.basename(nb_path))[0]
        self._append_cached_data_source(
            "jupyter",
            f"jupyter_data_{idx}_{nb_id}",
            {"notebook_path": nb_path, "notebook_id": nb_id, "idx": idx},
        )

    def _load_cached_html(self, source: dict[str, Any]) -> None:
        """Load cached local HTML scraper data."""
        idx = self._next_source_index("html")
        html_path = source["path"]
        html_id = os.path.splitext(os.path.basename(html_path.rstrip("/")))[0]
        self._append_cached_data_source(
            "html",
            f"html_data_{idx}_{html_id}",
            {"html_path": html_path, "html_id": html_id, "idx": idx},
        )

    def _load_cached_openapi(self, source: dict[str, Any]) -> None:
        """Load cached OpenAPI scraper data."""
        idx = self._next_source_index("openapi")
        spec_path = source.get("path", source.get("url", ""))
        spec_id = os.path.splitext(os.path.basename(spec_path))[0] if spec_path else f"spec_{idx}"
        self._append_cached_data_source(
            "openapi",
            f"openapi_data_{idx}_{spec_id}",
            {"spec_path": spec_path, "spec_id": spec_id, "idx": idx},
        )

    def _load_cached_asciidoc(self, source: dict[str, Any]) -> None:
        """Load cached AsciiDoc scraper data."""
        idx = self._next_source_index("asciidoc")
        adoc_path = source["path"]
        adoc_id = os.path.splitext(os.path.basename(adoc_path.rstrip("/")))[0]
        self._append_cached_data_source(
            "asciidoc",
            f"asciidoc_data_{idx}_{adoc_id}",
            {"asciidoc_path": adoc_path, "asciidoc_id": adoc_id, "idx": idx},
        )

    def _load_cached_pptx(self, source: dict[str, Any]) -> None:
        """Load cached PowerPoint scraper data."""
        idx = self._next_source_index("pptx")
        pptx_path = source["path"]
        pptx_id = os.path.splitext(os.path.basename(pptx_path))[0]
        self._append_cached_data_source(
            "pptx",
            f"pptx_data_{idx}_{pptx_id}",
            {"pptx_path": pptx_path, "pptx_id": pptx_id, "idx": idx},
        )

    def _load_cached_confluence(self, source: dict[str, Any]) -> None:
        """Load cached Confluence scraper data."""
        idx = self._next_source_index("confluence")
        source_id = source.get("space_key", source.get("path", f"confluence_{idx}"))
        if isinstance(source_id, str) and "/" in source_id:
            source_id = os.path.basename(source_id.rstrip("/"))
        self._append_cached_data_source(
            "confluence",
            f"confluence_data_{idx}_{source_id}",
            {"source_id": source_id, "idx": idx},
        )

    def _load_cached_notion(self, source: dict[str, Any]) -> None:
        """Load cached Notion scraper data."""
        idx = self._next_source_index("notion")
        source_id = source.get(
            "database_id", source.get("page_id", source.get("path", f"notion_{idx}"))
        )
        if isinstance(source_id, str) and "/" in source_id:
            source_id = os.path.basename(source_id.rstrip("/"))
        self._append_cached_data_source(
            "notion",
            f"notion_data_{idx}_{source_id}",
            {"source_id": source_id, "idx": idx},
        )

    def _load_cached_rss(self, source: dict[str, Any]) -> None:
        """Load cached RSS scraper data."""
        idx = self._next_source_index("rss")
        feed_url = source.get("url", source.get("path", ""))
        feed_id = feed_url.split("/")[-1].split(".")[0] if feed_url else f"feed_{idx}"
        self._append_cached_data_source(
            "rss",
            f"rss_data_{idx}_{feed_id}",
            {"feed_url": feed_url, "feed_id": feed_id, "idx": idx},
        )

    def _load_cached_manpage(self, source: dict[str, Any]) -> None:
        """Load cached manpage scraper data."""
        idx = self._next_source_index("manpage")
        man_names = source.get("names", [])
        man_path = source.get("path", "")
        man_id = man_names[0] if man_names else os.path.basename(man_path.rstrip("/"))
        self._append_cached_data_source(
            "manpage",
            f"manpage_data_{idx}_{man_id}",
            {"man_id": man_id, "idx": idx},
        )

    def _load_cached_chat(self, source: dict[str, Any]) -> None:
        """Load cached chat scraper data."""
        idx = self._next_source_index("chat")
        export_path = source.get("path", "")
        channel = source.get("channel", source.get("channel_id", ""))
        chat_id = channel or os.path.basename(export_path.rstrip("/")) or f"chat_{idx}"
        self._append_cached_data_source(
            "chat",
            f"chat_data_{idx}_{chat_id}",
            {"chat_id": chat_id, "platform": source.get("platform", "slack"), "idx": idx},
        )

    def _load_json_fallback(self, primary: Path, fallback: Path) -> dict:
        """Load JSON from primary path, falling back to secondary if not found."""
        if primary.exists():
            return self._load_json(primary)
        return self._load_json(fallback)

    def _load_json(self, file_path: Path) -> dict:
        """
        Load JSON file safely.

        Args:
            file_path: Path to JSON file

        Returns:
            Dict with JSON data, or empty dict if file doesn't exist or is invalid
        """
        if not file_path.exists():
            logger.warning(f"JSON file not found: {file_path}")
            return {}

        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load JSON {file_path}: {e}")
            return {}

    def _load_guide_collection(self, tutorials_dir: Path) -> dict:
        """
        Load how-to guide collection from tutorials directory.

        Returns an empty dict (falsy) when the directory or any guide files
        are missing, so callers can chain ``primary or fallback`` to fall
        through to a secondary path. Returning a non-empty placeholder here
        would short-circuit those chains and silently drop real guide data
        in the fallback location (issue #364).

        Args:
            tutorials_dir: Path to tutorials directory

        Returns:
            Dict with guide collection data, or ``{}`` when no guides found.
        """
        if not tutorials_dir.exists():
            logger.debug(f"Tutorials directory not found: {tutorials_dir}")
            return {}

        collection_file = tutorials_dir / "guide_collection.json"
        if collection_file.exists():
            return self._load_json(collection_file)

        # Fallback: scan for individual guide JSON files
        guides = []
        for guide_file in tutorials_dir.glob("guide_*.json"):
            guide_data = self._load_json(guide_file)
            if guide_data:
                guides.append(guide_data)

        if not guides:
            return {}
        return {"guides": guides, "total_count": len(guides)}

    def _load_api_reference(self, api_dir: Path) -> dict[str, Any]:
        """
        Load API reference markdown files from api_reference directory.

        Args:
            api_dir: Path to api_reference directory

        Returns:
            Dict mapping module names to markdown content, or empty dict if not found
        """
        if not api_dir.exists():
            logger.debug(f"API reference directory not found: {api_dir}")
            return {}

        api_refs = {}
        for md_file in api_dir.glob("*.md"):
            try:
                module_name = md_file.stem
                api_refs[module_name] = md_file.read_text(encoding="utf-8")
            except OSError as e:
                logger.warning(f"Failed to read API reference {md_file}: {e}")

        return api_refs

    def _run_c3_analysis(self, local_repo_path: str, source: dict[str, Any]) -> dict[str, Any]:
        """
        Run comprehensive C3.x codebase analysis.

        Calls codebase_scraper.analyze_codebase() with all C3.x features enabled,
        loads the results into memory, and cleans up temporary files.

        Args:
            local_repo_path: Path to local repository
            source: GitHub source configuration dict

        Returns:
            Dict with keys: patterns, test_examples, how_to_guides,
            config_patterns, architecture
        """
        try:
            from skill_seekers.cli.codebase_scraper import analyze_codebase
        except ImportError:
            logger.error("codebase_scraper.py not found")
            return {}

        # Create temp output dir for C3.x analysis
        temp_output = Path(self.data_dir) / "c3_analysis_temp"
        temp_output.mkdir(parents=True, exist_ok=True)

        logger.info(f"   Analyzing codebase: {local_repo_path}")

        try:
            # Resolve agent from CLI args for C3.x analysis
            cli_args = getattr(self, "_cli_args", None)
            agent = getattr(cli_args, "agent", None) if cli_args else None
            agent_cmd = getattr(cli_args, "agent_cmd", None) if cli_args else None

            # Run full C3.x analysis
            _results = analyze_codebase(
                directory=Path(local_repo_path),
                output_dir=temp_output,
                depth="deep",
                languages=source.get("languages"),  # Respect language filter from source config
                file_patterns=source.get("file_patterns"),
                build_api_reference=True,  # C2.5: API Reference
                extract_comments=False,  # Not needed
                build_dependency_graph=True,  # C2.6: Dependency Graph
                detect_patterns=True,  # C3.1: Design patterns
                extract_test_examples=True,  # C3.2: Test examples
                build_how_to_guides=True,  # C3.3: How-to guides
                extract_config_patterns=True,  # C3.4: Config patterns
                extract_docs=True,
                enhance_level=0 if source.get("ai_mode", "auto") == "none" else 2,
                agent=agent,
                agent_cmd=agent_cmd,
            )

            # Load C3.x outputs into memory.
            # _generate_references() inside analyze_codebase() moves analysis dirs
            # into references/ and deletes the originals, so we check both locations.
            refs = temp_output / "references"
            c3_data = {
                "patterns": self._load_json_fallback(
                    refs / "patterns" / "all_patterns.json",
                    temp_output / "patterns" / "all_patterns.json",
                ),
                "test_examples": self._load_json_fallback(
                    refs / "test_examples" / "test_examples.json",
                    temp_output / "test_examples" / "test_examples.json",
                ),
                "how_to_guides": self._load_guide_collection(refs / "tutorials")
                or self._load_guide_collection(temp_output / "tutorials"),
                "config_patterns": self._load_json_fallback(
                    refs / "config_patterns" / "config_patterns.json",
                    temp_output / "config_patterns" / "config_patterns.json",
                ),
                "architecture": self._load_json_fallback(
                    refs / "architecture" / "architectural_patterns.json",
                    temp_output / "architecture" / "architectural_patterns.json",
                ),
                "api_reference": self._load_api_reference(refs / "api_reference")
                or self._load_api_reference(temp_output / "api_reference"),
                "dependency_graph": self._load_json_fallback(
                    refs / "dependencies" / "dependency_graph.json",
                    temp_output / "dependencies" / "dependency_graph.json",
                ),
            }

            # Log summary
            total_patterns = sum(len(f.get("patterns", [])) for f in c3_data.get("patterns", []))
            total_examples = c3_data.get("test_examples", {}).get("total_examples", 0)
            total_guides = len(c3_data.get("how_to_guides", {}).get("guides", []))
            total_configs = len(c3_data.get("config_patterns", {}).get("config_files", []))
            arch_patterns = len(c3_data.get("architecture", {}).get("patterns", []))

            logger.info(f"   ✓ Design Patterns: {total_patterns}")
            logger.info(f"   ✓ Test Examples: {total_examples}")
            logger.info(f"   ✓ How-To Guides: {total_guides}")
            logger.info(f"   ✓ Config Files: {total_configs}")
            logger.info(f"   ✓ Architecture Patterns: {arch_patterns}")

            return c3_data

        except Exception as e:
            logger.error(f"C3.x analysis failed: {e}")
            import traceback

            traceback.print_exc()
            return {}

        finally:
            # Clean up temp directory
            if temp_output.exists():
                try:
                    shutil.rmtree(temp_output)
                except Exception as e:
                    logger.warning(f"Failed to clean up temp directory: {e}")

    def detect_conflicts(self) -> list:
        """
        Detect conflicts between documentation and code.

        Only applicable if both documentation and GitHub sources exist.

        Returns:
            List of conflicts
        """
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 2: Detecting conflicts")
        logger.info("=" * 60)

        if not self.validator.needs_api_merge():
            logger.info("No API merge needed (only one API source)")
            logger.info("\n" + "=" * 60)
            logger.info("PHASE 3: Merging sources (skipped - no conflicts detected)")
            logger.info("=" * 60)
            return []

        # Get documentation and GitHub data (scraped_data stores lists of sources)
        docs_list = self.scraped_data.get("documentation", [])
        github_list = self.scraped_data.get("github", [])

        if not docs_list or not github_list:
            logger.warning("Missing documentation or GitHub data for conflict detection")
            return []

        # Use the first source from each list
        docs_data = docs_list[0]
        github_data = github_list[0]

        # Load data files (cached for reuse in merge_sources)
        with open(docs_data["data_file"], encoding="utf-8") as f:
            docs_json = json.load(f)
        docs_json = self._enrich_docs_json(docs_json, docs_data["data_file"])

        with open(github_data["data_file"], encoding="utf-8") as f:
            github_json = json.load(f)

        self._cached_docs_json = docs_json
        self._cached_github_json = github_json

        # Detect conflicts
        detector = ConflictDetector(docs_json, github_json)
        conflicts = detector.detect_all_conflicts()

        # Save conflicts
        conflicts_file = os.path.join(self.data_dir, "conflicts.json")
        detector.save_conflicts(conflicts, conflicts_file)

        # Print summary
        summary = detector.generate_summary(conflicts)
        logger.info("\n📊 Conflict Summary:")
        logger.info(f"   Total: {summary['total']}")
        logger.info("   By Type:")
        for ctype, count in summary["by_type"].items():
            if count > 0:
                logger.info(f"     - {ctype}: {count}")
        logger.info("   By Severity:")
        for severity, count in summary["by_severity"].items():
            if count > 0:
                emoji = "🔴" if severity == "high" else "🟡" if severity == "medium" else "🟢"
                logger.info(f"     {emoji} {severity}: {count}")

        return conflicts

    def merge_sources(self, conflicts: list):
        """
        Merge data from multiple sources.

        Args:
            conflicts: List of detected conflicts
        """
        logger.info("\n" + "=" * 60)
        logger.info(f"PHASE 3: Merging sources ({self.merge_mode})")
        logger.info("=" * 60)

        if not conflicts:
            logger.info("No conflicts to merge")
            return None

        # Get data files (scraped_data stores lists of sources)
        docs_list = self.scraped_data.get("documentation", [])
        github_list = self.scraped_data.get("github", [])

        if not docs_list or not github_list:
            logger.warning("Missing documentation or GitHub data for merging")
            return None

        # Reuse cached data from detect_conflicts() to avoid redundant disk I/O
        docs_json = getattr(self, "_cached_docs_json", None)
        github_json = getattr(self, "_cached_github_json", None)

        if docs_json is None or github_json is None:
            docs_data = docs_list[0]
            github_data = github_list[0]
            with open(docs_data["data_file"], encoding="utf-8") as f:
                docs_json = json.load(f)
            docs_json = self._enrich_docs_json(docs_json, docs_data["data_file"])
            with open(github_data["data_file"], encoding="utf-8") as f:
                github_json = json.load(f)

        # Choose merger
        if self.merge_mode in ("ai-enhanced", "claude-enhanced"):
            merger = AIEnhancedMerger(docs_json, github_json, conflicts)
        else:
            merger = RuleBasedMerger(docs_json, github_json, conflicts)

        # Merge
        merged_data = merger.merge_all()

        # Save merged data
        merged_file = os.path.join(self.data_dir, "merged_data.json")
        with open(merged_file, "w", encoding="utf-8") as f:
            json.dump(merged_data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Merged data saved: {merged_file}")

        return merged_data

    def extract(self):
        """SkillConverter interface — delegates to scrape_all_sources()."""
        if getattr(self, "skip_scrape", False):
            self._load_cached_sources()
        else:
            self.scrape_all_sources()

    def build_skill(self, merged_data: dict | None = None):
        """
        Build final unified skill.

        Args:
            merged_data: Merged API data (if conflicts were resolved)
        """
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 4: Building unified skill")
        logger.info("=" * 60)

        # Load conflicts if they exist
        conflicts = []
        conflicts_file = os.path.join(self.data_dir, "conflicts.json")
        if os.path.exists(conflicts_file):
            with open(conflicts_file, encoding="utf-8") as f:
                conflicts_data = json.load(f)
                conflicts = conflicts_data.get("conflicts", [])

        # Build skill
        builder = UnifiedSkillBuilder(
            self.config, self.scraped_data, merged_data, conflicts, cache_dir=self.cache_dir
        )

        builder.build()

        logger.info(f"✅ Unified skill built: {self.output_dir}/")

    def run(self, args=None):
        """
        Execute complete unified scraping workflow.

        Args:
            args: Optional parsed CLI arguments for workflow integration.
                  When provided, enhancement workflows (--enhance-workflow,
                  --enhance-stage) are executed after the skill is built.
        """
        # Store CLI args so _scrape_local() can access --enhance-level override
        self._cli_args = args

        logger.info("\n" + "🚀 " * 20)
        logger.info(f"Unified Scraper: {self.config['name']}")
        logger.info("🚀 " * 20 + "\n")

        # Dry run: preview the sources without scraping or writing anything.
        if getattr(self, "dry_run", False):
            sources = self.config.get("sources", [])
            logger.info("DRY RUN — no scraping or writes will be performed.")
            logger.info(f"Would scrape {len(sources)} source(s):")
            for i, source in enumerate(sources, 1):
                location = (
                    source.get("base_url")
                    or source.get("repo")
                    or source.get("path")
                    or source.get("file")
                    or ""
                )
                logger.info(f"  [{i}] {source.get('type', 'unknown')} {location}".rstrip())
            logger.info(f"Would write skill to: {self.output_dir}/")
            return 0

        try:
            # Phase 1: Scrape all sources, or rebuild in-memory source state
            # from the previous .skillseeker-cache when skip_scrape is set.
            if getattr(self, "skip_scrape", False):
                scraped_count = self._load_cached_sources()
            else:
                scraped_count = self.scrape_all_sources()

            # Abort if every source failed — otherwise we'd build (and report
            # success for) an empty skill from no data.
            if not scraped_count:
                logger.error("❌ All sources failed to scrape (no data collected); aborting build.")
                return 1

            # Phase 2: Detect conflicts (if applicable)
            conflicts = self.detect_conflicts()

            # Phase 3: Merge sources (if conflicts exist)
            merged_data = None
            if conflicts:
                merged_data = self.merge_sources(conflicts)

            # Phase 4: Build skill
            self.build_skill(merged_data)

            # Phase 5: Enhancement Workflow Integration
            # Support workflow fields in JSON config as well as CLI args.
            # JSON fields: "workflows" (list), "workflow_stages" (list), "workflow_vars" (dict)
            # CLI args always take precedence; JSON fields are appended after.
            json_workflows = self.config.get("workflows", [])
            json_stages = self.config.get("workflow_stages", [])
            json_vars = self.config.get("workflow_vars", {})
            has_json_workflows = bool(json_workflows or json_stages or json_vars)

            if args is not None or has_json_workflows:
                import argparse

                from skill_seekers.cli.workflow_runner import run_workflows

                # Build effective args: use CLI args when provided, otherwise empty namespace
                effective_args = (
                    args
                    if args is not None
                    else argparse.Namespace(
                        enhance_workflow=None,
                        enhance_stage=None,
                        var=None,
                        workflow_dry_run=False,
                    )
                )

                # Merge JSON workflow config into effective_args (JSON appended after CLI)
                if json_workflows:
                    effective_args.enhance_workflow = (
                        list(effective_args.enhance_workflow or []) + json_workflows
                    )
                if json_stages:
                    effective_args.enhance_stage = (
                        list(effective_args.enhance_stage or []) + json_stages
                    )
                if json_vars:
                    effective_args.var = list(effective_args.var or []) + [
                        f"{k}={v}" for k, v in json_vars.items()
                    ]

                unified_context = {
                    "name": self.config.get("name", ""),
                    "description": self.config.get("description", ""),
                }
                run_workflows(effective_args, context=unified_context)

            # Phase 6: AI Enhancement of SKILL.md
            # Read from ExecutionContext first (has correct priority resolution),
            # fall back to raw config dict for backward compatibility.
            enhancement_config = self.config.get("enhancement", {})
            from skill_seekers.cli.execution_context import ExecutionContext

            # ExecutionContext.get() never raises (it auto-creates a default
            # context), so "context vs raw config" must be decided explicitly:
            # only trust the context when the CLI actually initialized it.
            ctx_initialized = ExecutionContext.is_initialized()
            if ctx_initialized:
                ctx = ExecutionContext.get()
                enhancement_enabled = ctx.enhancement.enabled
                enhancement_level = ctx.enhancement.level
                enhancement_mode = ctx.enhancement.mode.upper()
            else:
                # Standalone/MCP use: honor the config file's enhancement block + args
                enhancement_enabled = enhancement_config.get("enabled", False)
                enhancement_level = enhancement_config.get("level", 0)
                enhancement_mode = enhancement_config.get("mode", "AUTO").upper()

                cli_enhance_level = (
                    getattr(args, "enhance_level", None) if args is not None else None
                )
                if cli_enhance_level is not None:
                    enhancement_enabled = cli_enhance_level > 0
                    enhancement_level = cli_enhance_level

            if enhancement_enabled and enhancement_level > 0:
                logger.info("\n" + "=" * 60)
                logger.info(
                    f"PHASE 6: Enhancing SKILL.md (level {enhancement_level}, mode {enhancement_mode})"
                )
                logger.info("=" * 60)

                skill_md_path = os.path.join(self.output_dir, "SKILL.md")
                if not os.path.exists(skill_md_path):
                    logger.warning("⚠️  SKILL.md not found, skipping enhancement")
                elif enhancement_mode == "LOCAL":
                    try:
                        from skill_seekers.cli.enhance_skill_local import LocalSkillEnhancer

                        # Get agent from ExecutionContext when the CLI initialized
                        # it (already resolved with correct priority); otherwise
                        # fall back to args/env.
                        if ctx_initialized:
                            ctx = ExecutionContext.get()
                            agent = ctx.enhancement.agent
                            agent_cmd = ctx.enhancement.agent_cmd
                        else:
                            agent = None
                            agent_cmd = None
                            if args is not None:
                                agent = getattr(args, "agent", None)
                                agent_cmd = getattr(args, "agent_cmd", None)
                            if not agent:
                                agent = os.environ.get("SKILL_SEEKER_AGENT", "").strip() or None

                        # Prefer the context's resolved timeout (CLI/env/config
                        # already merged) when explicitly initialized; otherwise
                        # honor the raw config block (incl. "unlimited").
                        if ctx_initialized:
                            timeout_val = ExecutionContext.get().enhancement.timeout
                        else:
                            timeout_val = enhancement_config.get("timeout")
                            if timeout_val is not None:
                                if isinstance(timeout_val, str) and timeout_val.lower() in (
                                    "unlimited",
                                    "none",
                                ):
                                    timeout_val = 86400  # 24 hours
                                else:
                                    try:
                                        timeout_val = int(timeout_val)
                                        if timeout_val <= 0:
                                            timeout_val = 86400
                                    except (ValueError, TypeError):
                                        timeout_val = 2700
                            else:
                                timeout_val = 2700

                        enhancer = LocalSkillEnhancer(
                            self.output_dir, force=True, agent=agent, agent_cmd=agent_cmd
                        )
                        success = enhancer.run(headless=True, timeout=timeout_val)
                        agent_name = agent or "claude"
                        if success:
                            logger.info(f"✅ SKILL.md enhanced (LOCAL mode via {agent_name})")
                        else:
                            logger.warning(
                                f"⚠️  SKILL.md enhancement returned false (LOCAL mode via {agent_name}). "
                                "Check logs above for the exact error."
                            )
                    except Exception as e:
                        logger.warning(f"⚠️  LOCAL enhancement failed: {e}")
                        logger.info(
                            "   Try manually: skill-seekers enhance "
                            + self.output_dir
                            + " --agent kimi"
                        )
                else:
                    # API mode — use AgentClient for multi-provider support
                    try:
                        from skill_seekers.cli.agent_client import AgentClient

                        # Forward the context's api_key so a CLI --api-key isn't
                        # dropped (AgentClient would otherwise env-detect only).
                        # get() never raises; a default context just has no key.
                        _api_key = ExecutionContext.get().enhancement.api_key
                        client = AgentClient(mode="api", api_key=_api_key)
                        if client.client:
                            # Read references and current SKILL.md
                            references = ""
                            refs_dir = Path(self.output_dir) / "references"
                            if refs_dir.exists():
                                for md_file in sorted(refs_dir.rglob("*.md")):
                                    content = md_file.read_text(encoding="utf-8", errors="ignore")
                                    references += f"\n\n## {md_file.name}\n\n{content}"
                            current_skill = Path(skill_md_path).read_text(encoding="utf-8")

                            # Build enhancement prompt
                            prompt = (
                                f"Enhance this SKILL.md using the reference documentation.\n\n"
                                f"CURRENT SKILL.MD:\n{current_skill}\n\n"
                                f"REFERENCES:\n{references}\n\n"
                                f"Return ONLY the complete enhanced SKILL.md content, "
                                f"starting with the frontmatter (---)."
                            )
                            enhanced = client.call(prompt, max_tokens=8192)
                            if enhanced:
                                from skill_seekers.cli.adaptors.base import (
                                    save_skill_md_atomic,
                                )

                                save_skill_md_atomic(Path(skill_md_path), enhanced)
                                logger.info(
                                    f"✅ SKILL.md enhanced (API mode via {client.provider})"
                                )
                            else:
                                logger.warning("⚠️  API enhancement returned empty result")
                        else:
                            logger.warning("⚠️  No API key found, skipping API enhancement")
                            logger.info('   Set an API key or use "mode": "LOCAL" in config')
                    except Exception as e:
                        logger.warning(f"⚠️  API enhancement failed: {e}")
            else:
                logger.info("\n" + "=" * 60)
                logger.info("PHASE 6: Enhancement (skipped - not enabled in config)")
                logger.info("=" * 60)

            logger.info("\n" + "✅ " * 20)
            logger.info("Unified scraping complete!")
            logger.info("✅ " * 20 + "\n")

            logger.info(f"📁 Output: {self.output_dir}/")
            logger.info(f"📁 Data: {self.data_dir}/")

            return 0

        except KeyboardInterrupt:
            logger.info("\n\n⚠️  Scraping interrupted by user")
            return 130
        except Exception as e:
            logger.error(f"\n\n❌ Error during scraping: {e}")
            import traceback

            traceback.print_exc()
            return 1
