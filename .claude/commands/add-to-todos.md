---
description: Add todo item to TO-DOS.md with context from conversation
argument-hint: <todo-description> (optional - infers from conversation if omitted)
allowed-tools:
  - Read
  - Edit
  - Write
---

# Add Todo Item

## Context

- Current timestamp: !`date "+%Y-%m-%d %H:%M"`

## Instructions

1. Read TO-DOS.md in the working directory (create with Write tool if it doesn't exist)

2. Check for duplicates:
   - Extract key concept/action from the new todo
   - Search existing todos for similar titles or overlapping scope
   - If found, ask user: "A similar todo already exists: [title]. Would you like to:\n\n1. Skip adding (keep existing)\n2. Replace existing with new version\n3. Add anyway as separate item\n\nReply with the number of your choice."
   - Wait for user response before proceeding

3. Extract todo content:
   - **With $ARGUMENTS**: Use as the focus/title for the todo and context heading
   - **Without $ARGUMENTS**: Analyze recent conversation to extract:
     - Specific problem or task discussed
     - Relevant file paths that need attention
     - Technical details (line numbers, error messages, conflicting specifications)
     - Root cause if identified

4. Append new section to bottom of file:
   - **Heading**: `## Brief Context Title - YYYY-MM-DD HH:MM` (3-8 word title, current timestamp)
   - **Todo format**: `- **[Action verb] [Component]** - [Brief description]. **Problem:** [What's wrong/why needed]. **Files:** [Comma-separated paths with line numbers]. **Solution:** [Approach hints or constraints, if applicable].`
   - **Required fields**: Problem and Files (with line numbers like `path/to/file.ts:123-145`)
   - **Optional field**: Solution
   - Make each section self-contained for future Claude to understand weeks later
   - Use simple list items (not checkboxes) - todos are removed when work begins

5. Confirm and offer to continue with original work:
   - Identify what the user was working on before `/add-to-todos` was called
   - Confirm the todo was saved: "✓ Saved to todos."
   - Ask if they want to continue with the original work: "Would you like to continue with [original task]?"
   - Wait for user response

## Format Example

```markdown
## Add Todo Command Improvements - 2025-11-15 14:23

- **Add structured format to add-to-todos** - Standardize todo entries with Problem/Files/Solution pattern. **Problem:** Current todos lack consistent structure, making it hard for Claude to have enough context when revisiting tasks later. **Files:** `commands/add-to-todos.md:22-29`. **Solution:** Use inline bold labels with required Problem and Files fields, optional Solution field.

- **Create check-todos command** - Build companion command to list and select todos. **Problem:** Need workflow to review outstanding todos and load context for selected item. **Files:** `commands/check-todos.md` (new), `TO-DOS.md` (reads from). **Solution:** Parse markdown list, display numbered list, accept selection to load full context and remove item.
```
