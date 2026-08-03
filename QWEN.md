# QWEN.md - Skill Seekers

> **This file is intentionally short.** The full agent reference lives in
> **[AGENTS.md](AGENTS.md)** — read it first. Keeping one canonical file avoids the
> drift that previously left this one advertising three different version numbers
> at once (v3.6.0, 3.3.0, and "17+ source types" alongside "18 source types").

## Project in one paragraph

**Skill Seekers** is a Python CLI tool and MCP server that converts documentation
sites, GitHub repositories, PDFs, videos, notebooks, wikis and more — **18 source
types** — into structured, AI-ready skills and RAG knowledge for **22 export
targets** (12 LLM platforms, 8 RAG/vector targets, plus Atlas and IBM Bob).
Published on PyPI as `skill-seekers`.

The version is deliberately **not** hardcoded here — read it from
`pyproject.toml` (`[project] version`), which is the single source of truth.

## Essential commands

```bash
# REQUIRED before running tests or the CLI (src/ layout)
pip install -e .

# Tests — all must pass before committing
pytest tests/ -v

# Fast iteration (skips the slow suites)
pytest tests/ -m "not slow and not integration and not e2e and not network and not serial and not mcp_only" -q

# Code quality — must pass before push (CI pins ruff 0.15.8)
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/skill_seekers
```

## Primary entry points

```bash
skill-seekers create <source>                 # auto-detects URL, owner/repo, ./path, file.pdf, ...
skill-seekers scan <dir>                      # AI-driven discovery → one config per detected framework
skill-seekers package <dir> --target claude   # 22 targets available
```

## Where to look

| Topic | File |
|---|---|
| **Full agent reference** | **[AGENTS.md](AGENTS.md)** |
| Claude Code specifics | [CLAUDE.md](CLAUDE.md) |
| Architecture + UML | [docs/UML_ARCHITECTURE.md](docs/UML_ARCHITECTURE.md) |
| CLI reference | [docs/reference/CLI_REFERENCE.md](docs/reference/CLI_REFERENCE.md) |
| Troubleshooting | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |
| Contributing | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Changelog | [CHANGELOG.md](CHANGELOG.md) |

## Conventions that matter

- **Source layout:** `src/skill_seekers/` — always `pip install -e .` first; `tests/conftest.py` hard-exits if the package isn't importable.
- **CLI flags:** define them **only** in the central parser (`cli/parsers/*.py`). A drift-guard test fails CI otherwise.
- **New source type:** register in `CONVERTER_REGISTRY` (`cli/skill_converter.py`) — it then works in unified configs automatically.
- **New platform target:** add an adaptor under `cli/adaptors/` and register it in `adaptors/__init__.py`.
- **AI calls:** everything routes through `AgentClient` (`cli/agent_client.py`). Do not call provider SDKs directly.
- **Style:** line length 100, ruff rules `E,W,F,I,B,C4,UP,ARG,SIM`, modern typing (`str | None`, `list[str]`).
