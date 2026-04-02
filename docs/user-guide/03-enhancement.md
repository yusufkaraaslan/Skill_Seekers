# Enhancement Guide

> **Skill Seekers v3.1.0**  
> **AI-powered quality improvement for skills**

---

## What is Enhancement?

Enhancement uses AI to improve the quality of generated SKILL.md files:

```
Basic SKILL.md ──▶ AI Enhancer ──▶ Enhanced SKILL.md
(100 lines)         (60 sec)        (400+ lines)
     ↓                                  ↓
  Sparse                          Comprehensive
  examples                        with patterns,
                                  navigation, depth
```

---

## Enhancement Levels

Choose how much enhancement to apply:

| Level | What Happens | Time | Cost |
|-------|--------------|------|------|
| **0** | No enhancement | 0 sec | Free |
| **1** | SKILL.md only | ~30 sec | Low |
| **2** | + architecture/config | ~60 sec | Medium |
| **3** | Full enhancement | ~2 min | Higher |

**Default:** Level 2 (recommended balance)

---

## Enhancement Modes

### API Mode (Default if key available)

Uses any supported AI provider API via `AgentClient`. Providers: Anthropic (Claude), Moonshot/Kimi, Google Gemini, OpenAI.

**Requirements:**
```bash
# Any one of these activates API mode:
export ANTHROPIC_API_KEY=sk-ant-...   # Claude
export MOONSHOT_API_KEY=...           # Kimi
export GOOGLE_API_KEY=...             # Gemini
export OPENAI_API_KEY=...             # OpenAI
```

**Usage:**
```bash
# Auto-detects API mode
skill-seekers create <source>

# Explicit
skill-seekers enhance output/my-skill/ --agent api
```

**Pros:**
- Fast (~60 seconds)
- No local setup needed

**Cons:**
- Costs ~$0.10-0.30 per skill
- Requires API key

---

### LOCAL Mode (Default if no key)

Uses a local AI coding agent via `AgentClient`. Supports Claude Code, Kimi Code, Codex, Copilot, OpenCode, or custom agents.

**Requirements:**
- One of the supported agents installed (Claude Code, Codex, Copilot, OpenCode, Kimi)

**Usage:**
```bash
# Auto-detects LOCAL mode (no API key), defaults to Claude Code
skill-seekers create <source>

# Use a different local agent
skill-seekers enhance output/my-skill/ --agent codex
skill-seekers enhance output/my-skill/ --agent copilot
skill-seekers enhance output/my-skill/ --agent kimi
skill-seekers enhance output/my-skill/ --agent opencode

# Custom agent
skill-seekers enhance output/my-skill/ --agent custom --agent-cmd "my-agent {prompt_file}"
```

**Pros:**
- Free (with agent subscription)
- Better quality (full context)
- Agent-agnostic -- works with any supported coding agent

**Cons:**
- Requires a local coding agent
- Slightly slower (~60-120 sec)

---

## How to Enhance

### During Creation

```bash
# Default enhancement (level 2)
skill-seekers create <source>

# No enhancement (fastest)
skill-seekers create <source> --enhance-level 0

# Maximum enhancement
skill-seekers create <source> --enhance-level 3
```

### After Creation

```bash
# Enhance existing skill
skill-seekers enhance output/my-skill/

# With specific agent
skill-seekers enhance output/my-skill/ --agent local

# With timeout
skill-seekers enhance output/my-skill/ --timeout 1200
```

### Background Mode

```bash
# Run in background
skill-seekers enhance output/my-skill/ --background

# Check status
skill-seekers enhance-status output/my-skill/

# Watch in real-time
skill-seekers enhance-status output/my-skill/ --watch
```

---

## Enhancement Workflows

Apply specialized AI analysis with preset workflows.

### Built-in Presets

| Preset | Stages | Focus |
|--------|--------|-------|
| `default` | 2 | General improvement |
| `minimal` | 1 | Light touch-up |
| `security-focus` | 4 | Security analysis |
| `architecture-comprehensive` | 7 | Deep architecture |
| `api-documentation` | 3 | API docs focus |

### Using Workflows

```bash
# Apply workflow
skill-seekers create <source> --enhance-workflow security-focus

# Chain multiple workflows
skill-seekers create <source> \
  --enhance-workflow security-focus \
  --enhance-workflow api-documentation

# List available
skill-seekers workflows list

# Show workflow content
skill-seekers workflows show security-focus
```

### Custom Workflows

Create your own YAML workflow:

```yaml
# my-workflow.yaml
name: my-custom
stages:
  - name: overview
    prompt: "Add comprehensive overview section"
  - name: examples
    prompt: "Add practical code examples"
```

```bash
# Add workflow
skill-seekers workflows add my-workflow.yaml

# Use it
skill-seekers create <source> --enhance-workflow my-custom
```

---

## What Enhancement Adds

### Level 1: SKILL.md Improvement

- Better structure and organization
- Improved descriptions
- Fixed formatting
- Added navigation

### Level 2: Architecture & Config (Default)

Everything in Level 1, plus:

- Architecture overview
- Configuration examples
- Pattern documentation
- Best practices

### Level 3: Full Enhancement

Everything in Level 2, plus:

- Deep code examples
- Common pitfalls
- Performance tips
- Integration guides

---

## Enhancement Workflow Details

### Security-Focus Workflow

4 stages:
1. **Security Overview** - Identify security features
2. **Vulnerability Analysis** - Common issues
3. **Best Practices** - Secure coding patterns
4. **Compliance** - Security standards

### Architecture-Comprehensive Workflow

7 stages:
1. **System Overview** - High-level architecture
2. **Component Analysis** - Key components
3. **Data Flow** - How data moves
4. **Integration Points** - External connections
5. **Scalability** - Performance considerations
6. **Deployment** - Infrastructure
7. **Maintenance** - Operational concerns

### API-Documentation Workflow

3 stages:
1. **Endpoint Catalog** - All API endpoints
2. **Request/Response** - Detailed examples
3. **Error Handling** - Common errors

---

## Monitoring Enhancement

### Check Status

```bash
# Current status
skill-seekers enhance-status output/my-skill/

# JSON output (for scripting)
skill-seekers enhance-status output/my-skill/ --json

# Watch mode
skill-seekers enhance-status output/my-skill/ --watch --interval 10
```

### Process Status Values

| Status | Meaning |
|--------|---------|
| `running` | Enhancement in progress |
| `completed` | Successfully finished |
| `failed` | Error occurred |
| `pending` | Waiting to start |

---

## When to Skip Enhancement

Skip enhancement when:

- **Testing:** Quick iteration during development
- **Large batches:** Process many skills, enhance best ones later
- **Custom processing:** You have your own enhancement pipeline
- **Time critical:** Need results immediately

```bash
# Skip during creation
skill-seekers create <source> --enhance-level 0

# Enhance best ones later
skill-seekers enhance output/best-skill/
```

---

## Enhancement Best Practices

### 1. Use Level 2 for Most Cases

```bash
# Default is usually perfect
skill-seekers create <source>
```

### 2. Apply Domain-Specific Workflows

```bash
# Security review
skill-seekers create <source> --enhance-workflow security-focus

# API focus
skill-seekers create <source> --enhance-workflow api-documentation
```

### 3. Chain for Comprehensive Analysis

```bash
# Multiple perspectives
skill-seekers create <source> \
  --enhance-workflow security-focus \
  --enhance-workflow architecture-comprehensive
```

### 4. Use LOCAL Mode for Quality

```bash
# Better results with Claude Code
export ANTHROPIC_API_KEY=""  # Unset to force LOCAL
skill-seekers enhance output/my-skill/
```

### 5. Enhance Iteratively

```bash
# Create without enhancement
skill-seekers create <source> --enhance-level 0

# Review and enhance
skill-seekers enhance output/my-skill/
# Review again...
skill-seekers enhance output/my-skill/  # Run again for more polish
```

---

## Troubleshooting

### "Enhancement failed: No API key"

**Solution:**
```bash
# Set API key
export ANTHROPIC_API_KEY=sk-ant-...

# Or use LOCAL mode
skill-seekers enhance output/my-skill/ --agent local
```

### "Enhancement timeout"

**Solution:**
```bash
# Increase timeout
skill-seekers enhance output/my-skill/ --timeout 1200

# Or use background mode
skill-seekers enhance output/my-skill/ --background
```

### "Claude Code not found" (LOCAL mode)

**Solution:**
```bash
# Install Claude Code
# See: https://claude.ai/code

# Or switch to API mode
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers enhance output/my-skill/ --agent api
```

### "Workflow not found"

**Solution:**
```bash
# List available workflows
skill-seekers workflows list

# Check spelling
skill-seekers create <source> --enhance-workflow security-focus
```

---

## Cost Estimation

### API Mode Costs

| Skill Size | Level 1 | Level 2 | Level 3 |
|------------|---------|---------|---------|
| Small (< 50 pages) | $0.02 | $0.05 | $0.10 |
| Medium (50-200 pages) | $0.05 | $0.10 | $0.20 |
| Large (200-500 pages) | $0.10 | $0.20 | $0.40 |

*Costs are approximate and depend on actual content.*

### LOCAL Mode Costs

Free with Claude Code Max subscription (~$20/month).

---

## Summary

| Approach | When to Use |
|----------|-------------|
| **Level 0** | Testing, batch processing |
| **Level 2 (default)** | Most use cases |
| **Level 3** | Maximum quality needed |
| **API Mode** | Speed, no Claude Code |
| **LOCAL Mode** | Quality, free with Max |
| **Workflows** | Domain-specific needs |

---

## Next Steps

- [Workflows Guide](05-workflows.md) - Custom workflow creation
- [Packaging Guide](04-packaging.md) - Export enhanced skills
- [MCP Reference](../reference/MCP_REFERENCE.md) - Enhancement via MCP
