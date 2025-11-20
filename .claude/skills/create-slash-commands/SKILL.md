---
name: create-slash-commands
description: Expert guidance for creating Claude Code slash commands. Use when working with slash commands, creating custom commands, understanding command structure, or learning YAML configuration.
---

<objective>
Create effective slash commands for Claude Code that enable users to trigger reusable prompts with `/command-name` syntax. Slash commands expand as prompts in the current conversation, allowing teams to standardize workflows and operations. This skill teaches you to structure commands with XML tags, YAML frontmatter, dynamic context loading, and intelligent argument handling.
</objective>

<quick_start>

<workflow>
1. Create `.claude/commands/` directory (project) or use `~/.claude/commands/` (personal)
2. Create `command-name.md` file
3. Add YAML frontmatter (at minimum: `description`)
4. Write command prompt
5. Test with `/command-name [args]`
</workflow>

<example>
**File**: `.claude/commands/optimize.md`

```markdown
---
description: Analyze this code for performance issues and suggest optimizations
---

Analyze the performance of this code and suggest three specific optimizations:
```

**Usage**: `/optimize`

Claude receives the expanded prompt and analyzes the code in context.
</example>
</quick_start>

<xml_structure>
All generated slash commands should use XML tags in the body (after YAML frontmatter) for clarity and consistency.

<required_tags>

**`<objective>`** - What the command does and why it matters
```markdown
<objective>
What needs to happen and why this matters.
Context about who uses this and what it accomplishes.
</objective>
```

**`<process>` or `<steps>`** - How to execute the command
```markdown
<process>
Sequential steps to accomplish the objective:
1. First step
2. Second step
3. Final step
</process>
```

**`<success_criteria>`** - How to know the command succeeded
```markdown
<success_criteria>
Clear, measurable criteria for successful completion.
</success_criteria>
```
</required_tags>

<conditional_tags>

**`<context>`** - When loading dynamic state or files
```markdown
<context>
Current state: ! `git status`
Relevant files: @ package.json
</context>
```
(Note: Remove the space after @ in actual usage)

**`<verification>`** - When producing artifacts that need checking
```markdown
<verification>
Before completing, verify:
- Specific test or check to perform
- How to confirm it works
</verification>
```

**`<testing>`** - When running tests is part of the workflow
```markdown
<testing>
Run tests: ! `npm test`
Check linting: ! `npm run lint`
</testing>
```

**`<output>`** - When creating/modifying specific files
```markdown
<output>
Files created/modified:
- `./path/to/file.ext` - Description
</output>
```
</conditional_tags>

<structure_example>

```markdown
---
name: example-command
description: Does something useful
argument-hint: [input]
---

<objective>
Process $ARGUMENTS to accomplish [goal].

This helps [who] achieve [outcome].
</objective>

<context>
Current state: ! `relevant command`
Files: @ relevant/files
</context>

<process>
1. Parse $ARGUMENTS
2. Execute operation
3. Verify results
</process>

<success_criteria>
- Operation completed without errors
- Output matches expected format
</success_criteria>
```
</structure_example>

<intelligence_rules>

**Simple commands** (single operation, no artifacts):
- Required: `<objective>`, `<process>`, `<success_criteria>`
- Example: `/check-todos`, `/first-principles`

**Complex commands** (multi-step, produces artifacts):
- Required: `<objective>`, `<process>`, `<success_criteria>`
- Add: `<context>` (if loading state), `<verification>` (if creating files), `<output>` (what gets created)
- Example: `/commit`, `/create-prompt`, `/run-prompt`

**Commands with dynamic arguments**:
- Use `$ARGUMENTS` in `<objective>` or `<process>` tags
- Include `argument-hint` in frontmatter
- Make it clear what the arguments are for

**Commands that produce files**:
- Always include `<output>` tag specifying what gets created
- Always include `<verification>` tag with checks to perform

**Commands that run tests/builds**:
- Include `<testing>` tag with specific commands
- Include pass/fail criteria in `<success_criteria>`
</intelligence_rules>
</xml_structure>

<arguments_intelligence>
The skill should intelligently determine whether a slash command needs arguments.

<commands_that_need_arguments>

**User provides specific input:**
- `/fix-issue [issue-number]` - Needs issue number
- `/review-pr [pr-number]` - Needs PR number
- `/optimize [file-path]` - Needs file to optimize
- `/commit [type]` - Needs commit type (optional)

**Pattern:** Task operates on user-specified data

Include `argument-hint: [description]` in frontmatter and reference `$ARGUMENTS` in the body.
</commands_that_need_arguments>

<commands_without_arguments>

**Self-contained procedures:**
- `/check-todos` - Operates on known file (TO-DOS.md)
- `/first-principles` - Operates on current conversation
- `/whats-next` - Analyzes current context

**Pattern:** Task operates on implicit context (current conversation, known files, project state)

Omit `argument-hint` and don't reference `$ARGUMENTS`.
</commands_without_arguments>

<incorporating_arguments>

**In `<objective>` tag:**
```markdown
<objective>
Fix issue #$ARGUMENTS following project conventions.

This ensures bugs are resolved systematically with proper testing.
</objective>
```

**In `<process>` tag:**
```markdown
<process>
1. Understand issue #$ARGUMENTS from issue tracker
2. Locate relevant code
3. Implement fix
4. Add tests
</process>
```

**In `<context>` tag:**
```markdown
<context>
Issue details: @ issues/$ARGUMENTS.md
Related files: ! `grep -r "TODO.*$ARGUMENTS" src/`
</context>
```
(Note: Remove the space after the exclamation mark in actual usage)
</incorporating_arguments>

<positional_arguments>

For structured input, use `$1`, `$2`, `$3`:

```markdown
---
argument-hint: <pr-number> <priority> <assignee>
---

<objective>
Review PR #$1 with priority $2 and assign to $3.
</objective>
```

**Usage:** `/review-pr 456 high alice`
</positional_arguments>
</arguments_intelligence>

<file_structure>

**Project commands**: `.claude/commands/`
- Shared with team via version control
- Shows `(project)` in `/help` list

**Personal commands**: `~/.claude/commands/`
- Available across all your projects
- Shows `(user)` in `/help` list

**File naming**: `command-name.md` → invoked as `/command-name`
</file_structure>

<yaml_frontmatter>

<field name="description">
**Required** - Describes what the command does

```yaml
description: Analyze this code for performance issues and suggest optimizations
```

Shown in the `/help` command list.
</field>

<field name="allowed-tools">
**Optional** - Restricts which tools Claude can use

```yaml
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
```

**Formats**:
- Array: `allowed-tools: [Read, Edit, Write]`
- Single tool: `allowed-tools: SequentialThinking`
- Bash restrictions: `allowed-tools: Bash(git add:*)`

If omitted: All tools available
</field>
</yaml_frontmatter>

<arguments>
<all_arguments_string>

**Command file**: `.claude/commands/fix-issue.md`
```markdown
---
description: Fix issue following coding standards
---

Fix issue #$ARGUMENTS following our coding standards
```

**Usage**: `/fix-issue 123 high-priority`

**Claude receives**: "Fix issue #123 high-priority following our coding standards"
</all_arguments_string>

<positional_arguments_syntax>

**Command file**: `.claude/commands/review-pr.md`
```markdown
---
description: Review PR with priority and assignee
---

Review PR #$1 with priority $2 and assign to $3
```

**Usage**: `/review-pr 456 high alice`

**Claude receives**: "Review PR #456 with priority high and assign to alice"

See [references/arguments.md](references/arguments.md) for advanced patterns.
</positional_arguments_syntax>
</arguments>

<dynamic_context>

Execute bash commands before the prompt using the exclamation mark prefix directly before backticks (no space between).

**Note:** Examples below show a space after the exclamation mark to prevent execution during skill loading. In actual slash commands, remove the space.

Example:

```markdown
---
description: Create a git commit
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
---

## Context

- Current git status: ! `git status`
- Current git diff: ! `git diff HEAD`
- Current branch: ! `git branch --show-current`
- Recent commits: ! `git log --oneline -10`

## Your task

Based on the above changes, create a single git commit.
```

The bash commands execute and their output is included in the expanded prompt.
</dynamic_context>

<file_references>

Use `@` prefix to reference specific files:

```markdown
---
description: Review implementation
---

Review the implementation in @ src/utils/helpers.js
```
(Note: Remove the space after @ in actual usage)

Claude can access the referenced file's contents.
</file_references>

<best_practices>

**1. Always use XML structure**
```yaml
# All slash commands should have XML-structured bodies
```

After frontmatter, use XML tags:
- `<objective>` - What and why (always)
- `<process>` - How to do it (always)
- `<success_criteria>` - Definition of done (always)
- Additional tags as needed (see xml_structure section)

**2. Clear descriptions**
```yaml
# Good
description: Analyze this code for performance issues and suggest optimizations

# Bad
description: Optimize stuff
```

**3. Use dynamic context for state-dependent tasks**
```markdown
Current git status: ! `git status`
Files changed: ! `git diff --name-only`
```

**4. Restrict tools when appropriate**
```yaml
# For git commands - prevent running arbitrary bash
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)

# For analysis - thinking only
allowed-tools: SequentialThinking
```

**5. Use $ARGUMENTS for flexibility**
```markdown
Find and fix issue #$ARGUMENTS
```

**6. Reference relevant files**
```markdown
Review @ package.json for dependencies
Analyze @ src/database/* for schema
```
(Note: Remove the space after @ in actual usage)
</best_practices>

<common_patterns>

**Simple analysis command**:
```markdown
---
description: Review this code for security vulnerabilities
---

<objective>
Review code for security vulnerabilities and suggest fixes.
</objective>

<process>
1. Scan code for common vulnerabilities (XSS, SQL injection, etc.)
2. Identify specific issues with line numbers
3. Suggest remediation for each issue
</process>

<success_criteria>
- All major vulnerability types checked
- Specific issues identified with locations
- Actionable fixes provided
</success_criteria>
```

**Git workflow with context**:
```markdown
---
description: Create a git commit
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
---

<objective>
Create a git commit for current changes following repository conventions.
</objective>

<context>
- Current status: ! `git status`
- Changes: ! `git diff HEAD`
- Recent commits: ! `git log --oneline -5`
</context>

<process>
1. Review staged and unstaged changes
2. Stage relevant files
3. Write commit message following recent commit style
4. Create commit
</process>

<success_criteria>
- All relevant changes staged
- Commit message follows repository conventions
- Commit created successfully
</success_criteria>
```

**Parameterized command**:
```markdown
---
description: Fix issue following coding standards
argument-hint: [issue-number]
---

<objective>
Fix issue #$ARGUMENTS following project coding standards.

This ensures bugs are resolved systematically with proper testing.
</objective>

<process>
1. Understand the issue described in ticket #$ARGUMENTS
2. Locate the relevant code in codebase
3. Implement a solution that addresses root cause
4. Add appropriate tests
5. Verify fix resolves the issue
</process>

<success_criteria>
- Issue fully understood and addressed
- Solution follows coding standards
- Tests added and passing
- No regressions introduced
</success_criteria>
```

**File-specific command**:
```markdown
---
description: Optimize code performance
argument-hint: [file-path]
---

<objective>
Analyze performance of @ $ARGUMENTS and suggest specific optimizations.

This helps improve application performance through targeted improvements.
</objective>

<process>
1. Review code in @ $ARGUMENTS for performance issues
2. Identify bottlenecks and inefficiencies
3. Suggest three specific optimizations with rationale
4. Estimate performance impact of each
</process>

<success_criteria>
- Performance issues clearly identified
- Three concrete optimizations suggested
- Implementation guidance provided
- Performance impact estimated
</success_criteria>
```

**Usage**: `/optimize src/utils/helpers.js`

See [references/patterns.md](references/patterns.md) for more examples.
</common_patterns>

<reference_guides>

**Arguments reference**: [references/arguments.md](references/arguments.md)
- $ARGUMENTS variable
- Positional arguments ($1, $2, $3)
- Parsing strategies
- Examples from official docs

**Patterns reference**: [references/patterns.md](references/patterns.md)
- Git workflows
- Code analysis
- File operations
- Security reviews
- Examples from official docs

**Tool restrictions**: [references/tool-restrictions.md](references/tool-restrictions.md)
- Bash command patterns
- Security best practices
- When to restrict tools
- Examples from official docs
</reference_guides>

<generation_protocol>

1. **Analyze the user's request**:
   - What is the command's purpose?
   - Does it need user input ($ARGUMENTS)?
   - Does it produce files or artifacts?
   - Does it require verification or testing?
   - Is it simple (single-step) or complex (multi-step)?

2. **Create frontmatter**:
   ```yaml
   ---
   name: command-name
   description: Clear description of what it does
   argument-hint: [input] # Only if arguments needed
   allowed-tools: [...] # Only if tool restrictions needed
   ---
   ```

3. **Create XML-structured body**:

   **Always include:**
   - `<objective>` - What and why
   - `<process>` - How to do it (numbered steps)
   - `<success_criteria>` - Definition of done

   **Include when relevant:**
   - `<context>` - Dynamic state (! `commands`) or file references (@ files)
   - `<verification>` - Checks to perform if creating artifacts
   - `<testing>` - Test commands if tests are part of workflow
   - `<output>` - Files created/modified

4. **Integrate $ARGUMENTS properly**:
   - If user input needed: Add `argument-hint` and use `$ARGUMENTS` in tags
   - If self-contained: Omit `argument-hint` and `$ARGUMENTS`

5. **Apply intelligence**:
   - Simple commands: Keep it concise (objective + process + success criteria)
   - Complex commands: Add context, verification, testing as needed
   - Don't over-engineer simple commands
   - Don't under-specify complex commands

6. **Save the file**:
   - Project: `.claude/commands/command-name.md`
   - Personal: `~/.claude/commands/command-name.md`
</generation_protocol>

<success_criteria>
A well-structured slash command meets these criteria:

**YAML Frontmatter**:
- `description` field is clear and concise
- `argument-hint` present if command accepts arguments
- `allowed-tools` specified if tool restrictions needed

**XML Structure**:
- All three required tags present: `<objective>`, `<process>`, `<success_criteria>`
- Conditional tags used appropriately based on complexity
- No raw markdown headings in body
- All XML tags properly closed

**Arguments Handling**:
- `$ARGUMENTS` used when command operates on user-specified data
- Positional arguments (`$1`, `$2`, etc.) used when structured input needed
- No `$ARGUMENTS` reference for self-contained commands

**Functionality**:
- Command expands correctly when invoked
- Dynamic context loads properly (bash commands, file references)
- Tool restrictions prevent unauthorized operations
- Command accomplishes intended purpose reliably

**Quality**:
- Clear, actionable instructions in `<process>` tag
- Measurable completion criteria in `<success_criteria>`
- Appropriate level of detail (not over-engineered for simple tasks)
- Examples provided when beneficial
</success_criteria>
