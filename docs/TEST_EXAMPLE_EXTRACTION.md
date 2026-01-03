# Test Example Extraction (C3.2)

**Transform test files into documentation assets by extracting real API usage patterns**

## Overview

The Test Example Extractor analyzes test files to automatically extract meaningful usage examples showing:

- **Object Instantiation**: Real parameter values and configuration
- **Method Calls**: Expected behaviors and return values
- **Configuration Examples**: Valid configuration dictionaries
- **Setup Patterns**: Initialization from setUp() methods and pytest fixtures
- **Multi-Step Workflows**: Integration test sequences

### Supported Languages (9)

| Language | Extraction Method | Supported Features |
|----------|------------------|-------------------|
| **Python** | AST-based (deep) | All categories, high accuracy |
| JavaScript | Regex patterns | Instantiation, assertions, configs |
| TypeScript | Regex patterns | Instantiation, assertions, configs |
| Go | Regex patterns | Table tests, assertions |
| Rust | Regex patterns | Test macros, assertions |
| Java | Regex patterns | JUnit patterns |
| C# | Regex patterns | xUnit patterns |
| PHP | Regex patterns | PHPUnit patterns |
| Ruby | Regex patterns | RSpec patterns |

## Quick Start

### CLI Usage

```bash
# Extract from directory
skill-seekers extract-test-examples tests/ --language python

# Extract from single file
skill-seekers extract-test-examples --file tests/test_scraper.py

# JSON output
skill-seekers extract-test-examples tests/ --json > examples.json

# Markdown output
skill-seekers extract-test-examples tests/ --markdown > examples.md

# Filter by confidence
skill-seekers extract-test-examples tests/ --min-confidence 0.7

# Limit examples per file
skill-seekers extract-test-examples tests/ --max-per-file 5
```

### MCP Tool Usage

```python
# From Claude Code
extract_test_examples(directory="tests/", language="python")

# Single file with JSON output
extract_test_examples(file="tests/test_api.py", json=True)

# High confidence only
extract_test_examples(directory="tests/", min_confidence=0.7)
```

### Codebase Integration

```bash
# Combine with codebase analysis
skill-seekers analyze --directory . --extract-test-examples
```

## Output Formats

### JSON Schema

```json
{
  "total_examples": 42,
  "examples_by_category": {
    "instantiation": 15,
    "method_call": 12,
    "config": 8,
    "setup": 4,
    "workflow": 3
  },
  "examples_by_language": {
    "Python": 42
  },
  "avg_complexity": 0.65,
  "high_value_count": 28,
  "examples": [
    {
      "example_id": "a3f2b1c0",
      "test_name": "test_database_connection",
      "category": "instantiation",
      "code": "db = Database(host=\"localhost\", port=5432)",
      "language": "Python",
      "description": "Instantiate Database: Test database connection",
      "expected_behavior": "self.assertTrue(db.connect())",
      "setup_code": null,
      "file_path": "tests/test_db.py",
      "line_start": 15,
      "line_end": 15,
      "complexity_score": 0.6,
      "confidence": 0.85,
      "tags": ["unittest"],
      "dependencies": ["unittest", "database"]
    }
  ]
}
```

### Markdown Format

```markdown
# Test Example Extraction Report

**Total Examples**: 42
**High Value Examples** (confidence > 0.7): 28
**Average Complexity**: 0.65

## Examples by Category

- **instantiation**: 15
- **method_call**: 12
- **config**: 8
- **setup**: 4
- **workflow**: 3

## Extracted Examples

### test_database_connection

**Category**: instantiation
**Description**: Instantiate Database: Test database connection
**Expected**: self.assertTrue(db.connect())
**Confidence**: 0.85
**Tags**: unittest

```python
db = Database(host="localhost", port=5432)
```

*Source: tests/test_db.py:15*
```

## Extraction Categories

### 1. Instantiation

**Extracts**: Object creation with real parameters

```python
# Example from test
db = Database(
    host="localhost",
    port=5432,
    user="admin",
    password="secret"
)
```

**Use Case**: Shows valid initialization parameters

### 2. Method Call

**Extracts**: Method calls followed by assertions

```python
# Example from test
response = api.get("/users/1")
assert response.status_code == 200
```

**Use Case**: Demonstrates expected behavior

### 3. Config

**Extracts**: Configuration dictionaries (2+ keys)

```python
# Example from test
config = {
    "debug": True,
    "database_url": "postgresql://localhost/test",
    "cache_enabled": False
}
```

**Use Case**: Shows valid configuration examples

### 4. Setup

**Extracts**: setUp() methods and pytest fixtures

```python
# Example from setUp
self.client = APIClient(api_key="test-key")
self.client.connect()
```

**Use Case**: Demonstrates initialization sequences

### 5. Workflow

**Extracts**: Multi-step integration tests (3+ steps)

```python
# Example workflow
user = User(name="John", email="john@example.com")
user.save()
user.verify()
session = user.login(password="secret")
assert session.is_active
```

**Use Case**: Shows complete usage patterns

## Quality Filtering

### Confidence Scoring (0.0 - 1.0)

- **Instantiation**: 0.8 (high - clear object creation)
- **Method Call + Assertion**: 0.85 (very high - behavior proven)
- **Config Dict**: 0.75 (good - clear configuration)
- **Workflow**: 0.9 (excellent - complete pattern)

### Automatic Filtering

**Removes**:
- Trivial patterns: `assertTrue(True)`, `assertEqual(1, 1)`
- Mock-only code: `Mock()`, `MagicMock()`
- Too short: < 20 characters
- Empty constructors: `MyClass()` with no parameters

**Adjustable Thresholds**:
```bash
# High confidence only (0.7+)
--min-confidence 0.7

# Allow lower confidence for discovery
--min-confidence 0.4
```

## Use Cases

### 1. Enhanced Documentation

**Problem**: Documentation often lacks real usage examples

**Solution**: Extract examples from working tests

```bash
# Generate examples for SKILL.md
skill-seekers extract-test-examples tests/ --markdown >> SKILL.md
```

### 2. API Understanding

**Problem**: New developers struggle with API usage

**Solution**: Show how APIs are actually tested

### 3. Tutorial Generation

**Problem**: Creating step-by-step guides is time-consuming

**Solution**: Use workflow examples as tutorial steps

### 4. Configuration Examples

**Problem**: Valid configuration is unclear

**Solution**: Extract config dictionaries from tests

## Architecture

### Core Components

```
TestExampleExtractor (Orchestrator)
├── PythonTestAnalyzer (AST-based)
│   ├── extract_from_test_class()
│   ├── extract_from_test_function()
│   ├── _find_instantiations()
│   ├── _find_method_calls_with_assertions()
│   ├── _find_config_dicts()
│   └── _find_workflows()
├── GenericTestAnalyzer (Regex-based)
│   └── PATTERNS (per-language regex)
└── ExampleQualityFilter
    ├── filter()
    └── _is_trivial()
```

### Data Flow

1. **Find Test Files**: Glob patterns (test_*.py, *_test.go, etc.)
2. **Detect Language**: File extension mapping
3. **Extract Examples**:
   - Python → PythonTestAnalyzer (AST)
   - Others → GenericTestAnalyzer (Regex)
4. **Apply Quality Filter**: Remove trivial patterns
5. **Limit Per File**: Top N by confidence
6. **Generate Report**: JSON or Markdown

## Limitations

### Current Scope

- **Python**: Full AST-based extraction (all categories)
- **Other Languages**: Regex-based (limited to common patterns)
- **Focus**: Test files only (not production code)
- **Complexity**: Simple to moderate test patterns

### Not Extracted

- Complex mocking setups
- Parameterized tests (partial support)
- Nested helper functions
- Dynamically generated tests

### Future Enhancements (Roadmap C3.3-C3.5)

- C3.3: Build 'how to' guides from workflow examples
- C3.4: Extract configuration patterns
- C3.5: Architectural overview from test coverage

## Troubleshooting

### No Examples Extracted

**Symptom**: `total_examples: 0`

**Causes**:
1. Test files not found (check patterns: test_*.py, *_test.go)
2. Confidence threshold too high
3. Language not supported

**Solutions**:
```bash
# Lower confidence threshold
--min-confidence 0.3

# Check test file detection
ls tests/test_*.py

# Verify language support
--language python  # Use supported language
```

### Low Quality Examples

**Symptom**: Many trivial or incomplete examples

**Causes**:
1. Tests use heavy mocking
2. Tests are too simple
3. Confidence threshold too low

**Solutions**:
```bash
# Increase confidence threshold
--min-confidence 0.7

# Reduce examples per file (get best only)
--max-per-file 3
```

### Parsing Errors

**Symptom**: `Failed to parse` warnings

**Causes**:
1. Syntax errors in test files
2. Incompatible Python version
3. Dynamic code generation

**Solutions**:
- Fix syntax errors in test files
- Ensure tests are valid Python/JS/Go code
- Errors are logged but don't stop extraction

## Examples

### Python unittest

```python
# tests/test_database.py
import unittest

class TestDatabase(unittest.TestCase):
    def test_connection(self):
        """Test database connection with real params"""
        db = Database(
            host="localhost",
            port=5432,
            user="admin",
            timeout=30
        )
        self.assertTrue(db.connect())
```

**Extracts**:
- Category: instantiation
- Code: `db = Database(host="localhost", port=5432, user="admin", timeout=30)`
- Confidence: 0.8
- Expected: `self.assertTrue(db.connect())`

### Python pytest

```python
# tests/test_api.py
import pytest

@pytest.fixture
def client():
    return APIClient(base_url="https://api.test.com")

def test_get_user(client):
    """Test fetching user data"""
    response = client.get("/users/123")
    assert response.status_code == 200
    assert response.json()["id"] == 123
```

**Extracts**:
- Category: method_call
- Setup: `# Fixtures: client`
- Code: `response = client.get("/users/123")\nassert response.status_code == 200`
- Confidence: 0.85

### Go Table Test

```go
// add_test.go
func TestAdd(t *testing.T) {
    calc := Calculator{mode: "basic"}
    result := calc.Add(2, 3)
    if result != 5 {
        t.Errorf("Add(2, 3) = %d; want 5", result)
    }
}
```

**Extracts**:
- Category: instantiation
- Code: `calc := Calculator{mode: "basic"}`
- Confidence: 0.6

## Performance

| Metric | Value |
|--------|-------|
| Processing Speed | ~100 files/second (Python AST) |
| Memory Usage | ~50MB for 1000 test files |
| Example Quality | 80%+ high-confidence (>0.7) |
| False Positives | <5% (with default filtering) |

## Integration Points

### 1. Standalone CLI

```bash
skill-seekers extract-test-examples tests/
```

### 2. Codebase Analysis

```bash
codebase-scraper --directory . --extract-test-examples
```

### 3. MCP Server

```python
# Via Claude Code
extract_test_examples(directory="tests/")
```

### 4. Python API

```python
from skill_seekers.cli.test_example_extractor import TestExampleExtractor

extractor = TestExampleExtractor(min_confidence=0.6)
report = extractor.extract_from_directory("tests/")

print(f"Found {report.total_examples} examples")
for example in report.examples:
    print(f"- {example.test_name}: {example.code[:50]}...")
```

## See Also

- [Pattern Detection (C3.1)](../src/skill_seekers/cli/pattern_recognizer.py) - Detect design patterns
- [Codebase Scraper](../src/skill_seekers/cli/codebase_scraper.py) - Analyze local repositories
- [Unified Scraping](UNIFIED_SCRAPING.md) - Multi-source documentation

---

**Status**: ✅ Implemented in v2.6.0
**Issue**: #TBD (C3.2)
**Related Tasks**: C3.1 (Pattern Detection), C3.3-C3.5 (Future enhancements)
