#!/usr/bin/env python3
"""
Test Example Extractor - Extract real usage examples from test files

Analyzes test files to extract meaningful code examples showing:
- Object instantiation with real parameters
- Method calls with expected behaviors
- Configuration examples
- Setup patterns from fixtures/setUp()
- Multi-step workflows from integration tests

Supports 9 languages:
- Python (AST-based, deep analysis)
- JavaScript, TypeScript, Go, Rust, Java, C#, PHP, Ruby (regex-based)

Example usage:
    # Extract from directory
    python test_example_extractor.py tests/ --language python

    # Extract from single file
    python test_example_extractor.py --file tests/test_scraper.py

    # JSON output
    python test_example_extractor.py tests/ --json > examples.json

    # Filter by confidence
    python test_example_extractor.py tests/ --min-confidence 0.7
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Literal, Set
from pathlib import Path
import ast
import re
import hashlib
import logging
import argparse
import json
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class TestExample:
    """Single extracted usage example from test code"""

    # Identity
    example_id: str          # Unique hash of example
    test_name: str           # Test function/method name
    category: Literal["instantiation", "method_call", "config", "setup", "workflow"]

    # Code
    code: str                # Actual example code
    language: str            # Programming language

    # Context
    description: str         # What this demonstrates
    expected_behavior: str   # Expected outcome from assertions

    # Source
    file_path: str
    line_start: int
    line_end: int

    # Quality
    complexity_score: float  # 0-1 scale (higher = more complex/valuable)
    confidence: float        # 0-1 scale (higher = more confident extraction)

    # Optional fields (must come after required fields)
    setup_code: Optional[str] = None  # Required setup code
    tags: List[str] = field(default_factory=list)  # ["pytest", "mock", "async"]
    dependencies: List[str] = field(default_factory=list)  # Imported modules
    ai_analysis: Optional[Dict] = None  # AI-generated analysis (C3.6)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    def to_markdown(self) -> str:
        """Convert to markdown format"""
        md = f"### {self.test_name}\n\n"
        md += f"**Category**: {self.category}  \n"
        md += f"**Description**: {self.description}  \n"
        if self.expected_behavior:
            md += f"**Expected**: {self.expected_behavior}  \n"
        md += f"**Confidence**: {self.confidence:.2f}  \n"
        if self.tags:
            md += f"**Tags**: {', '.join(self.tags)}  \n"

        # Add AI analysis if available (C3.6)
        if self.ai_analysis:
            md += f"\n**🤖 AI Analysis:**  \n"
            if self.ai_analysis.get('explanation'):
                md += f"*{self.ai_analysis['explanation']}*  \n"
            if self.ai_analysis.get('best_practices'):
                md += f"**Best Practices:** {', '.join(self.ai_analysis['best_practices'])}  \n"
            if self.ai_analysis.get('tutorial_group'):
                md += f"**Tutorial Group:** {self.ai_analysis['tutorial_group']}  \n"

        md += f"\n```{self.language.lower()}\n"
        if self.setup_code:
            md += f"# Setup\n{self.setup_code}\n\n"
        md += f"{self.code}\n```\n\n"
        md += f"*Source: {self.file_path}:{self.line_start}*\n\n"
        return md


@dataclass
class ExampleReport:
    """Summary of test example extraction results"""

    total_examples: int
    examples_by_category: Dict[str, int]
    examples_by_language: Dict[str, int]
    examples: List[TestExample]
    avg_complexity: float
    high_value_count: int  # confidence > 0.7
    file_path: Optional[str] = None  # If single file
    directory: Optional[str] = None  # If directory

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "total_examples": self.total_examples,
            "examples_by_category": self.examples_by_category,
            "examples_by_language": self.examples_by_language,
            "avg_complexity": self.avg_complexity,
            "high_value_count": self.high_value_count,
            "file_path": self.file_path,
            "directory": self.directory,
            "examples": [ex.to_dict() for ex in self.examples]
        }

    def to_markdown(self) -> str:
        """Convert to markdown format"""
        md = "# Test Example Extraction Report\n\n"
        md += f"**Total Examples**: {self.total_examples}  \n"
        md += f"**High Value Examples** (confidence > 0.7): {self.high_value_count}  \n"
        md += f"**Average Complexity**: {self.avg_complexity:.2f}  \n"

        md += "\n## Examples by Category\n\n"
        for category, count in sorted(self.examples_by_category.items()):
            md += f"- **{category}**: {count}\n"

        md += "\n## Examples by Language\n\n"
        for language, count in sorted(self.examples_by_language.items()):
            md += f"- **{language}**: {count}\n"

        md += "\n## Extracted Examples\n\n"
        for example in sorted(self.examples, key=lambda x: x.confidence, reverse=True):
            md += example.to_markdown()

        return md


# ============================================================================
# PYTHON TEST ANALYZER (AST-based)
# ============================================================================

class PythonTestAnalyzer:
    """Deep AST-based test example extraction for Python"""

    def __init__(self):
        self.trivial_patterns = {
            'assertTrue(True)',
            'assertFalse(False)',
            'assertEqual(1, 1)',
            'assertIsNone(None)',
            'assertIsNotNone(None)',
        }

    def extract(self, file_path: str, code: str) -> List[TestExample]:
        """Extract examples from Python test file"""
        examples = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return []

        # Extract imports for dependency tracking
        imports = self._extract_imports(tree)

        # Find test classes (unittest.TestCase)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if self._is_test_class(node):
                    examples.extend(self._extract_from_test_class(
                        node, file_path, imports
                    ))

            # Find test functions (pytest)
            elif isinstance(node, ast.FunctionDef):
                if self._is_test_function(node):
                    examples.extend(self._extract_from_test_function(
                        node, file_path, imports
                    ))

        return examples

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract imported modules"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend([alias.name for alias in node.names])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports

    def _is_test_class(self, node: ast.ClassDef) -> bool:
        """Check if class is a test class"""
        # unittest.TestCase pattern
        for base in node.bases:
            if isinstance(base, ast.Name) and 'Test' in base.id:
                return True
            elif isinstance(base, ast.Attribute) and base.attr == 'TestCase':
                return True
        return False

    def _is_test_function(self, node: ast.FunctionDef) -> bool:
        """Check if function is a test function"""
        # pytest pattern: starts with test_
        if node.name.startswith('test_'):
            return True
        # Has @pytest.mark decorator
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Attribute):
                if 'pytest' in ast.unparse(decorator):
                    return True
        return False

    def _extract_from_test_class(
        self,
        class_node: ast.ClassDef,
        file_path: str,
        imports: List[str]
    ) -> List[TestExample]:
        """Extract examples from unittest.TestCase class"""
        examples = []

        # Extract setUp method if exists
        setup_code = self._extract_setup_method(class_node)

        # Process each test method
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                examples.extend(self._analyze_test_body(
                    node,
                    file_path,
                    imports,
                    setup_code=setup_code
                ))

        return examples

    def _extract_from_test_function(
        self,
        func_node: ast.FunctionDef,
        file_path: str,
        imports: List[str]
    ) -> List[TestExample]:
        """Extract examples from pytest test function"""
        # Check for fixture parameters
        fixture_setup = self._extract_fixtures(func_node)

        return self._analyze_test_body(
            func_node,
            file_path,
            imports,
            setup_code=fixture_setup
        )

    def _extract_setup_method(self, class_node: ast.ClassDef) -> Optional[str]:
        """Extract setUp method code"""
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef) and node.name == 'setUp':
                return ast.unparse(node.body)
        return None

    def _extract_fixtures(self, func_node: ast.FunctionDef) -> Optional[str]:
        """Extract pytest fixture parameters"""
        if not func_node.args.args:
            return None

        # Skip 'self' parameter
        params = [arg.arg for arg in func_node.args.args if arg.arg != 'self']
        if params:
            return f"# Fixtures: {', '.join(params)}"
        return None

    def _analyze_test_body(
        self,
        func_node: ast.FunctionDef,
        file_path: str,
        imports: List[str],
        setup_code: Optional[str] = None
    ) -> List[TestExample]:
        """Analyze test function body for extractable patterns"""
        examples = []

        # Get docstring for description
        docstring = ast.get_docstring(func_node) or func_node.name.replace('_', ' ')

        # Detect tags
        tags = self._detect_tags(func_node, imports)

        # Extract different pattern categories

        # 1. Instantiation patterns
        instantiations = self._find_instantiations(func_node, file_path, docstring, setup_code, tags, imports)
        examples.extend(instantiations)

        # 2. Method calls with assertions
        method_calls = self._find_method_calls_with_assertions(func_node, file_path, docstring, setup_code, tags, imports)
        examples.extend(method_calls)

        # 3. Configuration dictionaries
        configs = self._find_config_dicts(func_node, file_path, docstring, setup_code, tags, imports)
        examples.extend(configs)

        # 4. Multi-step workflows (integration tests)
        workflows = self._find_workflows(func_node, file_path, docstring, setup_code, tags, imports)
        examples.extend(workflows)

        return examples

    def _detect_tags(self, func_node: ast.FunctionDef, imports: List[str]) -> List[str]:
        """Detect test tags (pytest, mock, async, etc.)"""
        tags = []

        # Check decorators
        for decorator in func_node.decorator_list:
            decorator_str = ast.unparse(decorator).lower()
            if 'pytest' in decorator_str:
                tags.append('pytest')
            if 'mock' in decorator_str:
                tags.append('mock')
            if 'async' in decorator_str or func_node.name.startswith('test_async'):
                tags.append('async')

        # Check if using unittest
        if 'unittest' in imports:
            tags.append('unittest')

        # Check function body for mock usage
        func_str = ast.unparse(func_node).lower()
        if 'mock' in func_str or 'patch' in func_str:
            tags.append('mock')

        return list(set(tags))

    def _find_instantiations(
        self,
        func_node: ast.FunctionDef,
        file_path: str,
        description: str,
        setup_code: Optional[str],
        tags: List[str],
        imports: List[str]
    ) -> List[TestExample]:
        """Find object instantiation patterns: obj = ClassName(...)"""
        examples = []

        for node in ast.walk(func_node):
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Call):
                    # Check if meaningful instantiation
                    if self._is_meaningful_instantiation(node):
                        code = ast.unparse(node)

                        # Skip trivial or mock-only
                        if len(code) < 20 or 'Mock()' in code:
                            continue

                        # Get class name
                        class_name = self._get_class_name(node.value)

                        example = TestExample(
                            example_id=self._generate_id(code),
                            test_name=func_node.name,
                            category="instantiation",
                            code=code,
                            language="Python",
                            description=f"Instantiate {class_name}: {description}",
                            expected_behavior=self._extract_assertion_after(func_node, node),
                            setup_code=setup_code,
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.end_lineno or node.lineno,
                            complexity_score=self._calculate_complexity(code),
                            confidence=0.8,
                            tags=tags,
                            dependencies=imports
                        )
                        examples.append(example)

        return examples

    def _find_method_calls_with_assertions(
        self,
        func_node: ast.FunctionDef,
        file_path: str,
        description: str,
        setup_code: Optional[str],
        tags: List[str],
        imports: List[str]
    ) -> List[TestExample]:
        """Find method calls followed by assertions"""
        examples = []

        statements = func_node.body
        for i, stmt in enumerate(statements):
            # Look for method calls
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                # Check if next statement is an assertion
                if i + 1 < len(statements):
                    next_stmt = statements[i + 1]
                    if self._is_assertion(next_stmt):
                        method_call = ast.unparse(stmt)
                        assertion = ast.unparse(next_stmt)

                        code = f"{method_call}\n{assertion}"

                        # Skip trivial assertions
                        if any(trivial in assertion for trivial in self.trivial_patterns):
                            continue

                        example = TestExample(
                            example_id=self._generate_id(code),
                            test_name=func_node.name,
                            category="method_call",
                            code=code,
                            language="Python",
                            description=description,
                            expected_behavior=assertion,
                            setup_code=setup_code,
                            file_path=file_path,
                            line_start=stmt.lineno,
                            line_end=next_stmt.end_lineno or next_stmt.lineno,
                            complexity_score=self._calculate_complexity(code),
                            confidence=0.85,
                            tags=tags,
                            dependencies=imports
                        )
                        examples.append(example)

        return examples

    def _find_config_dicts(
        self,
        func_node: ast.FunctionDef,
        file_path: str,
        description: str,
        setup_code: Optional[str],
        tags: List[str],
        imports: List[str]
    ) -> List[TestExample]:
        """Find configuration dictionary patterns"""
        examples = []

        for node in ast.walk(func_node):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
                # Must have 2+ keys and be meaningful
                if len(node.value.keys) >= 2:
                    code = ast.unparse(node)

                    # Check if looks like configuration
                    if self._is_config_dict(node.value):
                        example = TestExample(
                            example_id=self._generate_id(code),
                            test_name=func_node.name,
                            category="config",
                            code=code,
                            language="Python",
                            description=f"Configuration example: {description}",
                            expected_behavior=self._extract_assertion_after(func_node, node),
                            setup_code=setup_code,
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.end_lineno or node.lineno,
                            complexity_score=self._calculate_complexity(code),
                            confidence=0.75,
                            tags=tags,
                            dependencies=imports
                        )
                        examples.append(example)

        return examples

    def _find_workflows(
        self,
        func_node: ast.FunctionDef,
        file_path: str,
        description: str,
        setup_code: Optional[str],
        tags: List[str],
        imports: List[str]
    ) -> List[TestExample]:
        """Find multi-step workflow patterns (integration tests)"""
        examples = []

        # Check if this looks like an integration test (3+ meaningful steps)
        if len(func_node.body) >= 3 and self._is_integration_test(func_node):
            # Extract the full workflow
            code = ast.unparse(func_node.body)

            # Skip if too long (> 30 lines)
            if code.count('\n') > 30:
                return examples

            example = TestExample(
                example_id=self._generate_id(code),
                test_name=func_node.name,
                category="workflow",
                code=code,
                language="Python",
                description=f"Workflow: {description}",
                expected_behavior=self._extract_final_assertion(func_node),
                setup_code=setup_code,
                file_path=file_path,
                line_start=func_node.lineno,
                line_end=func_node.end_lineno or func_node.lineno,
                complexity_score=min(1.0, len(func_node.body) / 10),
                confidence=0.9,
                tags=tags + ['workflow', 'integration'],
                dependencies=imports
            )
            examples.append(example)

        return examples

    # Helper methods

    def _is_meaningful_instantiation(self, node: ast.Assign) -> bool:
        """Check if instantiation has meaningful parameters"""
        if not isinstance(node.value, ast.Call):
            return False

        # Must have at least one argument or keyword argument
        call = node.value
        if call.args or call.keywords:
            return True

        return False

    def _get_class_name(self, call_node: ast.Call) -> str:
        """Extract class name from Call node"""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr
        return "UnknownClass"

    def _is_assertion(self, node: ast.stmt) -> bool:
        """Check if statement is an assertion"""
        if isinstance(node, ast.Assert):
            return True

        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call_str = ast.unparse(node.value).lower()
            assertion_methods = ['assert', 'expect', 'should']
            return any(method in call_str for method in assertion_methods)

        return False

    def _is_config_dict(self, dict_node: ast.Dict) -> bool:
        """Check if dictionary looks like configuration"""
        # Keys should be strings
        for key in dict_node.keys:
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                return False
        return True

    def _is_integration_test(self, func_node: ast.FunctionDef) -> bool:
        """Check if test looks like an integration test"""
        test_name = func_node.name.lower()
        integration_keywords = ['workflow', 'integration', 'end_to_end', 'e2e', 'full']
        return any(keyword in test_name for keyword in integration_keywords)

    def _extract_assertion_after(self, func_node: ast.FunctionDef, target_node: ast.AST) -> str:
        """Find assertion that follows the target node"""
        found_target = False
        for stmt in func_node.body:
            if stmt == target_node:
                found_target = True
                continue
            if found_target and self._is_assertion(stmt):
                return ast.unparse(stmt)
        return ""

    def _extract_final_assertion(self, func_node: ast.FunctionDef) -> str:
        """Extract the final assertion from test"""
        for stmt in reversed(func_node.body):
            if self._is_assertion(stmt):
                return ast.unparse(stmt)
        return ""

    def _calculate_complexity(self, code: str) -> float:
        """Calculate code complexity score (0-1)"""
        # Simple heuristic: more lines + more parameters = more complex
        lines = code.count('\n') + 1
        params = code.count(',') + 1

        complexity = min(1.0, (lines * 0.1) + (params * 0.05))
        return round(complexity, 2)

    def _generate_id(self, code: str) -> str:
        """Generate unique ID for example"""
        return hashlib.md5(code.encode()).hexdigest()[:8]


# ============================================================================
# GENERIC TEST ANALYZER (Regex-based for non-Python languages)
# ============================================================================

class GenericTestAnalyzer:
    """Regex-based test example extraction for non-Python languages"""

    # Language-specific regex patterns
    PATTERNS = {
        "javascript": {
            "instantiation": r'(?:const|let|var)\s+(\w+)\s*=\s*new\s+(\w+)\(([^)]*)\)',
            "assertion": r'expect\(([^)]+)\)\.to(?:Equal|Be|Match)\(([^)]+)\)',
            "test_function": r'(?:test|it)\(["\']([^"\']+)["\']',
            "config": r'(?:const|let)\s+config\s*=\s*\{[\s\S]{20,500}?\}',
        },
        "typescript": {
            "instantiation": r'(?:const|let|var)\s+(\w+):\s*\w+\s*=\s*new\s+(\w+)\(([^)]*)\)',
            "assertion": r'expect\(([^)]+)\)\.to(?:Equal|Be|Match)\(([^)]+)\)',
            "test_function": r'(?:test|it)\(["\']([^"\']+)["\']',
            "config": r'(?:const|let)\s+config:\s*\w+\s*=\s*\{[\s\S]{20,500}?\}',
        },
        "go": {
            "instantiation": r'(\w+)\s*:=\s*(\w+)\{([^}]+)\}',
            "assertion": r't\.(?:Error|Fatal)(?:f)?\(["\']([^"\']+)["\']',
            "test_function": r'func\s+(Test\w+)\(t\s+\*testing\.T\)',
            "table_test": r'tests\s*:=\s*\[\]struct\s*\{[\s\S]{50,1000}?\}',
        },
        "rust": {
            "instantiation": r'let\s+(\w+)\s*=\s*(\w+)::new\(([^)]*)\)',
            "assertion": r'assert(?:_eq)?!\(([^)]+)\)',
            "test_function": r'#\[test\]\s*fn\s+(\w+)\(\)',
        },
        "java": {
            "instantiation": r'(\w+)\s+(\w+)\s*=\s*new\s+(\w+)\(([^)]*)\)',
            "assertion": r'assert(?:Equals|True|False|NotNull)\(([^)]+)\)',
            "test_function": r'@Test\s+public\s+void\s+(\w+)\(\)',
        },
        "csharp": {
            "instantiation": r'var\s+(\w+)\s*=\s*new\s+(\w+)\(([^)]*)\)',
            "assertion": r'Assert\.(?:AreEqual|IsTrue|IsFalse|IsNotNull)\(([^)]+)\)',
            "test_function": r'\[Test\]\s+public\s+void\s+(\w+)\(\)',
        },
        "php": {
            "instantiation": r'\$(\w+)\s*=\s*new\s+(\w+)\(([^)]*)\)',
            "assertion": r'\$this->assert(?:Equals|True|False|NotNull)\(([^)]+)\)',
            "test_function": r'public\s+function\s+(test\w+)\(\)',
        },
        "ruby": {
            "instantiation": r'(\w+)\s*=\s*(\w+)\.new\(([^)]*)\)',
            "assertion": r'expect\(([^)]+)\)\.to\s+(?:eq|be|match)\(([^)]+)\)',
            "test_function": r'(?:test|it)\s+["\']([^"\']+)["\']',
        }
    }

    def extract(self, file_path: str, code: str, language: str) -> List[TestExample]:
        """Extract examples from test file using regex patterns"""
        examples = []

        language_lower = language.lower()
        if language_lower not in self.PATTERNS:
            logger.warning(f"Language {language} not supported for regex extraction")
            return []

        patterns = self.PATTERNS[language_lower]

        # Extract test functions
        test_functions = re.finditer(patterns["test_function"], code)

        for match in test_functions:
            test_name = match.group(1)

            # Get test function body (approximate - find next function start)
            start_pos = match.end()
            next_match = re.search(patterns["test_function"], code[start_pos:])
            end_pos = start_pos + next_match.start() if next_match else len(code)
            test_body = code[start_pos:end_pos]

            # Extract instantiations
            for inst_match in re.finditer(patterns["instantiation"], test_body):
                example = self._create_example(
                    test_name=test_name,
                    category="instantiation",
                    code=inst_match.group(0),
                    language=language,
                    file_path=file_path,
                    line_number=code[:start_pos + inst_match.start()].count('\n') + 1
                )
                examples.append(example)

            # Extract config dictionaries (if pattern exists)
            if "config" in patterns:
                for config_match in re.finditer(patterns["config"], test_body):
                    example = self._create_example(
                        test_name=test_name,
                        category="config",
                        code=config_match.group(0),
                        language=language,
                        file_path=file_path,
                        line_number=code[:start_pos + config_match.start()].count('\n') + 1
                    )
                    examples.append(example)

        return examples

    def _create_example(
        self,
        test_name: str,
        category: str,
        code: str,
        language: str,
        file_path: str,
        line_number: int
    ) -> TestExample:
        """Create TestExample from regex match"""
        return TestExample(
            example_id=hashlib.md5(code.encode()).hexdigest()[:8],
            test_name=test_name,
            category=category,
            code=code,
            language=language,
            description=f"Test: {test_name}",
            expected_behavior="",
            file_path=file_path,
            line_start=line_number,
            line_end=line_number + code.count('\n'),
            complexity_score=min(1.0, (code.count('\n') + 1) * 0.1),
            confidence=0.6,  # Lower confidence for regex extraction
            tags=[],
            dependencies=[]
        )


# ============================================================================
# EXAMPLE QUALITY FILTER
# ============================================================================

class ExampleQualityFilter:
    """Filter out trivial or low-quality examples"""

    def __init__(self, min_confidence: float = 0.7, min_code_length: int = 20):
        self.min_confidence = min_confidence
        self.min_code_length = min_code_length

        # Trivial patterns to exclude
        self.trivial_patterns = [
            'Mock()',
            'MagicMock()',
            'assertTrue(True)',
            'assertFalse(False)',
            'assertEqual(1, 1)',
            'pass',
            '...',
        ]

    def filter(self, examples: List[TestExample]) -> List[TestExample]:
        """Filter examples by quality criteria"""
        filtered = []

        for example in examples:
            # Check confidence threshold
            if example.confidence < self.min_confidence:
                continue

            # Check code length
            if len(example.code) < self.min_code_length:
                continue

            # Check for trivial patterns
            if self._is_trivial(example.code):
                continue

            filtered.append(example)

        return filtered

    def _is_trivial(self, code: str) -> bool:
        """Check if code contains trivial patterns"""
        return any(pattern in code for pattern in self.trivial_patterns)


# ============================================================================
# TEST EXAMPLE EXTRACTOR (Main Orchestrator)
# ============================================================================

class TestExampleExtractor:
    """Main orchestrator for test example extraction"""

    # Test file patterns
    TEST_PATTERNS = [
        'test_*.py',
        '*_test.py',
        'test*.js',
        '*test.js',
        '*_test.go',
        '*_test.rs',
        'Test*.java',
        'Test*.cs',
        '*Test.php',
        '*_spec.rb',
    ]

    # Language detection by extension
    LANGUAGE_MAP = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.go': 'Go',
        '.rs': 'Rust',
        '.java': 'Java',
        '.cs': 'C#',
        '.php': 'PHP',
        '.rb': 'Ruby',
    }

    def __init__(
        self,
        min_confidence: float = 0.7,
        max_per_file: int = 10,
        languages: Optional[List[str]] = None,
        enhance_with_ai: bool = True
    ):
        self.python_analyzer = PythonTestAnalyzer()
        self.generic_analyzer = GenericTestAnalyzer()
        self.quality_filter = ExampleQualityFilter(min_confidence=min_confidence)
        self.max_per_file = max_per_file
        self.languages = [lang.lower() for lang in languages] if languages else None
        self.enhance_with_ai = enhance_with_ai

        # Initialize AI enhancer if enabled (C3.6)
        self.ai_enhancer = None
        if self.enhance_with_ai:
            try:
                from skill_seekers.cli.ai_enhancer import TestExampleEnhancer
                self.ai_enhancer = TestExampleEnhancer()
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize AI enhancer: {e}")
                self.enhance_with_ai = False

    def extract_from_directory(
        self,
        directory: Path,
        recursive: bool = True
    ) -> ExampleReport:
        """Extract examples from all test files in directory"""
        directory = Path(directory)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        # Find test files
        test_files = self._find_test_files(directory, recursive)

        logger.info(f"Found {len(test_files)} test files in {directory}")

        # Extract from each file
        all_examples = []
        for test_file in test_files:
            examples = self.extract_from_file(test_file)
            all_examples.extend(examples)

        # Generate report
        return self._create_report(all_examples, directory=str(directory))

    def extract_from_file(self, file_path: Path) -> List[TestExample]:
        """Extract examples from single test file"""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Detect language
        language = self._detect_language(file_path)

        # Filter by language if specified
        if self.languages and language.lower() not in self.languages:
            return []

        # Read file
        try:
            code = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            logger.warning(f"Failed to read {file_path} (encoding error)")
            return []

        # Extract examples based on language
        if language == 'Python':
            examples = self.python_analyzer.extract(str(file_path), code)
        else:
            examples = self.generic_analyzer.extract(str(file_path), code, language)

        # Apply quality filter
        filtered_examples = self.quality_filter.filter(examples)

        # Limit per file
        if len(filtered_examples) > self.max_per_file:
            # Sort by confidence and take top N
            filtered_examples = sorted(
                filtered_examples,
                key=lambda x: x.confidence,
                reverse=True
            )[:self.max_per_file]

        logger.info(f"Extracted {len(filtered_examples)} examples from {file_path.name}")

        return filtered_examples

    def _find_test_files(self, directory: Path, recursive: bool) -> List[Path]:
        """Find test files in directory"""
        test_files = []

        for pattern in self.TEST_PATTERNS:
            if recursive:
                test_files.extend(directory.rglob(pattern))
            else:
                test_files.extend(directory.glob(pattern))

        return list(set(test_files))  # Remove duplicates

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        suffix = file_path.suffix.lower()
        return self.LANGUAGE_MAP.get(suffix, 'Unknown')

    def _create_report(
        self,
        examples: List[TestExample],
        file_path: Optional[str] = None,
        directory: Optional[str] = None
    ) -> ExampleReport:
        """Create summary report from examples"""
        # Enhance examples with AI analysis (C3.6)
        if self.enhance_with_ai and self.ai_enhancer and examples:
            # Convert examples to dict format for AI processing
            example_dicts = [ex.to_dict() for ex in examples]
            enhanced_dicts = self.ai_enhancer.enhance_examples(example_dicts)

            # Update examples with AI analysis
            for i, example in enumerate(examples):
                if i < len(enhanced_dicts) and 'ai_analysis' in enhanced_dicts[i]:
                    example.ai_analysis = enhanced_dicts[i]['ai_analysis']

        # Count by category
        examples_by_category = {}
        for example in examples:
            examples_by_category[example.category] = \
                examples_by_category.get(example.category, 0) + 1

        # Count by language
        examples_by_language = {}
        for example in examples:
            examples_by_language[example.language] = \
                examples_by_language.get(example.language, 0) + 1

        # Calculate averages
        avg_complexity = sum(ex.complexity_score for ex in examples) / len(examples) if examples else 0.0
        high_value_count = sum(1 for ex in examples if ex.confidence > 0.7)

        return ExampleReport(
            total_examples=len(examples),
            examples_by_category=examples_by_category,
            examples_by_language=examples_by_language,
            examples=examples,
            avg_complexity=round(avg_complexity, 2),
            high_value_count=high_value_count,
            file_path=file_path,
            directory=directory
        )


# ============================================================================
# COMMAND-LINE INTERFACE
# ============================================================================

def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description='Extract usage examples from test files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract from directory
  %(prog)s tests/ --language python

  # Extract from single file
  %(prog)s --file tests/test_scraper.py

  # JSON output
  %(prog)s tests/ --json > examples.json

  # Filter by confidence
  %(prog)s tests/ --min-confidence 0.7
        """
    )

    parser.add_argument(
        'directory',
        nargs='?',
        help='Directory containing test files'
    )
    parser.add_argument(
        '--file',
        help='Single test file to analyze'
    )
    parser.add_argument(
        '--language',
        help='Filter by programming language (python, javascript, etc.)'
    )
    parser.add_argument(
        '--min-confidence',
        type=float,
        default=0.5,
        help='Minimum confidence threshold (0.0-1.0, default: 0.5)'
    )
    parser.add_argument(
        '--max-per-file',
        type=int,
        default=10,
        help='Maximum examples per file (default: 10)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output JSON format'
    )
    parser.add_argument(
        '--markdown',
        action='store_true',
        help='Output Markdown format'
    )
    parser.add_argument(
        '--recursive',
        action='store_true',
        default=True,
        help='Search directory recursively (default: True)'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.directory and not args.file:
        parser.error("Either directory or --file must be specified")

    # Create extractor
    languages = [args.language] if args.language else None
    extractor = TestExampleExtractor(
        min_confidence=args.min_confidence,
        max_per_file=args.max_per_file,
        languages=languages
    )

    # Extract examples
    if args.file:
        examples = extractor.extract_from_file(Path(args.file))
        report = extractor._create_report(examples, file_path=args.file)
    else:
        report = extractor.extract_from_directory(
            Path(args.directory),
            recursive=args.recursive
        )

    # Output results
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    elif args.markdown:
        print(report.to_markdown())
    else:
        # Human-readable summary
        print(f"\nTest Example Extraction Results")
        print(f"=" * 50)
        print(f"Total Examples: {report.total_examples}")
        print(f"High Value (confidence > 0.7): {report.high_value_count}")
        print(f"Average Complexity: {report.avg_complexity:.2f}")
        print(f"\nExamples by Category:")
        for category, count in sorted(report.examples_by_category.items()):
            print(f"  {category}: {count}")
        print(f"\nExamples by Language:")
        for language, count in sorted(report.examples_by_language.items()):
            print(f"  {language}: {count}")
        print(f"\nUse --json or --markdown for detailed output")


if __name__ == '__main__':
    main()
