# Input/Output Schemas

Complete JSON schemas for all hook types.

## Common Input Fields

All hooks receive these fields:

```typescript
{
  session_id: string           // Unique session identifier
  transcript_path: string      // Path to session transcript (.jsonl file)
  cwd: string                  // Current working directory
  permission_mode: string      // "default" | "plan" | "acceptEdits" | "bypassPermissions"
  hook_event_name: string      // Name of the hook event
}
```

---

## PreToolUse

**Input**:
```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "cwd": "/Users/username/project",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm install",
    "description": "Install dependencies"
  }
}
```

**Output** (optional, for control):
```json
{
  "decision": "approve" | "block",
  "reason": "Explanation for the decision",
  "permissionDecision": "allow" | "deny" | "ask",
  "permissionDecisionReason": "Why this permission decision",
  "updatedInput": {
    "command": "npm install --save-exact"
  },
  "systemMessage": "Message displayed to user",
  "suppressOutput": false,
  "continue": true
}
```

**Fields**:
- `decision`: Whether to allow the tool call
- `reason`: Explanation (required if blocking)
- `permissionDecision`: Override permission system
- `updatedInput`: Modified tool input (partial update)
- `systemMessage`: Message shown to user
- `suppressOutput`: Hide hook output from user
- `continue`: If false, stop execution

---

## PostToolUse

**Input**:
```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "cwd": "/Users/username/project",
  "permission_mode": "default",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.js",
    "content": "const x = 1;"
  },
  "tool_output": "File created successfully at: /path/to/file.js"
}
```

**Output** (optional):
```json
{
  "systemMessage": "Code formatted successfully",
  "suppressOutput": false
}
```

**Fields**:
- `systemMessage`: Additional message to display
- `suppressOutput`: Hide tool output from user

---

## UserPromptSubmit

**Input**:
```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "cwd": "/Users/username/project",
  "permission_mode": "default",
  "hook_event_name": "UserPromptSubmit",
  "prompt": "Write a function to calculate factorial"
}
```

**Output**:
```json
{
  "decision": "approve" | "block",
  "reason": "Prompt is clear and actionable",
  "systemMessage": "Optional message to user"
}
```

**Fields**:
- `decision`: Whether to allow the prompt
- `reason`: Explanation (required if blocking)
- `systemMessage`: Message shown to user

---

## Stop

**Input**:
```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "cwd": "/Users/username/project",
  "permission_mode": "default",
  "hook_event_name": "Stop",
  "stop_hook_active": false
}
```

**Output**:
```json
{
  "decision": "block" | undefined,
  "reason": "Tests are still failing - please fix before stopping",
  "continue": true,
  "stopReason": "Cannot stop yet",
  "systemMessage": "Additional context"
}
```

**Fields**:
- `decision`: `"block"` to prevent stopping, `undefined` to allow
- `reason`: Why Claude should continue (required if blocking)
- `continue`: If true and blocking, Claude continues working
- `stopReason`: Message shown when stopping is blocked
- `systemMessage`: Additional context for Claude
- `stop_hook_active`: If true, don't block again (prevents infinite loops)

**Important**: Always check `stop_hook_active` to avoid infinite loops:

```javascript
if (input.stop_hook_active) {
  return { decision: undefined }; // Don't block again
}
```

---

## SubagentStop

**Input**: Same as Stop

**Output**: Same as Stop

**Usage**: Same as Stop, but for subagent completion

---

## SessionStart

**Input**:
```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "cwd": "/Users/username/project",
  "permission_mode": "default",
  "hook_event_name": "SessionStart",
  "source": "startup" | "continue" | "checkpoint"
}
```

**Output**:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Current sprint: Sprint 23\nFocus: User authentication\nDeadline: Friday"
  }
}
```

**Fields**:
- `additionalContext`: Text injected into session context
- Multiple SessionStart hooks' contexts are concatenated

---

## SessionEnd

**Input**:
```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "cwd": "/Users/username/project",
  "permission_mode": "default",
  "hook_event_name": "SessionEnd",
  "reason": "exit" | "error" | "timeout" | "compact"
}
```

**Output**: None (ignored)

**Usage**: Cleanup tasks only. Cannot prevent session end.

---

## PreCompact

**Input**:
```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "cwd": "/Users/username/project",
  "permission_mode": "default",
  "hook_event_name": "PreCompact",
  "trigger": "manual" | "auto",
  "custom_instructions": "Preserve all git commit messages"
}
```

**Output**:
```json
{
  "decision": "approve" | "block",
  "reason": "Safe to compact" | "Wait until task completes"
}
```

**Fields**:
- `trigger`: How compaction was initiated
- `custom_instructions`: User's compaction preferences (if manual)
- `decision`: Whether to proceed with compaction
- `reason`: Explanation

---

## Notification

**Input**:
```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "cwd": "/Users/username/project",
  "permission_mode": "default",
  "hook_event_name": "Notification"
}
```

**Output**: None (hook just performs notification action)

**Usage**: Trigger external notifications (desktop, sound, status bar)

---

## Common Output Fields

These fields can be returned by any hook:

```json
{
  "continue": true | false,
  "stopReason": "Reason shown when stopping",
  "suppressOutput": true | false,
  "systemMessage": "Additional context or message"
}
```

**Fields**:
- `continue`: If false, stop Claude's execution immediately
- `stopReason`: Message displayed when execution stops
- `suppressOutput`: If true, hide hook's stdout/stderr from user
- `systemMessage`: Context added to Claude's next message

---

## LLM Prompt Hook Response

When using `type: "prompt"`, the LLM must return JSON:

```json
{
  "decision": "approve" | "block",
  "reason": "Detailed explanation",
  "systemMessage": "Optional message",
  "continue": true | false,
  "stopReason": "Optional stop message"
}
```

**Example prompt**:
```
Evaluate this command: $ARGUMENTS

Check if it's safe to execute.

Return JSON:
{
  "decision": "approve" or "block",
  "reason": "your explanation"
}
```

The `$ARGUMENTS` placeholder is replaced with the hook's input JSON.

---

## Tool-Specific Input Fields

Different tools provide different `tool_input` fields:

### Bash
```json
{
  "tool_input": {
    "command": "npm install",
    "description": "Install dependencies",
    "timeout": 120000,
    "run_in_background": false
  }
}
```

### Write
```json
{
  "tool_input": {
    "file_path": "/path/to/file.js",
    "content": "const x = 1;"
  }
}
```

### Edit
```json
{
  "tool_input": {
    "file_path": "/path/to/file.js",
    "old_string": "const x = 1;",
    "new_string": "const x = 2;",
    "replace_all": false
  }
}
```

### Read
```json
{
  "tool_input": {
    "file_path": "/path/to/file.js",
    "offset": 0,
    "limit": 100
  }
}
```

### Grep
```json
{
  "tool_input": {
    "pattern": "function.*",
    "path": "/path/to/search",
    "output_mode": "content"
  }
}
```

### MCP tools
```json
{
  "tool_input": {
    // MCP tool-specific parameters
  }
}
```

Access these in hooks:
```bash
command=$(echo "$input" | jq -r '.tool_input.command')
file_path=$(echo "$input" | jq -r '.tool_input.file_path')
```

---

## Modifying Tool Input

PreToolUse hooks can modify `tool_input` before execution:

**Original input**:
```json
{
  "tool_input": {
    "command": "npm install lodash"
  }
}
```

**Hook output**:
```json
{
  "decision": "approve",
  "reason": "Adding --save-exact flag",
  "updatedInput": {
    "command": "npm install --save-exact lodash"
  }
}
```

**Result**: Tool executes with modified input.

**Partial updates**: Only specify fields you want to change:
```json
{
  "updatedInput": {
    "timeout": 300000  // Only update timeout, keep other fields
  }
}
```

---

## Error Handling

**Command hooks**: Return non-zero exit code to indicate error
```bash
if [ error ]; then
  echo '{"decision": "block", "reason": "Error occurred"}' >&2
  exit 1
fi
```

**Prompt hooks**: LLM should return valid JSON. If malformed, hook fails gracefully.

**Timeout**: Set `timeout` (ms) to prevent hanging:
```json
{
  "type": "command",
  "command": "/path/to/slow-script.sh",
  "timeout": 30000
}
```

Default: 60000ms (60s)
