#!/usr/bin/env python3
"""
PostToolUse Hook: Update Agent Registry

Runs after successful agent creation/edit to update the agent registry.
Maintains agent_registry.json with full history and metadata.
"""

import json
import sys
import os
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

def is_agent_file(file_path: str) -> bool:
    """Check if file is an agent definition."""
    return file_path.endswith(".md") and "/.claude/agents/" in file_path

def extract_agent_metadata(file_path: str) -> Dict[str, Any]:
    """Extract agent metadata from file."""
    with open(file_path) as f:
        content = f.read()
    
    # Extract YAML frontmatter
    if not content.startswith("---"):
        raise ValueError("Invalid agent file format")
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Invalid YAML frontmatter")
    
    frontmatter = yaml.safe_load(parts[1])
    
    return {
        "name": frontmatter.get("name", "unknown"),
        "file_path": file_path,
        "type": frontmatter.get("type", "unknown"),
        "description": frontmatter.get("description", ""),
        "tools": frontmatter.get("tools", []),
        "delegates_to": frontmatter.get("delegates_to", []),
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }

def load_registry(registry_path: Path) -> Dict[str, Any]:
    """Load existing registry or create new one."""
    if not registry_path.exists():
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        return {
            "version": "1.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "agents": []
        }
    
    with open(registry_path) as f:
        return json.load(f)

def update_registry(registry: Dict[str, Any], agent_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Update registry with new/updated agent."""
    agents = registry.get("agents", [])
    agent_name = agent_metadata["name"]
    
    # Check if agent already exists
    existing_idx = None
    for i, agent in enumerate(agents):
        if agent.get("name") == agent_name:
            existing_idx = i
            break
    
    if existing_idx is not None:
        # Update existing agent
        old_agent = agents[existing_idx]
        
        # Preserve creation time and version - handle both old and new field names
        created_time = old_agent.get("created_at") or old_agent.get("created", agent_metadata["updated_at"])
        agent_metadata["created_at"] = created_time
        
        # Increment version
        old_version = old_agent.get("version", "1.0")
        try:
            major, minor = old_version.split(".")
            new_version = f"{major}.{int(minor) + 1}"
        except:
            new_version = "1.1"
        agent_metadata["version"] = new_version
        
        # Preserve usage stats - handle both old and new formats
        if "usage_stats" in old_agent:
            agent_metadata["usage_stats"] = old_agent["usage_stats"]
        elif "usage_count" in old_agent:
            # Convert old format to new format
            agent_metadata["usage_stats"] = {
                "invocation_count": old_agent["usage_count"],
                "success_rate": 1.0
            }
        else:
            # No stats yet
            agent_metadata["usage_stats"] = {
                "invocation_count": 0,
                "success_rate": 1.0
            }
        
        agents[existing_idx] = agent_metadata
    else:
        # New agent
        agent_metadata["created_at"] = agent_metadata["updated_at"]
        agent_metadata["version"] = "1.0"
        agent_metadata["usage_stats"] = {
            "invocation_count": 0,
            "success_rate": 1.0
        }
        agents.append(agent_metadata)
    
    registry["agents"] = agents
    registry["generated_at"] = datetime.utcnow().isoformat() + "Z"
    
    return registry

def save_registry(registry_path: Path, registry: Dict[str, Any]) -> None:
    """Save registry to file."""
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)

def main():
    """Main entry point for registry update hook."""
    try:
        # Read hook input
        input_data = json.load(sys.stdin)
        
        tool_input = input_data.get("tool_input", {})
        file_path = tool_input.get("file_path", "")
        
        # Only process agent files
        if not is_agent_file(file_path):
            sys.exit(0)  # Not an agent file - skip
        
        # Check if file actually exists (might have been deleted)
        if not os.path.exists(file_path):
            sys.exit(0)
        
        # Get registry path
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
        registry_path = Path(project_dir) / ".claude" / "skills" / "agent-scaffolding-toolkit" / "assets" / "agent_registry.json"
        
        # Extract agent metadata
        agent_metadata = extract_agent_metadata(file_path)
        
        # Load registry
        registry = load_registry(registry_path)
        
        # Update registry
        registry = update_registry(registry, agent_metadata)
        
        # Save registry
        save_registry(registry_path, registry)
        
        print(f"✅ Registry updated: {agent_metadata['name']} (v{agent_metadata['version']})", file=sys.stderr)
        sys.exit(0)
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(0)  # Don't block on hook errors
    except Exception as e:
        print(f"Registry update error: {e}", file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()
