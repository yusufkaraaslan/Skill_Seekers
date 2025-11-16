# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Skill Seeker** is a Python-based tool that automatically converts documentation websites, GitHub repositories, and PDFs into Claude AI skills. It transforms scattered documentation into organized, comprehensive skills that can be uploaded to Claude for enhanced AI assistance.

**Version:** 2.0.0 (Production Ready)
**Python Requirements:** Python 3.10+
**Key Features:** Multi-source scraping, conflict detection, AI enhancement, MCP integration

## Repository Structure

```
Skill_Seekers/
├── cli/                           # Main CLI tools
│   ├── doc_scraper.py            # Core documentation scraper
│   ├── unified_scraper.py        # Multi-source scraper (NEW v2.0.0)
│   ├── github_scraper.py         # GitHub repository scraper
│   ├── pdf_scraper.py            # PDF extraction tool
│   ├── enhance_skill.py          # AI-powered skill enhancement
│   ├── enhance_skill_local.py    # Local enhancement (no API key)
│   ├── package_skill.py          # Package skills into .zip files
│   ├── upload_skill.py           # Auto-upload to Claude
│   ├── estimate_pages.py         # Quick page count estimation
│   ├── config_validator.py       # Configuration validation
│   ├── conflict_detector.py      # Documentation vs code conflict detection
│   ├── constants.py              # Centralized constants
│   ├── utils.py                  # Utility functions
│   └── run_tests.py              # Test runner with colored output
├── skill_seeker_mcp/              # MCP server for Claude Code integration
│   ├── server.py                 # Main MCP server (9 tools)
│   └── requirements.txt          # MCP-specific dependencies
├── configs/                       # Preset configurations for popular frameworks
│   ├── godot.json                # Godot Engine
│   ├── react.json                # React framework
│   ├── vue.json                  # Vue.js
│   ├── django.json               # Django web framework
│   ├── fastapi.json              # FastAPI
│   ├── *_unified.json            # Multi-source configurations (NEW)
│   └── ...                       # 20+ total configurations
├── tests/                         # Comprehensive test suite
│   ├── test_*.py                 # 299 tests (100% pass rate)
│   └── conftest.py               # Test configuration
├── docs/                          # Additional documentation
├── output/                        # Generated output (git-ignored)
├── requirements.txt               # Python dependencies
├── setup_mcp.sh                   # MCP server setup script
├── demo_conflicts.py             # Conflict detection demonstration
└── .claude/                       # Claude Code project configuration
    ├── agents/                   # Available agents
    │   ├── architectural-critic.md    # Architectural complexity specialist
    │   ├── code-analyzer.md           # Deep code analysis specialist
    │   ├── cognitive-resonator.md     # Cognitive flow and developer experience specialist
    │   ├── intelligence-orchestrator.md # Multi-Domain Intelligence Synthesis Specialist
    │   ├── orchestrator-agent.md      # Chief-of-staff orchestrator
    │   ├── performance-auditor.md     # Performance optimization specialist
    │   ├── possibility-weaver.md      # Creative catalyst agent
    │   ├── precision-editor.md        # Surgical code modification specialist
    │   ├── referee-agent-csp.md       # Convergent Synthesis Primitive for deterministic evaluation
    │   ├── security-analyst.md        # Practical security specialist for development workflows
    │   └── test-generator.md          # Comprehensive test generation specialist
    ├── commands/                 # Custom commands
    │   ├── check-hook.md          # Comprehensive hook validation system
    │   ├── create-agent.md        # Enhanced agent creation system with atomic operations and validation
    │   ├── refine-agent.md        # Multi-mental model agent refinement workflow
    │   └── update-CLAUDE.md      # Automatic documentation synchronization
    ├── hooks/                     # Hooks
    ├── skills/                    # Available skills
    │   └── agent-scaffolding-toolkit/  # Agent creation toolkit
    │       ├── SKILL.md
    │       ├── scripts/
    │       ├── assets/templates/
    │       └── references/
    └── mcp_config.example.json    # MCP configuration
```

## Development Commands

### Environment Setup

```bash
# Create and activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Optional: Install PDF support
pip install PyMuPDF

# Optional: Install GitHub support
pip install PyGithub

# Optional: Install for API-based enhancement
pip install anthropic
```

### Testing

```bash
# Run all tests with colored output
python3 cli/run_tests.py

# Run specific test suites
python3 cli/run_tests.py --suite config
python3 cli/run_tests.py --suite features
python3 cli/run_tests.py --suite integration

# Verbose testing
python3 cli/run_tests.py --verbose

# Run tests using pytest directly
pytest tests/ -v
pytest tests/test_mcp_server.py -v
```

### Core Development Workflows

```bash
# 1. Test with small dataset first
python3 cli/estimate_pages.py configs/react.json

# 2. Run a basic scrape
python3 cli/doc_scraper.py --config configs/react.json

# 3. Enhanced skill creation (recommended)
python3 cli/doc_scraper.py --config configs/react.json --enhance-local

# 4. Package the skill
python3 cli/package_skill.py output/react/

# 5. Test multi-source scraping (NEW v2.0.0)
python3 cli/unified_scraper.py --config configs/react_unified.json

# 6. Run conflict detection demo
python3 demo_conflicts.py
```

### MCP Server Development

```bash
# Setup MCP server for Claude Code integration
./setup_mcp.sh

# Test MCP server manually
python3 skill_seeker_mcp/server.py

# Test MCP server tools
python3 -m pytest tests/test_mcp_server.py -v
```

### Configuration Management

```bash
# Validate configuration files
python3 cli/config_validator.py configs/react.json

# Generate new configuration interactively
python3 cli/doc_scraper.py --interactive

# Create unified multi-source config
python3 cli/unified_scraper.py --create-config
```

## 🚀 Agent Scaffolding Toolkit (NEW)

**Location**: `.claude/skills/agent-scaffolding-toolkit/`

A surgical toolkit for creating specialized agents with interactive wizard-guided generation. Eliminates human-in-the-loop dependency while maintaining developer flexibility.

### **Quick Start**

```bash
# Setup agent scaffolding toolkit
cd .claude/skills/agent-scaffolding-toolkit/
./setup.sh

# Create agents interactively (60 seconds)
source .venv/bin/activate
python scripts/create_agent.py

# Available templates
python scripts/list_templates.py --detailed
```

### **Available Agents**

| Agent | Description | Use Case |
|--------|-------------|---------|
| **@architectural-critic** | Architectural complexity specialist that detects phase boundaries, system transitions, and structural evolution patterns in codebases through multi-dimensional analysis. Provides pre-emptive intervention strategies before architectural breakdown occurs. | Pre-emptive Architecture Review** |
| **@code-analyzer** | Deep code analysis agent specializing in complexity metrics, design patterns, anti-patterns, and technical debt. Provides quantifiable assessments with actionable refactoring recommendations. | Pre-commit Review** |
| **@cognitive-resonator** | Cognitive flow specialist that analyzes code harmony, mental model alignment, and developer experience optimization through psychological and computational analysis. Enhances developer productivity by ensuring code patterns resonate with natural cognitive processes. | Developer Experience Optimization** |
| **@orchestrator-agent** | The single interface pattern applied to agent fleets. Manages, delegates, and synthesizes results from parallel subagents. | orchestration |
| **@performance-auditor** | Performance optimization specialist that identifies bottlenecks, memory leaks, and inefficient algorithms through systematic profiling and data-driven analysis. Provides quantifiable performance improvements with ROI calculations. | API Endpoint Optimization** |
| **@possibility-weaver** | Creative catalyst agent that introduces novel perspectives and beneficial constraints to break developers out of local optima. Uses constraint innovation and perspective synthesis to expand solution spaces while maintaining core system invariants. | Innovation & Problem Solving** |
| **@precision-editor** | Surgical code modification specialist that performs precise, system-aware edits with minimal side effects and maximum architectural integrity. Uses gene-editing precision to make targeted modifications while preserving system coherence and design intent. | Surgical Code Modifications** |
| **@referee-agent-csp** | Convergent Synthesis Primitive for deterministic outcome evaluation and autonomous selection. Performs metric-driven synthesis of multiple parallel agent outputs. | synthesis |
| **@security-analyst** | Practical security specialist for development workflows. Analyzes code, configurations, and dependencies for common vulnerabilities without requiring security expertise. | security |
| **@intelligence-orchestrator** | Multi-Domain Intelligence Synthesis Specialist that enhances the entire Skill_Seekers ecosystem through agent intelligence enhancement, testing intelligence, and workflow orchestration. | Intelligence Enhancement, Testing Optimization, Workflow Orchestration** |
| **@test-generator** | Comprehensive test generation specialist that creates unit, integration, performance, and security tests with coverage optimization and CI/CD integration. Generates maintainable test suites using the T.E.S.T. methodology for maximum effectiveness and developer productivity. | New Feature Testing** |


### **Agent Creation Workflow**

1. **Interactive Wizard**: 4 surgical decisions (type, tools, model, customization)
2. **Template Selection**: Choose from battle-tested templates
3. **Instant Generation**: Creates validated agents in project-wide `.claude/agents/`
4. **Zero Learning Curve**: Immediate productivity from first use

### **Agent Refinement Workflow**

**Multi-Mental Model Agent Refinement**:
- **Command**: `/refine-agent <agent-name> [focus-area]`
- **Methodology**: check → plan → recheck → pause → create → recheck → refine → recheck → exit
- **Mental Models**: First principles, second order effects, interdependencies, systems thinking, inversion
- **Automation**: Systematic validation, YAML compliance, user scenario testing
- **Example**: Applied to security-analyst agent (expanded from 3 lines to 172 lines of practical security guidance)

### **Documentation Synchronization**

**Automatic CLAUDE.md Updates**:
- **Command**: `/update-CLAUDE.md [options]`
- **Detection**: Monitors agents, commands, skills, and structural changes
- **Automation**: Updates agent tables, command descriptions, structure diagrams
- **Validation**: Ensures consistency across all documentation sections
- **Integration**: Git hooks and CI/CD pipeline support

### **Hook Validation System**

**Comprehensive Hook Health Monitoring**:
- **Command**: `/check-hook [options]`
- **Validation**: JSON syntax, path resolution, executable permissions, environment health
- **Testing**: Functional testing with sample data and performance impact assessment
- **Auto-Fix**: Automatic resolution of common issues (permissions, paths, syntax)
- **Scoring**: Overall hook health score with detailed diagnostics

**Usage Examples**:
```bash
# Quick validation
/check-hook

# Full validation with fixes and testing
/check-hook --fix --test --verbose

# Test specific hook types
/check-hook --hooks PreToolUse --test
```

### **Key Features**

- **60-Second Agent Creation**: Interactive wizard with intelligent defaults
- **Battle-Tested Templates**: Orchestrator, Referee, Specialist patterns
- **Automatic Validation**: Structural compliance checking via hooks
- **Project-Wide Availability**: Agents created in `.claude/agents/` for immediate use
- **Progressive Documentation**: Layer 1 (immediate) + Layer 2 (detailed)
- **Comprehensive Test Suite**: 21 tests with 95% coverage target
- **Skill Seekers Export**: Convert agents to skills with conflict detection
- **Git Integration**: Pre-commit hooks for agent validation

### **Testing & Quality**

**Test Suite**: `.claude/tests/`
- **21 comprehensive tests** (unit, integration, E2E)
- **95% coverage target** across all hook scripts
- **Fixtures & mocks** for isolated testing
- **CI/CD ready** with GitHub Actions support

```bash
# Run tests
cd .claude/tests
source .venv/bin/activate
pip install -r requirements.txt
pytest -v

# With coverage
pytest --cov=../ --cov-report=html
```

### **Export Integration**

**Export to Skill Seekers**: `.claude/skills/agent-scaffolding-toolkit/scripts/export_to_skill_seekers.py`

```bash
# Export all agents to Skill Seekers format
cd .claude/skills/agent-scaffolding-toolkit
source .venv/bin/activate
python scripts/export_to_skill_seekers.py --detect-conflicts --package
```

**Features:**
- Maps agents → SKILL.md + configs
- Preserves delegation relationships
- Detects conflicts with existing skills
- Optional .zip packaging
- Registry integration for usage stats

## Key Architectural Components

### 1. Multi-Source Architecture (v2.0.0)

The unified scraper combines multiple data sources:
- **Documentation websites** - Traditional HTML docs scraping
- **GitHub repositories** - Code analysis, API extraction, issues/PRs
- **PDF files** - Text, table, and image extraction
- **Conflict Detection** - Identifies discrepancies between sources

### 2. MCP Integration

9 MCP tools available in Claude Code:
- `list_configs` - List available preset configurations
- `generate_config` - Create new configuration files
- `validate_config` - Validate configuration structure
- `estimate_pages` - Estimate scraping time and page count
- `scrape_docs` - Scrape documentation and build skills
- `package_skill` - Package skills with auto-upload capability
- `upload_skill` - Upload existing .zip files to Claude
- `split_config` - Split large documentation into focused skills
- `generate_router` - Create router/hub skills for sub-skill navigation

### 3. Conflict Detection System

Automatically detects 4 types of conflicts:
- **Missing in docs** (high): Features implemented but not documented
- **Missing in code** (high): Documented but not implemented
- **Signature mismatch** (medium): Different parameters/types
- **Description mismatch** (low): Different explanations

### 4. AI Enhancement

Two enhancement modes:
- **LOCAL**: Uses Claude Code Max plan (no API costs)
- **API**: Uses Anthropic API (~$0.15-0.30 per skill)

## Technical Architecture Deep Dive

### Single-File Design Philosophy

The core scraper (`cli/doc_scraper.py`) follows a class-based architecture with a single `DocToSkillConverter` class at **line 70** that handles:
- **Web scraping**: BFS traversal with URL validation
- **Content extraction**: CSS selectors for title, content, code blocks
- **Language detection**: Heuristic-based detection from code samples (Python, JavaScript, GDScript, C++, etc.)
- **Pattern extraction**: Identifies common coding patterns from documentation
- **Categorization**: Smart categorization using URL structure, page titles, and content keywords with scoring
- **Skill generation**: Creates SKILL.md with real code examples and categorized reference files

### Critical Code Locations (Verified)

| Function | Line | Purpose |
|----------|------|---------|
| `DocToSkillConverter` class | 70 | Main converter class |
| `scrape_all()` | 566 | Primary scraping loop (sync) |
| `scrape_all_async()` | 727 | Async scraping (3x faster) |
| `create_enhanced_skill_md()` | 1005 | SKILL.md generation with examples |
| `smart_categorize()` | ~280-321 | Smart categorization logic |
| `extract_patterns()` | ~165-181 | Pattern extraction from docs |
| `detect_language()` | ~133-163 | Code language detection |

### Data Flow Architecture

**Phase 1: Scrape**
```
Input: Config JSON → BFS Traversal → URL Validation → Content Extraction
Output: output/{name}_data/pages/*.json + summary.json
```

**Phase 2: Build**
```
Input: Scraped JSON → Smart Categorize → Extract Patterns → Generate References
Output: output/{name}/SKILL.md + references/*.md
```

### Selector Testing with BeautifulSoup

To find the right CSS selectors for a documentation site:

```python
from bs4 import BeautifulSoup
import requests

url = "https://docs.example.com/page"
soup = BeautifulSoup(requests.get(url).content, 'html.parser')

# Try different selectors
print(soup.select_one('article'))        # Common in modern docs
print(soup.select_one('main'))           # HTML5 semantic
print(soup.select_one('div[role="main"]')) # Accessibility markup
print(soup.select_one('div.content'))    # Classic pattern
```

**Common selector patterns:**
- `article` - Modern documentation (React, Vue)
- `main` - HTML5 semantic (MDN, W3C)
- `div[role="main"]` - Accessibility-first sites
- `div.content`, `div.docs` - Classic documentation

### llms.txt Support Detection Order

Skill_Seekers automatically detects llms.txt files before HTML scraping:

**Detection Priority:**
1. `{base_url}/llms-full.txt` (complete documentation)
2. `{base_url}/llms.txt` (standard version)
3. `{base_url}/llms-small.txt` (quick reference)
4. Falls back to HTML scraping if none found

**Benefits:**
- ⚡ **10x faster**: < 5 seconds vs 20-60 seconds
- ✅ **More reliable**: Maintained by docs authors
- 🎯 **Better quality**: Pre-formatted for LLMs
- 🚫 **No rate limiting**: Single file download

**Example:** Hono framework at https://hono.dev/llms-full.txt

### Output Quality Validation

After building, verify quality with these commands:

```bash
# Check SKILL.md has real code examples
cat output/godot/SKILL.md | grep -A 5 "```"

# Verify categorization worked
cat output/godot/references/index.md

# Check category files exist
ls -lh output/godot/references/

# Count total pages processed
jq '.total_pages' output/godot_data/summary.json

# Check for language detection
grep -o 'language-[a-z]*' output/godot/SKILL.md | sort | uniq -c
```

### Smart Categorization Algorithm

**Scoring system** (minimum 2 points for categorization):
- **3 points**: Keyword found in URL path
- **2 points**: Keyword found in page title
- **1 point**: Keyword found in content preview (first 500 chars)

**Category inference**: If no categories provided in config, auto-infers from URL segments:
- `/docs/api/` → "api" category
- `/guide/getting-started/` → "getting_started" category
- Falls back to "other" if no match

**Example categorization:**
```
Page: https://docs.godot.org/en/stable/tutorials/scripting/gdscript/
URL contains "scripting" (3 pts) + "gdscript" (3 pts) = 6 points
→ Categorized as "scripting"
```

## Configuration System

### Standard Config Structure

```json
{
  "name": "skill-name",
  "description": "When to use this skill",
  "base_url": "https://docs.example.com/",
  "selectors": {
    "main_content": "article",
    "title": "h1",
    "code_blocks": "pre code"
  },
  "url_patterns": {
    "include": ["/docs", "/guide"],
    "exclude": ["/blog", "/search"]
  },
  "categories": {
    "getting_started": ["intro", "quickstart"],
    "api": ["reference", "api"]
  },
  "rate_limit": 0.5,
  "max_pages": 500
}
```

### Unified Config Structure (v2.0.0)

```json
{
  "name": "skill-name",
  "description": "Comprehensive skill from multiple sources",
  "merge_mode": "rule-based",
  "sources": [
    {
      "type": "documentation",
      "base_url": "https://docs.example.com/",
      "extract_api": true,
      "max_pages": 200
    },
    {
      "type": "github",
      "repo": "owner/example",
      "include_code": true,
      "code_analysis_depth": "surface"
    }
  ]
}
```

## Core Constants and Limits

Key constants defined in `cli/constants.py`:
- `DEFAULT_RATE_LIMIT`: 0.5 seconds between requests
- `DEFAULT_MAX_PAGES`: 500 pages maximum
- `CONTENT_PREVIEW_LENGTH`: 500 characters for categorization
- `MIN_CATEGORIZATION_SCORE`: 2 points minimum for category assignment
- `API_CONTENT_LIMIT`: 100,000 characters for API enhancement
- `LOCAL_CONTENT_LIMIT`: 50,000 characters for local enhancement

## Testing Strategy

### Test Coverage
- **299 tests** with 100% pass rate
- Unit tests for all core components
- Integration tests for end-to-end workflows
- MCP server tests for all 9 tools
- Conflict detection tests

### Test Categories
- Configuration validation
- Scraping functionality (sync and async)
- PDF extraction features
- GitHub repository analysis
- Unified multi-source scraping
- MCP tool functionality
- Enhancement processes

## Performance Characteristics

### Scraping Performance
- **Sync mode**: ~18 pages/sec, 120 MB memory
- **Async mode**: ~55 pages/sec, 40 MB memory (3x faster)
- **Async workers**: 4-8 workers recommended
- **Rate limiting**: Configurable to avoid server blocks

### Processing Time
- Page estimation: 1-3 minutes
- Documentation scraping: 15-45 minutes
- GitHub analysis: 5-10 minutes
- PDF extraction: 2-15 minutes (varies by size)
- Skill building: 1-3 minutes
- Enhancement: 30-60 seconds (local), 20-40 seconds (API)
- Packaging: 5-10 seconds

## Development Methodology: Multi-Model Approach

This project follows a rigorous **check → plan → recheck → pause → create → recheck → refine → recheck → exit** methodology, enhanced by multiple mental models:

### **Mental Models Applied**

1. **First Principles**: Break problems down to fundamental truths
2. **Second Order Effects**: Consider consequences of consequences
3. **Interdependencies**: Map system relationships and feedback loops
4. **Systems Thinking**: View the project as an integrated whole
5. **Inversion**: Approach problems by considering what to avoid

### **Workflow Phases**

**CHECK Phase** (First Principles + Systems Thinking)
- Verify current state and identify structural issues
- Map existing dependencies and relationships
- Assess robustness of existing components

**PLAN Phase** (Second Order Effects + Interdependencies)
- Design solutions considering cascading impacts
- Plan for ripple effects across the system
- Create structured implementation roadmap

**RECHECK Phase** (Systems Thinking)
- Validate plan against system requirements
- Check for unintended consequences
- Verify integration points

**PAUSE Phase** (Inversion)
- Consider what could go wrong
- Identify failure modes and mitigation strategies
- Challenge assumptions

**CREATE Phase** (First Principles)
- Implement based on fundamental requirements
- Build with minimal complexity
- Focus on core functionality

**RECHECK Phase** (All Models)
- Validate implementation works correctly
- Check for second order effects
- Verify system integration

**REFINE Phase** (Continuous Improvement)
- Optimize based on testing results
- Address discovered issues
- Enhance robustness

**FINAL RECHECK Phase** (Holistic Validation)
- Complete system validation
- Cross-model verification
- Final quality assurance

**EXIT**: Document decisions and lessons learned

### **Practical Application**

This methodology was applied to:
- Agent scaffolding toolkit development
- Path calculation corrections (nested .claude folder elimination)
- YAML structure validation
- Multi-agent system orchestration design

## Development Guidelines

### Adding New Features

1. **Apply methodology**: Use check→plan→recheck→pause→create→recheck→refine→recheck→exit
2. **Create constants** in `cli/constants.py` for magic numbers
3. **Write tests** in appropriate `tests/test_*.py` file
4. **Update configurations** if adding new config options
5. **Document changes** in relevant docs files
6. **Run full test suite** before committing
7. **Consider second order effects** of changes
8. **Validate system integration** thoroughly

### Configuration Development

1. **Test selectors** using browser dev tools
2. **Validate with** `python3 cli/config_validator.py`
3. **Start with small** `max_pages` (20-50) for testing
4. **Use estimate_pages** to validate URL patterns
5. **Test categorization** with sample data

### MCP Tool Development

1. **Add tool** to `skill_seeker_mcp/server.py`
2. **Update tool list** in documentation
3. **Write tests** in `tests/test_mcp_server.py`
4. **Test with** `./setup_mcp.sh` script
5. **Update README.md** with new tool examples

## Important File Locations

- **Main scraper**: `cli/doc_scraper.py:228-251` (scrape_all)
- **Enhanced SKILL.md generation**: `cli/doc_scraper.py:426-542`
- **Conflict detection**: `cli/conflict_detector.py`
- **MCP server**: `skill_seeker_mcp/server.py`
- **Configuration validation**: `cli/config_validator.py`
- **Constants**: `cli/constants.py`
- **Test runner**: `cli/run_tests.py`

## Common Issues and Solutions

### Virtual Environment
Always use a virtual environment to avoid dependency conflicts:
```bash
source venv/bin/activate  # Required for each new terminal session
```

### Rate Limiting
If getting blocked by documentation servers:
1. Increase `rate_limit` in config (try 1.0 or 2.0)
2. Use `--async` mode for better performance
3. Add more exclude patterns for non-essential URLs

### Memory Issues
For large documentation (>10K pages):
1. Use `--async` mode (66% less memory)
2. Split config using `split_config.py`
3. Use checkpoint/resume functionality

### MCP Integration Issues
1. Ensure Python 3.10+ is installed
2. Run `./setup_mcp.sh` for proper configuration
3. Restart Claude Code after configuration
4. Check Claude Code logs for errors

## Additional Documentation

- **Complete User Guide**: [README.md](README.md)
- **Beginner's Guide**: [BULLETPROOF_QUICKSTART.md](BULLETPROOF_QUICKSTART.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **MCP Setup**: [docs/MCP_SETUP.md](docs/MCP_SETUP.md)
- **Multi-Source Scraping**: [docs/UNIFIED_SCRAPING.md](docs/UNIFIED_SCRAPING.md)
- **Enhancement Guide**: [docs/ENHANCEMENT.md](docs/ENHANCEMENT.md)
- **Testing Documentation**: [docs/TESTING.md](docs/TESTING.md)

## Project Status

- **Active Development**: Yes, task-based incremental approach
- **Production Ready**: Yes, v2.0.0 with unified scraping
- **Test Coverage**: 299 tests, 100% pass rate
- **MCP Integration**: Fully functional with 9 tools
- **Documentation**: Comprehensive guides and examples

The project is actively maintained with a flexible roadmap approach. See [FLEXIBLE_ROADMAP.md](FLEXIBLE_ROADMAP.md) for planned features and development tasks.