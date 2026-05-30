# API 参考 - 程序化使用

**版本：** 3.6.0
**最后更新：** 2026-02-18
**状态：** ✅ 生产就绪

---

## 概述

Skill Seekers 可通过编程方式使用，以便集成到其他工具、自动化脚本和 CI/CD 流水线中。本指南面向希望将 Skill Seekers 功能嵌入到自有应用中的开发者，介绍所有可用的公共 API。

**使用场景：**
- CI/CD 中的自动化文档技能生成
- 批量处理多个文档源
- 自定义技能生成工作流
- 与内部工具集成
- 文档变更时自动更新技能

---

## 安装

### 基础安装

```bash
pip install skill-seekers
```

### 附带平台依赖

```bash
# Google Gemini 支持
pip install skill-seekers[gemini]

# OpenAI ChatGPT 支持
pip install skill-seekers[openai]

# 所有平台支持
pip install skill-seekers[all-llms]
```

### 开发安装

```bash
git clone https://github.com/yusufkaraaslan/Skill_Seekers.git
cd Skill_Seekers
pip install -e ".[all-llms]"
```

---

## 核心 API

### 1. 文档抓取 API

使用 BFS 遍历和智能分类从文档网站提取内容。

#### 基本用法

```python
from skill_seekers.cli.doc_scraper import scrape_all, build_skill
import json

# 加载配置
with open('configs/react.json', 'r') as f:
    config = json.load(f)

# 抓取文档
pages = scrape_all(
    base_url=config['base_url'],
    selectors=config['selectors'],
    config=config,
    output_dir='output/react_data'
)

print(f"Scraped {len(pages)} pages")

# 根据抓取的数据构建技能
skill_path = build_skill(
    config_name='react',
    output_dir='output/react',
    data_dir='output/react_data'
)

print(f"Skill created at: {skill_path}")
```

#### 高级抓取选项

```python
from skill_seekers.cli.doc_scraper import scrape_all

# 使用高级选项自定义抓取
pages = scrape_all(
    base_url='https://docs.example.com',
    selectors={
        'main_content': 'article',
        'title': 'h1',
        'code_blocks': 'pre code'
    },
    config={
        'name': 'my-framework',
        'description': 'Custom framework documentation',
        'rate_limit': 0.5,  # 请求间隔 0.5 秒
        'max_pages': 500,   # 限制为 500 页
        'url_patterns': {
            'include': ['/docs/'],
            'exclude': ['/blog/', '/changelog/']
        }
    },
    output_dir='output/my-framework_data',
    use_async=True  # 启用异步抓取（快 2-3 倍）
)
```

#### 不抓取直接重建

```python
from skill_seekers.cli.doc_scraper import build_skill

# 从现有数据重建技能（快！）
skill_path = build_skill(
    config_name='react',
    output_dir='output/react',
    data_dir='output/react_data',  # 使用已抓取的数据
    skip_scrape=True  # 不再重新抓取
)
```

---

### 2. GitHub 仓库分析 API

使用三流架构（代码 + 文档 + 洞察）分析 GitHub 仓库。

#### 基本 GitHub 分析

```python
from skill_seekers.cli.github_scraper import scrape_github_repo

# 分析 GitHub 仓库
result = scrape_github_repo(
    repo_url='https://github.com/facebook/react',
    output_dir='output/react-github',
    analysis_depth='c3x',  # 选项：'basic' 或 'c3x'
    github_token='ghp_...'  # 可选：更高的速率限制
)

print(f"Analysis complete: {result['skill_path']}")
print(f"Code files analyzed: {result['stats']['code_files']}")
print(f"Patterns detected: {result['stats']['patterns']}")
```

#### 特定流分析

```python
from skill_seekers.cli.github_scraper import scrape_github_repo

# 聚焦特定流
result = scrape_github_repo(
    repo_url='https://github.com/vercel/next.js',
    output_dir='output/nextjs',
    analysis_depth='c3x',
    enable_code_stream=True,      # C3.x 代码库分析
    enable_docs_stream=True,      # README、docs/、wiki
    enable_insights_stream=True,  # GitHub 元数据、issues
    include_tests=True,           # 提取测试示例
    include_patterns=True,        # 检测设计模式
    include_how_to_guides=True    # 从测试生成指南
)
```

---

### 3. PDF 提取 API

通过 OCR 和图像支持从 PDF 文档提取内容。

#### 基本 PDF 提取

```python
from skill_seekers.cli.pdf_scraper import scrape_pdf

# 从单个 PDF 提取
skill_path = scrape_pdf(
    pdf_path='documentation.pdf',
    output_dir='output/pdf-skill',
    skill_name='my-pdf-skill',
    description='Documentation from PDF'
)

print(f"PDF skill created: {skill_path}")
```

#### 高级 PDF 处理

```python
from skill_seekers.cli.pdf_scraper import scrape_pdf

# 使用全部功能提取 PDF
skill_path = scrape_pdf(
    pdf_path='large-manual.pdf',
    output_dir='output/manual',
    skill_name='product-manual',
    description='Product manual documentation',
    enable_ocr=True,              # 扫描版 PDF 的 OCR
    extract_images=True,          # 提取嵌入的图像
    extract_tables=True,          # 解析表格
    chunk_size=50,                # 每块页数（大 PDF）
    language='eng',               # OCR 语言
    dpi=300                       # OCR 图像 DPI
)
```

---

### 4. 统一多源抓取 API

将多个来源（文档 + GitHub + PDF）合并为单个统一技能。

#### 统一抓取

```python
from skill_seekers.cli.unified_scraper import unified_scrape

# 从多个来源抓取
result = unified_scrape(
    config_path='configs/unified/react-unified.json',
    output_dir='output/react-complete'
)

print(f"Unified skill created: {result['skill_path']}")
print(f"Sources merged: {result['sources']}")
print(f"Conflicts detected: {result['conflicts']}")
```

#### 冲突检测

```python
from skill_seekers.cli.unified_scraper import detect_conflicts

# 检测来源之间的差异
conflicts = detect_conflicts(
    docs_dir='output/react_data',
    github_dir='output/react-github',
    pdf_dir='output/react-pdf'
)

for conflict in conflicts:
    print(f"Conflict in {conflict['topic']}:")
    print(f"  Docs say: {conflict['docs_version']}")
    print(f"  Code shows: {conflict['code_version']}")
```

---

### 5. 技能打包 API

使用平台适配器架构为不同 LLM 平台打包技能。

#### 基础打包

```python
from skill_seekers.cli.adaptors import get_adaptor

# 获取平台特定适配器
adaptor = get_adaptor('claude')  # 选项：claude、gemini、openai、markdown

# 打包技能
package_path = adaptor.package(
    skill_dir='output/react/',
    output_path='output/'
)

print(f"Claude skill package: {package_path}")
```

#### 多平台打包

```python
from skill_seekers.cli.adaptors import get_adaptor

# 为所有平台打包
platforms = ['claude', 'gemini', 'openai', 'markdown']

for platform in platforms:
    adaptor = get_adaptor(platform)
    package_path = adaptor.package(
        skill_dir='output/react/',
        output_path='output/'
    )
    print(f"{platform.capitalize()} package: {package_path}")
```

#### 自定义打包选项

```python
from skill_seekers.cli.adaptors import get_adaptor

adaptor = get_adaptor('gemini')

# Gemini 特定打包（.tar.gz 格式）
package_path = adaptor.package(
    skill_dir='output/react/',
    output_path='output/',
    compress_level=9,  # 最大压缩
    include_metadata=True
)
```

---

### 6. 技能上传 API

通过各平台 API 将打包的技能上传到 LLM 平台。

#### Claude AI 上传

```python
import os
from skill_seekers.cli.adaptors import get_adaptor

adaptor = get_adaptor('claude')

# 上传到 Claude AI
result = adaptor.upload(
    package_path='output/react-claude.zip',
    api_key=os.getenv('ANTHROPIC_API_KEY')
)

print(f"Uploaded to Claude AI: {result['skill_id']}")
```

#### Google Gemini 上传

```python
import os
from skill_seekers.cli.adaptors import get_adaptor

adaptor = get_adaptor('gemini')

# 上传到 Google Gemini
result = adaptor.upload(
    package_path='output/react-gemini.tar.gz',
    api_key=os.getenv('GOOGLE_API_KEY')
)

print(f"Gemini corpus ID: {result['corpus_id']}")
```

#### OpenAI ChatGPT 上传

```python
import os
from skill_seekers.cli.adaptors import get_adaptor

adaptor = get_adaptor('openai')

# 上传到 OpenAI Vector Store
result = adaptor.upload(
    package_path='output/react-openai.zip',
    api_key=os.getenv('OPENAI_API_KEY')
)

print(f"Vector store ID: {result['vector_store_id']}")
```

---

### 7. AI 增强 API

使用平台特定模型通过 AI 驱动的改进来增强技能。

#### API 模式增强

```python
import os
from skill_seekers.cli.adaptors import get_adaptor

adaptor = get_adaptor('claude')

# 使用 Claude API 增强
result = adaptor.enhance(
    skill_dir='output/react/',
    mode='api',
    api_key=os.getenv('ANTHROPIC_API_KEY')
)

print(f"Enhanced skill: {result['enhanced_path']}")
print(f"Quality score: {result['quality_score']}/10")
```

#### LOCAL 模式增强

```python
from skill_seekers.cli.adaptors import get_adaptor

adaptor = get_adaptor('claude')

# 使用 Claude Code CLI 增强（免费！）
result = adaptor.enhance(
    skill_dir='output/react/',
    mode='LOCAL',
    execution_mode='headless',  # 选项：headless、background、daemon
    timeout=300  # 5 分钟超时
)

print(f"Enhanced skill: {result['enhanced_path']}")
```

#### 后台增强与监控

```python
from skill_seekers.cli.enhance_skill_local import enhance_skill
from skill_seekers.cli.enhance_status import monitor_enhancement
import time

# 启动后台增强
result = enhance_skill(
    skill_dir='output/react/',
    mode='background'
)

pid = result['pid']
print(f"Enhancement started in background (PID: {pid})")

# 监控进度
while True:
    status = monitor_enhancement('output/react/')
    print(f"Status: {status['state']}, Progress: {status['progress']}%")

    if status['state'] == 'completed':
        print(f"Enhanced skill: {status['output_path']}")
        break
    elif status['state'] == 'failed':
        print(f"Enhancement failed: {status['error']}")
        break

    time.sleep(5)  # 每 5 秒检查一次
```

---

### 8. 完整工作流自动化 API

自动化整个工作流：获取配置 → 抓取 → 增强 → 打包 → 上传。

#### 单命令安装

```python
import os
from skill_seekers.cli.install_skill import install_skill

# 完整工作流自动化
result = install_skill(
    config_name='react',  # 使用预设配置
    target='claude',      # 目标平台
    api_key=os.getenv('ANTHROPIC_API_KEY'),
    enhance=True,         # 启用 AI 增强
    upload=True,          # 上传到平台
    force=True            # 跳过确认
)

print(f"Skill installed: {result['skill_id']}")
print(f"Package path: {result['package_path']}")
print(f"Time taken: {result['duration']}s")
```

#### 自定义配置安装

```python
from skill_seekers.cli.install_skill import install_skill

# 使用自定义配置安装
result = install_skill(
    config_path='configs/custom/my-framework.json',
    target='gemini',
    api_key=os.getenv('GOOGLE_API_KEY'),
    enhance=True,
    upload=True,
    analysis_depth='c3x',  # 深度代码库分析
    enable_router=True     # 为大型文档生成路由器
)
```

---

## 配置对象

### 配置 Schema

Skill Seekers 使用 JSON 配置文件定义抓取行为。

```json
{
  "name": "framework-name",
  "description": "When to use this skill",
  "base_url": "https://docs.example.com/",
  "selectors": {
    "main_content": "article",
    "title": "h1",
    "code_blocks": "pre code",
    "navigation": "nav.sidebar"
  },
  "url_patterns": {
    "include": ["/docs/", "/api/", "/guides/"],
    "exclude": ["/blog/", "/changelog/", "/archive/"]
  },
  "categories": {
    "getting_started": ["intro", "quickstart", "installation"],
    "api": ["api", "reference", "methods"],
    "guides": ["guide", "tutorial", "how-to"],
    "examples": ["example", "demo", "sample"]
  },
  "rate_limit": 0.5,
  "max_pages": 500,
  "llms_txt_url": "https://example.com/llms.txt",
  "enable_async": true
}
```

### 必填字段

| 字段 | 类型 | 描述 |
|-------|------|-------------|
| `name` | string | 技能名称（字母数字 + 连字符） |
| `description` | string | 何时使用此技能 |
| `base_url` | string | 文档网站 URL |
| `selectors` | object | 用于内容提取的 CSS 选择器 |

### 可选字段

| 字段 | 类型 | 默认值 | 描述 |
|-------|------|---------|-------------|
| `url_patterns.include` | array | `[]` | 包含的 URL 路径模式 |
| `url_patterns.exclude` | array | `[]` | 排除的 URL 路径模式 |
| `categories` | object | `{}` | 类别关键词映射 |
| `rate_limit` | float | `0.5` | 请求间隔（秒） |
| `max_pages` | int | `500` | 最大抓取页数 |
| `llms_txt_url` | string | `null` | llms.txt 文件 URL |
| `enable_async` | bool | `false` | 启用异步抓取（更快） |

### 统一配置 Schema（多源）

```json
{
  "name": "framework-unified",
  "description": "Complete framework documentation",
  "sources": {
    "documentation": {
      "type": "docs",
      "base_url": "https://docs.example.com/",
      "selectors": { "main_content": "article" }
    },
    "github": {
      "type": "github",
      "repo_url": "https://github.com/org/repo",
      "analysis_depth": "c3x"
    },
    "pdf": {
      "type": "pdf",
      "pdf_path": "manual.pdf",
      "enable_ocr": true
    }
  },
  "conflict_resolution": "prefer_code",
  "merge_strategy": "smart"
}
```

---

## 高级选项

### 自定义选择器

```python
from skill_seekers.cli.doc_scraper import scrape_all

# 复杂站点的自定义 CSS 选择器
pages = scrape_all(
    base_url='https://complex-site.com',
    selectors={
        'main_content': 'div.content-wrapper > article',
        'title': 'h1.page-title',
        'code_blocks': 'pre.highlight code',
        'navigation': 'aside.sidebar nav',
        'metadata': 'meta[name="description"]'
    },
    config={'name': 'complex-site'}
)
```

### URL 模式匹配

```python
# 高级 URL 过滤
config = {
    'url_patterns': {
        'include': [
            '/docs/',           # 精确路径匹配
            '/api/**',          # 通配符：所有子路径
            '/guides/v2.*'      # 正则：特定版本
        ],
        'exclude': [
            '/blog/',
            '/changelog/',
            '**/*.png',         # 排除图像
            '**/*.pdf'          # 排除 PDF
        ]
    }
}
```

### 类别推断

```python
from skill_seekers.cli.doc_scraper import infer_categories

# 从 URL 结构自动检测类别
categories = infer_categories(
    pages=[
        {'url': 'https://docs.example.com/getting-started/intro'},
        {'url': 'https://docs.example.com/api/authentication'},
        {'url': 'https://docs.example.com/guides/tutorial'}
    ]
)

print(categories)
# Output: {
#   'getting-started': ['intro'],
#   'api': ['authentication'],
#   'guides': ['tutorial']
# }
```

---

## 错误处理

### 常见异常

```python
from skill_seekers.cli.doc_scraper import scrape_all
from skill_seekers.exceptions import (
    NetworkError,
    InvalidConfigError,
    ScrapingError,
    RateLimitError
)

try:
    pages = scrape_all(
        base_url='https://docs.example.com',
        selectors={'main_content': 'article'},
        config={'name': 'example'}
    )
except NetworkError as e:
    print(f"Network error: {e}")
    # 使用指数退避重试
except InvalidConfigError as e:
    print(f"Invalid config: {e}")
    # 修复配置后重试
except RateLimitError as e:
    print(f"Rate limited: {e}")
    # 在配置中增加 rate_limit
except ScrapingError as e:
    print(f"Scraping failed: {e}")
    # 检查选择器和 URL 模式
```

### 重试逻辑

```python
from skill_seekers.cli.doc_scraper import scrape_all
from skill_seekers.utils import retry_with_backoff

@retry_with_backoff(max_retries=3, base_delay=1.0)
def scrape_with_retry(base_url, config):
    return scrape_all(
        base_url=base_url,
        selectors=config['selectors'],
        config=config
    )

# 网络错误时自动重试
pages = scrape_with_retry(
    base_url='https://docs.example.com',
    config={'name': 'example', 'selectors': {...}}
)
```

---

## 测试你的集成

### 单元测试

```python
import pytest
from skill_seekers.cli.doc_scraper import scrape_all

def test_basic_scraping():
    """Test basic documentation scraping."""
    pages = scrape_all(
        base_url='https://docs.example.com',
        selectors={'main_content': 'article'},
        config={
            'name': 'test-framework',
            'max_pages': 10  # 测试时限制
        }
    )

    assert len(pages) > 0
    assert all('title' in p for p in pages)
    assert all('content' in p for p in pages)

def test_config_validation():
    """Test configuration validation."""
    from skill_seekers.cli.config_validator import validate_config

    config = {
        'name': 'test',
        'base_url': 'https://example.com',
        'selectors': {'main_content': 'article'}
    }

    is_valid, errors = validate_config(config)
    assert is_valid
    assert len(errors) == 0
```

### 集成测试

```python
import pytest
import os
from skill_seekers.cli.install_skill import install_skill

@pytest.mark.integration
def test_end_to_end_workflow():
    """Test complete skill installation workflow."""
    result = install_skill(
        config_name='react',
        target='markdown',  # markdown 不需要 API key
        enhance=False,      # 跳过 AI 增强
        upload=False,       # 不上传
        force=True
    )

    assert result['success']
    assert os.path.exists(result['package_path'])
    assert result['package_path'].endswith('.zip')

@pytest.mark.integration
def test_multi_platform_packaging():
    """Test packaging for multiple platforms."""
    from skill_seekers.cli.adaptors import get_adaptor

    platforms = ['claude', 'gemini', 'openai', 'markdown']

    for platform in platforms:
        adaptor = get_adaptor(platform)
        package_path = adaptor.package(
            skill_dir='output/test-skill/',
            output_path='output/'
        )
        assert os.path.exists(package_path)
```

---

## 性能优化

### 异步抓取

```python
from skill_seekers.cli.doc_scraper import scrape_all

# 启用异步可获得 2-3 倍速度提升
pages = scrape_all(
    base_url='https://docs.example.com',
    selectors={'main_content': 'article'},
    config={'name': 'example'},
    use_async=True  # 快 2-3 倍
)
```

### 缓存与重建

```python
from skill_seekers.cli.doc_scraper import build_skill

# 首次抓取（慢 - 15-45 分钟）
build_skill(config_name='react', output_dir='output/react')

# 不重新抓取直接重建（快 - <1 分钟）
build_skill(
    config_name='react',
    output_dir='output/react',
    data_dir='output/react_data',
    skip_scrape=True  # 使用缓存数据
)
```

### 批量处理

```python
from concurrent.futures import ThreadPoolExecutor
from skill_seekers.cli.install_skill import install_skill

configs = ['react', 'vue', 'angular', 'svelte']

def install_config(config_name):
    return install_skill(
        config_name=config_name,
        target='markdown',
        enhance=False,
        upload=False,
        force=True
    )

# 并行处理 4 个配置
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(install_config, configs))

for config, result in zip(configs, results):
    print(f"{config}: {result['success']}")
```

---

## CI/CD 集成示例

### GitHub Actions

```yaml
name: Generate Skills

on:
  schedule:
    - cron: '0 0 * * *'  # 每天午夜
  workflow_dispatch:

jobs:
  generate-skills:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Skill Seekers
        run: pip install skill-seekers[all-llms]

      - name: Generate Skills
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: |
          skill-seekers install react --target claude --enhance --upload
          skill-seekers install vue --target gemini --enhance --upload

      - name: Archive Skills
        uses: actions/upload-artifact@v3
        with:
          name: skills
          path: output/**/*.zip
```

### GitLab CI

```yaml
generate_skills:
  image: python:3.11
  script:
    - pip install skill-seekers[all-llms]
    - skill-seekers install react --target claude --enhance --upload
    - skill-seekers install vue --target gemini --enhance --upload
  artifacts:
    paths:
      - output/
  only:
    - schedules
```

---

## 最佳实践

### 1. **使用配置文件**
将配置放入版本控制以确保可复现性：
```python
import json
with open('configs/my-framework.json') as f:
    config = json.load(f)
scrape_all(config=config)
```

### 2. **为大型站点启用异步**
```python
pages = scrape_all(base_url=url, config=config, use_async=True)
```

### 3. **缓存抓取的数据**
```python
# 抓取一次
scrape_all(config=config, output_dir='output/data')

# 多次重建（快！）
build_skill(config_name='framework', data_dir='output/data', skip_scrape=True)
```

### 4. **使用平台适配器**
```python
# 良好：与平台无关
adaptor = get_adaptor(target_platform)
adaptor.package(skill_dir)

# 不佳：硬编码单个平台
# create_zip_for_claude(skill_dir)
```

### 5. **优雅地处理错误**
```python
try:
    result = install_skill(config_name='framework', target='claude')
except NetworkError:
    # 重试逻辑
except InvalidConfigError:
    # 修复配置
```

### 6. **监控后台增强**
```python
# 启动增强
enhance_skill(skill_dir='output/react/', mode='background')

# 监控进度
monitor_enhancement('output/react/', watch=True)
```

---

## API 参考摘要

| API | 模块 | 使用场景 |
|-----|--------|----------|
| **文档抓取** | `doc_scraper` | 从文档网站提取 |
| **GitHub 分析** | `github_scraper` | 分析代码仓库 |
| **PDF 提取** | `pdf_scraper` | 从 PDF 文件提取 |
| **统一抓取** | `unified_scraper` | 多源抓取 |
| **技能打包** | `adaptors` | 为 LLM 平台打包 |
| **技能上传** | `adaptors` | 上传到平台 |
| **AI 增强** | `adaptors` | 提升技能质量 |
| **完整工作流** | `install_skill` | 端到端自动化 |

---

## 其他资源

- **[主文档](../../README.md)** - 完整用户指南
- **[使用指南](../guides/USAGE.md)** - CLI 使用示例
- **[MCP 设置](../guides/MCP_SETUP.md)** - MCP 服务器集成
- **[多 LLM 支持](../integrations/MULTI_LLM_SUPPORT.md)** - 平台对比
- **[CHANGELOG](../../CHANGELOG.md)** - 版本历史和 API 变更

---

**版本：** 3.6.0
**最后更新：** 2026-02-18
**状态：** ✅ 生产就绪
