"""
Unit tests for registry management.
"""
import json
from pathlib import Path
import subprocess
import sys

import pytest


def test_registry_creation(temp_project_dir, create_registry_file):
    """Test creating a new registry."""
    registry_data = {
        "agents": [],
        "last_updated": "2025-01-15T10:00:00Z"
    }
    registry_path = create_registry_file(registry_data)
    
    assert registry_path.exists()
    
    loaded = json.loads(registry_path.read_text())
    assert "agents" in loaded
    assert "last_updated" in loaded
    assert len(loaded["agents"]) == 0


def test_add_agent_to_registry(temp_project_dir, create_registry_file, create_agent_file, sample_agent_yaml):
    """Test adding an agent to the registry."""
    registry_data = {
        "agents": [],
        "last_updated": "2025-01-15T10:00:00Z"
    }
    registry_path = create_registry_file(registry_data)
    
    # Create agent
    agent_path = create_agent_file("new-agent", sample_agent_yaml.replace("test-agent", "new-agent"))
    
    # Update registry
    update_script = Path(__file__).parent.parent.parent / "scripts" / "update-registry.py"
    hook_input = json.dumps({
        "tool_input": {
            "file_path": str(agent_path)
        }
    })
    result = subprocess.run(
        [sys.executable, str(update_script)],
        input=hook_input,
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    assert result.returncode == 0
    
    # Verify agent added
    registry = json.loads(registry_path.read_text())
    assert len(registry["agents"]) == 1
    assert registry["agents"][0]["name"] == "new-agent"
    assert registry["agents"][0]["version"] == "1.0"


def test_update_existing_agent_in_registry(temp_project_dir, create_registry_file, create_agent_file):
    """Test updating an existing agent in the registry."""
    registry_data = {
        "agents": [
            {
                "name": "existing-agent",
                "version": "1.0",
                "created": "2025-01-15T10:00:00Z",
                "last_modified": "2025-01-15T10:00:00Z",
                "usage_count": 10,
                "delegates_to": []
            }
        ],
        "last_updated": "2025-01-15T10:00:00Z"
    }
    registry_path = create_registry_file(registry_data)
    
    # Modify agent
    modified_agent = """---
name: existing-agent
description: Updated agent with new description
tools: [read_file, grep_search]
model: claude-3-5-sonnet-20241022
delegates_to: []
version: 1.0
---

# Existing Agent (Updated)
"""
    agent_path = create_agent_file("existing-agent", modified_agent)
    
    # Update registry
    update_script = Path(__file__).parent.parent.parent / "scripts" / "update-registry.py"
    hook_input = json.dumps({
        "tool_input": {
            "file_path": str(agent_path)
        }
    })
    result = subprocess.run(
        [sys.executable, str(update_script)],
        input=hook_input,
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    assert result.returncode == 0
    
    # Verify version incremented
    registry = json.loads(registry_path.read_text())
    assert len(registry["agents"]) == 1
    agent = registry["agents"][0]
    assert agent["name"] == "existing-agent"
    assert agent["version"] == "1.1"
    # Handle both usage_count and usage_stats formats
    if "usage_count" in agent:
        assert agent["usage_count"] == 10  # Preserved
    elif "usage_stats" in agent:
        assert agent["usage_stats"]["invocation_count"] == 10  # Preserved


def test_registry_preserves_usage_stats(temp_project_dir, create_registry_file, create_agent_file):
    """Test that registry updates preserve usage statistics."""
    registry_data = {
        "agents": [
            {
                "name": "stats-agent",
                "version": "1.0",
                "created": "2025-01-10T10:00:00Z",
                "last_modified": "2025-01-12T10:00:00Z",
                "usage_count": 42,
                "delegates_to": ["other-agent"]
            }
        ],
        "last_updated": "2025-01-12T10:00:00Z"
    }
    registry_path = create_registry_file(registry_data)
    
    # Update agent
    updated_agent = """---
name: stats-agent
description: Agent with updated description to test stats preservation
tools: [read_file]
model: claude-3-5-sonnet-20241022
delegates_to: [other-agent]
version: 1.0
---

# Stats Agent
"""
    agent_path = create_agent_file("stats-agent", updated_agent)
    
    update_script = Path(__file__).parent.parent.parent / "scripts" / "update-registry.py"
    hook_input = json.dumps({
        "tool_input": {
            "file_path": str(agent_path)
        }
    })
    result = subprocess.run(
        [sys.executable, str(update_script)],
        input=hook_input,
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    assert result.returncode == 0
    
    registry = json.loads(registry_path.read_text())
    agent = registry["agents"][0]
    # Handle both usage_count and usage_stats formats
    if "usage_count" in agent:
        assert agent["usage_count"] == 42  # Preserved
    elif "usage_stats" in agent:
        assert agent["usage_stats"]["invocation_count"] == 42  # Preserved
    # Handle both old and new field names for creation time
    created_time = agent.get("created_at") or agent.get("created")
    assert created_time == "2025-01-10T10:00:00Z"  # Preserved


def test_delegation_tracking_in_registry(temp_project_dir, create_registry_file, create_agent_file):
    """Test that delegation relationships are tracked in registry."""
    registry_data = {
        "agents": [],
        "last_updated": "2025-01-15T10:00:00Z"
    }
    registry_path = create_registry_file(registry_data)
    
    # Create agents with delegation
    base_agent = """---
name: base
description: Base agent with no dependencies
tools: [read_file]
model: claude-3-5-sonnet-20241022
delegates_to: []
version: 1.0
---

# Base
"""
    
    derived_agent = """---
name: derived
description: Derived agent that delegates to base
tools: [grep_search]
model: claude-3-5-sonnet-20241022
delegates_to: [base]
version: 1.0
---

# Derived
"""
    
    # Add base first
    base_path = create_agent_file("base", base_agent)
    update_script = Path(__file__).parent.parent.parent / "scripts" / "update-registry.py"
    hook_input_base = json.dumps({
        "tool_input": {
            "file_path": str(base_path)
        }
    })
    subprocess.run(
        [sys.executable, str(update_script)],
        input=hook_input_base,
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    # Add derived
    derived_path = create_agent_file("derived", derived_agent)
    hook_input_derived = json.dumps({
        "tool_input": {
            "file_path": str(derived_path)
        }
    })
    subprocess.run(
        [sys.executable, str(update_script)],
        input=hook_input_derived,
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    # Verify delegation tracked
    registry = json.loads(registry_path.read_text())
    derived = next(a for a in registry["agents"] if a["name"] == "derived")
    assert "base" in derived["delegates_to"]
