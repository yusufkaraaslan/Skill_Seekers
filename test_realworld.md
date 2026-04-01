# Real-World Test Scenarios

## Test 1: Create Skill with Kimi (LOCAL mode)

```bash
# Set Kimi as the agent
export SKILL_SEEKER_AGENT=kimi

# Create a skill from documentation
skill-seekers create https://react.dev \
  --name react-docs \
  --preset quick \
  --enhance-level 2 \
  --output ./output/react-kimi

# Verify output
ls -la ./output/react-kimi/
cat ./output/react-kimi/SKILL.md | head -20
```

## Test 2: Create Skill with Claude (LOCAL mode)

```bash
# Set Claude as the agent
export SKILL_SEEKER_AGENT=claude

# Create a skill from GitHub
skill-seekers create facebook/react \
  --name react-github \
  --preset standard \
  --enhance-level 2 \
  --output ./output/react-claude

# Verify output
ls -la ./output/react-claude/
```

## Test 3: Kimi API Mode (with MOONSHOT_API_KEY)

```bash
# Set API key
export MOONSHOT_API_KEY=sk-your-key-here

# Create skill with API enhancement
skill-seekers create https://docs.python.org \
  --name python-docs \
  --preset comprehensive \
  --enhance-level 3 \
  --output ./output/python-kimi-api

# Should use API mode automatically (detected from env var)
```

## Test 4: Claude API Mode (with ANTHROPIC_API_KEY)

```bash
# Set API key
export ANTHROPIC_API_KEY=sk-your-key-here

# Create skill with API enhancement
skill-seekers create https://docs.python.org \
  --name python-docs \
  --preset comprehensive \
  --enhance-level 3 \
  --output ./output/python-claude-api

# Should use API mode automatically (detected from env var)
```

## Test 5: Package for Kimi

```bash
# Package a skill for Kimi
skill-seekers package ./output/react-kimi \
  --target kimi \
  --output ./output/react-kimi-package.zip

# Verify package
unzip -l ./output/react-kimi-package.zip
```

## Test 6: Package for Claude

```bash
# Package a skill for Claude
skill-seekers package ./output/react-claude \
  --target claude \
  --output ./output/react-claude-package.zip

# Verify package
unzip -l ./output/react-claude-package.zip
```

## Test 7: Unified Config with Multi-Agent

```bash
# Create a unified config
skill-seekers unified --config configs/claude-code-unified.json \
  --agent kimi \
  --enhance-level 3

# Or with Claude
skill-seekers unified --config configs/claude-code-unified.json \
  --agent claude \
  --enhance-level 3
```

## Test 8: Custom Agent

```bash
# Set custom agent command
export SKILL_SEEKER_AGENT=custom
export SKILL_SEEKER_AGENT_CMD="my-custom-agent {prompt_file} --some-flag"

# Use custom agent
skill-seekers create ./my-project \
  --name my-project-skill \
  --agent custom
```

## Test 9: Auto-Detection Verification

```bash
# Test 1: No API keys set - should default to LOCAL mode
unset ANTHROPIC_API_KEY MOONSHOT_API_KEY GOOGLE_API_KEY OPENAI_API_KEY
skill-seekers create ./test-project --name test
# Expected: Uses LOCAL mode with agent from SKILL_SEEKER_AGENT or default

# Test 2: Only MOONSHOT_API_KEY set - should use Kimi API mode
export MOONSHOT_API_KEY=sk-test
skill-seekers create ./test-project --name test
# Expected: Uses API mode with Kimi

# Test 3: Only ANTHROPIC_API_KEY set - should use Claude API mode
unset MOONSHOT_API_KEY
export ANTHROPIC_API_KEY=sk-test
skill-seekers create ./test-project --name test
# Expected: Uses API mode with Claude
```

## Test 10: AgentClient Direct Usage

```python
from skill_seekers.cli.agent_client import AgentClient

# Test with Kimi
client = AgentClient(mode='local', agent='kimi')
print(f"Agent: {client.agent}")
print(f"Display: {client.agent_display}")
print(f"Mode: {client.mode}")

# Test with Claude
client = AgentClient(mode='local', agent='claude')
print(f"Agent: {client.agent}")
print(f"Display: {client.agent_display}")
print(f"Mode: {client.mode}")

# Test API mode with Kimi
import os
os.environ['MOONSHOT_API_KEY'] = 'sk-test'
client = AgentClient(mode='auto')
print(f"Detected provider: {client.provider}")
print(f"Mode: {client.mode}")
print(f"Model: {client.get_model()}")
```

## Verification Checklist

- [ ] Kimi agent works in LOCAL mode
- [ ] Claude agent works in LOCAL mode
- [ ] Kimi API mode works with MOONSHOT_API_KEY
- [ ] Claude API mode works with ANTHROPIC_API_KEY
- [ ] Auto-detection works correctly
- [ ] Package for Kimi creates correct format
- [ ] Package for Claude creates correct format
- [ ] Unified command works with both agents
- [ ] Custom agent works with SKILL_SEEKER_AGENT_CMD
- [ ] All help text is agent-neutral
- [ ] No hardcoded "claude" defaults
