#!/usr/bin/env python3
"""
Code Analyzer for GitHub Repositories

Extracts code signatures at configurable depth levels:
- surface: File tree only (existing behavior)
- deep: Parse files for signatures, parameters, types
- full: Complete AST analysis (future enhancement)

Supports 9 programming languages with language-specific parsers:
- Python (AST-based, production quality)
- JavaScript/TypeScript (regex-based)
- C/C++ (regex-based)
- C# (regex-based, inspired by Microsoft C# spec)
- Go (regex-based, Go language spec)
- Rust (regex-based, Rust reference)
- Java (regex-based, Oracle Java spec)
- Ruby (regex-based, Ruby documentation)
- PHP (regex-based, PHP reference)

Note: Regex-based parsers are simplified implementations. For production use,
consider using dedicated parsers (tree-sitter, language-specific AST libraries).
"""

import ast
import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Parameter:
    """Represents a function parameter."""
    name: str
    type_hint: Optional[str] = None
    default: Optional[str] = None


@dataclass
class FunctionSignature:
    """Represents a function/method signature."""
    name: str
    parameters: List[Parameter]
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    line_number: Optional[int] = None
    is_async: bool = False
    is_method: bool = False
    decorators: List[str] = None

    def __post_init__(self):
        if self.decorators is None:
            self.decorators = []


@dataclass
class ClassSignature:
    """Represents a class signature."""
    name: str
    base_classes: List[str]
    methods: List[FunctionSignature]
    docstring: Optional[str] = None
    line_number: Optional[int] = None


class CodeAnalyzer:
    """
    Analyzes code at different depth levels.
    """

    def __init__(self, depth: str = 'surface'):
        """
        Initialize code analyzer.

        Args:
            depth: Analysis depth ('surface', 'deep', 'full')
        """
        self.depth = depth

    def analyze_file(self, file_path: str, content: str, language: str) -> Dict[str, Any]:
        """
        Analyze a single file based on depth level.

        Args:
            file_path: Path to file in repository
            content: File content as string
            language: Programming language (Python, JavaScript, C#, Go, Rust, Java, Ruby, PHP, etc.)

        Returns:
            Dict containing extracted signatures
        """
        if self.depth == 'surface':
            return {}  # Surface level doesn't analyze individual files

        logger.debug(f"Analyzing {file_path} (language: {language}, depth: {self.depth})")

        try:
            if language == 'Python':
                return self._analyze_python(content, file_path)
            elif language in ['JavaScript', 'TypeScript']:
                return self._analyze_javascript(content, file_path)
            elif language in ['C', 'C++']:
                return self._analyze_cpp(content, file_path)
            elif language == 'C#':
                return self._analyze_csharp(content, file_path)
            elif language == 'Go':
                return self._analyze_go(content, file_path)
            elif language == 'Rust':
                return self._analyze_rust(content, file_path)
            elif language == 'Java':
                return self._analyze_java(content, file_path)
            elif language == 'Ruby':
                return self._analyze_ruby(content, file_path)
            elif language == 'PHP':
                return self._analyze_php(content, file_path)
            else:
                logger.debug(f"No analyzer for language: {language}")
                return {}
        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")
            return {}

    def _analyze_python(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze Python file using AST."""
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.debug(f"Syntax error in {file_path}: {e}")
            return {}

        classes = []
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_sig = self._extract_python_class(node)
                classes.append(asdict(class_sig))
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Only top-level functions (not methods)
                # Fix AST parser to check isinstance(parent.body, list) before 'in' operator
                is_method = False
                try:
                    is_method = any(isinstance(parent, ast.ClassDef)
                                  for parent in ast.walk(tree)
                                  if hasattr(parent, 'body') and isinstance(parent.body, list) and node in parent.body)
                except (TypeError, AttributeError):
                    # If body is not iterable or check fails, assume it's a top-level function
                    is_method = False

                if not is_method:
                    func_sig = self._extract_python_function(node)
                    functions.append(asdict(func_sig))

        # Extract comments
        comments = self._extract_python_comments(content)

        return {
            'classes': classes,
            'functions': functions,
            'comments': comments
        }

    def _extract_python_class(self, node: ast.ClassDef) -> ClassSignature:
        """Extract class signature from AST node."""
        # Extract base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{base.value.id}.{base.attr}" if hasattr(base.value, 'id') else base.attr)

        # Extract methods
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_sig = self._extract_python_function(item, is_method=True)
                methods.append(method_sig)

        # Extract docstring
        docstring = ast.get_docstring(node)

        return ClassSignature(
            name=node.name,
            base_classes=bases,
            methods=methods,
            docstring=docstring,
            line_number=node.lineno
        )

    def _extract_python_function(self, node, is_method: bool = False) -> FunctionSignature:
        """Extract function signature from AST node."""
        # Extract parameters
        params = []
        for arg in node.args.args:
            param_type = None
            if arg.annotation:
                param_type = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else None

            params.append(Parameter(
                name=arg.arg,
                type_hint=param_type
            ))

        # Extract defaults
        defaults = node.args.defaults
        if defaults:
            # Defaults are aligned to the end of params
            num_no_default = len(params) - len(defaults)
            for i, default in enumerate(defaults):
                param_idx = num_no_default + i
                if param_idx < len(params):
                    try:
                        params[param_idx].default = ast.unparse(default) if hasattr(ast, 'unparse') else str(default)
                    except:
                        params[param_idx].default = "..."

        # Extract return type
        return_type = None
        if node.returns:
            try:
                return_type = ast.unparse(node.returns) if hasattr(ast, 'unparse') else None
            except:
                pass

        # Extract decorators
        decorators = []
        for decorator in node.decorator_list:
            try:
                if hasattr(ast, 'unparse'):
                    decorators.append(ast.unparse(decorator))
                elif isinstance(decorator, ast.Name):
                    decorators.append(decorator.id)
            except:
                pass

        # Extract docstring
        docstring = ast.get_docstring(node)

        return FunctionSignature(
            name=node.name,
            parameters=params,
            return_type=return_type,
            docstring=docstring,
            line_number=node.lineno,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_method=is_method,
            decorators=decorators
        )

    def _analyze_javascript(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Analyze JavaScript/TypeScript file using regex patterns.

        Note: This is a simplified approach. For production, consider using
        a proper JS/TS parser like esprima or ts-morph.
        """
        classes = []
        functions = []

        # Extract class definitions
        class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            base_class = match.group(2) if match.group(2) else None

            # Try to extract methods (simplified)
            class_block_start = match.end()
            # This is a simplification - proper parsing would track braces
            class_block_end = content.find('}', class_block_start)
            if class_block_end != -1:
                class_body = content[class_block_start:class_block_end]
                methods = self._extract_js_methods(class_body)
            else:
                methods = []

            classes.append({
                'name': class_name,
                'base_classes': [base_class] if base_class else [],
                'methods': methods,
                'docstring': None,
                'line_number': content[:match.start()].count('\n') + 1
            })

        # Extract top-level functions
        func_pattern = r'(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(func_pattern, content):
            func_name = match.group(1)
            params_str = match.group(2)
            is_async = 'async' in match.group(0)

            params = self._parse_js_parameters(params_str)

            functions.append({
                'name': func_name,
                'parameters': params,
                'return_type': None,  # JS doesn't have type annotations (unless TS)
                'docstring': None,
                'line_number': content[:match.start()].count('\n') + 1,
                'is_async': is_async,
                'is_method': False,
                'decorators': []
            })

        # Extract arrow functions assigned to const/let
        arrow_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>'
        for match in re.finditer(arrow_pattern, content):
            func_name = match.group(1)
            params_str = match.group(2)
            is_async = 'async' in match.group(0)

            params = self._parse_js_parameters(params_str)

            functions.append({
                'name': func_name,
                'parameters': params,
                'return_type': None,
                'docstring': None,
                'line_number': content[:match.start()].count('\n') + 1,
                'is_async': is_async,
                'is_method': False,
                'decorators': []
            })

        # Extract comments
        comments = self._extract_js_comments(content)

        return {
            'classes': classes,
            'functions': functions,
            'comments': comments
        }

    def _extract_js_methods(self, class_body: str) -> List[Dict]:
        """Extract method signatures from class body."""
        methods = []

        # Match method definitions
        method_pattern = r'(?:async\s+)?(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(method_pattern, class_body):
            method_name = match.group(1)
            params_str = match.group(2)
            is_async = 'async' in match.group(0)

            # Skip constructor keyword detection
            if method_name in ['if', 'for', 'while', 'switch']:
                continue

            params = self._parse_js_parameters(params_str)

            methods.append({
                'name': method_name,
                'parameters': params,
                'return_type': None,
                'docstring': None,
                'line_number': None,
                'is_async': is_async,
                'is_method': True,
                'decorators': []
            })

        return methods

    def _parse_js_parameters(self, params_str: str) -> List[Dict]:
        """Parse JavaScript parameter string."""
        params = []

        if not params_str.strip():
            return params

        # Split by comma (simplified - doesn't handle complex default values)
        param_list = [p.strip() for p in params_str.split(',')]

        for param in param_list:
            if not param:
                continue

            # Check for default value
            if '=' in param:
                name, default = param.split('=', 1)
                name = name.strip()
                default = default.strip()
            else:
                name = param
                default = None

            # Check for type annotation (TypeScript)
            type_hint = None
            if ':' in name:
                name, type_hint = name.split(':', 1)
                name = name.strip()
                type_hint = type_hint.strip()

            params.append({
                'name': name,
                'type_hint': type_hint,
                'default': default
            })

        return params

    def _analyze_cpp(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Analyze C/C++ header file using regex patterns.

        Note: This is a simplified approach focusing on header files.
        For production, consider using libclang or similar.
        """
        classes = []
        functions = []

        # Extract class definitions (simplified - doesn't handle nested classes)
        class_pattern = r'class\s+(\w+)(?:\s*:\s*public\s+(\w+))?\s*\{'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            base_class = match.group(2) if match.group(2) else None

            classes.append({
                'name': class_name,
                'base_classes': [base_class] if base_class else [],
                'methods': [],  # Simplified - would need to parse class body
                'docstring': None,
                'line_number': content[:match.start()].count('\n') + 1
            })

        # Extract function declarations
        func_pattern = r'(\w+(?:\s*\*|\s*&)?)\s+(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(func_pattern, content):
            return_type = match.group(1).strip()
            func_name = match.group(2)
            params_str = match.group(3)

            # Skip common keywords
            if func_name in ['if', 'for', 'while', 'switch', 'return']:
                continue

            params = self._parse_cpp_parameters(params_str)

            functions.append({
                'name': func_name,
                'parameters': params,
                'return_type': return_type,
                'docstring': None,
                'line_number': content[:match.start()].count('\n') + 1,
                'is_async': False,
                'is_method': False,
                'decorators': []
            })

        # Extract comments
        comments = self._extract_cpp_comments(content)

        return {
            'classes': classes,
            'functions': functions,
            'comments': comments
        }

    def _parse_cpp_parameters(self, params_str: str) -> List[Dict]:
        """Parse C++ parameter string."""
        params = []

        if not params_str.strip() or params_str.strip() == 'void':
            return params

        # Split by comma (simplified)
        param_list = [p.strip() for p in params_str.split(',')]

        for param in param_list:
            if not param:
                continue

            # Check for default value
            default = None
            if '=' in param:
                param, default = param.rsplit('=', 1)
                param = param.strip()
                default = default.strip()

            # Extract type and name (simplified)
            # Format: "type name" or "type* name" or "type& name"
            parts = param.split()
            if len(parts) >= 2:
                param_type = ' '.join(parts[:-1])
                param_name = parts[-1]
            else:
                param_type = param
                param_name = "unknown"

            params.append({
                'name': param_name,
                'type_hint': param_type,
                'default': default
            })

        return params

    def _extract_python_comments(self, content: str) -> List[Dict]:
        """
        Extract Python comments (# style).

        Returns list of comment dictionaries with line number, text, and type.
        """
        comments = []

        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()

            # Skip shebang and encoding declarations
            if stripped.startswith('#!') or stripped.startswith('#') and 'coding' in stripped:
                continue

            # Extract regular comments
            if stripped.startswith('#'):
                comment_text = stripped[1:].strip()
                comments.append({
                    'line': i,
                    'text': comment_text,
                    'type': 'inline'
                })

        return comments

    def _extract_js_comments(self, content: str) -> List[Dict]:
        """
        Extract JavaScript/TypeScript comments (// and /* */ styles).

        Returns list of comment dictionaries with line number, text, and type.
        """
        comments = []

        # Extract single-line comments (//)
        for match in re.finditer(r'//(.+)$', content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            comment_text = match.group(1).strip()

            comments.append({
                'line': line_num,
                'text': comment_text,
                'type': 'inline'
            })

        # Extract multi-line comments (/* */)
        for match in re.finditer(r'/\*(.+?)\*/', content, re.DOTALL):
            start_line = content[:match.start()].count('\n') + 1
            comment_text = match.group(1).strip()

            comments.append({
                'line': start_line,
                'text': comment_text,
                'type': 'block'
            })

        return comments

    def _extract_cpp_comments(self, content: str) -> List[Dict]:
        """
        Extract C++ comments (// and /* */ styles, same as JavaScript).

        Returns list of comment dictionaries with line number, text, and type.
        """
        # C++ uses the same comment syntax as JavaScript
        return self._extract_js_comments(content)

    def _analyze_csharp(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Analyze C# file using regex patterns.

        Note: This is a simplified regex-based approach. For production use with Unity/ASP.NET,
        consider using tree-sitter-c-sharp or Roslyn via pythonnet for more accurate parsing.

        Regex patterns inspired by C# language specification:
        https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/
        """
        classes = []
        functions = []

        # Extract class definitions
        # Matches: [modifiers] class ClassName [: BaseClass] [, Interface]
        class_pattern = r'(?:public|private|internal|protected)?\s*(?:static|abstract|sealed)?\s*class\s+(\w+)(?:\s*:\s*([\w\s,<>]+))?\s*\{'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            bases_str = match.group(2) if match.group(2) else ''

            # Parse base classes and interfaces
            base_classes = []
            if bases_str:
                base_classes = [b.strip() for b in bases_str.split(',')]

            # Try to extract methods (simplified)
            class_block_start = match.end()
            # Find matching closing brace (simplified - doesn't handle nested classes perfectly)
            brace_count = 1
            class_block_end = class_block_start
            for i, char in enumerate(content[class_block_start:], class_block_start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        class_block_end = i
                        break

            if class_block_end > class_block_start:
                class_body = content[class_block_start:class_block_end]
                methods = self._extract_csharp_methods(class_body)
            else:
                methods = []

            classes.append({
                'name': class_name,
                'base_classes': base_classes,
                'methods': methods,
                'docstring': None,  # Would need to extract XML doc comments
                'line_number': content[:match.start()].count('\n') + 1
            })

        # Extract top-level functions/methods
        # Matches: [modifiers] [async] ReturnType MethodName(params)
        func_pattern = r'(?:public|private|internal|protected)?\s*(?:static|virtual|override|abstract)?\s*(?:async\s+)?(\w+(?:<[\w\s,]+>)?)\s+(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(func_pattern, content):
            return_type = match.group(1).strip()
            func_name = match.group(2)
            params_str = match.group(3)
            is_async = 'async' in match.group(0)

            # Skip common keywords
            if func_name in ['if', 'for', 'while', 'switch', 'return', 'using', 'namespace']:
                continue

            params = self._parse_csharp_parameters(params_str)

            functions.append({
                'name': func_name,
                'parameters': params,
                'return_type': return_type,
                'docstring': None,
                'line_number': content[:match.start()].count('\n') + 1,
                'is_async': is_async,
                'is_method': False,
                'decorators': []
            })

        # Extract comments
        comments = self._extract_csharp_comments(content)

        return {
            'classes': classes,
            'functions': functions,
            'comments': comments
        }

    def _extract_csharp_methods(self, class_body: str) -> List[Dict]:
        """Extract C# method signatures from class body."""
        methods = []

        # Match method definitions
        method_pattern = r'(?:public|private|internal|protected)?\s*(?:static|virtual|override|abstract)?\s*(?:async\s+)?(\w+(?:<[\w\s,]+>)?)\s+(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(method_pattern, class_body):
            return_type = match.group(1).strip()
            method_name = match.group(2)
            params_str = match.group(3)
            is_async = 'async' in match.group(0)

            # Skip keywords
            if method_name in ['if', 'for', 'while', 'switch', 'get', 'set']:
                continue

            params = self._parse_csharp_parameters(params_str)

            methods.append({
                'name': method_name,
                'parameters': params,
                'return_type': return_type,
                'docstring': None,
                'line_number': None,
                'is_async': is_async,
                'is_method': True,
                'decorators': []
            })

        return methods

    def _parse_csharp_parameters(self, params_str: str) -> List[Dict]:
        """Parse C# parameter string."""
        params = []

        if not params_str.strip():
            return params

        # Split by comma (simplified)
        param_list = [p.strip() for p in params_str.split(',')]

        for param in param_list:
            if not param:
                continue

            # Check for default value
            default = None
            if '=' in param:
                param, default = param.split('=', 1)
                param = param.strip()
                default = default.strip()

            # Parse: [ref/out] Type name
            parts = param.split()
            if len(parts) >= 2:
                # Remove ref/out modifiers
                if parts[0] in ['ref', 'out', 'in', 'params']:
                    parts = parts[1:]

                if len(parts) >= 2:
                    param_type = parts[0]
                    param_name = parts[1]
                else:
                    param_type = parts[0]
                    param_name = "unknown"
            else:
                param_type = None
                param_name = param

            params.append({
                'name': param_name,
                'type_hint': param_type,
                'default': default
            })

        return params

    def _extract_csharp_comments(self, content: str) -> List[Dict]:
        """Extract C# comments (// and /* */ and /// XML docs)."""
        comments = []

        # Single-line comments (//)
        for match in re.finditer(r'//(.+)$', content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            comment_text = match.group(1).strip()

            # Distinguish XML doc comments (///)
            comment_type = 'doc' if match.group(1).startswith('/') else 'inline'

            comments.append({
                'line': line_num,
                'text': comment_text.lstrip('/').strip(),
                'type': comment_type
            })

        # Multi-line comments (/* */)
        for match in re.finditer(r'/\*(.+?)\*/', content, re.DOTALL):
            start_line = content[:match.start()].count('\n') + 1
            comment_text = match.group(1).strip()

            comments.append({
                'line': start_line,
                'text': comment_text,
                'type': 'block'
            })

        return comments

    def _analyze_go(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Analyze Go file using regex patterns.

        Note: This is a simplified regex-based approach. For production,
        consider using go/parser from the Go standard library via subprocess.

        Regex patterns based on Go language specification:
        https://go.dev/ref/spec
        """
        classes = []  # Go doesn't have classes, but we'll extract structs
        functions = []

        # Extract struct definitions (Go's equivalent of classes)
        struct_pattern = r'type\s+(\w+)\s+struct\s*\{'
        for match in re.finditer(struct_pattern, content):
            struct_name = match.group(1)

            classes.append({
                'name': struct_name,
                'base_classes': [],  # Go uses embedding, not inheritance
                'methods': [],  # Methods extracted separately
                'docstring': None,
                'line_number': content[:match.start()].count('\n') + 1
            })

        # Extract function definitions
        # Matches: func [receiver] name(params) [returns]
        func_pattern = r'func\s+(?:\((\w+)\s+\*?(\w+)\)\s+)?(\w+)\s*\(([^)]*)\)(?:\s+\(([^)]+)\)|(?:\s+(\w+(?:\[.*?\])?(?:,\s*\w+)*)))?'
        for match in re.finditer(func_pattern, content):
            receiver_var = match.group(1)
            receiver_type = match.group(2)
            func_name = match.group(3)
            params_str = match.group(4)
            returns_multi = match.group(5)  # Multiple returns in parentheses
            returns_single = match.group(6)  # Single return without parentheses

            # Determine if it's a method (has receiver)
            is_method = bool(receiver_type)

            # Parse return type
            return_type = None
            if returns_multi:
                return_type = f"({returns_multi})"
            elif returns_single:
                return_type = returns_single

            params = self._parse_go_parameters(params_str)

            functions.append({
                'name': func_name,
                'parameters': params,
                'return_type': return_type,
                'docstring': None,
                'line_number': content[:match.start()].count('\n') + 1,
                'is_async': False,  # Go uses goroutines differently
                'is_method': is_method,
                'decorators': []
            })

        # Extract comments
        comments = self._extract_go_comments(content)

        return {
            'classes': classes,
            'functions': functions,
            'comments': comments
        }

    def _parse_go_parameters(self, params_str: str) -> List[Dict]:
        """Parse Go parameter string."""
        params = []

        if not params_str.strip():
            return params

        # Split by comma
        param_list = [p.strip() for p in params_str.split(',')]

        for param in param_list:
            if not param:
                continue

            # Go format: name type or name1, name2 type
            # Simplified parsing
            parts = param.split()
            if len(parts) >= 2:
                # Last part is type
                param_type = parts[-1]
                param_name = ' '.join(parts[:-1])
            else:
                param_type = param
                param_name = "unknown"

            params.append({
                'name': param_name,
                'type_hint': param_type,
                'default': None  # Go doesn't support default parameters
            })

        return params

    def _extract_go_comments(self, content: str) -> List[Dict]:
        """Extract Go comments (// and /* */ styles)."""
        # Go uses C-style comments
        return self._extract_js_comments(content)

    def _analyze_rust(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Analyze Rust file using regex patterns.

        Note: This is a simplified regex-based approach. For production,
        consider using syn crate via subprocess or tree-sitter-rust.

        Regex patterns based on Rust language reference:
        https://doc.rust-lang.org/reference/
        """
        classes = []  # Rust uses structs/enums/traits
        functions = []

        # Extract struct definitions
        struct_pattern = r'(?:pub\s+)?struct\s+(\w+)(?:<[^>]+>)?\s*\{'
        for match in re.finditer(struct_pattern, content):
            struct_name = match.group(1)

            classes.append({
                'name': struct_name,
                'base_classes': [],  # Rust uses traits, not inheritance
                'methods': [],
                'docstring': None,
                'line_number': content[:match.start()].count('\n') + 1
            })

        # Extract function definitions
        # Matches: [pub] [async] [unsafe] [const] fn name<generics>(params) -> ReturnType
        func_pattern = r'(?:pub\s+)?(?:async\s+)?(?:unsafe\s+)?(?:const\s+)?fn\s+(\w+)(?:<[^>]+>)?\s*\(([^)]*)\)(?:\s*->\s*([^{;]+))?'
        for match in re.finditer(func_pattern, content):
            func_name = match.group(1)
            params_str = match.group(2)
            return_type = match.group(3).strip() if match.group(3) else None
            is_async = 'async' in match.group(0)

            params = self._parse_rust_parameters(params_str)

            functions.append({
                'name': func_name,
                'parameters': params,
                'return_type': return_type,
                'docstring': None,
                'line_number': content[:match.start()].count('\n') + 1,
                'is_async': is_async,
                'is_method': False,
                'decorators': []
            })

        # Extract comments
        comments = self._extract_rust_comments(content)

        return {
            'classes': classes,
            'functions': functions,
            'comments': comments
        }

    def _parse_rust_parameters(self, params_str: str) -> List[Dict]:
        """Parse Rust parameter string."""
        params = []

        if not params_str.strip():
            return params

        # Split by comma
        param_list = [p.strip() for p in params_str.split(',')]

        for param in param_list:
            if not param:
                continue

            # Rust format: name: type or &self
            if ':' in param:
                name, param_type = param.split(':', 1)
                name = name.strip()
                param_type = param_type.strip()
            else:
                # Handle &self, &mut self, self
                name = param
                param_type = None

            params.append({
                'name': name,
                'type_hint': param_type,
                'default': None  # Rust doesn't support default parameters
            })

        return params

    def _extract_rust_comments(self, content: str) -> List[Dict]:
        """Extract Rust comments (// and /* */ and /// doc comments)."""
        comments = []

        # Single-line comments (//)
        for match in re.finditer(r'//(.+)$', content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            comment_text = match.group(1).strip()

            # Distinguish doc comments (/// or //!)
            if comment_text.startswith('/') or comment_text.startswith('!'):
                comment_type = 'doc'
                comment_text = comment_text.lstrip('/!').strip()
            else:
                comment_type = 'inline'

            comments.append({
                'line': line_num,
                'text': comment_text,
                'type': comment_type
            })

        # Multi-line comments (/* */)
        for match in re.finditer(r'/\*(.+?)\*/', content, re.DOTALL):
            start_line = content[:match.start()].count('\n') + 1
            comment_text = match.group(1).strip()

            comments.append({
                'line': start_line,
                'text': comment_text,
                'type': 'block'
            })

        return comments

    def _analyze_java(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Analyze Java file using regex patterns.

        Note: This is a simplified regex-based approach. For production,
        consider using Eclipse JDT or JavaParser library.

        Regex patterns based on Java language specification:
        https://docs.oracle.com/javase/specs/
        """
        classes = []
        functions = []

        # Extract class definitions
        # Matches: [modifiers] class ClassName [extends Base] [implements Interfaces]
        class_pattern = r'(?:public|private|protected)?\s*(?:static|final|abstract)?\s*class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w\s,]+))?\s*\{'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            base_class = match.group(2)
            interfaces_str = match.group(3)

            base_classes = []
            if base_class:
                base_classes.append(base_class)
            if interfaces_str:
                base_classes.extend([i.strip() for i in interfaces_str.split(',')])

            # Extract methods (simplified)
            class_block_start = match.end()
            brace_count = 1
            class_block_end = class_block_start
            for i, char in enumerate(content[class_block_start:], class_block_start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        class_block_end = i
                        break

            if class_block_end > class_block_start:
                class_body = content[class_block_start:class_block_end]
                methods = self._extract_java_methods(class_body)
            else:
                methods = []

            classes.append({
                'name': class_name,
                'base_classes': base_classes,
                'methods': methods,
                'docstring': None,
                'line_number': content[:match.start()].count('\n') + 1
            })

        # Extract top-level functions (rare in Java, but static methods)
        func_pattern = r'(?:public|private|protected)?\s*(?:static|final|synchronized)?\s*(\w+(?:<[\w\s,]+>)?)\s+(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(func_pattern, content):
            return_type = match.group(1).strip()
            func_name = match.group(2)
            params_str = match.group(3)

            # Skip keywords
            if func_name in ['if', 'for', 'while', 'switch', 'return', 'class', 'void']:
                continue

            params = self._parse_java_parameters(params_str)

            functions.append({
                'name': func_name,
                'parameters': params,
                'return_type': return_type,
                'docstring': None,
                'line_number': content[:match.start()].count('\n') + 1,
                'is_async': False,
                'is_method': False,
                'decorators': []
            })

        # Extract comments
        comments = self._extract_java_comments(content)

        return {
            'classes': classes,
            'functions': functions,
            'comments': comments
        }

    def _extract_java_methods(self, class_body: str) -> List[Dict]:
        """Extract Java method signatures from class body."""
        methods = []

        method_pattern = r'(?:public|private|protected)?\s*(?:static|final|synchronized)?\s*(\w+(?:<[\w\s,]+>)?)\s+(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(method_pattern, class_body):
            return_type = match.group(1).strip()
            method_name = match.group(2)
            params_str = match.group(3)

            # Skip keywords
            if method_name in ['if', 'for', 'while', 'switch']:
                continue

            params = self._parse_java_parameters(params_str)

            methods.append({
                'name': method_name,
                'parameters': params,
                'return_type': return_type,
                'docstring': None,
                'line_number': None,
                'is_async': False,
                'is_method': True,
                'decorators': []
            })

        return methods

    def _parse_java_parameters(self, params_str: str) -> List[Dict]:
        """Parse Java parameter string."""
        params = []

        if not params_str.strip():
            return params

        # Split by comma
        param_list = [p.strip() for p in params_str.split(',')]

        for param in param_list:
            if not param:
                continue

            # Java format: Type name or final Type name
            parts = param.split()
            if len(parts) >= 2:
                # Remove 'final' if present
                if parts[0] == 'final':
                    parts = parts[1:]

                if len(parts) >= 2:
                    param_type = parts[0]
                    param_name = parts[1]
                else:
                    param_type = parts[0]
                    param_name = "unknown"
            else:
                param_type = param
                param_name = "unknown"

            params.append({
                'name': param_name,
                'type_hint': param_type,
                'default': None  # Java doesn't support default parameters
            })

        return params

    def _extract_java_comments(self, content: str) -> List[Dict]:
        """Extract Java comments (// and /* */ and /** JavaDoc */)."""
        comments = []

        # Single-line comments (//)
        for match in re.finditer(r'//(.+)$', content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            comment_text = match.group(1).strip()

            comments.append({
                'line': line_num,
                'text': comment_text,
                'type': 'inline'
            })

        # Multi-line and JavaDoc comments (/* */ and /** */)
        for match in re.finditer(r'/\*\*?(.+?)\*/', content, re.DOTALL):
            start_line = content[:match.start()].count('\n') + 1
            comment_text = match.group(1).strip()

            # Distinguish JavaDoc (starts with **)
            comment_type = 'doc' if match.group(0).startswith('/**') else 'block'

            comments.append({
                'line': start_line,
                'text': comment_text,
                'type': comment_type
            })

        return comments

    def _analyze_ruby(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Analyze Ruby file using regex patterns.

        Note: This is a simplified regex-based approach. For production,
        consider using parser gem or tree-sitter-ruby.

        Regex patterns based on Ruby language documentation:
        https://ruby-doc.org/
        """
        classes = []
        functions = []

        # Extract class definitions
        class_pattern = r'class\s+(\w+)(?:\s*<\s*(\w+))?\s*$'
        for match in re.finditer(class_pattern, content, re.MULTILINE):
            class_name = match.group(1)
            base_class = match.group(2)

            base_classes = [base_class] if base_class else []

            classes.append({
                'name': class_name,
                'base_classes': base_classes,
                'methods': [],  # Would need to parse class body
                'docstring': None,
                'line_number': content[:match.start()].count('\n') + 1
            })

        # Extract method/function definitions
        # Matches: def method_name(params)
        func_pattern = r'def\s+(?:self\.)?(\w+[?!]?)\s*(?:\(([^)]*)\))?'
        for match in re.finditer(func_pattern, content):
            func_name = match.group(1)
            params_str = match.group(2) if match.group(2) else ''

            params = self._parse_ruby_parameters(params_str)

            functions.append({
                'name': func_name,
                'parameters': params,
                'return_type': None,  # Ruby has no type annotations (usually)
                'docstring': None,
                'line_number': content[:match.start()].count('\n') + 1,
                'is_async': False,
                'is_method': False,
                'decorators': []
            })

        # Extract comments
        comments = self._extract_ruby_comments(content)

        return {
            'classes': classes,
            'functions': functions,
            'comments': comments
        }

    def _parse_ruby_parameters(self, params_str: str) -> List[Dict]:
        """Parse Ruby parameter string."""
        params = []

        if not params_str.strip():
            return params

        # Split by comma
        param_list = [p.strip() for p in params_str.split(',')]

        for param in param_list:
            if not param:
                continue

            # Check for default value
            default = None
            if '=' in param:
                name, default = param.split('=', 1)
                name = name.strip()
                default = default.strip()
            else:
                name = param

            # Ruby doesn't have type hints in method signatures
            params.append({
                'name': name,
                'type_hint': None,
                'default': default
            })

        return params

    def _extract_ruby_comments(self, content: str) -> List[Dict]:
        """Extract Ruby comments (# style)."""
        comments = []

        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()

            # Ruby comments start with #
            if stripped.startswith('#'):
                comment_text = stripped[1:].strip()
                comments.append({
                    'line': i,
                    'text': comment_text,
                    'type': 'inline'
                })

        return comments

    def _analyze_php(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Analyze PHP file using regex patterns.

        Note: This is a simplified regex-based approach. For production,
        consider using nikic/PHP-Parser via subprocess or tree-sitter-php.

        Regex patterns based on PHP language reference:
        https://www.php.net/manual/en/langref.php
        """
        classes = []
        functions = []

        # Extract class definitions
        class_pattern = r'(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w\s,]+))?\s*\{'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            base_class = match.group(2)
            interfaces_str = match.group(3)

            base_classes = []
            if base_class:
                base_classes.append(base_class)
            if interfaces_str:
                base_classes.extend([i.strip() for i in interfaces_str.split(',')])

            # Extract methods (simplified)
            class_block_start = match.end()
            brace_count = 1
            class_block_end = class_block_start
            for i, char in enumerate(content[class_block_start:], class_block_start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        class_block_end = i
                        break

            if class_block_end > class_block_start:
                class_body = content[class_block_start:class_block_end]
                methods = self._extract_php_methods(class_body)
            else:
                methods = []

            classes.append({
                'name': class_name,
                'base_classes': base_classes,
                'methods': methods,
                'docstring': None,
                'line_number': content[:match.start()].count('\n') + 1
            })

        # Extract function definitions
        func_pattern = r'function\s+(\w+)\s*\(([^)]*)\)(?:\s*:\s*(\??\w+))?'
        for match in re.finditer(func_pattern, content):
            func_name = match.group(1)
            params_str = match.group(2)
            return_type = match.group(3)

            params = self._parse_php_parameters(params_str)

            functions.append({
                'name': func_name,
                'parameters': params,
                'return_type': return_type,
                'docstring': None,
                'line_number': content[:match.start()].count('\n') + 1,
                'is_async': False,
                'is_method': False,
                'decorators': []
            })

        # Extract comments
        comments = self._extract_php_comments(content)

        return {
            'classes': classes,
            'functions': functions,
            'comments': comments
        }

    def _extract_php_methods(self, class_body: str) -> List[Dict]:
        """Extract PHP method signatures from class body."""
        methods = []

        method_pattern = r'(?:public|private|protected)?\s*(?:static|final)?\s*function\s+(\w+)\s*\(([^)]*)\)(?:\s*:\s*(\??\w+))?'
        for match in re.finditer(method_pattern, class_body):
            method_name = match.group(1)
            params_str = match.group(2)
            return_type = match.group(3)

            params = self._parse_php_parameters(params_str)

            methods.append({
                'name': method_name,
                'parameters': params,
                'return_type': return_type,
                'docstring': None,
                'line_number': None,
                'is_async': False,
                'is_method': True,
                'decorators': []
            })

        return methods

    def _parse_php_parameters(self, params_str: str) -> List[Dict]:
        """Parse PHP parameter string."""
        params = []

        if not params_str.strip():
            return params

        # Split by comma
        param_list = [p.strip() for p in params_str.split(',')]

        for param in param_list:
            if not param:
                continue

            # Check for default value
            default = None
            if '=' in param:
                param, default = param.split('=', 1)
                param = param.strip()
                default = default.strip()

            # PHP format: Type $name or just $name
            parts = param.split()
            if len(parts) >= 2:
                param_type = parts[0]
                param_name = parts[1]
            else:
                param_type = None
                param_name = parts[0] if parts else "unknown"

            # Remove $ from variable name
            if param_name.startswith('$'):
                param_name = param_name[1:]

            params.append({
                'name': param_name,
                'type_hint': param_type,
                'default': default
            })

        return params

    def _extract_php_comments(self, content: str) -> List[Dict]:
        """Extract PHP comments (// and /* */ and # and /** PHPDoc */)."""
        comments = []

        # Single-line comments (// and #)
        for match in re.finditer(r'(?://|#)(.+)$', content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            comment_text = match.group(1).strip()

            comments.append({
                'line': line_num,
                'text': comment_text,
                'type': 'inline'
            })

        # Multi-line and PHPDoc comments (/* */ and /** */)
        for match in re.finditer(r'/\*\*?(.+?)\*/', content, re.DOTALL):
            start_line = content[:match.start()].count('\n') + 1
            comment_text = match.group(1).strip()

            # Distinguish PHPDoc (starts with **)
            comment_type = 'doc' if match.group(0).startswith('/**') else 'block'

            comments.append({
                'line': start_line,
                'text': comment_text,
                'type': comment_type
            })

        return comments


if __name__ == '__main__':
    # Test the analyzer
    python_code = '''
class Node2D:
    """Base class for 2D nodes."""

    def move_local_x(self, delta: float, snap: bool = False) -> None:
        """Move node along local X axis."""
        pass

    async def tween_position(self, target: tuple, duration: float = 1.0):
        """Animate position to target."""
        pass

def create_sprite(texture: str) -> Node2D:
    """Create a new sprite node."""
    return Node2D()
'''

    analyzer = CodeAnalyzer(depth='deep')
    result = analyzer.analyze_file('test.py', python_code, 'Python')

    print("Analysis Result:")
    print(f"Classes: {len(result.get('classes', []))}")
    print(f"Functions: {len(result.get('functions', []))}")

    if result.get('classes'):
        cls = result['classes'][0]
        print(f"\nClass: {cls['name']}")
        print(f"  Methods: {len(cls['methods'])}")
        for method in cls['methods']:
            params = ', '.join([f"{p['name']}: {p['type_hint']}" + (f" = {p['default']}" if p.get('default') else "")
                               for p in method['parameters']])
            print(f"    {method['name']}({params}) -> {method['return_type']}")
