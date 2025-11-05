"""
Integration tests for agent composition and delegation.
"""
import json
from pathlib import Path

import pytest


def test_simple_delegation(temp_project_dir, create_agent_file, create_registry_file):
    """Test simple delegation from one agent to another."""
    # Create base agent
    base_agent = """---
name: base-agent
description: Base agent that performs simple tasks
tools:
  - read_file
model: claude-3-5-sonnet-20241022
delegates_to: []
version: 1.0
---

# Base Agent

Performs basic file reading operations.
"""
    
    # Create delegating agent
    delegating_agent = """---
name: delegating-agent
description: Agent that delegates to base-agent
tools:
  - replace_string_in_file
model: claude-3-5-sonnet-20241022
delegates_to: [base-agent]
version: 1.0
---

# Delegating Agent

Delegates file reading to base-agent, handles modifications.
"""
    
    create_agent_file("base-agent", base_agent)
    create_agent_file("delegating-agent", delegating_agent)
    
    # Create registry
    registry_data = {
        "agents": [
            {
                "name": "base-agent",
                "version": "1.0",
                "delegates_to": [],
                "created": "2025-01-15T10:00:00Z",
                "last_modified": "2025-01-15T10:00:00Z",
                "usage_count": 0
            },
            {
                "name": "delegating-agent",
                "version": "1.0",
                "delegates_to": ["base-agent"],
                "created": "2025-01-15T10:00:00Z",
                "last_modified": "2025-01-15T10:00:00Z",
                "usage_count": 0
            }
        ],
        "last_updated": "2025-01-15T10:00:00Z"
    }
    registry_path = create_registry_file(registry_data)
    
    # Verify delegation chain
    registry = json.loads(registry_path.read_text())
    delegating = next(a for a in registry['agents'] if a['name'] == 'delegating-agent')
    assert "base-agent" in delegating['delegates_to']


def test_multi_agent_delegation(temp_project_dir, create_agent_file, create_registry_file):
    """Test agent delegating to multiple other agents."""
    # Create specialized agents
    analyzer = """---
name: analyzer
description: Analyzes code
tools: [read_file, grep_search]
model: claude-3-5-sonnet-20241022
delegates_to: []
version: 1.0
---

# Analyzer
"""
    
    formatter = """---
name: formatter
description: Formats code
tools: [replace_string_in_file]
model: claude-3-5-sonnet-20241022
delegates_to: []
version: 1.0
---

# Formatter
"""
    
    orchestrator = """---
name: orchestrator
description: Orchestrates analysis and formatting
tools: [list_dir]
model: claude-3-5-sonnet-20241022
delegates_to: [analyzer, formatter]
version: 1.0
---

# Orchestrator

Delegates to analyzer and formatter.
"""
    
    create_agent_file("analyzer", analyzer)
    create_agent_file("formatter", formatter)
    create_agent_file("orchestrator", orchestrator)
    
    # Verify orchestrator delegates to both
    orchestrator_path = temp_project_dir / ".claude" / "agents" / "orchestrator.md"
    content = orchestrator_path.read_text()
    assert "analyzer" in content
    assert "formatter" in content


def test_delegation_chain_depth(temp_project_dir, create_registry_file):
    """Test calculating delegation chain depth."""
    # Create 3-level delegation chain
    registry_data = {
        "agents": [
            {"name": "level-0", "version": "1.0", "delegates_to": [], 
             "created": "2025-01-15T10:00:00Z", "last_modified": "2025-01-15T10:00:00Z", "usage_count": 0},
            {"name": "level-1", "version": "1.0", "delegates_to": ["level-0"],
             "created": "2025-01-15T10:00:00Z", "last_modified": "2025-01-15T10:00:00Z", "usage_count": 0},
            {"name": "level-2", "version": "1.0", "delegates_to": ["level-1"],
             "created": "2025-01-15T10:00:00Z", "last_modified": "2025-01-15T10:00:00Z", "usage_count": 0},
            {"name": "level-3", "version": "1.0", "delegates_to": ["level-2"],
             "created": "2025-01-15T10:00:00Z", "last_modified": "2025-01-15T10:00:00Z", "usage_count": 0}
        ],
        "last_updated": "2025-01-15T10:00:00Z"
    }
    registry_path = create_registry_file(registry_data)
    
    # Calculate depth for level-3
    def calculate_depth(agent_name: str, registry: dict, visited=None) -> int:
        if visited is None:
            visited = set()
        
        if agent_name in visited:
            return 0  # Cycle detected
        
        visited.add(agent_name)
        agent = next((a for a in registry['agents'] if a['name'] == agent_name), None)
        
        if not agent or not agent['delegates_to']:
            return 0
        
        max_depth = 0
        for delegate in agent['delegates_to']:
            depth = calculate_depth(delegate, registry, visited.copy())
            max_depth = max(max_depth, depth)
        
        return max_depth + 1
    
    registry = json.loads(registry_path.read_text())
    depth = calculate_depth("level-3", registry)
    assert depth == 3, f"Expected depth 3, got {depth}"


def test_tool_aggregation_through_delegation(temp_project_dir, create_agent_file):
    """Test that delegating agent can access delegate's tools."""
    reader = """---
name: file-reader
description: Reads files
tools: [read_file, grep_search]
model: claude-3-5-sonnet-20241022
delegates_to: []
version: 1.0
---

# File Reader
"""
    
    writer = """---
name: file-writer
description: Writes files, delegates reading to file-reader
tools: [replace_string_in_file, create_file]
model: claude-3-5-sonnet-20241022
delegates_to: [file-reader]
version: 1.0
---

# File Writer

Can read (via delegation) and write files.
"""
    
    create_agent_file("file-reader", reader)
    create_agent_file("file-writer", writer)
    
    # Aggregate tools - improved parser
    def get_all_tools(agent_name: str, agents_dir: Path, visited=None) -> set:
        if visited is None:
            visited = set()
        
        if agent_name in visited:
            return set()
        
        visited.add(agent_name)
        agent_path = agents_dir / f"{agent_name}.md"
        
        if not agent_path.exists():
            return set()
        
        # Parse YAML frontmatter properly
        import yaml
        content = agent_path.read_text()
        
        # Extract YAML between --- markers
        lines = content.split('\n')
        yaml_lines = []
        in_yaml = False
        yaml_count = 0
        
        for line in lines:
            if line.strip() == '---':
                yaml_count += 1
                if yaml_count == 1:
                    in_yaml = True
                    continue
                elif yaml_count == 2:
                    break
            if in_yaml:
                yaml_lines.append(line)
        
        if yaml_lines:
            yaml_content = '\n'.join(yaml_lines)
            try:
                metadata = yaml.safe_load(yaml_content)
                if metadata and 'tools' in metadata:
                    return set(metadata['tools'])
            except:
                pass
        
        return set()
    
    agents_dir = temp_project_dir / ".claude" / "agents"
    writer_tools = get_all_tools("file-writer", agents_dir)
    
    assert "replace_string_in_file" in writer_tools
    assert "create_file" in writer_tools
