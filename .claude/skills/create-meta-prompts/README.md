# Create Meta-Prompts

The skill-based evolution of the [meta-prompting](../../prompts/meta-prompting/) system. Creates prompts optimized for Claude-to-Claude pipelines with improved dependency detection and structured outputs.

## The Problem

Complex tasks benefit from staged workflows: research first, then plan, then implement. But manually crafting prompts that produce structured outputs for subsequent prompts is tedious. Each stage needs metadata (confidence, dependencies, open questions) that the next stage can parse.

## The Solution

`/create-meta-prompt` creates prompts designed for multi-stage workflows. Outputs (research.md, plan.md) are structured with XML metadata for efficient parsing by subsequent prompts. Each prompt gets its own folder with clear provenance and automatic dependency detection.

## Commands

### `/create-meta-prompt [description]`

Describe your task. Claude creates a prompt optimized for its purpose.

**What it does:**
1. Determines purpose: Do (execute), Plan (strategize), or Research (gather info)
2. Detects existing research/plan files to chain from
3. Creates prompt with purpose-specific structure
4. Saves to `.prompts/{number}-{topic}-{purpose}/`
5. Runs with dependency-aware execution

**Usage:**
```bash
# Research task
/create-meta-prompt research authentication options for the app

# Planning task
/create-meta-prompt plan the auth implementation approach

# Implementation task
/create-meta-prompt implement JWT authentication
```

## Installation

**Install command** (global):
```bash
cp commands/*.md ~/.claude/commands/
```

**Install skill**:
```bash
cp -r skills/* ~/.claude/skills/
```

## Example Workflow

**Full research → plan → implement chain:**

```
You: /create-meta-prompt research authentication libraries for Node.js

Claude: [Asks about depth, sources, output format]

You: [Answer questions]

Claude: [Creates research prompt]
✓ Created: .prompts/001-auth-research/001-auth-research.md

What's next?
1. Run prompt now
2. Review/edit prompt first

You: 1

Claude: [Executes research]
✓ Output: .prompts/001-auth-research/auth-research.md
```

```
You: /create-meta-prompt plan the auth implementation

Claude: Found existing files: auth-research.md
Should this prompt reference any existing research?

You: [Select auth-research.md]

Claude: [Creates plan prompt referencing the research]
✓ Created: .prompts/002-auth-plan/002-auth-plan.md

You: 1

Claude: [Executes plan, reads research output]
✓ Output: .prompts/002-auth-plan/auth-plan.md
```

```
You: /create-meta-prompt implement the auth system

Claude: Found existing files: auth-research.md, auth-plan.md
[Detects it should reference the plan]

Claude: [Creates implementation prompt]
✓ Created: .prompts/003-auth-implement/003-auth-implement.md

You: 1

Claude: [Executes implementation following the plan]
✓ Implementation complete
```

## File Structure

```
create-meta-prompts/
├── README.md
├── commands/
│   └── create-meta-prompt.md
└── skills/
    └── create-meta-prompts/
        ├── SKILL.md
        └── references/
            ├── do-patterns.md
            ├── plan-patterns.md
            ├── research-patterns.md
            ├── question-bank.md
            └── intelligence-rules.md
```

**Generated prompts structure:**
```
.prompts/
├── 001-auth-research/
│   ├── completed/
│   │   └── 001-auth-research.md    # Prompt (archived after run)
│   └── auth-research.md            # Output
├── 002-auth-plan/
│   ├── completed/
│   │   └── 002-auth-plan.md
│   └── auth-plan.md
└── 003-auth-implement/
    └── 003-auth-implement.md       # Prompt
```

## Why This Works

**Structured outputs for chaining:**
- Research and plan outputs include XML metadata
- `<confidence>`, `<dependencies>`, `<open_questions>`, `<assumptions>`
- Subsequent prompts can parse and act on this structure

**Automatic dependency detection:**
- Scans for existing research/plan files
- Suggests relevant files to chain from
- Executes in correct order (sequential/parallel/mixed)

**Clear provenance:**
- Each prompt gets its own folder
- Outputs stay with their prompts
- Completed prompts archived separately

---

**Questions or improvements?** Open an issue or submit a PR.

—TÂCHES
