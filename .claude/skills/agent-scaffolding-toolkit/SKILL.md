---
name: agent-scaffolding-toolkit
type: project-specific
category: Development & Programming
location: .claude/skills/agent-scaffolding-toolkit/
version: 2.0.0
description: Meta-capability toolkit for programmatic agent/command creation with validation, versioning, registry management, and Skill Seekers integration. Features interactive wizard, LLM-assisted validation, and auto-discovery hooks.
---

## 🎯 Quick Value (5-second scan)

**Create production-ready Claude Code agents in 60 seconds** with:
- Interactive wizard (zero learning curve)
- Battle-tested templates (orchestrator, referee, specialist)
- Auto-validation (YAML + behavioral + security)
- Registry management (version tracking, delegation graphs)
- Skill Seekers export (agents → skills/configs)

### 🚀 Instant Start

```bash
# Setup (one-time)
cd .claude/skills/agent-scaffolding-toolkit
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Create agent (interactive wizard)
python scripts/create_agent.py

# List all agents
python scripts/list_agents.py
```

### 📋 Available Templates

| Agent Type | Primary Use | Tools | Delegates To |
|------------|-------------|-------|--------------|
| `orchestrator` | Multi-agent coordination, parallel execution | Task, Bash | Multiple specialists |
| `referee` | Deterministic synthesis, metric-driven selection | Read, Bash, Task | None (evaluates outputs) |
| `specialist` | Domain-specific (code-analyzer, test-generator, etc.) | Customizable | Optional delegation |

## 🔧 Generation Workflow (Interactive Wizard)

The wizard guides you through **4 surgical decisions**:

1. **Role Selection** (What problem does this agent solve?)
2. **Tool Assignment** (What native Claude Code tools needed?)
3. **Model Specification** (Opus for synthesis, Sonnet/Haiku for tasks)
4. **Customization** (Modify prompts, add specific constraints)

**Result**: Production-ready agent in `.claude/agents/` with proper YAML structure.

## ⚡ Performance Architecture

### Semantic Compression
- **Layer 1** (this file): Immediate value, minimal tokens
- **Layer 2** (references/): Detailed patterns on-demand
- **Templates**: Battle-tested, easily customizable

### Zero-Dependency Design
- **No external APIs**: Pure Claude Code native tools
- **No complex setup**: Single command execution
- **No breaking changes**: Backward-compatible template system

## 🎯 Use Cases (Pain Points Solved)

### ✅ **Human-in-the-Loop Elimination**
- **Before**: Manual agent creation, YAML validation, tool selection
- **After**: 60-second wizard-guided generation, automatic validation

### ✅ **Consistency Enforcement**
- **Before**: Inconsistent agent structures, forgotten tools
- **After**: Battle-tested templates, automatic validation

### ✅ **Rapid Prototyping**
- **Before**: Hours crafting agent system prompts
- **After**: Minutes with intelligent defaults and customization

## 🛠️ Advanced Features

### Hook System (Auto-Validation & Registry)
**Configured in `.claude/settings.json`:**

- **SessionStart**: Load registry, inject agent list into context
- **PreToolUse**: Quick syntax check (non-blocking)
- **PostToolUse**: LLM validation + deterministic fallback + registry update

**Benefits:**
- Auto-discover agents on creation
- Validate YAML + behavior before save
- Track versions, usage stats, delegation graphs

### Registry Management
```bash
# View all registered agents
python scripts/list_agents.py

# Query agent by name
python scripts/list_agents.py --name code-analyzer

# Show delegation graph
python scripts/list_agents.py --show-graph
```

**Registry Schema** (`.claude/skills/agent-scaffolding-toolkit/assets/agent_registry.json`):
- Metadata: name, type, description, tools
- History: created_at, updated_at, version
- Stats: invocation_count, success_rate
- Delegation: delegates_to (multi-agent composition)

### Validation Engine
- **Structural**: YAML frontmatter, required fields (name, type, description ≥50 chars)
- **Behavioral**: Tool existence in Claude Code, description quality, security anti-patterns
- **LLM-Assisted**: Semantic validation via PostToolUse hook (with deterministic fallback)

### Skill Seekers Integration
```bash
# Export agent as Skill
python scripts/export_to_skill_seekers.py \
  --agent code-analyzer \
  --output-type skill

# Export agent as Config (for scraping)
python scripts/export_to_skill_seekers.py \
  --agent test-generator \
  --output-type config
```

**Features:**
- Conflict detection (agent vs. skill/config discrepancies)
- Version sync across systems
- Multi-source integration (agents + docs + code)

## 📚 Progressive Documentation

**Layer 2** (references/) contains:
- **AGENT_SCHEMA.md**: Complete YAML specification
- **BEST_PRACTICES.md**: Design patterns & anti-patterns
- **COMPOSITION_PATTERNS.md**: Multi-agent orchestration
- **TROUBLESHOOTING.md**: Common issues & solutions
- **Troubleshooting** (Common agent configuration issues)

---

*🎯 **Next Step**: Run `python scripts/list_templates.py` to see available templates, then `python scripts/create_agent.py` to begin interactive agent creation. Agents will be created in `../../.claude/agents/` for project-wide availability.*