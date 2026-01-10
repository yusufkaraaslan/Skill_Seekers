#!/usr/bin/env python3
"""
Dependency Graph Analyzer (C2.6)

Analyzes import/require/include/use statements to build dependency graphs.
Supports 9 programming languages with language-specific extraction.

Features:
- Multi-language import extraction (Python AST, others regex-based)
- Dependency graph construction with NetworkX
- Circular dependency detection
- Graph export (JSON, DOT/GraphViz, Mermaid)
- Strongly connected component analysis

Supported Languages:
- Python: import, from...import, relative imports (AST-based)
- JavaScript/TypeScript: ES6 import, CommonJS require (regex-based)
- C/C++: #include directives (regex-based)
- C#: using statements (regex, based on MS C# spec)
- Go: import statements (regex, based on Go language spec)
- Rust: use statements (regex, based on Rust reference)
- Java: import statements (regex, based on Oracle Java spec)
- Ruby: require/require_relative/load (regex, based on Ruby docs)
- PHP: require/include/use (regex, based on PHP reference)

Usage:
    from dependency_analyzer import DependencyAnalyzer

    analyzer = DependencyAnalyzer()
    analyzer.analyze_file('src/main.py', content, 'Python')
    analyzer.analyze_file('src/utils.go', go_content, 'Go')
    graph = analyzer.build_graph()
    cycles = analyzer.detect_cycles()

Credits:
- Regex patterns inspired by official language specifications
- NetworkX for graph algorithms: https://networkx.org/
"""

import re
import ast
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class DependencyInfo:
    """Information about a single dependency relationship."""
    source_file: str
    imported_module: str
    import_type: str  # 'import', 'from', 'require', 'include'
    is_relative: bool = False
    line_number: int = 0


@dataclass
class FileNode:
    """Represents a file node in the dependency graph."""
    file_path: str
    language: str
    dependencies: List[str] = field(default_factory=list)
    imported_by: List[str] = field(default_factory=list)


class DependencyAnalyzer:
    """
    Multi-language dependency analyzer using NetworkX.

    Analyzes import/require/include statements and builds dependency graphs
    with circular dependency detection.
    """

    def __init__(self):
        """Initialize dependency analyzer."""
        if not NETWORKX_AVAILABLE:
            raise ImportError(
                "NetworkX is required for dependency analysis. "
                "Install with: pip install networkx"
            )

        self.graph = nx.DiGraph()  # Directed graph for dependencies
        self.file_dependencies: Dict[str, List[DependencyInfo]] = {}
        self.file_nodes: Dict[str, FileNode] = {}

    def analyze_file(self, file_path: str, content: str, language: str) -> List[DependencyInfo]:
        """
        Extract dependencies from a source file.

        Args:
            file_path: Path to source file
            content: File content
            language: Programming language (Python, JavaScript, TypeScript, C, C++, C#, Go, Rust, Java, Ruby, PHP)

        Returns:
            List of DependencyInfo objects
        """
        if language == 'Python':
            deps = self._extract_python_imports(content, file_path)
        elif language in ('JavaScript', 'TypeScript'):
            deps = self._extract_js_imports(content, file_path)
        elif language in ('C++', 'C'):
            deps = self._extract_cpp_includes(content, file_path)
        elif language == 'C#':
            deps = self._extract_csharp_imports(content, file_path)
        elif language == 'Go':
            deps = self._extract_go_imports(content, file_path)
        elif language == 'Rust':
            deps = self._extract_rust_imports(content, file_path)
        elif language == 'Java':
            deps = self._extract_java_imports(content, file_path)
        elif language == 'Ruby':
            deps = self._extract_ruby_imports(content, file_path)
        elif language == 'PHP':
            deps = self._extract_php_imports(content, file_path)
        else:
            logger.warning(f"Unsupported language: {language}")
            deps = []

        self.file_dependencies[file_path] = deps

        # Create file node
        imported_modules = [dep.imported_module for dep in deps]
        self.file_nodes[file_path] = FileNode(
            file_path=file_path,
            language=language,
            dependencies=imported_modules
        )

        return deps

    def _extract_python_imports(self, content: str, file_path: str) -> List[DependencyInfo]:
        """
        Extract Python import statements using AST.

        Handles:
        - import module
        - import module as alias
        - from module import name
        - from . import relative
        """
        deps = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            logger.warning(f"Syntax error in {file_path}, skipping import extraction")
            return deps

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    deps.append(DependencyInfo(
                        source_file=file_path,
                        imported_module=alias.name,
                        import_type='import',
                        is_relative=False,
                        line_number=node.lineno
                    ))

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                is_relative = node.level > 0

                # Handle relative imports
                if is_relative:
                    module = '.' * node.level + module

                deps.append(DependencyInfo(
                    source_file=file_path,
                    imported_module=module,
                    import_type='from',
                    is_relative=is_relative,
                    line_number=node.lineno
                ))

        return deps

    def _extract_js_imports(self, content: str, file_path: str) -> List[DependencyInfo]:
        """
        Extract JavaScript/TypeScript import statements.

        Handles:
        - import x from 'module'
        - import { x } from 'module'
        - import * as x from 'module'
        - const x = require('module')
        - require('module')
        """
        deps = []

        # ES6 imports: import ... from 'module'
        import_pattern = r"import\s+(?:[\w\s{},*]+\s+from\s+)?['\"]([^'\"]+)['\"]"
        for match in re.finditer(import_pattern, content):
            module = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            is_relative = module.startswith('.') or module.startswith('/')

            deps.append(DependencyInfo(
                source_file=file_path,
                imported_module=module,
                import_type='import',
                is_relative=is_relative,
                line_number=line_num
            ))

        # CommonJS requires: require('module')
        require_pattern = r"require\s*\(['\"]([^'\"]+)['\"]\)"
        for match in re.finditer(require_pattern, content):
            module = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            is_relative = module.startswith('.') or module.startswith('/')

            deps.append(DependencyInfo(
                source_file=file_path,
                imported_module=module,
                import_type='require',
                is_relative=is_relative,
                line_number=line_num
            ))

        return deps

    def _extract_cpp_includes(self, content: str, file_path: str) -> List[DependencyInfo]:
        """
        Extract C++ #include directives.

        Handles:
        - #include "local/header.h"
        - #include <system/header.h>
        """
        deps = []

        # Match #include statements
        include_pattern = r'#include\s+[<"]([^>"]+)[>"]'
        for match in re.finditer(include_pattern, content):
            header = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Headers with "" are usually local, <> are system headers
            is_relative = '"' in match.group(0)

            deps.append(DependencyInfo(
                source_file=file_path,
                imported_module=header,
                import_type='include',
                is_relative=is_relative,
                line_number=line_num
            ))

        return deps

    def _extract_csharp_imports(self, content: str, file_path: str) -> List[DependencyInfo]:
        """
        Extract C# using statements.

        Handles:
        - using System;
        - using MyNamespace;
        - using static MyClass;
        - using alias = Namespace;

        Regex patterns based on C# language specification:
        https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/using-directive
        """
        deps = []

        # Match using statements: using [static] Namespace[.Type];
        using_pattern = r'using\s+(?:static\s+)?(?:(\w+)\s*=\s*)?([A-Za-z_][\w.]*)\s*;'
        for match in re.finditer(using_pattern, content):
            alias = match.group(1)  # Optional alias
            namespace = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            # Skip 'using' statements for IDisposable (using var x = ...)
            if '=' in match.group(0) and not alias:
                continue

            deps.append(DependencyInfo(
                source_file=file_path,
                imported_module=namespace,
                import_type='using',
                is_relative=False,  # C# uses absolute namespaces
                line_number=line_num
            ))

        return deps

    def _extract_go_imports(self, content: str, file_path: str) -> List[DependencyInfo]:
        """
        Extract Go import statements.

        Handles:
        - import "package"
        - import alias "package"
        - import ( "pkg1" "pkg2" )

        Regex patterns based on Go language specification:
        https://go.dev/ref/spec#Import_declarations
        """
        deps = []

        # Single import: import [alias] "package"
        single_import_pattern = r'import\s+(?:(\w+)\s+)?"([^"]+)"'
        for match in re.finditer(single_import_pattern, content):
            alias = match.group(1)  # Optional alias
            package = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            # Check if relative (starts with ./ or ../)
            is_relative = package.startswith('./')

            deps.append(DependencyInfo(
                source_file=file_path,
                imported_module=package,
                import_type='import',
                is_relative=is_relative,
                line_number=line_num
            ))

        # Multi-import block: import ( ... )
        multi_import_pattern = r'import\s*\((.*?)\)'
        for match in re.finditer(multi_import_pattern, content, re.DOTALL):
            block = match.group(1)
            block_start = match.start()

            # Extract individual imports from block
            import_line_pattern = r'(?:(\w+)\s+)?"([^"]+)"'
            for line_match in re.finditer(import_line_pattern, block):
                alias = line_match.group(1)
                package = line_match.group(2)
                line_num = content[:block_start + line_match.start()].count('\n') + 1

                is_relative = package.startswith('./')

                deps.append(DependencyInfo(
                    source_file=file_path,
                    imported_module=package,
                    import_type='import',
                    is_relative=is_relative,
                    line_number=line_num
                ))

        return deps

    def _extract_rust_imports(self, content: str, file_path: str) -> List[DependencyInfo]:
        """
        Extract Rust use statements.

        Handles:
        - use std::collections::HashMap;
        - use crate::module;
        - use super::sibling;
        - use self::child;

        Regex patterns based on Rust reference:
        https://doc.rust-lang.org/reference/items/use-declarations.html
        """
        deps = []

        # Match use statements: use path::to::item; (including curly braces with spaces)
        # This pattern matches: use word::word; or use word::{item, item};
        use_pattern = r'use\s+([\w:{}]+(?:\s*,\s*[\w:{}]+)*|[\w:]+::\{[^}]+\})\s*;'
        for match in re.finditer(use_pattern, content):
            module_path = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Determine if relative
            is_relative = module_path.startswith(('self::', 'super::'))

            # Handle curly brace imports (use std::{io, fs})
            if '{' in module_path:
                # Extract base path
                base_path = module_path.split('{')[0].rstrip(':')
                # Extract items inside braces
                items_match = re.search(r'\{([^}]+)\}', module_path)
                if items_match:
                    items = [item.strip() for item in items_match.group(1).split(',')]
                    for item in items:
                        full_path = f"{base_path}::{item}" if base_path else item
                        deps.append(DependencyInfo(
                            source_file=file_path,
                            imported_module=full_path,
                            import_type='use',
                            is_relative=is_relative,
                            line_number=line_num
                        ))
            else:
                deps.append(DependencyInfo(
                    source_file=file_path,
                    imported_module=module_path,
                    import_type='use',
                    is_relative=is_relative,
                    line_number=line_num
                ))

        return deps

    def _extract_java_imports(self, content: str, file_path: str) -> List[DependencyInfo]:
        """
        Extract Java import statements.

        Handles:
        - import java.util.List;
        - import java.util.*;
        - import static java.lang.Math.PI;

        Regex patterns based on Java language specification:
        https://docs.oracle.com/javase/specs/jls/se17/html/jls-7.html#jls-7.5
        """
        deps = []

        # Match import statements: import [static] package.Class;
        import_pattern = r'import\s+(?:static\s+)?([A-Za-z_][\w.]*(?:\.\*)?)\s*;'
        for match in re.finditer(import_pattern, content):
            import_path = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            deps.append(DependencyInfo(
                source_file=file_path,
                imported_module=import_path,
                import_type='import',
                is_relative=False,  # Java uses absolute package names
                line_number=line_num
            ))

        return deps

    def _extract_ruby_imports(self, content: str, file_path: str) -> List[DependencyInfo]:
        """
        Extract Ruby require/require_relative/load statements.

        Handles:
        - require 'gem_name'
        - require_relative 'file'
        - load 'script.rb'

        Regex patterns based on Ruby documentation:
        https://ruby-doc.org/core/Kernel.html#method-i-require
        """
        deps = []

        # Match require: require 'module' or require "module"
        require_pattern = r"require\s+['\"]([^'\"]+)['\"]"
        for match in re.finditer(require_pattern, content):
            module = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            deps.append(DependencyInfo(
                source_file=file_path,
                imported_module=module,
                import_type='require',
                is_relative=False,  # require looks in load path
                line_number=line_num
            ))

        # Match require_relative: require_relative 'file'
        require_relative_pattern = r"require_relative\s+['\"]([^'\"]+)['\"]"
        for match in re.finditer(require_relative_pattern, content):
            module = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            deps.append(DependencyInfo(
                source_file=file_path,
                imported_module=module,
                import_type='require_relative',
                is_relative=True,
                line_number=line_num
            ))

        # Match load: load 'script.rb'
        load_pattern = r"load\s+['\"]([^'\"]+)['\"]"
        for match in re.finditer(load_pattern, content):
            module = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            deps.append(DependencyInfo(
                source_file=file_path,
                imported_module=module,
                import_type='load',
                is_relative=True,  # load is usually relative
                line_number=line_num
            ))

        return deps

    def _extract_php_imports(self, content: str, file_path: str) -> List[DependencyInfo]:
        """
        Extract PHP require/include/use statements.

        Handles:
        - require 'file.php';
        - require_once 'file.php';
        - include 'file.php';
        - include_once 'file.php';
        - use Namespace\\Class;

        Regex patterns based on PHP language reference:
        https://www.php.net/manual/en/function.require.php
        """
        deps = []

        # Match require/include: require[_once] 'file' or require[_once] "file"
        require_pattern = r"(?:require|include)(?:_once)?\s+['\"]([^'\"]+)['\"]"
        for match in re.finditer(require_pattern, content):
            module = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Determine import type
            import_type = 'require' if 'require' in match.group(0) else 'include'

            # PHP file paths are relative by default
            is_relative = not module.startswith(('/', 'http://', 'https://'))

            deps.append(DependencyInfo(
                source_file=file_path,
                imported_module=module,
                import_type=import_type,
                is_relative=is_relative,
                line_number=line_num
            ))

        # Match namespace use: use Namespace\Class;
        use_pattern = r'use\s+([A-Za-z_][\w\\]*)\s*(?:as\s+\w+)?\s*;'
        for match in re.finditer(use_pattern, content):
            namespace = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            deps.append(DependencyInfo(
                source_file=file_path,
                imported_module=namespace,
                import_type='use',
                is_relative=False,  # Namespaces are absolute
                line_number=line_num
            ))

        return deps

    def build_graph(self) -> nx.DiGraph:
        """
        Build dependency graph from analyzed files.

        Returns:
            NetworkX DiGraph with file dependencies
        """
        self.graph.clear()

        # Add all file nodes
        for file_path, node in self.file_nodes.items():
            self.graph.add_node(file_path, language=node.language)

        # Add dependency edges
        for file_path, deps in self.file_dependencies.items():
            for dep in deps:
                # Try to resolve the imported module to an actual file
                target = self._resolve_import(file_path, dep.imported_module, dep.is_relative)

                if target and target in self.file_nodes:
                    # Add edge from source to dependency
                    self.graph.add_edge(
                        file_path,
                        target,
                        import_type=dep.import_type,
                        line_number=dep.line_number
                    )

                    # Update imported_by lists
                    if target in self.file_nodes:
                        self.file_nodes[target].imported_by.append(file_path)

        return self.graph

    def _resolve_import(self, source_file: str, imported_module: str, is_relative: bool) -> Optional[str]:
        """
        Resolve import statement to actual file path.

        This is a simplified resolution - a full implementation would need
        to handle module resolution rules for each language.
        """
        # For now, just return the imported module if it exists in our file_nodes
        # In a real implementation, this would resolve relative paths, handle
        # module resolution (node_modules, Python packages, etc.)

        if imported_module in self.file_nodes:
            return imported_module

        # Try common variations
        variations = [
            imported_module,
            f"{imported_module}.py",
            f"{imported_module}.js",
            f"{imported_module}.ts",
            f"{imported_module}.h",
            f"{imported_module}.cpp",
        ]

        for var in variations:
            if var in self.file_nodes:
                return var

        return None

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect circular dependencies in the graph.

        Returns:
            List of cycles, where each cycle is a list of file paths
        """
        try:
            cycles = list(nx.simple_cycles(self.graph))
            if cycles:
                logger.warning(f"Found {len(cycles)} circular dependencies")
                for cycle in cycles:
                    logger.warning(f"  Cycle: {' -> '.join(cycle)} -> {cycle[0]}")
            return cycles
        except Exception as e:
            logger.error(f"Error detecting cycles: {e}")
            return []

    def get_strongly_connected_components(self) -> List[Set[str]]:
        """
        Get strongly connected components (groups of mutually dependent files).

        Returns:
            List of sets, each containing file paths in a component
        """
        return list(nx.strongly_connected_components(self.graph))

    def export_dot(self, output_path: str):
        """
        Export graph as GraphViz DOT format.

        Args:
            output_path: Path to save .dot file
        """
        try:
            from networkx.drawing.nx_pydot import write_dot
            write_dot(self.graph, output_path)
            logger.info(f"Exported graph to DOT format: {output_path}")
        except ImportError:
            logger.warning("pydot not installed - cannot export to DOT format")
            logger.warning("Install with: pip install pydot")

    def export_json(self) -> Dict[str, Any]:
        """
        Export graph as JSON structure.

        Returns:
            Dictionary with nodes and edges
        """
        return {
            'nodes': [
                {
                    'file': node,
                    'language': data.get('language', 'Unknown')
                }
                for node, data in self.graph.nodes(data=True)
            ],
            'edges': [
                {
                    'source': source,
                    'target': target,
                    'import_type': data.get('import_type', 'unknown'),
                    'line_number': data.get('line_number', 0)
                }
                for source, target, data in self.graph.edges(data=True)
            ]
        }

    def export_mermaid(self) -> str:
        """
        Export graph as Mermaid diagram format.

        Returns:
            Mermaid diagram as string
        """
        lines = ['graph TD']

        # Create node labels (shorten file paths for readability)
        node_ids = {}
        for i, node in enumerate(self.graph.nodes()):
            node_id = f"N{i}"
            node_ids[node] = node_id
            label = Path(node).name  # Just filename
            lines.append(f"    {node_id}[{label}]")

        # Add edges
        for source, target in self.graph.edges():
            source_id = node_ids[source]
            target_id = node_ids[target]
            lines.append(f"    {source_id} --> {target_id}")

        return '\n'.join(lines)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get graph statistics.

        Returns:
            Dictionary with various statistics
        """
        return {
            'total_files': self.graph.number_of_nodes(),
            'total_dependencies': self.graph.number_of_edges(),
            'circular_dependencies': len(self.detect_cycles()),
            'strongly_connected_components': len(self.get_strongly_connected_components()),
            'avg_dependencies_per_file': (
                self.graph.number_of_edges() / self.graph.number_of_nodes()
                if self.graph.number_of_nodes() > 0 else 0
            ),
            'files_with_no_dependencies': len([
                node for node in self.graph.nodes()
                if self.graph.out_degree(node) == 0
            ]),
            'files_not_imported': len([
                node for node in self.graph.nodes()
                if self.graph.in_degree(node) == 0
            ]),
        }
