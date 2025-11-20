# Arguments Reference

Official documentation examples for using arguments in slash commands.

## $ARGUMENTS - All Arguments

**Source**: Official Claude Code documentation

Captures all arguments as a single concatenated string.

### Basic Example

**Command file**: `.claude/commands/fix-issue.md`
```markdown
---
description: Fix issue following coding standards
---

Fix issue #$ARGUMENTS following our coding standards
```

**Usage**:
```
/fix-issue 123 high-priority
```

**Claude receives**:
```
Fix issue #123 high-priority following our coding standards
```

### Multi-Step Workflow Example

**Command file**: `.claude/commands/fix-issue.md`
```markdown
---
description: Fix issue following coding standards
---

Fix issue #$ARGUMENTS. Follow these steps:

1. Understand the issue described in the ticket
2. Locate the relevant code in our codebase
3. Implement a solution that addresses the root cause
4. Add appropriate tests
5. Prepare a concise PR description
```

**Usage**:
```
/fix-issue 456
```

**Claude receives the full prompt** with "456" replacing $ARGUMENTS.

## Positional Arguments - $1, $2, $3

**Source**: Official Claude Code documentation

Access specific arguments individually.

### Example

**Command file**: `.claude/commands/review-pr.md`
```markdown
---
description: Review PR with priority and assignee
---

Review PR #$1 with priority $2 and assign to $3
```

**Usage**:
```
/review-pr 456 high alice
```

**Claude receives**:
```
Review PR #456 with priority high and assign to alice
```

- `$1` becomes `456`
- `$2` becomes `high`
- `$3` becomes `alice`

## Argument Patterns from Official Docs

### Pattern 1: File Reference with Argument

**Command**:
```markdown
---
description: Optimize code performance
---

Analyze the performance of this code and suggest three specific optimizations:

@ $ARGUMENTS
```

**Usage**:
```
/optimize src/utils/helpers.js
```

References the file specified in the argument.

### Pattern 2: Issue Tracking

**Command**:
```markdown
---
description: Find and fix issue
---

Find and fix issue #$ARGUMENTS.

Follow these steps:
1. Understand the issue described in the ticket
2. Locate the relevant code in our codebase
3. Implement a solution that addresses the root cause
4. Add appropriate tests
5. Prepare a concise PR description
```

**Usage**:
```
/fix-issue 789
```

### Pattern 3: Code Review with Context

**Command**:
```markdown
---
description: Review PR with context
---

Review PR #$1 with priority $2 and assign to $3

Context from git:
- Changes: ! `gh pr diff $1`
- Status: ! `gh pr view $1 --json state`
```

**Usage**:
```
/review-pr 123 critical bob
```

Combines positional arguments with dynamic bash execution.

## Best Practices

### Use $ARGUMENTS for Simple Commands

When you just need to pass a value through:
```markdown
Fix issue #$ARGUMENTS
Optimize @ $ARGUMENTS
Summarize $ARGUMENTS
```

### Use Positional Arguments for Structure

When different arguments have different meanings:
```markdown
Review PR #$1 with priority $2 and assign to $3
Deploy $1 to $2 environment with tag $3
```

### Provide Clear Descriptions

Help users understand what arguments are expected:
```yaml
# Good
description: Fix issue following coding standards (usage: /fix-issue <issue-number>)

# Better - if using argument-hint field
description: Fix issue following coding standards
argument-hint: <issue-number> [priority]
```

## Empty Arguments

Commands work with or without arguments:

**Command**:
```markdown
---
description: Analyze code for issues
---

Analyze this code for issues: $ARGUMENTS

If no specific file provided, analyze the current context.
```

**Usage 1**: `/analyze src/app.js`
**Usage 2**: `/analyze` (analyzes current conversation context)

## Combining with Other Features

### Arguments + Dynamic Context

```markdown
---
description: Review changes for issue
---

Issue #$ARGUMENTS

Recent changes:
- Status: ! `git status`
- Diff: ! `git diff`

Review the changes related to this issue.
```

### Arguments + File References

```markdown
---
description: Compare files
---

Compare @ $1 with @ $2 and highlight key differences.
```

**Usage**: `/compare src/old.js src/new.js`

### Arguments + Tool Restrictions

```markdown
---
description: Commit changes for issue
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
---

Create commit for issue #$ARGUMENTS

Status: ! `git status`
Changes: ! `git diff HEAD`
```

## Notes

- Arguments are whitespace-separated by default
- Quote arguments containing spaces: `/command "argument with spaces"`
- Arguments are passed as-is (no special parsing)
- Empty arguments are replaced with empty string
