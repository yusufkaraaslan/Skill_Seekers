# Todo Management System for Claude Code

Capture ideas mid-conversation without derailing your current work.

When you're deep in a conversation and spot a bug, think of a new feature, or notice something to refactor - but don't want to lose focus on what you're doing NOW - use `/add-to-todos` to capture it with full context. Later, `/check-todos` lets you resume exactly where that thought left off.

**The problem:** You're debugging auth when you notice the logging is terrible. You want to fix it, but not right now. You keep working, forget the details, and weeks later can't remember what you wanted to do or why.

**The solution:** `/add-to-todos` captures the idea, file paths, and reasoning in the moment. `/check-todos` brings it all back with zero context loss.

## Commands

### `/add-to-todos [optional description]`

Captures the current conversation context as a structured todo item in `TO-DOS.md`.

**What it captures:**
- Specific problem or task from conversation
- File paths with line numbers
- Technical details (error messages, root causes, constraints)
- Timestamp and context title
- Solution approach hints (optional)

**Format:**
```markdown
## Brief Context Title - 2025-11-15 14:23

- **[Action] [Component]** - Brief description. **Problem:** What's wrong/why needed. **Files:** path/to/file.ts:123-145. **Solution:** Approach hints.
```

**Usage:**
- `/add-to-todos` - Infers todo from current conversation
- `/add-to-todos fix authentication bug` - Uses provided description as focus

### `/check-todos`

Lists todos, lets you select one, loads full context, and removes it from the list.

**What it does:**
1. Shows compact numbered list of todos with dates
2. Waits for selection
3. Loads full todo context (Problem/Files/Solution)
4. Checks for project workflows (CLAUDE.md, skills)
5. Suggests relevant workflow if found
6. Removes todo from list
7. Ready to start work

**Workflow detection:**
- Reads `CLAUDE.md` for project-specific patterns
- Checks `.claude/skills/` for matching workflows
- Matches file paths to domains (plugins/, mcp-servers/, etc.)
- Presents choice: invoke skill or work directly

## Why This Works

**Stay focused:**
- Don't derail current work to chase every idea
- Capture inspiration the moment it strikes
- Build a backlog of improvements without breaking flow

**Never lose ideas:**
- "Should refactor this..." → captured with context
- "This could be a feature..." → saved with reasoning
- "Need to investigate..." → logged with file paths

**Resume with full context:**
- Claude gets the full picture weeks later
- No "what was I thinking?" moments
- Exact files, line numbers, and reasoning intact

## Installation

**Install globally** - these commands work in any directory:

```bash
cp add-to-todos.md ~/.claude/commands/
cp check-todos.md ~/.claude/commands/
```

Once installed, the commands are available everywhere. Each project gets its own `TO-DOS.md` in its working directory - todos are captured per-project automatically.

## Example Workflow

**Mid-conversation capture:**
```
You: "Fix the login redirect bug"
Claude: [investigating auth.ts, finds the issue]
You: "Actually, I notice the error handling here is messy too.
      Let's just fix the redirect for now."
You: /add-to-todos refactor error handling

[stays focused on login redirect, doesn't derail]
```

**Later that week:**
```
You: /check-todos

Outstanding Todos:

1. Refactor error handling in auth flow (2025-11-15 14:23)
2. Add user preference caching (2025-11-14 09:30)
3. Research Redis vs Memcached (2025-11-12 16:45)

Reply with number: 1

Claude loads:
- **Refactor error handling in auth flow** - Error handling in
  authentication is inconsistent and hard to debug. **Problem:**
  Try-catch blocks scattered across auth.ts, no centralized error
  logging, generic error messages. **Files:** auth.ts:145-230,
  middleware/error.ts:12-45. **Solution:** Centralize error
  handling, add structured logging, improve error messages.

[Removes from list, starts work with full context]
```

## File Structure

**Global (install once, use everywhere):**
```
~/.claude/commands/
  add-to-todos.md        # Add todo command
  check-todos.md         # Check/select todo command
```

**Per-project (created automatically in working directory):**
```
/your/project/
  TO-DOS.md              # Project-specific todos

/another/project/
  TO-DOS.md              # Different project's todos
```

Each project maintains its own todo list. The commands are global, the todos are local.

## Tips

- Use `/add-to-todos` liberally - capture anything you might revisit
- Include specific line numbers when you find them
- The structured format ensures Claude has enough context later
- Todos are removed when work begins - if incomplete, re-add with new context
- Empty sections are automatically cleaned up

## Integration with Workflows

The system checks for established workflows before starting work:
- Plugin development → checks for plugin skill
- MCP servers → checks for MCP workflow
- Generic tasks → works directly

This ensures you follow project-specific patterns and use the right tools automatically.

---

**Questions or improvements?** Open an issue or submit a PR.

—TÂCHES
