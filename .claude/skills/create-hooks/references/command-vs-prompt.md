# Command vs Prompt Hooks

Decision guide for choosing between command-based and prompt-based hooks.

## Decision Tree

```
Need to execute a hook?
│
├─ Simple yes/no validation?
│  └─ Use COMMAND (faster, cheaper)
│
├─ Need natural language understanding?
│  └─ Use PROMPT (LLM evaluation)
│
├─ External tool interaction?
│  └─ Use COMMAND (formatters, linters, git)
│
├─ Complex decision logic?
│  └─ Use PROMPT (reasoning required)
│
└─ Logging/notification only?
   └─ Use COMMAND (no decision needed)
```

---

## Command Hooks

### Characteristics

- **Execution**: Shell command
- **Input**: JSON via stdin
- **Output**: JSON via stdout (optional)
- **Speed**: Fast (no LLM call)
- **Cost**: Free (no API usage)
- **Complexity**: Limited to shell scripting logic

### When to use

✅ **Use command hooks for**:
- File operations (read, write, check existence)
- Running tools (prettier, eslint, git)
- Simple pattern matching (grep, regex)
- Logging to files
- Desktop notifications
- Fast validation (file size, permissions)

❌ **Don't use command hooks for**:
- Natural language analysis
- Complex decision logic
- Context-aware validation
- Semantic understanding

### Examples

**1. Log bash commands**
```json
{
  "type": "command",
  "command": "jq -r '\"\\(.tool_input.command) - \\(.tool_input.description // \\\"No description\\\")\"' >> ~/.claude/bash-log.txt"
}
```

**2. Block if file doesn't exist**
```bash
#!/bin/bash
# check-file-exists.sh

input=$(cat)
file=$(echo "$input" | jq -r '.tool_input.file_path')

if [ ! -f "$file" ]; then
  echo '{"decision": "block", "reason": "File does not exist"}'
  exit 0
fi

echo '{"decision": "approve", "reason": "File exists"}'
```

**3. Run prettier after edits**
```json
{
  "type": "command",
  "command": "prettier --write \"$(echo {} | jq -r '.tool_input.file_path')\"",
  "timeout": 10000
}
```

**4. Desktop notification**
```json
{
  "type": "command",
  "command": "osascript -e 'display notification \"Claude needs input\" with title \"Claude Code\"'"
}
```

### Parsing input in commands

Command hooks receive JSON via stdin. Use `jq` to parse:

```bash
#!/bin/bash
input=$(cat)  # Read stdin

# Extract fields
tool_name=$(echo "$input" | jq -r '.tool_name')
command=$(echo "$input" | jq -r '.tool_input.command')
session_id=$(echo "$input" | jq -r '.session_id')

# Your logic here
if [[ "$command" == *"rm -rf"* ]]; then
  echo '{"decision": "block", "reason": "Dangerous command"}'
else
  echo '{"decision": "approve", "reason": "Safe"}'
fi
```

---

## Prompt Hooks

### Characteristics

- **Execution**: LLM evaluates prompt
- **Input**: Prompt string with `$ARGUMENTS` placeholder
- **Output**: LLM generates JSON response
- **Speed**: Slower (~1-3s per evaluation)
- **Cost**: Uses API credits
- **Complexity**: Can reason, understand context, analyze semantics

### When to use

✅ **Use prompt hooks for**:
- Natural language validation
- Semantic analysis (intent, safety, appropriateness)
- Complex decision trees
- Context-aware checks
- Reasoning about code quality
- Understanding user intent

❌ **Don't use prompt hooks for**:
- Simple pattern matching (use regex/grep)
- File operations (use command hooks)
- High-frequency events (too slow/expensive)
- Non-decision tasks (logging, notifications)

### Examples

**1. Validate commit messages**
```json
{
  "type": "prompt",
  "prompt": "Evaluate this git commit message: $ARGUMENTS\n\nCheck if it:\n1. Starts with conventional commit type (feat|fix|docs|refactor|test|chore)\n2. Is descriptive and clear\n3. Under 72 characters\n\nReturn: {\"decision\": \"approve\" or \"block\", \"reason\": \"specific feedback\"}"
}
```

**2. Check if Stop is appropriate**
```json
{
  "type": "prompt",
  "prompt": "Review the conversation transcript: $ARGUMENTS\n\nDetermine if Claude should stop:\n1. All user tasks completed?\n2. Any errors that need fixing?\n3. Tests passing?\n4. Documentation updated?\n\nIf incomplete: {\"decision\": \"block\", \"reason\": \"what's missing\"}\nIf complete: {\"decision\": \"approve\", \"reason\": \"all done\"}"
}
```

**3. Validate code changes for security**
```json
{
  "type": "prompt",
  "prompt": "Analyze this code change for security issues: $ARGUMENTS\n\nCheck for:\n- SQL injection vulnerabilities\n- XSS attack vectors\n- Authentication bypasses\n- Sensitive data exposure\n\nIf issues found: {\"decision\": \"block\", \"reason\": \"specific vulnerabilities\"}\nIf safe: {\"decision\": \"approve\", \"reason\": \"no issues found\"}"
}
```

**4. Semantic prompt validation**
```json
{
  "type": "prompt",
  "prompt": "Evaluate user prompt: $ARGUMENTS\n\nIs this:\n1. Related to coding/development?\n2. Appropriate and professional?\n3. Clear and actionable?\n\nIf inappropriate: {\"decision\": \"block\", \"reason\": \"why\"}\nIf good: {\"decision\": \"approve\", \"reason\": \"ok\"}"
}
```

### Writing effective prompts

**Be specific about output format**:
```
Return JSON: {"decision": "approve" or "block", "reason": "explanation"}
```

**Provide clear criteria**:
```
Block if:
1. Command contains 'rm -rf /'
2. Force push to main branch
3. Credentials in plain text

Otherwise approve.
```

**Use $ARGUMENTS placeholder**:
```
Analyze this input: $ARGUMENTS

Check for...
```

The `$ARGUMENTS` placeholder is replaced with the actual hook input JSON.

---

## Performance Comparison

| Aspect | Command Hook | Prompt Hook |
|--------|--------------|-------------|
| **Speed** | <100ms | 1-3s |
| **Cost** | Free | ~$0.001-0.01 per call |
| **Complexity** | Shell scripting | Natural language |
| **Context awareness** | Limited | High |
| **Reasoning** | No | Yes |
| **Best for** | Operations, logging | Validation, analysis |

---

## Combining Both

You can use multiple hooks for the same event:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "echo \"$input\" >> ~/bash-log.txt",
            "comment": "Log every command (fast)"
          },
          {
            "type": "prompt",
            "prompt": "Analyze this bash command for safety: $ARGUMENTS",
            "comment": "Validate with LLM (slower, smarter)"
          }
        ]
      }
    ]
  }
}
```

Hooks execute in order. If any hook blocks, execution stops.

---

## Recommendations

**High-frequency events** (PreToolUse, PostToolUse):
- Prefer command hooks
- Use prompt hooks sparingly
- Cache LLM decisions when possible

**Low-frequency events** (Stop, UserPromptSubmit):
- Prompt hooks are fine
- Cost/latency less critical

**Balance**:
- Command hooks for simple checks
- Prompt hooks for complex validation
- Combine when appropriate
