# Testing Guide

**Version:** 2.7.0
**Last Updated:** 2026-01-18
**Test Count:** 1200+ tests
**Coverage:** >85%
**Status:** ✅ Production Ready

---

## Overview

Skill Seekers has comprehensive test coverage with **1200+ tests** spanning unit tests, integration tests, end-to-end tests, and MCP integration tests. This guide covers everything you need to know about testing in the project.

**Test Philosophy:**
- **Never skip tests** - All tests must pass before commits
- **Test-driven development** - Write tests first when possible
- **Comprehensive coverage** - >80% code coverage minimum
- **Fast feedback** - Unit tests run in seconds
- **CI/CD integration** - Automated testing on every commit

---

## Quick Start

### Running All Tests

```bash
# Install package with dev dependencies
pip install -e ".[all-llms,dev]"

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/skill_seekers --cov-report=html

# View coverage report
open htmlcov/index.html
```

**Expected Output:**
```
============================== test session starts ===============================
platform linux -- Python 3.11.7, pytest-8.4.2, pluggy-1.5.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /path/to/Skill_Seekers
configfile: pyproject.toml
plugins: asyncio-0.24.0, cov-7.0.0
collected 1215 items

tests/test_scraper_features.py::test_detect_language PASSED                 [  1%]
tests/test_scraper_features.py::test_smart_categorize PASSED                [  2%]
...
============================== 1215 passed in 45.23s ==============================
```

---

## Test Structure

### Directory Layout

```
tests/
├── test_*.py                      # Unit tests (800+ tests)
├── test_*_integration.py          # Integration tests (300+ tests)
├── test_*_e2e.py                  # End-to-end tests (100+ tests)
├── test_mcp*.py                   # MCP tests (63 tests)
├── fixtures/                      # Test fixtures and data
│   ├── configs/                   # Test configurations
│   ├── html/                      # Sample HTML files
│   ├── pdfs/                      # Sample PDF files
│   └── repos/                     # Sample repository structures
└── conftest.py                    # Shared pytest fixtures
```

### Test File Naming Conventions

| Pattern | Purpose | Example |
|---------|---------|---------|
| `test_*.py` | Unit tests | `test_doc_scraper.py` |
| `test_*_integration.py` | Integration tests | `test_unified_integration.py` |
| `test_*_e2e.py` | End-to-end tests | `test_install_e2e.py` |
| `test_mcp*.py` | MCP server tests | `test_mcp_fastmcp.py` |

---

## Test Categories

### 1. Unit Tests (800+ tests)

Test individual functions and classes in isolation.

#### Example: Testing Language Detection

```python
# tests/test_scraper_features.py

def test_detect_language():
    """Test code language detection from CSS classes."""
    from skill_seekers.cli.doc_scraper import detect_language

    # Test Python detection
    html = '<code class="language-python">def foo():</code>'
    assert detect_language(html) == 'python'

    # Test JavaScript detection
    html = '<code class="lang-js">const x = 1;</code>'
    assert detect_language(html) == 'javascript'

    # Test heuristics fallback
    html = '<code>def foo():</code>'
    assert detect_language(html) == 'python'

    # Test unknown language
    html = '<code>random text</code>'
    assert detect_language(html) == 'unknown'
```

#### Running Unit Tests

```bash
# All unit tests
pytest tests/test_*.py -v

# Specific test file
pytest tests/test_scraper_features.py -v

# Specific test function
pytest tests/test_scraper_features.py::test_detect_language -v

# With output
pytest tests/test_scraper_features.py -v -s
```

### 2. Integration Tests (300+ tests)

Test multiple components working together.

#### Example: Testing Multi-Source Scraping

```python
# tests/test_unified_integration.py

def test_unified_scraping_integration(tmp_path):
    """Test docs + GitHub + PDF unified scraping."""
    from skill_seekers.cli.unified_scraper import unified_scrape

    # Create unified config
    config = {
        'name': 'test-unified',
        'sources': {
            'documentation': {
                'type': 'docs',
                'base_url': 'https://docs.example.com',
                'selectors': {'main_content': 'article'}
            },
            'github': {
                'type': 'github',
                'repo_url': 'https://github.com/org/repo',
                'analysis_depth': 'basic'
            },
            'pdf': {
                'type': 'pdf',
                'pdf_path': 'tests/fixtures/pdfs/sample.pdf'
            }
        }
    }

    # Run unified scraping
    result = unified_scrape(
        config=config,
        output_dir=tmp_path / 'output'
    )

    # Verify all sources processed
    assert result['success']
    assert len(result['sources']) == 3
    assert 'documentation' in result['sources']
    assert 'github' in result['sources']
    assert 'pdf' in result['sources']

    # Verify skill created
    skill_path = tmp_path / 'output' / 'test-unified' / 'SKILL.md'
    assert skill_path.exists()
```

#### Running Integration Tests

```bash
# All integration tests
pytest tests/test_*_integration.py -v

# Specific integration test
pytest tests/test_unified_integration.py -v

# With coverage
pytest tests/test_*_integration.py --cov=src/skill_seekers
```

### 3. End-to-End Tests (100+ tests)

Test complete user workflows from start to finish.

#### Example: Testing Complete Install Workflow

```python
# tests/test_install_e2e.py

def test_install_workflow_end_to_end(tmp_path):
    """Test complete install workflow: fetch → scrape → package."""
    from skill_seekers.cli.install_skill import install_skill

    # Run complete workflow
    result = install_skill(
        config_name='react',
        target='markdown',      # No API key needed
        output_dir=tmp_path,
        enhance=False,          # Skip AI enhancement
        upload=False,           # Don't upload
        force=True              # Skip confirmations
    )

    # Verify workflow completed
    assert result['success']
    assert result['package_path'].endswith('.zip')

    # Verify package contents
    import zipfile
    with zipfile.ZipFile(result['package_path']) as z:
        files = z.namelist()
        assert 'SKILL.md' in files
        assert 'metadata.json' in files
        assert any(f.startswith('references/') for f in files)
```

#### Running E2E Tests

```bash
# All E2E tests
pytest tests/test_*_e2e.py -v

# Specific E2E test
pytest tests/test_install_e2e.py -v

# E2E tests can be slow, run in parallel
pytest tests/test_*_e2e.py -v -n auto
```

### 4. MCP Tests (63 tests)

Test MCP server and all 18 MCP tools.

#### Example: Testing MCP Tool

```python
# tests/test_mcp_fastmcp.py

@pytest.mark.asyncio
async def test_mcp_list_configs():
    """Test list_configs MCP tool."""
    from skill_seekers.mcp.server_fastmcp import app

    # Call list_configs tool
    result = await app.call_tool('list_configs', {})

    # Verify result structure
    assert 'configs' in result
    assert isinstance(result['configs'], list)
    assert len(result['configs']) > 0

    # Verify config structure
    config = result['configs'][0]
    assert 'name' in config
    assert 'description' in config
    assert 'category' in config
```

#### Running MCP Tests

```bash
# All MCP tests
pytest tests/test_mcp*.py -v

# FastMCP server tests
pytest tests/test_mcp_fastmcp.py -v

# HTTP transport tests
pytest tests/test_server_fastmcp_http.py -v

# With async support
pytest tests/test_mcp*.py -v --asyncio-mode=auto
```

---

## Test Markers

### Available Markers

Pytest markers organize and filter tests:

```python
# Mark slow tests
@pytest.mark.slow
def test_large_documentation_scraping():
    """Slow test - takes 5+ minutes."""
    pass

# Mark async tests
@pytest.mark.asyncio
async def test_async_scraping():
    """Async test using asyncio."""
    pass

# Mark integration tests
@pytest.mark.integration
def test_multi_component_workflow():
    """Integration test."""
    pass

# Mark E2E tests
@pytest.mark.e2e
def test_end_to_end_workflow():
    """End-to-end test."""
    pass
```

### Running Tests by Marker

```bash
# Skip slow tests (default for fast feedback)
pytest tests/ -m "not slow"

# Run only slow tests
pytest tests/ -m slow

# Run only async tests
pytest tests/ -m asyncio

# Run integration + E2E tests
pytest tests/ -m "integration or e2e"

# Run everything except slow tests
pytest tests/ -v -m "not slow"
```

---

## Writing Tests

### Test Structure Pattern

Follow the **Arrange-Act-Assert** pattern:

```python
def test_scrape_single_page():
    """Test scraping a single documentation page."""
    # Arrange: Set up test data and mocks
    base_url = 'https://docs.example.com/intro'
    config = {
        'name': 'test',
        'selectors': {'main_content': 'article'}
    }

    # Act: Execute the function under test
    result = scrape_page(base_url, config)

    # Assert: Verify the outcome
    assert result['title'] == 'Introduction'
    assert 'content' in result
    assert result['url'] == base_url
```

### Using Fixtures

#### Shared Fixtures (conftest.py)

```python
# tests/conftest.py

import pytest
from pathlib import Path

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / 'output'
    output_dir.mkdir()
    return output_dir

@pytest.fixture
def sample_config():
    """Provide sample configuration."""
    return {
        'name': 'test-framework',
        'description': 'Test configuration',
        'base_url': 'https://docs.example.com',
        'selectors': {
            'main_content': 'article',
            'title': 'h1'
        }
    }

@pytest.fixture
def sample_html():
    """Provide sample HTML content."""
    return '''
    <html>
      <body>
        <h1>Test Page</h1>
        <article>
          <p>This is test content.</p>
          <pre><code class="language-python">def foo(): pass</code></pre>
        </article>
      </body>
    </html>
    '''
```

#### Using Fixtures in Tests

```python
def test_with_fixtures(temp_output_dir, sample_config, sample_html):
    """Test using multiple fixtures."""
    # Fixtures are automatically injected
    assert temp_output_dir.exists()
    assert sample_config['name'] == 'test-framework'
    assert '<html>' in sample_html
```

### Mocking External Dependencies

#### Mocking HTTP Requests

```python
from unittest.mock import patch, Mock

@patch('requests.get')
def test_scrape_with_mock(mock_get):
    """Test scraping with mocked HTTP requests."""
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '<html><body>Test</body></html>'
    mock_get.return_value = mock_response

    # Run test
    result = scrape_page('https://example.com')

    # Verify mock was called
    mock_get.assert_called_once_with('https://example.com')
    assert result['content'] == 'Test'
```

#### Mocking File System

```python
from unittest.mock import mock_open, patch

def test_read_config_with_mock():
    """Test config reading with mocked file system."""
    mock_data = '{"name": "test", "base_url": "https://example.com"}'

    with patch('builtins.open', mock_open(read_data=mock_data)):
        config = read_config('config.json')

    assert config['name'] == 'test'
    assert config['base_url'] == 'https://example.com'
```

### Testing Exceptions

```python
import pytest

def test_invalid_config_raises_error():
    """Test that invalid config raises ValueError."""
    from skill_seekers.cli.config_validator import validate_config

    invalid_config = {'name': 'test'}  # Missing required fields

    with pytest.raises(ValueError, match="Missing required field"):
        validate_config(invalid_config)
```

### Parametrized Tests

Test multiple inputs efficiently:

```python
@pytest.mark.parametrize('input_html,expected_lang', [
    ('<code class="language-python">def foo():</code>', 'python'),
    ('<code class="lang-js">const x = 1;</code>', 'javascript'),
    ('<code class="language-rust">fn main() {}</code>', 'rust'),
    ('<code>unknown code</code>', 'unknown'),
])
def test_language_detection_parametrized(input_html, expected_lang):
    """Test language detection with multiple inputs."""
    from skill_seekers.cli.doc_scraper import detect_language

    assert detect_language(input_html) == expected_lang
```

---

## Coverage Analysis

### Generating Coverage Reports

```bash
# Terminal coverage report
pytest tests/ --cov=src/skill_seekers --cov-report=term

# HTML coverage report (recommended)
pytest tests/ --cov=src/skill_seekers --cov-report=html

# XML coverage report (for CI/CD)
pytest tests/ --cov=src/skill_seekers --cov-report=xml

# Combined report
pytest tests/ --cov=src/skill_seekers --cov-report=term --cov-report=html
```

### Understanding Coverage Reports

**Terminal Output:**
```
Name                                          Stmts   Miss  Cover
-----------------------------------------------------------------
src/skill_seekers/__init__.py                     8      0   100%
src/skill_seekers/cli/doc_scraper.py           420     35    92%
src/skill_seekers/cli/github_scraper.py        310     20    94%
src/skill_seekers/cli/adaptors/claude.py       125      5    96%
-----------------------------------------------------------------
TOTAL                                         3500    280    92%
```

**HTML Report:**
- Green lines: Covered by tests
- Red lines: Not covered
- Yellow lines: Partially covered (branches)

### Improving Coverage

```bash
# Find untested code
pytest tests/ --cov=src/skill_seekers --cov-report=html
open htmlcov/index.html

# Click on files with low coverage (red)
# Identify untested lines
# Write tests for uncovered code
```

**Example: Adding Missing Tests**

```python
# Coverage report shows line 145 in doc_scraper.py is uncovered
# Line 145: return "unknown"  # Fallback for unknown languages

# Add test for this branch
def test_detect_language_unknown():
    """Test fallback to 'unknown' for unrecognized code."""
    html = '<code>completely random text</code>'
    assert detect_language(html) == 'unknown'
```

---

## CI/CD Testing

### GitHub Actions Integration

Tests run automatically on every commit and pull request.

#### Workflow Configuration

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, development]
  pull_request:
    branches: [main, development]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ['3.10', '3.11', '3.12', '3.13']

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e ".[all-llms,dev]"

      - name: Run tests
        run: |
          pytest tests/ -v --cov=src/skill_seekers --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
```

### CI Matrix Testing

Tests run across:
- **2 operating systems:** Ubuntu + macOS
- **4 Python versions:** 3.10, 3.11, 3.12, 3.13
- **Total:** 8 test matrix configurations

**Why Matrix Testing:**
- Ensures cross-platform compatibility
- Catches Python version-specific issues
- Validates against multiple environments

### Coverage Reporting

Coverage is uploaded to Codecov for tracking:

```bash
# Generate XML coverage report
pytest tests/ --cov=src/skill_seekers --cov-report=xml

# Upload to Codecov (in CI)
codecov -f coverage.xml
```

---

## Performance Testing

### Measuring Test Performance

```bash
# Show slowest 10 tests
pytest tests/ --durations=10

# Show all test durations
pytest tests/ --durations=0

# Profile test execution
pytest tests/ --profile
```

**Sample Output:**
```
========== slowest 10 durations ==========
12.45s call     tests/test_unified_integration.py::test_large_docs
8.23s call      tests/test_github_scraper.py::test_full_repo_analysis
5.67s call      tests/test_pdf_scraper.py::test_ocr_extraction
3.45s call      tests/test_mcp_fastmcp.py::test_all_tools
2.89s call      tests/test_install_e2e.py::test_complete_workflow
...
```

### Optimizing Slow Tests

**Strategies:**
1. **Mock external calls** - Avoid real HTTP requests
2. **Use smaller test data** - Reduce file sizes
3. **Parallel execution** - Run tests concurrently
4. **Mark as slow** - Skip in fast feedback loop

```python
# Mark slow tests
@pytest.mark.slow
def test_large_dataset():
    """Test with large dataset (slow)."""
    pass

# Run fast tests only
pytest tests/ -m "not slow"
```

### Parallel Test Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest tests/ -n 4

# Auto-detect number of CPUs
pytest tests/ -n auto

# Parallel with coverage
pytest tests/ -n auto --cov=src/skill_seekers
```

---

## Debugging Tests

### Running Tests in Debug Mode

```bash
# Show print statements
pytest tests/test_file.py -v -s

# Very verbose output
pytest tests/test_file.py -vv

# Show local variables on failure
pytest tests/test_file.py -l

# Drop into debugger on failure
pytest tests/test_file.py --pdb

# Stop on first failure
pytest tests/test_file.py -x

# Show traceback for failed tests
pytest tests/test_file.py --tb=short
```

### Using Breakpoints

```python
def test_with_debugging():
    """Test with debugger breakpoint."""
    result = complex_function()

    # Set breakpoint
    import pdb; pdb.set_trace()

    # Or use Python 3.7+ built-in
    breakpoint()

    assert result == expected
```

### Logging in Tests

```python
import logging

def test_with_logging(caplog):
    """Test with log capture."""
    # Set log level
    caplog.set_level(logging.DEBUG)

    # Run function that logs
    result = function_that_logs()

    # Check logs
    assert "Expected log message" in caplog.text
    assert any(record.levelname == "WARNING" for record in caplog.records)
```

---

## Best Practices

### 1. Test Naming

```python
# Good: Descriptive test names
def test_scrape_page_with_missing_title_returns_default():
    """Test that missing title returns 'Untitled'."""
    pass

# Bad: Vague test names
def test_scraping():
    """Test scraping."""
    pass
```

### 2. Single Assertion Focus

```python
# Good: Test one thing
def test_language_detection_python():
    """Test Python language detection."""
    html = '<code class="language-python">def foo():</code>'
    assert detect_language(html) == 'python'

# Acceptable: Multiple related assertions
def test_config_validation():
    """Test config has all required fields."""
    assert 'name' in config
    assert 'base_url' in config
    assert 'selectors' in config
```

### 3. Isolate Tests

```python
# Good: Each test is independent
def test_create_skill(tmp_path):
    """Test skill creation in isolated directory."""
    skill_dir = tmp_path / 'skill'
    create_skill(skill_dir)
    assert skill_dir.exists()

# Bad: Tests depend on order
def test_step1():
    global shared_state
    shared_state = {}

def test_step2():  # Depends on test_step1
    assert shared_state is not None
```

### 4. Keep Tests Fast

```python
# Good: Mock external dependencies
@patch('requests.get')
def test_with_mock(mock_get):
    """Fast test with mocked HTTP."""
    pass

# Bad: Real HTTP requests in tests
def test_with_real_request():
    """Slow test with real HTTP request."""
    response = requests.get('https://example.com')
```

### 5. Use Descriptive Assertions

```python
# Good: Clear assertion messages
assert result == expected, f"Expected {expected}, got {result}"

# Better: Use pytest's automatic messages
assert result == expected

# Best: Custom assertion functions
def assert_valid_skill(skill_path):
    """Assert skill is valid."""
    assert skill_path.exists(), f"Skill not found: {skill_path}"
    assert (skill_path / 'SKILL.md').exists(), "Missing SKILL.md"
```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem:**
```
ImportError: No module named 'skill_seekers'
```

**Solution:**
```bash
# Install package in editable mode
pip install -e ".[all-llms,dev]"
```

#### 2. Fixture Not Found

**Problem:**
```
fixture 'temp_output_dir' not found
```

**Solution:**
```python
# Add fixture to conftest.py or import from another test file
@pytest.fixture
def temp_output_dir(tmp_path):
    return tmp_path / 'output'
```

#### 3. Async Test Failures

**Problem:**
```
RuntimeError: no running event loop
```

**Solution:**
```bash
# Install pytest-asyncio
pip install pytest-asyncio

# Mark async tests
@pytest.mark.asyncio
async def test_async_function():
    await async_operation()
```

#### 4. Coverage Not Tracking

**Problem:**
Coverage shows 0% or incorrect values.

**Solution:**
```bash
# Ensure pytest-cov is installed
pip install pytest-cov

# Specify correct source directory
pytest tests/ --cov=src/skill_seekers
```

---

## Related Documentation

- **[Code Quality Standards](../reference/CODE_QUALITY.md)** - Linting and quality tools
- **[Contributing Guide](../../CONTRIBUTING.md)** - Development guidelines
- **[API Reference](../reference/API_REFERENCE.md)** - Programmatic testing
- **[CI/CD Configuration](../../.github/workflows/ci.yml)** - Automated testing setup

---

**Version:** 2.7.0
**Last Updated:** 2026-01-18
**Test Count:** 1200+ tests
**Coverage:** >85%
**Status:** ✅ Production Ready
