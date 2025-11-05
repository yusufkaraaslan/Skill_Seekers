#!/usr/bin/env python3
"""
Export agents to Skill Seekers format.

This script converts Claude Code agents into Skill Seekers skills and configurations,
enabling the agent scaffolding toolkit to integrate with the broader Skill Seekers
ecosystem for documentation scraping and skill packaging.

Features:
- Maps agent metadata to Skill Seekers skill format
- Generates skill configurations for each agent
- Detects conflicts between agent definitions and existing skills
- Creates unified skill packages
- Preserves delegation relationships

Usage:
    python3 export_to_skill_seekers.py [options]

Options:
    --agents-dir PATH     Path to .claude/agents directory (default: auto-detect)
    --output-dir PATH     Output directory for skills (default: output/agent-skills/)
    --format {skill|config|both}  Export format (default: both)
    --detect-conflicts    Enable conflict detection with existing skills
    --package             Package exported skills as .zip files
    --verbose            Enable verbose output
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install PyYAML", file=sys.stderr)
    sys.exit(1)


class AgentToSkillExporter:
    """Convert Claude Code agents to Skill Seekers skills."""
    
    def __init__(
        self,
        agents_dir: Path,
        output_dir: Path,
        format: str = "both",
        detect_conflicts: bool = False,
        verbose: bool = False
    ):
        self.agents_dir = agents_dir
        self.output_dir = output_dir
        self.format = format
        self.detect_conflicts = detect_conflicts
        self.verbose = verbose
        
        # Load registry if available
        self.registry_path = self._find_registry()
        self.registry = self._load_registry() if self.registry_path else None
    
    def _find_registry(self) -> Optional[Path]:
        """Find agent registry file."""
        possible_paths = [
            self.agents_dir.parent / "skills" / "agent-scaffolding-toolkit" / "assets" / "agent_registry.json",
            self.agents_dir.parent / "assets" / "agent_registry.json"
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def _load_registry(self) -> Optional[Dict[str, Any]]:
        """Load agent registry."""
        if not self.registry_path:
            return None
        
        try:
            with open(self.registry_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            if self.verbose:
                print(f"Warning: Failed to load registry: {e}", file=sys.stderr)
            return None
    
    def _parse_agent_yaml(self, agent_path: Path) -> Optional[Dict[str, Any]]:
        """Parse agent YAML frontmatter."""
        content = agent_path.read_text()
        
        # Extract YAML frontmatter
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
        
        if not yaml_lines:
            return None
        
        try:
            yaml_content = '\n'.join(yaml_lines)
            return yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            if self.verbose:
                print(f"Warning: Failed to parse YAML in {agent_path.name}: {e}", file=sys.stderr)
            return None
    
    def _agent_to_skill_md(self, agent_path: Path, metadata: Dict[str, Any]) -> str:
        """Convert agent to SKILL.md format."""
        agent_name = metadata.get('name', agent_path.stem)
        description = metadata.get('description', 'No description provided')
        tools = metadata.get('tools', [])
        delegates_to = metadata.get('delegates_to', [])
        version = metadata.get('version', '1.0')
        
        # Read full agent content for examples
        full_content = agent_path.read_text()
        
        # Extract sections after YAML
        lines = full_content.split('\n')
        content_lines = []
        yaml_count = 0
        past_yaml = False
        
        for line in lines:
            if line.strip() == '---':
                yaml_count += 1
                if yaml_count == 2:
                    past_yaml = True
                continue
            if past_yaml:
                content_lines.append(line)
        
        agent_body = '\n'.join(content_lines).strip()
        
        # Generate SKILL.md
        skill_md = f"""# {agent_name}

**Version:** {version}
**Type:** Claude Code Agent

## When to Use This Skill

{description}

## What This Skill Contains

### Agent Capabilities

- **Tools:** {', '.join(tools) if tools else 'None'}
- **Model:** {metadata.get('model', 'claude-3-5-sonnet-20241022')}
- **Delegation:** {'Delegates to: ' + ', '.join(delegates_to) if delegates_to else 'Standalone agent'}

### Skill Structure

```
{agent_name}/
├── SKILL.md                    # This file
├── agent_definition.md         # Original agent definition
└── metadata.json              # Agent metadata
```

## Agent Definition

{agent_body}

## Integration with Claude Code

This skill is designed for use with Claude Code's agent system. To use:

1. Copy `agent_definition.md` to `.claude/agents/{agent_name}.md` in your project
2. Reload Claude Code or trigger SessionStart hook
3. Agent will be automatically registered and available

## Delegation Chain

"""
        
        if delegates_to:
            skill_md += "This agent delegates tasks to the following agents:\n\n"
            for delegate in delegates_to:
                skill_md += f"- **{delegate}**: Handles specialized sub-tasks\n"
        else:
            skill_md += "This is a standalone agent with no delegation dependencies.\n"
        
        skill_md += f"""

## Generated Information

- **Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Source:** Claude Code Agent Scaffolding Toolkit
- **Original Agent:** `.claude/agents/{agent_name}.md`

---

*This skill was automatically generated from a Claude Code agent definition.*
"""
        
        return skill_md
    
    def _agent_to_config(self, agent_path: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Convert agent to Skill Seekers config format."""
        agent_name = metadata.get('name', agent_path.stem)
        description = metadata.get('description', 'No description provided')
        
        # Map agent properties to Skill Seekers config
        config = {
            "name": agent_name,
            "description": description,
            "type": "claude_code_agent",
            "version": str(metadata.get('version', '1.0')),
            "metadata": {
                "model": metadata.get('model', 'claude-3-5-sonnet-20241022'),
                "tools": metadata.get('tools', []),
                "delegates_to": metadata.get('delegates_to', []),
                "export_date": datetime.now().isoformat(),
                "source": "agent-scaffolding-toolkit"
            },
            "categories": {
                "agent_definitions": [f"agents/{agent_name}"]
            }
        }
        
        # Add registry info if available
        if self.registry:
            agent_info = next(
                (a for a in self.registry.get('agents', []) if a['name'] == agent_name),
                None
            )
            if agent_info:
                config['metadata']['usage_count'] = agent_info.get('usage_count', 0)
                config['metadata']['created'] = agent_info.get('created')
                config['metadata']['last_modified'] = agent_info.get('last_modified')
        
        return config
    
    def _detect_conflicts_for_agent(
        self,
        agent_name: str,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect conflicts between agent and existing skills."""
        conflicts = []
        
        # Check for existing skill with same name
        existing_skill_dir = Path("output") / agent_name
        if existing_skill_dir.exists():
            conflicts.append({
                "severity": "medium",
                "type": "name_collision",
                "message": f"Skill directory '{agent_name}' already exists",
                "resolution": "Consider using a different name or merging definitions"
            })
        
        # Check for tool conflicts
        tools = set(metadata.get('tools', []))
        if 'run_in_terminal' in tools:
            conflicts.append({
                "severity": "low",
                "type": "security_concern",
                "message": "Agent uses run_in_terminal tool",
                "resolution": "Review security implications before deployment"
            })
        
        # Check delegation conflicts
        delegates_to = metadata.get('delegates_to', [])
        if delegates_to and self.registry:
            registered_agents = {a['name'] for a in self.registry.get('agents', [])}
            missing_delegates = set(delegates_to) - registered_agents
            
            if missing_delegates:
                conflicts.append({
                    "severity": "high",
                    "type": "missing_dependency",
                    "message": f"Agent delegates to non-existent agents: {', '.join(missing_delegates)}",
                    "resolution": "Export delegated agents first or update delegation list"
                })
        
        return conflicts
    
    def export_agent(self, agent_path: Path) -> Tuple[bool, List[str]]:
        """Export a single agent to Skill Seekers format."""
        messages = []
        
        # Parse agent
        metadata = self._parse_agent_yaml(agent_path)
        if not metadata:
            return False, [f"Failed to parse agent YAML: {agent_path.name}"]
        
        agent_name = metadata.get('name', agent_path.stem)
        
        # Create output directory
        skill_dir = self.output_dir / agent_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        # Detect conflicts
        if self.detect_conflicts:
            conflicts = self._detect_conflicts_for_agent(agent_name, metadata)
            if conflicts:
                messages.append(f"\n⚠️  Conflicts detected for {agent_name}:")
                for conflict in conflicts:
                    messages.append(f"  [{conflict['severity'].upper()}] {conflict['message']}")
                    messages.append(f"  → {conflict['resolution']}")
        
        # Export SKILL.md
        if self.format in ["skill", "both"]:
            skill_md = self._agent_to_skill_md(agent_path, metadata)
            skill_md_path = skill_dir / "SKILL.md"
            skill_md_path.write_text(skill_md)
            messages.append(f"✅ Generated SKILL.md: {skill_md_path}")
        
        # Export config
        if self.format in ["config", "both"]:
            config = self._agent_to_config(agent_path, metadata)
            config_path = skill_dir / f"{agent_name}.json"
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            messages.append(f"✅ Generated config: {config_path}")
        
        # Copy original agent definition
        agent_def_path = skill_dir / "agent_definition.md"
        agent_def_path.write_text(agent_path.read_text())
        
        # Create metadata file
        metadata_path = skill_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump({
                "name": agent_name,
                "version": str(metadata.get('version', '1.0')),
                "export_date": datetime.now().isoformat(),
                "source_file": str(agent_path),
                "metadata": metadata
            }, f, indent=2)
        
        return True, messages
    
    def export_all_agents(self) -> Dict[str, Any]:
        """Export all agents in the agents directory."""
        results = {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "messages": []
        }
        
        # Find all agent files
        agent_files = list(self.agents_dir.glob("*.md"))
        results["total"] = len(agent_files)
        
        if not agent_files:
            results["messages"].append("⚠️  No agent files found in agents directory")
            return results
        
        results["messages"].append(f"📦 Exporting {len(agent_files)} agents to Skill Seekers format...\n")
        
        # Export each agent
        for agent_path in sorted(agent_files):
            success, messages = self.export_agent(agent_path)
            
            if success:
                results["successful"] += 1
            else:
                results["failed"] += 1
            
            results["messages"].extend(messages)
            results["messages"].append("")  # Blank line between agents
        
        # Summary
        results["messages"].append("=" * 60)
        results["messages"].append(f"Export Summary:")
        results["messages"].append(f"  Total: {results['total']}")
        results["messages"].append(f"  Successful: {results['successful']}")
        results["messages"].append(f"  Failed: {results['failed']}")
        results["messages"].append(f"  Output: {self.output_dir}")
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description="Export Claude Code agents to Skill Seekers format"
    )
    parser.add_argument(
        "--agents-dir",
        type=Path,
        help="Path to .claude/agents directory (default: auto-detect)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/agent-skills"),
        help="Output directory for skills (default: output/agent-skills/)"
    )
    parser.add_argument(
        "--format",
        choices=["skill", "config", "both"],
        default="both",
        help="Export format (default: both)"
    )
    parser.add_argument(
        "--detect-conflicts",
        action="store_true",
        help="Enable conflict detection with existing skills"
    )
    parser.add_argument(
        "--package",
        action="store_true",
        help="Package exported skills as .zip files"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Auto-detect agents directory
    if not args.agents_dir:
        # Try to find .claude/agents from current directory or CLAUDE_PROJECT_DIR
        project_dir = os.getenv("CLAUDE_PROJECT_DIR")
        if project_dir:
            args.agents_dir = Path(project_dir) / ".claude" / "agents"
        else:
            # Search upward for .claude directory
            current = Path.cwd()
            while current != current.parent:
                claude_dir = current / ".claude" / "agents"
                if claude_dir.exists():
                    args.agents_dir = claude_dir
                    break
                current = current.parent
        
        if not args.agents_dir or not args.agents_dir.exists():
            print("Error: Could not find .claude/agents directory", file=sys.stderr)
            print("Use --agents-dir to specify the path", file=sys.stderr)
            sys.exit(1)
    
    if not args.agents_dir.exists():
        print(f"Error: Agents directory not found: {args.agents_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Create exporter
    exporter = AgentToSkillExporter(
        agents_dir=args.agents_dir,
        output_dir=args.output_dir,
        format=args.format,
        detect_conflicts=args.detect_conflicts,
        verbose=args.verbose
    )
    
    # Export all agents
    results = exporter.export_all_agents()
    
    # Print results
    for message in results["messages"]:
        print(message)
    
    # Package if requested
    if args.package:
        print("\n📦 Packaging exported skills...")
        try:
            # Import packaging module from Skill Seekers
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cli"))
            from package_skill import package_skill
            
            for skill_dir in args.output_dir.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    zip_path = package_skill(skill_dir)
                    print(f"✅ Packaged: {zip_path}")
        except ImportError:
            print("⚠️  Packaging requires Skill Seekers package_skill module", file=sys.stderr)
    
    # Exit code based on results
    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
