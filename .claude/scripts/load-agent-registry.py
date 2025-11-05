#!/usr/bin/env python3
"""
SessionStart Hook: Load Agent Registry

Runs at session start to inject available custom agents into Claude's context.
Reads agent_registry.json and outputs formatted markdown for Claude to consume.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

def load_registry():
    """Load agent registry from assets folder."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
    registry_path = Path(project_dir) / ".claude" / "skills" / "agent-scaffolding-toolkit" / "assets" / "agent_registry.json"
    
    if not registry_path.exists():
        # Registry doesn't exist yet - create empty one
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        default_registry = {
            "version": "1.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "agents": []
        }
        with open(registry_path, 'w') as f:
            json.dump(default_registry, f, indent=2)
        return default_registry
    
    with open(registry_path) as f:
        return json.load(f)

def format_agent_context(registry):
    """Format registry as markdown for Claude's session context."""
    agents = registry.get("agents", [])
    
    if not agents:
        return "No custom agents registered yet. Use the agent-scaffolding-toolkit skill to create one."
    
    context = f"""
## 🤖 Custom Agents Available ({len(agents)} total)

"""
    
    # Group agents by type
    by_type = {}
    for agent in agents:
        agent_type = agent.get("type", "unknown")
        by_type.setdefault(agent_type, []).append(agent)
    
    for agent_type, agents_list in sorted(by_type.items()):
        context += f"\n### {agent_type.title()} Agents\n\n"
        for agent in agents_list:
            name = agent.get("name", "unknown")
            description = agent.get("description", "No description")
            tools = agent.get("tools", [])
            delegates = agent.get("delegates_to", [])
            
            context += f"- **@{name}**: {description}\n"
            if tools:
                context += f"  - Tools: {', '.join(tools[:5])}"
                if len(tools) > 5:
                    context += f" (+{len(tools) - 5} more)"
                context += "\n"
            if delegates:
                context += f"  - Delegates to: {', '.join(f'@{d}' for d in delegates)}\n"
    
    context += f"\n\n*Registry last updated: {registry.get('generated_at', 'unknown')}*\n"
    
    return context

def main():
    """Main entry point for SessionStart hook."""
    try:
        # Read stdin (hook input from Claude Code)
        try:
            input_data = json.load(sys.stdin)
        except json.JSONDecodeError:
            # No input or invalid JSON - proceed anyway
            input_data = {}
        
        # Load registry
        registry = load_registry()
        
        # Generate context
        context = format_agent_context(registry)
        
        # Output to stdout (Claude will consume this)
        print(context)
        
        sys.exit(0)
        
    except Exception as e:
        print(f"Error loading agent registry: {e}", file=sys.stderr)
        sys.exit(0)  # Don't block session start

if __name__ == "__main__":
    main()
