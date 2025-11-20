# Working Examples

Real-world hook configurations ready to use.

## Desktop Notifications

### macOS notification when input needed
```json
{
  "hooks": {
    "Notification": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "osascript -e 'display notification \"Claude needs your input\" with title \"Claude Code\" sound name \"Glass\"'"
          }
        ]
      }
    ]
  }
}
```

### Linux notification (notify-send)
```json
{
  "hooks": {
    "Notification": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "notify-send 'Claude Code' 'Awaiting your input' --urgency=normal"
          }
        ]
      }
    ]
  }
}
```

### Play sound on notification
```json
{
  "hooks": {
    "Notification": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "afplay /System/Library/Sounds/Glass.aiff"
          }
        ]
      }
    ]
  }
}
```

---

## Logging

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
            "command": "jq -r '\"[\" + (.timestamp // now | todate) + \"] \" + .tool_input.command + \" - \" + (.tool_input.description // \"No description\")' >> ~/.claude/bash-log.txt"
          }
        ]
      }
    ]
  }
}
```

### Log file operations
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '\"[\" + (now | todate) + \"] \" + .tool_name + \": \" + .tool_input.file_path' >> ~/.claude/file-operations.log"
          }
        ]
      }
    ]
  }
}
```

### Audit trail for MCP operations
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__.*",
        "hooks": [
          {
            "type": "command",
            "command": "jq '. + {timestamp: now}' >> ~/.claude/mcp-audit.jsonl"
          }
        ]
      }
    ]
  }
}
```

---

## Code Quality

### Auto-format after edits
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "prettier --write \"$(echo {} | jq -r '.tool_input.file_path')\" 2>/dev/null || true",
            "timeout": 10000
          }
        ]
      }
    ]
  }
}
```

### Run linter after code changes
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "eslint \"$(echo {} | jq -r '.tool_input.file_path')\" --fix 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

### Run tests before stopping
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/check-tests.sh"
          }
        ]
      }
    ]
  }
}
```

`check-tests.sh`:
```bash
#!/bin/bash
cd "$cwd" || exit 1

# Run tests
npm test > /dev/null 2>&1

if [ $? -eq 0 ]; then
  echo '{"decision": "approve", "reason": "All tests passing"}'
else
  echo '{"decision": "block", "reason": "Tests are failing. Please fix before stopping.", "systemMessage": "Run npm test to see failures"}'
fi
```

---

## Safety and Validation

### Block destructive commands
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/check-command-safety.sh"
          }
        ]
      }
    ]
  }
}
```

`check-command-safety.sh`:
```bash
#!/bin/bash
input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command')

# Check for dangerous patterns
if [[ "$command" == *"rm -rf /"* ]] || \
   [[ "$command" == *"mkfs"* ]] || \
   [[ "$command" == *"> /dev/sda"* ]]; then
  echo '{"decision": "block", "reason": "Destructive command detected", "systemMessage": "This command could cause data loss"}'
  exit 0
fi

# Check for force push to main
if [[ "$command" == *"git push"*"--force"* ]] && \
   [[ "$command" == *"main"* || "$command" == *"master"* ]]; then
  echo '{"decision": "block", "reason": "Force push to main branch blocked", "systemMessage": "Use a feature branch instead"}'
  exit 0
fi

echo '{"decision": "approve", "reason": "Command is safe"}'
```

### Validate commit messages
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Check if this is a git commit command: $ARGUMENTS\n\nIf it's a git commit, validate the message follows conventional commits format (feat|fix|docs|refactor|test|chore): description\n\nIf invalid format: {\"decision\": \"block\", \"reason\": \"Commit message must follow conventional commits\"}\nIf valid or not a commit: {\"decision\": \"approve\", \"reason\": \"ok\"}"
          }
        ]
      }
    ]
  }
}
```

### Block writes to critical files
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/check-protected-files.sh"
          }
        ]
      }
    ]
  }
}
```

`check-protected-files.sh`:
```bash
#!/bin/bash
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path')

# Protected files
protected_files=(
  "package-lock.json"
  ".env.production"
  "credentials.json"
)

for protected in "${protected_files[@]}"; do
  if [[ "$file_path" == *"$protected"* ]]; then
    echo "{\"decision\": \"block\", \"reason\": \"Cannot modify $protected\", \"systemMessage\": \"This file is protected from automated changes\"}"
    exit 0
  fi
done

echo '{"decision": "approve", "reason": "File is not protected"}'
```

---

## Context Injection

### Load sprint context at session start
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/load-sprint-context.sh"
          }
        ]
      }
    ]
  }
}
```

`load-sprint-context.sh`:
```bash
#!/bin/bash

# Read sprint info from file
sprint_info=$(cat "$CLAUDE_PROJECT_DIR/.sprint-context.txt" 2>/dev/null || echo "No sprint context available")

# Return as SessionStart context
jq -n \
  --arg context "$sprint_info" \
  '{
    "hookSpecificOutput": {
      "hookEventName": "SessionStart",
      "additionalContext": $context
    }
  }'
```

### Load git branch context
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "cd \"$cwd\" && git branch --show-current | jq -Rs '{\"hookSpecificOutput\": {\"hookEventName\": \"SessionStart\", \"additionalContext\": (\"Current branch: \" + .)}}'"
          }
        ]
      }
    ]
  }
}
```

### Load environment info
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo '{\"hookSpecificOutput\": {\"hookEventName\": \"SessionStart\", \"additionalContext\": \"Environment: '$(hostname)'\\nNode version: '$(node --version 2>/dev/null || echo 'not installed')'\\nPython version: '$(python3 --version 2>/dev/null || echo 'not installed)'\"}}'"
          }
        ]
      }
    ]
  }
}
```

---

## Workflow Automation

### Auto-commit after major changes
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/auto-commit.sh"
          }
        ]
      }
    ]
  }
}
```

`auto-commit.sh`:
```bash
#!/bin/bash
cd "$cwd" || exit 1

# Check if there are changes
if ! git diff --quiet; then
  git add -A
  git commit -m "chore: auto-commit from claude session" --no-verify
  echo '{"systemMessage": "Changes auto-committed"}'
fi
```

### Update documentation after code changes
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/update-docs.sh",
            "timeout": 30000
          }
        ]
      }
    ]
  }
}
```

### Run pre-commit hooks
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/check-pre-commit.sh"
          }
        ]
      }
    ]
  }
}
```

`check-pre-commit.sh`:
```bash
#!/bin/bash
input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command')

# If git commit, run pre-commit hooks first
if [[ "$command" == *"git commit"* ]]; then
  pre-commit run --all-files > /dev/null 2>&1

  if [ $? -ne 0 ]; then
    echo '{"decision": "block", "reason": "Pre-commit hooks failed", "systemMessage": "Fix formatting/linting issues first"}'
    exit 0
  fi
fi

echo '{"decision": "approve", "reason": "ok"}'
```

---

## Session Management

### Archive transcript on session end
```json
{
  "hooks": {
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/archive-session.sh"
          }
        ]
      }
    ]
  }
}
```

`archive-session.sh`:
```bash
#!/bin/bash
input=$(cat)
transcript_path=$(echo "$input" | jq -r '.transcript_path')
session_id=$(echo "$input" | jq -r '.session_id')

# Create archive directory
archive_dir="$HOME/.claude/archives"
mkdir -p "$archive_dir"

# Copy transcript with timestamp
timestamp=$(date +%Y%m%d-%H%M%S)
cp "$transcript_path" "$archive_dir/${timestamp}-${session_id}.jsonl"

echo "Session archived to $archive_dir"
```

### Save session stats
```json
{
  "hooks": {
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "jq '. + {ended_at: now}' >> ~/.claude/session-stats.jsonl"
          }
        ]
      }
    ]
  }
}
```

---

## Advanced Patterns

### Intelligent stop logic
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Review the conversation: $ARGUMENTS\n\nCheck if:\n1. All user-requested tasks are complete\n2. Tests are passing (if code changes made)\n3. No errors that need fixing\n4. Documentation updated (if applicable)\n\nIf incomplete: {\"decision\": \"block\", \"reason\": \"specific issue\", \"systemMessage\": \"what needs to be done\"}\n\nIf complete: {\"decision\": \"approve\", \"reason\": \"all tasks done\"}\n\nIMPORTANT: If stop_hook_active is true, return {\"decision\": undefined} to avoid infinite loop",
            "timeout": 30000
          }
        ]
      }
    ]
  }
}
```

### Chain multiple hooks
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'First hook' >> /tmp/hook-chain.log"
          },
          {
            "type": "command",
            "command": "echo 'Second hook' >> /tmp/hook-chain.log"
          },
          {
            "type": "prompt",
            "prompt": "Final validation: $ARGUMENTS"
          }
        ]
      }
    ]
  }
}
```

Hooks execute in order. First block stops the chain.

### Conditional execution based on file type
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/format-by-type.sh"
          }
        ]
      }
    ]
  }
}
```

`format-by-type.sh`:
```bash
#!/bin/bash
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path')

case "$file_path" in
  *.js|*.jsx|*.ts|*.tsx)
    prettier --write "$file_path"
    ;;
  *.py)
    black "$file_path"
    ;;
  *.go)
    gofmt -w "$file_path"
    ;;
esac
```

---

## Project-Specific Hooks

Use `$CLAUDE_PROJECT_DIR` for project-specific hooks:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/init-session.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/validate-changes.sh"
          }
        ]
      }
    ]
  }
}
```

This keeps hook scripts versioned with the project.
