# Claude Code Configuration

This directory contains Claude Code configuration, agents, commands, skills, and hooks for the Skill Seekers project.

## 📁 Structure

```
.claude/
├── settings.json              # Hook configurations (project-level)
├── settings.local.json.example # Local overrides template (gitignored)
├── scripts/                   # Hook execution scripts
│   ├── check-hooks.py         # Hook validation system
│   ├── load-agent-registry.py
│   ├── check-agent-behavior.py
│   ├── validate-agent.py
│   ├── update-registry.py
│   └── git-pre-commit-hook
├── agents/                    # Custom AI agents
│   ├── orchestrator-agent.md
│   ├── referee-agent-csp.md
│   ├── security-analyst.md
│   ├── code-analyzer.md
│   ├── test-generator.md
│   └── performance-auditor.md
├── commands/                  # Reusable workflows
│   ├── check-hook.md          # Hook validation system
│   ├── refine-agent.md
│   └── update-CLAUDE.md
├── tests/                     # Comprehensive test suite
│   ├── conftest.py           # Shared fixtures
│   ├── requirements.txt      # Test dependencies
│   ├── README.md             # Test documentation
│   ├── fixtures/             # Sample agents
│   ├── unit/                 # Unit tests (8 tests)
│   ├── integration/          # Integration tests (9 tests)
│   └── e2e/                  # End-to-end tests (4 tests)
└── skills/                    # Knowledge repositories
    └── agent-scaffolding-toolkit/
        ├── SKILL.md
        ├── .venv/            # Skill-specific virtual environment
        ├── requirements.txt  # Skill dependencies (PyYAML, etc.)
        ├── scripts/          # Agent creation wizard & export
        │   └── export_to_skill_seekers.py
        ├── templates/        # Agent templates
        ├── references/       # Documentation
        ├── assets/           # agent_registry.json
        └── tests/            # Test suite
```

---

## 🚀 Setup

### **1. Install Skill Dependencies**

The hook scripts require the agent-scaffolding-toolkit's virtual environment:

```bash
# Navigate to skill directory
cd .claude/skills/agent-scaffolding-toolkit

# Create virtual environment (if it doesn't exist)
python3 -m venv .venv

# Activate venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

**Required dependencies:**
- `PyYAML>=6.0` - For YAML frontmatter parsing in agents

### **2. Install Git Pre-Commit Hook (Optional)**

To validate agents before Git commits:

```bash
# From project root
cp .claude/scripts/git-pre-commit-hook .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

---

## 🎯 How It Works

### **Hooks System**

Claude Code hooks are configured in `.claude/settings.json`:

1. **SessionStart** - Loads agent registry when Claude Code starts
   - Injects available agents into session context
   - Shows agent names, descriptions, and delegation graph

2. **PreToolUse** - Quick syntax validation before writing agent files
   - Checks YAML frontmatter structure
   - Non-blocking (warns only)

3. **PostToolUse** - Comprehensive validation after writing agent files
   - **LLM-based validation** (primary): Semantic checks using Claude
   - **Command-based fallback**: Deterministic validation if LLM times out
   - Auto-updates `agent_registry.json`

### **Agent Registry**

The registry (`.claude/skills/agent-scaffolding-toolkit/assets/agent_registry.json`) tracks:
- Agent metadata (name, type, description)
- Tools used by each agent
- Delegation graph (which agents delegate to others)
- Version history (created_at, updated_at, version)
- Usage stats (invocation_count, success_rate)

**Auto-updated** by PostToolUse hooks whenever agents are created/edited.

---

## 📝 Creating Custom Agents

### **Method 1: Use the Agent Scaffolding Toolkit** (Recommended)

```bash
# Activate skill venv
cd .claude/skills/agent-scaffolding-toolkit
source .venv/bin/activate

# Run interactive wizard
python scripts/create_agent.py

# Follow prompts to create agent
```

### **Method 2: Manual Creation**

Create a new `.md` file in `.claude/agents/` with YAML frontmatter:

```markdown
---
name: my-custom-agent
type: specialist
description: A detailed description of what this agent does (min 50 chars)
tools:
  - read_file
  - write_file
delegates_to: []
---

# My Custom Agent

## Capabilities

(Describe what this agent can do)

## Example Use Cases

(Provide concrete examples)
```

**Hooks will automatically:**
- Validate YAML structure
- Check tool existence
- Update registry
- Version the agent

---

## 🧪 Testing

Run the comprehensive test suite:

```bash
cd .claude/skills/agent-scaffolding-toolkit
source .venv/bin/activate

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=scripts --cov-report=html

# Run specific test category
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/e2e/ -v
```

---

## 🔧 Troubleshooting

### **Hook Scripts Fail with "No module named 'yaml'"**

**Solution**: Install skill dependencies in the venv:
```bash
cd .claude/skills/agent-scaffolding-toolkit
source .venv/bin/activate
pip install -r requirements.txt
```

### **Hooks Don't Run**

**Check:**
1. `.claude/settings.json` exists in project root
2. Skill venv exists at `.claude/skills/agent-scaffolding-toolkit/.venv`
3. Hook scripts are executable: `chmod +x .claude/scripts/*.py`
4. Claude Code has been restarted (hooks load at startup)

### **Agent Not Discovered by Claude Code**

**Solution**: 
1. Check agent file has valid YAML frontmatter (starts with `---`)
2. Run registry update manually:
   ```bash
   cd .claude/skills/agent-scaffolding-toolkit
   source .venv/bin/activate
   python ../scripts/update-registry.py
   ```
3. Restart Claude Code session

### **Git Pre-Commit Hook Blocks Valid Agents**

**Debug**:
```bash
# Test validation manually
export CLAUDE_PROJECT_DIR=$(pwd)
.claude/skills/agent-scaffolding-toolkit/.venv/bin/python3 .claude/scripts/validate-agent.py <<EOF
{
  "tool_input": {
    "file_path": ".claude/agents/my-agent.md"
  }
}
EOF
```

---

## 📚 Additional Documentation

- **Agent Schema**: `.claude/skills/agent-scaffolding-toolkit/references/AGENT_SCHEMA.md`
- **Best Practices**: `.claude/skills/agent-scaffolding-toolkit/references/BEST_PRACTICES.md`
- **Composition Patterns**: `.claude/skills/agent-scaffolding-toolkit/references/COMPOSITION_PATTERNS.md`
- **Troubleshooting**: `.claude/skills/agent-scaffolding-toolkit/references/TROUBLESHOOTING.md`

---

## Integration with Skill Seekers

The agent scaffolding toolkit integrates with the broader Skill Seekers ecosystem:

### Export Agents to Skills

```bash
# Export all agents to Skill Seekers format
cd .claude/skills/agent-scaffolding-toolkit
source .venv/bin/activate
python scripts/export_to_skill_seekers.py

# Export with conflict detection
python scripts/export_to_skill_seekers.py --detect-conflicts

# Export and package as .zip files
python scripts/export_to_skill_seekers.py --package
```

**What gets exported:**
- `SKILL.md`: Skill documentation with agent capabilities
- `{agent-name}.json`: Skill Seekers configuration
- `agent_definition.md`: Original agent definition
- `metadata.json`: Export metadata

**Export features:**
- Maps agents → Skills/Configs automatically
- Preserves delegation relationships
- Detects conflicts with existing skills
- Optional packaging for distribution
- Registry integration for usage stats

### Use Cases

1. **Share agents as skills**: Export agents for use in other projects
2. **Document agent capabilities**: Generate comprehensive skill documentation
3. **Integrate with Skill Seekers workflows**: Use agents in documentation scraping
4. **Version control**: Track agent evolution through exported skills

---

## 🎓 Quick Reference

### **Available Agents**

| Agent | Type | Purpose |
|-------|------|---------|
| `@orchestrator-agent` | coordinator | Multi-agent orchestration |
| `@referee-agent-csp` | evaluator | Deterministic outcome synthesis |
| `@security-analyst` | specialist | Security analysis & vulnerability detection |
| `@code-analyzer` | specialist | Code complexity, patterns, technical debt |
| `@test-generator` | specialist | Auto-generate comprehensive test suites |
| `@performance-auditor` | specialist | Performance profiling & optimization |

### **Available Commands**

| Command | Purpose |
|---------|---------|
| `/refine-agent` | Multi-mental model agent refinement |
| `/update-CLAUDE.md` | Automatic documentation synchronization |

---

**For detailed documentation, see individual files in `.claude/skills/agent-scaffolding-toolkit/references/`**
