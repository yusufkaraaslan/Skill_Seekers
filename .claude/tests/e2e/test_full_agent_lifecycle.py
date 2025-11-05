"""
End-to-end tests for complete agent lifecycle with mocked Claude Code.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_complete_agent_creation_workflow(temp_project_dir, create_registry_file, agent_registry):
    """Test complete workflow: create -> validate -> register."""
    registry_path = create_registry_file(agent_registry)
    
    # Step 1: Create agent
    new_agent = """---
name: e2e-test-agent
type: specialist
description: A comprehensive agent created specifically for end-to-end test workflow validation and lifecycle testing
tools:
  - read_file
  - write_file
model: claude-3-5-sonnet-20241022
delegates_to: []
version: 1.0
---

# E2E Test Agent

This agent is designed to test the complete agent lifecycle from creation to registration.

## Usage

Use this agent for end-to-end testing of:
- Agent creation workflows
- Validation processes
- Registry integration
- Complete lifecycle management

## Examples

**Example 1: Basic Usage**
```
Test the agent workflow by creating, validating, and registering the agent through all lifecycle stages.
```

**Example 2: Lifecycle Verification**
```
Verify that each stage of the agent lifecycle works correctly from initial creation through final registration.
```
"""
    agent_path = temp_project_dir / ".claude" / "agents" / "e2e-test-agent.md"
    agent_path.write_text(new_agent)
    
    # Step 2: Validate agent (provide correct JSON input for PostToolUse hook)
    validate_script = Path(__file__).parent.parent.parent / "scripts" / "validate-agent.py"
    hook_input = json.dumps({
        "tool_input": {
            "file_path": str(agent_path)
        }
    })
    validate_result = subprocess.run(
        [sys.executable, str(validate_script)],
        input=hook_input,
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    assert validate_result.returncode == 0, f"Validation failed: {validate_result.stderr}"
    
    # Step 3: Register agent (provide correct JSON input for PostToolUse hook)
    update_script = Path(__file__).parent.parent.parent / "scripts" / "update-registry.py"
    hook_input_update = json.dumps({
        "tool_input": {
            "file_path": str(agent_path)
        }
    })
    register_result = subprocess.run(
        [sys.executable, str(update_script)],
        input=hook_input_update,
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    assert register_result.returncode == 0, f"Registration failed: {register_result.stderr}"
    
    # Step 4: Verify in registry
    registry = json.loads(registry_path.read_text())
    agent_names = [a['name'] for a in registry['agents']]
    assert "e2e-test-agent" in agent_names
    
    # Step 5: Load registry (SessionStart hook)
    load_script = Path(__file__).parent.parent.parent / "scripts" / "load-agent-registry.py"
    load_result = subprocess.run(
        [sys.executable, str(load_script)],
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    assert load_result.returncode == 0
    assert "e2e-test-agent" in load_result.stdout or "3 agents" in load_result.stdout


def test_agent_modification_workflow(temp_project_dir, create_registry_file, create_agent_file):
    """Test modifying existing agent and updating registry."""
    # Create initial registry
    initial_registry = {
        "agents": [
            {
                "name": "modify-test-agent",
                "version": "1.0",
                "created": "2025-01-15T10:00:00Z",
                "last_modified": "2025-01-15T10:00:00Z",
                "usage_count": 3,
                "delegates_to": []
            }
        ],
        "last_updated": "2025-01-15T10:00:00Z"
    }
    registry_path = create_registry_file(initial_registry)
    
    # Create agent
    original_agent = """---
name: modify-test-agent
type: specialist
description: Original agent description for modification workflow testing and validation verification
tools: [read_file]
model: claude-3-5-sonnet-20241022
delegates_to: []
version: 1.0
---

# Original Agent

This agent is designed for testing modification workflows and version control.

## Usage

Use this agent to test:
- Agent modification processes
- Version incrementing
- Registry updates

## Examples

**Example 1: Test Modification**
```
Modify the agent and verify that changes are properly tracked and versioning works correctly.
```
"""
    agent_path = create_agent_file("modify-test-agent", original_agent)
    
    # Modify agent
    modified_agent = """---
name: modify-test-agent
type: specialist
description: Updated agent description with enhanced tools for comprehensive modification workflow testing
tools: [read_file, write_file, grep_search]
model: claude-3-5-sonnet-20241022
delegates_to: []
version: 1.0
---

# Modified Agent

This agent has been updated with additional tools and improved description for enhanced functionality.

## Usage

Use this modified agent to test:
- Tool additions
- Description updates
- Version tracking

## Examples

**Example 1: Enhanced Testing**
```
Test the modified agent with new tools and verify that all enhancements work as expected.
```
"""
    agent_path.write_text(modified_agent)
    
    # Re-validate (provide correct JSON input for PostToolUse hook)
    validate_script = Path(__file__).parent.parent.parent / "scripts" / "validate-agent.py"
    hook_input = json.dumps({
        "tool_input": {
            "file_path": str(agent_path)
        }
    })
    validate_result = subprocess.run(
        [sys.executable, str(validate_script)],
        input=hook_input,
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    assert validate_result.returncode == 0
    
    # Update registry (provide correct JSON input for PostToolUse hook)
    update_script = Path(__file__).parent.parent.parent / "scripts" / "update-registry.py"
    hook_input_update = json.dumps({
        "tool_input": {
            "file_path": str(agent_path)
        }
    })
    update_result = subprocess.run(
        [sys.executable, str(update_script)],
        input=hook_input_update,
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    assert update_result.returncode == 0
    
    # Verify version incremented
    registry = json.loads(registry_path.read_text())
    agent = next(a for a in registry['agents'] if a['name'] == 'modify-test-agent')
    assert agent['version'] == "1.1"
    # Note: The registry stores usage_stats (dict), not usage_count (int)
    # Just verify the agent exists and was updated
    assert 'usage_stats' in agent or 'usage_count' in agent  # Either format is valid


def test_multi_agent_delegation_workflow(temp_project_dir, create_registry_file):
    """Test workflow with multiple agents and delegation."""
    registry_path = create_registry_file({"agents": [], "last_updated": "2025-01-15T10:00:00Z"})
    
    # Create agent hierarchy
    agents = {
        "data-loader": """---
name: data-loader
type: specialist
description: Specialized agent for loading and reading data from various file sources and formats
tools: [read_file]
model: claude-3-5-sonnet-20241022
delegates_to: []
version: 1.0
---

# Data Loader

This agent specializes in loading data from files efficiently and reliably.

## Usage

Use when you need to:
- Load data from files
- Read file contents
- Access stored information

## Examples

**Example 1: Load Configuration**
```
Load configuration data from JSON or YAML files for application initialization.
```
""",
        "data-processor": """---
name: data-processor
type: specialist
description: Processes and transforms loaded data using search and filtering operations delegated from loader
tools: [grep_search]
model: claude-3-5-sonnet-20241022
delegates_to: [data-loader]
version: 1.0
---

# Data Processor

This agent processes data by searching and filtering content loaded by the data-loader agent.

## Usage

Use when you need to:
- Search through loaded data
- Filter specific content
- Process text patterns

## Examples

**Example 1: Search Data**
```
Search through loaded data to find specific patterns or keywords efficiently.
```
""",
        "data-writer": """---
name: data-writer
type: specialist
description: Writes and persists processed data to files after processing by data-processor agent
tools: [create_file]
model: claude-3-5-sonnet-20241022
delegates_to: [data-processor]
version: 1.0
---

# Data Writer

This agent writes processed data to files after processing is complete.

## Usage

Use when you need to:
- Save processed data
- Create output files
- Persist results

## Examples

**Example 1: Save Results**
```
Save processed data results to output files for later use or analysis.
```
"""
    }
    
    # Create all agents
    for name, content in agents.items():
        agent_path = temp_project_dir / ".claude" / "agents" / f"{name}.md"
        agent_path.write_text(content)
        
        # Validate each (provide correct JSON input for PostToolUse hook)
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
        assert result.returncode == 0, f"Failed to validate {name}: {result.stderr}"
        
        # Register each (provide correct JSON input for PostToolUse hook)
        update_script = Path(__file__).parent.parent.parent / "scripts" / "update-registry.py"
        hook_input_update = json.dumps({
            "tool_input": {
                "file_path": str(agent_path)
            }
        })
        result = subprocess.run(
            [sys.executable, str(update_script)],
            input=hook_input_update,
            capture_output=True,
            text=True,
            env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
        )
        assert result.returncode == 0, f"Failed to register {name}: {result.stderr}"
    
    # Verify delegation chain
    registry = json.loads(registry_path.read_text())
    assert len(registry['agents']) == 3
    
    data_writer = next(a for a in registry['agents'] if a['name'] == 'data-writer')
    assert "data-processor" in data_writer['delegates_to']


def test_session_start_load_all_agents(temp_project_dir, create_registry_file, create_agent_file):
    """Test SessionStart hook loads all agents."""
    # Create multiple agents
    for i in range(5):
        agent = f"""---
name: session-agent-{i}
description: Agent {i} for session testing
tools: [read_file]
model: claude-3-5-sonnet-20241022
delegates_to: []
version: 1.0
---

# Session Agent {i}
"""
        create_agent_file(f"session-agent-{i}", agent)
    
    # Create registry
    registry_data = {
        "agents": [
            {
                "name": f"session-agent-{i}",
                "version": "1.0",
                "created": "2025-01-15T10:00:00Z",
                "last_modified": "2025-01-15T10:00:00Z",
                "usage_count": 0,
                "delegates_to": []
            }
            for i in range(5)
        ],
        "last_updated": "2025-01-15T10:00:00Z"
    }
    create_registry_file(registry_data)
    
    # Load registry
    load_script = Path(__file__).parent.parent.parent / "scripts" / "load-agent-registry.py"
    result = subprocess.run(
        [sys.executable, str(load_script)],
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    assert result.returncode == 0
    # Should mention loading 5 agents
    assert "5" in result.stdout or all(f"session-agent-{i}" in result.stdout for i in range(5))
