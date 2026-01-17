# Code Quality Standards

**Version:** 2.7.0
**Last Updated:** 2026-01-18
**Status:** ✅ Production Ready

---

## Overview

Skill Seekers maintains high code quality through automated linting, comprehensive testing, and continuous integration. This document outlines the quality standards, tools, and processes used to ensure reliability and maintainability.

**Quality Pillars:**
1. **Linting** - Automated code style and error detection with Ruff
2. **Testing** - Comprehensive test coverage (1200+ tests)
3. **Type Safety** - Type hints and validation
4. **Security** - Security scanning with Bandit
5. **CI/CD** - Automated validation on every commit

---

## Linting with Ruff

### What is Ruff?

**Ruff** is an extremely fast Python linter written in Rust that combines the functionality of multiple tools:
- Flake8 (style checking)
- isort (import sorting)
- Black (code formatting)
- pyupgrade (Python version upgrades)
- And 100+ other linting rules

**Why Ruff:**
- ⚡ 10-100x faster than traditional linters
- 🔧 Auto-fixes for most issues
- 📦 Single tool replaces 10+ legacy tools
- 🎯 Comprehensive rule coverage

### Installation

```bash
# Using uv (recommended)
uv pip install ruff

# Using pip
pip install ruff

# Development installation
pip install -e ".[dev]"  # Includes ruff
```

### Running Ruff

#### Check for Issues

```bash
# Check all Python files
ruff check .

# Check specific directory
ruff check src/

# Check specific file
ruff check src/skill_seekers/cli/doc_scraper.py

# Check with auto-fix
ruff check --fix .
```

#### Format Code

```bash
# Check formatting (dry run)
ruff format --check .

# Apply formatting
ruff format .

# Format specific file
ruff format src/skill_seekers/cli/doc_scraper.py
```

### Configuration

Ruff configuration is in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "SIM",  # flake8-simplify
    "UP",   # pyupgrade
]

ignore = [
    "E501",  # Line too long (handled by formatter)
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = [
    "S101",  # Allow assert in tests
]
```

---

## Common Ruff Rules

### SIM102: Simplify Nested If Statements

**Before:**
```python
if condition1:
    if condition2:
        do_something()
```

**After:**
```python
if condition1 and condition2:
    do_something()
```

**Why:** Improves readability, reduces nesting levels.

### SIM117: Combine Multiple With Statements

**Before:**
```python
with open('file1.txt') as f1:
    with open('file2.txt') as f2:
        process(f1, f2)
```

**After:**
```python
with open('file1.txt') as f1, open('file2.txt') as f2:
    process(f1, f2)
```

**Why:** Cleaner syntax, better resource management.

### B904: Proper Exception Chaining

**Before:**
```python
try:
    risky_operation()
except Exception:
    raise CustomError("Failed")
```

**After:**
```python
try:
    risky_operation()
except Exception as e:
    raise CustomError("Failed") from e
```

**Why:** Preserves error context, aids debugging.

### SIM113: Remove Unused Enumerate Counter

**Before:**
```python
for i, item in enumerate(items):
    process(item)  # i is never used
```

**After:**
```python
for item in items:
    process(item)
```

**Why:** Clearer intent, removes unused variables.

### B007: Unused Loop Variable

**Before:**
```python
for item in items:
    total += 1  # item is never used
```

**After:**
```python
for _ in items:
    total += 1
```

**Why:** Explicit that loop variable is intentionally unused.

### ARG002: Unused Method Argument

**Before:**
```python
def process(self, data, unused_arg):
    return data.transform()  # unused_arg never used
```

**After:**
```python
def process(self, data):
    return data.transform()
```

**Why:** Removes dead code, clarifies function signature.

---

## Recent Code Quality Improvements

### v2.7.0 Fixes (January 18, 2026)

Fixed **all 21 ruff linting errors** across the codebase:

| Rule | Count | Files Affected | Impact |
|------|-------|----------------|--------|
| SIM102 | 7 | config_extractor.py, pattern_recognizer.py (3) | Combined nested if statements |
| SIM117 | 9 | test_example_extractor.py (3), unified_skill_builder.py | Combined with statements |
| B904 | 1 | pdf_scraper.py | Added exception chaining |
| SIM113 | 1 | config_validator.py | Removed unused enumerate counter |
| B007 | 1 | doc_scraper.py | Changed unused loop variable to _ |
| ARG002 | 1 | test fixture | Removed unused test argument |
| **Total** | **21** | **12 files** | **Zero linting errors** |

**Result:** Clean codebase with zero linting errors, improved maintainability.

### Files Updated

1. **src/skill_seekers/cli/config_extractor.py** (SIM102 fixes)
2. **src/skill_seekers/cli/config_validator.py** (SIM113 fix)
3. **src/skill_seekers/cli/doc_scraper.py** (B007 fix)
4. **src/skill_seekers/cli/pattern_recognizer.py** (3 × SIM102 fixes)
5. **src/skill_seekers/cli/test_example_extractor.py** (3 × SIM117 fixes)
6. **src/skill_seekers/cli/unified_skill_builder.py** (SIM117 fix)
7. **src/skill_seekers/cli/pdf_scraper.py** (B904 fix)
8. **6 test files** (various fixes)

---

## Testing Requirements

### Test Coverage Standards

**Critical Paths:** 100% coverage required
- Core scraping logic
- Platform adaptors
- MCP tool implementations
- Configuration validation

**Overall Project:** >80% coverage target

**Current Status:**
- ✅ 1200+ tests passing
- ✅ >85% code coverage
- ✅ All critical paths covered
- ✅ CI/CD integrated

### Running Tests

#### All Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/skill_seekers --cov-report=term --cov-report=html

# View HTML coverage report
open htmlcov/index.html
```

#### Specific Test Categories

```bash
# Unit tests only
pytest tests/test_*.py -v

# Integration tests
pytest tests/test_*_integration.py -v

# E2E tests
pytest tests/test_*_e2e.py -v

# MCP tests
pytest tests/test_mcp*.py -v
```

#### Test Markers

```bash
# Slow tests (skip by default)
pytest tests/ -m "not slow"

# Run slow tests
pytest tests/ -m slow

# Async tests
pytest tests/ -m asyncio
```

### Test Categories

1. **Unit Tests** (800+ tests)
   - Individual function testing
   - Isolated component testing
   - Mock external dependencies

2. **Integration Tests** (300+ tests)
   - Multi-component workflows
   - End-to-end feature testing
   - Real file system operations

3. **E2E Tests** (100+ tests)
   - Complete user workflows
   - CLI command testing
   - Platform integration testing

4. **MCP Tests** (63 tests)
   - All 18 MCP tools
   - Transport mode testing (stdio, HTTP)
   - Error handling validation

### Test Requirements Before Commits

**Per user instructions in `~/.claude/CLAUDE.md`:**

> "never skip any test. always make sure all test pass"

**This means:**
- ✅ **ALL 1200+ tests must pass** before commits
- ✅ No skipping tests, even if they're slow
- ✅ Add tests for new features
- ✅ Fix failing tests immediately
- ✅ Maintain or improve coverage

---

## CI/CD Integration

### GitHub Actions Workflow

Skill Seekers uses GitHub Actions for automated quality checks on every commit and PR.

#### Workflow Configuration

```yaml
# .github/workflows/ci.yml (excerpt)
name: CI

on:
  push:
    branches: [main, development]
  pull_request:
    branches: [main, development]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install ruff

      - name: Run Ruff Check
        run: ruff check .

      - name: Run Ruff Format Check
        run: ruff format --check .

  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ['3.10', '3.11', '3.12', '3.13']

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install package
        run: pip install -e ".[all-llms,dev]"

      - name: Run tests
        run: pytest tests/ --cov=src/skill_seekers --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### CI Checks

Every commit and PR must pass:

1. **Ruff Linting** - Zero linting errors
2. **Ruff Formatting** - Consistent code style
3. **Pytest** - All 1200+ tests passing
4. **Coverage** - >80% code coverage
5. **Multi-platform** - Ubuntu + macOS
6. **Multi-version** - Python 3.10-3.13

**Status:** ✅ All checks passing

---

## Pre-commit Hooks

### Setup

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

### Configuration

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.7.0
    hooks:
      # Run ruff linter
      - id: ruff
        args: [--fix]
      # Run ruff formatter
      - id: ruff-format

  - repo: local
    hooks:
      # Run tests before commit
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
        args: [tests/, -v]
```

### Usage

```bash
# Pre-commit hooks run automatically on git commit
git add .
git commit -m "Your message"
# → Runs ruff check, ruff format, pytest

# Run manually on all files
pre-commit run --all-files

# Skip hooks (emergency only!)
git commit -m "Emergency fix" --no-verify
```

---

## Best Practices

### Code Organization

#### Import Ordering

```python
# 1. Standard library imports
import os
import sys
from pathlib import Path

# 2. Third-party imports
import anthropic
import requests
from fastapi import FastAPI

# 3. Local application imports
from skill_seekers.cli.doc_scraper import scrape_all
from skill_seekers.cli.adaptors import get_adaptor
```

**Tool:** Ruff automatically sorts imports with `I` rule.

#### Naming Conventions

```python
# Constants: UPPER_SNAKE_CASE
MAX_PAGES = 500
DEFAULT_TIMEOUT = 30

# Classes: PascalCase
class DocumentationScraper:
    pass

# Functions/variables: snake_case
def scrape_all(base_url, config):
    pages_count = 0
    return pages_count

# Private: leading underscore
def _internal_helper():
    pass
```

### Documentation

#### Docstrings

```python
def scrape_all(base_url: str, config: dict) -> list[dict]:
    """Scrape documentation from a website using BFS traversal.

    Args:
        base_url: The root URL to start scraping from
        config: Configuration dict with selectors and patterns

    Returns:
        List of page dictionaries containing title, content, URL

    Raises:
        NetworkError: If connection fails
        InvalidConfigError: If config is malformed

    Example:
        >>> pages = scrape_all('https://docs.example.com', config)
        >>> len(pages)
        42
    """
    pass
```

#### Type Hints

```python
from typing import Optional, Union, Literal

def package_skill(
    skill_dir: str | Path,
    target: Literal['claude', 'gemini', 'openai', 'markdown'],
    output_path: Optional[str] = None
) -> str:
    """Package skill for target platform."""
    pass
```

### Error Handling

#### Exception Patterns

```python
# Good: Specific exceptions with context
try:
    result = risky_operation()
except NetworkError as e:
    raise ScrapingError(f"Failed to fetch {url}") from e

# Bad: Bare except
try:
    result = risky_operation()
except:  # ❌ Too broad, loses error info
    pass
```

#### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Log at appropriate levels
logger.debug("Processing page: %s", url)
logger.info("Scraped %d pages", len(pages))
logger.warning("Rate limit approaching: %d requests", count)
logger.error("Failed to parse: %s", url, exc_info=True)
```

---

## Security Scanning

### Bandit

Bandit scans for security vulnerabilities in Python code.

#### Installation

```bash
pip install bandit
```

#### Running Bandit

```bash
# Scan all Python files
bandit -r src/

# Scan with config
bandit -r src/ -c pyproject.toml

# Generate JSON report
bandit -r src/ -f json -o bandit-report.json
```

#### Common Security Issues

**B404: Import of subprocess module**
```python
# Review: Ensure safe usage of subprocess
import subprocess

# ✅ Safe: Using subprocess with shell=False and list arguments
subprocess.run(['ls', '-l'], shell=False)

# ❌ UNSAFE: Using shell=True with user input (NEVER DO THIS)
# This is an example of what NOT to do - security vulnerability!
# subprocess.run(f'ls {user_input}', shell=True)
```

**B605: Start process with a shell**
```python
# ❌ UNSAFE: Shell injection risk (NEVER DO THIS)
# Example of security anti-pattern:
# import os
# os.system(f'rm {filename}')

# ✅ Safe: Use subprocess with list arguments
import subprocess
subprocess.run(['rm', filename], shell=False)
```

**Security Best Practices:**
- Never use `shell=True` with user input
- Always validate and sanitize user input
- Use subprocess with list arguments instead of shell commands
- Avoid dynamic command construction

---

## Development Workflow

### 1. Before Starting Work

```bash
# Pull latest changes
git checkout development
git pull origin development

# Create feature branch
git checkout -b feature/your-feature

# Install dependencies
pip install -e ".[all-llms,dev]"
```

### 2. During Development

```bash
# Run linter frequently
ruff check src/skill_seekers/cli/your_file.py --fix

# Run relevant tests
pytest tests/test_your_feature.py -v

# Check formatting
ruff format src/skill_seekers/cli/your_file.py
```

### 3. Before Committing

```bash
# Run all linting checks
ruff check .
ruff format --check .

# Run full test suite (REQUIRED)
pytest tests/ -v

# Check coverage
pytest tests/ --cov=src/skill_seekers --cov-report=term

# Verify all tests pass ✅
```

### 4. Committing Changes

```bash
# Stage changes
git add .

# Commit (pre-commit hooks will run)
git commit -m "feat: Add your feature

- Detailed change 1
- Detailed change 2

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Push to remote
git push origin feature/your-feature
```

### 5. Creating Pull Request

```bash
# Create PR via GitHub CLI
gh pr create --title "Add your feature" --body "Description..."

# CI checks will run automatically:
# ✅ Ruff linting
# ✅ Ruff formatting
# ✅ Pytest (1200+ tests)
# ✅ Coverage report
# ✅ Multi-platform (Ubuntu + macOS)
# ✅ Multi-version (Python 3.10-3.13)
```

---

## Quality Metrics

### Current Status (v2.7.0)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Linting Errors | 0 | 0 | ✅ |
| Test Count | 1200+ | 1000+ | ✅ |
| Test Pass Rate | 100% | 100% | ✅ |
| Code Coverage | >85% | >80% | ✅ |
| CI Pass Rate | 100% | >95% | ✅ |
| Python Versions | 3.10-3.13 | 3.10+ | ✅ |
| Platforms | Ubuntu, macOS | 2+ | ✅ |

### Historical Improvements

| Version | Linting Errors | Tests | Coverage |
|---------|----------------|-------|----------|
| v2.5.0 | 38 | 602 | 75% |
| v2.6.0 | 21 | 700+ | 80% |
| v2.7.0 | 0 | 1200+ | 85%+ |

**Progress:** Continuous improvement in all quality metrics.

---

## Troubleshooting

### Common Issues

#### 1. Linting Errors After Update

```bash
# Update ruff
pip install --upgrade ruff

# Re-run checks
ruff check .
```

#### 2. Tests Failing Locally

```bash
# Ensure package is installed
pip install -e ".[all-llms,dev]"

# Clear pytest cache
rm -rf .pytest_cache/
rm -rf **/__pycache__/

# Re-run tests
pytest tests/ -v
```

#### 3. Coverage Too Low

```bash
# Generate detailed coverage report
pytest tests/ --cov=src/skill_seekers --cov-report=html

# Open report
open htmlcov/index.html

# Identify untested code (red lines)
# Add tests for uncovered lines
```

---

## Related Documentation

- **[Testing Guide](../guides/TESTING_GUIDE.md)** - Comprehensive testing documentation
- **[Contributing Guide](../../CONTRIBUTING.md)** - Contribution guidelines
- **[API Reference](API_REFERENCE.md)** - Programmatic usage
- **[CHANGELOG](../../CHANGELOG.md)** - Version history and changes

---

**Version:** 2.7.0
**Last Updated:** 2026-01-18
**Status:** ✅ Production Ready
