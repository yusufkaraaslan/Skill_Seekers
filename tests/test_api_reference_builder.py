#!/usr/bin/env python3
"""
Tests for api_reference_builder.py - Markdown API documentation generation.

Test Coverage:
- Class formatting
- Function formatting
- Parameter table generation
- Markdown output structure
- Integration with code analysis results
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from skill_seekers.cli.api_reference_builder import APIReferenceBuilder


class TestAPIReferenceBuilder(unittest.TestCase):
    """Tests for API reference builder"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "api_reference"

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_class_formatting(self):
        """Test markdown formatting for class signatures."""
        code_analysis = {
            'files': [{
                'file': 'test.py',
                'language': 'Python',
                'classes': [{
                    'name': 'Calculator',
                    'docstring': 'A simple calculator class.',
                    'base_classes': ['object'],
                    'methods': [{
                        'name': 'add',
                        'parameters': [
                            {'name': 'a', 'type_hint': 'int', 'default': None},
                            {'name': 'b', 'type_hint': 'int', 'default': None}
                        ],
                        'return_type': 'int',
                        'docstring': 'Add two numbers.',
                        'is_async': False,
                        'is_method': True,
                        'decorators': []
                    }]
                }],
                'functions': []
            }]
        }

        builder = APIReferenceBuilder(code_analysis)
        generated = builder.build_reference(self.output_dir)

        # Verify file was generated
        self.assertEqual(len(generated), 1)
        output_file = list(generated.values())[0]
        self.assertTrue(output_file.exists())

        # Verify content
        content = output_file.read_text()
        self.assertIn('### Calculator', content)
        self.assertIn('A simple calculator class', content)
        self.assertIn('**Inherits from**: object', content)
        self.assertIn('##### add', content)
        self.assertIn('Add two numbers', content)

    def test_function_formatting(self):
        """Test markdown formatting for function signatures."""
        code_analysis = {
            'files': [{
                'file': 'utils.py',
                'language': 'Python',
                'classes': [],
                'functions': [{
                    'name': 'calculate_sum',
                    'parameters': [
                        {'name': 'numbers', 'type_hint': 'list', 'default': None}
                    ],
                    'return_type': 'int',
                    'docstring': 'Calculate sum of numbers.',
                    'is_async': False,
                    'is_method': False,
                    'decorators': []
                }]
            }]
        }

        builder = APIReferenceBuilder(code_analysis)
        generated = builder.build_reference(self.output_dir)

        # Verify content
        output_file = list(generated.values())[0]
        content = output_file.read_text()

        self.assertIn('## Functions', content)
        self.assertIn('### calculate_sum', content)
        self.assertIn('Calculate sum of numbers', content)
        self.assertIn('**Returns**: `int`', content)

    def test_parameter_table_generation(self):
        """Test parameter table formatting."""
        code_analysis = {
            'files': [{
                'file': 'test.py',
                'language': 'Python',
                'classes': [],
                'functions': [{
                    'name': 'create_user',
                    'parameters': [
                        {'name': 'name', 'type_hint': 'str', 'default': None},
                        {'name': 'age', 'type_hint': 'int', 'default': '18'},
                        {'name': 'active', 'type_hint': 'bool', 'default': 'True'}
                    ],
                    'return_type': 'dict',
                    'docstring': 'Create a user object.',
                    'is_async': False,
                    'is_method': False,
                    'decorators': []
                }]
            }]
        }

        builder = APIReferenceBuilder(code_analysis)
        generated = builder.build_reference(self.output_dir)

        # Verify parameter table
        output_file = list(generated.values())[0]
        content = output_file.read_text()

        self.assertIn('**Parameters**:', content)
        self.assertIn('| Name | Type | Default | Description |', content)
        self.assertIn('| name | str | - |', content)  # Parameters with no default show "-"
        self.assertIn('| age | int | 18 |', content)
        self.assertIn('| active | bool | True |', content)

    def test_markdown_output_structure(self):
        """Test overall markdown document structure."""
        code_analysis = {
            'files': [{
                'file': 'module.py',
                'language': 'Python',
                'classes': [{
                    'name': 'TestClass',
                    'docstring': 'Test class.',
                    'base_classes': [],
                    'methods': []
                }],
                'functions': [{
                    'name': 'test_func',
                    'parameters': [],
                    'return_type': None,
                    'docstring': 'Test function.',
                    'is_async': False,
                    'is_method': False,
                    'decorators': []
                }]
            }]
        }

        builder = APIReferenceBuilder(code_analysis)
        generated = builder.build_reference(self.output_dir)

        # Verify structure
        output_file = list(generated.values())[0]
        content = output_file.read_text()

        # Check header
        self.assertIn('# API Reference: module.py', content)
        self.assertIn('**Language**: Python', content)
        self.assertIn('**Source**: `module.py`', content)

        # Check sections in order
        classes_pos = content.find('## Classes')
        functions_pos = content.find('## Functions')

        self.assertNotEqual(classes_pos, -1)
        self.assertNotEqual(functions_pos, -1)
        self.assertLess(classes_pos, functions_pos)

    def test_integration_with_code_analyzer(self):
        """Test integration with actual code analyzer output format."""
        # Simulate real code analyzer output
        code_analysis = {
            'files': [
                {
                    'file': 'calculator.py',
                    'language': 'Python',
                    'classes': [{
                        'name': 'Calculator',
                        'base_classes': [],
                        'methods': [
                            {
                                'name': 'add',
                                'parameters': [
                                    {'name': 'a', 'type_hint': 'float', 'default': None},
                                    {'name': 'b', 'type_hint': 'float', 'default': None}
                                ],
                                'return_type': 'float',
                                'docstring': 'Add two numbers.',
                                'decorators': [],
                                'is_async': False,
                                'is_method': True
                            }
                        ],
                        'docstring': 'Calculator class.',
                        'line_number': 1
                    }],
                    'functions': []
                },
                {
                    'file': 'utils.js',
                    'language': 'JavaScript',
                    'classes': [],
                    'functions': [{
                        'name': 'formatDate',
                        'parameters': [
                            {'name': 'date', 'type_hint': None, 'default': None}
                        ],
                        'return_type': None,
                        'docstring': None,
                        'is_async': False,
                        'is_method': False,
                        'decorators': []
                    }]
                }
            ]
        }

        builder = APIReferenceBuilder(code_analysis)
        generated = builder.build_reference(self.output_dir)

        # Verify multiple files generated
        self.assertEqual(len(generated), 2)

        # Verify filenames
        filenames = [f.name for f in generated.values()]
        self.assertIn('calculator.md', filenames)
        self.assertIn('utils.md', filenames)

        # Verify Python file content
        py_file = next(f for f in generated.values() if f.name == 'calculator.md')
        py_content = py_file.read_text()
        self.assertIn('Calculator class', py_content)
        self.assertIn('add(a: float, b: float) → float', py_content)

        # Verify JavaScript file content
        js_file = next(f for f in generated.values() if f.name == 'utils.md')
        js_content = js_file.read_text()
        self.assertIn('formatDate', js_content)
        self.assertIn('**Language**: JavaScript', js_content)

    def test_async_function_indicator(self):
        """Test that async functions are marked in output."""
        code_analysis = {
            'files': [{
                'file': 'async_utils.py',
                'language': 'Python',
                'classes': [],
                'functions': [{
                    'name': 'fetch_data',
                    'parameters': [
                        {'name': 'url', 'type_hint': 'str', 'default': None}
                    ],
                    'return_type': 'dict',
                    'docstring': 'Fetch data from URL.',
                    'is_async': True,
                    'is_method': False,
                    'decorators': []
                }]
            }]
        }

        builder = APIReferenceBuilder(code_analysis)
        generated = builder.build_reference(self.output_dir)

        # Verify async indicator
        output_file = list(generated.values())[0]
        content = output_file.read_text()

        self.assertIn('**Async function**', content)
        self.assertIn('fetch_data', content)

    def test_empty_analysis_skipped(self):
        """Test that files with no analysis are skipped."""
        code_analysis = {
            'files': [
                {
                    'file': 'empty.py',
                    'language': 'Python',
                    'classes': [],
                    'functions': []
                },
                {
                    'file': 'valid.py',
                    'language': 'Python',
                    'classes': [],
                    'functions': [{
                        'name': 'test',
                        'parameters': [],
                        'return_type': None,
                        'docstring': None,
                        'is_async': False,
                        'is_method': False,
                        'decorators': []
                    }]
                }
            ]
        }

        builder = APIReferenceBuilder(code_analysis)
        generated = builder.build_reference(self.output_dir)

        # Only valid.py should be generated
        self.assertEqual(len(generated), 1)
        self.assertIn('valid.py', list(generated.keys())[0])


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
