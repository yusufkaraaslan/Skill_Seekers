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
from skill_seekers.cli.config_extractor import ConfigExtractor

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
    build_api_reference: bool = True,
    extract_comments: bool = True,
    build_dependency_graph: bool = True,
    detect_patterns: bool = True,
    extract_test_examples: bool = True,
    build_how_to_guides: bool = True,
    extract_config_patterns: bool = True,
    enhance_with_ai: bool = True,
    ai_mode: str = "auto"
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
        extract_test_examples: Extract usage examples from test files
        build_how_to_guides: Build how-to guides from workflow examples (C3.3)
        extract_config_patterns: Extract configuration patterns from config files (C3.4)
        enhance_with_ai: Enhance patterns and examples with AI analysis (C3.6)
        ai_mode: AI enhancement mode for how-to guides (auto, api, local, none)

    Returns:
        Analysis results dictionary
    """
    # Resolve directory to absolute path to avoid relative_to() errors
    directory = Path(directory).resolve()

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

        pattern_recognizer = PatternRecognizer(depth=depth, enhance_with_ai=enhance_with_ai)
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

    # Extract test examples if requested (C3.2)
    if extract_test_examples:
        logger.info("Extracting usage examples from test files...")
        from skill_seekers.cli.test_example_extractor import TestExampleExtractor

        # Create extractor
        test_extractor = TestExampleExtractor(
            min_confidence=0.5,
            max_per_file=10,
            languages=languages,
            enhance_with_ai=enhance_with_ai
        )

        # Extract examples from directory
        try:
            example_report = test_extractor.extract_from_directory(
                directory,
                recursive=True
            )

            if example_report.total_examples > 0:
                # Save results
                examples_output = output_dir / 'test_examples'
                examples_output.mkdir(parents=True, exist_ok=True)

                # Save as JSON
                examples_json = examples_output / 'test_examples.json'
                with open(examples_json, 'w', encoding='utf-8') as f:
                    json.dump(example_report.to_dict(), f, indent=2)

                # Save as Markdown
                examples_md = examples_output / 'test_examples.md'
                examples_md.write_text(example_report.to_markdown(), encoding='utf-8')

                logger.info(f"✅ Extracted {example_report.total_examples} test examples "
                           f"({example_report.high_value_count} high-value)")
                logger.info(f"📁 Saved to: {examples_output}")
            else:
                logger.info("No test examples extracted")

        except Exception as e:
            logger.warning(f"Test example extraction failed: {e}")
            example_report = None

    # Build how-to guides from workflow examples (C3.3)
    if build_how_to_guides and extract_test_examples:
        logger.info("Building how-to guides from workflow examples...")
        try:
            from skill_seekers.cli.how_to_guide_builder import HowToGuideBuilder

            # Create guide builder
            guide_builder = HowToGuideBuilder(enhance_with_ai=enhance_with_ai)

            # Build guides from workflow examples
            tutorials_dir = output_dir / 'tutorials'

            # Get workflow examples from the example_report if available
            if 'example_report' in locals() and example_report and example_report.total_examples > 0:
                # Convert example_report to list of dicts for processing
                examples_list = example_report.to_dict().get('examples', [])

                guide_collection = guide_builder.build_guides_from_examples(
                    examples_list,
                    grouping_strategy='ai-tutorial-group',
                    output_dir=tutorials_dir,
                    enhance_with_ai=enhance_with_ai,
                    ai_mode=ai_mode
                )

                if guide_collection and guide_collection.total_guides > 0:
                    # Save collection summary
                    collection_json = tutorials_dir / 'guide_collection.json'
                    with open(collection_json, 'w', encoding='utf-8') as f:
                        json.dump(guide_collection.to_dict(), f, indent=2)

                    logger.info(f"✅ Built {guide_collection.total_guides} how-to guides")
                    logger.info(f"📁 Saved to: {tutorials_dir}")
                else:
                    logger.info("No how-to guides generated (insufficient workflow examples)")
            else:
                logger.info("No workflow examples available for guide generation")

        except Exception as e:
            logger.warning(f"How-to guide building failed: {e}")

    # Extract configuration patterns (C3.4)
    if extract_config_patterns:
        logger.info("Extracting configuration patterns...")
        try:
            config_extractor = ConfigExtractor()

            # Extract config patterns from directory
            extraction_result = config_extractor.extract_from_directory(directory)

            if extraction_result.config_files:
                # Convert to dict for enhancement
                result_dict = config_extractor.to_dict(extraction_result)

                # AI Enhancement (if enabled)
                if enhance_with_ai and ai_mode != 'none':
                    try:
                        from skill_seekers.cli.config_enhancer import ConfigEnhancer
                        logger.info(f"🤖 Enhancing config analysis with AI (mode: {ai_mode})...")
                        enhancer = ConfigEnhancer(mode=ai_mode)
                        result_dict = enhancer.enhance_config_result(result_dict)
                        logger.info("✅ AI enhancement complete")
                    except Exception as e:
                        logger.warning(f"⚠️  Config AI enhancement failed: {e}")

                # Save results
                config_output = output_dir / 'config_patterns'
                config_output.mkdir(parents=True, exist_ok=True)

                # Save as JSON
                config_json = config_output / 'config_patterns.json'
                with open(config_json, 'w', encoding='utf-8') as f:
                    json.dump(result_dict, f, indent=2)

                # Save as Markdown (basic - AI enhancements in JSON only for now)
                config_md = config_output / 'config_patterns.md'
                config_md.write_text(extraction_result.to_markdown(), encoding='utf-8')

                # Count total settings across all files
                total_settings = sum(len(cf.settings) for cf in extraction_result.config_files)
                total_patterns = sum(len(cf.patterns) for cf in extraction_result.config_files)

                logger.info(f"✅ Extracted {len(extraction_result.config_files)} config files "
                           f"with {total_settings} settings and {total_patterns} detected patterns")

                if 'ai_enhancements' in result_dict:
                    insights = result_dict['ai_enhancements'].get('overall_insights', {})
                    if insights.get('security_issues_found'):
                        logger.info(f"🔐 Security issues found: {insights['security_issues_found']}")

                logger.info(f"📁 Saved to: {config_output}")
            else:
                logger.info("No configuration files found")

        except Exception as e:
            logger.warning(f"Config pattern extraction failed: {e}")

    # Detect architectural patterns (C3.7)
    # Always run this - it provides high-level overview
    logger.info("Analyzing architectural patterns...")
    from skill_seekers.cli.architectural_pattern_detector import ArchitecturalPatternDetector

    arch_detector = ArchitecturalPatternDetector(enhance_with_ai=enhance_with_ai)
    arch_report = arch_detector.analyze(directory, results['files'])

    if arch_report.patterns:
        arch_output = output_dir / 'architecture'
        arch_output.mkdir(parents=True, exist_ok=True)

        # Save as JSON
        arch_json = arch_output / 'architectural_patterns.json'
        with open(arch_json, 'w', encoding='utf-8') as f:
            json.dump(arch_report.to_dict(), f, indent=2)

        logger.info(f"🏗️  Detected {len(arch_report.patterns)} architectural patterns")
        for pattern in arch_report.patterns:
            logger.info(f"   - {pattern.pattern_name} (confidence: {pattern.confidence:.2f})")
        logger.info(f"📁 Saved to: {arch_json}")
    else:
        logger.info("No clear architectural patterns detected")

    # Generate SKILL.md and references/ directory
    logger.info("Generating SKILL.md and references...")
    _generate_skill_md(
        output_dir=output_dir,
        directory=directory,
        results=results,
        depth=depth,
        build_api_reference=build_api_reference,
        build_dependency_graph=build_dependency_graph,
        detect_patterns=detect_patterns,
        extract_test_examples=extract_test_examples,
        extract_config_patterns=extract_config_patterns
    )

    return results


def _generate_skill_md(
    output_dir: Path,
    directory: Path,
    results: Dict[str, Any],
    depth: str,
    build_api_reference: bool,
    build_dependency_graph: bool,
    detect_patterns: bool,
    extract_test_examples: bool,
    extract_config_patterns: bool
):
    """
    Generate rich SKILL.md from codebase analysis results.

    Creates a 300+ line skill file with:
    - Front matter (name, description)
    - Repository info (path, languages, file count)
    - When to Use section
    - Quick Reference (patterns, languages, stats)
    - Code Examples (from test files)
    - API Reference (from code analysis)
    - Architecture Overview
    - Configuration Patterns
    - Available References
    """
    repo_name = directory.name

    # Generate skill name (lowercase, hyphens only, max 64 chars)
    skill_name = repo_name.lower().replace('_', '-').replace(' ', '-')[:64]

    # Generate description
    description = f"Local codebase analysis for {repo_name}"

    # Count files by language
    language_stats = _get_language_stats(results.get('files', []))
    total_files = len(results.get('files', []))

    # Start building content
    skill_content = f"""---
name: {skill_name}
description: {description}
---

# {repo_name} Codebase

## Description

Local codebase analysis and documentation generated from code analysis.

**Path:** `{directory}`
**Files Analyzed:** {total_files}
**Languages:** {', '.join(language_stats.keys())}
**Analysis Depth:** {depth}

## When to Use This Skill

Use this skill when you need to:
- Understand the codebase architecture and design patterns
- Find implementation examples and usage patterns
- Review API documentation extracted from code
- Check configuration patterns and best practices
- Explore test examples and real-world usage
- Navigate the codebase structure efficiently

## ⚡ Quick Reference

### Codebase Statistics

"""

    # Language breakdown
    skill_content += "**Languages:**\n"
    for lang, count in sorted(language_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_files * 100) if total_files > 0 else 0
        skill_content += f"- **{lang}**: {count} files ({percentage:.1f}%)\n"
    skill_content += "\n"

    # Analysis features performed
    skill_content += "**Analysis Performed:**\n"
    if build_api_reference:
        skill_content += "- ✅ API Reference (C2.5)\n"
    if build_dependency_graph:
        skill_content += "- ✅ Dependency Graph (C2.6)\n"
    if detect_patterns:
        skill_content += "- ✅ Design Patterns (C3.1)\n"
    if extract_test_examples:
        skill_content += "- ✅ Test Examples (C3.2)\n"
    if extract_config_patterns:
        skill_content += "- ✅ Configuration Patterns (C3.4)\n"
    skill_content += "- ✅ Architectural Analysis (C3.7)\n\n"

    # Add design patterns if available
    if detect_patterns:
        patterns_content = _format_patterns_section(output_dir)
        if patterns_content:
            skill_content += patterns_content

    # Add code examples if available
    if extract_test_examples:
        examples_content = _format_examples_section(output_dir)
        if examples_content:
            skill_content += examples_content

    # Add API reference if available
    if build_api_reference:
        api_content = _format_api_section(output_dir)
        if api_content:
            skill_content += api_content

    # Add architecture if available
    arch_content = _format_architecture_section(output_dir)
    if arch_content:
        skill_content += arch_content

    # Add configuration patterns if available
    if extract_config_patterns:
        config_content = _format_config_section(output_dir)
        if config_content:
            skill_content += config_content

    # Available references
    skill_content += "## 📚 Available References\n\n"
    skill_content += "This skill includes detailed reference documentation:\n\n"

    refs_added = False
    if build_api_reference and (output_dir / 'api_reference').exists():
        skill_content += "- **API Reference**: `references/api_reference/` - Complete API documentation\n"
        refs_added = True
    if build_dependency_graph and (output_dir / 'dependencies').exists():
        skill_content += "- **Dependencies**: `references/dependencies/` - Dependency graph and analysis\n"
        refs_added = True
    if detect_patterns and (output_dir / 'patterns').exists():
        skill_content += "- **Patterns**: `references/patterns/` - Detected design patterns\n"
        refs_added = True
    if extract_test_examples and (output_dir / 'test_examples').exists():
        skill_content += "- **Examples**: `references/test_examples/` - Usage examples from tests\n"
        refs_added = True
    if extract_config_patterns and (output_dir / 'config_patterns').exists():
        skill_content += "- **Configuration**: `references/config_patterns/` - Configuration patterns\n"
        refs_added = True
    if (output_dir / 'architecture').exists():
        skill_content += "- **Architecture**: `references/architecture/` - Architectural patterns\n"
        refs_added = True

    if not refs_added:
        skill_content += "No additional references generated (analysis features disabled).\n"

    skill_content += "\n"

    # Footer
    skill_content += "---\n\n"
    skill_content += "**Generated by Skill Seeker** | Codebase Analyzer with C3.x Analysis\n"

    # Write SKILL.md
    skill_path = output_dir / "SKILL.md"
    skill_path.write_text(skill_content, encoding='utf-8')

    line_count = len(skill_content.split('\n'))
    logger.info(f"✅ Generated SKILL.md: {skill_path} ({line_count} lines)")

    # Generate references/ directory structure
    _generate_references(output_dir)


def _get_language_stats(files: List[Dict]) -> Dict[str, int]:
    """Count files by language from analysis results."""
    stats = {}
    for file_data in files:
        # files is a list of dicts with 'language' key
        lang = file_data.get('language', 'Unknown')
        if lang != 'Unknown':
            stats[lang] = stats.get(lang, 0) + 1
    return stats


def _format_patterns_section(output_dir: Path) -> str:
    """Format design patterns section from patterns/detected_patterns.json."""
    patterns_file = output_dir / 'patterns' / 'detected_patterns.json'
    if not patterns_file.exists():
        return ""

    try:
        with open(patterns_file, 'r', encoding='utf-8') as f:
            patterns_data = json.load(f)
    except Exception:
        return ""

    if not patterns_data:
        return ""

    # Count patterns by type (deduplicate by class, keep highest confidence)
    pattern_counts = {}
    by_class = {}

    for pattern_file in patterns_data:
        for pattern in pattern_file.get('patterns', []):
            ptype = pattern.get('pattern_type', 'Unknown')
            cls = pattern.get('class_name', '')
            confidence = pattern.get('confidence', 0)

            # Skip low confidence
            if confidence < 0.7:
                continue

            # Deduplicate by class
            key = f"{cls}:{ptype}"
            if key not in by_class or by_class[key]['confidence'] < confidence:
                by_class[key] = pattern

            # Count by type
            pattern_counts[ptype] = pattern_counts.get(ptype, 0) + 1

    if not pattern_counts:
        return ""

    content = "### 🎨 Design Patterns Detected\n\n"
    content += "*From C3.1 codebase analysis (confidence > 0.7)*\n\n"

    # Top 5 pattern types
    for ptype, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        content += f"- **{ptype}**: {count} instances\n"

    content += f"\n*Total: {len(by_class)} high-confidence patterns*\n\n"
    content += "*See `references/patterns/` for complete pattern analysis*\n\n"
    return content


def _format_examples_section(output_dir: Path) -> str:
    """Format code examples section from test_examples/test_examples.json."""
    examples_file = output_dir / 'test_examples' / 'test_examples.json'
    if not examples_file.exists():
        return ""

    try:
        with open(examples_file, 'r', encoding='utf-8') as f:
            examples_data = json.load(f)
    except Exception:
        return ""

    examples = examples_data.get('examples', [])
    if not examples:
        return ""

    # Filter high-value examples (complexity > 0.7)
    high_value = [ex for ex in examples if ex.get('complexity_score', 0) > 0.7]

    if not high_value:
        # If no high complexity, take any examples
        high_value = examples[:10]

    if not high_value:
        return ""

    content = "## 📝 Code Examples\n\n"
    content += "*High-quality examples extracted from test files (C3.2)*\n\n"

    # Top 10 examples
    for ex in sorted(high_value, key=lambda x: x.get('complexity_score', 0), reverse=True)[:10]:
        desc = ex.get('description', 'Example')
        lang = ex.get('language', 'python').lower()
        code = ex.get('code', '')
        complexity = ex.get('complexity_score', 0)

        content += f"**{desc}** (complexity: {complexity:.2f})\n\n"
        content += f"```{lang}\n{code}\n```\n\n"

    content += "*See `references/test_examples/` for all extracted examples*\n\n"
    return content


def _format_api_section(output_dir: Path) -> str:
    """Format API reference section."""
    api_dir = output_dir / 'api_reference'
    if not api_dir.exists():
        return ""

    api_md = api_dir / 'api_reference.md'
    if not api_md.exists():
        return ""

    try:
        api_content = api_md.read_text(encoding='utf-8')
    except Exception:
        return ""

    # Extract first section (up to 500 chars)
    preview = api_content[:500]
    if len(api_content) > 500:
        preview += "..."

    content = "## 🔧 API Reference\n\n"
    content += "*Extracted from codebase analysis (C2.5)*\n\n"
    content += preview + "\n\n"
    content += "*See `references/api_reference/` for complete API documentation*\n\n"
    return content


def _format_architecture_section(output_dir: Path) -> str:
    """Format architecture section from architecture/architectural_patterns.json."""
    arch_file = output_dir / 'architecture' / 'architectural_patterns.json'
    if not arch_file.exists():
        return ""

    try:
        with open(arch_file, 'r', encoding='utf-8') as f:
            arch_data = json.load(f)
    except Exception:
        return ""

    patterns = arch_data.get('patterns', [])
    if not patterns:
        return ""

    content = "## 🏗️ Architecture Overview\n\n"
    content += "*From C3.7 architectural analysis*\n\n"

    content += "**Detected Architectural Patterns:**\n\n"
    for pattern in patterns[:5]:
        name = pattern.get('pattern_name', 'Unknown')
        confidence = pattern.get('confidence', 0)
        indicators = pattern.get('indicators', [])

        content += f"- **{name}** (confidence: {confidence:.2f})\n"
        if indicators:
            content += f"  - Indicators: {', '.join(indicators[:3])}\n"

    content += f"\n*Total: {len(patterns)} architectural patterns detected*\n\n"
    content += "*See `references/architecture/` for complete architectural analysis*\n\n"
    return content


def _format_config_section(output_dir: Path) -> str:
    """Format configuration patterns section."""
    config_file = output_dir / 'config_patterns' / 'config_patterns.json'
    if not config_file.exists():
        return ""

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except Exception:
        return ""

    config_files = config_data.get('config_files', [])
    if not config_files:
        return ""

    total_settings = sum(len(cf.get('settings', [])) for cf in config_files)
    total_patterns = sum(len(cf.get('patterns', [])) for cf in config_files)

    content = "## ⚙️ Configuration Patterns\n\n"
    content += "*From C3.4 configuration analysis*\n\n"
    content += f"**Configuration Files Analyzed:** {len(config_files)}\n"
    content += f"**Total Settings:** {total_settings}\n"
    content += f"**Patterns Detected:** {total_patterns}\n\n"

    # List config file types found
    file_types = {}
    for cf in config_files:
        ctype = cf.get('config_type', 'unknown')
        file_types[ctype] = file_types.get(ctype, 0) + 1

    if file_types:
        content += "**Configuration Types:**\n"
        for ctype, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
            content += f"- {ctype}: {count} files\n"
        content += "\n"

    content += "*See `references/config_patterns/` for detailed configuration analysis*\n\n"
    return content


def _generate_references(output_dir: Path):
    """
    Generate references/ directory structure by symlinking analysis output.

    Creates a clean references/ directory that links to all analysis outputs.
    """
    references_dir = output_dir / 'references'
    references_dir.mkdir(exist_ok=True)

    # Map analysis directories to reference names
    mappings = {
        'api_reference': 'api_reference',
        'dependencies': 'dependencies',
        'patterns': 'patterns',
        'test_examples': 'test_examples',
        'tutorials': 'tutorials',
        'config_patterns': 'config_patterns',
        'architecture': 'architecture'
    }

    for source, target in mappings.items():
        source_dir = output_dir / source
        target_dir = references_dir / target

        if source_dir.exists() and source_dir.is_dir():
            # Copy directory to references/ (not symlink, for portability)
            if target_dir.exists():
                import shutil
                shutil.rmtree(target_dir)

            import shutil
            shutil.copytree(source_dir, target_dir)
            logger.debug(f"Copied {source} → references/{target}")

    logger.info(f"✅ Generated references directory: {references_dir}")


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

  # Full analysis with all features (default)
  codebase-scraper --directory . --depth deep

  # Surface analysis (fast, skip all analysis features)
  codebase-scraper --directory . --depth surface --skip-api-reference --skip-dependency-graph --skip-patterns --skip-test-examples

  # Skip specific features
  codebase-scraper --directory . --skip-patterns --skip-test-examples
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
        '--skip-api-reference',
        action='store_true',
        default=False,
        help='Skip API reference markdown documentation generation (default: enabled)'
    )
    parser.add_argument(
        '--skip-dependency-graph',
        action='store_true',
        default=False,
        help='Skip dependency graph and circular dependency detection (default: enabled)'
    )
    parser.add_argument(
        '--skip-patterns',
        action='store_true',
        default=False,
        help='Skip design pattern detection (Singleton, Factory, Observer, etc.) (default: enabled)'
    )
    parser.add_argument(
        '--skip-test-examples',
        action='store_true',
        default=False,
        help='Skip test example extraction (instantiation, method calls, configs, etc.) (default: enabled)'
    )
    parser.add_argument(
        '--skip-how-to-guides',
        action='store_true',
        default=False,
        help='Skip how-to guide generation from workflow examples (default: enabled)'
    )
    parser.add_argument(
        '--skip-config-patterns',
        action='store_true',
        default=False,
        help='Skip configuration pattern extraction from config files (JSON, YAML, TOML, ENV, etc.) (default: enabled)'
    )
    parser.add_argument(
        '--ai-mode',
        choices=['auto', 'api', 'local', 'none'],
        default='auto',
        help='AI enhancement mode for how-to guides: auto (detect best), api (Claude API), local (Claude Code CLI), none (disable) (default: auto)'
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

    # Check for deprecated flags
    deprecated_flags = {
        '--build-api-reference': '--skip-api-reference',
        '--build-dependency-graph': '--skip-dependency-graph',
        '--detect-patterns': '--skip-patterns',
        '--extract-test-examples': '--skip-test-examples',
        '--build-how-to-guides': '--skip-how-to-guides',
        '--extract-config-patterns': '--skip-config-patterns'
    }

    for old_flag, new_flag in deprecated_flags.items():
        if old_flag in sys.argv:
            logger.warning(f"⚠️  DEPRECATED: {old_flag} is deprecated. "
                          f"All features are now enabled by default. "
                          f"Use {new_flag} to disable this feature.")

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
            build_api_reference=not args.skip_api_reference,
            extract_comments=not args.no_comments,
            build_dependency_graph=not args.skip_dependency_graph,
            detect_patterns=not args.skip_patterns,
            extract_test_examples=not args.skip_test_examples,
            build_how_to_guides=not args.skip_how_to_guides,
            extract_config_patterns=not args.skip_config_patterns,
            enhance_with_ai=True,  # Auto-disables if no API key present
            ai_mode=args.ai_mode  # NEW: AI enhancement mode for how-to guides
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
