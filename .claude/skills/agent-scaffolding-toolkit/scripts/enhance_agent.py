#!/usr/bin/env python3
"""
Agent Enhancement Tool
Enhances existing agents with new capabilities and improvements.
"""

import os
import sys
import argparse
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional

# Available enhancements
ENHANCEMENTS = {
    "add_tool": "Add a new Claude Code tool to the agent",
    "remove_tool": "Remove a tool from the agent",
    "change_model": "Change the agent's model (opus/sonnet/haiku)",
    "add_tag": "Add descriptive tags",
    "improve_prompt": "Enhance system prompt with best practices",
    "add_workflow": "Add specific workflow instructions",
    "add_constraints": "Add operational constraints and guardrails"
}

def parse_agent_file(file_path: str) -> tuple[Dict, str]:
    """Parse existing agent file"""
    with open(file_path, 'r') as f:
        content = f.read()

    if not content.startswith('---'):
        raise ValueError("Invalid agent file format")

    parts = content.split('---', 2)
    if len(parts) < 3:
        raise ValueError("Invalid agent file format")

    metadata = yaml.safe_load(parts[1])
    body = parts[2].strip()

    return metadata, body

def write_agent_file(file_path: str, metadata: Dict, body: str):
    """Write agent file with proper formatting"""
    yaml_content = ["---"]

    # Required fields first
    yaml_content.append(f"name: {metadata['name']}")
    yaml_content.append(f"description: {metadata['description']}")
    if 'model' in metadata:
        yaml_content.append(f"model: {metadata['model']}")

    yaml_content.append("tools:")
    for tool in sorted(metadata.get('tools', [])):
        yaml_content.append(f"  - {tool}")

    if metadata.get('tags'):
        yaml_content.append("tags:")
        for tag in sorted(metadata['tags']):
            yaml_content.append(f"  - {tag}")

    yaml_content.append("---")

    with open(file_path, 'w') as f:
        f.write('\n'.join(yaml_content) + '\n\n' + body)

def enhance_with_tool(metadata: Dict, body: str, tool: str, action: str = "add") -> tuple[Dict, str]:
    """Add or remove a tool from agent"""
    tools = set(metadata.get('tools', []))

    if action == "add" and tool not in tools:
        tools.add(tool)
        # Add tool usage to system prompt
        if "You have access to the following tools:" not in body:
            body += "\n\n#### Available Tools:\nYou have access to these Claude Code tools:\n"
        body += f"\n- **{tool}**: [Add specific usage guidance for {tool}]"

    elif action == "remove" and tool in tools:
        tools.remove(tool)

    metadata['tools'] = list(tools)
    return metadata, body

def enhance_model(metadata: Dict, body: str, model: str) -> tuple[Dict, str]:
    """Change agent model"""
    if model not in ['opus', 'sonnet', 'haiku']:
        raise ValueError("Model must be one of: opus, sonnet, haiku")

    metadata['model'] = model

    # Update system prompt based on model capabilities
    if model == 'opus':
        if "maximum reasoning" not in body:
            body += "\n\nYou are using the Opus model with maximum reasoning capabilities."
    elif model == 'haiku':
        if "fast and efficient" not in body:
            body += "\n\nYou are using the Haiku model. Focus on fast, efficient responses."

    return metadata, body

def enhance_tags(metadata: Dict, body: str, tags: List[str]) -> tuple[Dict, str]:
    """Add tags to agent"""
    current_tags = set(metadata.get('tags', []))
    current_tags.update(tags)
    metadata['tags'] = list(current_tags)
    return metadata, body

def enhance_prompt(metadata: Dict, body: str) -> tuple[Dict, str]:
    """Improve system prompt with best practices"""
    enhancements = []

    # Add role clarity
    if "You are" not in body:
        role_name = metadata['name'].replace('-', ' ').title()
        enhancements.append(f"You are {role_name}, " + metadata['description'])

    # Add core workflow
    if "workflow" not in body.lower() and "steps" not in body.lower():
        enhancements.append("""
#### Core Workflow:
1. **Analyze**: Understand the user's request and context
2. **Plan**: Determine the best approach and required tools
3. **Execute**: Use available tools to complete the task
4. **Review**: Verify the result meets requirements
""")

    # Add output format guidance
    if "output format" not in body.lower():
        enhancements.append("""
#### Output Format:
Provide clear, actionable responses. Use markdown formatting for readability.
""")

    # Add error handling
    if "error" not in body.lower() or "fail" not in body.lower():
        enhancements.append("""
#### Error Handling:
If you encounter issues, clearly explain the problem and suggest alternative approaches.
""")

    if enhancements:
        body += "\n" + "\n".join(enhancements)

    return metadata, body

def enhance_workflow(metadata: Dict, body: str, workflow: str) -> tuple[Dict, str]:
    """Add specific workflow instructions"""
    workflow_section = f"""
#### Specific Workflow: {workflow}

Follow these steps when handling {workflow.lower()} requests:
1. [Add specific steps for this workflow]
2. [Include tool usage patterns]
3. [Define success criteria]

"""
    body += workflow_section
    return metadata, body

def enhance_constraints(metadata: Dict, body: str, constraints: List[str]) -> tuple[Dict, str]:
    """Add operational constraints"""
    if "constraints" not in body.lower() or "guardrails" not in body.lower():
        constraints_section = "\n#### Constraints and Guardrails:\n"
        for constraint in constraints:
            constraints_section += f"- **{constraint}**\n"
        body += constraints_section

    return metadata, body

def main():
    parser = argparse.ArgumentParser(description="Enhance existing agents")
    parser.add_argument("--agent", required=True, help="Path to agent file (e.g., .claude/agents/my-agent.md)")
    parser.add_argument("--add-tool", help="Add a tool (Task, Bash, Read, Write, Grep, SlashCommand)")
    parser.add_argument("--remove-tool", help="Remove a tool")
    parser.add_argument("--model", choices=["opus", "sonnet", "haiku"], help="Change model")
    parser.add_argument("--add-tags", help="Add tags (comma-separated)")
    parser.add_argument("--improve-prompt", action="store_true", help="Enhance system prompt")
    parser.add_argument("--add-workflow", help="Add specific workflow instructions")
    parser.add_argument("--add-constraints", help="Add constraints (comma-separated)")
    parser.add_argument("--backup", action="store_true", help="Create backup before modification")

    args = parser.parse_args()

    # Validate agent file exists
    agent_path = Path(args.agent)
    if not agent_path.exists():
        print(f"❌ Agent file not found: {args.agent}")
        sys.exit(1)

    # Create backup
    if args.backup:
        backup_path = agent_path.with_suffix('.md.backup')
        import shutil
        shutil.copy2(agent_path, backup_path)
        print(f"✅ Backup created: {backup_path}")

    try:
        # Parse existing agent
        metadata, body = parse_agent_file(args.agent)
        print(f"📖 Loaded agent: {metadata['name']}")

        # Apply enhancements
        changes_made = False

        if args.add_tool:
            metadata, body = enhance_with_tool(metadata, body, args.add_tool, "add")
            print(f"✅ Added tool: {args.add_tool}")
            changes_made = True

        if args.remove_tool:
            metadata, body = enhance_with_tool(metadata, body, args.remove_tool, "remove")
            print(f"✅ Removed tool: {args.remove_tool}")
            changes_made = True

        if args.model:
            metadata, body = enhance_model(metadata, body, args.model)
            print(f"✅ Changed model to: {args.model}")
            changes_made = True

        if args.add_tags:
            tags = [tag.strip() for tag in args.add_tags.split(',')]
            metadata, body = enhance_tags(metadata, body, tags)
            print(f"✅ Added tags: {', '.join(tags)}")
            changes_made = True

        if args.improve_prompt:
            metadata, body = enhance_prompt(metadata, body)
            print("✅ Enhanced system prompt")
            changes_made = True

        if args.add_workflow:
            metadata, body = enhance_workflow(metadata, body, args.add_workflow)
            print(f"✅ Added workflow: {args.add_workflow}")
            changes_made = True

        if args.add_constraints:
            constraints = [c.strip() for c in args.add_constraints.split(',')]
            metadata, body = enhance_constraints(metadata, body, constraints)
            print(f"✅ Added constraints: {', '.join(constraints)}")
            changes_made = True

        if not changes_made:
            print("ℹ️  No enhancements specified. Use --help to see available options.")
            return

        # Write enhanced agent
        write_agent_file(args.agent, metadata, body)
        print(f"✅ Enhanced agent saved: {args.agent}")

        # Validate enhanced agent
        import subprocess
        result = subprocess.run([
            sys.executable, "validate_agent.py",
            "--file", args.agent
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Enhanced agent validation passed!")
        else:
            print("⚠️  Validation warnings:")
            print(result.stderr)

    except Exception as e:
        print(f"❌ Error enhancing agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()