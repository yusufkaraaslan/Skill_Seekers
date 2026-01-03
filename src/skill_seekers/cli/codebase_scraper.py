#!/usr/bin/env python3
"""
Codebase Scraper CLI Tool

Standalone tool for analyzing local codebases without GitHub API.
Extracts code signatures, comments, and optionally generates API documentation.

Usage:
    codebase-scraper --directory /path/to/repo --output output/codebase/
    codebase-scraper --directory . --depth deep --languages Python,JavaScript
    codebase-scraper --directory /path/to/repo --build-api-reference

Features:
    - File tree walking with .gitignore support
    - Multi-language code analysis (9 languages: Python, JavaScript/TypeScript, C/C++, C#, Go, Rust, Java, Ruby, PHP)
    - API reference generation
    - Comment extraction
    - Dependency graph analysis
    - Configurable depth levels

Credits:
    - Language parsing patterns inspired by official language specifications
    - NetworkX for dependency graph analysis: https://networkx.org/
    - pathspec for .gitignore support: https://pypi.org/project/pathspec/
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skill_seekers.cli.code_analyzer import CodeAnalyzer
from skill_seekers.cli.api_reference_builder import APIReferenceBuilder
from skill_seekers.cli.dependency_analyzer import DependencyAnalyzer

# Try to import pathspec for .gitignore support
try:
    import pathspec
    PATHSPEC_AVAILABLE = True
except ImportError:
    PATHSPEC_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Language extension mapping
LANGUAGE_EXTENSIONS = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.jsx': 'JavaScript',
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript',
    '.cpp': 'C++',
    '.cc': 'C++',
    '.cxx': 'C++',
    '.h': 'C++',
    '.hpp': 'C++',
    '.hxx': 'C++',
    '.c': 'C',
    '.cs': 'C#',
    '.go': 'Go',
    '.rs': 'Rust',
    '.java': 'Java',
    '.rb': 'Ruby',
    '.php': 'PHP',
}

# Default directories to exclude
DEFAULT_EXCLUDED_DIRS = {
    'node_modules', 'venv', '__pycache__', '.git', '.svn', '.hg',
    'build', 'dist', 'target', '.pytest_cache', '.tox', '.mypy_cache',
    'htmlcov', 'coverage', '.coverage', '.eggs', '*.egg-info',
    '.idea', '.vscode', '.vs', '__pypackages__'
}


def detect_language(file_path: Path) -> str:
    """
    Detect programming language from file extension.

    Args:
        file_path: Path to source file

    Returns:
        Language name or 'Unknown'
    """
    extension = file_path.suffix.lower()
    return LANGUAGE_EXTENSIONS.get(extension, 'Unknown')


def load_gitignore(directory: Path) -> Optional[pathspec.PathSpec]:
    """
    Load .gitignore file and create pathspec matcher.

    Args:
        directory: Root directory to search for .gitignore

    Returns:
        PathSpec object if .gitignore found, None otherwise
    """
    if not PATHSPEC_AVAILABLE:
        logger.warning("pathspec not installed - .gitignore support disabled")
        logger.warning("Install with: pip install pathspec")
        return None

    gitignore_path = directory / '.gitignore'
    if not gitignore_path.exists():
        logger.debug(f"No .gitignore found in {directory}")
        return None

    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            spec = pathspec.PathSpec.from_lines('gitwildmatch', f)
        logger.info(f"Loaded .gitignore from {gitignore_path}")
        return spec
    except Exception as e:
        logger.warning(f"Failed to load .gitignore: {e}")
        return None


def should_exclude_dir(dir_name: str, excluded_dirs: set) -> bool:
    """
    Check if directory should be excluded from analysis.

    Args:
        dir_name: Directory name
        excluded_dirs: Set of directory names to exclude

    Returns:
        True if directory should be excluded
    """
    return dir_name in excluded_dirs


def walk_directory(
    root: Path,
    patterns: Optional[List[str]] = None,
    gitignore_spec: Optional[pathspec.PathSpec] = None,
    excluded_dirs: Optional[set] = None
) -> List[Path]:
    """
    Walk directory tree and collect source files.

    Args:
        root: Root directory to walk
        patterns: Optional file patterns to include (e.g., ['*.py', '*.js'])
        gitignore_spec: Optional PathSpec object for .gitignore rules
        excluded_dirs: Set of directory names to exclude

    Returns:
        List of source file paths
    """
    if excluded_dirs is None:
        excluded_dirs = DEFAULT_EXCLUDED_DIRS

    files = []
    root = Path(root).resolve()

    for dirpath, dirnames, filenames in os.walk(root):
        current_dir = Path(dirpath)

        # Filter out excluded directories (in-place modification)
        dirnames[:] = [d for d in dirnames if not should_exclude_dir(d, excluded_dirs)]

        for filename in filenames:
            file_path = current_dir / filename

            # Check .gitignore rules
            if gitignore_spec:
                try:
                    rel_path = file_path.relative_to(root)
                    if gitignore_spec.match_file(str(rel_path)):
                        logger.debug(f"Skipping (gitignore): {rel_path}")
                        continue
                except ValueError:
                    # File is outside root, skip it
                    continue

            # Check file extension
            if file_path.suffix.lower() not in LANGUAGE_EXTENSIONS:
                continue

            # Check file patterns if provided
            if patterns:
                if not any(file_path.match(pattern) for pattern in patterns):
                    continue

            files.append(file_path)

    return sorted(files)


def analyze_codebase(
    directory: Path,
    output_dir: Path,
    depth: str = 'deep',
    languages: Optional[List[str]] = None,
    file_patterns: Optional[List[str]] = None,
    build_api_reference: bool = False,
    extract_comments: bool = True,
    build_dependency_graph: bool = False,
    detect_patterns: bool = False
) -> Dict[str, Any]:
    """
    Analyze local codebase and extract code knowledge.

    Args:
        directory: Directory to analyze
        output_dir: Output directory for results
        depth: Analysis depth (surface, deep, full)
        languages: Optional list of languages to analyze
        file_patterns: Optional file patterns to include
        build_api_reference: Generate API reference markdown
        extract_comments: Extract inline comments
        build_dependency_graph: Generate dependency graph and detect circular dependencies
        detect_patterns: Detect design patterns (Singleton, Factory, Observer, etc.)

    Returns:
        Analysis results dictionary
    """
    logger.info(f"Analyzing codebase: {directory}")
    logger.info(f"Depth: {depth}")

    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load .gitignore
    gitignore_spec = load_gitignore(directory)

    # Walk directory tree
    logger.info("Scanning directory tree...")
    files = walk_directory(
        directory,
        patterns=file_patterns,
        gitignore_spec=gitignore_spec
    )

    logger.info(f"Found {len(files)} source files")

    # Filter by language if specified
    if languages:
        language_set = set(languages)
        files = [f for f in files if detect_language(f) in language_set]
        logger.info(f"Filtered to {len(files)} files for languages: {', '.join(languages)}")

    # Initialize code analyzer
    analyzer = CodeAnalyzer(depth=depth)

    # Analyze each file
    results = {'files': []}
    analyzed_count = 0

    for file_path in files:
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            language = detect_language(file_path)

            if language == 'Unknown':
                continue

            # Analyze file
            analysis = analyzer.analyze_file(str(file_path), content, language)

            # Only include files with actual analysis results
            if analysis and (analysis.get('classes') or analysis.get('functions')):
                results['files'].append({
                    'file': str(file_path.relative_to(directory)),
                    'language': language,
                    **analysis
                })
                analyzed_count += 1

                if analyzed_count % 10 == 0:
                    logger.info(f"Analyzed {analyzed_count}/{len(files)} files...")

        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")
            continue

    logger.info(f"✅ Successfully analyzed {analyzed_count} files")

    # Save results
    output_json = output_dir / 'code_analysis.json'
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    logger.info(f"📁 Saved analysis to: {output_json}")

    # Build API reference if requested
    if build_api_reference and results['files']:
        logger.info("Building API reference documentation...")
        builder = APIReferenceBuilder(results)
        api_output_dir = output_dir / 'api_reference'
        generated_files = builder.build_reference(api_output_dir)
        logger.info(f"✅ Generated {len(generated_files)} API reference files")
        logger.info(f"📁 API reference: {api_output_dir}")

    # Build dependency graph if requested (C2.6)
    if build_dependency_graph:
        logger.info("Building dependency graph...")
        dep_analyzer = DependencyAnalyzer()

        # Analyze dependencies for all files
        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                language = detect_language(file_path)

                if language != 'Unknown':
                    # Use relative path from directory for better graph readability
                    rel_path = str(file_path.relative_to(directory))
                    dep_analyzer.analyze_file(rel_path, content, language)
            except Exception as e:
                logger.warning(f"Error analyzing dependencies for {file_path}: {e}")
                continue

        # Build the graph
        graph = dep_analyzer.build_graph()

        # Detect circular dependencies
        cycles = dep_analyzer.detect_cycles()
        if cycles:
            logger.warning(f"⚠️  Found {len(cycles)} circular dependencies:")
            for i, cycle in enumerate(cycles[:5], 1):  # Show first 5
                cycle_str = ' → '.join(cycle) + f" → {cycle[0]}"
                logger.warning(f"  {i}. {cycle_str}")
            if len(cycles) > 5:
                logger.warning(f"  ... and {len(cycles) - 5} more")
        else:
            logger.info("✅ No circular dependencies found")

        # Save dependency graph data
        dep_output_dir = output_dir / 'dependencies'
        dep_output_dir.mkdir(parents=True, exist_ok=True)

        # Export as JSON
        dep_json = dep_output_dir / 'dependency_graph.json'
        with open(dep_json, 'w', encoding='utf-8') as f:
            json.dump(dep_analyzer.export_json(), f, indent=2)
        logger.info(f"📁 Saved dependency graph: {dep_json}")

        # Export as Mermaid diagram
        mermaid_file = dep_output_dir / 'dependency_graph.mmd'
        mermaid_file.write_text(dep_analyzer.export_mermaid())
        logger.info(f"📁 Saved Mermaid diagram: {mermaid_file}")

        # Save statistics
        stats = dep_analyzer.get_statistics()
        stats_file = dep_output_dir / 'statistics.json'
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        logger.info(f"📊 Statistics: {stats['total_files']} files, "
                   f"{stats['total_dependencies']} dependencies, "
                   f"{stats['circular_dependencies']} cycles")

        # Try to export as DOT (requires pydot)
        try:
            dot_file = dep_output_dir / 'dependency_graph.dot'
            dep_analyzer.export_dot(str(dot_file))
        except:
            pass  # pydot not installed, skip DOT export

    # Detect design patterns if requested (C3.1)
    if detect_patterns:
        logger.info("Detecting design patterns...")
        from skill_seekers.cli.pattern_recognizer import PatternRecognizer

        pattern_recognizer = PatternRecognizer(depth=depth)
        pattern_results = []

        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                language = detect_language(file_path)

                if language != 'Unknown':
                    report = pattern_recognizer.analyze_file(
                        str(file_path), content, language
                    )

                    if report.patterns:
                        pattern_results.append(report.to_dict())
            except Exception as e:
                logger.warning(f"Pattern detection failed for {file_path}: {e}")
                continue

        # Save pattern results
        if pattern_results:
            pattern_output = output_dir / 'patterns'
            pattern_output.mkdir(parents=True, exist_ok=True)

            pattern_json = pattern_output / 'detected_patterns.json'
            with open(pattern_json, 'w', encoding='utf-8') as f:
                json.dump(pattern_results, f, indent=2)

            total_patterns = sum(len(r['patterns']) for r in pattern_results)
            logger.info(f"✅ Detected {total_patterns} patterns in {len(pattern_results)} files")
            logger.info(f"📁 Saved to: {pattern_json}")
        else:
            logger.info("No design patterns detected")

    return results


def main():
    """Command-line interface for codebase analysis."""
    parser = argparse.ArgumentParser(
        description='Analyze local codebases and extract code knowledge',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze current directory
  codebase-scraper --directory . --output output/codebase/

  # Deep analysis with API reference and dependency graph
  codebase-scraper --directory /path/to/repo --depth deep --build-api-reference --build-dependency-graph

  # Analyze only Python and JavaScript
  codebase-scraper --directory . --languages Python,JavaScript

  # Use file patterns
  codebase-scraper --directory . --file-patterns "*.py,src/**/*.js"

  # Full analysis with all features
  codebase-scraper --directory . --depth deep --build-api-reference --build-dependency-graph

  # Surface analysis (fast, no details)
  codebase-scraper --directory . --depth surface
"""
    )

    parser.add_argument(
        '--directory',
        required=True,
        help='Directory to analyze'
    )
    parser.add_argument(
        '--output',
        default='output/codebase/',
        help='Output directory (default: output/codebase/)'
    )
    parser.add_argument(
        '--depth',
        choices=['surface', 'deep', 'full'],
        default='deep',
        help='Analysis depth (default: deep)'
    )
    parser.add_argument(
        '--languages',
        help='Comma-separated languages to analyze (e.g., Python,JavaScript,C++)'
    )
    parser.add_argument(
        '--file-patterns',
        help='Comma-separated file patterns (e.g., *.py,src/**/*.js)'
    )
    parser.add_argument(
        '--build-api-reference',
        action='store_true',
        help='Generate API reference markdown documentation'
    )
    parser.add_argument(
        '--build-dependency-graph',
        action='store_true',
        help='Generate dependency graph and detect circular dependencies'
    )
    parser.add_argument(
        '--detect-patterns',
        action='store_true',
        help='Detect design patterns in code (Singleton, Factory, Observer, etc.)'
    )
    parser.add_argument(
        '--no-comments',
        action='store_true',
        help='Skip comment extraction'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate directory
    directory = Path(args.directory)
    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        return 1

    if not directory.is_dir():
        logger.error(f"Not a directory: {directory}")
        return 1

    # Parse languages
    languages = None
    if args.languages:
        languages = [lang.strip() for lang in args.languages.split(',')]

    # Parse file patterns
    file_patterns = None
    if args.file_patterns:
        file_patterns = [p.strip() for p in args.file_patterns.split(',')]

    # Analyze codebase
    try:
        results = analyze_codebase(
            directory=directory,
            output_dir=Path(args.output),
            depth=args.depth,
            languages=languages,
            file_patterns=file_patterns,
            build_api_reference=args.build_api_reference,
            extract_comments=not args.no_comments,
            build_dependency_graph=args.build_dependency_graph,
            detect_patterns=args.detect_patterns
        )

        # Print summary
        print(f"\n{'='*60}")
        print(f"CODEBASE ANALYSIS COMPLETE")
        print(f"{'='*60}")
        print(f"Files analyzed: {len(results['files'])}")
        print(f"Output directory: {args.output}")
        if args.build_api_reference:
            print(f"API reference: {Path(args.output) / 'api_reference'}")
        print(f"{'='*60}\n")

        return 0

    except KeyboardInterrupt:
        logger.error("\nAnalysis interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
