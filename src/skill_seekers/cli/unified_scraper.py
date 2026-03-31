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

import argparse
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
    from skill_seekers.cli.config_validator import validate_config
    from skill_seekers.cli.conflict_detector import ConflictDetector
    from skill_seekers.cli.merge_sources import AIEnhancedMerger, RuleBasedMerger
    from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder
    from skill_seekers.cli.utils import setup_logging
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

logger = logging.getLogger(__name__)


class UnifiedScraper:
    """
    Orchestrates multi-source scraping and merging.

    Main workflow:
    1. Load and validate unified config
    2. Scrape all sources (docs, GitHub, PDF)
    3. Detect conflicts between sources
    4. Merge intelligently (rule-based or Claude-enhanced)
    5. Build unified skill
    """

    def __init__(self, config_path: str, merge_mode: str | None = None):
        """
        Initialize unified scraper.

        Args:
            config_path: Path to unified config JSON
            merge_mode: Override config merge_mode ('rule-based' or 'claude-enhanced')
        """
        self.config_path = config_path

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
        self.output_dir = f"output/{self.name}"  # Final skill only

        # Use hidden cache directory for intermediate files
        self.cache_dir = f".skillseeker-cache/{self.name}"
        self.sources_dir = f"{self.cache_dir}/sources"
        self.data_dir = f"{self.cache_dir}/data"
        self.repos_dir = f"{self.cache_dir}/repos"
        self.logs_dir = f"{self.cache_dir}/logs"

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
                if source_type == "documentation":
                    self._scrape_documentation(source)
                elif source_type == "github":
                    self._scrape_github(source)
                elif source_type == "pdf":
                    self._scrape_pdf(source)
                elif source_type == "word":
                    self._scrape_word(source)
                elif source_type == "video":
                    self._scrape_video(source)
                elif source_type == "local":
                    self._scrape_local(source)
                elif source_type == "epub":
                    self._scrape_epub(source)
                elif source_type == "jupyter":
                    self._scrape_jupyter(source)
                elif source_type == "html":
                    self._scrape_html(source)
                elif source_type == "openapi":
                    self._scrape_openapi(source)
                elif source_type == "asciidoc":
                    self._scrape_asciidoc(source)
                elif source_type == "pptx":
                    self._scrape_pptx(source)
                elif source_type == "confluence":
                    self._scrape_confluence(source)
                elif source_type == "notion":
                    self._scrape_notion(source)
                elif source_type == "rss":
                    self._scrape_rss(source)
                elif source_type == "manpage":
                    self._scrape_manpage(source)
                elif source_type == "chat":
                    self._scrape_chat(source)
                else:
                    logger.warning(f"Unknown source type: {source_type}")
            except Exception as e:
                logger.error(f"Error scraping {source_type}: {e}")
                logger.info("Continuing with other sources...")

        logger.info(f"\n✅ Scraped {len(self.scraped_data)} sources successfully")

    def _scrape_documentation(self, source: dict[str, Any]):
        """Scrape documentation website."""
        # Create temporary config for doc scraper in unified format
        # (doc_scraper's ConfigValidator requires "sources" key)
        doc_source = {
            "type": "documentation",
            "base_url": source["base_url"],
            "selectors": source.get("selectors", {}),
            "url_patterns": source.get("url_patterns", {}),
            "categories": source.get("categories", {}),
            "rate_limit": source.get("rate_limit", 0.5),
            "max_pages": source.get("max_pages", 100),
        }

        # Pass through llms.txt settings (so unified configs behave the same as doc_scraper configs)
        if "llms_txt_url" in source:
            doc_source["llms_txt_url"] = source["llms_txt_url"]

        if "skip_llms_txt" in source:
            doc_source["skip_llms_txt"] = source["skip_llms_txt"]

        # Optional: support overriding start URLs
        if "start_urls" in source:
            doc_source["start_urls"] = source["start_urls"]

        doc_config = {
            "name": f"{self.name}_docs",
            "description": f"Documentation for {self.name}",
            "base_url": source["base_url"],
            "sources": [doc_source],
        }

        # Write temporary config
        temp_config_path = os.path.join(self.data_dir, "temp_docs_config.json")
        with open(temp_config_path, "w", encoding="utf-8") as f:
            json.dump(doc_config, f, indent=2)

        # Run doc_scraper as subprocess
        logger.info(f"Scraping documentation from {source['base_url']}")

        doc_scraper_path = Path(__file__).parent / "doc_scraper.py"
        cmd = [sys.executable, str(doc_scraper_path), "--config", temp_config_path, "--fresh"]

        # Support "browser": true in source config for JavaScript SPA sites
        if source.get("browser", False):
            cmd.append("--browser")
            logger.info("  🌐 Browser mode enabled (JavaScript rendering via Playwright)")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=3600
            )
        except subprocess.TimeoutExpired:
            logger.error("Documentation scraping timed out after 60 minutes")
            return

        if result.returncode != 0:
            logger.error(f"Documentation scraping failed with return code {result.returncode}")
            logger.error(f"STDERR: {result.stderr}")
            logger.error(f"STDOUT: {result.stdout}")
            return

        # Log subprocess output for debugging
        if result.stdout:
            logger.info(f"Doc scraper output: {result.stdout[-500:]}")  # Last 500 chars

        # Load scraped data
        docs_data_file = f"output/{doc_config['name']}_data/summary.json"

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
                    "refs_dir": "",  # Will be set after moving to cache
                }
            )

            logger.info(f"✅ Documentation: {summary.get('total_pages', 0)} pages scraped")
        else:
            logger.warning("Documentation data file not found")

        # Clean up temp config
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)

        # Move intermediate files to cache to keep output/ clean
        docs_output_dir = f"output/{doc_config['name']}"
        docs_data_dir = f"output/{doc_config['name']}_data"

        if os.path.exists(docs_output_dir):
            cache_docs_dir = os.path.join(self.sources_dir, f"{doc_config['name']}")
            if os.path.exists(cache_docs_dir):
                shutil.rmtree(cache_docs_dir)
            shutil.move(docs_output_dir, cache_docs_dir)
            logger.info(f"📦 Moved docs output to cache: {cache_docs_dir}")

            # Update refs_dir in scraped_data with cache location
            refs_dir_path = os.path.join(cache_docs_dir, "references")
            if self.scraped_data["documentation"]:
                self.scraped_data["documentation"][-1]["refs_dir"] = refs_dir_path

        if os.path.exists(docs_data_dir):
            cache_data_dir = os.path.join(self.data_dir, f"{doc_config['name']}_data")
            if os.path.exists(cache_data_dir):
                shutil.rmtree(cache_data_dir)
            shutil.move(docs_data_dir, cache_data_dir)
            logger.info(f"📦 Moved docs data to cache: {cache_data_dir}")

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
                timeout=600,  # 10 minute timeout for full clone
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
            "local_repo_path": local_repo_path,  # Use cloned path if available
        }

        # Pass directory exclusions if specified (optional)
        if "exclude_dirs" in source:
            github_config["exclude_dirs"] = source["exclude_dirs"]
        if "exclude_dirs_additional" in source:
            github_config["exclude_dirs_additional"] = source["exclude_dirs_additional"]

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

        # ALSO save to the location GitHubToSkillConverter expects (with C3.x data!)
        converter_data_file = f"output/{github_config['name']}_github_data.json"
        with open(converter_data_file, "w", encoding="utf-8") as f:
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

        # Build standalone SKILL.md for synthesis using GitHubToSkillConverter
        try:
            from skill_seekers.cli.github_scraper import GitHubToSkillConverter

            # Use github_config which has the correct name field
            # Converter will load from output/{name}_github_data.json which now has C3.x data
            converter = GitHubToSkillConverter(config=github_config)
            converter.build_skill()
            logger.info("✅ GitHub: Standalone SKILL.md created")
        except Exception as e:
            logger.warning(f"⚠️  Failed to build standalone GitHub SKILL.md: {e}")

        # Move intermediate files to cache to keep output/ clean
        github_output_dir = f"output/{github_config['name']}"
        github_data_file_path = f"output/{github_config['name']}_github_data.json"

        if os.path.exists(github_output_dir):
            cache_github_dir = os.path.join(self.sources_dir, github_config["name"])
            if os.path.exists(cache_github_dir):
                shutil.rmtree(cache_github_dir)
            shutil.move(github_output_dir, cache_github_dir)
            logger.info(f"📦 Moved GitHub output to cache: {cache_github_dir}")

        if os.path.exists(github_data_file_path):
            cache_github_data = os.path.join(
                self.data_dir, f"{github_config['name']}_github_data.json"
            )
            if os.path.exists(cache_github_data):
                os.remove(cache_github_data)
            shutil.move(github_data_file_path, cache_github_data)
            logger.info(f"📦 Moved GitHub data to cache: {cache_github_data}")

        logger.info("✅ GitHub: Repository scraped successfully")

    def _scrape_pdf(self, source: dict[str, Any]):
        """Scrape PDF document."""
        try:
            from skill_seekers.cli.pdf_scraper import PDFToSkillConverter
        except ImportError:
            logger.error("pdf_scraper.py not found")
            return

        # Multi-source support: Get unique index for this PDF source
        idx = self._source_counters["pdf"]
        self._source_counters["pdf"] += 1

        # Extract PDF identifier for unique naming (filename without extension)
        pdf_path = source["path"]
        pdf_id = os.path.splitext(os.path.basename(pdf_path))[0]

        # Create config for PDF scraper
        pdf_config = {
            "name": f"{self.name}_pdf_{idx}_{pdf_id}",
            "pdf_path": source["path"],  # Fixed: use pdf_path instead of pdf
            "description": f"{source.get('name', pdf_id)} documentation",
            "extract_tables": source.get("extract_tables", False),
            "ocr": source.get("ocr", False),
            "password": source.get("password"),
        }

        # Scrape
        logger.info(f"Scraping PDF: {source['path']}")
        converter = PDFToSkillConverter(pdf_config)

        # Extract PDF content
        converter.extract_pdf()

        # Load extracted data from file
        pdf_data_file = converter.data_file
        with open(pdf_data_file, encoding="utf-8") as f:
            pdf_data = json.load(f)

        # Copy data file to cache
        cache_pdf_data = os.path.join(self.data_dir, f"pdf_data_{idx}_{pdf_id}.json")
        shutil.copy(pdf_data_file, cache_pdf_data)

        # Append to list instead of overwriting
        self.scraped_data["pdf"].append(
            {
                "pdf_path": pdf_path,
                "pdf_id": pdf_id,
                "idx": idx,
                "data": pdf_data,
                "data_file": cache_pdf_data,
            }
        )

        # Build standalone SKILL.md for synthesis
        try:
            converter.build_skill()
            logger.info("✅ PDF: Standalone SKILL.md created")
        except Exception as e:
            logger.warning(f"⚠️  Failed to build standalone PDF SKILL.md: {e}")

        logger.info(f"✅ PDF: {len(pdf_data.get('pages', []))} pages extracted")

    def _scrape_word(self, source: dict[str, Any]):
        """Scrape Word document (.docx)."""
        try:
            from skill_seekers.cli.word_scraper import WordToSkillConverter
        except ImportError:
            logger.error("word_scraper.py not found")
            return

        # Multi-source support: Get unique index for this Word source
        idx = self._source_counters["word"]
        self._source_counters["word"] += 1

        # Extract Word identifier for unique naming (filename without extension)
        docx_path = source["path"]
        docx_id = os.path.splitext(os.path.basename(docx_path))[0]

        # Create config for Word scraper
        word_config = {
            "name": f"{self.name}_word_{idx}_{docx_id}",
            "docx_path": source["path"],
            "description": f"{source.get('name', docx_id)} documentation",
        }

        # Scrape
        logger.info(f"Scraping Word document: {source['path']}")
        converter = WordToSkillConverter(word_config)

        # Extract Word content
        converter.extract_docx()

        # Load extracted data from file
        word_data_file = converter.data_file
        with open(word_data_file, encoding="utf-8") as f:
            word_data = json.load(f)

        # Copy data file to cache
        cache_word_data = os.path.join(self.data_dir, f"word_data_{idx}_{docx_id}.json")
        shutil.copy(word_data_file, cache_word_data)

        # Append to list
        self.scraped_data["word"].append(
            {
                "docx_path": docx_path,
                "docx_id": docx_id,
                "word_id": docx_id,  # Alias for generic reference generation
                "idx": idx,
                "data": word_data,
                "data_file": cache_word_data,
            }
        )

        # Build standalone SKILL.md for synthesis
        try:
            converter.build_skill()
            logger.info("✅ Word: Standalone SKILL.md created")
        except Exception as e:
            logger.warning(f"⚠️  Failed to build standalone Word SKILL.md: {e}")

        logger.info(f"✅ Word: {len(word_data.get('pages', []))} sections extracted")

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

        # Process video
        logger.info(f"Scraping video: {video_id}")
        converter = VideoToSkillConverter(video_config)

        try:
            result = converter.process()
            converter.save_extracted_data()

            # Append to list
            self.scraped_data["video"].append(
                {
                    "video_id": video_id,
                    "idx": idx,
                    "data": result.to_dict(),
                    "data_file": converter.data_file,
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

            # Load analysis outputs into memory
            local_data = {
                "source_id": f"{self.name}_local_{idx}_{path_id}",
                "path": local_path,
                "name": source_name,
                "description": source.get("description", f"Local analysis of {path_id}"),
                "weight": source.get("weight", 1.0),
                "patterns": self._load_json(temp_output / "patterns" / "detected_patterns.json"),
                "test_examples": self._load_json(
                    temp_output / "test_examples" / "test_examples.json"
                ),
                "how_to_guides": self._load_guide_collection(temp_output / "tutorials"),
                "config_patterns": self._load_json(
                    temp_output / "config_patterns" / "config_patterns.json"
                ),
                "architecture": self._load_json(temp_output / "ARCHITECTURE.json"),
                "api_reference": self._load_api_reference(temp_output / "api_reference"),
                "dependency_graph": self._load_json(
                    temp_output / "dependencies" / "dependency_graph.json"
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
        try:
            from skill_seekers.cli.epub_scraper import EpubToSkillConverter
        except ImportError:
            logger.error(
                "EPUB scraper dependencies not installed.\n"
                "  Install with: pip install skill-seekers[epub]"
            )
            return

        idx = self._source_counters["epub"]
        self._source_counters["epub"] += 1

        epub_path = source["path"]
        epub_id = os.path.splitext(os.path.basename(epub_path))[0]

        epub_config = {
            "name": f"{self.name}_epub_{idx}_{epub_id}",
            "epub_path": source["path"],
            "description": source.get("description", f"{epub_id} e-book"),
        }

        logger.info(f"Scraping EPUB: {source['path']}")
        converter = EpubToSkillConverter(epub_config)
        converter.extract_epub()

        epub_data_file = converter.data_file
        with open(epub_data_file, encoding="utf-8") as f:
            epub_data = json.load(f)

        cache_epub_data = os.path.join(self.data_dir, f"epub_data_{idx}_{epub_id}.json")
        shutil.copy(epub_data_file, cache_epub_data)

        self.scraped_data["epub"].append(
            {
                "epub_path": epub_path,
                "epub_id": epub_id,
                "idx": idx,
                "data": epub_data,
                "data_file": cache_epub_data,
            }
        )

        try:
            converter.build_skill()
            logger.info("✅ EPUB: Standalone SKILL.md created")
        except Exception as e:
            logger.warning(f"⚠️  Failed to build standalone EPUB SKILL.md: {e}")

        logger.info(f"✅ EPUB: {len(epub_data.get('chapters', []))} chapters extracted")

    def _scrape_jupyter(self, source: dict[str, Any]):
        """Scrape Jupyter Notebook (.ipynb)."""
        try:
            from skill_seekers.cli.jupyter_scraper import JupyterToSkillConverter
        except ImportError:
            logger.error(
                "Jupyter scraper dependencies not installed.\n"
                "  Install with: pip install skill-seekers[jupyter]"
            )
            return

        idx = self._source_counters["jupyter"]
        self._source_counters["jupyter"] += 1

        nb_path = source["path"]
        nb_id = os.path.splitext(os.path.basename(nb_path))[0]

        nb_config = {
            "name": f"{self.name}_jupyter_{idx}_{nb_id}",
            "notebook_path": source["path"],
            "description": source.get("description", f"{nb_id} notebook"),
        }

        logger.info(f"Scraping Jupyter Notebook: {source['path']}")
        converter = JupyterToSkillConverter(nb_config)
        converter.extract_notebook()

        nb_data_file = converter.data_file
        with open(nb_data_file, encoding="utf-8") as f:
            nb_data = json.load(f)

        cache_nb_data = os.path.join(self.data_dir, f"jupyter_data_{idx}_{nb_id}.json")
        shutil.copy(nb_data_file, cache_nb_data)

        self.scraped_data["jupyter"].append(
            {
                "notebook_path": nb_path,
                "notebook_id": nb_id,
                "idx": idx,
                "data": nb_data,
                "data_file": cache_nb_data,
            }
        )

        try:
            converter.build_skill()
            logger.info("✅ Jupyter: Standalone SKILL.md created")
        except Exception as e:
            logger.warning(f"⚠️  Failed to build standalone Jupyter SKILL.md: {e}")

        logger.info(f"✅ Jupyter: {len(nb_data.get('cells', []))} cells extracted")

    def _scrape_html(self, source: dict[str, Any]):
        """Scrape local HTML file(s)."""
        try:
            from skill_seekers.cli.html_scraper import HtmlToSkillConverter
        except ImportError:
            logger.error("html_scraper.py not found")
            return

        idx = self._source_counters["html"]
        self._source_counters["html"] += 1

        html_path = source["path"]
        html_id = os.path.splitext(os.path.basename(html_path.rstrip("/")))[0]

        html_config = {
            "name": f"{self.name}_html_{idx}_{html_id}",
            "html_path": source["path"],
            "description": source.get("description", f"{html_id} HTML content"),
        }

        logger.info(f"Scraping local HTML: {source['path']}")
        converter = HtmlToSkillConverter(html_config)
        converter.extract_html()

        html_data_file = converter.data_file
        with open(html_data_file, encoding="utf-8") as f:
            html_data = json.load(f)

        cache_html_data = os.path.join(self.data_dir, f"html_data_{idx}_{html_id}.json")
        shutil.copy(html_data_file, cache_html_data)

        self.scraped_data["html"].append(
            {
                "html_path": html_path,
                "html_id": html_id,
                "idx": idx,
                "data": html_data,
                "data_file": cache_html_data,
            }
        )

        try:
            converter.build_skill()
            logger.info("✅ HTML: Standalone SKILL.md created")
        except Exception as e:
            logger.warning(f"⚠️  Failed to build standalone HTML SKILL.md: {e}")

        logger.info(f"✅ HTML: {len(html_data.get('pages', []))} pages extracted")

    def _scrape_openapi(self, source: dict[str, Any]):
        """Scrape OpenAPI/Swagger specification."""
        try:
            from skill_seekers.cli.openapi_scraper import OpenAPIToSkillConverter
        except ImportError:
            logger.error("openapi_scraper.py not found")
            return

        idx = self._source_counters["openapi"]
        self._source_counters["openapi"] += 1

        spec_path = source.get("path", source.get("url", ""))
        spec_id = os.path.splitext(os.path.basename(spec_path))[0] if spec_path else f"spec_{idx}"

        openapi_config = {
            "name": f"{self.name}_openapi_{idx}_{spec_id}",
            "spec_path": source.get("path"),
            "spec_url": source.get("url"),
            "description": source.get("description", f"{spec_id} API spec"),
        }

        logger.info(f"Scraping OpenAPI spec: {spec_path}")
        converter = OpenAPIToSkillConverter(openapi_config)
        converter.extract_spec()

        api_data_file = converter.data_file
        with open(api_data_file, encoding="utf-8") as f:
            api_data = json.load(f)

        cache_api_data = os.path.join(self.data_dir, f"openapi_data_{idx}_{spec_id}.json")
        shutil.copy(api_data_file, cache_api_data)

        self.scraped_data["openapi"].append(
            {
                "spec_path": spec_path,
                "spec_id": spec_id,
                "idx": idx,
                "data": api_data,
                "data_file": cache_api_data,
            }
        )

        try:
            converter.build_skill()
            logger.info("✅ OpenAPI: Standalone SKILL.md created")
        except Exception as e:
            logger.warning(f"⚠️  Failed to build standalone OpenAPI SKILL.md: {e}")

        logger.info(f"✅ OpenAPI: {len(api_data.get('endpoints', []))} endpoints extracted")

    def _scrape_asciidoc(self, source: dict[str, Any]):
        """Scrape AsciiDoc document(s)."""
        try:
            from skill_seekers.cli.asciidoc_scraper import AsciiDocToSkillConverter
        except ImportError:
            logger.error(
                "AsciiDoc scraper dependencies not installed.\n"
                "  Install with: pip install skill-seekers[asciidoc]"
            )
            return

        idx = self._source_counters["asciidoc"]
        self._source_counters["asciidoc"] += 1

        adoc_path = source["path"]
        adoc_id = os.path.splitext(os.path.basename(adoc_path.rstrip("/")))[0]

        adoc_config = {
            "name": f"{self.name}_asciidoc_{idx}_{adoc_id}",
            "asciidoc_path": source["path"],
            "description": source.get("description", f"{adoc_id} AsciiDoc content"),
        }

        logger.info(f"Scraping AsciiDoc: {source['path']}")
        converter = AsciiDocToSkillConverter(adoc_config)
        converter.extract_asciidoc()

        adoc_data_file = converter.data_file
        with open(adoc_data_file, encoding="utf-8") as f:
            adoc_data = json.load(f)

        cache_adoc_data = os.path.join(self.data_dir, f"asciidoc_data_{idx}_{adoc_id}.json")
        shutil.copy(adoc_data_file, cache_adoc_data)

        self.scraped_data["asciidoc"].append(
            {
                "asciidoc_path": adoc_path,
                "asciidoc_id": adoc_id,
                "idx": idx,
                "data": adoc_data,
                "data_file": cache_adoc_data,
            }
        )

        try:
            converter.build_skill()
            logger.info("✅ AsciiDoc: Standalone SKILL.md created")
        except Exception as e:
            logger.warning(f"⚠️  Failed to build standalone AsciiDoc SKILL.md: {e}")

        logger.info(f"✅ AsciiDoc: {len(adoc_data.get('sections', []))} sections extracted")

    def _scrape_pptx(self, source: dict[str, Any]):
        """Scrape PowerPoint presentation (.pptx)."""
        try:
            from skill_seekers.cli.pptx_scraper import PptxToSkillConverter
        except ImportError:
            logger.error(
                "PowerPoint scraper dependencies not installed.\n"
                "  Install with: pip install skill-seekers[pptx]"
            )
            return

        idx = self._source_counters["pptx"]
        self._source_counters["pptx"] += 1

        pptx_path = source["path"]
        pptx_id = os.path.splitext(os.path.basename(pptx_path))[0]

        pptx_config = {
            "name": f"{self.name}_pptx_{idx}_{pptx_id}",
            "pptx_path": source["path"],
            "description": source.get("description", f"{pptx_id} presentation"),
        }

        logger.info(f"Scraping PowerPoint: {source['path']}")
        converter = PptxToSkillConverter(pptx_config)
        converter.extract_pptx()

        pptx_data_file = converter.data_file
        with open(pptx_data_file, encoding="utf-8") as f:
            pptx_data = json.load(f)

        cache_pptx_data = os.path.join(self.data_dir, f"pptx_data_{idx}_{pptx_id}.json")
        shutil.copy(pptx_data_file, cache_pptx_data)

        self.scraped_data["pptx"].append(
            {
                "pptx_path": pptx_path,
                "pptx_id": pptx_id,
                "idx": idx,
                "data": pptx_data,
                "data_file": cache_pptx_data,
            }
        )

        try:
            converter.build_skill()
            logger.info("✅ PowerPoint: Standalone SKILL.md created")
        except Exception as e:
            logger.warning(f"⚠️  Failed to build standalone PowerPoint SKILL.md: {e}")

        logger.info(f"✅ PowerPoint: {len(pptx_data.get('slides', []))} slides extracted")

    def _scrape_confluence(self, source: dict[str, Any]):
        """Scrape Confluence wiki (API or exported HTML/XML)."""
        try:
            from skill_seekers.cli.confluence_scraper import ConfluenceToSkillConverter
        except ImportError:
            logger.error(
                "Confluence scraper dependencies not installed.\n"
                "  Install with: pip install skill-seekers[confluence]"
            )
            return

        idx = self._source_counters["confluence"]
        self._source_counters["confluence"] += 1

        source_id = source.get("space_key", source.get("path", f"confluence_{idx}"))
        if isinstance(source_id, str) and "/" in source_id:
            source_id = os.path.basename(source_id.rstrip("/"))

        conf_config = {
            "name": f"{self.name}_confluence_{idx}_{source_id}",
            "base_url": source.get("base_url", source.get("url")),
            "space_key": source.get("space_key"),
            "export_path": source.get("path"),
            "username": source.get("username"),
            "token": source.get("token"),
            "description": source.get("description", f"{source_id} Confluence content"),
            "max_pages": source.get("max_pages", 500),
        }

        logger.info(f"Scraping Confluence: {source_id}")
        converter = ConfluenceToSkillConverter(conf_config)
        converter.extract_confluence()

        conf_data_file = converter.data_file
        with open(conf_data_file, encoding="utf-8") as f:
            conf_data = json.load(f)

        cache_conf_data = os.path.join(self.data_dir, f"confluence_data_{idx}_{source_id}.json")
        shutil.copy(conf_data_file, cache_conf_data)

        self.scraped_data["confluence"].append(
            {
                "source_id": source_id,
                "idx": idx,
                "data": conf_data,
                "data_file": cache_conf_data,
            }
        )

        try:
            converter.build_skill()
            logger.info("✅ Confluence: Standalone SKILL.md created")
        except Exception as e:
            logger.warning(f"⚠️  Failed to build standalone Confluence SKILL.md: {e}")

        logger.info(f"✅ Confluence: {len(conf_data.get('pages', []))} pages extracted")

    def _scrape_notion(self, source: dict[str, Any]):
        """Scrape Notion pages (API or exported Markdown)."""
        try:
            from skill_seekers.cli.notion_scraper import NotionToSkillConverter
        except ImportError:
            logger.error(
                "Notion scraper dependencies not installed.\n"
                "  Install with: pip install skill-seekers[notion]"
            )
            return

        idx = self._source_counters["notion"]
        self._source_counters["notion"] += 1

        source_id = source.get(
            "database_id", source.get("page_id", source.get("path", f"notion_{idx}"))
        )
        if isinstance(source_id, str) and "/" in source_id:
            source_id = os.path.basename(source_id.rstrip("/"))

        notion_config = {
            "name": f"{self.name}_notion_{idx}_{source_id}",
            "database_id": source.get("database_id"),
            "page_id": source.get("page_id"),
            "export_path": source.get("path"),
            "token": source.get("token"),
            "description": source.get("description", f"{source_id} Notion content"),
            "max_pages": source.get("max_pages", 500),
        }

        logger.info(f"Scraping Notion: {source_id}")
        converter = NotionToSkillConverter(notion_config)
        converter.extract_notion()

        notion_data_file = converter.data_file
        with open(notion_data_file, encoding="utf-8") as f:
            notion_data = json.load(f)

        cache_notion_data = os.path.join(self.data_dir, f"notion_data_{idx}_{source_id}.json")
        shutil.copy(notion_data_file, cache_notion_data)

        self.scraped_data["notion"].append(
            {
                "source_id": source_id,
                "idx": idx,
                "data": notion_data,
                "data_file": cache_notion_data,
            }
        )

        try:
            converter.build_skill()
            logger.info("✅ Notion: Standalone SKILL.md created")
        except Exception as e:
            logger.warning(f"⚠️  Failed to build standalone Notion SKILL.md: {e}")

        logger.info(f"✅ Notion: {len(notion_data.get('pages', []))} pages extracted")

    def _scrape_rss(self, source: dict[str, Any]):
        """Scrape RSS/Atom feed (with optional full article scraping)."""
        try:
            from skill_seekers.cli.rss_scraper import RssToSkillConverter
        except ImportError:
            logger.error(
                "RSS scraper dependencies not installed.\n"
                "  Install with: pip install skill-seekers[rss]"
            )
            return

        idx = self._source_counters["rss"]
        self._source_counters["rss"] += 1

        feed_url = source.get("url", source.get("path", ""))
        feed_id = feed_url.split("/")[-1].split(".")[0] if feed_url else f"feed_{idx}"

        rss_config = {
            "name": f"{self.name}_rss_{idx}_{feed_id}",
            "feed_url": source.get("url"),
            "feed_path": source.get("path"),
            "follow_links": source.get("follow_links", True),
            "max_articles": source.get("max_articles", 50),
            "description": source.get("description", f"{feed_id} RSS/Atom feed"),
        }

        logger.info(f"Scraping RSS/Atom feed: {feed_url}")
        converter = RssToSkillConverter(rss_config)
        converter.extract_feed()

        rss_data_file = converter.data_file
        with open(rss_data_file, encoding="utf-8") as f:
            rss_data = json.load(f)

        cache_rss_data = os.path.join(self.data_dir, f"rss_data_{idx}_{feed_id}.json")
        shutil.copy(rss_data_file, cache_rss_data)

        self.scraped_data["rss"].append(
            {
                "feed_url": feed_url,
                "feed_id": feed_id,
                "idx": idx,
                "data": rss_data,
                "data_file": cache_rss_data,
            }
        )

        try:
            converter.build_skill()
            logger.info("✅ RSS: Standalone SKILL.md created")
        except Exception as e:
            logger.warning(f"⚠️  Failed to build standalone RSS SKILL.md: {e}")

        logger.info(f"✅ RSS: {len(rss_data.get('articles', []))} articles extracted")

    def _scrape_manpage(self, source: dict[str, Any]):
        """Scrape man page(s)."""
        try:
            from skill_seekers.cli.man_scraper import ManPageToSkillConverter
        except ImportError:
            logger.error("man_scraper.py not found")
            return

        idx = self._source_counters["manpage"]
        self._source_counters["manpage"] += 1

        man_names = source.get("names", [])
        man_path = source.get("path", "")
        man_id = man_names[0] if man_names else os.path.basename(man_path.rstrip("/"))

        man_config = {
            "name": f"{self.name}_manpage_{idx}_{man_id}",
            "man_names": man_names,
            "man_path": man_path,
            "sections": source.get("sections", []),
            "description": source.get("description", f"{man_id} man pages"),
        }

        logger.info(f"Scraping man pages: {man_id}")
        converter = ManPageToSkillConverter(man_config)
        converter.extract_manpages()

        man_data_file = converter.data_file
        with open(man_data_file, encoding="utf-8") as f:
            man_data = json.load(f)

        cache_man_data = os.path.join(self.data_dir, f"manpage_data_{idx}_{man_id}.json")
        shutil.copy(man_data_file, cache_man_data)

        self.scraped_data["manpage"].append(
            {
                "man_id": man_id,
                "idx": idx,
                "data": man_data,
                "data_file": cache_man_data,
            }
        )

        try:
            converter.build_skill()
            logger.info("✅ Man pages: Standalone SKILL.md created")
        except Exception as e:
            logger.warning(f"⚠️  Failed to build standalone man page SKILL.md: {e}")

        logger.info(f"✅ Man pages: {len(man_data.get('pages', []))} man pages extracted")

    def _scrape_chat(self, source: dict[str, Any]):
        """Scrape Slack/Discord chat export or API."""
        try:
            from skill_seekers.cli.chat_scraper import ChatToSkillConverter
        except ImportError:
            logger.error(
                "Chat scraper dependencies not installed.\n"
                "  Install with: pip install skill-seekers[chat]"
            )
            return

        idx = self._source_counters["chat"]
        self._source_counters["chat"] += 1

        export_path = source.get("path", "")
        channel = source.get("channel", source.get("channel_id", ""))
        chat_id = channel or os.path.basename(export_path.rstrip("/")) or f"chat_{idx}"

        chat_config = {
            "name": f"{self.name}_chat_{idx}_{chat_id}",
            "export_path": source.get("path"),
            "platform": source.get("platform", "slack"),
            "token": source.get("token"),
            "channel": channel,
            "max_messages": source.get("max_messages", 10000),
            "description": source.get("description", f"{chat_id} chat export"),
        }

        logger.info(f"Scraping chat: {chat_id}")
        converter = ChatToSkillConverter(chat_config)
        converter.extract_chat()

        chat_data_file = converter.data_file
        with open(chat_data_file, encoding="utf-8") as f:
            chat_data = json.load(f)

        cache_chat_data = os.path.join(self.data_dir, f"chat_data_{idx}_{chat_id}.json")
        shutil.copy(chat_data_file, cache_chat_data)

        self.scraped_data["chat"].append(
            {
                "chat_id": chat_id,
                "platform": source.get("platform", "slack"),
                "idx": idx,
                "data": chat_data,
                "data_file": cache_chat_data,
            }
        )

        try:
            converter.build_skill()
            logger.info("✅ Chat: Standalone SKILL.md created")
        except Exception as e:
            logger.warning(f"⚠️  Failed to build standalone chat SKILL.md: {e}")

        logger.info(f"✅ Chat: {len(chat_data.get('messages', []))} messages extracted")

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

        Args:
            tutorials_dir: Path to tutorials directory

        Returns:
            Dict with guide collection data
        """
        if not tutorials_dir.exists():
            logger.warning(f"Tutorials directory not found: {tutorials_dir}")
            return {"guides": []}

        collection_file = tutorials_dir / "guide_collection.json"
        if collection_file.exists():
            return self._load_json(collection_file)

        # Fallback: scan for individual guide JSON files
        guides = []
        for guide_file in tutorials_dir.glob("guide_*.json"):
            guide_data = self._load_json(guide_file)
            if guide_data:
                guides.append(guide_data)

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
            # Run full C3.x analysis
            _results = analyze_codebase(
                directory=Path(local_repo_path),
                output_dir=temp_output,
                depth="deep",
                languages=None,  # Analyze all languages
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
            )

            # Load C3.x outputs into memory
            c3_data = {
                "patterns": self._load_json(temp_output / "patterns" / "detected_patterns.json"),
                "test_examples": self._load_json(
                    temp_output / "test_examples" / "test_examples.json"
                ),
                "how_to_guides": self._load_guide_collection(temp_output / "tutorials"),
                "config_patterns": self._load_json(
                    temp_output / "config_patterns" / "config_patterns.json"
                ),
                "architecture": self._load_json(
                    temp_output / "architecture" / "architectural_patterns.json"
                ),
                "api_reference": self._load_api_reference(temp_output / "api_reference"),  # C2.5
                "dependency_graph": self._load_json(
                    temp_output / "dependencies" / "dependency_graph.json"
                ),  # C2.6
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

        # Load data files
        with open(docs_data["data_file"], encoding="utf-8") as f:
            docs_json = json.load(f)

        with open(github_data["data_file"], encoding="utf-8") as f:
            github_json = json.load(f)

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

        docs_data = docs_list[0]
        github_data = github_list[0]

        # Load data
        with open(docs_data["data_file"], encoding="utf-8") as f:
            docs_json = json.load(f)

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

        try:
            # Phase 1: Scrape all sources
            self.scrape_all_sources()

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
            # Triggered by config "enhancement" block or CLI --enhance-level
            enhancement_config = self.config.get("enhancement", {})
            enhancement_enabled = enhancement_config.get("enabled", False)
            enhancement_level = enhancement_config.get("level", 0)
            enhancement_mode = enhancement_config.get("mode", "AUTO").upper()

            # CLI --enhance-level overrides config
            cli_enhance_level = getattr(args, "enhance_level", None) if args is not None else None
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

                        # Get agent from CLI args, config enhancement block, or env var
                        agent = None
                        agent_cmd = None
                        if args is not None:
                            agent = getattr(args, "agent", None)
                            agent_cmd = getattr(args, "agent_cmd", None)
                        if not agent:
                            agent = enhancement_config.get("agent", None)
                        if not agent:
                            agent = os.environ.get("SKILL_SEEKER_AGENT", "").strip() or None

                        enhancer = LocalSkillEnhancer(
                            self.output_dir, force=True, agent=agent, agent_cmd=agent_cmd
                        )
                        enhancer.run(headless=True, timeout=1000)
                        agent_name = agent or "claude"
                        logger.info(f"✅ SKILL.md enhanced (LOCAL mode via {agent_name})")
                    except Exception as e:
                        logger.warning(f"⚠️  LOCAL enhancement failed: {e}")
                        logger.info(
                            "   Try manually: skill-seekers enhance "
                            + self.output_dir
                            + " --agent kimi"
                        )
                else:
                    # API mode
                    try:
                        from skill_seekers.cli.enhance_skill import SkillEnhancer

                        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
                        if api_key:
                            enhancer = SkillEnhancer(self.output_dir, api_key=api_key)
                            # Read references from output dir
                            references = ""
                            refs_dir = Path(self.output_dir) / "references"
                            if refs_dir.exists():
                                for md_file in sorted(refs_dir.rglob("*.md")):
                                    content = md_file.read_text(encoding="utf-8", errors="ignore")
                                    references += f"\n\n## {md_file.name}\n\n{content}"
                            current_skill = enhancer.read_current_skill_md()
                            enhanced = enhancer.enhance_skill_md(references, current_skill)
                            if enhanced:
                                shutil.copy2(skill_md_path, skill_md_path + ".backup")
                                Path(skill_md_path).write_text(enhanced, encoding="utf-8")
                                logger.info("✅ SKILL.md enhanced (API mode)")
                            else:
                                logger.warning("⚠️  API enhancement returned empty result")
                        else:
                            logger.warning("⚠️  ANTHROPIC_API_KEY not set, skipping API enhancement")
                            logger.info('   Set ANTHROPIC_API_KEY or use "mode": "LOCAL" in config')
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

        except KeyboardInterrupt:
            logger.info("\n\n⚠️  Scraping interrupted by user")
            sys.exit(1)
        except Exception as e:
            logger.error(f"\n\n❌ Error during scraping: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Unified multi-source scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with unified config
  skill-seekers unified --config configs/godot_unified.json

  # Override merge mode
  skill-seekers unified --config configs/react_unified.json --merge-mode ai-enhanced

  # Backward compatible with legacy configs
  skill-seekers unified --config configs/react.json
        """,
    )

    parser.add_argument("--config", "-c", required=True, help="Path to unified config JSON file")
    parser.add_argument(
        "--merge-mode",
        "-m",
        choices=["rule-based", "ai-enhanced", "claude-enhanced"],
        help="Override config merge mode (ai-enhanced or rule-based). 'claude-enhanced' accepted as alias.",
    )
    parser.add_argument(
        "--skip-codebase-analysis",
        action="store_true",
        help="Skip C3.x codebase analysis for GitHub sources (default: enabled)",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Clear any existing data and start fresh (ignore checkpoints)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what will be scraped without actually scraping",
    )
    # Enhancement Workflow arguments (mirrors scrape/github/pdf/codebase scrapers)
    parser.add_argument(
        "--enhance-workflow",
        action="append",
        dest="enhance_workflow",
        help="Apply enhancement workflow (file path or preset). Can use multiple times to chain workflows.",
        metavar="WORKFLOW",
    )
    parser.add_argument(
        "--enhance-stage",
        action="append",
        dest="enhance_stage",
        help="Add inline enhancement stage (format: 'name:prompt'). Can be used multiple times.",
        metavar="STAGE",
    )
    parser.add_argument(
        "--var",
        action="append",
        dest="var",
        help="Override workflow variable (format: 'key=value'). Can be used multiple times.",
        metavar="VAR",
    )
    parser.add_argument(
        "--workflow-dry-run",
        action="store_true",
        dest="workflow_dry_run",
        help="Preview workflow stages without executing (requires --enhance-workflow)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        metavar="KEY",
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)",
    )
    parser.add_argument(
        "--enhance-level",
        type=int,
        choices=[0, 1, 2, 3],
        default=None,
        metavar="LEVEL",
        help=(
            "Global AI enhancement level override for all sources "
            "(0=off, 1=SKILL.md, 2=+arch/config, 3=full). "
            "Overrides per-source enhance_level in config."
        ),
    )

    args = parser.parse_args()
    setup_logging()

    # Create scraper
    scraper = UnifiedScraper(args.config, args.merge_mode)

    # Disable codebase analysis if requested
    if args.skip_codebase_analysis:
        for source in scraper.config.get("sources", []):
            if source["type"] == "github":
                source["enable_codebase_analysis"] = False
                logger.info(
                    f"⏭️  Skipping codebase analysis for GitHub source: {source.get('repo', 'unknown')}"
                )

    # Handle --fresh flag (clear cache)
    if args.fresh:
        import shutil

        if os.path.exists(scraper.cache_dir):
            logger.info(f"🧹 Clearing cache: {scraper.cache_dir}")
            shutil.rmtree(scraper.cache_dir)
            # Recreate directories
            os.makedirs(scraper.sources_dir, exist_ok=True)
            os.makedirs(scraper.data_dir, exist_ok=True)
            os.makedirs(scraper.repos_dir, exist_ok=True)
            os.makedirs(scraper.logs_dir, exist_ok=True)

    # Handle --dry-run flag
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - Preview only, no scraping will occur")
        logger.info(f"\nWould scrape {len(scraper.config.get('sources', []))} sources:")
        # Source type display config: type -> (label, key for detail)
        _SOURCE_DISPLAY = {
            "documentation": ("Documentation", "base_url"),
            "github": ("GitHub", "repo"),
            "pdf": ("PDF", "path"),
            "word": ("Word", "path"),
            "epub": ("EPUB", "path"),
            "video": ("Video", "url"),
            "local": ("Local Codebase", "path"),
            "jupyter": ("Jupyter Notebook", "path"),
            "html": ("HTML", "path"),
            "openapi": ("OpenAPI Spec", "path"),
            "asciidoc": ("AsciiDoc", "path"),
            "pptx": ("PowerPoint", "path"),
            "confluence": ("Confluence", "base_url"),
            "notion": ("Notion", "page_id"),
            "rss": ("RSS/Atom Feed", "url"),
            "manpage": ("Man Page", "names"),
            "chat": ("Chat Export", "path"),
        }
        for idx, source in enumerate(scraper.config.get("sources", []), 1):
            source_type = source.get("type", "unknown")
            label, key = _SOURCE_DISPLAY.get(source_type, (source_type.title(), "path"))
            detail = source.get(key, "N/A")
            if isinstance(detail, list):
                detail = ", ".join(str(d) for d in detail)
            logger.info(f"  {idx}. {label}: {detail}")
        logger.info(f"\nOutput directory: {scraper.output_dir}")
        logger.info(f"Merge mode: {scraper.merge_mode}")
        return

    # Run scraper (pass args for workflow integration)
    scraper.run(args=args)


if __name__ == "__main__":
    main()
