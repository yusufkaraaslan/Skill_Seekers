# Create Agent Skills

Build skills by describing what you want in natural language.

## The Problem

You have a repeatable workflow—PDF processing, API integrations, astrological charts—and you want Claude to handle it consistently. Creating effective skills requires understanding YAML frontmatter, XML structure, progressive disclosure, reference files, and a dozen other patterns.

## The Solution

`/create-agent-skill` asks clarifying questions, researches APIs if needed, and generates properly structured skill files automatically. When things don't work perfectly the first time, `/heal-skill` analyzes what went wrong and updates the skill based on what actually worked.

## Commands

### `/create-agent-skill [description]`

Describe what you want. Claude builds the skill.

**What it does:**

1. Asks clarifying questions (scope, output format, APIs needed)
2. Researches current API documentation if external services involved
3. Generates skill with proper structure and reference files
4. Creates slash command wrapper for easy invocation

**Usage:**

```bash
# Describe what you want
/create-agent-skill I want to generate natal charts from birth data

# Or start with the menu
/create-agent-skill
# Select "Create a new skill" or "Update an existing skill"
```

### `/heal-skill [issue]`

Claude learns from failures and improves the skill.

**What it does:**

1. Detects which skill was running from conversation context
2. Analyzes what the skill said to do vs. what actually worked
3. Proposes specific fixes with before/after diffs
4. Gets approval, applies changes, optionally commits

**Usage:**

```bash
# After running into issues
/heal-skill

# Or specify the issue
/heal-skill the API endpoint was deprecated
```

## Installation

**Install commands** (global):

```bash
cp commands/*.md ~/.claude/commands/
```

**Install skill**:

```bash
cp -r skills/* ~/.claude/skills/
```

## Example Workflow

**Create a skill:**

```
You: /create-agent-skill I want to generate astrological natal charts from birth data

Claude: [Asks about calculations, output format, visualization style]

You: [Answer questions]

Claude: [Researches Python astrology libraries]
Claude: [Creates skill and slash command wrapper]

✓ Created skill: generate-natal-chart
✓ Created command: /generate-natal-chart
```

**Use the skill:**

```
You: /generate-natal-chart Lex, January 24 1994, 12:12am, London England

Claude: [Runs skill, hits API issues, figures out the fix]

✓ Generated natal chart
```

**Heal from failures:**

```
You: /heal-skill

Claude: [Analyzes conversation]
"The skill references deprecated V5 API properties.
Here's what needs to change..."

[Shows before/after diffs]

Should I apply these changes?
1. Yes, apply and commit
2. Apply but don't commit
3. Revise the changes
4. Cancel

You: 1

Claude: [Applies fixes, commits]

✓ Skill healed
```

**Next run works correctly:**

```
You: /generate-natal-chart Lex, January 24 1994, 12:12am, London England

Claude: [Generates chart correctly on first try]
```

## File Structure

```
create-agent-skills/
├── README.md
├── commands/
│   ├── create-agent-skill.md
│   └── heal-skill.md
└── skills/
    └── create-agent-skills/
        ├── SKILL.md
        └── references/
            ├── api-security.md
            ├── be-clear-and-direct.md
            ├── common-patterns.md
            ├── core-principles.md
            ├── executable-code.md
            ├── iteration-and-testing.md
            ├── skill-structure.md
            ├── use-xml-tags.md
            └── workflows-and-validation.md
```

## Why This Works

**Self-improvement loop:**

- Run into real problems with real APIs
- `/heal-skill` captures what actually worked
- Future runs work correctly

**Automatic research:**

- Detects when external APIs are involved
- Fetches current documentation before building
- Avoids deprecated patterns

**Proper structure:**

- Pure XML for reliable parsing
- Progressive disclosure keeps skills lean
- Reference files for deep documentation

---

**Watch the full explanation:** [YouTube](https://youtu.be/LJI7FafIDg4)

**Questions or improvements?** Open an issue or submit a PR.

—TÂCHES
