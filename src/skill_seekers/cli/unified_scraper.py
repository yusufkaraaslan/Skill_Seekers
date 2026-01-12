#!/usr/bin/env python3
"""
Unified Multi-Source Scraper

Orchestrates scraping from multiple sources (documentation, GitHub, PDF),
detects conflicts, merges intelligently, and builds unified skills.

This is the main entry point for unified config workflow.

Usage:
    skill-seekers unified --config configs/godot_unified.json
    skill-seekers unified --config configs/react_unified.json --merge-mode claude-enhanced
"""

import os
import sys
import json
import logging
import argparse
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import validators and scrapers
try:
    from skill_seekers.cli.config_validator import ConfigValidator, validate_config
    from skill_seekers.cli.conflict_detector import ConflictDetector
    from skill_seekers.cli.merge_sources import RuleBasedMerger, ClaudeEnhancedMerger
    from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
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

    def __init__(self, config_path: str, merge_mode: Optional[str] = None):
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

        # Determine merge mode
        self.merge_mode = merge_mode or self.config.get('merge_mode', 'rule-based')
        logger.info(f"Merge mode: {self.merge_mode}")

        # Storage for scraped data - use lists to support multiple sources of same type
        self.scraped_data = {
            'documentation': [],  # List of doc sources
            'github': [],         # List of github sources
            'pdf': []             # List of pdf sources
        }

        # Track source index for unique naming (multi-source support)
        self._source_counters = {'documentation': 0, 'github': 0, 'pdf': 0}

        # Output paths - cleaner organization
        self.name = self.config['name']
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
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_file = f"{self.logs_dir}/unified_{timestamp}.log"

        # Add file handler to root logger
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
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

        if not self.validator.is_unified:
            logger.warning("Config is not unified format, converting...")
            self.config = self.validator.convert_legacy_to_unified()

        sources = self.config.get('sources', [])

        for i, source in enumerate(sources):
            source_type = source['type']
            logger.info(f"\n[{i+1}/{len(sources)}] Scraping {source_type} source...")

            try:
                if source_type == 'documentation':
                    self._scrape_documentation(source)
                elif source_type == 'github':
                    self._scrape_github(source)
                elif source_type == 'pdf':
                    self._scrape_pdf(source)
                else:
                    logger.warning(f"Unknown source type: {source_type}")
            except Exception as e:
                logger.error(f"Error scraping {source_type}: {e}")
                logger.info("Continuing with other sources...")

        logger.info(f"\n✅ Scraped {len(self.scraped_data)} sources successfully")

    def _scrape_documentation(self, source: Dict[str, Any]):
        """Scrape documentation website."""
        # Create temporary config for doc scraper
        doc_config = {
            'name': f"{self.name}_docs",
            'base_url': source['base_url'],
            'selectors': source.get('selectors', {}),
            'url_patterns': source.get('url_patterns', {}),
            'categories': source.get('categories', {}),
            'rate_limit': source.get('rate_limit', 0.5),
            'max_pages': source.get('max_pages', 100)
        }

        # Pass through llms.txt settings (so unified configs behave the same as doc_scraper configs)
        if 'llms_txt_url' in source:
            doc_config['llms_txt_url'] = source.get('llms_txt_url')

        if 'skip_llms_txt' in source:
            doc_config['skip_llms_txt'] = source.get('skip_llms_txt')

        # Optional: support overriding start URLs
        if 'start_urls' in source:
            doc_config['start_urls'] = source.get('start_urls')

        # Write temporary config
        temp_config_path = os.path.join(self.data_dir, 'temp_docs_config.json')
        with open(temp_config_path, 'w', encoding='utf-8') as f:
            json.dump(doc_config, f, indent=2)

        # Run doc_scraper as subprocess
        logger.info(f"Scraping documentation from {source['base_url']}")

        doc_scraper_path = Path(__file__).parent / "doc_scraper.py"
        cmd = [sys.executable, str(doc_scraper_path), '--config', temp_config_path, '--fresh']

        result = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)

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
            with open(docs_data_file, 'r', encoding='utf-8') as f:
                summary = json.load(f)

            # Append to documentation list (multi-source support)
            self.scraped_data['documentation'].append({
                'source_id': doc_config['name'],
                'base_url': source['base_url'],
                'pages': summary.get('pages', []),
                'total_pages': summary.get('total_pages', 0),
                'data_file': docs_data_file,
                'refs_dir': ''  # Will be set after moving to cache
            })

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
            refs_dir_path = os.path.join(cache_docs_dir, 'references')
            if self.scraped_data['documentation']:
                self.scraped_data['documentation'][-1]['refs_dir'] = refs_dir_path

        if os.path.exists(docs_data_dir):
            cache_data_dir = os.path.join(self.data_dir, f"{doc_config['name']}_data")
            if os.path.exists(cache_data_dir):
                shutil.rmtree(cache_data_dir)
            shutil.move(docs_data_dir, cache_data_dir)
            logger.info(f"📦 Moved docs data to cache: {cache_data_dir}")

    def _clone_github_repo(self, repo_name: str, idx: int = 0) -> Optional[str]:
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
        if os.path.exists(clone_path) and os.path.isdir(os.path.join(clone_path, '.git')):
            logger.info(f"♻️  Found existing repository clone: {clone_path}")
            logger.info(f"   Reusing for C3.x analysis (skip re-cloning)")
            return clone_path

        # repos_dir already created in __init__

        # Clone repo (full clone, not shallow - for complete analysis)
        repo_url = f"https://github.com/{repo_name}.git"
        logger.info(f"🔄 Cloning repository for C3.x analysis: {repo_url}")
        logger.info(f"   → {clone_path}")
        logger.info(f"   💾 Clone will be saved for future reuse")

        try:
            result = subprocess.run(
                ['git', 'clone', repo_url, clone_path],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for full clone
            )

            if result.returncode == 0:
                logger.info(f"✅ Repository cloned successfully")
                logger.info(f"   📁 Saved to: {clone_path}")
                return clone_path
            else:
                logger.error(f"❌ Git clone failed: {result.stderr}")
                # Clean up failed clone
                if os.path.exists(clone_path):
                    shutil.rmtree(clone_path)
                return None

        except subprocess.TimeoutExpired:
            logger.error(f"❌ Git clone timed out after 10 minutes")
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path)
            return None
        except Exception as e:
            logger.error(f"❌ Git clone failed: {e}")
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path)
            return None

    def _scrape_github(self, source: Dict[str, Any]):
        """Scrape GitHub repository."""
        try:
            from skill_seekers.cli.github_scraper import GitHubScraper
        except ImportError:
            logger.error("github_scraper.py not found")
            return

        # Multi-source support: Get unique index for this GitHub source
        idx = self._source_counters['github']
        self._source_counters['github'] += 1

        # Extract repo identifier for unique naming
        repo = source['repo']
        repo_id = repo.replace('/', '_')

        # Check if we need to clone for C3.x analysis
        enable_codebase_analysis = source.get('enable_codebase_analysis', True)
        local_repo_path = source.get('local_repo_path')
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
            'repo': repo,
            'name': f"{self.name}_github_{idx}_{repo_id}",
            'github_token': source.get('github_token'),
            'include_issues': source.get('include_issues', True),
            'max_issues': source.get('max_issues', 100),
            'include_changelog': source.get('include_changelog', True),
            'include_releases': source.get('include_releases', True),
            'include_code': source.get('include_code', True),
            'code_analysis_depth': source.get('code_analysis_depth', 'surface'),
            'file_patterns': source.get('file_patterns', []),
            'local_repo_path': local_repo_path  # Use cloned path if available
        }

        # Pass directory exclusions if specified (optional)
        if 'exclude_dirs' in source:
            github_config['exclude_dirs'] = source['exclude_dirs']
        if 'exclude_dirs_additional' in source:
            github_config['exclude_dirs_additional'] = source['exclude_dirs_additional']

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
                    github_data['c3_analysis'] = c3_data
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
        github_data_file = os.path.join(self.data_dir, f'github_data_{idx}_{repo_id}.json')
        with open(github_data_file, 'w', encoding='utf-8') as f:
            json.dump(github_data, f, indent=2, ensure_ascii=False)

        # ALSO save to the location GitHubToSkillConverter expects (with C3.x data!)
        converter_data_file = f"output/{github_config['name']}_github_data.json"
        with open(converter_data_file, 'w', encoding='utf-8') as f:
            json.dump(github_data, f, indent=2, ensure_ascii=False)

        # Append to list instead of overwriting (multi-source support)
        self.scraped_data['github'].append({
            'repo': repo,
            'repo_id': repo_id,
            'idx': idx,
            'data': github_data,
            'data_file': github_data_file
        })

        # Build standalone SKILL.md for synthesis using GitHubToSkillConverter
        try:
            from skill_seekers.cli.github_scraper import GitHubToSkillConverter
            # Use github_config which has the correct name field
            # Converter will load from output/{name}_github_data.json which now has C3.x data
            converter = GitHubToSkillConverter(config=github_config)
            converter.build_skill()
            logger.info(f"✅ GitHub: Standalone SKILL.md created")
        except Exception as e:
            logger.warning(f"⚠️  Failed to build standalone GitHub SKILL.md: {e}")

        # Move intermediate files to cache to keep output/ clean
        github_output_dir = f"output/{github_config['name']}"
        github_data_file_path = f"output/{github_config['name']}_github_data.json"

        if os.path.exists(github_output_dir):
            cache_github_dir = os.path.join(self.sources_dir, github_config['name'])
            if os.path.exists(cache_github_dir):
                shutil.rmtree(cache_github_dir)
            shutil.move(github_output_dir, cache_github_dir)
            logger.info(f"📦 Moved GitHub output to cache: {cache_github_dir}")

        if os.path.exists(github_data_file_path):
            cache_github_data = os.path.join(self.data_dir, f"{github_config['name']}_github_data.json")
            if os.path.exists(cache_github_data):
                os.remove(cache_github_data)
            shutil.move(github_data_file_path, cache_github_data)
            logger.info(f"📦 Moved GitHub data to cache: {cache_github_data}")

        logger.info(f"✅ GitHub: Repository scraped successfully")

    def _scrape_pdf(self, source: Dict[str, Any]):
        """Scrape PDF document."""
        try:
            from skill_seekers.cli.pdf_scraper import PDFToSkillConverter
        except ImportError:
            logger.error("pdf_scraper.py not found")
            return

        # Multi-source support: Get unique index for this PDF source
        idx = self._source_counters['pdf']
        self._source_counters['pdf'] += 1

        # Extract PDF identifier for unique naming (filename without extension)
        pdf_path = source['path']
        pdf_id = os.path.splitext(os.path.basename(pdf_path))[0]

        # Create config for PDF scraper
        pdf_config = {
            'name': f"{self.name}_pdf_{idx}_{pdf_id}",
            'pdf': source['path'],
            'extract_tables': source.get('extract_tables', False),
            'ocr': source.get('ocr', False),
            'password': source.get('password')
        }

        # Scrape
        logger.info(f"Scraping PDF: {source['path']}")
        converter = PDFToSkillConverter(pdf_config)
        pdf_data = converter.extract_all()

        # Save data
        pdf_data_file = os.path.join(self.data_dir, f'pdf_data_{idx}_{pdf_id}.json')
        with open(pdf_data_file, 'w', encoding='utf-8') as f:
            json.dump(pdf_data, f, indent=2, ensure_ascii=False)

        # Append to list instead of overwriting
        self.scraped_data['pdf'].append({
            'pdf_path': pdf_path,
            'pdf_id': pdf_id,
            'idx': idx,
            'data': pdf_data,
            'data_file': pdf_data_file
        })

        # Build standalone SKILL.md for synthesis
        try:
            converter.build_skill()
            logger.info(f"✅ PDF: Standalone SKILL.md created")
        except Exception as e:
            logger.warning(f"⚠️  Failed to build standalone PDF SKILL.md: {e}")

        logger.info(f"✅ PDF: {len(pdf_data.get('pages', []))} pages extracted")

    def _load_json(self, file_path: Path) -> Dict:
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
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load JSON {file_path}: {e}")
            return {}

    def _load_guide_collection(self, tutorials_dir: Path) -> Dict:
        """
        Load how-to guide collection from tutorials directory.

        Args:
            tutorials_dir: Path to tutorials directory

        Returns:
            Dict with guide collection data
        """
        if not tutorials_dir.exists():
            logger.warning(f"Tutorials directory not found: {tutorials_dir}")
            return {'guides': []}

        collection_file = tutorials_dir / 'guide_collection.json'
        if collection_file.exists():
            return self._load_json(collection_file)

        # Fallback: scan for individual guide JSON files
        guides = []
        for guide_file in tutorials_dir.glob('guide_*.json'):
            guide_data = self._load_json(guide_file)
            if guide_data:
                guides.append(guide_data)

        return {'guides': guides, 'total_count': len(guides)}

    def _load_api_reference(self, api_dir: Path) -> Dict[str, Any]:
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
        for md_file in api_dir.glob('*.md'):
            try:
                module_name = md_file.stem
                api_refs[module_name] = md_file.read_text(encoding='utf-8')
            except IOError as e:
                logger.warning(f"Failed to read API reference {md_file}: {e}")

        return api_refs

    def _run_c3_analysis(self, local_repo_path: str, source: Dict[str, Any]) -> Dict[str, Any]:
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
        temp_output = Path(self.data_dir) / 'c3_analysis_temp'
        temp_output.mkdir(parents=True, exist_ok=True)

        logger.info(f"   Analyzing codebase: {local_repo_path}")

        try:
            # Run full C3.x analysis
            results = analyze_codebase(
                directory=Path(local_repo_path),
                output_dir=temp_output,
                depth='deep',
                languages=None,  # Analyze all languages
                file_patterns=source.get('file_patterns'),
                build_api_reference=True,   # C2.5: API Reference
                extract_comments=False,     # Not needed
                build_dependency_graph=True,  # C2.6: Dependency Graph
                detect_patterns=True,       # C3.1: Design patterns
                extract_test_examples=True, # C3.2: Test examples
                build_how_to_guides=True,   # C3.3: How-to guides
                extract_config_patterns=True,  # C3.4: Config patterns
                enhance_with_ai=source.get('ai_mode', 'auto') != 'none',
                ai_mode=source.get('ai_mode', 'auto')
            )

            # Load C3.x outputs into memory
            c3_data = {
                'patterns': self._load_json(temp_output / 'patterns' / 'detected_patterns.json'),
                'test_examples': self._load_json(temp_output / 'test_examples' / 'test_examples.json'),
                'how_to_guides': self._load_guide_collection(temp_output / 'tutorials'),
                'config_patterns': self._load_json(temp_output / 'config_patterns' / 'config_patterns.json'),
                'architecture': self._load_json(temp_output / 'architecture' / 'architectural_patterns.json'),
                'api_reference': self._load_api_reference(temp_output / 'api_reference'),  # C2.5
                'dependency_graph': self._load_json(temp_output / 'dependencies' / 'dependency_graph.json')  # C2.6
            }

            # Log summary
            total_patterns = sum(len(f.get('patterns', [])) for f in c3_data.get('patterns', []))
            total_examples = c3_data.get('test_examples', {}).get('total_examples', 0)
            total_guides = len(c3_data.get('how_to_guides', {}).get('guides', []))
            total_configs = len(c3_data.get('config_patterns', {}).get('config_files', []))
            arch_patterns = len(c3_data.get('architecture', {}).get('patterns', []))

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

    def detect_conflicts(self) -> List:
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
            return []

        # Get documentation and GitHub data
        docs_data = self.scraped_data.get('documentation', {})
        github_data = self.scraped_data.get('github', {})

        if not docs_data or not github_data:
            logger.warning("Missing documentation or GitHub data for conflict detection")
            return []

        # Load data files
        with open(docs_data['data_file'], 'r', encoding='utf-8') as f:
            docs_json = json.load(f)

        with open(github_data['data_file'], 'r', encoding='utf-8') as f:
            github_json = json.load(f)

        # Detect conflicts
        detector = ConflictDetector(docs_json, github_json)
        conflicts = detector.detect_all_conflicts()

        # Save conflicts
        conflicts_file = os.path.join(self.data_dir, 'conflicts.json')
        detector.save_conflicts(conflicts, conflicts_file)

        # Print summary
        summary = detector.generate_summary(conflicts)
        logger.info(f"\n📊 Conflict Summary:")
        logger.info(f"   Total: {summary['total']}")
        logger.info(f"   By Type:")
        for ctype, count in summary['by_type'].items():
            if count > 0:
                logger.info(f"     - {ctype}: {count}")
        logger.info(f"   By Severity:")
        for severity, count in summary['by_severity'].items():
            if count > 0:
                emoji = '🔴' if severity == 'high' else '🟡' if severity == 'medium' else '🟢'
                logger.info(f"     {emoji} {severity}: {count}")

        return conflicts

    def merge_sources(self, conflicts: List):
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

        # Get data files
        docs_data = self.scraped_data.get('documentation', {})
        github_data = self.scraped_data.get('github', {})

        # Load data
        with open(docs_data['data_file'], 'r', encoding='utf-8') as f:
            docs_json = json.load(f)

        with open(github_data['data_file'], 'r', encoding='utf-8') as f:
            github_json = json.load(f)

        # Choose merger
        if self.merge_mode == 'claude-enhanced':
            merger = ClaudeEnhancedMerger(docs_json, github_json, conflicts)
        else:
            merger = RuleBasedMerger(docs_json, github_json, conflicts)

        # Merge
        merged_data = merger.merge_all()

        # Save merged data
        merged_file = os.path.join(self.data_dir, 'merged_data.json')
        with open(merged_file, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Merged data saved: {merged_file}")

        return merged_data

    def build_skill(self, merged_data: Optional[Dict] = None):
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
        conflicts_file = os.path.join(self.data_dir, 'conflicts.json')
        if os.path.exists(conflicts_file):
            with open(conflicts_file, 'r', encoding='utf-8') as f:
                conflicts_data = json.load(f)
                conflicts = conflicts_data.get('conflicts', [])

        # Build skill
        builder = UnifiedSkillBuilder(
            self.config,
            self.scraped_data,
            merged_data,
            conflicts,
            cache_dir=self.cache_dir
        )

        builder.build()

        logger.info(f"✅ Unified skill built: {self.output_dir}/")

    def run(self):
        """
        Execute complete unified scraping workflow.
        """
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
        description='Unified multi-source scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with unified config
  skill-seekers unified --config configs/godot_unified.json

  # Override merge mode
  skill-seekers unified --config configs/react_unified.json --merge-mode claude-enhanced

  # Backward compatible with legacy configs
  skill-seekers unified --config configs/react.json
        """
    )

    parser.add_argument('--config', '-c', required=True,
                       help='Path to unified config JSON file')
    parser.add_argument('--merge-mode', '-m',
                       choices=['rule-based', 'claude-enhanced'],
                       help='Override config merge mode')
    parser.add_argument('--skip-codebase-analysis',
                       action='store_true',
                       help='Skip C3.x codebase analysis for GitHub sources (default: enabled)')

    args = parser.parse_args()

    # Create scraper
    scraper = UnifiedScraper(args.config, args.merge_mode)

    # Disable codebase analysis if requested
    if args.skip_codebase_analysis:
        for source in scraper.config.get('sources', []):
            if source['type'] == 'github':
                source['enable_codebase_analysis'] = False
                logger.info(f"⏭️  Skipping codebase analysis for GitHub source: {source.get('repo', 'unknown')}")

    # Run scraper
    scraper.run()


if __name__ == '__main__':
    main()
