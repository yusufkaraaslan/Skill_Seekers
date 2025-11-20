# Meta-Prompting System for Claude Code

A systematic approach to building complex software with Claude Code by delegating prompt engineering to Claude itself.

## The Problem

When building complex features, most people either:

- Write vague prompts → get mediocre results → iterate 20+ times
- Spend hours crafting detailed prompts manually
- Pollute their main context window with exploration, analysis, and implementation all mixed together

## The Solution

This system separates **analysis** from **execution**:

1. **Analysis Phase** (main context): Tell Claude what you want in natural language. It asks clarifying questions, analyzes your codebase, and generates a rigorous, specification-grade prompt.

2. **Execution Phase** (fresh sub-agent): The generated prompt runs in a clean context window, producing high-quality implementation on the first try.

## What Makes This Effective

The system consistently generates prompts with:

- **XML structure** for clear semantic organization
- **Contextual "why"** - explains purpose, audience, and goals
- **Success criteria** - specific, measurable outcomes
- **Verification protocols** - how to test that it worked
- **"What to avoid and WHY"** - prevents common mistakes with reasoning
- **Extended thinking triggers** - for complex tasks requiring deep analysis
- **Trade-off analysis** - considers multiple approaches and their implications

Most developers don't naturally think through all these dimensions. This system does, every time.

## Installation

**Install globally** - commands work in any directory:

```bash
cp create-prompt.md ~/.claude/commands/
cp run-prompt.md ~/.claude/commands/
```

**Create prompts directory per-project** (optional - created automatically if missing):

```bash
cd /your/project
mkdir .prompts
```

The `/create-prompt` and `/run-prompt` commands are available everywhere. Each project stores its prompts in `.prompts/` in the working directory.

## Usage

### Basic Workflow

```bash
# 1. Describe what you want
/create-prompt I want to build a dashboard for user analytics with real-time graphs

# 2. Answer clarifying questions (if asked)
# Claude will ask about specifics: data sources, chart types, frameworks, etc.

# 3. Review and confirm
# Claude shows you what it understood and asks if you want to proceed

# 4. Choose execution strategy
# After prompt is created, you get options:
# 1. Run prompt now
# 2. Review/edit prompt first
# 3. Save for later
# 4. Other

# 5. Execute
# If you chose "1", it automatically runs the prompt in a fresh sub-agent
```

### When to Use This

**Use meta-prompting for:**

- Complex refactoring across multiple files
- New features requiring architectural decisions
- Database migrations and schema changes
- Performance optimization requiring analysis
- Any task with 3+ distinct steps

**Skip meta-prompting for:**

- Simple edits (change background color)
- Single-file tweaks
- Obvious, straightforward tasks
- Quick experiments

### Advanced: Multiple Prompts

For complex projects, Claude may break your request into multiple prompts:

**Parallel execution** (independent tasks):

```bash
# Claude detects independent modules and offers:
# 1. Run all prompts in parallel now (launches 3 sub-agents simultaneously)
# 2. Run prompts sequentially instead
# 3. Review/edit prompts first
```

**Sequential execution** (dependent tasks):

```bash
# Claude detects dependencies and offers:
# 1. Run prompts sequentially now (one completes before next starts)
# 2. Run first prompt only
# 3. Review/edit prompts first
```

### Prompt Organization

**Global commands, per-project prompts:**

```
~/.claude/commands/          # Install once
  create-prompt.md
  run-prompt.md

/your/project/              # Each project has its own prompts
  .prompts/
    ├── 001-implement-auth.md
    ├── 002-create-dashboard.md
    └── completed/
        └── 001-implement-auth.md  # Archived after execution

/another/project/           # Different project, different prompts
  .prompts/
    └── 001-setup-database.md
```

After successful execution, prompts are automatically moved to `.prompts/completed/` with metadata.

## Why This Works

The system transforms vague ideas into rigorous specifications by:

1. **Asking the right questions** - Clarifies ambiguity before generating anything
2. **Adding structure automatically** - XML tags, success criteria, verification steps
3. **Explaining constraints** - Not just "what" but "WHY" things should be done certain ways
4. **Thinking about failure modes** - "What to avoid and why" prevents common mistakes
5. **Defining done** - Clear, measurable success criteria so you know when it's complete

This level of systematic thinking is hard to maintain manually, especially when you're focused on solving the problem itself.

## The Context Advantage

With Claude Max plan, token usage doesn't matter. What matters is **context quality**.

**Without meta-prompting:**

- Main window fills with: codebase exploration + requirements gathering + implementation + debugging + iteration
- Context becomes cluttered with analytical work mixed with execution

**With meta-prompting:**

- Main window: Clean requirements gathering and prompt generation
- Sub-agent: Fresh context with only the pristine specification
- Result: Higher quality implementation, cleaner separation of concerns

## Tips for Best Results

1. **Be conversational in initial request** - Don't try to write a perfect prompt yourself, just explain what you want naturally

2. **Answer clarifying questions thoroughly** - The quality of your answers directly impacts the generated prompt

3. **Review generated prompts** - They're saved as markdown files; you can edit them before execution

4. **Trust the system** - It asks "what to avoid and why", defines success criteria, and includes verification steps you might forget

5. **Use parallel execution** - If Claude detects independent tasks, running them in parallel saves time without token concerns

## How It Works Under the Hood

1. **create-prompt** analyzes your request using structured thinking:

   - Clarity check (would a colleague understand this?)
   - Task complexity assessment
   - Single vs multiple prompts decision
   - Parallel vs sequential execution strategy
   - Reasoning depth needed
   - Project context requirements
   - Verification needs

2. Conditionally includes advanced features:

   - Extended thinking triggers for complex reasoning
   - "Go beyond basics" language for ambitious tasks
   - WHY explanations for constraints
   - Parallel tool calling guidance
   - Reflection after tool use for agentic workflows

3. **run-prompt** delegates to fresh sub-agent(s):
   - Reads the generated prompt(s)
   - Spawns sub-agent(s) with clean context
   - Waits for completion
   - Archives prompts to `/completed/`
   - Returns consolidated results

## Credits

Developed by TÂCHES for systematic, high-quality Claude Code workflows.

---

**Watch the full explanation:** [Stop Telling Claude Code What To Do](https://www.youtube.com/@tachesteaches)

**Questions or improvements?** Open an issue or submit a PR.

—TÂCHES
