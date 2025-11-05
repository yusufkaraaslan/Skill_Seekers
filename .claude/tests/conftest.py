"""
Pytest configuration and shared fixtures for agent scaffolding tests.
"""
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator

import pytest


@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """Create a temporary project directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        # Create .claude structure
        (project_dir / ".claude" / "agents").mkdir(parents=True)
        (project_dir / ".claude" / "scripts").mkdir(parents=True)
        (project_dir / ".claude" / "skills" / "agent-scaffolding-toolkit" / "assets").mkdir(parents=True)
        
        yield project_dir


@pytest.fixture
def sample_agent_yaml() -> str:
    """Valid agent YAML frontmatter."""
    return """---
name: test-agent
type: specialist
description: A comprehensive test agent designed specifically for validation testing purposes and workflow verification
tools:
  - read_file
  - write_file
model: claude-3-5-sonnet-20241022
delegates_to: []
version: 1.0
---

# Test Agent

This is a test agent designed for comprehensive validation testing.

## Usage

Use this agent when you need to:
- Test validation workflows
- Verify agent creation processes
- Ensure proper configuration

## Examples

**Example 1: Basic Test**
```
Test the agent functionality with sample inputs and verify correct behavior.
```

**Example 2: Validation Test**
```
Verify that all validation rules are properly enforced and working as expected.
```
"""


@pytest.fixture
def invalid_agent_yaml() -> str:
    """Invalid agent YAML (missing required fields)."""
    return """---
name: invalid-agent
# Missing: type, description (adequate length), tools
---

# Invalid Agent

This agent is missing required fields and will fail validation checks.
"""


@pytest.fixture
def agent_registry() -> Dict[str, Any]:
    """Sample agent registry structure."""
    return {
        "agents": [
            {
                "name": "code-analyzer",
                "version": "1.0",
                "created": "2025-01-15T10:00:00Z",
                "last_modified": "2025-01-15T10:00:00Z",
                "usage_count": 5,
                "delegates_to": []
            },
            {
                "name": "test-generator",
                "version": "1.0",
                "created": "2025-01-15T11:00:00Z",
                "last_modified": "2025-01-15T11:00:00Z",
                "usage_count": 3,
                "delegates_to": ["code-analyzer"]
            }
        ],
        "last_updated": "2025-01-15T11:00:00Z"
    }


@pytest.fixture
def mock_claude_project_dir(temp_project_dir: Path, monkeypatch) -> Path:
    """Mock CLAUDE_PROJECT_DIR environment variable."""
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(temp_project_dir))
    return temp_project_dir


@pytest.fixture
def create_agent_file(temp_project_dir: Path):
    """Factory fixture to create agent files."""
    def _create_agent(name: str, content: str) -> Path:
        agent_path = temp_project_dir / ".claude" / "agents" / f"{name}.md"
        agent_path.write_text(content)
        return agent_path
    return _create_agent


@pytest.fixture
def create_registry_file(temp_project_dir: Path):
    """Factory fixture to create registry file."""
    def _create_registry(data: Dict[str, Any]) -> Path:
        registry_path = (
            temp_project_dir / ".claude" / "skills" / 
            "agent-scaffolding-toolkit" / "assets" / "agent_registry.json"
        )
        registry_path.write_text(json.dumps(data, indent=2))
        return registry_path
    return _create_registry
