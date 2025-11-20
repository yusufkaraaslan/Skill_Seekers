# TÂCHES Claude Code Resources - Installation Summary

**Installation Date:** November 20, 2025
**Source:** https://github.com/glittercowboy/taches-cc-resources

## What Was Installed

### 📋 Commands (15+ root commands + subdirectories)

**Meta-Prompting:**
- `/create-prompt` - Generate optimized prompts with XML structure
- `/run-prompt` - Execute saved prompts in sub-agent contexts

**Todo Management:**
- `/add-to-todos` - Capture tasks with full context
- `/check-todos` - Resume work on captured tasks

**Context Handoff:**
- `/whats-next` - Create handoff document for fresh context

**Create Extensions:**
- `/create-agent-skill` - Create a new skill
- `/create-meta-prompt` - Create staged workflow prompts
- `/create-slash-command` - Create a new slash command
- `/create-subagent` - Create a new subagent
- `/create-hook` - Create a new hook

**Audit Extensions:**
- `/audit-skill` - Audit skill for best practices
- `/audit-slash-command` - Audit command for best practices
- `/audit-subagent` - Audit subagent for best practices

**Self-Improvement:**
- `/heal-skill` - Fix skills based on execution issues

### 📁 Command Categories

Subdirectories with specialized commands:
- `consider/` - 12 thinking model commands (pareto, first-principles, inversion, etc.)
- `write/` - 8 content generation commands (email, blog, docs, tutorial, etc.)
- `plan/` - 5 planning commands (brief, breakdown, sprint, project, mvp)
- `research/` - 8 research commands (technical, options, competitive, feasibility, etc.)
- `explain/` - 12 explanation commands (eli5, analogy, socratic, visual, etc.)
- `extract/` - 2 extraction commands (spec, ui)
- `summarize/` - 9 summarization commands (tldr, key-points, bullet, etc.)

### �� Agents (3 specialized subagents)
- `skill-auditor` - Expert skill auditor for best practices compliance
- `slash-command-auditor` - Expert slash command auditor
- `subagent-auditor` - Expert subagent configuration auditor

### 🎯 Skills (5 skill packages)
- `create-agent-skills/` - Build skills by describing what you want
- `create-meta-prompts/` - Build prompts with structured outputs
- `create-slash-commands/` - Build commands that expand into full prompts
- `create-subagents/` - Build specialized Claude instances
- `create-hooks/` - Build event-driven automation

## How to Use

### Start Using Commands Immediately

All commands are now available in your Claude Code session. Example usage:

```bash
# Generate optimized prompt
/create-prompt

# Manage todos
/add-to-todos Implement unified scraping test fixes
/check-todos

# Create extensions
/create-slash-command
/create-agent-skill

# Think through decisions
/consider:pareto
/consider:first-principles

# Plan work
/plan:brief
/plan:sprint

# Research
/research:technical
/research:options

# Write content
/write:docs
/write:spec

# Explain concepts
/explain:eli5
/explain:layers
```

### Command Discovery

- Browse all commands: `ls .claude/commands/`
- Check specific category: `ls .claude/commands/plan/`
- Read command details: `cat .claude/commands/create-prompt.md`

## Integration with Skill Seekers

These TÂCHES resources are now integrated into your Skill Seekers development workflow. You can:

1. **Create Skills** - Use `/create-agent-skill` to build new skills for your scraped documentation
2. **Plan Features** - Use `/plan:*` commands to organize roadmap tasks
3. **Write Documentation** - Use `/write:docs` or `/write:tutorial` for user guides
4. **Research** - Use `/research:*` commands when exploring new integrations
5. **Think Through Decisions** - Use `/consider:*` commands for architectural choices

## File Locations

```
/workspaces/Skill_Seekers/.claude/
├── commands/           # 15+ root commands + subdirectories
│   ├── consider/       # Thinking model commands
│   ├── write/          # Content generation
│   ├── plan/           # Planning commands
│   ├── research/       # Research commands
│   ├── explain/        # Explanation commands
│   ├── extract/        # Extraction commands
│   └── summarize/      # Summarization commands
├── agents/             # 3 auditor subagents
└── skills/             # 5 skill packages
```

## More Information

- **Original Repository:** https://github.com/glittercowboy/taches-cc-resources
- **Community Ports:** [OpenCode](https://github.com/stephenschoettler/taches-oc-prompts)
- **TÂCHES Website:** More resources coming soon

---

**Installation Complete!** Start a new Claude Code session or continue in this one to use the commands.
