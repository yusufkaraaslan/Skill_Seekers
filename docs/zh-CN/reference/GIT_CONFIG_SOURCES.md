# 基于 Git 的配置源 - 完整指南

**版本：** v3.6.0
**功能：** A1.9 - 多源 Git 仓库支持
**最后更新：** 2025 年 12 月 21 日

---

## 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [架构](#架构)
- [MCP 工具参考](#mcp-工具参考)
- [身份验证](#身份验证)
- [使用场景](#使用场景)
- [最佳实践](#最佳实践)
- [故障排除](#故障排除)
- [高级主题](#高级主题)

---

## 概述

### 这个功能是什么？

基于 Git 的配置源允许你除了公共 API 之外，还能从**私有/团队 git 仓库**获取配置文件。这解锁了：

- 🔐 **私有配置** - 公司/内部文档
- 👥 **团队协作** - 在 3-5 人团队中共享配置
- 🏢 **企业规模** - 支持 500+ 开发者
- 📦 **自定义集合** - 精选的配置仓库
- 🌐 **去中心化** - 类似 npm（公共 + 私有注册表）

### 工作原理

```
User → fetch_config(source="team", config_name="react-custom")
    ↓
SourceManager (~/.skill-seekers/sources.json)
    ↓
GitConfigRepo (clone/pull with GitPython)
    ↓
Local cache (~/.skill-seekers/cache/team/)
    ↓
Config JSON returned
```

### 三种模式

1. **API 模式**（现有，未变化）
   - `fetch_config(config_name="react")`
   - 从 api.skillseekersweb.com 获取

2. **源模式**（新增 - 推荐）
   - `fetch_config(source="team", config_name="react-custom")`
   - 使用已注册的 git 源

3. **Git URL 模式**（新增 - 一次性）
   - `fetch_config(git_url="https://...", config_name="react-custom")`
   - 直接克隆，无需注册

---

## 快速开始

### 1. 设置身份验证

```bash
# GitHub
export GITHUB_TOKEN=ghp_your_token_here

# GitLab
export GITLAB_TOKEN=glpat_your_token_here

# Bitbucket
export BITBUCKET_TOKEN=your_token_here
```

### 2. 注册一个源

使用 MCP 工具（推荐）：

```python
add_config_source(
    name="team",
    git_url="https://github.com/mycompany/skill-configs.git",
    source_type="github",  # Optional, auto-detected
    token_env="GITHUB_TOKEN",  # Optional, auto-detected
    branch="main",  # Optional, default: "main"
    priority=100  # Optional, lower = higher priority
)
```

### 3. 获取配置

```python
# From registered source
fetch_config(source="team", config_name="react-custom")

# List available sources
list_config_sources()

# Remove when done
remove_config_source(name="team")
```

### 4. 使用示例仓库快速测试

```bash
cd /path/to/Skill_Seekers

# Run E2E test
python3 configs/example-team/test_e2e.py

# Or test manually
add_config_source(
    name="example",
    git_url="file://$(pwd)/configs/example-team",
    branch="master"
)

fetch_config(source="example", config_name="react-custom")
```

---

## 架构

### 存储位置

**源注册表：**
```
~/.skill-seekers/sources.json
```

示例内容：
```json
{
  "version": "1.0",
  "sources": [
    {
      "name": "team",
      "git_url": "https://github.com/myorg/configs.git",
      "type": "github",
      "token_env": "GITHUB_TOKEN",
      "branch": "main",
      "enabled": true,
      "priority": 1,
      "added_at": "2025-12-21T10:00:00Z",
      "updated_at": "2025-12-21T10:00:00Z"
    }
  ]
}
```

**缓存目录：**
```
$SKILL_SEEKERS_CACHE_DIR  (default: ~/.skill-seekers/cache/)
```

结构：
```
~/.skill-seekers/
├── sources.json       # Source registry
└── cache/             # Git clones
    ├── team/          # One directory per source
    │   ├── .git/
    │   ├── react-custom.json
    │   └── vue-internal.json
    └── company/
        ├── .git/
        └── internal-api.json
```

### Git 策略

- **浅克隆**：`git clone --depth 1 --single-branch`
  - 快 10-50 倍
  - 占用磁盘空间极小
  - 没有历史记录，只有最新提交

- **自动 pull**：自动更新缓存
  - 每次获取时检查变更
  - 使用 `refresh=true` 强制重新克隆

- **配置发现**：递归扫描 `*.json` 文件
  - 没有硬编码路径
  - 仓库结构灵活
  - 排除 `.git` 目录

---

## MCP 工具参考

### add_config_source

将一个 git 仓库注册为配置源。

**参数：**
- `name`（必填）：源标识符（小写、字母数字、连字符/下划线）
- `git_url`（必填）：Git 仓库 URL（HTTPS 或 SSH）
- `source_type`（可选）："github"、"gitlab"、"gitea"、"bitbucket"、"custom"（从 URL 自动检测）
- `token_env`（可选）：token 的环境变量名（根据类型自动检测）
- `branch`（可选）：Git 分支（默认："main"）
- `priority`（可选）：优先级数字（默认：100，越小优先级越高）
- `enabled`（可选）：源是否启用（默认：true）

**返回：**
- 包含注册时间戳的源详细信息

**示例：**

```python
# Minimal (auto-detects everything)
add_config_source(
    name="team",
    git_url="https://github.com/myorg/configs.git"
)

# Full parameters
add_config_source(
    name="company",
    git_url="https://gitlab.company.com/platform/configs.git",
    source_type="gitlab",
    token_env="GITLAB_COMPANY_TOKEN",
    branch="develop",
    priority=1,
    enabled=true
)

# SSH URL (auto-converts to HTTPS with token)
add_config_source(
    name="team",
    git_url="git@github.com:myorg/configs.git",
    token_env="GITHUB_TOKEN"
)
```

### list_config_sources

列出所有已注册的配置源。

**参数：**
- `enabled_only`（可选）：仅显示已启用的源（默认：false）

**返回：**
- 按优先级排序的源列表

**示例：**

```python
# List all sources
list_config_sources()

# List only enabled sources
list_config_sources(enabled_only=true)
```

**输出：**
```
📋 Config Sources (2 total)

✓ **team**
  📁 https://github.com/myorg/configs.git
  🔖 Type: github | 🌿 Branch: main
  🔑 Token: GITHUB_TOKEN | ⚡ Priority: 1
  🕒 Added: 2025-12-21 10:00:00

✓ **company**
  📁 https://gitlab.company.com/configs.git
  🔖 Type: gitlab | 🌿 Branch: develop
  🔑 Token: GITLAB_TOKEN | ⚡ Priority: 2
  🕒 Added: 2025-12-21 11:00:00
```

### remove_config_source

移除一个已注册的配置源。

**参数：**
- `name`（必填）：源标识符

**返回：**
- 成功/失败消息

**注意：** 不会删除已缓存的 git 仓库数据。要释放磁盘空间，请手动删除 `~/.skill-seekers/cache/{source_name}/`

**示例：**

```python
remove_config_source(name="team")
```

### fetch_config

从 API、git URL 或命名源获取配置。

**模式 1：命名源（最高优先级）**

```python
fetch_config(
    source="team",  # Use registered source
    config_name="react-custom",
    destination="configs/",  # Optional
    branch="main",  # Optional, overrides source default
    refresh=false  # Optional, force re-clone
)
```

**模式 2：直接 Git URL**

```python
fetch_config(
    git_url="https://github.com/myorg/configs.git",
    config_name="react-custom",
    branch="main",  # Optional
    token="ghp_token",  # Optional, prefer env vars
    destination="configs/",  # Optional
    refresh=false  # Optional
)
```

**模式 3：API（现有，未变化）**

```python
fetch_config(
    config_name="react",
    destination="configs/"  # Optional
)

# Or list available
fetch_config(list_available=true)
```

---

## 身份验证

### 仅使用环境变量

Token **只**存储在环境变量中。这是：
- ✅ **安全** - 不在文件中，不在 git 中
- ✅ **标准** - 与 GitHub CLI、Docker 等一致
- ✅ **临时** - 注销时清除
- ✅ **灵活** - 不同服务使用不同 token

### 创建 Token

**GitHub：**
1. 访问 https://github.com/settings/tokens
2. 生成新 token（classic）
3. 选择 scope：`repo`（用于私有仓库）
4. 复制 token：`ghp_xxxxxxxxxxxxx`
5. 导出：`export GITHUB_TOKEN=ghp_xxxxxxxxxxxxx`

**GitLab：**
1. 访问 https://gitlab.com/-/profile/personal_access_tokens
2. 创建具有 `read_repository` scope 的 token
3. 复制 token：`glpat-xxxxxxxxxxxxx`
4. 导出：`export GITLAB_TOKEN=glpat-xxxxxxxxxxxxx`

**Bitbucket：**
1. 访问 https://bitbucket.org/account/settings/app-passwords/
2. 创建具有 `Repositories: Read` 权限的应用密码
3. 复制密码
4. 导出：`export BITBUCKET_TOKEN=your_password`

### 持久化 Token

添加到你的 shell 配置文件（`~/.bashrc`、`~/.zshrc` 等）：

```bash
# GitHub token
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxx

# GitLab token
export GITLAB_TOKEN=glpat-xxxxxxxxxxxxx

# Company GitLab (separate token)
export GITLAB_COMPANY_TOKEN=glpat-yyyyyyyyyyyyy
```

然后：`source ~/.bashrc`

### Token 注入

GitConfigRepo 会自动：
1. 将 SSH URL 转换为 HTTPS
2. 将 token 注入 URL
3. 使用 token 进行身份验证

**示例：**
- 输入：`git@github.com:myorg/repo.git` + token `ghp_xxx`
- 输出：`https://ghp_xxx@github.com/myorg/repo.git`

---

## 使用场景

### 小型团队（3-5 人）

**场景：** 前端团队需要用于内部文档的自定义 React 配置。

**设置：**

```bash
# 1. Team lead creates repo
gh repo create myteam/skill-configs --private

# 2. Add configs
cd myteam-skill-configs
cp ../Skill_Seekers/configs/react.json ./react-internal.json

# Edit for internal docs:
# - Change base_url to internal docs site
# - Adjust selectors for company theme
# - Customize categories

git add . && git commit -m "Add internal React config" && git push

# 3. Team members register (one-time)
export GITHUB_TOKEN=ghp_their_token
add_config_source(
    name="team",
    git_url="https://github.com/myteam/skill-configs.git"
)

# 4. Daily usage
fetch_config(source="team", config_name="react-internal")
```

**优势：**
- ✅ 团队共享配置
- ✅ 版本控制
- ✅ 公司私有
- ✅ 更新方便（git push）

### 企业（500+ 开发者）

**场景：** 拥有多个团队、内部文档的大公司，需要基于优先级的配置解析。

**设置：**

```bash
# IT pre-configures sources for all developers
# (via company setup script or documentation)

# 1. Platform team configs (highest priority)
add_config_source(
    name="platform",
    git_url="https://gitlab.company.com/platform/skill-configs.git",
    source_type="gitlab",
    token_env="GITLAB_COMPANY_TOKEN",
    priority=1
)

# 2. Mobile team configs
add_config_source(
    name="mobile",
    git_url="https://gitlab.company.com/mobile/skill-configs.git",
    source_type="gitlab",
    token_env="GITLAB_COMPANY_TOKEN",
    priority=2
)

# 3. Public/official configs (fallback)
# (API mode, no registration needed, lowest priority)
```

**开发者使用：**

```python
# Automatically finds config with highest priority
fetch_config(config_name="platform-api")  # Found in platform source
fetch_config(config_name="react-native")  # Found in mobile source
fetch_config(config_name="react")  # Falls back to public API
```

**优势：**
- ✅ 集中式配置管理
- ✅ 团队特定的覆盖
- ✅ 回退到公共配置
- ✅ 基于优先级的解析
- ✅ 可扩展到数百名开发者

### 开源项目

**场景：** 开源项目想为贡献者提供精选配置。

**设置：**

```bash
# 1. Create public repo
gh repo create myproject/skill-configs --public

# 2. Add configs for project stack
- react.json (frontend)
- django.json (backend)
- postgres.json (database)
- nginx.json (deployment)

# 3. Contributors use directly (no token needed for public repos)
add_config_source(
    name="myproject",
    git_url="https://github.com/myproject/skill-configs.git"
)

fetch_config(source="myproject", config_name="react")
```

**优势：**
- ✅ 为项目精选的配置
- ✅ 不依赖 API
- ✅ 社区可通过 PR 贡献
- ✅ 版本控制

---

## 最佳实践

### 配置命名

**好的命名：**
- `react-internal.json` - 用途清晰
- `api-v2.json` - 包含版本
- `platform-auth.json` - 主题明确

**不好的命名：**
- `config1.json` - 太泛泛
- `react.json` - 与官方配置冲突
- `test.json` - 缺乏描述性

### 仓库结构

**扁平结构（小型仓库推荐）：**
```
skill-configs/
├── README.md
├── react-internal.json
├── vue-internal.json
└── api-v2.json
```

**分类组织（大型仓库推荐）：**
```
skill-configs/
├── README.md
├── frontend/
│   ├── react-internal.json
│   └── vue-internal.json
├── backend/
│   ├── django-api.json
│   └── fastapi-platform.json
└── mobile/
    ├── react-native.json
    └── flutter.json
```

**注意：** 配置发现是递归的，所以两种结构都可以！

### 源优先级

数字越小优先级越高。使用合理的默认值：

- `1-10`：关键/覆盖配置
- `50-100`：团队配置（默认：100）
- `1000+`：回退/实验性配置

**示例：**
```python
# Override official React config with internal version
add_config_source(name="team", ..., priority=1)  # Checked first
# Official API is checked last (priority: infinity)
```

### 安全

✅ **应该：**
- 使用环境变量存储 token
- 敏感配置使用私有仓库
- 定期轮换 token
- 使用细粒度 token（尽可能只读）

❌ **不应该：**
- 把 token 提交到 git
- 在人员之间共享 token
- 团队使用个人 token（应使用服务账号）
- 把 token 存储在配置文件中

### 维护

**日常任务：**
```bash
# Update configs in repo
cd myteam-skill-configs
# Edit configs...
git commit -m "Update React config" && git push

# Developers get updates automatically on next fetch
fetch_config(source="team", config_name="react-internal")
# ^--- Auto-pulls latest changes
```

**强制刷新：**
```python
# Delete cache and re-clone
fetch_config(source="team", config_name="react-internal", refresh=true)
```

**清理旧源：**
```bash
# Remove unused sources
remove_config_source(name="old-team")

# Free disk space
rm -rf ~/.skill-seekers/cache/old-team/
```

---

## 故障排除

### 身份验证失败

**错误：** "Authentication failed for https://github.com/org/repo.git"

**解决方案：**
1. 检查 token 已设置：
   ```bash
   echo $GITHUB_TOKEN  # Should show token
   ```

2. 验证 token 具有正确的权限：
   - GitHub：私有仓库需要 `repo` scope
   - GitLab：`read_repository` scope

3. 检查 token 是否过期：
   - 必要时重新生成

4. 尝试直接访问：
   ```bash
   git clone https://$GITHUB_TOKEN@github.com/org/repo.git test-clone
   ```

### 找不到配置

**错误：** "Config 'react' not found in repository. Available configs: django, vue"

**解决方案：**
1. 列出可用的配置：
   ```python
   # Shows what's actually in the repo
   list_config_sources()
   ```

2. 检查配置文件确实存在于仓库中：
   ```bash
   # Clone locally and inspect
   git clone <git_url> temp-inspect
   find temp-inspect -name "*.json"
   ```

3. 验证配置名称（不区分大小写）：
   - `react` 可匹配 `React.json` 或 `react.json`

### 克隆缓慢

**问题：** 仓库克隆需要数分钟。

**解决方案：**
1. 浅克隆已默认启用（depth=1）

2. 检查仓库大小：
   ```bash
   # See repo size
   gh repo view owner/repo --json diskUsage
   ```

3. 如果非常大（>100MB），考虑：
   - 将配置拆分到不同仓库
   - 使用稀疏检出（sparse checkout）
   - 联系 IT 优化仓库

### 缓存问题

**问题：** 仓库已更新但仍获取到旧配置。

**解决方案：**
1. 强制刷新：
   ```python
   fetch_config(source="team", config_name="react", refresh=true)
   ```

2. 手动清除缓存：
   ```bash
   rm -rf ~/.skill-seekers/cache/team/
   ```

3. 检查自动 pull 是否生效：
   ```bash
   cd ~/.skill-seekers/cache/team
   git log -1  # Shows latest commit
   ```

---

## 高级主题

### 多个 Git 账号

为不同的仓库使用不同的 token：

```bash
# Personal GitHub
export GITHUB_TOKEN=ghp_personal_xxx

# Work GitHub
export GITHUB_WORK_TOKEN=ghp_work_yyy

# Company GitLab
export GITLAB_COMPANY_TOKEN=glpat-zzz
```

使用特定 token 注册：
```python
add_config_source(
    name="personal",
    git_url="https://github.com/myuser/configs.git",
    token_env="GITHUB_TOKEN"
)

add_config_source(
    name="work",
    git_url="https://github.com/mycompany/configs.git",
    token_env="GITHUB_WORK_TOKEN"
)
```

### 自定义缓存位置

设置自定义缓存目录：

```bash
export SKILL_SEEKERS_CACHE_DIR=/mnt/large-disk/skill-seekers-cache
```

或传递给 GitConfigRepo：
```python
from skill_seekers.mcp.git_repo import GitConfigRepo

gr = GitConfigRepo(cache_dir="/custom/path/cache")
```

### SSH URL

SSH URL 会自动转换为 HTTPS + token：

```python
# Input
add_config_source(
    name="team",
    git_url="git@github.com:myorg/configs.git",
    token_env="GITHUB_TOKEN"
)

# Internally becomes
# https://ghp_xxx@github.com/myorg/configs.git
```

### 优先级解析

当同一配置存在于多个源中时：

```python
add_config_source(name="team", ..., priority=1)     # Checked first
add_config_source(name="company", ..., priority=2)  # Checked second
# API mode is checked last (priority: infinity)

fetch_config(config_name="react")
# 1. Checks team source
# 2. If not found, checks company source
# 3. If not found, falls back to API
```

### CI/CD 集成

在 GitHub Actions 中使用：

```yaml
name: Generate Skills

on: push

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Skill Seekers
        run: pip install skill-seekers

      - name: Register config source
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 << EOF
          from skill_seekers.mcp.source_manager import SourceManager
          sm = SourceManager()
          sm.add_source(
              name="team",
              git_url="https://github.com/myorg/configs.git"
          )
          EOF

      - name: Fetch and use config
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # Use MCP fetch_config or direct Python
          skill-seekers create --config <fetched_config>
```

---

## API 参考

### GitConfigRepo 类

**位置：** `src/skill_seekers/mcp/git_repo.py`

**方法：**

```python
def __init__(cache_dir: Optional[str] = None)
    """Initialize with optional cache directory."""

def clone_or_pull(
    source_name: str,
    git_url: str,
    branch: str = "main",
    token: Optional[str] = None,
    force_refresh: bool = False
) -> Path:
    """Clone if not cached, else pull latest changes."""

def find_configs(repo_path: Path) -> list[Path]:
    """Find all *.json files in repository."""

def get_config(repo_path: Path, config_name: str) -> dict:
    """Load specific config by name."""

@staticmethod
def inject_token(git_url: str, token: str) -> str:
    """Inject token into git URL."""

@staticmethod
def validate_git_url(git_url: str) -> bool:
    """Validate git URL format."""
```

### SourceManager 类

**位置：** `src/skill_seekers/mcp/source_manager.py`

**方法：**

```python
def __init__(config_dir: Optional[str] = None)
    """Initialize with optional config directory."""

def add_source(
    name: str,
    git_url: str,
    source_type: str = "github",
    token_env: Optional[str] = None,
    branch: str = "main",
    priority: int = 100,
    enabled: bool = True
) -> dict:
    """Add or update config source."""

def get_source(name: str) -> dict:
    """Get source by name."""

def list_sources(enabled_only: bool = False) -> list[dict]:
    """List all sources."""

def remove_source(name: str) -> bool:
    """Remove source."""

def update_source(name: str, **kwargs) -> dict:
    """Update specific fields."""
```

---

## 另请参阅

- [README.md](../README.md) - 主文档
- [MCP_SETUP.md](MCP_SETUP.md) - MCP 服务器设置
- [UNIFIED_SCRAPING.md](UNIFIED_SCRAPING.md) - 多源抓取
- [configs/example-team/](../configs/example-team/) - 示例仓库

---

## 变更日志

### v2.2.0（2025-12-21）
- 基于 git 的配置源首次发布
- 3 种获取模式：API、Git URL、命名源
- 4 个 MCP 工具：add/list/remove/fetch
- 支持 GitHub、GitLab、Bitbucket、Gitea
- 浅克隆优化
- 基于优先级的解析
- 83 个测试（100% 通过）

---

**有问题？** 请在 https://github.com/yusufkaraaslan/Skill_Seekers/issues 提交 issue
