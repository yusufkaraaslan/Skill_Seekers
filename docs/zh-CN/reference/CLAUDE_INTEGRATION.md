# CLAUDE.md

本文件为 Claude Code（claude.ai/code）在此仓库中处理代码时提供指导。

## 🎯 当前状态（2026 年 1 月 8 日）

**版本：** v3.6.0
**状态：** 生产就绪

### 近期更新（2026 年 1 月）：

**🚀 重大版本：三流 GitHub 架构（v2.6.0）**
- **✅ 阶段 1-5 已完成**（26 小时实现，81 个测试通过）
- **新增：GitHub 三流获取器** - 将仓库拆分为代码、文档、洞察三个流
- **新增：统一代码库分析器** - 支持 GitHub URL + 本地路径，C3.x 作为分析深度
- **增强：来源合并** - 与 GitHub 文档和洞察的多层合并
- **增强：路由器生成** - GitHub 元数据、README 快速开始、常见问题
- **关键修复：真正的 C3.x 集成** - 真实的模式检测（不再是占位符）
- **质量指标**：GitHub 开销 20-60 行，路由器大小 60-250 行
- **文档**：完整的实现总结和 E2E 测试

### 近期更新（2025 年 12 月）：

**🎉 重大版本：多平台功能对等！（v2.5.0）**
- **🌐 多 LLM 支持**：完整支持 21 个平台 - Claude AI、Google Gemini、OpenAI ChatGPT、MiniMax AI、OpenCode、Kimi、DeepSeek、Qwen、OpenRouter、Together AI、Fireworks AI、IBM Bob、LangChain、LlamaIndex、Haystack、Pinecone、Weaviate、Chroma、FAISS、Qdrant 以及通用 Markdown
- **🔄 完整功能对等**：所有技能模式适用于所有平台
- **🏗️ 平台适配器**：采用平台特定实现的清晰架构
- **✨ 40 个 MCP 工具**：增强的多平台支持（打包、上传、增强）
- **📚 全面的文档**：所有平台的完整指南
- **🧪 测试覆盖**：1,880+ 测试通过，广泛的平台兼容性测试

**🚀 新增：三流 GitHub 架构（v2.6.0）**
- **📊 三流获取器**：将 GitHub 仓库拆分为代码、文档和洞察流
- **🔬 统一代码库分析器**：支持 GitHub URL 和本地路径
- **🎯 增强的路由器生成**：GitHub 洞察 + C3.x 模式，实现更好的路由
- **📝 GitHub Issue 集成**：子技能中包含常见问题和解决方案
- **✅ 81 个测试通过**：全面的 E2E 验证（0.43 秒）

## 三流 GitHub 架构

**v2.6.0 新增**：现在使用三流架构分析 GitHub 仓库：

**流 1：代码**（用于 C3.x 分析）
- 文件：`*.py, *.js, *.ts, *.go, *.rs, *.java, etc.`
- 用途：使用 C3.x 组件进行深度代码分析
- 耗时：20-60 分钟
- 组件：模式（C3.1）、示例（C3.2）、指南（C3.3）、配置（C3.4）、架构（C3.7）

**流 2：文档**（来自仓库）
- 文件：`README.md, CONTRIBUTING.md, docs/*.md`
- 用途：快速开始指南和官方文档
- 耗时：1-2 分钟

**流 3：GitHub 洞察**（元数据与社区）
- 数据：开放 issue、已关闭 issue、标签、star、fork
- 用途：真实的用户问题和已知解决方案
- 耗时：1-2 分钟

### 使用示例

```python
from skill_seekers.cli.unified_codebase_analyzer import UnifiedCodebaseAnalyzer

# Analyze GitHub repo with three streams
analyzer = UnifiedCodebaseAnalyzer()
result = analyzer.analyze(
    source="https://github.com/facebook/react",
    depth="c3x",  # or "basic"
    fetch_github_metadata=True
)

# Access all three streams
print(f"Files: {len(result.code_analysis['files'])}")
print(f"README: {result.github_docs['readme'][:100]}")
print(f"Stars: {result.github_insights['metadata']['stars']}")
print(f"C3.x Patterns: {len(result.code_analysis['c3_1_patterns'])}")
```

### 使用 GitHub 生成路由器

```python
from skill_seekers.cli.generate_router import RouterGenerator
from skill_seekers.cli.github_fetcher import GitHubThreeStreamFetcher

# Fetch GitHub repo with three streams
fetcher = GitHubThreeStreamFetcher("https://github.com/jlowin/fastmcp")
three_streams = fetcher.fetch()

# Generate router with GitHub integration
generator = RouterGenerator(
    ['configs/fastmcp-oauth.json', 'configs/fastmcp-async.json'],
    github_streams=three_streams
)

# Result includes:
# - Repository stats (stars, language)
# - README quick start
# - Common issues from GitHub
# - Enhanced routing keywords (GitHub labels with 2x weight)
skill_md = generator.generate_skill_md()
```

**完整文档请参阅**：[三流实现总结](IMPLEMENTATION_SUMMARY_THREE_STREAM.md)

## 概述

这是一个基于 Python 的文档抓取工具，可将任何文档网站转换为 Claude 技能。它是一个单文件工具（`doc_scraper.py`），能够抓取文档、提取代码模式、检测编程语言，并生成可直接用于 Claude 的结构化技能文件。

## 依赖项

```bash
pip3 install requests beautifulsoup4
```

## 核心命令

### 使用预设配置运行
```bash
skill-seekers create --config configs/godot.json
skill-seekers create --config configs/react.json
skill-seekers create --config configs/vue.json
skill-seekers create --config configs/django.json
skill-seekers create --config configs/fastapi.json
```

### 交互模式（用于新框架）
```bash
skill-seekers create --interactive
```

### 快速模式（最小配置）
```bash
skill-seekers create --name react --url https://react.dev/ --description "React framework"
```

### 跳过抓取（使用缓存数据）
```bash
skill-seekers create --config configs/godot.json --skip-scrape
```

### 恢复中断的抓取
```bash
# If scrape was interrupted
skill-seekers create --config configs/godot.json --resume

# Start fresh (clear checkpoint)
skill-seekers create --config configs/godot.json --fresh
```

### 大型文档（10K-40K+ 页面）
```bash
# 1. Estimate page count
skill-seekers estimate configs/godot.json

# 2. Split into focused sub-skills
python -m skill_seekers.cli.split_config configs/godot.json --strategy router

# 3. Generate router skill
skill-seekers create configs/godot-*.json

# 4. Package multiple skills
skill-seekers package output/godot*/
```

### AI 驱动的 SKILL.md 增强
```bash
# Option 1: During scraping (API-based when ANTHROPIC_API_KEY is set)
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers create --config configs/react.json --enhance-level 2

# Option 2: During scraping (LOCAL, no API key - uses Claude Code Max)
skill-seekers create --config configs/react.json --enhance-level 2 --agent claude

# Option 3: Standalone after scraping (API-based)
skill-seekers enhance output/react/

# Option 4: Standalone after scraping (LOCAL, no API key)
skill-seekers enhance output/react/
```

LOCAL 增强选项（`--enhance-local` 或 `enhance_skill_local.py`）会打开一个运行 Claude Code 的新终端，自动分析参考文件并增强 SKILL.md。这需要 Claude Code Max 计划，但无需 API 密钥。

### MCP 集成（Claude Code）
```bash
# One-time setup
./setup_mcp.sh

# Then in Claude Code, use natural language:
"List all available configs"
"Generate config for Tailwind at https://tailwindcss.com/docs"
"Split configs/godot.json using router strategy"
"Generate router for configs/godot-*.json"
"Package skill at output/react/"
```

提供 40 个支持多平台的 MCP 工具：list_configs、generate_config、validate_config、fetch_config、estimate_pages、scrape_docs、scrape_github、scrape_pdf、package_skill、upload_skill、enhance_skill（新增）、install_skill、split_config、generate_router、add_config_source、list_config_sources、remove_config_source、submit_config

### 使用有限页面测试（先编辑配置）
在配置文件中设置 `"max_pages": 20` 以使用较少的页面进行测试。

## 多平台支持（v2.5.0+）

**4 个平台获得完整支持：**
- **Claude AI**（默认）- ZIP 格式、Skills API、MCP 集成
- **Google Gemini** - tar.gz 格式、Files API、1M token 上下文
- **OpenAI ChatGPT** - ZIP 格式、Assistants API、Vector Store
- **通用 Markdown** - ZIP 格式、通用兼容性

**所有技能模式适用于所有平台：**
- 文档抓取
- GitHub 仓库分析
- PDF 提取
- 统一多源
- 本地仓库分析

**打包、上传和增强时使用 `--target` 参数：**
```bash
# Package for different platforms
skill-seekers package output/react/ --target claude     # Default
skill-seekers package output/react/ --target gemini
skill-seekers package output/react/ --target openai
skill-seekers package output/react/ --target markdown

# Upload to platforms (requires API keys)
skill-seekers upload output/react.zip --target claude
skill-seekers upload output/react-gemini.tar.gz --target gemini
skill-seekers upload output/react-openai.zip --target openai

# Enhance with platform-specific AI
skill-seekers enhance output/react/ --target claude     # Sonnet 4
skill-seekers enhance output/react/ --target gemini     # Gemini 2.0
skill-seekers enhance output/react/ --target openai     # GPT-4o
```

完整详情请参阅[多平台指南](UPLOAD_GUIDE.md)和[功能矩阵](FEATURE_MATRIX.md)。

## 架构

### 单文件设计
整个工具包含在 `doc_scraper.py` 中（约 737 行）。它采用基于类的架构，由单个 `DocToSkillConverter` 类处理：
- **网页抓取**：带 URL 验证的 BFS 遍历
- **内容提取**：用于标题、内容、代码块的 CSS 选择器
- **语言检测**：基于启发式规则从代码示例中检测（Python、JavaScript、GDScript、C++ 等）
- **模式提取**：从文档中识别常见编码模式
- **分类**：使用 URL 结构、页面标题和内容关键词进行带评分的智能分类
- **技能生成**：创建包含真实代码示例和分类参考文件的 SKILL.md

### 数据流
1. **抓取阶段**：
   - 输入：配置 JSON（name、base_url、selectors、url_patterns、categories、rate_limit、max_pages）
   - 处理：从 base_url 开始的 BFS 遍历，遵循 include/exclude 模式
   - 输出：`output/{name}_data/pages/*.json` + `summary.json`

2. **构建阶段**：
   - 输入：来自 `output/{name}_data/` 的已抓取 JSON 数据
   - 处理：加载页面 → 智能分类 → 提取模式 → 生成参考文件
   - 输出：`output/{name}/SKILL.md` + `output/{name}/references/*.md`

### 目录结构
```
Skill_Seekers/
├── cli/                        # CLI tools
│   ├── doc_scraper.py         # Main scraping & building tool
│   ├── enhance_skill.py       # AI enhancement (API-based)
│   ├── enhance_skill_local.py # AI enhancement (LOCAL, no API)
│   ├── estimate_pages.py      # Page count estimator
│   ├── split_config.py        # Large docs splitter (NEW)
│   ├── generate_router.py     # Router skill generator (NEW)
│   ├── package_skill.py       # Single skill packager
│   └── package_multi.py       # Multi-skill packager (NEW)
├── mcp/                        # MCP server
│   ├── server.py              # 9 MCP tools (includes upload)
│   └── README.md
├── configs/                    # Preset configurations
│   ├── godot.json
│   ├── godot-large-example.json  # Large docs example (NEW)
│   ├── react.json
│   └── ...
├── docs/                       # Documentation
│   ├── CLAUDE.md              # Technical architecture (this file)
│   ├── LARGE_DOCUMENTATION.md # Large docs guide (NEW)
│   ├── ENHANCEMENT.md
│   ├── MCP_SETUP.md
│   └── ...
└── output/                     # Generated output (git-ignored)
    ├── {name}_data/           # Raw scraped data (cached)
    │   ├── pages/             # Individual page JSONs
    │   ├── summary.json       # Scraping summary
    │   └── checkpoint.json    # Resume checkpoint (NEW)
    └── {name}/                # Generated skill
        ├── SKILL.md           # Main skill file with examples
        ├── SKILL.md.backup    # Backup (if enhanced)
        ├── references/        # Categorized documentation
        │   ├── index.md
        │   ├── getting_started.md
        │   ├── api.md
        │   └── ...
        ├── scripts/           # Empty (for user scripts)
        └── assets/            # Empty (for user assets)
```

### 配置格式
`configs/*.json` 中的配置文件包含：
- `name`：技能标识符（例如 "godot"、"react"）
- `description`：何时使用此技能
- `base_url`：抓取的起始 URL
- `selectors`：用于内容提取的 CSS 选择器
  - `main_content`：主要文档内容（例如 "article"、"div[role='main']"）
  - `title`：页面标题选择器
  - `code_blocks`：代码示例选择器（例如 "pre code"、"pre"）
- `url_patterns`：URL 过滤
  - `include`：仅抓取包含这些模式的 URL
  - `exclude`：跳过包含这些模式的 URL
- `categories`：基于关键词的分类映射
- `rate_limit`：请求之间的延迟（秒）
- `max_pages`：最大抓取页数
- `split_strategy`：（可选）拆分大型文档的方式："auto"、"category"、"router"、"size"
- `split_config`：（可选）拆分配置
  - `target_pages_per_skill`：每个子技能的页数（默认：5000）
  - `create_router`：创建路由器/枢纽技能（默认：true）
  - `split_by_categories`：用于拆分的类别名称
- `checkpoint`：（可选）检查点/恢复配置
  - `enabled`：启用检查点（默认：false）
  - `interval`：每 N 页保存一次（默认：1000）

### 关键特性

**自动检测现有数据**：工具会检查 `output/{name}_data/` 并提示是否复用，避免重新抓取。

**语言检测**：通过以下方式检测代码语言：
1. CSS class 属性（`language-*`、`lang-*`）
2. 启发式规则（`def`、`const`、`func` 等关键词）

**模式提取**：在内容中查找 "Example:"、"Pattern:"、"Usage:" 标记并提取其后的代码块（每页最多 5 个）。

**智能分类**：
- 根据类别关键词为页面评分（URL 匹配 3 分、标题 2 分、内容 1 分）
- 达到 2 分及以上才进行分类
- 如果未提供类别，则从 URL 片段自动推断
- 回退到 "other" 类别

**增强版 SKILL.md**：生成内容包括：
- 来自文档的真实代码示例（带语言注解）
- 从文档中提取的快速参考模式
- 常见模式部分
- 类别文件列表

**AI 驱动的增强**：两个脚本可显著提升 SKILL.md 质量：
- `enhance_skill.py`：使用 Anthropic API（每个技能约 $0.15-$0.30，需要 API 密钥）
- `enhance_skill_local.py`：使用 Claude Code Max（免费，无需 API 密钥）
- 将 75 行的通用模板转化为 500+ 行的全面指南
- 提取最佳示例、解释关键概念、添加导航指导
- 成功率：9/10 质量（基于 steam-economy 测试）

**大型文档支持（新增）**：处理 10K-40K+ 页面的文档：
- `split_config.py`：将大型配置拆分为多个聚焦的子技能
- `generate_router.py`：创建智能路由器/枢纽技能来引导查询
- `package_multi.py`：一次打包多个技能
- 4 种拆分策略：auto、category、router、size
- 支持并行抓取以加快处理速度
- MCP 集成，支持自然语言使用

**检查点/恢复（新增）**：长时间抓取永不丢失进度：
- 每 N 页自动保存（可配置，默认：1000）
- 使用 `--resume` 标志恢复
- 使用 `--fresh` 标志清除检查点
- 中断时保存（Ctrl+C）

## 关键代码位置

- **URL 验证**：`is_valid_url()` doc_scraper.py:47-62
- **内容提取**：`extract_content()` doc_scraper.py:64-131
- **语言检测**：`detect_language()` doc_scraper.py:133-163
- **模式提取**：`extract_patterns()` doc_scraper.py:165-181
- **智能分类**：`smart_categorize()` doc_scraper.py:280-321
- **类别推断**：`infer_categories()` doc_scraper.py:323-349
- **快速参考生成**：`generate_quick_reference()` doc_scraper.py:351-370
- **SKILL.md 生成**：`create_enhanced_skill_md()` doc_scraper.py:424-540
- **抓取循环**：`scrape_all()` doc_scraper.py:226-249
- **主工作流**：`main()` doc_scraper.py:661-733

## 工作流示例

### 首次抓取（包含抓取）
```bash
# 1. Scrape + Build
skill-seekers create --config configs/godot.json
# Time: 20-40 minutes

# 2. Package
skill-seekers package output/godot/

# Result: godot.zip
```

### 使用缓存数据（快速迭代）
```bash
# 1. Use existing data
skill-seekers create --config configs/godot.json --skip-scrape
# Time: 1-3 minutes

# 2. Package
skill-seekers package output/godot/
```

### 为新框架创建配置
```bash
# Option 1: Interactive
skill-seekers create --interactive

# Option 2: Copy and modify
cp configs/react.json configs/myframework.json
# Edit configs/myframework.json
skill-seekers create --config configs/myframework.json
```

### 大型文档工作流（40K 页面）
```bash
# 1. Estimate page count (fast, 1-2 minutes)
skill-seekers estimate configs/godot.json

# 2. Split into focused sub-skills
python -m skill_seekers.cli.split_config configs/godot.json --strategy router --target-pages 5000

# Creates: godot-scripting.json, godot-2d.json, godot-3d.json, etc.

# 3. Scrape all in parallel (4-8 hours instead of 20-40!)
for config in configs/godot-*.json; do
  skill-seekers create --config $config &
done
wait

# 4. Generate intelligent router skill
skill-seekers create configs/godot-*.json

# 5. Package all skills
skill-seekers package output/godot*/

# 6. Upload all .zip files to Claude
# Result: Router automatically directs queries to the right sub-skill!
```

**时间节省：** 并行抓取将 20-40 小时缩短至 4-8 小时

**完整指南请参阅：** [大型文档指南](LARGE_DOCUMENTATION.md)

## 测试选择器

为文档站点查找合适的 CSS 选择器：

```python
from bs4 import BeautifulSoup
import requests

url = "https://docs.example.com/page"
soup = BeautifulSoup(requests.get(url).content, 'html.parser')

# Try different selectors
print(soup.select_one('article'))
print(soup.select_one('main'))
print(soup.select_one('div[role="main"]'))
```

## 运行测试

**重要：运行测试前必须先安装包**

```bash
# 1. Install package in editable mode (one-time setup)
pip install -e .

# 2. Run all tests
pytest

# 3. Run specific test files
pytest tests/test_config_validation.py
pytest tests/test_github_scraper.py

# 4. Run with verbose output
pytest -v

# 5. Run with coverage report
pytest --cov=src/skill_seekers --cov-report=html
```

**为什么要先安装？**
- 测试从 `skill_seekers.cli` 导入，这要求先安装该包
- 符合现代 Python 打包最佳实践（PEP 517/518）
- CI/CD 会自动使用 `pip install -e .` 安装
- 如果包未安装，conftest.py 会显示有用的错误信息

**测试覆盖：**
- 391+ 测试通过
- 39% 代码覆盖率
- 所有核心功能均已测试
- CI/CD 在 Ubuntu + macOS 上使用 Python 3.10-3.12 进行测试

## 故障排除

**未提取到内容**：检查 `main_content` 选择器。常见值：`article`、`main`、`div[role="main"]`、`div.content`

**分类效果差**：编辑配置中的 `categories` 部分，使用更贴合该文档结构的关键词

**强制重新抓取**：使用 `rm -rf output/{name}_data/` 删除缓存数据

**速率限制问题**：增大配置中的 `rate_limit` 值（例如从 0.5 增至 1.0 秒）

## 输出质量检查

构建后验证质量：
```bash
cat output/godot/SKILL.md              # Should have real code examples
cat output/godot/references/index.md   # Should show categories
ls output/godot/references/            # Should have category .md files
```

## llms.txt 支持

Skill_Seekers 会在 HTML 抓取前自动检测 llms.txt 文件：

### 检测顺序
1. `{base_url}/llms-full.txt`（完整文档）
2. `{base_url}/llms.txt`（标准版本）
3. `{base_url}/llms-small.txt`（快速参考）

### 优势
- ⚡ 快 10 倍（< 5 秒 vs 20-60 秒）
- ✅ 更可靠（由文档作者维护）
- 🎯 质量更好（为 LLM 预先格式化）
- 🚫 无需速率限制

### 示例站点
- Hono: https://hono.dev/llms-full.txt

如果未找到 llms.txt，会自动回退到 HTML 抓取。
