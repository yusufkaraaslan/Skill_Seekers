# Changelog

All notable changes to Skill Seeker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

- [v1.0.0](https://github.com/yusufkaraaslan/Skill_Seekers/releases/tag/v1.0.0) - Production Release
- [v0.4.0](https://github.com/yusufkaraaslan/Skill_Seekers/releases/tag/v0.4.0) - Large Documentation Support
- [v0.3.0](https://github.com/yusufkaraaslan/Skill_Seekers/releases/tag/v0.3.0) - MCP Integration

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| **1.0.0** | 2025-10-19 | 🚀 Production release, auto-upload, 9 MCP tools |
| **0.4.0** | 2025-10-18 | 📚 Large docs support (40K+ pages) |
| **0.3.0** | 2025-10-15 | 🔌 MCP integration with Claude Code |
| **0.2.0** | 2025-10-10 | 🧪 Testing & optimization |
| **0.1.0** | 2025-10-05 | 🎬 Initial release |

---

[Unreleased]: https://github.com/yusufkaraaslan/Skill_Seekers/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yusufkaraaslan/Skill_Seekers/compare/v0.4.0...v1.0.0
[0.4.0]: https://github.com/yusufkaraaslan/Skill_Seekers/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/yusufkaraaslan/Skill_Seekers/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/yusufkaraaslan/Skill_Seekers/releases/tag/v0.2.0
[0.1.0]: https://github.com/yusufkaraaslan/Skill_Seekers/releases/tag/v0.1.0
