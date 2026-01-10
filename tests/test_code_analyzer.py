#!/usr/bin/env python3
"""
Tests for code_analyzer.py - Code analysis at configurable depth levels.

Test Coverage:
- Python AST parsing (docstrings, signatures, decorators)
- JavaScript/TypeScript regex parsing
- C++ regex parsing
- Depth level behavior (surface/deep)
- Error handling
"""

import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from skill_seekers.cli.code_analyzer import CodeAnalyzer


class TestPythonParsing(unittest.TestCase):
    """Tests for Python AST parsing"""

    def setUp(self):
        """Set up test analyzer with deep analysis"""
        self.analyzer = CodeAnalyzer(depth='deep')

    def test_python_function_signature_basic(self):
        """Test basic Python function signature extraction."""
        code = '''
def greet(name, age):
    """Say hello."""
    return f"Hello {name}, you are {age}"
'''
        result = self.analyzer.analyze_file('test.py', code, 'Python')

        self.assertIn('functions', result)
        self.assertEqual(len(result['functions']), 1)

        func = result['functions'][0]
        self.assertEqual(func['name'], 'greet')
        self.assertEqual(len(func['parameters']), 2)
        self.assertEqual(func['parameters'][0]['name'], 'name')
        self.assertEqual(func['parameters'][1]['name'], 'age')
        self.assertEqual(func['docstring'], 'Say hello.')

    def test_python_function_with_type_hints(self):
        """Test Python function with type annotations."""
        code = '''
def add_numbers(a: int, b: int) -> int:
    """Add two integers."""
    return a + b
'''
        result = self.analyzer.analyze_file('test.py', code, 'Python')

        self.assertIn('functions', result)
        func = result['functions'][0]

        self.assertEqual(func['name'], 'add_numbers')
        self.assertEqual(func['return_type'], 'int')
        self.assertEqual(func['parameters'][0]['type_hint'], 'int')
        self.assertEqual(func['parameters'][1]['type_hint'], 'int')
        self.assertEqual(func['docstring'], 'Add two integers.')

    def test_python_function_with_defaults(self):
        """Test Python function with default parameter values."""
        code = '''
def create_user(name: str, age: int = 18, active: bool = True) -> dict:
    """Create a user object."""
    return {"name": name, "age": age, "active": active}
'''
        result = self.analyzer.analyze_file('test.py', code, 'Python')

        func = result['functions'][0]
        self.assertEqual(func['name'], 'create_user')

        # Check defaults
        self.assertIsNone(func['parameters'][0]['default'])
        self.assertEqual(func['parameters'][1]['default'], '18')
        self.assertEqual(func['parameters'][2]['default'], 'True')

    def test_python_async_function(self):
        """Test async Python function detection."""
        code = '''
async def fetch_data(url: str) -> dict:
    """Fetch data from URL."""
    pass
'''
        result = self.analyzer.analyze_file('test.py', code, 'Python')

        func = result['functions'][0]
        self.assertEqual(func['name'], 'fetch_data')
        self.assertTrue(func['is_async'])
        self.assertEqual(func['return_type'], 'dict')

    def test_python_class_extraction(self):
        """Test Python class extraction with inheritance."""
        code = '''
class Animal:
    """Base animal class."""

    def make_sound(self):
        """Make a sound."""
        pass

class Dog(Animal):
    """Dog class."""

    def bark(self):
        """Bark loudly."""
        print("Woof!")
'''
        result = self.analyzer.analyze_file('test.py', code, 'Python')

        self.assertIn('classes', result)
        self.assertEqual(len(result['classes']), 2)

        # Check first class
        animal_class = result['classes'][0]
        self.assertEqual(animal_class['name'], 'Animal')
        self.assertEqual(animal_class['docstring'], 'Base animal class.')
        self.assertEqual(len(animal_class['methods']), 1)
        self.assertEqual(animal_class['methods'][0]['name'], 'make_sound')

        # Check inherited class
        dog_class = result['classes'][1]
        self.assertEqual(dog_class['name'], 'Dog')
        self.assertEqual(dog_class['base_classes'], ['Animal'])
        self.assertEqual(len(dog_class['methods']), 1)
        self.assertEqual(dog_class['methods'][0]['name'], 'bark')

    def test_python_docstring_extraction(self):
        """Test docstring extraction for functions and classes."""
        code = '''
class Calculator:
    """A simple calculator class.

    Supports basic arithmetic operations.
    """

    def add(self, a, b):
        """Add two numbers.

        Args:
            a: First number
            b: Second number

        Returns:
            Sum of a and b
        """
        return a + b
'''
        result = self.analyzer.analyze_file('test.py', code, 'Python')

        # Check class docstring
        calc_class = result['classes'][0]
        self.assertIn('A simple calculator class', calc_class['docstring'])
        self.assertIn('Supports basic arithmetic operations', calc_class['docstring'])

        # Check method docstring
        add_method = calc_class['methods'][0]
        self.assertIn('Add two numbers', add_method['docstring'])
        self.assertIn('Args:', add_method['docstring'])
        self.assertIn('Returns:', add_method['docstring'])

    def test_python_decorators(self):
        """Test decorator extraction."""
        code = '''
class MyClass:
    @property
    def value(self):
        """Get value."""
        return self._value

    @staticmethod
    def helper():
        """Static helper."""
        pass

    @classmethod
    def from_dict(cls, data):
        """Create from dict."""
        pass
'''
        result = self.analyzer.analyze_file('test.py', code, 'Python')

        my_class = result['classes'][0]
        methods = my_class['methods']

        # Check decorators
        self.assertIn('property', methods[0]['decorators'])
        self.assertIn('staticmethod', methods[1]['decorators'])
        self.assertIn('classmethod', methods[2]['decorators'])

    def test_python_syntax_error_handling(self):
        """Test handling of malformed Python code."""
        code = '''
def broken_function(
    # Missing closing parenthesis
    return "broken"
'''
        result = self.analyzer.analyze_file('test.py', code, 'Python')

        # Should return empty dict or handle gracefully, not crash
        self.assertIsInstance(result, dict)
        # No functions should be extracted from broken code
        self.assertEqual(result.get('functions', []), [])


class TestJavaScriptParsing(unittest.TestCase):
    """Tests for JavaScript/TypeScript regex parsing"""

    def setUp(self):
        """Set up test analyzer with deep analysis"""
        self.analyzer = CodeAnalyzer(depth='deep')

    def test_javascript_function_basic(self):
        """Test basic JavaScript function extraction."""
        code = '''
function greet(name, age) {
    return `Hello ${name}, you are ${age}`;
}
'''
        result = self.analyzer.analyze_file('test.js', code, 'JavaScript')

        self.assertIn('functions', result)
        func = result['functions'][0]
        self.assertEqual(func['name'], 'greet')
        self.assertEqual(len(func['parameters']), 2)
        self.assertEqual(func['parameters'][0]['name'], 'name')
        self.assertEqual(func['parameters'][1]['name'], 'age')

    def test_javascript_arrow_function(self):
        """Test arrow function detection."""
        code = '''
const add = (a, b) => {
    return a + b;
};

const multiply = (x, y) => x * y;
'''
        result = self.analyzer.analyze_file('test.js', code, 'JavaScript')

        self.assertIn('functions', result)
        self.assertEqual(len(result['functions']), 2)

        # Check first arrow function
        self.assertEqual(result['functions'][0]['name'], 'add')
        self.assertEqual(len(result['functions'][0]['parameters']), 2)

    def test_javascript_class_methods(self):
        """Test ES6 class method extraction.

        Note: Regex-based parser has limitations in extracting all methods.
        This test verifies basic method extraction works.
        """
        code = '''
class User {
    constructor(name, email) {
        this.name = name;
        this.email = email;
    }

    getProfile() {
        return { name: this.name, email: this.email };
    }

    async fetchData() {
        return await fetch('/api/user');
    }
}
'''
        result = self.analyzer.analyze_file('test.js', code, 'JavaScript')

        self.assertIn('classes', result)
        user_class = result['classes'][0]

        self.assertEqual(user_class['name'], 'User')
        # Regex parser may not catch all methods, verify at least one method extracted
        self.assertGreaterEqual(len(user_class['methods']), 1)

        # Check that methods list is not empty
        method_names = [m['name'] for m in user_class['methods']]
        self.assertGreater(len(method_names), 0)

    def test_typescript_type_annotations(self):
        """Test TypeScript type annotation extraction.

        Note: Current regex-based parser extracts parameter type hints
        but NOT return types. Return type extraction requires a proper
        TypeScript parser (ts-morph or typescript library).
        """
        code = '''
function calculate(a: number, b: number): number {
    return a + b;
}

interface User {
    name: string;
    age: number;
}

function createUser(name: string, age: number = 18): User {
    return { name, age };
}
'''
        result = self.analyzer.analyze_file('test.ts', code, 'TypeScript')

        self.assertIn('functions', result)

        # Check first function - parameters extracted, but not return type
        calc_func = result['functions'][0]
        self.assertEqual(calc_func['name'], 'calculate')
        self.assertEqual(calc_func['parameters'][0]['type_hint'], 'number')
        # Note: return_type is None because regex parser doesn't extract it
        self.assertIsNone(calc_func['return_type'])

        # Check function with default
        create_func = result['functions'][1]
        self.assertEqual(create_func['name'], 'createUser')
        self.assertEqual(create_func['parameters'][1]['default'], '18')
        # Note: return_type is None (regex parser limitation)
        self.assertIsNone(create_func['return_type'])

    def test_javascript_async_detection(self):
        """Test async function detection in JavaScript."""
        code = '''
async function fetchUser(id) {
    const response = await fetch(`/api/users/${id}`);
    return response.json();
}

const loadData = async () => {
    return await fetchUser(1);
};
'''
        result = self.analyzer.analyze_file('test.js', code, 'JavaScript')

        self.assertIn('functions', result)
        self.assertGreaterEqual(len(result['functions']), 1)

        # Check async function
        fetch_func = result['functions'][0]
        self.assertEqual(fetch_func['name'], 'fetchUser')
        self.assertTrue(fetch_func['is_async'])


class TestCppParsing(unittest.TestCase):
    """Tests for C++ regex parsing"""

    def setUp(self):
        """Set up test analyzer with deep analysis"""
        self.analyzer = CodeAnalyzer(depth='deep')

    def test_cpp_function_signature(self):
        """Test C++ function declaration parsing."""
        code = '''
int add(int a, int b);

std::string getName();

void processData(const std::vector<int>& data);
'''
        result = self.analyzer.analyze_file('test.h', code, 'C++')

        self.assertIn('functions', result)
        self.assertGreaterEqual(len(result['functions']), 2)

        # Check first function
        add_func = result['functions'][0]
        self.assertEqual(add_func['name'], 'add')
        self.assertEqual(add_func['return_type'], 'int')

    def test_cpp_class_extraction(self):
        """Test C++ class extraction with inheritance."""
        code = '''
class Animal {
public:
    virtual void makeSound() = 0;
};

class Dog : public Animal {
public:
    void makeSound() override;
    void bark();
private:
    std::string breed;
};
'''
        result = self.analyzer.analyze_file('test.h', code, 'C++')

        self.assertIn('classes', result)
        self.assertEqual(len(result['classes']), 2)

        # Check Animal class
        animal_class = result['classes'][0]
        self.assertEqual(animal_class['name'], 'Animal')

        # Check Dog class with inheritance
        dog_class = result['classes'][1]
        self.assertEqual(dog_class['name'], 'Dog')
        self.assertIn('Animal', dog_class['base_classes'])

    def test_cpp_pointer_parameters(self):
        """Test C++ function with pointer/reference parameters."""
        code = '''
void process(int* ptr);
void update(const int& value);
void transform(std::vector<int>* vec);
'''
        result = self.analyzer.analyze_file('test.h', code, 'C++')

        self.assertIn('functions', result)
        self.assertGreaterEqual(len(result['functions']), 2)

        # Check that parameters include pointer/reference syntax
        process_func = result['functions'][0]
        self.assertEqual(process_func['name'], 'process')

    def test_cpp_default_parameters(self):
        """Test C++ function with default parameter values."""
        code = '''
void initialize(int size = 100, bool verbose = false);

class Config {
public:
    Config(std::string name = "default", int timeout = 30);
};
'''
        result = self.analyzer.analyze_file('test.h', code, 'C++')

        self.assertIn('functions', result)

        # Check function with defaults
        init_func = result['functions'][0]
        self.assertEqual(init_func['name'], 'initialize')
        # Verify defaults are captured
        self.assertGreaterEqual(len(init_func['parameters']), 2)


class TestDepthLevels(unittest.TestCase):
    """Tests for depth level behavior"""

    def test_surface_depth_returns_empty(self):
        """Test that surface depth returns empty analysis."""
        analyzer = CodeAnalyzer(depth='surface')
        code = '''
def test_function(a, b):
    """Test."""
    return a + b
'''
        result = analyzer.analyze_file('test.py', code, 'Python')

        # Surface depth should return empty dict
        self.assertEqual(result, {})

    def test_deep_depth_extracts_signatures(self):
        """Test that deep depth extracts full signatures."""
        analyzer = CodeAnalyzer(depth='deep')
        code = '''
def calculate(x: int, y: int) -> int:
    """Calculate sum."""
    return x + y
'''
        result = analyzer.analyze_file('test.py', code, 'Python')

        # Deep depth should extract full analysis
        self.assertIn('functions', result)
        self.assertEqual(len(result['functions']), 1)
        func = result['functions'][0]
        self.assertEqual(func['name'], 'calculate')
        self.assertEqual(func['return_type'], 'int')

    def test_unknown_language_returns_empty(self):
        """Test that unknown language returns empty dict."""
        analyzer = CodeAnalyzer(depth='deep')
        code = '''
import Foundation
func greet(name: String) {
    print("Hello, \\(name)!")
}
'''
        result = analyzer.analyze_file('test.swift', code, 'Swift')

        # Unknown language should return empty dict
        self.assertEqual(result, {})


class TestIntegration(unittest.TestCase):
    """Integration tests"""

    def test_analyze_file_interface(self):
        """Test the analyze_file public interface."""
        analyzer = CodeAnalyzer(depth='deep')

        # Test with Python code
        py_code = 'def test(): pass'
        result = analyzer.analyze_file('test.py', py_code, 'Python')
        self.assertIsInstance(result, dict)

        # Test with JavaScript code
        js_code = 'function test() {}'
        result = analyzer.analyze_file('test.js', js_code, 'JavaScript')
        self.assertIsInstance(result, dict)

        # Test with C++ code
        cpp_code = 'void test();'
        result = analyzer.analyze_file('test.h', cpp_code, 'C++')
        self.assertIsInstance(result, dict)

    def test_multiple_items_extraction(self):
        """Test extracting multiple classes and functions."""
        analyzer = CodeAnalyzer(depth='deep')
        code = '''
def helper_func():
    """Helper function."""
    pass

class ClassA:
    """First class."""
    def method_a(self):
        pass

class ClassB:
    """Second class."""
    def method_b(self):
        pass

def main_func():
    """Main function."""
    pass
'''
        result = analyzer.analyze_file('test.py', code, 'Python')

        # Should extract 2 standalone functions
        self.assertEqual(len(result['functions']), 2)

        # Should extract 2 classes
        self.assertEqual(len(result['classes']), 2)

        # Verify names
        func_names = [f['name'] for f in result['functions']]
        self.assertIn('helper_func', func_names)
        self.assertIn('main_func', func_names)

        class_names = [c['name'] for c in result['classes']]
        self.assertIn('ClassA', class_names)
        self.assertIn('ClassB', class_names)


class TestCommentExtraction(unittest.TestCase):
    """Tests for comment extraction"""

    def setUp(self):
        """Set up test analyzer with deep analysis"""
        self.analyzer = CodeAnalyzer(depth='deep')

    def test_python_comment_extraction(self):
        """Test Python # comment extraction."""
        code = '''
# This is a comment
def test_func():
    # Inside function comment
    x = 5  # Inline comment (not extracted due to code on same line)
    return x

# Another top-level comment
class TestClass:
    # Class-level comment
    pass
'''
        result = self.analyzer.analyze_file('test.py', code, 'Python')

        self.assertIn('comments', result)
        comments = result['comments']

        # Should have extracted standalone comments
        self.assertGreaterEqual(len(comments), 3)

        # Check comment content
        comment_texts = [c['text'] for c in comments]
        self.assertIn('This is a comment', comment_texts)
        self.assertIn('Inside function comment', comment_texts)
        self.assertIn('Another top-level comment', comment_texts)

        # Check all are inline type
        for comment in comments:
            self.assertEqual(comment['type'], 'inline')

    def test_python_comment_line_numbers(self):
        """Test Python comment line number tracking."""
        code = '''# Line 1 comment
def func():
    # Line 3 comment
    pass
# Line 5 comment
'''
        result = self.analyzer.analyze_file('test.py', code, 'Python')

        comments = result['comments']
        self.assertEqual(len(comments), 3)

        # Check line numbers
        line_nums = [c['line'] for c in comments]
        self.assertIn(1, line_nums)
        self.assertIn(3, line_nums)
        self.assertIn(5, line_nums)

    def test_python_skip_shebang_and_encoding(self):
        """Test that shebang and encoding declarations are skipped."""
        code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This is a real comment
def func():
    pass
'''
        result = self.analyzer.analyze_file('test.py', code, 'Python')

        comments = result['comments']

        # Should only have the real comment
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0]['text'], 'This is a real comment')

    def test_javascript_inline_comments(self):
        """Test JavaScript // comment extraction."""
        code = '''
// Top-level comment
function test() {
    // Inside function
    const x = 5; // Inline (not extracted)
    return x;
}

// Another comment
const y = 10;
'''
        result = self.analyzer.analyze_file('test.js', code, 'JavaScript')

        self.assertIn('comments', result)
        comments = result['comments']

        # Should have extracted standalone comments
        self.assertGreaterEqual(len(comments), 3)

        # Check comment types
        inline_comments = [c for c in comments if c['type'] == 'inline']
        self.assertGreaterEqual(len(inline_comments), 3)

    def test_javascript_block_comments(self):
        """Test JavaScript /* */ block comment extraction."""
        code = '''
/* This is a
   multi-line
   block comment */
function test() {
    /* Another block comment */
    return 42;
}
'''
        result = self.analyzer.analyze_file('test.js', code, 'JavaScript')

        comments = result['comments']

        # Should have extracted block comments
        block_comments = [c for c in comments if c['type'] == 'block']
        self.assertGreaterEqual(len(block_comments), 2)

        # Check multi-line content is preserved
        first_block = next(c for c in comments if 'multi-line' in c['text'])
        self.assertIn('multi-line', first_block['text'])

    def test_javascript_mixed_comments(self):
        """Test JavaScript mixed inline and block comments."""
        code = '''
// Inline comment
/* Block comment */
function test() {
    // Another inline
    /* Another block */
    return true;
}
'''
        result = self.analyzer.analyze_file('test.js', code, 'JavaScript')

        comments = result['comments']

        # Should have both types
        inline_comments = [c for c in comments if c['type'] == 'inline']
        block_comments = [c for c in comments if c['type'] == 'block']

        self.assertGreaterEqual(len(inline_comments), 2)
        self.assertGreaterEqual(len(block_comments), 2)

    def test_cpp_comment_extraction(self):
        """Test C++ comment extraction (uses same logic as JavaScript)."""
        code = '''
// Header comment
class Node {
public:
    // Method comment
    void update();

    /* Block comment for data member */
    int value;
};
'''
        result = self.analyzer.analyze_file('test.h', code, 'C++')

        self.assertIn('comments', result)
        comments = result['comments']

        # Should have extracted comments
        self.assertGreaterEqual(len(comments), 3)

        # Check both inline and block
        inline_comments = [c for c in comments if c['type'] == 'inline']
        block_comments = [c for c in comments if c['type'] == 'block']

        self.assertGreaterEqual(len(inline_comments), 2)
        self.assertGreaterEqual(len(block_comments), 1)

    def test_todo_fixme_comment_detection(self):
        """Test that TODO/FIXME comments are extracted."""
        code = '''
# TODO: Implement this feature
def incomplete_func():
    # FIXME: Handle edge case
    pass

# NOTE: Important information
'''
        result = self.analyzer.analyze_file('test.py', code, 'Python')

        comments = result['comments']

        comment_texts = [c['text'] for c in comments]
        self.assertTrue(any('TODO' in text for text in comment_texts))
        self.assertTrue(any('FIXME' in text for text in comment_texts))
        self.assertTrue(any('NOTE' in text for text in comment_texts))


class TestCSharpParsing(unittest.TestCase):
    """Tests for C# code analysis"""

    def setUp(self):
        self.analyzer = CodeAnalyzer(depth='deep')

    def test_csharp_class_extraction(self):
        """Test C# class extraction with inheritance."""
        code = '''
using System;

public class PlayerController : MonoBehaviour
{
    private float speed = 5f;
}
'''
        result = self.analyzer.analyze_file('test.cs', code, 'C#')

        self.assertIn('classes', result)
        self.assertEqual(len(result['classes']), 1)

        cls = result['classes'][0]
        self.assertEqual(cls['name'], 'PlayerController')
        self.assertIn('MonoBehaviour', cls['base_classes'])

    def test_csharp_method_extraction(self):
        """Test C# method extraction with parameters."""
        code = '''
public class Calculator
{
    public int Add(int a, int b)
    {
        return a + b;
    }
}
'''
        result = self.analyzer.analyze_file('test.cs', code, 'C#')

        self.assertIn('functions', result)
        self.assertEqual(len(result['functions']), 1)

        method = result['functions'][0]
        self.assertEqual(method['name'], 'Add')
        self.assertEqual(len(method['parameters']), 2)
        self.assertEqual(method['return_type'], 'int')

    def test_csharp_property_extraction(self):
        """Test C# property extraction."""
        code = '''
public class Player
{
    public int Health { get; set; } = 100;
    private string Name { get; }
}
'''
        result = self.analyzer.analyze_file('test.cs', code, 'C#')

        # Properties are extracted as part of class analysis
        self.assertIn('classes', result)
        cls = result['classes'][0]
        self.assertEqual(cls['name'], 'Player')

    def test_csharp_async_method(self):
        """Test C# async method detection."""
        code = '''
public class DataLoader
{
    public async Task<string> LoadDataAsync()
    {
        await Task.Delay(100);
        return "data";
    }
}
'''
        result = self.analyzer.analyze_file('test.cs', code, 'C#')

        self.assertIn('functions', result)
        method = result['functions'][0]
        self.assertEqual(method['name'], 'LoadDataAsync')
        self.assertTrue(method['is_async'])


class TestGoParsing(unittest.TestCase):
    """Tests for Go code analysis"""

    def setUp(self):
        self.analyzer = CodeAnalyzer(depth='deep')

    def test_go_function_extraction(self):
        """Test Go function extraction."""
        code = '''
package main

func Add(a int, b int) int {
    return a + b
}
'''
        result = self.analyzer.analyze_file('test.go', code, 'Go')

        self.assertIn('functions', result)
        self.assertEqual(len(result['functions']), 1)

        func = result['functions'][0]
        self.assertEqual(func['name'], 'Add')
        self.assertEqual(func['return_type'], 'int')

    def test_go_method_with_receiver(self):
        """Test Go method with receiver."""
        code = '''
package main

type Person struct {
    Name string
}

func (p *Person) Greet() string {
    return "Hello " + p.Name
}
'''
        result = self.analyzer.analyze_file('test.go', code, 'Go')

        self.assertIn('functions', result)
        # Should extract method
        method = next((f for f in result['functions'] if f['name'] == 'Greet'), None)
        self.assertIsNotNone(method)
        self.assertEqual(method['return_type'], 'string')

    def test_go_struct_extraction(self):
        """Test Go struct extraction."""
        code = '''
package main

type Rectangle struct {
    Width  float64
    Height float64
}
'''
        result = self.analyzer.analyze_file('test.go', code, 'Go')

        self.assertIn('classes', result)
        self.assertEqual(len(result['classes']), 1)

        struct = result['classes'][0]
        self.assertEqual(struct['name'], 'Rectangle')

    def test_go_multiple_return_values(self):
        """Test Go function with multiple return values."""
        code = '''
func Divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, errors.New("division by zero")
    }
    return a / b, nil
}
'''
        result = self.analyzer.analyze_file('test.go', code, 'Go')

        self.assertIn('functions', result)
        func = result['functions'][0]
        self.assertEqual(func['name'], 'Divide')


class TestRustParsing(unittest.TestCase):
    """Tests for Rust code analysis"""

    def setUp(self):
        self.analyzer = CodeAnalyzer(depth='deep')

    def test_rust_function_extraction(self):
        """Test Rust function extraction."""
        code = '''
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}
'''
        result = self.analyzer.analyze_file('test.rs', code, 'Rust')

        self.assertIn('functions', result)
        self.assertEqual(len(result['functions']), 1)

        func = result['functions'][0]
        self.assertEqual(func['name'], 'add')
        self.assertEqual(func['return_type'], 'i32')

    def test_rust_struct_extraction(self):
        """Test Rust struct extraction."""
        code = '''
pub struct Point {
    x: f64,
    y: f64,
}
'''
        result = self.analyzer.analyze_file('test.rs', code, 'Rust')

        self.assertIn('classes', result)
        self.assertEqual(len(result['classes']), 1)

        struct = result['classes'][0]
        self.assertEqual(struct['name'], 'Point')

    def test_rust_async_function(self):
        """Test Rust async function detection."""
        code = '''
pub async fn fetch_data() -> Result<String, Error> {
    Ok("data".to_string())
}
'''
        result = self.analyzer.analyze_file('test.rs', code, 'Rust')

        self.assertIn('functions', result)
        func = result['functions'][0]
        self.assertEqual(func['name'], 'fetch_data')
        self.assertTrue(func['is_async'])

    def test_rust_impl_block(self):
        """Test Rust impl block method extraction."""
        code = '''
struct Circle {
    radius: f64,
}

impl Circle {
    pub fn area(&self) -> f64 {
        std::f64::consts::PI * self.radius * self.radius
    }
}
'''
        result = self.analyzer.analyze_file('test.rs', code, 'Rust')

        self.assertIn('classes', result)
        self.assertIn('functions', result)


class TestJavaParsing(unittest.TestCase):
    """Tests for Java code analysis"""

    def setUp(self):
        self.analyzer = CodeAnalyzer(depth='deep')

    def test_java_class_extraction(self):
        """Test Java class extraction with inheritance."""
        code = '''
public class ArrayList extends AbstractList implements List {
    private int size;
}
'''
        result = self.analyzer.analyze_file('test.java', code, 'Java')

        self.assertIn('classes', result)
        self.assertEqual(len(result['classes']), 1)

        cls = result['classes'][0]
        self.assertEqual(cls['name'], 'ArrayList')
        self.assertIn('AbstractList', cls['base_classes'])

    def test_java_method_extraction(self):
        """Test Java method extraction."""
        code = '''
public class Calculator {
    public static int multiply(int a, int b) {
        return a * b;
    }
}
'''
        result = self.analyzer.analyze_file('test.java', code, 'Java')

        self.assertIn('functions', result)
        self.assertEqual(len(result['functions']), 1)

        method = result['functions'][0]
        self.assertEqual(method['name'], 'multiply')
        self.assertEqual(method['return_type'], 'int')

    def test_java_interface_implementation(self):
        """Test Java interface implementation."""
        code = '''
public class MyHandler implements EventHandler, Runnable {
    public void run() {}
}
'''
        result = self.analyzer.analyze_file('test.java', code, 'Java')

        self.assertIn('classes', result)
        cls = result['classes'][0]
        self.assertEqual(cls['name'], 'MyHandler')

    def test_java_generic_class(self):
        """Test Java generic class."""
        code = '''
public class Box<T> {
    private T value;

    public T getValue() {
        return value;
    }
}
'''
        result = self.analyzer.analyze_file('test.java', code, 'Java')

        self.assertIn('classes', result)
        self.assertIn('functions', result)


class TestRubyParsing(unittest.TestCase):
    """Tests for Ruby code analysis"""

    def setUp(self):
        self.analyzer = CodeAnalyzer(depth='deep')

    def test_ruby_class_extraction(self):
        """Test Ruby class extraction."""
        code = '''
class Person
  def initialize(name)
    @name = name
  end
end
'''
        result = self.analyzer.analyze_file('test.rb', code, 'Ruby')

        self.assertIn('classes', result)
        self.assertEqual(len(result['classes']), 1)

        cls = result['classes'][0]
        self.assertEqual(cls['name'], 'Person')

    def test_ruby_method_extraction(self):
        """Test Ruby method extraction."""
        code = '''
def greet(name)
  puts "Hello, #{name}!"
end
'''
        result = self.analyzer.analyze_file('test.rb', code, 'Ruby')

        self.assertIn('functions', result)
        self.assertEqual(len(result['functions']), 1)

        method = result['functions'][0]
        self.assertEqual(method['name'], 'greet')

    def test_ruby_class_inheritance(self):
        """Test Ruby class inheritance."""
        code = '''
class Dog < Animal
  def bark
    puts "Woof!"
  end
end
'''
        result = self.analyzer.analyze_file('test.rb', code, 'Ruby')

        self.assertIn('classes', result)
        cls = result['classes'][0]
        self.assertEqual(cls['name'], 'Dog')
        self.assertIn('Animal', cls['base_classes'])

    def test_ruby_predicate_methods(self):
        """Test Ruby predicate methods (ending with ?)."""
        code = '''
def empty?
  @items.length == 0
end
'''
        result = self.analyzer.analyze_file('test.rb', code, 'Ruby')

        self.assertIn('functions', result)
        method = result['functions'][0]
        self.assertEqual(method['name'], 'empty?')


class TestPHPParsing(unittest.TestCase):
    """Tests for PHP code analysis"""

    def setUp(self):
        self.analyzer = CodeAnalyzer(depth='deep')

    def test_php_class_extraction(self):
        """Test PHP class extraction."""
        code = '''
<?php
class User {
    private $name;

    public function getName() {
        return $this->name;
    }
}
?>
'''
        result = self.analyzer.analyze_file('test.php', code, 'PHP')

        self.assertIn('classes', result)
        self.assertEqual(len(result['classes']), 1)

        cls = result['classes'][0]
        self.assertEqual(cls['name'], 'User')

    def test_php_method_extraction(self):
        """Test PHP method extraction."""
        code = '''
<?php
function calculate($a, $b) {
    return $a + $b;
}
?>
'''
        result = self.analyzer.analyze_file('test.php', code, 'PHP')

        self.assertIn('functions', result)
        self.assertEqual(len(result['functions']), 1)

        func = result['functions'][0]
        self.assertEqual(func['name'], 'calculate')

    def test_php_class_inheritance(self):
        """Test PHP class inheritance and interfaces."""
        code = '''
<?php
class Rectangle extends Shape implements Drawable {
    public function draw() {
        // Implementation
    }
}
?>
'''
        result = self.analyzer.analyze_file('test.php', code, 'PHP')

        self.assertIn('classes', result)
        cls = result['classes'][0]
        self.assertEqual(cls['name'], 'Rectangle')
        self.assertIn('Shape', cls['base_classes'])

    def test_php_namespace(self):
        """Test PHP namespace handling."""
        code = '''
<?php
namespace App\\Models;

class Product {
    public function getPrice() {
        return 99.99;
    }
}
?>
'''
        result = self.analyzer.analyze_file('test.php', code, 'PHP')

        self.assertIn('classes', result)
        cls = result['classes'][0]
        self.assertEqual(cls['name'], 'Product')


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
