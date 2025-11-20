# Matchers and Pattern Matching

Complete guide to matching tools with hook matchers.

## What are matchers?

Matchers are regex patterns that filter which tools trigger a hook. They allow you to:
- Target specific tools (e.g., only `Bash`)
- Match multiple tools (e.g., `Write|Edit`)
- Match tool categories (e.g., all MCP tools)
- Match everything (omit matcher)

---

## Syntax

Matchers use JavaScript regex syntax:

```json
{
  "matcher": "pattern"
}
```

The pattern is tested against the tool name using `new RegExp(pattern).test(toolName)`.

---

## Common Patterns

### Exact match
```json
{
  "matcher": "Bash"
}
```
Matches: `Bash`
Doesn't match: `bash`, `BashOutput`

### Multiple tools (OR)
```json
{
  "matcher": "Write|Edit"
}
```
Matches: `Write`, `Edit`
Doesn't match: `Read`, `Bash`

### Starts with
```json
{
  "matcher": "^Bash"
}
```
Matches: `Bash`, `BashOutput`
Doesn't match: `Read`

### Ends with
```json
{
  "matcher": "Output$"
}
```
Matches: `BashOutput`
Doesn't match: `Bash`, `Read`

### Contains
```json
{
  "matcher": ".*write.*"
}
```
Matches: `Write`, `NotebookWrite`, `TodoWrite`
Doesn't match: `Read`, `Edit`

Case-sensitive! `write` won't match `Write`.

### Any tool (no matcher)
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "hooks": [...]  // No matcher = matches all tools
      }
    ]
  }
}
```

---

## Tool Categories

### All file operations
```json
{
  "matcher": "Read|Write|Edit|Glob|Grep"
}
```

### All bash tools
```json
{
  "matcher": "Bash.*"
}
```
Matches: `Bash`, `BashOutput`, `BashKill`

### All MCP tools
```json
{
  "matcher": "mcp__.*"
}
```
Matches: `mcp__memory__store`, `mcp__filesystem__read`, etc.

### Specific MCP server
```json
{
  "matcher": "mcp__memory__.*"
}
```
Matches: `mcp__memory__store`, `mcp__memory__retrieve`
Doesn't match: `mcp__filesystem__read`

### Specific MCP tool
```json
{
  "matcher": "mcp__.*__write.*"
}
```
Matches: `mcp__filesystem__write`, `mcp__memory__write`
Doesn't match: `mcp__filesystem__read`

---

## MCP Tool Naming

MCP tools follow the pattern: `mcp__{server}__{tool}`

Examples:
- `mcp__memory__store`
- `mcp__filesystem__read`
- `mcp__github__create_issue`

**Match all tools from a server**:
```json
{
  "matcher": "mcp__github__.*"
}
```

**Match specific tool across all servers**:
```json
{
  "matcher": "mcp__.*__read.*"
}
```

---

## Real-World Examples

### Log all bash commands
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.command' >> ~/bash-log.txt"
          }
        ]
      }
    ]
  }
}
```

### Format code after any file write
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|NotebookEdit",
        "hooks": [
          {
            "type": "command",
            "command": "prettier --write $CLAUDE_PROJECT_DIR"
          }
        ]
      }
    ]
  }
}
```

### Validate all MCP memory writes
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__memory__.*",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Validate this memory operation: $ARGUMENTS\n\nCheck if data is appropriate to store.\n\nReturn: {\"decision\": \"approve\" or \"block\", \"reason\": \"why\"}"
          }
        ]
      }
    ]
  }
}
```

### Block destructive git commands
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/check-git-safety.sh"
          }
        ]
      }
    ]
  }
}
```

`check-git-safety.sh`:
```bash
#!/bin/bash
input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command')

if [[ "$command" == *"git push --force"* ]] || \
   [[ "$command" == *"rm -rf /"* ]] || \
   [[ "$command" == *"git reset --hard"* ]]; then
  echo '{"decision": "block", "reason": "Destructive command detected"}'
else
  echo '{"decision": "approve", "reason": "Safe"}'
fi
```

---

## Multiple Matchers

You can have multiple matcher blocks for the same event:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/bash-validator.sh"
          }
        ]
      },
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/file-validator.sh"
          }
        ]
      },
      {
        "matcher": "mcp__.*",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/mcp-logger.sh"
          }
        ]
      }
    ]
  }
}
```

Each matcher is evaluated independently. A tool can match multiple matchers.

---

## Debugging Matchers

### Enable debug mode
```bash
claude --debug
```

Debug output shows:
```
[DEBUG] Getting matching hook commands for PreToolUse with query: Bash
[DEBUG] Found 3 hook matchers in settings
[DEBUG] Matched 1 hooks for query "Bash"
```

### Test your matcher

Use JavaScript regex to test patterns:

```javascript
const toolName = "mcp__memory__store";
const pattern = "mcp__memory__.*";
const regex = new RegExp(pattern);
console.log(regex.test(toolName)); // true
```

Or in Node.js:
```bash
node -e "console.log(/mcp__memory__.*/.test('mcp__memory__store'))"
```

### Common mistakes

❌ **Case sensitivity**
```json
{
  "matcher": "bash"  // Won't match "Bash"
}
```

✅ **Correct**
```json
{
  "matcher": "Bash"
}
```

---

❌ **Missing escape**
```json
{
  "matcher": "mcp__memory__*"  // * is literal, not wildcard
}
```

✅ **Correct**
```json
{
  "matcher": "mcp__memory__.*"  // .* is regex for "any characters"
}
```

---

❌ **Unintended partial match**
```json
{
  "matcher": "Write"  // Matches "Write", "TodoWrite", "NotebookWrite"
}
```

✅ **Exact match only**
```json
{
  "matcher": "^Write$"
}
```

---

## Advanced Patterns

### Negative lookahead (exclude tools)
```json
{
  "matcher": "^(?!Read).*"
}
```
Matches: Everything except `Read`

### Match any file operation except Grep
```json
{
  "matcher": "^(Read|Write|Edit|Glob)$"
}
```

### Case-insensitive match
```json
{
  "matcher": "(?i)bash"
}
```
Matches: `Bash`, `bash`, `BASH`

(Note: Claude Code tools are PascalCase by convention, so this is rarely needed)

---

## Performance Considerations

**Broad matchers** (e.g., `.*`) run on every tool use:
- Simple command hooks: negligible impact
- Prompt hooks: can slow down significantly

**Recommendation**: Be as specific as possible with matchers to minimize unnecessary hook executions.

**Example**: Instead of matching all tools and checking inside the hook:
```json
{
  "matcher": ".*",  // Runs on EVERY tool
  "hooks": [
    {
      "type": "command",
      "command": "if [[ $(jq -r '.tool_name') == 'Bash' ]]; then ...; fi"
    }
  ]
}
```

Do this:
```json
{
  "matcher": "Bash",  // Only runs on Bash
  "hooks": [
    {
      "type": "command",
      "command": "..."
    }
  ]
}
```

---

## Tool Name Reference

Common Claude Code tool names:
- `Bash`
- `BashOutput`
- `KillShell`
- `Read`
- `Write`
- `Edit`
- `Glob`
- `Grep`
- `TodoWrite`
- `NotebookEdit`
- `WebFetch`
- `WebSearch`
- `Task`
- `Skill`
- `SlashCommand`
- `AskUserQuestion`
- `ExitPlanMode`

MCP tools: `mcp__{server}__{tool}` (varies by installed servers)

Run `claude --debug` and watch tool calls to discover available tool names.
