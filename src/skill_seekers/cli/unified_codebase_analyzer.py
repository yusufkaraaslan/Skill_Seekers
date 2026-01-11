"""
Unified Codebase Analyzer

Key Insight: C3.x is an ANALYSIS DEPTH, not a source type.

This analyzer works with ANY codebase source:
- GitHub URLs (uses three-stream fetcher)
- Local paths (analyzes directly)

Analysis modes:
- basic (1-2 min): File structure, imports, entry points
- c3x (20-60 min): Full C3.x suite + GitHub insights
"""

import os
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass

from skill_seekers.cli.github_fetcher import GitHubThreeStreamFetcher, ThreeStreamData


@dataclass
class AnalysisResult:
    """Unified analysis result from any codebase source."""
    code_analysis: Dict
    github_docs: Optional[Dict] = None
    github_insights: Optional[Dict] = None
    source_type: str = 'local'  # 'local' or 'github'
    analysis_depth: str = 'basic'  # 'basic' or 'c3x'


class UnifiedCodebaseAnalyzer:
    """
    Unified analyzer for ANY codebase (local or GitHub).

    Key insight: C3.x is a DEPTH MODE, not a source type.

    Usage:
        analyzer = UnifiedCodebaseAnalyzer()

        # Analyze from GitHub
        result = analyzer.analyze(
            source="https://github.com/facebook/react",
            depth="c3x",
            fetch_github_metadata=True
        )

        # Analyze local directory
        result = analyzer.analyze(
            source="/path/to/project",
            depth="c3x"
        )

        # Quick basic analysis
        result = analyzer.analyze(
            source="/path/to/project",
            depth="basic"
        )
    """

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize analyzer.

        Args:
            github_token: Optional GitHub API token for higher rate limits
        """
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')

    def analyze(
        self,
        source: str,
        depth: str = 'c3x',
        fetch_github_metadata: bool = True,
        output_dir: Optional[Path] = None
    ) -> AnalysisResult:
        """
        Analyze codebase with specified depth.

        Args:
            source: GitHub URL or local path
            depth: 'basic' or 'c3x'
            fetch_github_metadata: Whether to fetch GitHub insights (only for GitHub sources)
            output_dir: Directory for temporary files (GitHub clones)

        Returns:
            AnalysisResult with all available streams
        """
        print(f"🔍 Analyzing codebase: {source}")
        print(f"📊 Analysis depth: {depth}")

        # Step 1: Acquire source
        if self.is_github_url(source):
            print(f"📦 Source type: GitHub repository")
            return self._analyze_github(source, depth, fetch_github_metadata, output_dir)
        else:
            print(f"📁 Source type: Local directory")
            return self._analyze_local(source, depth)

    def _analyze_github(
        self,
        repo_url: str,
        depth: str,
        fetch_metadata: bool,
        output_dir: Optional[Path]
    ) -> AnalysisResult:
        """
        Analyze GitHub repository with three-stream fetcher.

        Args:
            repo_url: GitHub repository URL
            depth: Analysis depth mode
            fetch_metadata: Whether to fetch GitHub metadata
            output_dir: Output directory for clone

        Returns:
            AnalysisResult with all 3 streams
        """
        # Use three-stream fetcher
        fetcher = GitHubThreeStreamFetcher(repo_url, self.github_token)
        three_streams = fetcher.fetch(output_dir)

        # Analyze code with specified depth
        code_directory = three_streams.code_stream.directory
        if depth == 'basic':
            code_analysis = self.basic_analysis(code_directory)
        elif depth == 'c3x':
            code_analysis = self.c3x_analysis(code_directory)
        else:
            raise ValueError(f"Unknown depth: {depth}. Use 'basic' or 'c3x'")

        # Build result with all streams
        result = AnalysisResult(
            code_analysis=code_analysis,
            source_type='github',
            analysis_depth=depth
        )

        # Add GitHub-specific data if available
        if fetch_metadata:
            result.github_docs = {
                'readme': three_streams.docs_stream.readme,
                'contributing': three_streams.docs_stream.contributing,
                'docs_files': three_streams.docs_stream.docs_files
            }
            result.github_insights = {
                'metadata': three_streams.insights_stream.metadata,
                'common_problems': three_streams.insights_stream.common_problems,
                'known_solutions': three_streams.insights_stream.known_solutions,
                'top_labels': three_streams.insights_stream.top_labels
            }

        return result

    def _analyze_local(self, directory: str, depth: str) -> AnalysisResult:
        """
        Analyze local directory.

        Args:
            directory: Path to local directory
            depth: Analysis depth mode

        Returns:
            AnalysisResult with code analysis only
        """
        code_directory = Path(directory)

        if not code_directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not code_directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        # Analyze code with specified depth
        if depth == 'basic':
            code_analysis = self.basic_analysis(code_directory)
        elif depth == 'c3x':
            code_analysis = self.c3x_analysis(code_directory)
        else:
            raise ValueError(f"Unknown depth: {depth}. Use 'basic' or 'c3x'")

        return AnalysisResult(
            code_analysis=code_analysis,
            source_type='local',
            analysis_depth=depth
        )

    def basic_analysis(self, directory: Path) -> Dict:
        """
        Fast, shallow analysis (1-2 min).

        Returns:
        - File structure
        - Imports
        - Entry points
        - Basic statistics

        Args:
            directory: Path to analyze

        Returns:
            Dict with basic analysis
        """
        print("📊 Running basic analysis (1-2 min)...")

        analysis = {
            'directory': str(directory),
            'analysis_type': 'basic',
            'files': self.list_files(directory),
            'structure': self.get_directory_structure(directory),
            'imports': self.extract_imports(directory),
            'entry_points': self.find_entry_points(directory),
            'statistics': self.compute_statistics(directory)
        }

        print(f"✅ Basic analysis complete: {len(analysis['files'])} files analyzed")
        return analysis

    def c3x_analysis(self, directory: Path) -> Dict:
        """
        Deep C3.x analysis (20-60 min).

        Returns:
        - Everything from basic
        - C3.1: Design patterns
        - C3.2: Test examples
        - C3.3: How-to guides
        - C3.4: Config patterns
        - C3.7: Architecture

        Args:
            directory: Path to analyze

        Returns:
            Dict with full C3.x analysis
        """
        print("📊 Running C3.x analysis (20-60 min)...")

        # Start with basic analysis
        basic = self.basic_analysis(directory)

        # Run full C3.x analysis using existing codebase_scraper
        print("🔍 Running C3.x components (patterns, examples, guides, configs, architecture)...")

        try:
            # Import codebase analyzer
            from .codebase_scraper import analyze_codebase
            import tempfile

            # Create temporary output directory for C3.x analysis
            temp_output = Path(tempfile.mkdtemp(prefix='c3x_analysis_'))

            # Run full C3.x analysis
            analyze_codebase(
                directory=directory,
                output_dir=temp_output,
                depth='deep',
                languages=None,  # All languages
                file_patterns=None,  # All files
                build_api_reference=True,
                build_dependency_graph=True,
                detect_patterns=True,
                extract_test_examples=True,
                build_how_to_guides=True,
                extract_config_patterns=True,
                enhance_with_ai=False,  # Disable AI for speed
                ai_mode='none'
            )

            # Load C3.x results from output files
            c3x_data = self._load_c3x_results(temp_output)

            # Merge with basic analysis
            c3x = {
                **basic,
                'analysis_type': 'c3x',
                **c3x_data
            }

            print(f"✅ C3.x analysis complete!")
            print(f"   - {len(c3x_data.get('c3_1_patterns', []))} design patterns detected")
            print(f"   - {c3x_data.get('c3_2_examples_count', 0)} test examples extracted")
            print(f"   - {len(c3x_data.get('c3_3_guides', []))} how-to guides generated")
            print(f"   - {len(c3x_data.get('c3_4_configs', []))} config files analyzed")
            print(f"   - {len(c3x_data.get('c3_7_architecture', []))} architectural patterns found")

            return c3x

        except Exception as e:
            print(f"⚠️  C3.x analysis failed: {e}")
            print(f"   Falling back to basic analysis with placeholders")

            # Fall back to placeholders
            c3x = {
                **basic,
                'analysis_type': 'c3x',
                'c3_1_patterns': [],
                'c3_2_examples': [],
                'c3_2_examples_count': 0,
                'c3_3_guides': [],
                'c3_4_configs': [],
                'c3_7_architecture': [],
                'error': str(e)
            }

            return c3x

    def _load_c3x_results(self, output_dir: Path) -> Dict:
        """
        Load C3.x analysis results from output directory.

        Args:
            output_dir: Directory containing C3.x analysis output

        Returns:
            Dict with C3.x data (c3_1_patterns, c3_2_examples, etc.)
        """
        import json

        c3x_data = {}

        # C3.1: Design Patterns
        patterns_file = output_dir / 'patterns' / 'design_patterns.json'
        if patterns_file.exists():
            with open(patterns_file, 'r') as f:
                patterns_data = json.load(f)
                c3x_data['c3_1_patterns'] = patterns_data.get('patterns', [])
        else:
            c3x_data['c3_1_patterns'] = []

        # C3.2: Test Examples
        examples_file = output_dir / 'test_examples' / 'test_examples.json'
        if examples_file.exists():
            with open(examples_file, 'r') as f:
                examples_data = json.load(f)
                c3x_data['c3_2_examples'] = examples_data.get('examples', [])
                c3x_data['c3_2_examples_count'] = examples_data.get('total_examples', 0)
        else:
            c3x_data['c3_2_examples'] = []
            c3x_data['c3_2_examples_count'] = 0

        # C3.3: How-to Guides
        guides_file = output_dir / 'tutorials' / 'guide_collection.json'
        if guides_file.exists():
            with open(guides_file, 'r') as f:
                guides_data = json.load(f)
                c3x_data['c3_3_guides'] = guides_data.get('guides', [])
        else:
            c3x_data['c3_3_guides'] = []

        # C3.4: Config Patterns
        config_file = output_dir / 'config_patterns' / 'config_patterns.json'
        if config_file.exists():
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                c3x_data['c3_4_configs'] = config_data.get('config_files', [])
        else:
            c3x_data['c3_4_configs'] = []

        # C3.7: Architecture
        arch_file = output_dir / 'architecture' / 'architectural_patterns.json'
        if arch_file.exists():
            with open(arch_file, 'r') as f:
                arch_data = json.load(f)
                c3x_data['c3_7_architecture'] = arch_data.get('patterns', [])
        else:
            c3x_data['c3_7_architecture'] = []

        # Add dependency graph data
        dep_file = output_dir / 'dependencies' / 'dependency_graph.json'
        if dep_file.exists():
            with open(dep_file, 'r') as f:
                dep_data = json.load(f)
                c3x_data['dependency_graph'] = dep_data

        # Add API reference data
        api_file = output_dir / 'code_analysis.json'
        if api_file.exists():
            with open(api_file, 'r') as f:
                api_data = json.load(f)
                c3x_data['api_reference'] = api_data

        return c3x_data

    def is_github_url(self, source: str) -> bool:
        """
        Check if source is a GitHub URL.

        Args:
            source: Source string (URL or path)

        Returns:
            True if GitHub URL, False otherwise
        """
        return 'github.com' in source

    def list_files(self, directory: Path) -> List[Dict]:
        """
        List all files in directory with metadata.

        Args:
            directory: Directory to scan

        Returns:
            List of file info dicts
        """
        files = []
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                try:
                    files.append({
                        'path': str(file_path.relative_to(directory)),
                        'size': file_path.stat().st_size,
                        'extension': file_path.suffix
                    })
                except Exception:
                    # Skip files we can't access
                    continue
        return files

    def get_directory_structure(self, directory: Path) -> Dict:
        """
        Get directory structure tree.

        Args:
            directory: Directory to analyze

        Returns:
            Dict representing directory structure
        """
        structure = {
            'name': directory.name,
            'type': 'directory',
            'children': []
        }

        try:
            for item in sorted(directory.iterdir()):
                if item.name.startswith('.'):
                    continue  # Skip hidden files

                if item.is_dir():
                    # Only include immediate subdirectories
                    structure['children'].append({
                        'name': item.name,
                        'type': 'directory'
                    })
                elif item.is_file():
                    structure['children'].append({
                        'name': item.name,
                        'type': 'file',
                        'extension': item.suffix
                    })
        except Exception:
            pass

        return structure

    def extract_imports(self, directory: Path) -> Dict[str, List[str]]:
        """
        Extract import statements from code files.

        Args:
            directory: Directory to scan

        Returns:
            Dict mapping file extensions to import lists
        """
        imports = {
            '.py': [],
            '.js': [],
            '.ts': []
        }

        # Sample up to 10 files per extension
        for ext in imports.keys():
            files = list(directory.rglob(f'*{ext}'))[:10]
            for file_path in files:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    if ext == '.py':
                        # Extract Python imports
                        for line in content.split('\n')[:50]:  # Check first 50 lines
                            if line.strip().startswith(('import ', 'from ')):
                                imports[ext].append(line.strip())
                    elif ext in ['.js', '.ts']:
                        # Extract JS/TS imports
                        for line in content.split('\n')[:50]:
                            if line.strip().startswith(('import ', 'require(')):
                                imports[ext].append(line.strip())
                except Exception:
                    continue

        # Remove empty lists
        return {k: v for k, v in imports.items() if v}

    def find_entry_points(self, directory: Path) -> List[str]:
        """
        Find potential entry points (main files, setup files, etc.).

        Args:
            directory: Directory to scan

        Returns:
            List of entry point file paths
        """
        entry_points = []

        # Common entry point patterns
        entry_patterns = [
            'main.py', '__main__.py', 'app.py', 'server.py',
            'index.js', 'index.ts', 'main.js', 'main.ts',
            'setup.py', 'pyproject.toml', 'package.json',
            'Makefile', 'docker-compose.yml', 'Dockerfile'
        ]

        for pattern in entry_patterns:
            matches = list(directory.rglob(pattern))
            for match in matches:
                try:
                    entry_points.append(str(match.relative_to(directory)))
                except Exception:
                    continue

        return entry_points

    def compute_statistics(self, directory: Path) -> Dict:
        """
        Compute basic statistics about the codebase.

        Args:
            directory: Directory to analyze

        Returns:
            Dict with statistics
        """
        stats = {
            'total_files': 0,
            'total_size_bytes': 0,
            'file_types': {},
            'languages': {}
        }

        for file_path in directory.rglob('*'):
            if not file_path.is_file():
                continue

            try:
                stats['total_files'] += 1
                stats['total_size_bytes'] += file_path.stat().st_size

                ext = file_path.suffix
                if ext:
                    stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1

                    # Map extensions to languages
                    language_map = {
                        '.py': 'Python',
                        '.js': 'JavaScript',
                        '.ts': 'TypeScript',
                        '.go': 'Go',
                        '.rs': 'Rust',
                        '.java': 'Java',
                        '.rb': 'Ruby',
                        '.php': 'PHP'
                    }
                    if ext in language_map:
                        lang = language_map[ext]
                        stats['languages'][lang] = stats['languages'].get(lang, 0) + 1
            except Exception:
                continue

        return stats
