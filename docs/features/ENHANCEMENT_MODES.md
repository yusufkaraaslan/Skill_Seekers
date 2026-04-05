# Enhancement Modes Guide

Complete guide to all LOCAL enhancement modes in Skill Seekers.

## Overview

Skill Seekers supports **4 enhancement modes** for different use cases:

1. **Headless** (default) - Runs in foreground, waits for completion
2. **Background** - Runs in background thread, returns immediately
3. **Daemon** - Fully detached process, continues after parent exits
4. **Terminal** - Opens new terminal window (interactive)

## Multi-Agent Support (NEW)

All enhancement modes now support **multiple local coding agents**:

### Supported Agents

| Agent | Display Name | Default | Notes |
|-------|--------------|---------|-------|
| **claude** | Claude Code | ✅ Yes | Your Claude Code Max plan (no API costs) |
| **codex** | OpenAI Codex CLI | No | Uses `codex exec --full-auto` |
| **copilot** | GitHub Copilot CLI | No | Uses `gh copilot chat` |
| **opencode** | OpenCode CLI | No | Uses `opencode` command |
| **custom** | Custom CLI Agent | No | Use any CLI tool with `--agent-cmd` |

### Agent Selection

**CLI Flags:**
```bash
# Use Codex CLI
skill-seekers enhance output/react/ --agent codex

# Use Copilot CLI
skill-seekers enhance output/react/ --agent copilot

# Use OpenCode CLI
skill-seekers enhance output/react/ --agent opencode

# Custom agent with file input
skill-seekers enhance output/react/ --agent custom --agent-cmd "my-agent --prompt {prompt_file}"

# Custom agent with stdin input
skill-seekers enhance output/react/ --agent custom --agent-cmd "my-agent --enhance"
```

**Environment Variables (CI/CD):**
```bash
# Set default agent
export SKILL_SEEKER_AGENT=codex
skill-seekers enhance output/react/

# Set custom command template
export SKILL_SEEKER_AGENT=custom
export SKILL_SEEKER_AGENT_CMD="my-agent {prompt_file}"
skill-seekers enhance output/react/
```

### Agent Command Templates

**File-based agents** (use `{prompt_file}` placeholder):
```bash
--agent-cmd "my-agent --input {prompt_file}"
--agent-cmd "my-agent < {prompt_file}"
```

**Stdin-based agents** (no placeholder):
```bash
--agent-cmd "my-agent --enhance"
```

### Security

Custom commands are validated for security:
- ✅ Blocks dangerous shell characters: `;`, `&`, `|`, `$`, `` ` ``, `\n`, `\r`
- ✅ Validates executable exists in PATH
- ✅ Safe parsing with `shlex.split()`

**Example rejection:**
```bash
# This will fail with security error:
skill-seekers enhance . --agent custom --agent-cmd "evil; rm -rf /"
# Error: Custom command contains dangerous shell characters
```

### Agent Aliases

Agent names are normalized with smart alias support:
```bash
# All resolve to "claude"
--agent claude
--agent claude-code
--agent claude_code
--agent CLAUDE

# All resolve to "codex"
--agent codex
--agent codex-cli

# All resolve to "copilot"
--agent copilot
--agent copilot-cli
```

## Mode Comparison

| Feature | Headless | Background | Daemon | Terminal |
|---------|----------|------------|--------|----------|
| **Blocks** | Yes (waits) | No (returns) | No (returns) | No (separate window) |
| **Survives parent exit** | No | No | **Yes** | Yes |
| **Progress monitoring** | Direct output | Status file | Status file + logs | Visual in terminal |
| **Force mode** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| **Best for** | CI/CD | Scripts | Long tasks | Manual work |

## Usage Examples

### 1. Headless Mode (Default)

**When to use**: CI/CD pipelines, automation scripts, when you want to wait for completion

```bash
# Basic usage - waits until done (uses Claude Code by default)
skill-seekers enhance output/react/

# Use different agent
skill-seekers enhance output/react/ --agent codex
skill-seekers enhance output/react/ --agent copilot

# With custom timeout
skill-seekers enhance output/react/ --timeout 1200

# Force mode - no confirmations
skill-seekers enhance output/react/ --force

# Combine agent + force mode
skill-seekers enhance output/react/ --agent codex --force
```

**Behavior**:
- Runs selected coding agent CLI directly (default: Claude Code)
- **BLOCKS** until enhancement completes
- Shows progress output
- Returns exit code: 0 = success, 1 = failure

### 2. Background Mode

**When to use**: When you want to continue working while enhancement runs

```bash
# Start enhancement in background (default agent: Claude Code)
skill-seekers enhance output/react/ --background

# Start with different agent
skill-seekers enhance output/react/ --background --agent codex
skill-seekers enhance output/react/ --background --agent copilot

# Returns immediately with status file created
# ✅ Background enhancement started!
# 📊 Status file: output/react/.enhancement_status.json
```

**Behavior**:
- Starts background thread
- Returns immediately
- Creates `.enhancement_status.json` for monitoring
- Thread continues even if you close terminal

**Monitor progress**:
```bash
# Check status once
skill-seekers enhance-status output/react/

# Watch in real-time
skill-seekers enhance-status output/react/ --watch

# JSON output (for scripts)
skill-seekers enhance-status output/react/ --json
```

### 3. Daemon Mode

**When to use**: Long-running tasks that must survive parent process exit

```bash
# Start as daemon (fully detached)
skill-seekers enhance output/react/ --daemon

# Process continues even if you:
# - Close the terminal
# - Logout
# - SSH session ends
```

**Behavior**:
- Creates fully detached process using `nohup`
- Writes to `.enhancement_daemon.log`
- Creates status file with PID
- **Survives parent process exit**

**Monitor daemon**:
```bash
# Check status
skill-seekers enhance-status output/react/

# View logs
tail -f output/react/.enhancement_daemon.log

# Check if process is running
cat output/react/.enhancement_status.json
# Look for "pid" field
```

### 4. Terminal Mode (Interactive)

**When to use**: When you want to see Claude Code in action

```bash
# Open in new terminal window
skill-seekers enhance output/react/ --interactive-enhancement
```

**Behavior**:
- Opens new terminal window (macOS)
- Runs Claude Code visually
- Terminal auto-closes when done
- Useful for debugging

## Force Mode (Default ON)

**What it does**: Skips ALL confirmations, auto-answers "yes" to everything

**Default behavior**: Force mode is **ON by default** for maximum automation

```bash
# Force mode is ON by default (no flag needed)
skill-seekers enhance output/react/

# Disable force mode if you want confirmations
skill-seekers enhance output/react/ --no-force
```

**Use cases**:
- ✅ CI/CD automation (default ON)
- ✅ Batch processing multiple skills (default ON)
- ✅ Unattended execution (default ON)
- ⚠️ Use `--no-force` if you need manual confirmation prompts

## Status File Format

When using `--background` or `--daemon`, a status file is created:

**Location**: `{skill_directory}/.enhancement_status.json`

**Format**:
```json
{
  "status": "running",
  "message": "Running Claude Code enhancement...",
  "progress": 0.5,
  "timestamp": "2026-01-03T12:34:56.789012",
  "skill_dir": "/path/to/output/react",
  "error": null,
  "pid": 12345
}
```

**Status values**:
- `pending` - Task queued, not started yet
- `running` - Currently executing
- `completed` - Finished successfully
- `failed` - Error occurred (see `error` field)

## Monitoring Background Tasks

### Check Status Command

```bash
# One-time check
skill-seekers enhance-status output/react/

# Output:
# ============================================================
# ENHANCEMENT STATUS: RUNNING
# ============================================================
#
# 🔄 Status: RUNNING
#    Message: Running Claude Code enhancement...
#    Progress: [██████████░░░░░░░░░░] 50%
#    PID: 12345
#    Timestamp: 2026-01-03T12:34:56.789012
```

### Watch Mode (Real-time)

```bash
# Watch status updates every 2 seconds
skill-seekers enhance-status output/react/ --watch

# Custom interval
skill-seekers enhance-status output/react/ --watch --interval 5
```

### JSON Output (For Scripts)

```bash
# Get raw JSON
skill-seekers enhance-status output/react/ --json

# Use in scripts
STATUS=$(skill-seekers enhance-status output/react/ --json | jq -r '.status')
if [ "$STATUS" = "completed" ]; then
    echo "Enhancement complete!"
fi
```

## Advanced Workflows

### Batch Enhancement (Multiple Skills)

```bash
#!/bin/bash
# Enhance multiple skills in parallel
# Note: Force mode is ON by default (no --force flag needed)

skills=("react" "vue" "django" "fastapi")

for skill in "${skills[@]}"; do
    echo "Starting enhancement: $skill"
    skill-seekers enhance output/$skill/ --background
done

echo "All enhancements started in background!"

# Monitor all
for skill in "${skills[@]}"; do
    skill-seekers enhance-status output/$skill/
done
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Enhance skill
  run: |
    # Headless mode (blocks until done, force is ON by default)
    skill-seekers enhance output/react/ --timeout 1200

    # Check if enhancement succeeded
    if [ $? -eq 0 ]; then
      echo "✅ Enhancement successful"
    else
      echo "❌ Enhancement failed"
      exit 1
    fi
```

### Long-running Daemon

```bash
# Start daemon for large skill
skill-seekers enhance output/godot-large/ --daemon --timeout 3600

# Logout and come back later
# ... (hours later) ...

# Check if it completed
skill-seekers enhance-status output/godot-large/
```

## Timeout Configuration

Default timeout: **600 seconds (10 minutes)**

**Adjust based on skill size**:

```bash
# Small skills (< 100 pages)
skill-seekers enhance output/hono/ --timeout 300

# Medium skills (100-1000 pages)
skill-seekers enhance output/react/ --timeout 600

# Large skills (1000+ pages)
skill-seekers enhance output/godot/ --timeout 1200

# Extra large (with PDF/GitHub sources)
skill-seekers enhance output/django-unified/ --timeout 1800
```

**What happens on timeout**:
- Headless: Returns error immediately
- Background: Status marked as `failed` with timeout error
- Daemon: Same as background
- Terminal: Claude Code keeps running (user can see it)

## Error Handling

### Status Check Exit Codes

```bash
skill-seekers enhance-status output/react/
echo $?

# Exit codes:
# 0 = completed successfully
# 1 = failed (error occurred)
# 2 = no status file found (not started or cleaned up)
```

### Common Errors

**"claude command not found"**:
```bash
# Install Claude Code CLI
# See: https://docs.claude.com/claude-code
```

**"Enhancement timed out"**:
```bash
# Increase timeout
skill-seekers enhance output/react/ --timeout 1200
```

**"SKILL.md was not updated"**:
```bash
# Check if references exist
ls output/react/references/

# Try terminal mode to see what's happening
skill-seekers enhance output/react/ --interactive-enhancement
```

## File Artifacts

Enhancement creates these files:

```
output/react/
├── SKILL.md                    # Enhanced file
├── SKILL.md.backup             # Original backup
├── .enhancement_status.json    # Status (background/daemon only)
├── .enhancement_daemon.log     # Logs (daemon only)
└── .enhancement_daemon.py      # Daemon script (daemon only)
```

**Cleanup**:
```bash
# Remove status files after completion
rm output/react/.enhancement_status.json
rm output/react/.enhancement_daemon.log
rm output/react/.enhancement_daemon.py
```

## API Mode Configuration

When using API mode for AI enhancement (instead of LOCAL mode), you can configure any Claude-compatible endpoint:

```bash
# Required for API mode
export ANTHROPIC_API_KEY=sk-ant-...

# Optional: Use custom Claude-compatible endpoint (e.g., GLM-4.7)
export ANTHROPIC_BASE_URL=https://your-endpoint.com/v1
```

**Note**: You can use any Claude-compatible API by setting `ANTHROPIC_BASE_URL`. This includes:
- GLM-4.7 (智谱 AI)
- Other Claude-compatible services

**All AI enhancement features respect these settings**:
- `enhance_skill.py` - API mode SKILL.md enhancement
- `ai_enhancer.py` - C3.1/C3.2 pattern and test example enhancement
- `guide_enhancer.py` - C3.3 guide enhancement
- `config_enhancer.py` - C3.4 configuration enhancement
- `adaptors/claude.py` - Claude platform adaptor enhancement

## Comparison with API Mode

| Feature | LOCAL Mode | API Mode |
|---------|-----------|----------|
| **API Key** | Not needed | Required (ANTHROPIC_API_KEY) |
| **Endpoint** | N/A | Customizable via ANTHROPIC_BASE_URL |
| **Cost** | Free (uses Claude Code Max) | ~$0.15-$0.30 per skill |
| **Speed** | 30-60 seconds | 20-40 seconds |
| **Quality** | 9/10 | 9/10 (same) |
| **Modes** | 4 modes | 1 mode only |
| **Automation** | ✅ Full support | ✅ Full support |
| **Best for** | Personal use, small teams | CI/CD, high volume |

## Best Practices

1. **Use headless by default** - Simple and reliable
2. **Use background for scripts** - When you need to do other work
3. **Use daemon for large tasks** - When task might take hours
4. **Use force in CI/CD** - Avoid hanging on confirmations
5. **Always set timeout** - Prevent infinite waits
6. **Monitor background tasks** - Use enhance-status to check progress

## Troubleshooting

### Background task not progressing

```bash
# Check status
skill-seekers enhance-status output/react/ --json

# If stuck, check process
ps aux | grep claude

# Kill if needed
kill -9 <PID>
```

### Daemon not starting

```bash
# Check logs
cat output/react/.enhancement_daemon.log

# Check status file
cat output/react/.enhancement_status.json

# Try without force mode
skill-seekers enhance output/react/ --daemon
```

### Status file shows error

```bash
# Read error details
skill-seekers enhance-status output/react/ --json | jq -r '.error'

# Common fixes:
# 1. Increase timeout
# 2. Check references exist
# 3. Try terminal mode to debug
```

## See Also

- [ENHANCEMENT.md](ENHANCEMENT.md) - Main enhancement guide
- [UPLOAD_GUIDE.md](UPLOAD_GUIDE.md) - Upload instructions
- [README.md](../README.md) - Main documentation
