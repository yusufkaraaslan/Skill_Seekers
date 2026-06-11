# API 参考 - 程序化使用

**版本：** 3.7.0
**最后更新：** 2026-06-11
**状态：** ✅ 已对照 v3.7.0 验证（本文档中的每个导入和签名都通过实际导入进行了检查）

---

## 概述

Skill Seekers 可通过编程方式使用，以便集成到其他工具、自动化脚本和 CI/CD 流水线中。本指南面向希望将 Skill Seekers 功能嵌入到自有应用中的开发者，介绍可用的 Python API。

> **稳定性说明 —— 请先阅读**
>
> **PyPI 包的稳定、受支持接口是 `skill-seekers` CLI**（以及 MCP 服务器）。本文档介绍的 Python API 真实存在且可以导入 —— 它就是 CLI 运行的同一份代码 —— 但它跟随实现演进：模块路径、签名和配置字典键可能在次要版本之间发生变化。**Semver 保证不覆盖这些内部实现。** 如果你导入这些模块，请固定到精确版本（`skill-seekers==3.7.0`），并在升级时重新验证。

**使用场景：**
- CI/CD 中的自动化文档技能生成
- 批量处理多个文档源
- 自定义技能生成工作流
- 与内部工具集成
- 文档变更时自动更新技能

下面的每个示例都标注了 **[offline]**（无网络、无 AI）、**[network]**（获取远程内容）或 **[AI]**（调用 LLM API 或生成本地代理）。

---

## 安装

### 基础安装

```bash
pip install skill-seekers
```

### 附带平台依赖

```bash
# Google Gemini support
pip install skill-seekers[gemini]

# OpenAI ChatGPT support
pip install skill-seekers[openai]

# All LLM platform support
pip install skill-seekers[all-llms]

# Everything (all source types + platforms, except video-full)
pip install skill-seekers[all]
```

### 开发安装

```bash
git clone https://github.com/yusufkaraaslan/Skill_Seekers.git
cd Skill_Seekers
pip install -e ".[all-llms]"
```

---

## 核心 API

### 1. 技能转换 API（`get_converter`）

主要的编程入口与 `skill-seekers create` 命令一一对应：工厂函数为 18 种来源类型中的任意一种返回一个 `SkillConverter`，而 `run()` 执行完整的 extract → build 流水线。

```python
from skill_seekers.cli.skill_converter import get_converter, CONVERTER_REGISTRY

# get_converter(source_type: str, config: dict[str, Any]) -> SkillConverter
# SkillConverter.run() -> int   (0 = success, non-zero = failure)

print(sorted(CONVERTER_REGISTRY))
# ['asciidoc', 'chat', 'config', 'confluence', 'epub', 'github', 'html',
#  'jupyter', 'local', 'manpage', 'notion', 'openapi', 'pdf', 'pptx',
#  'rss', 'video', 'web', 'word']
```

#### 基本用法 —— 网页文档 **[network]**

```python
from skill_seekers.cli.skill_converter import get_converter

config = {
    "name": "django",
    "description": "Use when working with Django web framework",
    "base_url": "https://docs.djangoproject.com/en/5.0/",
    "selectors": {"main_content": "article", "title": "h1", "code_blocks": "pre code"},
    "url_patterns": {"include": ["/en/5.0/"], "exclude": []},
    "max_pages": 50,
    "rate_limit": 0.5,
    "output_dir": "output/django",
}

converter = get_converter("web", config)
exit_code = converter.run()          # scrapes, then builds output/django/SKILL.md
print("ok" if exit_code == 0 else "failed")
```

#### 模板方法契约

`run()` 是 `SkillConverter` 基类上的模板方法：

1. `extract()` —— 特定于来源的提取（抓取、解析、克隆……）
2. `build_skill()` —— 对内容进行分类并写出 `SKILL.md` + `references/`

`run()` **返回退出码而不是抛出异常**：来自 `extract()`/`build_skill()` 的异常会被记录日志并转换为返回值 `1`。请检查返回值，而不是写 `try/except`。

```python
converter = get_converter("pdf", {"name": "manual", "pdf_path": "manual.pdf"})

# Reuse existing on-disk extracted data (skip extraction, rebuild only):
converter.skip_scrape = True   # run() checks this attribute
converter.run()
```

#### 工厂错误 **[offline]**

- `ValueError` —— 未知的来源类型（错误消息会列出支持的类型）
- `RuntimeError` —— 该来源类型的可选依赖未安装（错误消息包含 `pip install` 提示）

#### 通过工厂使用统一配置 **[offline 构造]**

`"config"` 来源类型将多源 `UnifiedScraper`（第 4 节）包装在同一个工厂之后。它接受**工厂形态的字典** —— 只有 `config_path` 是必需的：

```python
from skill_seekers.cli.skill_converter import get_converter

scraper = get_converter("config", {
    "config_path": "configs/unified/react-unified.json",
    "output_dir": "output/react-complete",   # optional override
    "merge_mode": "rule-based",              # optional: 'rule-based' | 'claude-enhanced'
    "dry_run": True,                         # optional: preview sources, write nothing
})
scraper.run()
```

---

### 2. 来源检测 API

`SourceDetector` 是 `skill-seekers create` 用来从原始输入字符串自动检测来源类型的组件。它返回一个 `SourceInfo` 数据类。

#### 基本用法 **[offline]**

```python
from skill_seekers.cli.source_detector import SourceDetector

detector = SourceDetector()

# detect(source: str) -> SourceInfo
info = detector.detect("https://docs.djangoproject.com/")
print(info.type)            # 'web'
print(info.parsed)          # {'url': 'https://docs.djangoproject.com/'}
print(info.suggested_name)  # 'djangoproject'
print(info.raw_input)       # original input string

detector.detect("fastapi/fastapi").type   # 'github'  -> parsed: {'repo': 'fastapi/fastapi'}
detector.detect("./manual.pdf").type      # 'pdf'     -> parsed: {'file_path': './manual.pdf'}
detector.detect("./my-project").type      # 'local'   -> parsed: {'directory': '/abs/path/my-project'}
detector.detect("configs/react.json").type  # 'config' -> parsed: {'config_path': 'configs/react.json'}
```

`SourceInfo` 字段：`type`、`parsed`（字典，形态取决于 `type`）、`suggested_name`、`raw_input`。

注意：本地目录检测要求该路径在磁盘上真实存在 —— 不存在的 `./name` 会落入其他检测器（例如 `owner/repo` GitHub 简写）。

#### 先检测后转换的流水线 **[network，针对 web/github]**

```python
from skill_seekers.cli.source_detector import SourceDetector
from skill_seekers.cli.skill_converter import get_converter

info = SourceDetector().detect("./manual.pdf")

config = {
    "name": info.suggested_name,
    "pdf_path": info.parsed["file_path"],
    "output_dir": f"output/{info.suggested_name}",
}
get_converter(info.type, config).run()
```

（CLI 的 `create_command.py:_build_config()` 是从 `SourceInfo.parsed` 到各转换器配置键的规范映射。）

---

### 3. 直接构造转换器

每个转换器类都可以用配置字典直接构造（工厂所做的只是注册表查找 + 可选依赖检查）。下方的配置键由各转换器的 `__init__` 读取，并已对照 v3.7.0 验证。

#### PDF —— `PDFToSkillConverter` **[offline —— 本地文件处理]**

```python
from skill_seekers.cli.pdf_scraper import PDFToSkillConverter

converter = PDFToSkillConverter({
    "name": "product-manual",                  # required
    "pdf_path": "manual.pdf",                  # path to the PDF
    "description": "Product manual reference", # optional
    "output_dir": "output/product-manual",     # optional (default: output/<name>)
    "extract_options": {                       # optional
        "chunk_size": 10,         # pages per chunk
        "min_quality": 5.0,       # quality threshold for extracted text
        "extract_images": True,
        "min_image_size": 100,
    },
    "categories": {},                          # optional keyword mapping
})
converter.run()
```

#### Web —— `DocToSkillConverter` **[network]**

```python
from skill_seekers.cli.doc_scraper import DocToSkillConverter

converter = DocToSkillConverter({
    "name": "react",                                  # required
    "base_url": "https://react.dev/",                 # required
    "selectors": {"main_content": "article", "title": "h1", "code_blocks": "pre code"},
    "url_patterns": {"include": ["/learn", "/reference"], "exclude": ["/blog"]},
    "categories": {},          # optional; smart categorization fills the gap
    "rate_limit": 0.5,         # seconds between requests
    "max_pages": 200,          # -1 = unlimited
    "start_urls": [],          # optional explicit seed URLs
    "llms_txt_url": None,      # optional llms.txt source
    "browser": False,          # Playwright rendering for JS-heavy sites
    "workers": 1,              # parallel scrape workers
    "async_mode": False,       # asyncio scraping (faster on large sites)
    "doc_version": "",         # stamped into SKILL.md metadata
    "output_dir": "output/react",
})
converter.run()
```

构造函数还接受 `dry_run=True` / `resume=True` 关键字参数（或配置字典中的同名键）。

#### GitHub —— `GitHubScraper` **[network —— GitHub API；设置 `GITHUB_TOKEN` 可获得更高速率限制]**

```python
from skill_seekers.cli.github_scraper import GitHubScraper

converter = GitHubScraper({
    "repo": "fastapi/fastapi",        # required, owner/repo
    "name": "fastapi",                # optional (default: repo short name)
    "local_repo_path": None,          # optional local clone => unlimited analysis, no API limits
    "include_code": True,
    "include_issues": True,
    "max_issues": 100,
    "max_comments": 0,
    "issue_labels": [],               # filter issues by label
    "issue_state": "all",             # 'open' | 'closed' | 'all'
    "include_changelog": True,
    "include_releases": True,
    "output_dir": "output/fastapi",
})
converter.run()
```

其余 15 个转换器遵循相同的模式；各自的模块/类参见 `src/skill_seekers/cli/skill_converter.py` 中的 `CONVERTER_REGISTRY`，各自的配置键参见各类的 `__init__`（例如 `word` 读取 `docx_path`，`local` 读取 `directory` 以及 C3.x 的 `detect_patterns`/`extract_test_examples`/…… 开关）。

---

### 4. 统一多源抓取 API

`UnifiedScraper` 将多个来源（18 种受支持类型中的任意几种）合并为一个技能。它本身就是一个 `SkillConverter`（注册为来源类型 `"config"`）。

#### 构造形式

```python
from skill_seekers.cli.unified_scraper import UnifiedScraper

# 1. Path to a unified config JSON file
scraper = UnifiedScraper("configs/unified/react-unified.json")

# 2. Already-loaded unified config dict (name + description required)
scraper = UnifiedScraper({"name": "react-complete", "description": "...", "sources": [...]})

# 3. Factory-shaped dict (what get_converter("config", ...) passes through)
scraper = UnifiedScraper({"config_path": "configs/unified/react-unified.json"})

# Keyword overrides (win over the config file's values)
scraper = UnifiedScraper(
    "configs/unified/react-unified.json",
    merge_mode="rule-based",        # or 'claude-enhanced' (AI merge)
    output_dir="output/react-complete",
    dry_run=False,
)
```

#### 运行 **[network —— 抓取每个来源；merge_mode='claude-enhanced' 时为 AI]**

```python
scraper = UnifiedScraper("configs/unified/react-unified.json")
scraper.run()    # scrape all sources -> merge -> detect conflicts -> build skill
```

#### 干运行预览 **[offline]**

```python
UnifiedScraper("configs/unified/react-unified.json", dry_run=True).run()
# Logs the sources that WOULD be scraped and the output directory; writes nothing.
```

#### 冲突检测

冲突检测是**实例上的方法**，而不是模块级函数。`run()` 会在合并之后自动调用它；你也可以手动驱动各个阶段：

```python
scraper = UnifiedScraper("configs/unified/react-unified.json")
scraper.scrape_all_sources()              # [network]
merged = scraper.merge_sources()
conflicts = scraper.detect_conflicts()    # -> list of conflict records
scraper.build_skill(merged)
```

---

### 5. 技能打包 API

使用适配器架构（策略 + 工厂模式）为不同平台打包技能。

#### 基础打包 **[offline]**

```python
from pathlib import Path
from skill_seekers.cli.adaptors import get_adaptor, ADAPTORS

# get_adaptor(platform: str, config: dict = None) -> SkillAdaptor
print(sorted(ADAPTORS))
# ['atlas', 'chroma', 'claude', 'deepseek', 'faiss', 'fireworks', 'gemini',
#  'haystack', 'ibm-bob', 'kimi', 'langchain', 'llama-index', 'markdown',
#  'minimax', 'openai', 'opencode', 'openrouter', 'pinecone', 'qdrant',
#  'qwen', 'together', 'weaviate']

adaptor = get_adaptor("claude")

# package(skill_dir: Path, output_path: Path, ...) -> Path
package_path = adaptor.package(Path("output/react"), Path("output"))
print(package_path)   # output/react.zip
```

对于未知平台，`get_adaptor` 抛出 `ValueError`；若该平台的可选依赖缺失，则抛出 `ImportError`（附安装提示）。

#### 带分块的打包（RAG/向量目标）**[offline]**

```python
package_path = adaptor.package(
    Path("output/react"),
    Path("output"),
    enable_chunking=True,        # split content into token-bounded chunks
    chunk_max_tokens=512,
    preserve_code_blocks=True,   # never split inside a code fence
    chunk_overlap_tokens=50,
)
```

#### 多平台打包 **[offline]**

```python
from pathlib import Path
from skill_seekers.cli.adaptors import get_adaptor

for platform in ["claude", "gemini", "openai", "markdown"]:
    adaptor = get_adaptor(platform)
    pkg = adaptor.package(Path("output/react"), Path("output"))
    print(f"{platform}: {pkg}")
```

#### 格式化与能力检查 **[offline]**

```python
from pathlib import Path
from skill_seekers.cli.adaptors import get_adaptor
from skill_seekers.cli.adaptors.base import SkillAdaptor, SkillMetadata

adaptor = get_adaptor("claude")

adaptor.PLATFORM               # 'claude'
adaptor.supports_upload()      # True
adaptor.supports_enhancement() # True
adaptor.get_env_var_name()     # 'ANTHROPIC_API_KEY'

# format_skill_md(skill_dir: Path, metadata: SkillMetadata) -> str
meta = SkillMetadata(name="my-skill", description="When to use this skill")
text = adaptor.format_skill_md(Path("output/my-skill"), meta)
```

`SkillMetadata` 字段：`name`、`description`、`version`（默认 `"1.0.0"`）、`doc_version`、`author`、`tags`。

#### 共享 Embedding 方法

基类 `SkillAdaptor` 提供两个共享的 embedding 辅助方法，由所有向量数据库适配器（chroma、weaviate、pinecone、qdrant、faiss）继承：

- `_generate_openai_embeddings(texts, model)` —— 通过 OpenAI API 生成 embeddings。**[network]**
- `_generate_st_embeddings(texts, model)` —— 使用本地 sentence-transformers 模型生成 embeddings。**[offline]**

它们带下划线前缀（内部方法），但有意共享，以避免各向量适配器重复实现 embedding 逻辑。

---

### 6. 技能上传 API

通过各平台的 API 将打包好的技能上传到 LLM 平台。基类上的签名：

```python
# upload(package_path: Path, api_key: str, **kwargs) -> dict[str, Any]
```

返回字典的键是**平台特定的** —— 请查看具体适配器的 `upload()`（例如 `src/skill_seekers/cli/adaptors/claude.py`）了解确切形态。请先检查 `adaptor.supports_upload()`：不支持上传的适配器（例如 `markdown`）会返回一个包含 `"success": False` 和说明性 `"message"` 的结果字典，而不会执行上传。

#### Claude AI 上传 **[network —— Anthropic API]**

```python
import os
from pathlib import Path
from skill_seekers.cli.adaptors import get_adaptor

adaptor = get_adaptor("claude")
result = adaptor.upload(
    Path("output/react.zip"),
    api_key=os.environ["ANTHROPIC_API_KEY"],
)
```

#### Google Gemini 上传 **[network —— 需要 `pip install skill-seekers[gemini]`]**

```python
adaptor = get_adaptor("gemini")
result = adaptor.upload(Path("output/react.tar.gz"), api_key=os.environ["GOOGLE_API_KEY"])
```

#### OpenAI 上传 **[network —— 需要 `pip install skill-seekers[openai]`]**

```python
adaptor = get_adaptor("openai")
result = adaptor.upload(Path("output/react-openai.zip"), api_key=os.environ["OPENAI_API_KEY"])
```

使用 `adaptor.get_env_var_name()` 可以查询各平台约定读取的环境变量名；上传前可用 `adaptor.validate_api_key(key)` 做一次轻量的格式检查。

---

### 7. AI 增强 API

使用 AI 驱动的改进来增强技能。所有 API 模式的增强都经由共享的
`AgentClient`（`skill_seekers.cli.agent_client`）路由，它集中处理
提供商选择（Anthropic/Gemini/OpenAI/Moonshot）、模型与 base-URL 覆盖、
截断闸门、超时策略，以及 SKILL.md 的原子化备份再保存。

#### API 模式增强（按平台适配器）**[AI —— 提供商 API 调用]**

```python
import os
from pathlib import Path
from skill_seekers.cli.adaptors import get_adaptor

adaptor = get_adaptor('claude')  # also: gemini, openai, and OpenAI-compatible targets

# Enhance SKILL.md via the platform's API (returns True on success).
# The original is backed up to SKILL.md.backup and the save is atomic.
ok = adaptor.enhance(
    Path('output/react/'),
    os.getenv('ANTHROPIC_API_KEY'),
)
```

#### 直接使用 AgentClient **[AI]**

```python
from skill_seekers.cli.agent_client import AgentClient

client = AgentClient(mode='api')          # or mode='local' (spawns a local agent)
reply = client.call('Summarize this skill...', timeout=600)
```

`AgentClient(mode='auto'|'api'|'local', agent=None, api_key=None, provider=None, base_url=None, model=None)`；`call(prompt, max_tokens=4096, timeout=None, output_file=None, cwd=None, system=None, temperature=None) -> str | None`。还有：`is_available()`、`get_model()`、`detect_api_key()`。

#### LOCAL 模式增强（本地编码代理，免费）**[AI —— 生成本地代理]**

```python
from skill_seekers.cli.enhance_skill_local import LocalSkillEnhancer

enhancer = LocalSkillEnhancer(
    'output/react/',
    agent='claude',        # claude, codex, copilot, opencode, kimi, custom
)
enhancer.run(background=True)   # or headless=True (default), daemon=True
```

从 CLI 监控后台运行：

```bash
skill-seekers enhance-status output/react/ --watch
```

> LOCAL 模式会在生成的代理环境中设置 `SKILL_SEEKER_ENHANCE_ACTIVE=1`，
> 并在该变量已被设置时拒绝启动，防止代理被递归生成。

---

### 8. 执行上下文

`ExecutionContext` 是 CLI 从 argparse + 配置文件构建的、经 pydantic 验证的集中式设置单例。转换器和增强从它读取设置；编程调用方可以初始化并覆盖它。

```python
from skill_seekers.cli.execution_context import ExecutionContext

# Classmethods:
#   initialize(args=None, config_path=None, source_info=None) -> ExecutionContext
#   get() -> ExecutionContext          (active override, else base singleton)
#   is_initialized() -> bool
#   reset() -> None                    (mainly for tests)

ExecutionContext.is_initialized()   # False until initialize() is called
ctx = ExecutionContext.initialize() # defaults when args is None

ctx.enhancement.level    # 2
ctx.scraping.max_pages   # -1 (unlimited)
ctx.output.output_dir    # None
ctx.analysis.depth       # 'surface'
```

#### 临时覆盖（上下文管理器）**[offline]**

`override(**kwargs)` 是一个上下文管理器；双下划线键用于寻址嵌套的设置组（`source`、`enhancement`、`output`、`scraping`、`analysis`）。覆盖是**上下文局部的**（存储在 `contextvars.ContextVar` 中），因此并发的 asyncio 任务各自只能看到自己的覆盖，嵌套的覆盖也能干净地叠加和回退：

```python
ctx = ExecutionContext.get()

with ctx.override(enhancement__level=3, scraping__max_pages=100):
    active = ExecutionContext.get()
    assert active.enhancement.level == 3      # inside: overridden

assert ExecutionContext.get().enhancement.level == 2  # outside: restored
```

注意事项：contextvars 会自动流入 asyncio 任务，但流入工作线程只能通过 `contextvars.copy_context().run(...)` —— 裸的 `threading.Thread` 看到的是基础单例，而不是你的覆盖。

---

### 9. 服务层（`skill_seekers.services`）

由 CLI 和 MCP 服务器共享的领域逻辑。**无需** `[mcp]` extra 即可导入。请从子模块导入：

```python
from skill_seekers.services.marketplace_manager import MarketplaceManager
from skill_seekers.services.source_manager import SourceManager
from skill_seekers.services.config_publisher import ConfigPublisher, detect_category
from skill_seekers.services.git_repo import GitConfigRepo
```

#### 市场注册表 CRUD **[offline —— 本地注册表文件]**

```python
mm = MarketplaceManager()        # or MarketplaceManager(config_dir="~/.skill-seekers")
mm.list_marketplaces()           # -> list[dict]; also: add/get/update/remove_marketplace
```

#### 配置源注册表 CRUD **[offline]**

```python
sm = SourceManager()
sm.list_sources()                # also: add/get/update/remove_source
```

#### 配置类别检测 **[offline]**

```python
detect_category({"name": "react", "description": "React frontend UI library docs"})
# 'web-frameworks'   (keyword scoring over CATEGORY_KEYWORDS)
```

#### Git 后端的配置仓库 **[network —— 克隆/拉取]**

```python
repo = GitConfigRepo()                       # or GitConfigRepo(cache_dir=...)
repo.validate_git_url("https://github.com/owner/configs.git")   # offline check
path = repo.clone_or_pull("https://github.com/owner/configs.git")  # [network]
configs = repo.find_configs(path)
```

`ConfigPublisher`（`ConfigPublisher(cache_dir=None)`）将配置推送到已注册的配置源仓库；`MarketplacePublisher` 将打包好的技能发布到插件市场仓库。两者都会执行 git 推送 **[network]**。

---

## 配置对象

完整的配置文件模式（单源和统一）记录在 **[CONFIG_FORMAT.md](CONFIG_FORMAT.md)** 中 —— 那是权威参考。摘要如下：

### Web（单源）配置键

这些是 `DocToSkillConverter` 读取的键（无论是从 `configs/*.json` 文件加载还是在代码中构建，都是同一个字典）：

| 字段 | 类型 | 默认值 | 描述 |
|-------|------|---------|-------------|
| `name` | string | *必需* | 技能名称（字母数字 + 连字符） |
| `base_url` | string | *必需* | 文档网站 URL |
| `description` | string | 自动生成 | 何时使用此技能 |
| `selectors` | object | `{}` | CSS 选择器（`main_content`、`title`、`code_blocks`） |
| `url_patterns` | object | `{}` | `include` / `exclude` URL 子串列表 |
| `categories` | object | `{}` | 类别关键词映射 |
| `rate_limit` | float | `0.5` | 请求之间的延迟（秒） |
| `max_pages` | int | `-1` | 最大抓取页数（-1 = 无限制） |
| `start_urls` | array | `[]` | 显式种子 URL |
| `llms_txt_url` | string | `null` | llms.txt 文件的 URL |
| `async_mode` | bool | `false` | asyncio 抓取（大型站点更快） |
| `browser` | bool | `false` | 针对 JS 密集型站点的 Playwright 渲染 |
| `workers` | int | `1` | 并行抓取工作者数 |
| `output_dir` | string | `output/<name>` | 技能写出位置 |

### 统一配置模式（多源）

支持全部 18 种来源类型：`documentation`、`github`、`pdf`、`local`、`word`、`video`、`epub`、`jupyter`、`html`、`openapi`、`asciidoc`、`pptx`、`rss`、`manpage`、`confluence`、`notion`、`chat`、`config`。

```json
{
  "name": "framework-unified",
  "description": "Complete framework documentation",
  "merge_mode": "rule-based",
  "sources": [
    {
      "type": "documentation",
      "base_url": "https://docs.example.com/",
      "selectors": { "main_content": "article" }
    },
    {
      "type": "github",
      "repo": "org/repo",
      "include_code": true
    },
    {
      "type": "pdf",
      "path": "manual.pdf"
    },
    {
      "type": "openapi",
      "path": "specs/openapi.yaml"
    },
    {
      "type": "video",
      "url": "https://www.youtube.com/watch?v=example"
    },
    {
      "type": "jupyter",
      "path": "notebooks/examples.ipynb"
    },
    {
      "type": "confluence",
      "base_url": "https://company.atlassian.net/wiki",
      "space_key": "DOCS"
    }
  ]
}
```

配置在加载时由 `skill_seekers.cli.config_validator.validate_config(config_path)` 验证，CLI 和 `UnifiedScraper` 会替你调用它。

---

## 错误处理

Python API 通过三种不同方式表达失败 —— 请按你所调用的层来匹配：

```python
from pathlib import Path
from skill_seekers.cli.skill_converter import get_converter
from skill_seekers.cli.adaptors import get_adaptor

# 1. Factory-time errors RAISE:
try:
    converter = get_converter("web", config)
except ValueError as e:      # unknown source type
    print(e)
except RuntimeError as e:    # missing optional dependency (includes pip install hint)
    print(e)

try:
    adaptor = get_adaptor("chroma")
except ValueError as e:      # unknown platform
    print(e)
except ImportError as e:     # optional dependency not installed
    print(e)

# 2. Conversion errors are RETURN CODES (run() catches and logs exceptions):
if converter.run() != 0:
    raise SystemExit("skill build failed — see log output")

# 3. Adaptor operations either RAISE (network/API errors during real uploads)
#    or report failure in the returned dict — gate on capability and check
#    result["success"]:
if adaptor.supports_upload():
    result = adaptor.upload(Path("output/react.zip"), api_key=key)
    if not result.get("success"):
        print(result.get("message"))
```

不存在 `skill_seekers.exceptions` 模块 —— 全程使用标准异常（`ValueError`、`RuntimeError`、`ImportError`、`FileNotFoundError`）。

---

## 测试你的集成

使用 `dry_run` 和较小的 `max_pages` 限制，让测试保持快速且对离线友好：

```python
from skill_seekers.cli.skill_converter import get_converter
from skill_seekers.cli.source_detector import SourceDetector


def test_source_detection():            # [offline]
    info = SourceDetector().detect("https://docs.example.com/")
    assert info.type == "web"
    assert info.parsed["url"] == "https://docs.example.com/"


def test_unified_dry_run(tmp_path):     # [offline] — previews without scraping
    import json
    cfg = tmp_path / "unified.json"
    cfg.write_text(json.dumps({
        "name": "test",
        "description": "Test skill",   # name + description are required
        "sources": [{"type": "github", "repo": "owner/repo"}],
    }))
    scraper = get_converter("config", {"config_path": str(cfg), "dry_run": True})
    assert scraper.run() == 0


def test_packaging(tmp_path):           # [offline]
    from pathlib import Path
    from skill_seekers.cli.adaptors import get_adaptor

    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("---\nname: t\ndescription: d\n---\n# T\n")
    pkg = get_adaptor("markdown").package(skill, tmp_path)
    assert pkg.exists()
```

---

## 性能说明

- **异步抓取**：在 web 配置中设置 `"async_mode": True`，大型站点的抓取速度可提升 2–3 倍；`"workers": N` 可并行化基于线程的抓取器。
- **不重新抓取直接重建**：在 `run()` 之前设置 `converter.skip_scrape = True`，可以从磁盘上已有的提取数据（`output/<name>_data/`）重建 `SKILL.md`。
- **恢复**：web 配置支持检查点 —— 向 `DocToSkillConverter` 传递 `resume=True`（或在配置中写 `"resume": True`）即可继续被中断的抓取。
- **批量处理**：各转换器相互独立；可以在 `ThreadPoolExecutor` 中运行多个 `get_converter(...).run()` 调用。不要在普通线程之间共享同一个 `ExecutionContext.override()`（参见第 8 节的注意事项）。

---

## CI/CD 集成示例

对于流水线，请优先使用 CLI —— 它才是稳定接口：

### GitHub Actions

```yaml
name: Generate Skills

on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight
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
          skill-seekers install --config react --target claude
          skill-seekers install --config vue --target gemini

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
    - skill-seekers install --config react --target claude
    - skill-seekers install --config vue --target gemini --no-upload
  artifacts:
    paths:
      - output/
  only:
    - schedules
```

---

## 最佳实践

### 1. **自动化优先使用 CLI；Python 导入务必固定版本**
```bash
pip install skill-seekers==3.7.0   # internals can shift between minors
```

### 2. **使用工厂，而非硬编码类**
```python
# Good: registry-driven
converter = get_converter(info.type, config)
adaptor = get_adaptor(target_platform)

# Brittle: hardcoded imports break when modules move
```

### 3. **检查 run() 返回码**
```python
if get_converter("web", config).run() != 0:
    raise SystemExit(1)   # run() logs the exception; it does not re-raise
```

### 4. **缓存抓取数据，低成本重建**
```python
converter = get_converter("web", config)
converter.run()                 # first run: scrape + build (slow)

converter = get_converter("web", config)
converter.skip_scrape = True
converter.run()                 # rebuild from output/<name>_data/ (fast)
```

### 5. **调用前探测适配器能力**
```python
adaptor = get_adaptor(platform)
if adaptor.supports_upload():
    adaptor.upload(pkg, api_key=os.environ[adaptor.get_env_var_name()])
```

### 6. **在测试中使用干运行**
```python
get_converter("config", {"config_path": cfg, "dry_run": True}).run()
```

---

## API 参考摘要

| API | 导入 | 使用场景 |
|-----|--------|----------|
| **技能转换工厂** | `skill_seekers.cli.skill_converter.get_converter` | 18 种来源类型中任意一种 → 技能 |
| **转换器注册表** | `skill_seekers.cli.skill_converter.CONVERTER_REGISTRY` | 来源类型 → (module, class) 查找 |
| **来源检测** | `skill_seekers.cli.source_detector.SourceDetector` | 从原始输入自动检测类型 |
| **网页文档** | `skill_seekers.cli.doc_scraper.DocToSkillConverter` | 文档网站 |
| **GitHub 仓库** | `skill_seekers.cli.github_scraper.GitHubScraper` | 代码 + 文档 + 社区分析 |
| **PDF** | `skill_seekers.cli.pdf_scraper.PDFToSkillConverter` | PDF 文档 |
| **本地代码库** | `skill_seekers.cli.codebase_scraper.CodebaseAnalyzer` | 本地目录（C3.x 流水线） |
| **多源** | `skill_seekers.cli.unified_scraper.UnifiedScraper` | 合并 18 种来源类型 + 冲突检测 |
| **打包 / 上传 / 增强** | `skill_seekers.cli.adaptors.get_adaptor` | 22 个平台目标 |
| **AI 增强** | `skill_seekers.cli.agent_client.AgentClient` | API 或本地代理 LLM 调用 |
| **本地代理增强** | `skill_seekers.cli.enhance_skill_local.LocalSkillEnhancer` | 通过编码代理免费增强 |
| **设置单例** | `skill_seekers.cli.execution_context.ExecutionContext` | 初始化 / 获取 / 覆盖设置 |
| **市场注册表** | `skill_seekers.services.marketplace_manager.MarketplaceManager` | 市场 CRUD |
| **配置源** | `skill_seekers.services.source_manager.SourceManager` | 配置源注册表 CRUD |
| **配置发布** | `skill_seekers.services.config_publisher` | 推送配置；`detect_category()` |
| **Git 配置仓库** | `skill_seekers.services.git_repo.GitConfigRepo` | 克隆/拉取 + 配置发现 |

其余 14 个转换器类（word、epub、video、jupyter、html、openapi、asciidoc、pptx、rss、manpage、confluence、notion、chat）列在 `CONVERTER_REGISTRY` 中。

---

## 其他资源

- **[主文档](../../README.md)** - 完整用户指南
- **[CLI 参考](CLI_REFERENCE.md)** - 稳定的命令行接口
- **[配置格式](CONFIG_FORMAT.md)** - 权威配置模式
- **[MCP 设置](../guides/MCP_SETUP.md)** - MCP 服务器集成
- **[多 LLM 支持](../integrations/MULTI_LLM_SUPPORT.md)** - 平台对比
- **[CHANGELOG](../../CHANGELOG.md)** - 版本历史与 API 变更

---

**版本：** 3.7.0
**最后更新：** 2026-06-11
