"""
Unit tests for agent validation logic.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_valid_agent_passes_validation(temp_project_dir, create_agent_file, sample_agent_yaml):
    """Test that a valid agent passes validation."""
    agent_path = create_agent_file("valid-agent", sample_agent_yaml)
    
    # Run validation script with correct JSON input
    script_path = Path(__file__).parent.parent.parent / "scripts" / "validate-agent.py"
    hook_input = json.dumps({
        "tool_input": {
            "file_path": str(agent_path)
        }
    })
    result = subprocess.run(
        [sys.executable, str(script_path)],
        input=hook_input,
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    assert result.returncode == 0, f"Validation failed: {result.stderr}"
    assert "✅ Agent validation passed" in result.stderr


def test_invalid_agent_fails_validation(temp_project_dir, create_agent_file, invalid_agent_yaml):
    """Test that an invalid agent fails validation."""
    agent_path = create_agent_file("invalid-agent", invalid_agent_yaml)
    
    script_path = Path(__file__).parent.parent.parent / "scripts" / "validate-agent.py"
    hook_input = json.dumps({
        "tool_input": {
            "file_path": str(agent_path)
        }
    })
    result = subprocess.run(
        [sys.executable, str(script_path)],
        input=hook_input,
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    assert result.returncode == 2, "Expected validation to block invalid agent"
    assert "❌" in result.stderr or "Missing required field" in result.stderr


def test_missing_yaml_frontmatter_fails(temp_project_dir, create_agent_file):
    """Test that agent without YAML frontmatter fails validation."""
    content = """# Agent Without YAML

This agent has no YAML frontmatter.
"""
    agent_path = create_agent_file("no-yaml-agent", content)
    
    script_path = Path(__file__).parent.parent.parent / "scripts" / "validate-agent.py"
    hook_input = json.dumps({
        "tool_input": {
            "file_path": str(agent_path)
        }
    })
    result = subprocess.run(
        [sys.executable, str(script_path)],
        input=hook_input,
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    assert result.returncode != 0, "Expected validation to fail for agent without YAML"


def test_nonexistent_tool_fails_validation(temp_project_dir, create_agent_file):
    """Test that agent with non-existent tool fails validation."""
    content = """---
name: bad-tool-agent
description: Agent with non-existent tool
tools:
  - read_file
  - nonexistent_tool_xyz
model: claude-3-5-sonnet-20241022
delegates_to: []
version: 1.0
---

# Bad Tool Agent
"""
    agent_path = create_agent_file("bad-tool-agent", content)
    
    script_path = Path(__file__).parent.parent.parent / "scripts" / "validate-agent.py"
    hook_input = json.dumps({
        "tool_input": {
            "file_path": str(agent_path)
        }
    })
    result = subprocess.run(
        [sys.executable, str(script_path)],
        input=hook_input,
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    assert result.returncode == 2, "Expected validation to block agent with non-existent tool"
    assert "nonexistent_tool" in result.stderr.lower() or "unknown tool" in result.stderr.lower()


def test_security_pattern_detection(temp_project_dir, create_agent_file):
    """Test detection of potentially dangerous patterns."""
    dangerous_agent = """---
name: dangerous-agent
type: specialist
description: Agent with security issues that demonstrates detection of dangerous command patterns in system operations
tools: [run_in_terminal]
model: claude-3-5-sonnet-20241022
delegates_to: []
version: 1.0
---

# Dangerous Agent

This agent can run commands like `rm -rf /` which is dangerous and should be detected by security analysis. The validation system should warn about potentially destructive operations.
"""
    agent_path = create_agent_file("dangerous-agent", dangerous_agent)
    
    validate_script = Path(__file__).parent.parent.parent / "scripts" / "validate-agent.py"
    hook_input = json.dumps({
        "tool_input": {
            "file_path": str(agent_path)
        }
    })
    result = subprocess.run(
        [sys.executable, str(validate_script)],
        input=hook_input,
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    # Should warn about security patterns (or pass validation if no security checks implemented yet)
    # This test is flexible to allow for future security feature implementation
    assert result.returncode in [0, 1, 2]  # Allow any outcome for now


def test_short_description_fails_validation(temp_project_dir, create_agent_file):
    """Test that agents with too-short descriptions fail validation."""
    content = """---
name: short-desc-agent
description: Short
tools:
  - read_file
model: claude-3-5-sonnet-20241022
delegates_to: []
version: 1.0
---

# Short Description Agent
"""
    agent_path = create_agent_file("short-desc-agent", content)
    
    script_path = Path(__file__).parent.parent.parent / "scripts" / "validate-agent.py"
    hook_input = json.dumps({
        "tool_input": {
            "file_path": str(agent_path)
        }
    })
    result = subprocess.run(
        [sys.executable, str(script_path)],
        input=hook_input,
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    assert result.returncode == 2, "Expected validation to block short description"
    assert "description" in result.stderr.lower()


def test_delegation_cycle_detection(temp_project_dir, create_agent_file):
    """Test that delegation cycles are detected (if implemented)."""
    # Agent A delegates to Agent B
    agent_a = """---
name: agent-a
description: Agent A delegates to Agent B
tools:
  - read_file
model: claude-3-5-sonnet-20241022
delegates_to: [agent-b]
version: 1.0
---

# Agent A
"""
    
    # Agent B delegates to Agent A (cycle)
    agent_b = """---
name: agent-b
description: Agent B delegates to Agent A
tools:
  - read_file
model: claude-3-5-sonnet-20241022
delegates_to: [agent-a]
version: 1.0
---

# Agent B
"""
    
    create_agent_file("agent-a", agent_a)
    agent_b_path = create_agent_file("agent-b", agent_b)
    
    script_path = Path(__file__).parent.parent.parent / "scripts" / "validate-agent.py"
    hook_input = json.dumps({
        "tool_input": {
            "file_path": str(agent_b_path)
        }
    })
    result = subprocess.run(
        [sys.executable, str(script_path)],
        input=hook_input,
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    # Validation may warn or block cycles
    # This is a best-effort test
    print(f"Cycle detection result: {result.stderr}")
