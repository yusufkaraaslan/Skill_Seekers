# Changelog

All notable changes to Skill Seeker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- (No unreleased changes yet)

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
