---
description: List outstanding todos and select one to work on
allowed-tools:
  - Read
  - Edit
  - Glob
---

# Check Todos

## Instructions

1. Read TO-DOS.md in the working directory (if doesn't exist, say "No outstanding todos" and exit)

2. Parse and display todos:
   - Extract all list items starting with `- **` (active todos)
   - If none exist, say "No outstanding todos" and exit
   - Display compact numbered list showing:
     - Number (for selection)
     - Bold title only (part between `**` markers)
     - Date from h2 heading above it
   - Prompt: "Reply with the number of the todo you'd like to work on."
   - Wait for user to reply with a number

3. Load full context for selected todo:
   - Display complete line with all fields (Problem, Files, Solution)
   - Display h2 heading (topic + date) for additional context
   - Read and briefly summarize relevant files mentioned

4. Check for established workflows:
   - Read CLAUDE.md (if exists) to understand project-specific workflows and rules
   - Look for `.claude/skills/` directory
   - Match file paths in todo to domain patterns (`plugins/` → plugin workflow, `mcp-servers/` → MCP workflow)
   - Check CLAUDE.md for explicit workflow requirements for this type of work

5. Present action options to user:
   - **If matching skill/workflow found**: "This looks like [domain] work. Would you like to:\n\n1. Invoke [skill-name] skill and start\n2. Work on it directly\n3. Brainstorm approach first\n4. Put it back and browse other todos\n\nReply with the number of your choice."
   - **If no workflow match**: "Would you like to:\n\n1. Start working on it\n2. Brainstorm approach first\n3. Put it back and browse other todos\n\nReply with the number of your choice."
   - Wait for user response

6. Handle user choice:
   - **Option "Invoke skill" or "Start working"**: Remove todo from TO-DOS.md (and h2 heading if section becomes empty), then begin work (invoke skill if applicable, or proceed directly)
   - **Option "Brainstorm approach"**: Keep todo in file, invoke `/brainstorm` with the todo description as argument
   - **Option "Put it back"**: Keep todo in file, return to step 2 to display the full list again

## Display Format

```
Outstanding Todos:

1. Add structured format to add-to-todos (2025-11-15 14:23)
2. Create check-todos command (2025-11-15 14:23)
3. Fix cookie-extractor MCP workflow (2025-11-14 09:15)

Reply with the number of the todo you'd like to work on.
```
