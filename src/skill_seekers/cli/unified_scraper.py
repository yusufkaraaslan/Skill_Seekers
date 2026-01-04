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

        # Storage for scraped data
        self.scraped_data = {}

        # Output paths
        self.name = self.config['name']
        self.output_dir = f"output/{self.name}"
        self.data_dir = f"output/{self.name}_unified_data"

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

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
        cmd = [sys.executable, str(doc_scraper_path), '--config', temp_config_path]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"Documentation scraping failed: {result.stderr}")
            return

        # Load scraped data
        docs_data_file = f"output/{doc_config['name']}_data/summary.json"

        if os.path.exists(docs_data_file):
            with open(docs_data_file, 'r', encoding='utf-8') as f:
                summary = json.load(f)

            self.scraped_data['documentation'] = {
                'pages': summary.get('pages', []),
                'data_file': docs_data_file
            }

            logger.info(f"✅ Documentation: {summary.get('total_pages', 0)} pages scraped")
        else:
            logger.warning("Documentation data file not found")

        # Clean up temp config
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)

    def _scrape_github(self, source: Dict[str, Any]):
        """Scrape GitHub repository."""
        try:
            from skill_seekers.cli.github_scraper import GitHubScraper
        except ImportError:
            logger.error("github_scraper.py not found")
            return

        # Create config for GitHub scraper
        github_config = {
            'repo': source['repo'],
            'name': f"{self.name}_github",
            'github_token': source.get('github_token'),
            'include_issues': source.get('include_issues', True),
            'max_issues': source.get('max_issues', 100),
            'include_changelog': source.get('include_changelog', True),
            'include_releases': source.get('include_releases', True),
            'include_code': source.get('include_code', True),
            'code_analysis_depth': source.get('code_analysis_depth', 'surface'),
            'file_patterns': source.get('file_patterns', []),
            'local_repo_path': source.get('local_repo_path')  # Pass local_repo_path from config
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
        enable_codebase_analysis = source.get('enable_codebase_analysis', True)
        local_repo_path = source.get('local_repo_path')

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
                # Continue without C3.x data - graceful degradation

        # Save data
        github_data_file = os.path.join(self.data_dir, 'github_data.json')
        with open(github_data_file, 'w', encoding='utf-8') as f:
            json.dump(github_data, f, indent=2, ensure_ascii=False)

        self.scraped_data['github'] = {
            'data': github_data,
            'data_file': github_data_file
        }

        logger.info(f"✅ GitHub: Repository scraped successfully")

    def _scrape_pdf(self, source: Dict[str, Any]):
        """Scrape PDF document."""
        try:
            from skill_seekers.cli.pdf_scraper import PDFToSkillConverter
        except ImportError:
            logger.error("pdf_scraper.py not found")
            return

        # Create config for PDF scraper
        pdf_config = {
            'name': f"{self.name}_pdf",
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
        pdf_data_file = os.path.join(self.data_dir, 'pdf_data.json')
        with open(pdf_data_file, 'w', encoding='utf-8') as f:
            json.dump(pdf_data, f, indent=2, ensure_ascii=False)

        self.scraped_data['pdf'] = {
            'data': pdf_data,
            'data_file': pdf_data_file
        }

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
                build_api_reference=False,  # Not needed in skill
                extract_comments=False,     # Not needed
                build_dependency_graph=False,  # Can add later if needed
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
                'architecture': self._load_json(temp_output / 'architecture' / 'architectural_patterns.json')
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
            conflicts
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
