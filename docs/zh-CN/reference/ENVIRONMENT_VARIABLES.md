# 环境变量参考 - Skill Seekers

> **版本：** 3.7.0  
> **最后更新：** 2026-02-16  
> **完整的环境变量参考**

---

## 目录

- [概述](#overview)
- [API 密钥](#api-keys)
- [平台配置](#platform-configuration)
- [LLM 提供商选择](#llm-provider-selection)
- [路径与目录](#paths-and-directories)
- [抓取行为](#scraping-behavior)
- [增强设置](#enhancement-settings)
- [GitHub 配置](#github-configuration)
- [向量数据库设置](#vector-database-settings)
- [调试与开发](#debug-and-development)
- [MCP 服务器设置](#mcp-server-settings)
- [示例](#examples)

---

## 概述

Skill Seekers 使用环境变量来实现：
- API 身份验证（Claude、Gemini、OpenAI、GitHub）
- 配置路径
- 输出目录
- 行为自定义
- 调试设置

变量在运行时读取，并覆盖默认设置。

---

## API 密钥

### ANTHROPIC_API_KEY

**用途：** Claude AI API 访问，用于增强和上传。

**格式：** `sk-ant-api03-...`

**使用者：**
- `skill-seekers enhance`（API 模式）
- `skill-seekers upload`（Claude 目标）
- AI 增强功能

**示例：**
```bash
export ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**替代方式：** 在每个命令中使用 `--api-key` 标志。

---

### GOOGLE_API_KEY

**用途：** Google Gemini API 访问，用于上传。

**格式：** `AIza...`

**使用者：**
- `skill-seekers upload`（Gemini 目标）

**示例：**
```bash
export GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

### OPENAI_API_KEY

**用途：** OpenAI（以及 OpenAI 兼容）API 访问，用于增强、上传和 embeddings。

**格式：** `sk-...`

**使用者：**
- `skill-seekers create` / `scan` / `enhance`（AI 增强，API 模式）
- `skill-seekers upload`（OpenAI 目标）
- 向量数据库的 embedding 生成

**示例：**
```bash
export OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> 与 `OPENAI_BASE_URL` + `OPENAI_MODEL` 配合使用，可将增强请求路由到任意
> OpenAI 兼容提供商（OpenRouter、Groq、Cerebras、Mistral、NVIDIA NIM）。
> 参见 [LLM 提供商选择](#llm-provider-selection)。

---

### MOONSHOT_API_KEY

**用途：** Moonshot AI（Kimi）API 访问，用于增强（API 模式）。

**格式：** `sk-...`

**使用者：**
- `skill-seekers create` / `scan` / `enhance`（增强，Kimi/Moonshot）

**示例：**
```bash
export MOONSHOT_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

### GITHUB_TOKEN

**用途：** GitHub API 身份验证，用于获得更高的速率限制，以及提交社区注册表配置。

**格式：** `ghp_...`（个人访问令牌）或 `github_pat_...`（细粒度令牌）

**使用者：**
- `skill-seekers create`（GitHub 仓库）
- `skill-seekers create --config`（统一多源）
- `skill-seekers scan`（本地代码库）
- `skill-seekers scan` —— 向社区注册表提交 AI 生成的配置时*必需*（扫描本身无需该令牌即可运行；只是发布提示会被跳过并给出提示信息）

**好处：**
- 每小时 5000 次请求（未认证为 60 次）
- 访问私有仓库
- 更高的 GraphQL API 限额
- 允许从 `scan` 打开社区配置 GitHub issue

**示例：**
```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**创建令牌：** https://github.com/settings/tokens

---

## 平台配置

### ANTHROPIC_BASE_URL

**用途：** 自定义 Claude API 端点。

**默认值：** `https://api.anthropic.com`

**使用场景：** 代理服务器、企业部署、区域端点。

**示例：**
```bash
export ANTHROPIC_BASE_URL=https://custom-api.example.com
```

---

### OPENAI_BASE_URL

**用途：** 用于增强的自定义 OpenAI 兼容 API 端点。

**默认值：** `https://api.openai.com/v1`

**使用场景：** 任意 OpenAI 兼容提供商 —— OpenRouter、Groq、Cerebras、Mistral、
NVIDIA NIM、本地服务器（Ollama、vLLM、LM Studio）、代理。

**示例：**
```bash
export OPENAI_BASE_URL=https://openrouter.ai/api/v1
```

> 由 OpenAI SDK 自动读取。请与 `OPENAI_API_KEY` 和 `OPENAI_MODEL` 配对使用。

---

## LLM 提供商选择

AI **增强**步骤（`create`、`scan`、`enhance`）通过一个抽象层
（`AgentClient` —— 每次 API 增强调用都经由它路由）支持多个提供商。
提供商由找到的**第一个** API 密钥决定，顺序按照
`cli/agent_client.py` 中 `API_PROVIDERS` 注册表的定义：`ANTHROPIC_API_KEY` →
`ANTHROPIC_AUTH_TOKEN` → `GOOGLE_API_KEY` → `OPENAI_API_KEY` → `MOONSHOT_API_KEY`。
如果均未设置，则回退到 **LOCAL 代理模式**（`--agent`，无需 API 密钥
—— 使用你的 Claude Pro / ChatGPT Plus 订阅）。

当密钥前缀有歧义时（Moonshot 密钥同样以 `sk-` 开头），可通过将
`SKILL_SEEKER_PROVIDER` 设置为 `anthropic`、`google`、`openai`、
`moonshot`（别名：`kimi`）来强制指定提供商：

```bash
export SKILL_SEEKER_PROVIDER=moonshot
```

### 任意 OpenAI 兼容提供商（OpenRouter、Groq、Cerebras、Mistral、NVIDIA NIM）

```bash
export OPENAI_API_KEY="<provider key>"
export OPENAI_BASE_URL="https://api.groq.com/openai/v1"   # provider endpoint
export OPENAI_MODEL="llama-3.3-70b-versatile"             # a model that provider offers
skill-seekers create <source>
```

| 提供商       | `OPENAI_BASE_URL`                     |
|--------------|---------------------------------------|
| OpenRouter   | `https://openrouter.ai/api/v1`        |
| Groq         | `https://api.groq.com/openai/v1`      |
| Cerebras     | `https://api.cerebras.ai/v1`          |
| Mistral      | `https://api.mistral.ai/v1`           |
| NVIDIA NIM   | `https://integrate.api.nvidia.com/v1` |

> 请务必设置 `OPENAI_MODEL` —— OpenAI 的默认模型（`gpt-4o`）在其他提供商上不存在。
> 确保没有设置更高优先级的密钥（如 `ANTHROPIC_API_KEY`），否则它会胜出。

### 使用订阅而非 API 额度（LOCAL 模式）

```bash
skill-seekers create <source> --agent codex    # ChatGPT Plus via Codex CLI
skill-seekers create <source> --agent claude   # Claude Pro/Max via Claude Code
```

---

## 路径与目录

### SKILL_SEEKERS_HOME

**用途：** Skill Seekers 数据的基础目录。

**默认值：**
- Linux/macOS：`~/.config/skill-seekers/`
- Windows：`%APPDATA%\skill-seekers\`

**用于：**
- 配置文件
- 工作流预设
- 缓存数据
- 检查点

**示例：**
```bash
export SKILL_SEEKERS_HOME=/opt/skill-seekers
```

---

### SKILL_SEEKERS_OUTPUT

**用途：** 技能的默认输出目录。

**默认值：** `./output/`

**使用者：**
- 所有抓取命令
- 打包输出
- 技能生成

**示例：**
```bash
export SKILL_SEEKERS_OUTPUT=/var/skills/output
```

---

### SKILL_SEEKERS_CONFIG_DIR

**用途：** 包含预设配置的目录。

**默认值：** `configs/`（相对于工作目录）

**示例：**
```bash
export SKILL_SEEKERS_CONFIG_DIR=/etc/skill-seekers/configs
```

---

## 抓取行为

### SKILL_SEEKERS_RATE_LIMIT

**用途：** HTTP 请求的默认速率限制。

**默认值：** `0.5`（秒）

**单位：** 请求之间的间隔秒数

**示例：**
```bash
# More aggressive (faster)
export SKILL_SEEKERS_RATE_LIMIT=0.2

# More conservative (slower)
export SKILL_SEEKERS_RATE_LIMIT=1.0
```

**覆盖方式：** 在每个命令中使用 `--rate-limit` 标志。

---

### SKILL_SEEKERS_MAX_PAGES

**用途：** 默认的最大抓取页数。

**默认值：** `500`

**示例：**
```bash
export SKILL_SEEKERS_MAX_PAGES=1000
```

**覆盖方式：** 使用 `--max-pages` 标志或配置文件。

---

### SKILL_SEEKERS_WORKERS

**用途：** 默认并行工作者数量。

**默认值：** `1`

**最大值：** `10`

**示例：**
```bash
export SKILL_SEEKERS_WORKERS=4
```

**覆盖方式：** 使用 `--workers` 标志。

---

### SKILL_SEEKERS_TIMEOUT

**用途：** HTTP 请求超时。

**默认值：** `30`（秒）

**示例：**
```bash
# For slow servers
export SKILL_SEEKERS_TIMEOUT=60
```

---

### SKILL_SEEKERS_USER_AGENT

**用途：** 自定义 User-Agent 请求头。

**默认值：** `Skill-Seekers/3.7.0`

**示例：**
```bash
export SKILL_SEEKERS_USER_AGENT="MyBot/1.0 (contact@example.com)"
```

---

## 增强设置

### SKILL_SEEKER_AGENT

**用途：** 用于增强以及 scan 检测/生成的默认本地编码代理。

**默认值：** `claude`

**可选值：** `claude`、`codex`、`copilot`、`opencode`、`kimi`、`custom`，以及 IDE 模式别名（`cursor`、`windsurf`、`cline`、`continue`）

**使用者：**
- `skill-seekers enhance`
- `skill-seekers scan`（可在单次调用中通过 `--agent` 覆盖）

**示例：**
```bash
export SKILL_SEEKER_AGENT=cursor
```

---

### SKILL_SEEKER_AGENT_CMD

**用途：** `--agent custom`（LOCAL 模式）的自定义 CLI 命令模板。

**使用者：** 当 `SKILL_SEEKER_AGENT=custom` 时的 `skill-seekers create` / `scan` / `enhance`。

**示例：**
```bash
export SKILL_SEEKER_AGENT=custom
export SKILL_SEEKER_AGENT_CMD="my-llm-cli --prompt-file {prompt_file}"
```

---

### SKILL_SEEKER_PROVIDER

**用途：** 当密钥前缀检测有歧义时强制指定 API 提供商
（Moonshot 密钥同样以 `sk-` 开头，否则会被识别为 OpenAI）。

**可选值：** `anthropic`、`google`、`openai`、`moonshot`（别名：`kimi`）

**示例：**
```bash
export SKILL_SEEKER_PROVIDER=moonshot
```

---

### SKILL_SEEKER_MODEL

**用途：** API 模式增强的全局模型覆盖（优先于下方所有
按提供商的模型变量）。

**示例：**
```bash
export SKILL_SEEKER_MODEL=llama-3.3-70b-versatile
```

---

### 按提供商的模型覆盖

仅在未设置 `SKILL_SEEKER_MODEL` 时使用。每个变量都会回退到对应提供商的默认值。

| 变量              | 提供商             | 默认值（未设置时）          |
|-------------------|--------------------|-----------------------------|
| `ANTHROPIC_MODEL` | Anthropic          | `claude-sonnet-4-20250514`  |
| `OPENAI_MODEL`    | OpenAI/兼容        | `gpt-4o`                    |
| `GOOGLE_MODEL`    | Gemini             | `gemini-2.0-flash`          |
| `MOONSHOT_MODEL`  | Moonshot/Kimi      | `moonshot-v1-auto`          |

```bash
export OPENAI_MODEL=llama-3.3-70b-versatile
```

---

### SKILL_SEEKER_ENHANCE_TIMEOUT

**用途：** AI 增强操作的超时时间（秒）。

**默认值：** `2700`（45 分钟）

**特殊值：** `unlimited`、`none` 或 `0` 会映射为 24 小时上限。

**示例：**
```bash
# For large skills
export SKILL_SEEKER_ENHANCE_TIMEOUT=3600

# No practical limit
export SKILL_SEEKER_ENHANCE_TIMEOUT=unlimited
```

---

### SKILL_SEEKER_ENHANCE_ACTIVE

**用途：** LOCAL 代理增强的递归保护。Skill Seekers 会在它生成的每个
本地代理的环境中将此变量设置为 `1`（所有生成路径都如此）；当该变量
已被设置时，LOCAL 增强会拒绝再生成嵌套代理。通常你不需要自己设置它
—— 仅当你将 Skill Seekers 包装在另一个代理内、且希望抑制增强时才需要。

**示例：**
```bash
export SKILL_SEEKER_ENHANCE_ACTIVE=1   # suppress nested local-agent spawns
```

---

## GitHub 配置

### GITHUB_API_URL

**用途：** 自定义 GitHub API 端点。

**默认值：** `https://api.github.com`

**使用场景：** GitHub Enterprise Server。

**示例：**
```bash
export GITHUB_API_URL=https://github.company.com/api/v3
```

---

### GITHUB_ENTERPRISE_TOKEN

**用途：** GitHub Enterprise 的独立令牌。

**使用场景：** 为 github.com 和企业实例使用不同的令牌。

**示例：**
```bash
export GITHUB_TOKEN=ghp_...           # github.com
export GITHUB_ENTERPRISE_TOKEN=...   # enterprise
```

---

## 向量数据库设置

### CHROMA_URL

**用途：** ChromaDB 服务器 URL。

**默认值：** `http://localhost:8000`

**使用者：**
- `skill-seekers upload --target chroma`
- `export_to_chroma` MCP 工具

**示例：**
```bash
export CHROMA_URL=http://chroma.example.com:8000
```

---

### CHROMA_PERSIST_DIRECTORY

**用途：** ChromaDB 持久化的本地目录。

**默认值：** `./chroma_db/`

**示例：**
```bash
export CHROMA_PERSIST_DIRECTORY=/var/lib/chroma
```

---

### WEAVIATE_URL

**用途：** Weaviate 服务器 URL。

**默认值：** `http://localhost:8080`

**使用者：**
- `skill-seekers upload --target weaviate`
- `export_to_weaviate` MCP 工具

**示例：**
```bash
export WEAVIATE_URL=https://weaviate.example.com
```

---

### WEAVIATE_API_KEY

**用途：** 用于身份验证的 Weaviate API 密钥。

**使用者：**
- Weaviate Cloud
- 启用认证的 Weaviate 实例

**示例：**
```bash
export WEAVIATE_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

### QDRANT_URL

**用途：** Qdrant 服务器 URL。

**默认值：** `http://localhost:6333`

**示例：**
```bash
export QDRANT_URL=http://qdrant.example.com:6333
```

---

### QDRANT_API_KEY

**用途：** 用于身份验证的 Qdrant API 密钥。

**示例：**
```bash
export QDRANT_API_KEY=xxxxxxxxxxxxxxxx
```

---

## 调试与开发

### SKILL_SEEKERS_DEBUG

**用途：** 启用调试日志。

**可选值：** `1`、`true`、`yes`

**等效于：** `--verbose` 标志

**示例：**
```bash
export SKILL_SEEKERS_DEBUG=1
```

---

### SKILL_SEEKERS_LOG_LEVEL

**用途：** 设置日志级别。

**默认值：** `INFO`

**可选值：** `DEBUG`、`INFO`、`WARNING`、`ERROR`、`CRITICAL`

**示例：**
```bash
export SKILL_SEEKERS_LOG_LEVEL=DEBUG
```

---

### SKILL_SEEKERS_LOG_FILE

**用途：** 将日志写入文件而非 stdout。

**示例：**
```bash
export SKILL_SEEKERS_LOG_FILE=/var/log/skill-seekers.log
```

---

### SKILL_SEEKERS_CACHE_DIR

**用途：** 自定义缓存目录。

**默认值：** `~/.cache/skill-seekers/`

**示例：**
```bash
export SKILL_SEEKERS_CACHE_DIR=/tmp/skill-seekers-cache
```

---

### SKILL_SEEKERS_NO_CACHE

**用途：** 禁用缓存。

**可选值：** `1`、`true`、`yes`

**示例：**
```bash
export SKILL_SEEKERS_NO_CACHE=1
```

---

## MCP 服务器设置

### MCP_TRANSPORT

**用途：** 默认的 MCP 传输模式。

**默认值：** `stdio`

**可选值：** `stdio`、`http`

**示例：**
```bash
export MCP_TRANSPORT=http
```

**覆盖方式：** 使用 `--transport` 标志。

---

### MCP_PORT

**用途：** 默认的 MCP HTTP 端口。

**默认值：** `8765`

**示例：**
```bash
export MCP_PORT=8080
```

**覆盖方式：** 使用 `--port` 标志。

---

### MCP_HOST

**用途：** 默认的 MCP HTTP 主机。

**默认值：** `127.0.0.1`

**示例：**
```bash
export MCP_HOST=0.0.0.0
```

**覆盖方式：** 使用 `--host` 标志。

---

## 示例

### 开发环境

```bash
# Debug mode
export SKILL_SEEKERS_DEBUG=1
export SKILL_SEEKERS_LOG_LEVEL=DEBUG

# Custom paths
export SKILL_SEEKERS_HOME=./.skill-seekers
export SKILL_SEEKERS_OUTPUT=./output

# Faster scraping for testing
export SKILL_SEEKERS_RATE_LIMIT=0.1
export SKILL_SEEKERS_MAX_PAGES=50
```

### 生产环境

```bash
# API keys
export ANTHROPIC_API_KEY=sk-ant-...
export GITHUB_TOKEN=ghp_...

# Custom output directory
export SKILL_SEEKERS_OUTPUT=/var/www/skills

# Conservative scraping
export SKILL_SEEKERS_RATE_LIMIT=1.0
export SKILL_SEEKERS_WORKERS=2

# Logging
export SKILL_SEEKERS_LOG_FILE=/var/log/skill-seekers.log
export SKILL_SEEKERS_LOG_LEVEL=WARNING
```

### CI/CD 环境

```bash
# Non-interactive
export SKILL_SEEKERS_LOG_LEVEL=ERROR

# API keys from secrets
export ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY_SECRET}
export GITHUB_TOKEN=${GITHUB_TOKEN_SECRET}

# Fresh runs (no cache)
export SKILL_SEEKERS_NO_CACHE=1
```

### 多平台设置

```bash
# All API keys
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=AIza...
export OPENAI_API_KEY=sk-...
export GITHUB_TOKEN=ghp_...

# Vector databases
export CHROMA_URL=http://localhost:8000
export WEAVIATE_URL=http://localhost:8080
export WEAVIATE_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

## 配置文件

环境变量也可以在 `.env` 文件中设置：

```bash
# .env file
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=ghp_...
SKILL_SEEKERS_OUTPUT=./output
SKILL_SEEKERS_RATE_LIMIT=0.5
```

加载方式：
```bash
# Automatically loaded if python-dotenv is installed
# Or manually:
export $(cat .env | xargs)
```

---

## 优先级顺序

设置按以下顺序应用（后者覆盖前者）：

1. 默认值
2. 环境变量
3. 配置文件
4. 命令行标志

示例：
```bash
# Default: rate_limit = 0.5
export SKILL_SEEKERS_RATE_LIMIT=1.0  # Env var overrides default
# Config file: rate_limit = 0.2      # Config overrides env
skill-seekers create --rate-limit 2.0  # Flag overrides all
```

---

## 安全最佳实践

### 切勿提交 API 密钥

```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
```

### 使用密钥管理

```bash
# macOS Keychain
export ANTHROPIC_API_KEY=$(security find-generic-password -s "anthropic-api" -w)

# Linux Secret Service (with secret-tool)
export ANTHROPIC_API_KEY=$(secret-tool lookup service anthropic)

# 1Password CLI
export ANTHROPIC_API_KEY=$(op read "op://vault/anthropic/credential")
```

### 文件权限

```bash
# Restrict .env file
chmod 600 .env
```

---

## 故障排除

### 变量未被识别

```bash
# Check if set
echo $ANTHROPIC_API_KEY

# Check in Python
python -c "import os; print(os.getenv('ANTHROPIC_API_KEY'))"
```

### 优先级问题

```bash
# See effective configuration
skill-seekers config --show
```

### 路径展开

```bash
# Use full path or expand tilde
export SKILL_SEEKERS_HOME=$HOME/.skill-seekers
# NOT: ~/.skill-seekers (may not expand in all shells)
```

---

## 另请参阅

- [CLI 参考](CLI_REFERENCE.md) - 命令参考
- [配置格式](CONFIG_FORMAT.md) - JSON 配置

---

*平台相关的设置请参阅[安装指南](../getting-started/01-installation.md)*
