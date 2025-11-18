# Skill Seekers + TACHES Prompts Hub

This directory contains Claude Code slash commands from [TACHES](https://github.com/glittercowboy/taches-cc-prompts), integrated with Skill Seekers to create a comprehensive development hub.

## Two Complementary Systems

### Skill Seekers (MCP Tools)
Build AI skills from documentation:
- `mcp__skill-seeker__scrape_docs` - Scrape and build skills
- `mcp__skill-seeker__generate_config` - Generate configs
- `mcp__skill-seeker__package_skill` - Package for upload
- See [MCP_SETUP.md](../../docs/MCP_SETUP.md) for full list

### TACHES Prompts (Slash Commands)
Workflow automation for Claude Code:
- `/create-prompt` - Generate rigorous prompts from natural language
- `/run-prompt` - Execute prompts in fresh sub-agents
- `/add-to-todos` - Capture ideas without losing focus
- `/check-todos` - Resume work from your backlog
- `/whats-next` - Create handoff documents for context switching

## Available Commands

### Meta-Prompting
Delegate prompt engineering to Claude itself for complex tasks.

```bash
/create-prompt I want to add a new scraper for API documentation
```

Claude asks clarifying questions, then generates a specification-grade prompt with:
- XML structure for clarity
- Success criteria
- Verification steps
- "What to avoid and why"

See: [meta-prompting/README.md](meta-prompting/README.md)

### Todo Management
Capture ideas mid-conversation without derailing current work.

```bash
# While working on feature A, you notice a bug
/add-to-todos Fix the rate limiter edge case in scraper

# Later, check your backlog
/check-todos
```

See: [todo-management/README.md](todo-management/README.md)

### Context Handoff
Continue work across sessions without losing progress.

```bash
# End of session - create handoff
/whats-next

# Creates structured document with:
# - What was completed
# - What remains
# - Critical context
```

See: [context-handoff/README.md](context-handoff/README.md)

## Usage Example: Building a New Skill

```bash
# 1. Use meta-prompting to plan complex scraping
/create-prompt I want to create a unified config that scrapes React docs,
GitHub examples, and community patterns into one comprehensive skill

# 2. Claude generates rigorous prompt, you execute it
# 3. While working, capture related ideas
/add-to-todos Add conflict detection for React hooks documentation

# 4. End session with handoff
/whats-next

# 5. Package the result using Skill Seekers
skill-seekers package output/react_comprehensive/
```

## File Structure

```
.claude/commands/
├── README.md                    # This file
├── create-prompt.md             # Meta-prompting: generate prompts
├── run-prompt.md                # Meta-prompting: execute prompts
├── add-to-todos.md              # Todo: capture tasks
├── check-todos.md               # Todo: review backlog
├── whats-next.md                # Handoff: context switching
├── meta-prompting/
│   └── README.md                # Documentation
├── todo-management/
│   ├── README.md                # Documentation
│   └── todo-management.html     # HTML todo viewer
└── context-handoff/
    └── README.md                # Documentation
```

## Installation

These commands are already installed in this repository. They work automatically when using Claude Code in this project.

To install globally (available in any project):

```bash
cp .claude/commands/*.md ~/.claude/commands/
```

## Per-Project Data

Commands store data per-project:
- `.prompts/` - Generated prompts (meta-prompting)
- `.todos/` - Captured tasks (todo-management)
- `.handoffs/` - Context documents (context-handoff)

These directories are created automatically as needed.

## Credits

- **TACHES Prompts**: https://github.com/glittercowboy/taches-cc-prompts
- **Skill Seekers**: https://github.com/yusufkaraaslan/Skill_Seekers

---

Combined to create a unified hub for AI-assisted development workflows.
