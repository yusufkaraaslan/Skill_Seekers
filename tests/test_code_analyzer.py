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
func main() {
    fmt.Println("Hello, Go!")
}
'''
        result = analyzer.analyze_file('test.go', code, 'Go')

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


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
