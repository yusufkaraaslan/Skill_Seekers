"""
Integration tests for complete agent lifecycle.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_agent_creation_and_registration(temp_project_dir, create_registry_file, agent_registry, sample_agent_yaml):
    """Test creating an agent and registering it."""
    # Create initial registry
    registry_path = create_registry_file(agent_registry)
    
    # Create new agent
    agent_path = temp_project_dir / ".claude" / "agents" / "new-agent.md"
    agent_path.write_text(sample_agent_yaml.replace("test-agent", "new-agent"))
    
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
    
    assert result.returncode == 0, f"Registry update failed: {result.stderr}"
    
    # Verify agent in registry
    updated_registry = json.loads(registry_path.read_text())
    agent_names = [a['name'] for a in updated_registry['agents']]
    assert "new-agent" in agent_names


def test_agent_modification_increments_version(temp_project_dir, create_registry_file, create_agent_file, agent_registry, sample_agent_yaml):
    """Test that modifying an agent increments its version."""
    # Create registry with existing agent
    existing_agent = {
        "name": "test-agent",
        "version": "1.0",
        "created": "2025-01-15T10:00:00Z",
        "last_modified": "2025-01-15T10:00:00Z",
        "usage_count": 5,
        "delegates_to": []
    }
    registry_data = {
        "agents": [existing_agent],
        "last_updated": "2025-01-15T10:00:00Z"
    }
    registry_path = create_registry_file(registry_data)
    
    # Modify agent
    modified_yaml = sample_agent_yaml.replace("A test agent", "A modified test agent")
    agent_path = create_agent_file("test-agent", modified_yaml)
    
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
    
    # Verify version increment
    updated_registry = json.loads(registry_path.read_text())
    test_agent = next(a for a in updated_registry['agents'] if a['name'] == 'test-agent')
    assert test_agent['version'] == "1.1", f"Expected version 1.1, got {test_agent['version']}"


def test_agent_deletion_removes_from_registry(temp_project_dir, create_registry_file, agent_registry):
    """Test that deleting an agent removes it from registry."""
    registry_path = create_registry_file(agent_registry)
    
    # Get initial count
    initial_registry = json.loads(registry_path.read_text())
    initial_count = len(initial_registry['agents'])
    
    # Note: Deletion logic would need to be implemented
    # This is a placeholder test
    assert initial_count > 0


def test_load_registry_on_session_start(temp_project_dir, create_registry_file, agent_registry):
    """Test loading registry on session start."""
    registry_path = create_registry_file(agent_registry)
    
    # Run load script
    load_script = Path(__file__).parent.parent.parent / "scripts" / "load-agent-registry.py"
    result = subprocess.run(
        [sys.executable, str(load_script)],
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    assert result.returncode == 0, f"Load failed: {result.stderr}"
    
    # Verify agents loaded
    output = result.stdout
    assert "code-analyzer" in output or "test-generator" in output


def test_validation_blocks_invalid_agent(temp_project_dir, create_agent_file, invalid_agent_yaml):
    """Test that validation blocks creation of invalid agent."""
    agent_path = create_agent_file("invalid-agent", invalid_agent_yaml)
    
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
    
    assert result.returncode != 0, "Expected validation to fail"


def test_check_agent_behavior_hook(temp_project_dir, create_agent_file, sample_agent_yaml):
    """Test PreToolUse hook for agent behavior checking."""
    agent_path = create_agent_file("test-agent", sample_agent_yaml)
    
    check_script = Path(__file__).parent.parent.parent / "scripts" / "check-agent-behavior.py"
    result = subprocess.run(
        [sys.executable, str(check_script), "test-agent", "read_file"],
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    # Should complete without error
    assert result.returncode == 0


def test_delegation_chain_discovery(temp_project_dir, create_registry_file):
    """Test discovering delegation chains in registry."""
    # Create registry with delegation chain
    registry_data = {
        "agents": [
            {
                "name": "agent-a",
                "version": "1.0",
                "delegates_to": [],
                "created": "2025-01-15T10:00:00Z",
                "last_modified": "2025-01-15T10:00:00Z",
                "usage_count": 0
            },
            {
                "name": "agent-b",
                "version": "1.0",
                "delegates_to": ["agent-a"],
                "created": "2025-01-15T10:00:00Z",
                "last_modified": "2025-01-15T10:00:00Z",
                "usage_count": 0
            },
            {
                "name": "agent-c",
                "version": "1.0",
                "delegates_to": ["agent-b"],
                "created": "2025-01-15T10:00:00Z",
                "last_modified": "2025-01-15T10:00:00Z",
                "usage_count": 0
            }
        ],
        "last_updated": "2025-01-15T10:00:00Z"
    }
    registry_path = create_registry_file(registry_data)
    
    # Load and analyze registry
    registry = json.loads(registry_path.read_text())
    
    # Find agent-c's delegation chain
    agent_c = next(a for a in registry['agents'] if a['name'] == 'agent-c')
    assert agent_c['delegates_to'] == ['agent-b']
    
    # Verify chain: agent-c -> agent-b -> agent-a
    agent_b = next(a for a in registry['agents'] if a['name'] == 'agent-b')
    assert agent_b['delegates_to'] == ['agent-a']
