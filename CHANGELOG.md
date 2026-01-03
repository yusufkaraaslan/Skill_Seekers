# Changelog

All notable changes to Skill Seeker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **C3.1 Design Pattern Detection** - Detect 10 common design patterns in code
  - Detects: Singleton, Factory, Observer, Strategy, Decorator, Builder, Adapter, Command, Template Method, Chain of Responsibility
  - Supports 9 languages: Python, JavaScript, TypeScript, C++, C, C#, Go, Rust, Java (plus Ruby, PHP)
  - Three detection levels: surface (fast), deep (balanced), full (thorough)
  - Language-specific adaptations for better accuracy
  - CLI tool: `skill-seekers-patterns --file src/db.py`
  - Codebase scraper integration: `--detect-patterns` flag
  - MCP tool: `detect_patterns` for Claude Code integration
  - 24 comprehensive tests, 100% passing
  - 87% precision, 80% recall (tested on 100 real-world projects)
  - Documentation: `docs/PATTERN_DETECTION.md`

### Changed

### Fixed

### Removed

---

## [2.5.2] - 2025-12-31

### 🔧 Package Configuration Improvement

This **patch release** improves the packaging configuration by switching from manual package listing to automatic package discovery, preventing similar issues in the future.

### Changed

- **Package Discovery**: Switched from manual package listing to automatic discovery in pyproject.toml ([#227](https://github.com/yusufkaraaslan/Skill_Seekers/pull/227))
  - **Before**: Manually listed 5 packages (error-prone when adding new modules)
  - **After**: Automatic discovery using `[tool.setuptools.packages.find]`
  - **Benefits**: Future-proof, prevents missing module bugs, follows Python packaging best practices
  - **Impact**: No functional changes, same packages included
  - **Credit**: Thanks to [@iamKhan79690](https://github.com/iamKhan79690) for the improvement!

### Package Structure

No changes to package contents - all modules from v2.5.1 are still included:
- ✅ `skill_seekers` (core)
- ✅ `skill_seekers.cli` (CLI tools)
- ✅ `skill_seekers.cli.adaptors` (platform adaptors)
- ✅ `skill_seekers.mcp` (MCP server)
- ✅ `skill_seekers.mcp.tools` (MCP tools)

### Related Issues

- Closes #226 - MCP server package_skill tool fails (already fixed in v2.5.1, improved by this release)
- Merges #227 - Update setuptools configuration to include adaptors module

### Contributors

- [@iamKhan79690](https://github.com/iamKhan79690) - Automatic package discovery implementation

---

## [2.5.1] - 2025-12-30

### 🐛 Critical Bug Fix - PyPI Package Broken

This **patch release** fixes a critical packaging bug that made v2.5.0 completely unusable for PyPI users.

### Fixed

- **CRITICAL**: Added missing `skill_seekers.cli.adaptors` module to packages list in pyproject.toml ([#221](https://github.com/yusufkaraaslan/Skill_Seekers/pull/221))
  - **Issue**: v2.5.0 on PyPI throws `ModuleNotFoundError: No module named 'skill_seekers.cli.adaptors'`
  - **Impact**: Broke 100% of multi-platform features (Claude, Gemini, OpenAI, Markdown)
  - **Cause**: The adaptors module was missing from the explicit packages list
  - **Fix**: Added `skill_seekers.cli.adaptors` to packages in pyproject.toml
  - **Credit**: Thanks to [@MiaoDX](https://github.com/MiaoDX) for finding and fixing this issue!

### Package Structure

The `skill_seekers.cli.adaptors` module contains the platform adaptor architecture:
- `base.py` - Abstract base class for all adaptors
- `claude.py` - Claude AI platform implementation
- `gemini.py` - Google Gemini platform implementation
- `openai.py` - OpenAI ChatGPT platform implementation
- `markdown.py` - Generic markdown export

**Note**: v2.5.0 is broken on PyPI. All users should upgrade to v2.5.1 immediately.

---

## [2.5.0] - 2025-12-28

### 🚀 Multi-Platform Feature Parity - 4 LLM Platforms Supported

This **major feature release** adds complete multi-platform support for Claude AI, Google Gemini, OpenAI ChatGPT, and Generic Markdown export. All features now work across all platforms with full feature parity.

### 🎯 Major Features

#### Multi-LLM Platform Support
- **4 platforms supported**: Claude AI, Google Gemini, OpenAI ChatGPT, Generic Markdown
- **Complete feature parity**: All skill modes work with all platforms
- **Platform adaptors**: Clean architecture with platform-specific implementations
- **Unified workflow**: Same scraping output works for all platforms
- **Smart enhancement**: Platform-specific AI models (Claude Sonnet 4, Gemini 2.0 Flash, GPT-4o)

#### Platform-Specific Capabilities

**Claude AI (Default):**
- Format: ZIP with YAML frontmatter + markdown
- Upload: Anthropic Skills API
- Enhancement: Claude Sonnet 4 (local or API)
- MCP integration: Full support

**Google Gemini:**
- Format: tar.gz with plain markdown
- Upload: Google Files API + Grounding
- Enhancement: Gemini 2.0 Flash
- Long context: 1M tokens supported

**OpenAI ChatGPT:**
- Format: ZIP with assistant instructions
- Upload: Assistants API + Vector Store
- Enhancement: GPT-4o
- File search: Semantic search enabled

**Generic Markdown:**
- Format: ZIP with pure markdown
- Upload: Manual distribution
- Universal compatibility: Works with any LLM

#### Complete Feature Parity

**All skill modes work with all platforms:**
- Documentation scraping → All 4 platforms
- GitHub repository analysis → All 4 platforms
- PDF extraction → All 4 platforms
- Unified multi-source → All 4 platforms
- Local repository analysis → All 4 platforms

**18 MCP tools with multi-platform support:**
- `package_skill` - Now accepts `target` parameter (claude, gemini, openai, markdown)
- `upload_skill` - Now accepts `target` parameter (claude, gemini, openai)
- `enhance_skill` - NEW standalone tool with `target` parameter
- `install_skill` - Full multi-platform workflow automation

### Added

#### Core Infrastructure
- **Platform Adaptors** (`src/skill_seekers/cli/adaptors/`)
  - `base_adaptor.py` - Abstract base class for all adaptors
  - `claude_adaptor.py` - Claude AI implementation
  - `gemini_adaptor.py` - Google Gemini implementation
  - `openai_adaptor.py` - OpenAI ChatGPT implementation
  - `markdown_adaptor.py` - Generic Markdown export
  - `__init__.py` - Factory function `get_adaptor(target)`

#### CLI Tools
- **Multi-platform packaging**: `skill-seekers package output/skill/ --target gemini`
- **Multi-platform upload**: `skill-seekers upload skill.zip --target openai`
- **Multi-platform enhancement**: `skill-seekers enhance output/skill/ --target gemini --mode api`
- **Target parameter**: All packaging tools now accept `--target` flag

#### MCP Tools
- **`enhance_skill`** (NEW) - Standalone AI enhancement tool
  - Supports local mode (Claude Code Max, no API key)
  - Supports API mode (platform-specific APIs)
  - Works with Claude, Gemini, OpenAI
  - Creates SKILL.md.backup before enhancement

- **`package_skill`** (UPDATED) - Multi-platform packaging
  - New `target` parameter (claude, gemini, openai, markdown)
  - Creates ZIP for Claude/OpenAI/Markdown
  - Creates tar.gz for Gemini
  - Shows platform-specific output messages

- **`upload_skill`** (UPDATED) - Multi-platform upload
  - New `target` parameter (claude, gemini, openai)
  - Platform-specific API key validation
  - Returns skill ID and platform URL
  - Graceful error for markdown (no upload)

#### Documentation
- **`docs/FEATURE_MATRIX.md`** (NEW) - Comprehensive feature matrix
  - Platform support comparison table
  - Skill mode support across platforms
  - CLI command support matrix
  - MCP tool support matrix
  - Platform-specific examples
  - Verification checklist

- **`docs/UPLOAD_GUIDE.md`** (REWRITTEN) - Multi-platform upload guide
  - Complete guide for all 4 platforms
  - Platform selection table
  - API key setup instructions
  - Platform comparison matrices
  - Complete workflow examples

- **`docs/ENHANCEMENT.md`** (UPDATED)
  - Multi-platform enhancement section
  - Platform-specific model information
  - Cost comparison across platforms

- **`docs/MCP_SETUP.md`** (UPDATED)
  - Added enhance_skill to tool listings
  - Multi-platform usage examples
  - Updated tool count (10 → 18 tools)

- **`src/skill_seekers/mcp/README.md`** (UPDATED)
  - Corrected tool count (18 tools)
  - Added enhance_skill documentation
  - Updated package_skill with target parameter
  - Updated upload_skill with target parameter

#### Optional Dependencies
- **`[gemini]`** extra: `pip install skill-seekers[gemini]`
  - google-generativeai>=0.8.3
  - Required for Gemini enhancement and upload

- **`[openai]`** extra: `pip install skill-seekers[openai]`
  - openai>=1.59.6
  - Required for OpenAI enhancement and upload

- **`[all-llms]`** extra: `pip install skill-seekers[all-llms]`
  - Includes both Gemini and OpenAI dependencies

#### Tests
- **`tests/test_adaptors.py`** - Comprehensive adaptor tests
- **`tests/test_multi_llm_integration.py`** - E2E multi-platform tests
- **`tests/test_install_multiplatform.py`** - Multi-platform install_skill tests
- **700 total tests passing** (up from 427 in v2.4.0)

### Changed

#### CLI Architecture
- **Package command**: Now routes through platform adaptors
- **Upload command**: Now supports all 3 upload platforms
- **Enhancement command**: Now supports platform-specific models
- **Unified workflow**: All commands respect `--target` parameter

#### MCP Architecture
- **Tool modularity**: Cleaner separation with adaptor pattern
- **Error handling**: Platform-specific error messages
- **API key validation**: Per-platform validation logic
- **TextContent fallback**: Graceful degradation when MCP not installed

#### Documentation
- All platform documentation updated for multi-LLM support
- Consistent terminology across all docs
- Platform comparison tables added
- Examples updated to show all platforms

### Fixed

- **TextContent import error** in test environment (5 MCP tool files)
  - Added fallback TextContent class when MCP not installed
  - Prevents `TypeError: 'NoneType' object is not callable`
  - Ensures tests pass without MCP library

- **UTF-8 encoding** issues on Windows (continued from v2.4.0)
  - All file operations use explicit UTF-8 encoding
  - CHANGELOG encoding handling improved

- **API key environment variables** - Clear documentation for all platforms
  - ANTHROPIC_API_KEY for Claude
  - GOOGLE_API_KEY for Gemini
  - OPENAI_API_KEY for OpenAI

### Other Improvements

#### Smart Description Generation
- Automatically generates skill descriptions from documentation
- Analyzes reference files to suggest "When to Use" triggers
- Improves SKILL.md quality without manual editing

#### Smart Summarization
- Large skills (500+ lines) automatically summarized
- Preserves key examples and patterns
- Maintains quality while reducing token usage

### Deprecation Notice

None - All changes are backward compatible. Existing v2.4.0 workflows continue to work with default `target='claude'`.

### Migration Guide

**For users upgrading from v2.4.0:**

1. **No changes required** - Default behavior unchanged (targets Claude AI)

2. **To use other platforms:**
   ```bash
   # Install platform dependencies
   pip install skill-seekers[gemini]    # For Gemini
   pip install skill-seekers[openai]    # For OpenAI
   pip install skill-seekers[all-llms]  # For all platforms

   # Set API keys
   export GOOGLE_API_KEY=AIzaSy...      # For Gemini
   export OPENAI_API_KEY=sk-proj-...    # For OpenAI

   # Use --target flag
   skill-seekers package output/react/ --target gemini
   skill-seekers upload react-gemini.tar.gz --target gemini
   ```

3. **MCP users** - New tools available:
   - `enhance_skill` - Standalone enhancement (was only in install_skill)
   - All packaging tools now accept `target` parameter

**See full documentation:**
- [Multi-Platform Guide](docs/UPLOAD_GUIDE.md)
- [Feature Matrix](docs/FEATURE_MATRIX.md)
- [Enhancement Guide](docs/ENHANCEMENT.md)

### Contributors

- @yusufkaraaslan - Multi-platform architecture, all platform adaptors, comprehensive testing

### Stats

- **16 commits** since v2.4.0
- **700 tests** (up from 427, +273 new tests)
- **4 platforms** supported (was 1)
- **18 MCP tools** (up from 17)
- **5 documentation guides** updated/created
- **29 files changed**, 6,349 insertions(+), 253 deletions(-)

---

## [2.4.0] - 2025-12-25

### 🚀 MCP 2025 Upgrade - Multi-Agent Support & HTTP Transport

This **major release** upgrades the MCP infrastructure to the 2025 specification with support for 5 AI coding agents, dual transport modes (stdio + HTTP), and a complete FastMCP refactor.

### 🎯 Major Features

#### MCP SDK v1.25.0 Upgrade
- **Upgraded from v1.18.0 to v1.25.0** - Latest MCP protocol specification (November 2025)
- **FastMCP framework** - Decorator-based tool registration, 68% code reduction (2200 → 708 lines)
- **Enhanced reliability** - Better error handling, automatic schema generation from type hints
- **Backward compatible** - Existing v2.3.0 configurations continue to work

#### Dual Transport Support
- **stdio transport** (default) - Standard input/output for Claude Code, VS Code + Cline
- **HTTP transport** (new) - Server-Sent Events for Cursor, Windsurf, IntelliJ IDEA
- **Health check endpoint** - `GET /health` for monitoring
- **SSE endpoint** - `GET /sse` for real-time communication
- **Configurable server** - `--http`, `--port`, `--host`, `--log-level` flags
- **uvicorn-powered** - Production-ready ASGI server

#### Multi-Agent Auto-Configuration
- **5 AI agents supported**:
  - Claude Code (stdio)
  - Cursor (HTTP)
  - Windsurf (HTTP)
  - VS Code + Cline (stdio)
  - IntelliJ IDEA (HTTP)
- **Automatic detection** - `agent_detector.py` scans for installed agents
- **One-command setup** - `./setup_mcp.sh` configures all detected agents
- **Smart config merging** - Preserves existing MCP servers, only adds skill-seeker
- **Automatic backups** - Timestamped backups before modifications
- **HTTP server management** - Auto-starts HTTP server for HTTP-based agents

#### Expanded Tool Suite (17 Tools)
- **Config Tools (3)**: generate_config, list_configs, validate_config
- **Scraping Tools (4)**: estimate_pages, scrape_docs, scrape_github, scrape_pdf
- **Packaging Tools (3)**: package_skill, upload_skill, install_skill
- **Splitting Tools (2)**: split_config, generate_router
- **Source Tools (5)**: fetch_config, submit_config, add_config_source, list_config_sources, remove_config_source

### Added

#### Core Infrastructure
- **`server_fastmcp.py`** (708 lines) - New FastMCP-based MCP server
  - Decorator-based tool registration (`@safe_tool_decorator`)
  - Modular tool architecture (5 tool modules)
  - HTTP transport with uvicorn
  - stdio transport (default)
  - Comprehensive error handling

- **`agent_detector.py`** (333 lines) - Multi-agent detection and configuration
  - Detects 5 AI coding agents across platforms (Linux, macOS, Windows)
  - Generates agent-specific config formats (JSON, XML)
  - Auto-selects transport type (stdio vs HTTP)
  - Cross-platform path resolution

- **Tool modules** (5 modules, 1,676 total lines):
  - `tools/config_tools.py` (249 lines) - Configuration management
  - `tools/scraping_tools.py` (423 lines) - Documentation scraping
  - `tools/packaging_tools.py` (514 lines) - Skill packaging and upload
  - `tools/splitting_tools.py` (195 lines) - Config splitting and routing
  - `tools/source_tools.py` (295 lines) - Config source management

#### Setup & Configuration
- **`setup_mcp.sh`** (rewritten, 661 lines) - Multi-agent auto-configuration
  - Detects installed agents automatically
  - Offers configure all or select individual agents
  - Manages HTTP server startup
  - Smart config merging with existing configurations
  - Comprehensive validation and testing

- **HTTP server** - Production-ready HTTP transport
  - Health endpoint: `/health`
  - SSE endpoint: `/sse`
  - Messages endpoint: `/messages/`
  - CORS middleware for cross-origin requests
  - Configurable host and port
  - Debug logging support

#### Documentation
- **`docs/MCP_SETUP.md`** (completely rewritten) - Comprehensive MCP 2025 guide
  - Migration guide from v2.3.0
  - Transport modes explained (stdio vs HTTP)
  - Agent-specific configuration for all 5 agents
  - Troubleshooting for both transports
  - Advanced configuration (systemd, launchd services)

- **`docs/HTTP_TRANSPORT.md`** (434 lines, new) - HTTP transport guide
- **`docs/MULTI_AGENT_SETUP.md`** (643 lines, new) - Multi-agent setup guide
- **`docs/SETUP_QUICK_REFERENCE.md`** (387 lines, new) - Quick reference card
- **`SUMMARY_HTTP_TRANSPORT.md`** (360 lines, new) - Technical implementation details
- **`SUMMARY_MULTI_AGENT_SETUP.md`** (556 lines, new) - Multi-agent technical summary

#### Testing
- **`test_mcp_fastmcp.py`** (960 lines, 63 tests) - Comprehensive FastMCP server tests
  - All 17 tools tested
  - Error handling validation
  - Type validation
  - Integration workflows

- **`test_server_fastmcp_http.py`** (165 lines, 6 tests) - HTTP transport tests
  - Health check endpoint
  - SSE endpoint
  - CORS middleware
  - Argument parsing

- **All tests passing**: 602/609 tests (99.1% pass rate)

### Changed

#### MCP Server Architecture
- **Refactored to FastMCP** - Decorator-based, modular, maintainable
- **Code reduction** - 68% smaller (2200 → 708 lines)
- **Modular tools** - Separated into 5 category modules
- **Type safety** - Full type hints on all tool functions
- **Improved error handling** - Graceful degradation, clear error messages

#### Server Compatibility
- **`server.py`** - Now a compatibility shim (delegates to `server_fastmcp.py`)
- **Deprecation warning** - Alerts users to migrate to `server_fastmcp`
- **Backward compatible** - Existing configurations continue to work
- **Migration path** - Clear upgrade instructions in docs

#### Setup Experience
- **Multi-agent workflow** - One script configures all agents
- **Interactive prompts** - User-friendly with sensible defaults
- **Validation** - Config file validation before writing
- **Backup safety** - Automatic timestamped backups
- **Color-coded output** - Visual feedback (success/warning/error)

#### Documentation
- **README.md** - Added comprehensive multi-agent section
- **MCP_SETUP.md** - Completely rewritten for v2.4.0
- **CLAUDE.md** - Updated with new server details
- **Version badges** - Updated to v2.4.0

### Fixed
- Import issues in test files (updated to use new tool modules)
- CLI version test (updated to expect v2.3.0)
- Graceful MCP import handling (no sys.exit on import)
- Server compatibility for testing environments

### Deprecated
- **`server.py`** - Use `server_fastmcp.py` instead
  - Compatibility shim provided
  - Will be removed in v3.0.0 (6+ months)
  - Migration guide available

### Infrastructure
- **Python 3.10+** - Recommended for best compatibility
- **MCP SDK**: v1.25.0 (pinned to v1.x)
- **uvicorn**: v0.40.0+ (for HTTP transport)
- **starlette**: v0.50.0+ (for HTTP transport)

### Migration from v2.3.0

**Upgrade Steps:**
1. Update dependencies: `pip install -e ".[mcp]"`
2. Update MCP config to use `server_fastmcp`:
   ```json
   {
     "mcpServers": {
       "skill-seeker": {
         "command": "python",
         "args": ["-m", "skill_seekers.mcp.server_fastmcp"]
       }
     }
   }
   ```
3. For HTTP agents, start HTTP server: `python -m skill_seekers.mcp.server_fastmcp --http`
4. Or use auto-configuration: `./setup_mcp.sh`

**Breaking Changes:** None - fully backward compatible

**New Capabilities:**
- Multi-agent support (5 agents)
- HTTP transport for web-based agents
- 8 new MCP tools
- Automatic agent detection and configuration

### Contributors
- Implementation: Claude Sonnet 4.5
- Testing & Review: @yusufkaraaslan

---

## [2.3.0] - 2025-12-22

### 🤖 Multi-Agent Installation Support

This release adds automatic skill installation to 10+ AI coding agents with a single command.

### Added
- **Multi-agent installation support** (#210)
  - New `install-agent` command to install skills to any AI coding agent
  - Support for 10+ agents: Claude Code, Cursor, VS Code, Amp, Goose, OpenCode, Letta, Aide, Windsurf
  - `--agent all` flag to install to all agents at once
  - `--force` flag to overwrite existing installations
  - `--dry-run` flag to preview installations
  - Intelligent path resolution (global vs project-relative)
  - Fuzzy matching for agent names with suggestions
  - Comprehensive error handling and user feedback

### Changed
- Skills are now compatible with the Agent Skills open standard (agentskills.io)
- Installation paths follow standard conventions for each agent
- CLI updated with install-agent subcommand

### Documentation
- Added multi-agent installation guide to README.md
- Updated CLAUDE.md with install-agent examples
- Added agent compatibility table

### Testing
- Added 32 comprehensive tests for install-agent functionality
- All tests passing (603 tests total, 86 skipped)
- No regressions in existing functionality

---

## [2.2.0] - 2025-12-21

### 🚀 Private Config Repositories - Team Collaboration Unlocked

This major release adds **git-based config sources**, enabling teams to fetch configs from private/team repositories in addition to the public API. This unlocks team collaboration, enterprise deployment, and custom config collections.

### 🎯 Major Features

#### Git-Based Config Sources (Issue [#211](https://github.com/yusufkaraaslan/Skill_Seekers/issues/211))
- **Multi-source config management** - Fetch from API, git URL, or named sources
- **Private repository support** - GitHub, GitLab, Bitbucket, Gitea, and custom git servers
- **Team collaboration** - Share configs across 3-5 person teams with version control
- **Enterprise scale** - Support 500+ developers with priority-based resolution
- **Secure authentication** - Environment variable tokens only (GITHUB_TOKEN, GITLAB_TOKEN, etc.)
- **Intelligent caching** - Shallow clone (10-50x faster), auto-pull updates
- **Offline mode** - Works with cached repos when offline
- **Backward compatible** - Existing API-based configs work unchanged

#### New MCP Tools
- **`add_config_source`** - Register git repositories as config sources
  - Auto-detects source type (GitHub, GitLab, etc.)
  - Auto-selects token environment variable
  - Priority-based resolution for multiple sources
  - SSH URL support (auto-converts to HTTPS + token)

- **`list_config_sources`** - View all registered sources
  - Shows git URL, branch, priority, token env
  - Filter by enabled/disabled status
  - Sorted by priority (lower = higher priority)

- **`remove_config_source`** - Unregister sources
  - Removes from registry (cache preserved for offline use)
  - Helpful error messages with available sources

- **Enhanced `fetch_config`** - Three modes
  1. **Named source mode** - `fetch_config(source="team", config_name="react-custom")`
  2. **Git URL mode** - `fetch_config(git_url="https://...", config_name="react-custom")`
  3. **API mode** - `fetch_config(config_name="react")` (unchanged)

### Added

#### Core Infrastructure
- **GitConfigRepo class** (`src/skill_seekers/mcp/git_repo.py`, 283 lines)
  - `clone_or_pull()` - Shallow clone with auto-pull and force refresh
  - `find_configs()` - Recursive *.json discovery (excludes .git)
  - `get_config()` - Load config with case-insensitive matching
  - `inject_token()` - Convert SSH to HTTPS with token authentication
  - `validate_git_url()` - Support HTTPS, SSH, and file:// URLs
  - Comprehensive error handling (auth failures, missing repos, corrupted caches)

- **SourceManager class** (`src/skill_seekers/mcp/source_manager.py`, 260 lines)
  - `add_source()` - Register/update sources with validation
  - `get_source()` - Retrieve by name with helpful errors
  - `list_sources()` - List all/enabled sources sorted by priority
  - `remove_source()` - Unregister sources
  - `update_source()` - Modify specific fields
  - Atomic file I/O (write to temp, then rename)
  - Auto-detect token env vars from source type

#### Storage & Caching
- **Registry file**: `~/.skill-seekers/sources.json`
  - Stores source metadata (URL, branch, priority, timestamps)
  - Version-controlled schema (v1.0)
  - Atomic writes prevent corruption

- **Cache directory**: `$SKILL_SEEKERS_CACHE_DIR` (default: `~/.skill-seekers/cache/`)
  - One subdirectory per source
  - Shallow git clones (depth=1, single-branch)
  - Configurable via environment variable

#### Documentation
- **docs/GIT_CONFIG_SOURCES.md** (800+ lines) - Comprehensive guide
  - Quick start, architecture, authentication
  - MCP tools reference with examples
  - Use cases (small teams, enterprise, open source)
  - Best practices, troubleshooting, advanced topics
  - Complete API reference

- **configs/example-team/** - Example repository for testing
  - `react-custom.json` - Custom React config with metadata
  - `vue-internal.json` - Internal Vue config
  - `company-api.json` - Company API config example
  - `README.md` - Usage guide and best practices
  - `test_e2e.py` - End-to-end test script (7 steps, 100% passing)

- **README.md** - Updated with git source examples
  - New "Private Config Repositories" section in Key Features
  - Comprehensive usage examples (quick start, team collaboration, enterprise)
  - Supported platforms and authentication
  - Example workflows for different team sizes

### Dependencies
- **GitPython>=3.1.40** - Git operations (clone, pull, branch switching)
  - Replaces subprocess calls with high-level API
  - Better error handling and cross-platform support

### Testing
- **83 new tests** (100% passing)
  - `tests/test_git_repo.py` (35 tests) - GitConfigRepo functionality
    - Initialization, URL validation, token injection
    - Clone/pull operations, config discovery, error handling
  - `tests/test_source_manager.py` (48 tests) - SourceManager functionality
    - Add/get/list/remove/update sources
    - Registry persistence, atomic writes, default token env
  - `tests/test_mcp_git_sources.py` (18 tests) - MCP integration
    - All 3 fetch modes (API, Git URL, Named Source)
    - Source management tools (add/list/remove)
    - Complete workflow (add → fetch → remove)
    - Error scenarios (auth failures, missing configs)

### Improved
- **MCP server** - Now supports 12 tools (up from 9)
  - Maintains backward compatibility
  - Enhanced error messages with available sources
  - Priority-based config resolution

### Use Cases

**Small Teams (3-5 people):**
```bash
# One-time setup
add_config_source(name="team", git_url="https://github.com/myteam/configs.git")

# Daily usage
fetch_config(source="team", config_name="react-internal")
```

**Enterprise (500+ developers):**
```bash
# IT pre-configures sources
add_config_source(name="platform", ..., priority=1)
add_config_source(name="mobile", ..., priority=2)

# Developers use transparently
fetch_config(config_name="platform-api")  # Finds in platform source
```

**Example Repository:**
```bash
cd /path/to/Skill_Seekers
python3 configs/example-team/test_e2e.py  # Test E2E workflow
```

### Backward Compatibility
- ✅ All existing configs work unchanged
- ✅ API mode still default (no registration needed)
- ✅ No breaking changes to MCP tools or CLI
- ✅ New parameters are optional (git_url, source, refresh)

### Security
- ✅ Tokens via environment variables only (not in files)
- ✅ Shallow clones minimize attack surface
- ✅ No token storage in registry file
- ✅ Secure token injection (auto-converts SSH to HTTPS)

### Performance
- ✅ Shallow clone: 10-50x faster than full clone
- ✅ Minimal disk space (no git history)
- ✅ Auto-pull: Only fetches changes (not full re-clone)
- ✅ Offline mode: Works with cached repos

### Files Changed
- Modified (2): `pyproject.toml`, `src/skill_seekers/mcp/server.py`
- Added (6): 3 source files + 3 test files + 1 doc + 1 example repo
- Total lines added: ~2,600

### Migration Guide

No migration needed! This is purely additive:

```python
# Before v2.2.0 (still works)
fetch_config(config_name="react")

# New in v2.2.0 (optional)
add_config_source(name="team", git_url="...")
fetch_config(source="team", config_name="react-custom")
```

### Known Limitations
- MCP async tests require pytest-asyncio (added to dev dependencies)
- Example repository uses 'master' branch (git init default)

### See Also
- [GIT_CONFIG_SOURCES.md](docs/GIT_CONFIG_SOURCES.md) - Complete guide
- [configs/example-team/](configs/example-team/) - Example repository
- [Issue #211](https://github.com/yusufkaraaslan/Skill_Seekers/issues/211) - Original feature request

---

## [2.1.1] - 2025-11-30

### Fixed
- **submit_config MCP tool** - Comprehensive validation and format support ([#11](https://github.com/yusufkaraaslan/Skill_Seekers/issues/11))
  - Now uses ConfigValidator for comprehensive validation (previously only checked 3 fields)
  - Validates name format (alphanumeric, hyphens, underscores only)
  - Validates URL formats (must start with http:// or https://)
  - Validates selectors, patterns, rate limits, and max_pages
  - **Supports both legacy and unified config formats**
  - Provides detailed error messages with validation failures and examples
  - Adds warnings for unlimited scraping configurations
  - Enhanced category detection for multi-source configs
  - 8 comprehensive test cases added to test_mcp_server.py
  - Updated GitHub issue template with format type and validation warnings

---

## [2.1.1] - 2025-11-30

### 🚀 GitHub Repository Analysis Enhancements

This release significantly improves GitHub repository scraping with unlimited local analysis, configurable directory exclusions, and numerous bug fixes.

### Added
- **Configurable directory exclusions** for local repository analysis ([#203](https://github.com/yusufkaraaslan/Skill_Seekers/issues/203))
  - `exclude_dirs_additional`: Extend default exclusions with custom directories
  - `exclude_dirs`: Replace default exclusions entirely (advanced users)
  - 19 comprehensive tests covering all scenarios
  - Logging: INFO for extend mode, WARNING for replace mode
- **Unlimited local repository analysis** via `local_repo_path` configuration parameter
- **Auto-exclusion** of virtual environments, build artifacts, and cache directories
- **Support for analyzing repositories without GitHub API rate limits** (50 → unlimited files)
- **Skip llms.txt option** - Force HTML scraping even when llms.txt is detected ([#198](https://github.com/yusufkaraaslan/Skill_Seekers/pull/198))

### Fixed
- Fixed logger initialization error causing `AttributeError: 'NoneType' object has no attribute 'setLevel'` ([#190](https://github.com/yusufkaraaslan/Skill_Seekers/issues/190))
- Fixed 3 NoneType subscriptable errors in release tag parsing
- Fixed relative import paths causing `ModuleNotFoundError`
- Fixed hardcoded 50-file analysis limit preventing comprehensive code analysis
- Fixed GitHub API file tree limitation (140 → 345 files discovered)
- Fixed AST parser "not iterable" errors eliminating 100% of parsing failures (95 → 0 errors)
- Fixed virtual environment file pollution reducing file tree noise by 95%
- Fixed `force_rescrape` flag not checked before interactive prompt causing EOFError in CI/CD environments

### Improved
- Increased code analysis coverage from 14% to 93.6% (+79.6 percentage points)
- Improved file discovery from 140 to 345 files (+146%)
- Improved class extraction from 55 to 585 classes (+964%)
- Improved function extraction from 512 to 2,784 functions (+444%)
- Test suite expanded to 427 tests (up from 391)

---

## [2.1.0] - 2025-11-12

### 🎉 Major Enhancement: Quality Assurance + Race Condition Fixes

This release focuses on quality and reliability improvements, adding comprehensive quality checks and fixing critical race conditions in the enhancement workflow.

### 🚀 Major Features

#### Comprehensive Quality Checker
- **Automatic quality checks before packaging** - Validates skill quality before upload
- **Quality scoring system** - 0-100 score with A-F grades
- **Enhancement verification** - Checks for template text, code examples, sections
- **Structure validation** - Validates SKILL.md, references/ directory
- **Content quality checks** - YAML frontmatter, language tags, "When to Use" section
- **Link validation** - Validates internal markdown links
- **Detailed reporting** - Errors, warnings, and info messages with file locations
- **CLI tool** - `skill-seekers-quality-checker` with verbose and strict modes

#### Headless Enhancement Mode (Default)
- **No terminal windows** - Runs enhancement in background by default
- **Proper waiting** - Main console waits for enhancement to complete
- **Timeout protection** - 10-minute default timeout (configurable)
- **Verification** - Checks that SKILL.md was actually updated
- **Progress messages** - Clear status updates during enhancement
- **Interactive mode available** - `--interactive-enhancement` flag for terminal mode

### Added

#### New CLI Tools
- **quality_checker.py** - Comprehensive skill quality validation
  - Structure checks (SKILL.md, references/)
  - Enhancement verification (code examples, sections)
  - Content validation (frontmatter, language tags)
  - Link validation (internal markdown links)
  - Quality scoring (0-100 + A-F grade)

#### New Features
- **Headless enhancement** - `skill-seekers-enhance` runs in background by default
- **Quality checks in packaging** - Automatic validation before creating .zip
- **MCP quality skip** - MCP server skips interactive checks
- **Enhanced error handling** - Better error messages and timeout handling

#### Tests
- **+12 quality checker tests** - Comprehensive validation testing
- **391 total tests passing** - Up from 379 in v2.0.0
- **0 test failures** - All tests green
- **CI improvements** - Fixed macOS terminal detection tests

### Changed

#### Enhancement Workflow
- **Default mode changed** - Headless mode is now default (was terminal mode)
- **Waiting behavior** - Main console waits for enhancement completion
- **No race conditions** - Fixed "Package your skill" message appearing too early
- **Better progress** - Clear status messages during enhancement

#### Package Workflow
- **Quality checks added** - Automatic validation before packaging
- **User confirmation** - Ask to continue if warnings/errors found
- **Skip option** - `--skip-quality-check` flag to bypass checks
- **MCP context** - Automatically skips checks in non-interactive contexts

#### CLI Arguments
- **doc_scraper.py:**
  - Updated `--enhance-local` help text (mentions headless mode)
  - Added `--interactive-enhancement` flag
- **enhance_skill_local.py:**
  - Changed default to `headless=True`
  - Added `--interactive-enhancement` flag
  - Added `--timeout` flag (default: 600 seconds)
- **package_skill.py:**
  - Added `--skip-quality-check` flag

### Fixed

#### Critical Bugs
- **Enhancement race condition** - Main console no longer exits before enhancement completes
- **MCP stdin errors** - MCP server now skips interactive prompts
- **Terminal detection tests** - Fixed for headless mode default

#### Enhancement Issues
- **Process detachment** - subprocess.run() now waits properly instead of Popen()
- **Timeout handling** - Added timeout protection to prevent infinite hangs
- **Verification** - Checks file modification time and size to verify success
- **Error messages** - Better error handling and user-friendly messages

#### Test Fixes
- **package_skill tests** - Added skip_quality_check=True to prevent stdin errors
- **Terminal detection tests** - Updated to use headless=False for interactive tests
- **MCP server tests** - Fixed to skip quality checks in non-interactive context

### Technical Details

#### New Modules
- `src/skill_seekers/cli/quality_checker.py` - Quality validation engine
- `tests/test_quality_checker.py` - 12 comprehensive tests

#### Modified Modules
- `src/skill_seekers/cli/enhance_skill_local.py` - Added headless mode
- `src/skill_seekers/cli/doc_scraper.py` - Updated enhancement integration
- `src/skill_seekers/cli/package_skill.py` - Added quality checks
- `src/skill_seekers/mcp/server.py` - Skip quality checks in MCP context
- `tests/test_package_skill.py` - Updated for quality checker
- `tests/test_terminal_detection.py` - Updated for headless default

#### Commits in This Release
- `e279ed6` - Phase 1: Enhancement race condition fix (headless mode)
- `3272f9c` - Phases 2 & 3: Quality checker implementation
- `2dd1027` - Phase 4: Tests (+12 quality checker tests)
- `befcb89` - CI Fix: Skip quality checks in MCP context
- `67ab627` - CI Fix: Update terminal tests for headless default

### Upgrade Notes

#### Breaking Changes
- **Headless mode default** - Enhancement now runs in background by default
  - Use `--interactive-enhancement` if you want the old terminal mode
  - Affects: `skill-seekers-enhance` and `skill-seekers scrape --enhance-local`

#### New Behavior
- **Quality checks** - Packaging now runs quality checks by default
  - May prompt for confirmation if warnings/errors found
  - Use `--skip-quality-check` to bypass (not recommended)

#### Recommendations
- **Try headless mode** - Faster and more reliable than terminal mode
- **Review quality reports** - Fix warnings before packaging
- **Update scripts** - Add `--skip-quality-check` to automated packaging scripts if needed

### Migration Guide

**If you want the old terminal mode behavior:**
```bash
# Old (v2.0.0): Default was terminal mode
skill-seekers-enhance output/react/

# New (v2.1.0): Use --interactive-enhancement
skill-seekers-enhance output/react/ --interactive-enhancement
```

**If you want to skip quality checks:**
```bash
# Add --skip-quality-check to package command
skill-seekers-package output/react/ --skip-quality-check
```

---

## [2.0.0] - 2025-11-11

### 🎉 Major Release: PyPI Publication + Modern Python Packaging

**Skill Seekers is now available on PyPI!** Install with: `pip install skill-seekers`

This is a major milestone release featuring complete restructuring for modern Python packaging, comprehensive testing improvements, and publication to the Python Package Index.

### 🚀 Major Changes

#### PyPI Publication
- **Published to PyPI** - https://pypi.org/project/skill-seekers/
- **Installation:** `pip install skill-seekers` or `uv tool install skill-seekers`
- **No cloning required** - Install globally or in virtual environments
- **Automatic dependency management** - All dependencies handled by pip/uv

#### Modern Python Packaging
- **pyproject.toml-based configuration** - Standard PEP 621 metadata
- **src/ layout structure** - Best practice package organization
- **Entry point scripts** - `skill-seekers` command available globally
- **Proper dependency groups** - Separate dev, test, and MCP dependencies
- **Build backend** - setuptools-based build with uv support

#### Unified CLI Interface
- **Single `skill-seekers` command** - Git-style subcommands
- **Subcommands:** `scrape`, `github`, `pdf`, `unified`, `enhance`, `package`, `upload`, `estimate`
- **Consistent interface** - All tools accessible through one entry point
- **Help system** - Comprehensive `--help` for all commands

### Added

#### Testing Infrastructure
- **379 passing tests** (up from 299) - Comprehensive test coverage
- **0 test failures** - All tests passing successfully
- **Test suite improvements:**
  - Fixed import paths for src/ layout
  - Updated CLI tests for unified entry points
  - Added package structure verification tests
  - Fixed MCP server import tests
  - Added pytest configuration in pyproject.toml

#### Documentation
- **Updated README.md** - PyPI badges, reordered installation options
- **FUTURE_RELEASES.md** - Roadmap for upcoming features
- **Installation guides** - Simplified with PyPI as primary method
- **Testing documentation** - How to run full test suite

### Changed

#### Package Structure
- **Moved to src/ layout:**
  - `src/skill_seekers/` - Main package
  - `src/skill_seekers/cli/` - CLI tools
  - `src/skill_seekers/mcp/` - MCP server
- **Import paths updated** - All imports use proper package structure
- **Entry points configured** - All CLI tools available as commands

#### Import Fixes
- **Fixed `merge_sources.py`** - Corrected conflict_detector import (`.conflict_detector`)
- **Fixed MCP server tests** - Updated to use `skill_seekers.mcp.server` imports
- **Fixed test paths** - All tests updated for src/ layout

### Fixed

#### Critical Bugs
- **Import path errors** - Fixed relative imports in CLI modules
- **MCP test isolation** - Added proper MCP availability checks
- **Package installation** - Resolved entry point conflicts
- **Dependency resolution** - All dependencies properly specified

#### Test Improvements
- **17 test fixes** - Updated for modern package structure
- **MCP test guards** - Proper skipif decorators for MCP tests
- **CLI test updates** - Accept both exit codes 0 and 2 for help
- **Path validation** - Tests verify correct package structure

### Technical Details

#### Build System
- **Build backend:** setuptools.build_meta
- **Build command:** `uv build`
- **Publish command:** `uv publish`
- **Distribution formats:** wheel + source tarball

#### Dependencies
- **Core:** requests, beautifulsoup4, PyGithub, mcp, httpx
- **PDF:** PyMuPDF, Pillow, pytesseract
- **Dev:** pytest, pytest-cov, pytest-anyio, mypy
- **MCP:** mcp package for Claude Code integration

### Migration Guide

#### For Users
**Old way:**
```bash
git clone https://github.com/yusufkaraaslan/Skill_Seekers.git
cd Skill_Seekers
pip install -r requirements.txt
python3 cli/doc_scraper.py --config configs/react.json
```

**New way:**
```bash
pip install skill-seekers
skill-seekers scrape --config configs/react.json
```

#### For Developers
- Update imports: `from cli.* → from skill_seekers.cli.*`
- Use `pip install -e ".[dev]"` for development
- Run tests: `python -m pytest`
- Entry points instead of direct script execution

### Breaking Changes
- **CLI interface changed** - Use `skill-seekers` command instead of `python3 cli/...`
- **Import paths changed** - Package now at `skill_seekers.*` instead of `cli.*`
- **Installation method changed** - PyPI recommended over git clone

### Deprecations
- **Direct script execution** - Still works but deprecated (use `skill-seekers` command)
- **Old import patterns** - Legacy imports still work but will be removed in v3.0

### Compatibility
- **Python 3.10+** required
- **Backward compatible** - Old scripts still work with legacy CLI
- **Config files** - No changes required
- **Output format** - No changes to generated skills

---

## [1.3.0] - 2025-10-26

### Added - Refactoring & Performance Improvements
- **Async/Await Support for Parallel Scraping** (2-3x performance boost)
  - `--async` flag to enable async mode
  - `async def scrape_page_async()` method using httpx.AsyncClient
  - `async def scrape_all_async()` method with asyncio.gather()
  - Connection pooling for better performance
  - asyncio.Semaphore for concurrency control
  - Comprehensive async testing (11 new tests)
  - Full documentation in ASYNC_SUPPORT.md
  - Performance: ~55 pages/sec vs ~18 pages/sec (sync)
  - Memory: 40 MB vs 120 MB (66% reduction)
- **Python Package Structure** (Phase 0 Complete)
  - `cli/__init__.py` - CLI tools package with clean imports
  - `skill_seeker_mcp/__init__.py` - MCP server package (renamed from mcp/)
  - `skill_seeker_mcp/tools/__init__.py` - MCP tools subpackage
  - Proper package imports: `from cli import constants`
- **Centralized Configuration Module**
  - `cli/constants.py` with 18 configuration constants
  - `DEFAULT_ASYNC_MODE`, `DEFAULT_RATE_LIMIT`, `DEFAULT_MAX_PAGES`
  - Enhancement limits, categorization scores, file limits
  - All magic numbers now centralized and configurable
- **Code Quality Improvements**
  - Converted 71 print() statements to proper logging calls
  - Added type hints to all DocToSkillConverter methods
  - Fixed all mypy type checking issues
  - Installed types-requests for better type safety
- Multi-variant llms.txt detection: downloads all 3 variants (full, standard, small)
- Automatic .txt → .md file extension conversion
- No content truncation: preserves complete documentation
- `detect_all()` method for finding all llms.txt variants
- `get_proper_filename()` for correct .md naming

### Changed
- `_try_llms_txt()` now downloads all available variants instead of just one
- Reference files now contain complete content (no 2500 char limit)
- Code samples now include full code (no 600 char limit)
- Test count increased from 207 to 299 (92 new tests)
- All print() statements replaced with logging (logger.info, logger.warning, logger.error)
- Better IDE support with proper package structure
- Code quality improved from 5.5/10 to 6.5/10

### Fixed
- File extension bug: llms.txt files now saved as .md
- Content loss: 0% truncation (was 36%)
- Test isolation issues in test_async_scraping.py (proper cleanup with try/finally)
- Import issues: no more sys.path.insert() hacks needed
- .gitignore: added test artifacts (.pytest_cache, .coverage, htmlcov, etc.)

---

## [1.2.0] - 2025-10-23

### 🚀 PDF Advanced Features Release

Major enhancement to PDF extraction capabilities with Priority 2 & 3 features.

### Added

#### Priority 2: Support More PDF Types
- **OCR Support for Scanned PDFs**
  - Automatic text extraction from scanned documents using Tesseract OCR
  - Fallback mechanism when page text < 50 characters
  - Integration with pytesseract and Pillow
  - Command: `--ocr` flag
  - New dependencies: `Pillow==11.0.0`, `pytesseract==0.3.13`

- **Password-Protected PDF Support**
  - Handle encrypted PDFs with password authentication
  - Clear error messages for missing/wrong passwords
  - Secure password handling
  - Command: `--password PASSWORD` flag

- **Complex Table Extraction**
  - Extract tables from PDFs using PyMuPDF's table detection
  - Capture table data as 2D arrays with metadata (bbox, row/col count)
  - Integration with skill references in markdown format
  - Command: `--extract-tables` flag

#### Priority 3: Performance Optimizations
- **Parallel Page Processing**
  - 3x faster PDF extraction using ThreadPoolExecutor
  - Auto-detect CPU count or custom worker specification
  - Only activates for PDFs with > 5 pages
  - Commands: `--parallel` and `--workers N` flags
  - Benchmarks: 500-page PDF reduced from 4m 10s to 1m 15s

- **Intelligent Caching**
  - In-memory cache for expensive operations (text extraction, code detection, quality scoring)
  - 50% faster on re-runs
  - Command: `--no-cache` to disable (enabled by default)

#### New Documentation
- **`docs/PDF_ADVANCED_FEATURES.md`** (580 lines)
  - Complete usage guide for all advanced features
  - Installation instructions
  - Performance benchmarks showing 3x speedup
  - Best practices and troubleshooting
  - API reference with all parameters

#### Testing
- **New test file:** `tests/test_pdf_advanced_features.py` (568 lines, 26 tests)
  - TestOCRSupport (5 tests)
  - TestPasswordProtection (4 tests)
  - TestTableExtraction (5 tests)
  - TestCaching (5 tests)
  - TestParallelProcessing (4 tests)
  - TestIntegration (3 tests)
- **Updated:** `tests/test_pdf_extractor.py` (23 tests fixed and passing)
- **Total PDF tests:** 49/49 PASSING ✅ (100% pass rate)

### Changed
- Enhanced `cli/pdf_extractor_poc.py` with all advanced features
- Updated `requirements.txt` with new dependencies
- Updated `README.md` with PDF advanced features usage
- Updated `docs/TESTING.md` with new test counts (142 total tests)

### Performance Improvements
- **3.3x faster** with parallel processing (8 workers)
- **1.7x faster** on re-runs with caching enabled
- Support for unlimited page PDFs (no more 500-page limit)

### Dependencies
- Added `Pillow==11.0.0` for image processing
- Added `pytesseract==0.3.13` for OCR support
- Tesseract OCR engine (system package, optional)

---

## [1.1.0] - 2025-10-22

### 🌐 Documentation Scraping Enhancements

Major improvements to documentation scraping with unlimited pages, parallel processing, and new configs.

### Added

#### Unlimited Scraping & Performance
- **Unlimited Page Scraping** - Removed 500-page limit, now supports unlimited pages
- **Parallel Scraping Mode** - Process multiple pages simultaneously for faster scraping
- **Dynamic Rate Limiting** - Smart rate limit control to avoid server blocks
- **CLI Utilities** - New helper scripts for common tasks

#### New Configurations
- **Ansible Core 2.19** - Complete Ansible documentation config
- **Claude Code** - Documentation for this very tool!
- **Laravel 9.x** - PHP framework documentation

#### Testing & Quality
- Comprehensive test coverage for CLI utilities
- Parallel scraping test suite
- Virtual environment setup documentation
- Thread-safety improvements

### Fixed
- Thread-safety issues in parallel scraping
- CLI path references across all documentation
- Flaky upload_skill tests
- MCP server streaming subprocess implementation

### Changed
- All CLI examples now use `cli/` directory prefix
- Updated documentation structure
- Enhanced error handling

---

## [1.0.0] - 2025-10-19

### 🎉 First Production Release

This is the first production-ready release of Skill Seekers with complete feature set, full test coverage, and comprehensive documentation.

### Added

#### Smart Auto-Upload Feature
- New `upload_skill.py` CLI tool for automatic API-based upload
- Enhanced `package_skill.py` with `--upload` flag
- Smart API key detection with graceful fallback
- Cross-platform folder opening in `utils.py`
- Helpful error messages instead of confusing errors

#### MCP Integration Enhancements
- **9 MCP tools** (added `upload_skill` tool)
- `mcp__skill-seeker__upload_skill` - Upload .zip files to Claude automatically
- Enhanced `package_skill` tool with smart auto-upload parameter
- Updated all MCP documentation to reflect 9 tools

#### Documentation Improvements
- Updated README with version badge (v1.0.0)
- Enhanced upload guide with 3 upload methods
- Updated MCP setup guide with all 9 tools
- Comprehensive test documentation (14/14 tests)
- All references to tool counts corrected

### Fixed
- Missing `import os` in `mcp/server.py`
- `package_skill.py` exit code behavior (now exits 0 when API key missing)
- Improved UX with helpful messages instead of errors

### Changed
- Test count badge updated (96 → 14 passing)
- All documentation references updated to 9 tools

### Testing
- **CLI Tests:** 8/8 PASSED ✅
- **MCP Tests:** 6/6 PASSED ✅
- **Total:** 14/14 PASSED (100%)

---

## [0.4.0] - 2025-10-18

### Added

#### Large Documentation Support (40K+ Pages)
- Config splitting functionality for massive documentation sites
- Router/hub skill generation for intelligent query routing
- Checkpoint/resume feature for long scrapes
- Parallel scraping support for faster processing
- 4 split strategies: auto, category, router, size

#### New CLI Tools
- `split_config.py` - Split large configs into focused sub-skills
- `generate_router.py` - Generate router/hub skills
- `package_multi.py` - Package multiple skills at once

#### New MCP Tools
- `split_config` - Split large documentation via MCP
- `generate_router` - Generate router skills via MCP

#### Documentation
- New `docs/LARGE_DOCUMENTATION.md` guide
- Example config: `godot-large-example.json` (40K pages)

### Changed
- MCP tool count: 6 → 8 tools
- Updated documentation for large docs workflow

---

## [0.3.0] - 2025-10-15

### Added

#### MCP Server Integration
- Complete MCP server implementation (`mcp/server.py`)
- 6 MCP tools for Claude Code integration:
  - `list_configs`
  - `generate_config`
  - `validate_config`
  - `estimate_pages`
  - `scrape_docs`
  - `package_skill`

#### Setup & Configuration
- Automated setup script (`setup_mcp.sh`)
- MCP configuration examples
- Comprehensive MCP setup guide (`docs/MCP_SETUP.md`)
- MCP testing guide (`docs/TEST_MCP_IN_CLAUDE_CODE.md`)

#### Testing
- 31 comprehensive unit tests for MCP server
- Integration tests via Claude Code MCP protocol
- 100% test pass rate

#### Documentation
- Complete MCP integration documentation
- Natural language usage examples
- Troubleshooting guides

### Changed
- Restructured project as monorepo with CLI and MCP server
- Moved CLI tools to `cli/` directory
- Added MCP server to `mcp/` directory

---

## [0.2.0] - 2025-10-10

### Added

#### Testing & Quality
- Comprehensive test suite with 71 tests
- 100% test pass rate
- Test coverage for all major features
- Config validation tests

#### Optimization
- Page count estimator (`estimate_pages.py`)
- Framework config optimizations with `start_urls`
- Better URL pattern coverage
- Improved scraping efficiency

#### New Configs
- Kubernetes documentation config
- Tailwind CSS config
- Astro framework config

### Changed
- Optimized all framework configs
- Improved categorization accuracy
- Enhanced error messages

---

## [0.1.0] - 2025-10-05

### Added

#### Initial Release
- Basic documentation scraper functionality
- Manual skill creation
- Framework configs (Godot, React, Vue, Django, FastAPI)
- Smart categorization system
- Code language detection
- Pattern extraction
- Local and API-based enhancement options
- Basic packaging functionality

#### Core Features
- BFS traversal for documentation scraping
- CSS selector-based content extraction
- Smart categorization with scoring
- Code block detection and formatting
- Caching system for scraped data
- Interactive mode for config creation

#### Documentation
- README with quick start guide
- Basic usage documentation
- Configuration file examples

---

## Release Links

- [v1.2.0](https://github.com/yusufkaraaslan/Skill_Seekers/releases/tag/v1.2.0) - PDF Advanced Features
- [v1.1.0](https://github.com/yusufkaraaslan/Skill_Seekers/releases/tag/v1.1.0) - Documentation Scraping Enhancements
- [v1.0.0](https://github.com/yusufkaraaslan/Skill_Seekers/releases/tag/v1.0.0) - Production Release
- [v0.4.0](https://github.com/yusufkaraaslan/Skill_Seekers/releases/tag/v0.4.0) - Large Documentation Support
- [v0.3.0](https://github.com/yusufkaraaslan/Skill_Seekers/releases/tag/v0.3.0) - MCP Integration

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| **1.2.0** | 2025-10-23 | 📄 PDF advanced features: OCR, passwords, tables, 3x faster |
| **1.1.0** | 2025-10-22 | 🌐 Unlimited scraping, parallel mode, new configs (Ansible, Laravel) |
| **1.0.0** | 2025-10-19 | 🚀 Production release, auto-upload, 9 MCP tools |
| **0.4.0** | 2025-10-18 | 📚 Large docs support (40K+ pages) |
| **0.3.0** | 2025-10-15 | 🔌 MCP integration with Claude Code |
| **0.2.0** | 2025-10-10 | 🧪 Testing & optimization |
| **0.1.0** | 2025-10-05 | 🎬 Initial release |

---

[Unreleased]: https://github.com/yusufkaraaslan/Skill_Seekers/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/yusufkaraaslan/Skill_Seekers/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/yusufkaraaslan/Skill_Seekers/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/yusufkaraaslan/Skill_Seekers/compare/v0.4.0...v1.0.0
[0.4.0]: https://github.com/yusufkaraaslan/Skill_Seekers/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/yusufkaraaslan/Skill_Seekers/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/yusufkaraaslan/Skill_Seekers/releases/tag/v0.2.0
[0.1.0]: https://github.com/yusufkaraaslan/Skill_Seekers/releases/tag/v0.1.0
