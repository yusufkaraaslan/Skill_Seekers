"""
Test fixtures for agent testing.
"""

# Valid minimal agent
VALID_MINIMAL_AGENT = """---
name: minimal-agent
description: Minimal valid agent for testing purposes
tools:
  - read_file
model: claude-3-5-sonnet-20241022
delegates_to: []
version: 1.0
---

# Minimal Agent

A minimal valid agent.
"""

# Valid agent with delegation
VALID_DELEGATING_AGENT = """---
name: delegating-agent
description: Agent that delegates to other agents for specialized tasks
tools:
  - replace_string_in_file
model: claude-3-5-sonnet-20241022
delegates_to: [code-analyzer]
version: 1.0
---

# Delegating Agent

Delegates code analysis to code-analyzer agent.

## Usage

Use when you need to modify code based on analysis results.
"""

# Invalid agent - missing required fields
INVALID_MISSING_FIELDS = """---
name: broken-agent
# Missing: description, tools, model
---

# Broken Agent
"""

# Invalid agent - short description
INVALID_SHORT_DESCRIPTION = """---
name: short-agent
description: Bad
tools: [read_file]
model: claude-3-5-sonnet-20241022
delegates_to: []
version: 1.0
---

# Short Agent
"""

# Invalid agent - non-existent tool
INVALID_BAD_TOOL = """---
name: bad-tool-agent
description: Agent with non-existent tool reference
tools:
  - read_file
  - nonexistent_magic_tool
model: claude-3-5-sonnet-20241022
delegates_to: []
version: 1.0
---

# Bad Tool Agent
"""

# Security risk agent
SECURITY_RISK_AGENT = """---
name: risky-agent
description: Agent with potential security issues in examples
tools:
  - run_in_terminal
model: claude-3-5-sonnet-20241022
delegates_to: []
version: 1.0
---

# Risky Agent

## Examples

**Dangerous Example:**
```bash
rm -rf /
```
"""

# Sample registry data
SAMPLE_REGISTRY = {
    "agents": [
        {
            "name": "test-agent-1",
            "version": "1.0",
            "created": "2025-01-15T10:00:00Z",
            "last_modified": "2025-01-15T10:00:00Z",
            "usage_count": 5,
            "delegates_to": []
        },
        {
            "name": "test-agent-2",
            "version": "1.2",
            "created": "2025-01-14T09:00:00Z",
            "last_modified": "2025-01-15T11:30:00Z",
            "usage_count": 12,
            "delegates_to": ["test-agent-1"]
        }
    ],
    "last_updated": "2025-01-15T11:30:00Z"
}
