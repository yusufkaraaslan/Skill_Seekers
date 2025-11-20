# Command Patterns Reference

Verified patterns from official Claude Code documentation.

## Git Workflow Patterns

### Pattern: Commit with Full Context

**Source**: Official Claude Code documentation

```markdown
---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
description: Create a git commit
---

<objective>
Create a git commit for current changes following repository conventions.
</objective>

<context>
- Current git status: ! `git status`
- Current git diff (staged and unstaged changes): ! `git diff HEAD`
- Current branch: ! `git branch --show-current`
- Recent commits: ! `git log --oneline -10`
</context>

<process>
1. Review staged and unstaged changes
2. Stage relevant files with git add
3. Write commit message following recent commit style
4. Create commit
</process>

<success_criteria>
- All relevant changes staged
- Commit message follows repository conventions
- Commit created successfully
</success_criteria>
```

**Key features**:
- Tool restrictions prevent running arbitrary bash commands
- Dynamic context loaded via the exclamation mark prefix before backticks
- Git state injected before prompt execution

### Pattern: Simple Git Commit

```markdown
---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
description: Create a git commit
---

<objective>
Create a commit for current changes.
</objective>

<context>
Current changes: ! `git status`
</context>

<process>
1. Review changes
2. Stage files
3. Create commit
</process>

<success_criteria>
- Changes committed successfully
</success_criteria>
```

## Code Analysis Patterns

### Pattern: Performance Optimization

**Source**: Official Claude Code documentation

**File**: `.claude/commands/optimize.md`
```markdown
---
description: Analyze the performance of this code and suggest three specific optimizations
---

<objective>
Analyze code performance and suggest three specific optimizations.

This helps improve application performance through targeted improvements.
</objective>

<process>
1. Review code in current conversation context
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

**Usage**: `/optimize`

Claude analyzes code in the current conversation context.

### Pattern: Security Review

**File**: `.claude/commands/security-review.md`
```markdown
---
description: Review this code for security vulnerabilities
---

<objective>
Review code for security vulnerabilities and suggest fixes.
</objective>

<process>
1. Scan code for common vulnerabilities (XSS, SQL injection, CSRF, etc.)
2. Identify specific issues with line numbers
3. Assess severity of each vulnerability
4. Suggest remediation for each issue
</process>

<success_criteria>
- All major vulnerability types checked
- Specific issues identified with locations
- Severity levels assigned
- Actionable fixes provided
</success_criteria>
```

**Usage**: `/security-review`

### Pattern: File-Specific Analysis

```markdown
---
description: Optimize specific file
argument-hint: [file-path]
---

<objective>
Analyze performance of @ $ARGUMENTS and suggest three specific optimizations.

This helps improve application performance through targeted file improvements.
</objective>

<process>
1. Review code in @ $ARGUMENTS for performance issues
2. Identify bottlenecks and inefficiencies
3. Suggest three specific optimizations with rationale
4. Estimate performance impact of each
</process>

<success_criteria>
- File analyzed thoroughly
- Performance issues identified
- Three concrete optimizations suggested
- Implementation guidance provided
</success_criteria>
```

**Usage**: `/optimize src/utils/helpers.js`

References the specified file.

## Issue Tracking Patterns

### Pattern: Fix Issue with Workflow

**Source**: Official Claude Code documentation

```markdown
---
description: Find and fix issue following workflow
argument-hint: [issue-number]
---

<objective>
Find and fix issue #$ARGUMENTS following project workflow.

This ensures bugs are resolved systematically with proper testing and documentation.
</objective>

<process>
1. Understand the issue described in ticket #$ARGUMENTS
2. Locate the relevant code in codebase
3. Implement a solution that addresses the root cause
4. Add appropriate tests
5. Prepare a concise PR description
</process>

<success_criteria>
- Issue fully understood and addressed
- Solution addresses root cause
- Tests added and passing
- PR description clearly explains fix
</success_criteria>
```

**Usage**: `/fix-issue 123`

### Pattern: PR Review with Context

```markdown
---
description: Review PR with priority and assignment
argument-hint: <pr-number> <priority> <assignee>
---

<objective>
Review PR #$1 with priority $2 and assign to $3.

This ensures PRs are reviewed systematically with proper prioritization and assignment.
</objective>

<process>
1. Fetch PR #$1 details
2. Review code changes
3. Assess based on priority $2
4. Provide feedback
5. Assign to $3
</process>

<success_criteria>
- PR reviewed thoroughly
- Priority considered in review depth
- Constructive feedback provided
- Assigned to correct person
</success_criteria>
```

**Usage**: `/review-pr 456 high alice`

Uses positional arguments for structured input.

## File Operation Patterns

### Pattern: File Reference

**Source**: Official Claude Code documentation

```markdown
---
description: Review implementation
---

<objective>
Review the implementation in @ src/utils/helpers.js.

This ensures code quality and identifies potential improvements.
</objective>

<process>
1. Read @ src/utils/helpers.js
2. Analyze code structure and patterns
3. Check for best practices
4. Identify potential improvements
5. Suggest specific changes
</process>

<success_criteria>
- File reviewed thoroughly
- Code quality assessed
- Specific improvements identified
- Actionable suggestions provided
</success_criteria>
```

Uses `@` prefix to reference specific files.

### Pattern: Dynamic File Reference

```markdown
---
description: Review specific file
argument-hint: [file-path]
---

<objective>
Review the implementation in @ $ARGUMENTS.

This allows flexible file review based on user specification.
</objective>

<process>
1. Read @ $ARGUMENTS
2. Analyze code structure and patterns
3. Check for best practices
4. Identify potential improvements
5. Suggest specific changes
</process>

<success_criteria>
- File reviewed thoroughly
- Code quality assessed
- Specific improvements identified
- Actionable suggestions provided
</success_criteria>
```

**Usage**: `/review src/app.js`

File path comes from argument.

### Pattern: Multi-File Analysis

```markdown
---
description: Compare two files
argument-hint: <file1> <file2>
---

<objective>
Compare @ $1 with @ $2 and highlight key differences.

This helps understand changes and identify important variations between files.
</objective>

<process>
1. Read @ $1 and @ $2
2. Identify structural differences
3. Compare functionality and logic
4. Highlight key changes
5. Assess impact of differences
</process>

<success_criteria>
- Both files analyzed
- Key differences identified
- Impact of changes assessed
- Clear comparison provided
</success_criteria>
```

**Usage**: `/compare src/old.js src/new.js`

## Thinking-Only Patterns

### Pattern: Deep Analysis

```markdown
---
description: Analyze problem from first principles
allowed-tools: SequentialThinking
---

<objective>
Analyze the current problem from first principles.

This helps discover optimal solutions by stripping away assumptions and rebuilding from fundamental truths.
</objective>

<process>
1. Identify the core problem
2. Strip away all assumptions
3. Identify fundamental truths and constraints
4. Rebuild solution from first principles
5. Compare with current approach
</process>

<success_criteria>
- Problem analyzed from ground up
- Assumptions identified and questioned
- Solution rebuilt from fundamentals
- Novel insights discovered
</success_criteria>
```

Tool restriction ensures Claude only uses SequentialThinking.

### Pattern: Strategic Planning

```markdown
---
description: Plan implementation strategy
allowed-tools: SequentialThinking
argument-hint: [task description]
---

<objective>
Create a detailed implementation strategy for: $ARGUMENTS

This ensures complex tasks are approached systematically with proper planning.
</objective>

<process>
1. Break down task into phases
2. Identify dependencies between phases
3. Estimate complexity for each phase
4. Suggest optimal approach
5. Identify potential risks
</process>

<success_criteria>
- Task broken into clear phases
- Dependencies mapped
- Complexity estimated
- Optimal approach identified
- Risks and mitigations outlined
</success_criteria>
```

## Bash Execution Patterns

### Pattern: Dynamic Environment Loading

```markdown
---
description: Check project status
---

<objective>
Provide a comprehensive project health summary.

This helps understand current project state across git, dependencies, and tests.
</objective>

<context>
- Git: ! `git status --short`
- Node: ! `npm list --depth=0 2>/dev/null | head -20`
- Tests: ! `npm test -- --listTests 2>/dev/null | wc -l`
</context>

<process>
1. Analyze git status for uncommitted changes
2. Review npm dependencies for issues
3. Check test coverage
4. Identify potential problems
5. Provide actionable recommendations
</process>

<success_criteria>
- All metrics checked
- Current state clearly described
- Issues identified
- Recommendations provided
</success_criteria>
```

Multiple bash commands load environment state.

### Pattern: Conditional Execution

```markdown
---
description: Deploy if tests pass
allowed-tools: Bash(npm test:*), Bash(npm run deploy:*)
---

<objective>
Deploy to production only if all tests pass.

This ensures deployment safety through automated testing gates.
</objective>

<context>
Test results: ! `npm test`
</context>

<process>
1. Review test results
2. If all tests passed, proceed to deployment
3. If any tests failed, report failures and abort
4. Monitor deployment process
5. Confirm successful deployment
</process>

<success_criteria>
- All tests verified passing
- Deployment executed only on test success
- Deployment confirmed successful
- Or deployment aborted with clear failure reasons
</success_criteria>
```

## Multi-Step Workflow Patterns

### Pattern: Structured Workflow

```markdown
---
description: Complete feature development workflow
argument-hint: [feature description]
---

<objective>
Complete full feature development workflow for: $ARGUMENTS

This ensures features are developed systematically with proper planning, implementation, testing, and documentation.
</objective>

<process>
1. **Planning**
   - Review requirements
   - Design approach
   - Identify files to modify

2. **Implementation**
   - Write code
   - Add tests
   - Update documentation

3. **Review**
   - Run tests: ! `npm test`
   - Check lint: ! `npm run lint`
   - Verify changes: ! `git diff`

4. **Completion**
   - Create commit
   - Write PR description
</process>

<testing>
- Run tests: ! `npm test`
- Check lint: ! `npm run lint`
</testing>

<verification>
Before completing:
- All tests passing
- No lint errors
- Documentation updated
- Changes verified with git diff
</verification>

<success_criteria>
- Feature fully implemented
- Tests added and passing
- Code passes linting
- Documentation updated
- Commit created
- PR description written
</success_criteria>
```

## Command Chaining Patterns

### Pattern: Analysis → Action

```markdown
---
description: Analyze and fix performance issues
argument-hint: [file-path]
---

<objective>
Analyze and fix performance issues in @ $ARGUMENTS.

This provides end-to-end performance improvement from analysis through verification.
</objective>

<process>
1. Analyze @ $ARGUMENTS for performance issues
2. Identify top 3 most impactful optimizations
3. Implement the optimizations
4. Verify improvements with benchmarks
</process>

<verification>
Before completing:
- Benchmarks run showing performance improvement
- No functionality regressions
- Code quality maintained
</verification>

<success_criteria>
- Performance issues identified and fixed
- Measurable performance improvement
- Benchmarks confirm gains
- No regressions introduced
</success_criteria>
```

Sequential steps in single command.

## Tool Restriction Patterns

### Pattern: Git-Only Command

```markdown
---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git diff:*), Bash(git commit:*)
description: Git workflow command
---

<objective>
Perform git operations safely with tool restrictions.

This prevents running arbitrary bash commands while allowing necessary git operations.
</objective>

<context>
Current git state: ! `git status`
</context>

<process>
1. Review git status
2. Perform git operations
3. Verify changes
</process>

<success_criteria>
- Git operations completed successfully
- No arbitrary commands executed
- Repository state as expected
</success_criteria>
```

Prevents running non-git bash commands.

### Pattern: Read-Only Analysis

```markdown
---
allowed-tools: [Read, Grep, Glob]
description: Analyze codebase
argument-hint: [search pattern]
---

<objective>
Search codebase for pattern: $ARGUMENTS

This provides safe codebase analysis without modification or execution permissions.
</objective>

<process>
1. Use Grep to search for pattern across codebase
2. Analyze findings
3. Identify relevant files and code sections
4. Provide summary of results
</process>

<success_criteria>
- Pattern search completed
- All matches identified
- Relevant context provided
- No files modified
</success_criteria>
```

No write or execution permissions.

### Pattern: Specific Bash Commands

```markdown
---
allowed-tools: Bash(npm test:*), Bash(npm run lint:*)
description: Run project checks
---

<objective>
Run project quality checks (tests and linting).

This ensures code quality while restricting to specific npm scripts.
</objective>

<testing>
Tests: ! `npm test`
Lint: ! `npm run lint`
</testing>

<process>
1. Run tests and capture results
2. Run linting and capture results
3. Analyze both outputs
4. Report on pass/fail status
5. Provide specific failure details if any
</process>

<success_criteria>
- All tests passing
- No lint errors
- Clear report of results
- Or specific failures identified with details
</success_criteria>
```

Only allows specific npm scripts.

## Best Practices

### 1. Use Tool Restrictions for Safety

```yaml
# Git commands
allowed-tools: Bash(git add:*), Bash(git status:*)

# Analysis only
allowed-tools: [Read, Grep, Glob]

# Thinking only
allowed-tools: SequentialThinking
```

### 2. Load Dynamic Context When Needed

```markdown
Current state: ! `git status`
Recent activity: ! `git log --oneline -5`
```

### 3. Reference Files Explicitly

```markdown
Review @ package.json for dependencies
Check @ src/config/* for settings
```

### 4. Structure Complex Commands

```markdown
## Step 1: Analysis
[analysis prompt]

## Step 2: Implementation
[implementation prompt]

## Step 3: Verification
[verification prompt]
```

### 5. Use Arguments for Flexibility

```markdown
# Simple
Fix issue #$ARGUMENTS

# Positional
Review PR #$1 with priority $2

# File reference
Analyze @ $ARGUMENTS
```

## Anti-Patterns to Avoid

### ❌ No Description

```yaml
---
# Missing description field
---
```

### ❌ Overly Broad Tool Access

```yaml
# Git command with no restrictions
---
description: Create commit
---
```

Better:
```yaml
---
description: Create commit
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
---
```

### ❌ Vague Instructions

```markdown
Do the thing for $ARGUMENTS
```

Better:
```markdown
Fix issue #$ARGUMENTS by:
1. Understanding the issue
2. Locating relevant code
3. Implementing solution
4. Adding tests
```

### ❌ Missing Context for State-Dependent Tasks

```markdown
Create a git commit
```

Better:
```markdown
Current changes: ! `git status`
Diff: ! `git diff`

Create a git commit for these changes
```
