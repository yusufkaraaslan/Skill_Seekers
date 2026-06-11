# 代码质量标准

**版本：** 3.6.0
**最后更新：** 2026-02-18
**状态：** ✅ 生产就绪

---

## 概述

Skill Seekers 通过自动化 lint 检查、全面的测试和持续集成来保持高代码质量。本文档概述了用于确保可靠性和可维护性的质量标准、工具和流程。

**质量支柱：**
1. **Lint 检查** - 使用 Ruff 进行自动化代码风格和错误检测
2. **测试** - 全面的测试覆盖（1,880+ 测试）
3. **类型安全** - 类型提示与验证
4. **安全** - 使用 Bandit 进行安全扫描
5. **CI/CD** - 每次提交的自动化验证

---

## 使用 Ruff 进行 Lint 检查

### 什么是 Ruff？

**Ruff** 是一个用 Rust 编写的极速 Python linter，集成了多个工具的功能：
- Flake8（风格检查）
- isort（导入排序）
- Black（代码格式化）
- pyupgrade（Python 版本升级）
- 以及 100+ 其他 lint 规则

**为什么选择 Ruff：**
- ⚡ 比传统 linter 快 10-100 倍
- 🔧 大多数问题可自动修复
- 📦 一个工具替代 10+ 个传统工具
- 🎯 全面的规则覆盖

### 安装

```bash
# Using uv (recommended)
uv pip install ruff

# Using pip
pip install ruff

# Development installation
pip install -e ".[dev]"  # Includes ruff
```

### 运行 Ruff

#### 检查问题

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

#### 格式化代码

```bash
# Check formatting (dry run)
ruff format --check .

# Apply formatting
ruff format .

# Format specific file
ruff format src/skill_seekers/cli/doc_scraper.py
```

### 配置

Ruff 配置位于 `pyproject.toml`：

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

## 常见 Ruff 规则

### SIM102：简化嵌套 If 语句

**修改前：**
```python
if condition1:
    if condition2:
        do_something()
```

**修改后：**
```python
if condition1 and condition2:
    do_something()
```

**原因：** 提高可读性，减少嵌套层级。

### SIM117：合并多个 With 语句

**修改前：**
```python
with open('file1.txt') as f1:
    with open('file2.txt') as f2:
        process(f1, f2)
```

**修改后：**
```python
with open('file1.txt') as f1, open('file2.txt') as f2:
    process(f1, f2)
```

**原因：** 语法更简洁，资源管理更好。

### B904：正确的异常链

**修改前：**
```python
try:
    risky_operation()
except Exception:
    raise CustomError("Failed")
```

**修改后：**
```python
try:
    risky_operation()
except Exception as e:
    raise CustomError("Failed") from e
```

**原因：** 保留错误上下文，便于调试。

### SIM113：移除未使用的 Enumerate 计数器

**修改前：**
```python
for i, item in enumerate(items):
    process(item)  # i is never used
```

**修改后：**
```python
for item in items:
    process(item)
```

**原因：** 意图更清晰，移除未使用的变量。

### B007：未使用的循环变量

**修改前：**
```python
for item in items:
    total += 1  # item is never used
```

**修改后：**
```python
for _ in items:
    total += 1
```

**原因：** 明确表示循环变量是有意不使用的。

### ARG002：未使用的方法参数

**修改前：**
```python
def process(self, data, unused_arg):
    return data.transform()  # unused_arg never used
```

**修改后：**
```python
def process(self, data):
    return data.transform()
```

**原因：** 移除死代码，使函数签名更清晰。

---

## 近期代码质量改进

### v3.6.0 修复（2026 年 1 月 18 日）

修复了代码库中**全部 21 个 ruff lint 错误**：

| 规则 | 数量 | 受影响文件 | 影响 |
|------|------|-----------|------|
| SIM102 | 7 | config_extractor.py、pattern_recognizer.py（3 处） | 合并嵌套 if 语句 |
| SIM117 | 9 | test_example_extractor.py（3 处）、unified_skill_builder.py | 合并 with 语句 |
| B904 | 1 | pdf_scraper.py | 添加异常链 |
| SIM113 | 1 | config_validator.py | 移除未使用的 enumerate 计数器 |
| B007 | 1 | doc_scraper.py | 将未使用的循环变量改为 _ |
| ARG002 | 1 | 测试 fixture | 移除未使用的测试参数 |
| **总计** | **21** | **12 个文件** | **零 lint 错误** |

**结果：** 代码库干净无 lint 错误，可维护性提升。

### 已更新的文件

1. **src/skill_seekers/cli/config_extractor.py**（SIM102 修复）
2. **src/skill_seekers/cli/config_validator.py**（SIM113 修复）
3. **src/skill_seekers/cli/doc_scraper.py**（B007 修复）
4. **src/skill_seekers/cli/pattern_recognizer.py**（3 处 SIM102 修复）
5. **src/skill_seekers/cli/test_example_extractor.py**（3 处 SIM117 修复）
6. **src/skill_seekers/cli/unified_skill_builder.py**（SIM117 修复）
7. **src/skill_seekers/cli/pdf_scraper.py**（B904 修复）
8. **6 个测试文件**（各类修复）

---

## 测试要求

### 测试覆盖标准

**关键路径：** 要求 100% 覆盖
- 核心抓取逻辑
- 平台适配器
- MCP 工具实现
- 配置验证

**整体项目：** 覆盖率目标 >80%

**当前状态：**
- ✅ 1,880+ 测试通过
- ✅ 代码覆盖率 >85%
- ✅ 所有关键路径已覆盖
- ✅ 已集成 CI/CD

### 运行测试

#### 全部测试

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/skill_seekers --cov-report=term --cov-report=html

# View HTML coverage report
open htmlcov/index.html
```

#### 特定测试类别

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

#### 测试标记

```bash
# Slow tests (skip by default)
pytest tests/ -m "not slow"

# Run slow tests
pytest tests/ -m slow

# Async tests
pytest tests/ -m asyncio
```

### 测试类别

1. **单元测试**（800+ 测试）
   - 单个函数测试
   - 隔离的组件测试
   - 模拟外部依赖

2. **集成测试**（300+ 测试）
   - 多组件工作流
   - 端到端功能测试
   - 真实文件系统操作

3. **E2E 测试**（100+ 测试）
   - 完整用户工作流
   - CLI 命令测试
   - 平台集成测试

4. **MCP 测试**（63 个测试）
   - 全部 40 个 MCP 工具
   - 传输模式测试（stdio、HTTP）
   - 错误处理验证

### 提交前的测试要求

**根据 `~/.claude/CLAUDE.md` 中的用户指令：**

> "never skip any test. always make sure all test pass"

**这意味着：**
- ✅ 提交前**全部 1,880+ 测试必须通过**
- ✅ 不跳过任何测试，即使它们很慢
- ✅ 为新功能添加测试
- ✅ 立即修复失败的测试
- ✅ 保持或提升覆盖率

---

## CI/CD 集成

### GitHub Actions 工作流

Skill Seekers 使用 GitHub Actions 对每次提交和 PR 进行自动化质量检查。

#### 工作流配置

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

### CI 检查

每次提交和 PR 必须通过：

1. **Ruff Lint 检查** - 零 lint 错误
2. **Ruff 格式检查** - 一致的代码风格
3. **Pytest** - 全部 1,880+ 测试通过
4. **覆盖率** - 代码覆盖率 >80%
5. **多平台** - Ubuntu + macOS
6. **多版本** - Python 3.10-3.13

**状态：** ✅ 所有检查通过

---

## Pre-commit 钩子

### 设置

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

### 配置

创建 `.pre-commit-config.yaml`：

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

### 使用

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

## 最佳实践

### 代码组织

#### 导入顺序

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

**工具：** Ruff 通过 `I` 规则自动排序导入。

#### 命名约定

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

### 文档

#### 文档字符串

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

#### 类型提示

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

### 错误处理

#### 异常模式

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

#### 日志记录

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

## 安全扫描

### Bandit

Bandit 扫描 Python 代码中的安全漏洞。

#### 安装

```bash
pip install bandit
```

#### 运行 Bandit

```bash
# Scan all Python files
bandit -r src/

# Scan with config
bandit -r src/ -c pyproject.toml

# Generate JSON report
bandit -r src/ -f json -o bandit-report.json
```

#### 常见安全问题

**B404：导入 subprocess 模块**
```python
# Review: Ensure safe usage of subprocess
import subprocess

# ✅ Safe: Using subprocess with shell=False and list arguments
subprocess.run(['ls', '-l'], shell=False)

# ❌ UNSAFE: Using shell=True with user input (NEVER DO THIS)
# This is an example of what NOT to do - security vulnerability!
# subprocess.run(f'ls {user_input}', shell=True)
```

**B605：通过 shell 启动进程**
```python
# ❌ UNSAFE: Shell injection risk (NEVER DO THIS)
# Example of security anti-pattern:
# import os
# os.system(f'rm {filename}')

# ✅ Safe: Use subprocess with list arguments
import subprocess
subprocess.run(['rm', filename], shell=False)
```

**安全最佳实践：**
- 切勿对用户输入使用 `shell=True`
- 始终验证和清理用户输入
- 使用带列表参数的 subprocess 而不是 shell 命令
- 避免动态构造命令

---

## 开发工作流

### 1. 开始工作前

```bash
# Pull latest changes
git checkout development
git pull origin development

# Create feature branch
git checkout -b feature/your-feature

# Install dependencies
pip install -e ".[all-llms,dev]"
```

### 2. 开发过程中

```bash
# Run linter frequently
ruff check src/skill_seekers/cli/your_file.py --fix

# Run relevant tests
pytest tests/test_your_feature.py -v

# Check formatting
ruff format src/skill_seekers/cli/your_file.py
```

### 3. 提交前

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

### 4. 提交更改

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

### 5. 创建 Pull Request

```bash
# Create PR via GitHub CLI
gh pr create --title "Add your feature" --body "Description..."

# CI checks will run automatically:
# ✅ Ruff linting
# ✅ Ruff formatting
# ✅ Pytest (1,880+ tests)
# ✅ Coverage report
# ✅ Multi-platform (Ubuntu + macOS)
# ✅ Multi-version (Python 3.10-3.13)
```

---

## 质量指标

### 当前状态（v3.6.0）

| 指标 | 数值 | 目标 | 状态 |
|------|------|------|------|
| Lint 错误 | 0 | 0 | ✅ |
| 测试数量 | 1200+ | 1000+ | ✅ |
| 测试通过率 | 100% | 100% | ✅ |
| 代码覆盖率 | >85% | >80% | ✅ |
| CI 通过率 | 100% | >95% | ✅ |
| Python 版本 | 3.10-3.13 | 3.10+ | ✅ |
| 平台 | Ubuntu、macOS | 2+ | ✅ |

### 历史改进

| 版本 | Lint 错误 | 测试 | 覆盖率 |
|------|----------|------|--------|
| v2.5.0 | 38 | 602 | 75% |
| v2.6.0 | 21 | 700+ | 80% |
| v2.7.0 | 0 | 1200+ | 85%+ |

**进展：** 所有质量指标持续改进。

---

## 故障排除

### 常见问题

#### 1. 更新后出现 Lint 错误

```bash
# Update ruff
pip install --upgrade ruff

# Re-run checks
ruff check .
```

#### 2. 本地测试失败

```bash
# Ensure package is installed
pip install -e ".[all-llms,dev]"

# Clear pytest cache
rm -rf .pytest_cache/
rm -rf **/__pycache__/

# Re-run tests
pytest tests/ -v
```

#### 3. 覆盖率过低

```bash
# Generate detailed coverage report
pytest tests/ --cov=src/skill_seekers --cov-report=html

# Open report
open htmlcov/index.html

# Identify untested code (red lines)
# Add tests for uncovered lines
```

---

## 相关文档

- **[测试指南](../guides/TESTING_GUIDE.md)** - 全面的测试文档
- **[贡献指南](../../CONTRIBUTING.md)** - 贡献准则
- **[API 参考](API_REFERENCE.md)** - 编程方式使用
- **[CHANGELOG](../../CHANGELOG.md)** - 版本历史与变更

---

**版本：** 3.6.0
**最后更新：** 2026-02-18
**状态：** ✅ 生产就绪
