# Troubleshooting

Common issues and solutions when working with hooks.

## Hook Not Triggering

### Symptom
Hook never executes, even when expected event occurs.

### Diagnostic steps

**1. Enable debug mode**
```bash
claude --debug
```

Look for:
```
[DEBUG] Getting matching hook commands for PreToolUse with query: Bash
[DEBUG] Found 0 hooks
```

**2. Check hook file location**

Hooks must be in:
- Project: `.claude/hooks.json`
- User: `~/.claude/hooks.json`
- Plugin: `{plugin}/hooks.json`

Verify:
```bash
cat .claude/hooks.json
# or
cat ~/.claude/hooks.json
```

**3. Validate JSON syntax**

Invalid JSON is silently ignored:
```bash
jq . .claude/hooks.json
```

If error: fix JSON syntax.

**4. Check matcher pattern**

Common mistakes:

❌ Case sensitivity
```json
{
  "matcher": "bash"  // Won't match "Bash"
}
```

✅ Fix
```json
{
  "matcher": "Bash"
}
```

---

❌ Missing escape for regex
```json
{
  "matcher": "mcp__memory__*"  // Literal *, not wildcard
}
```

✅ Fix
```json
{
  "matcher": "mcp__memory__.*"  // Regex wildcard
}
```

**5. Test matcher in isolation**

```bash
node -e "console.log(/Bash/.test('Bash'))"  # true
node -e "console.log(/bash/.test('Bash'))"  # false
```

### Solutions

**Missing hook file**: Create `.claude/hooks.json` or `~/.claude/hooks.json`

**Invalid JSON**: Use `jq` to validate and format:
```bash
jq . .claude/hooks.json > temp.json && mv temp.json .claude/hooks.json
```

**Wrong matcher**: Check tool names with `--debug` and update matcher

**No matcher specified**: If you want to match all tools, omit the matcher field entirely:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "hooks": [...]  // No matcher = all tools
      }
    ]
  }
}
```

---

## Command Hook Failing

### Symptom
Hook executes but fails with error.

### Diagnostic steps

**1. Check debug output**
```
[DEBUG] Hook command completed with status 1: <error message>
```

Status 1 = command failed.

**2. Test command directly**

Copy the command and run in terminal:
```bash
echo '{"session_id":"test","tool_name":"Bash"}' | /path/to/your/hook.sh
```

**3. Check permissions**
```bash
ls -l /path/to/hook.sh
chmod +x /path/to/hook.sh  # If not executable
```

**4. Verify dependencies**

Does the command require tools?
```bash
which jq  # Check if jq is installed
which osascript  # macOS only
```

### Common issues

**Missing executable permission**
```bash
chmod +x /path/to/hook.sh
```

**Missing dependencies**

Install required tools:
```bash
# macOS
brew install jq

# Linux
apt-get install jq
```

**Bad path**

Use absolute paths:
```json
{
  "command": "/Users/username/.claude/hooks/script.sh"
}
```

Or use environment variables:
```json
{
  "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/script.sh"
}
```

**Timeout**

If command takes too long:
```json
{
  "command": "/path/to/slow-script.sh",
  "timeout": 120000  // 2 minutes
}
```

---

## Prompt Hook Not Working

### Symptom
Prompt hook blocks everything or doesn't block when expected.

### Diagnostic steps

**1. Check LLM response format**

Debug output shows:
```
[DEBUG] Hook command completed with status 0: {"decision": "approve", "reason": "ok"}
```

Verify JSON is valid.

**2. Check prompt structure**

Ensure prompt is clear:
```json
{
  "prompt": "Evaluate: $ARGUMENTS\n\nReturn JSON: {\"decision\": \"approve\" or \"block\", \"reason\": \"why\"}"
}
```

**3. Test prompt manually**

Submit similar prompt to Claude directly to see response format.

### Common issues

**Ambiguous instructions**

❌ Vague
```json
{
  "prompt": "Is this ok? $ARGUMENTS"
}
```

✅ Clear
```json
{
  "prompt": "Check if this command is safe: $ARGUMENTS\n\nBlock if: contains 'rm -rf', 'mkfs', or force push to main\n\nReturn: {\"decision\": \"approve\" or \"block\", \"reason\": \"explanation\"}"
}
```

**Missing $ARGUMENTS**

❌ No placeholder
```json
{
  "prompt": "Validate this command"
}
```

✅ With placeholder
```json
{
  "prompt": "Validate this command: $ARGUMENTS"
}
```

**Invalid JSON response**

The LLM must return valid JSON. If it returns plain text, the hook fails.

Add explicit formatting instructions:
```
IMPORTANT: Return ONLY valid JSON, no other text:
{
  "decision": "approve" or "block",
  "reason": "your explanation"
}
```

---

## Hook Blocks Everything

### Symptom
Hook blocks all operations, even safe ones.

### Diagnostic steps

**1. Check hook logic**

Review the script/prompt logic. Is the condition too broad?

**2. Test with known-safe input**

```bash
echo '{"tool_name":"Read","tool_input":{"file_path":"test.txt"}}' | /path/to/hook.sh
```

Expected: `{"decision": "approve"}`

**3. Check for errors in script**

Add error output:
```bash
#!/bin/bash
set -e  # Exit on error
input=$(cat)
# ... rest of script
```

### Solutions

**Logic error**

Review conditions:
```bash
# Before (blocks everything)
if [[ "$command" != "safe_command" ]]; then
  block
fi

# After (blocks dangerous commands)
if [[ "$command" == *"dangerous"* ]]; then
  block
fi
```

**Default to approve**

If logic is complex, default to approve on unclear cases:
```bash
# Default
decision="approve"
reason="ok"

# Only change if dangerous
if [[ "$command" == *"rm -rf"* ]]; then
  decision="block"
  reason="Dangerous command"
fi

echo "{\"decision\": \"$decision\", \"reason\": \"$reason\"}"
```

---

## Infinite Loop in Stop Hook

### Symptom
Stop hook runs repeatedly, Claude never stops.

### Cause
Hook blocks stop without checking `stop_hook_active` flag.

### Solution

**Always check the flag**:
```bash
#!/bin/bash
input=$(cat)
stop_hook_active=$(echo "$input" | jq -r '.stop_hook_active')

# If hook already active, don't block again
if [[ "$stop_hook_active" == "true" ]]; then
  echo '{"decision": undefined}'
  exit 0
fi

# Your logic here
if [ tests_passing ]; then
  echo '{"decision": "approve", "reason": "Tests pass"}'
else
  echo '{"decision": "block", "reason": "Tests failing"}'
fi
```

Or in prompt hooks:
```json
{
  "prompt": "Evaluate stopping: $ARGUMENTS\n\nIMPORTANT: If stop_hook_active is true, return {\"decision\": undefined}\n\nOtherwise check if tasks complete..."
}
```

---

## Hook Output Not Visible

### Symptom
Hook runs but output not shown to user.

### Cause
`suppressOutput: true` or output goes to stderr.

### Solutions

**Don't suppress output**:
```json
{
  "decision": "approve",
  "reason": "ok",
  "suppressOutput": false
}
```

**Use systemMessage**:
```json
{
  "decision": "approve",
  "reason": "ok",
  "systemMessage": "This message will be shown to user"
}
```

**Write to stdout, not stderr**:
```bash
echo "This is shown" >&1
echo "This is hidden" >&2
```

---

## Permission Errors

### Symptom
Hook script can't read files or execute commands.

### Solutions

**Make script executable**:
```bash
chmod +x /path/to/hook.sh
```

**Check file ownership**:
```bash
ls -l /path/to/hook.sh
chown $USER /path/to/hook.sh
```

**Use absolute paths**:
```bash
# Instead of
command="./script.sh"

# Use
command="$CLAUDE_PROJECT_DIR/.claude/hooks/script.sh"
```

---

## Hook Timeouts

### Symptom
```
[DEBUG] Hook command timed out after 60000ms
```

### Solutions

**Increase timeout**:
```json
{
  "type": "command",
  "command": "/path/to/slow-script.sh",
  "timeout": 300000  // 5 minutes
}
```

**Optimize script**:
- Reduce unnecessary operations
- Cache results when possible
- Run expensive operations in background

**Run in background**:
```bash
#!/bin/bash
# Start long operation in background
/path/to/long-operation.sh &

# Return immediately
echo '{"decision": "approve", "reason": "ok"}'
```

---

## Matcher Conflicts

### Symptom
Multiple hooks triggering when only one expected.

### Cause
Tool name matches multiple matchers.

### Diagnostic
```
[DEBUG] Matched 3 hooks for query "Bash"
```

### Solutions

**Be more specific**:
```json
// Instead of
{"matcher": ".*"}  // Matches everything

// Use
{"matcher": "Bash"}  // Exact match
```

**Check overlapping patterns**:
```json
{
  "hooks": {
    "PreToolUse": [
      {"matcher": "Bash", ...},        // Matches Bash
      {"matcher": "Bash.*", ...},      // Also matches Bash!
      {"matcher": ".*", ...}           // Also matches everything!
    ]
  }
}
```

Remove overlaps or make them mutually exclusive.

---

## Environment Variables Not Working

### Symptom
`$CLAUDE_PROJECT_DIR` or other variables are empty.

### Solutions

**Check variable spelling**:
- `$CLAUDE_PROJECT_DIR` (correct)
- `$CLAUDE_PROJECT_ROOT` (wrong)

**Use double quotes**:
```json
{
  "command": "$CLAUDE_PROJECT_DIR/hooks/script.sh"
}
```

**In shell scripts, use from input**:
```bash
#!/bin/bash
input=$(cat)
cwd=$(echo "$input" | jq -r '.cwd')
cd "$cwd" || exit 1
```

---

## Debugging Workflow

**Step 1**: Enable debug mode
```bash
claude --debug
```

**Step 2**: Look for hook execution logs
```
[DEBUG] Executing hooks for PreToolUse:Bash
[DEBUG] Found 1 hook matchers
[DEBUG] Executing hook command: /path/to/script.sh
[DEBUG] Hook command completed with status 0
```

**Step 3**: Test hook in isolation
```bash
echo '{"test":"data"}' | /path/to/hook.sh
```

**Step 4**: Check script with `set -x`
```bash
#!/bin/bash
set -x  # Print each command before executing
# ... your script
```

**Step 5**: Add logging
```bash
#!/bin/bash
echo "Hook started" >> /tmp/hook-debug.log
input=$(cat)
echo "Input: $input" >> /tmp/hook-debug.log
# ... your logic
echo "Decision: $decision" >> /tmp/hook-debug.log
```

**Step 6**: Verify JSON output
```bash
echo '{"decision":"approve","reason":"test"}' | jq .
```

If `jq` fails, JSON is invalid.
