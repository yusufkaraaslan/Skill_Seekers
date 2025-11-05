# Agent Scaffolding Toolkit

A surgical toolkit for creating specialized agents with interactive wizard-guided generation. Eliminates human-in-the-loop dependency while maintaining developer flexibility.

## Quick Setup

### One-Time Setup (60 seconds)

```bash
# Clone/download this skill to .claude/skills/agent-scaffolding-toolkit/
cd .claude/skills/agent-scaffolding-toolkit/

# Run setup script (creates venv, installs dependencies)
./setup.sh
```

### Usage

```bash
# Activate virtual environment (required each session)
source .venv/bin/activate

# Interactive agent creation (60 seconds)
python scripts/create_agent.py

# List available templates
python scripts/list_templates.py

# Validate existing agent
python scripts/validate_agent.py --file .claude/agents/my-agent.md
```

## Dependencies

### Core Dependencies
- **pyyaml>=6.0** - YAML frontmatter parsing
- **Python 3.10+** - Required for modern Python features

### Optional Development Dependencies
```bash
./setup.sh --dev  # Install pytest, black, mypy
```

## Claude Code Integration

This skill is designed for Claude Code workflows:

### Method 1: Use via Skill Tool
In Claude Code, simply ask:
```
Create a security analyst agent using the agent scaffolding toolkit
```

### Method 2: Direct Script Execution
Use the Bash tool in Claude Code:
```bash
cd .claude/skills/agent-scaffolding-toolkit/
source .venv/bin/activate
python scripts/create_agent.py --template specialist --name security-analyst --description "Security analysis specialist"
```

## Agent Templates

| Template | Use Case | Model | Tools |
|----------|----------|-------|-------|
| `orchestrator` | Multi-agent coordination | Opus | Task, Bash, Read, Grep |
| `referee` | Deterministic synthesis/selection | Opus | Read, Bash, Task, Grep |
| `specialist` | Domain-specific expertise | Sonnet | Task, Read, Write, Grep |

## Architecture

### Atomic Scripts
- **create_agent.py** - Interactive wizard for agent creation
- **validate_agent.py** - Structural validation and best practices
- **list_templates.py** - Template discovery and inspection
- **enhance_agent.py** - Agent improvement and customization

### Progressive Documentation
- **Layer 1** (SKILL.md): Immediate value, minimal tokens
- **Layer 2** (references/): Detailed patterns on-demand

## Error Handling

### Missing Dependencies
```bash
# If you see ModuleNotFoundError, run:
./setup.sh
source .venv/bin/activate
```

### Permission Issues
```bash
# Make scripts executable:
chmod +x scripts/*.py
chmod +x setup.sh
```

### Virtual Environment Issues
```bash
# Reset environment:
rm -rf .venv
./setup.sh
```

## File Structure

```
agent-scaffolding-toolkit/
├── SKILL.md                    # Main skill documentation
├── pyproject.toml              # Modern Python packaging
├── requirements.txt            # Dependencies for pip install
├── setup.sh                    # Automated setup script
├── scripts/                    # Atomic utility scripts
│   ├── create_agent.py         # Agent creation wizard
│   ├── validate_agent.py       # Validation engine
│   ├── list_templates.py       # Template discovery
│   └── enhance_agent.py        # Agent enhancement
├── assets/templates/            # Agent templates
│   └── agents/
│       ├── orchestrator.json   # Multi-agent coordination
│       ├── referee.json        # Deterministic synthesis
│       └── specialist.json     # Domain expertise
└── references/                  # Progressive documentation
    ├── architectural-patterns.md
    ├── best-practices.md
    └── troubleshooting.md
```

## Development

### Running Tests
```bash
source .venv/bin/activate
pytest
```

### Code Formatting
```bash
black scripts/
```

### Type Checking
```bash
mypy scripts/
```

## License

MIT License - see repository license file.