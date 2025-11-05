#!/usr/bin/env python3
"""
Automatic Documentation Synchronization for CLAUDE.md

Detects changes in agents, commands, skills, and project structure,
then automatically updates CLAUDE.md to maintain documentation consistency.
"""

import os
import sys
import json
import argparse
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
import re
import yaml

class ClaudeDocumentationUpdater:
    """Updates CLAUDE.md based on current project state."""

    def __init__(self, project_dir: str = None):
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.claude_md_path = self.project_dir / "CLAUDE.md"
        self.claude_dir = self.project_dir / ".claude"
        self.hash_file = self.claude_dir / ".docs_hash"

    def update_documentation(self, dry_run: bool = False, agents_only: bool = False,
                           commands_only: bool = False, skills_only: bool = False,
                           force: bool = False, verbose: bool = False) -> Dict[str, Any]:
        """Main update workflow using A.U.D.I.T. method."""

        results = {
            'changes_detected': False,
            'agents_updated': 0,
            'commands_updated': 0,
            'skills_updated': 0,
            'structure_updated': False,
            'updates_made': []
        }

        if verbose:
            print("🔍 A - Analyzing Current State...")

        # Check if changes are detected
        if not force and not self._changes_detected() and not dry_run:
            print("✅ No changes detected, documentation is up to date.")
            return results

        if dry_run:
            print("🔮 DRY RUN MODE - Showing what would be updated:")

        if verbose:
            print("📊 U - Update Detection...")

        # Load current CLAUDE.md
        if not self.claude_md_path.exists():
            print("❌ CLAUDE.md not found!")
            return results

        current_content = self.claude_md_path.read_text()

        # Generate updated sections
        updated_content = current_content

        if not commands_only and not skills_only:
            # Update agents section
            if verbose:
                print("  🤖 Checking agents...")
            agents_updated, new_agents_content = self._update_agents_section(current_content, verbose)
            if agents_updated > 0:
                updated_content = new_agents_content
                results['agents_updated'] = agents_updated
                results['changes_detected'] = True
                results['updates_made'].append(f"Updated {agents_updated} agent descriptions")

        if not agents_only and not skills_only:
            # Update commands section
            if verbose:
                print("  📋 Checking commands...")
            commands_updated, new_commands_content = self._update_commands_section(updated_content, verbose)
            if commands_updated > 0:
                updated_content = new_commands_content
                results['commands_updated'] = commands_updated
                results['changes_detected'] = True
                results['updates_made'].append(f"Updated {commands_updated} command descriptions")

        if not agents_only and not commands_only:
            # Update skills section
            if verbose:
                print("  🛠️ Checking skills...")
            skills_updated, new_skills_content = self._update_skills_section(updated_content, verbose)
            if skills_updated > 0:
                updated_content = new_skills_content
                results['skills_updated'] = skills_updated
                results['changes_detected'] = True
                results['updates_made'].append(f"Updated {skills_updated} skill descriptions")

        if verbose:
            print("🏗️ I - Integration with CLAUDE.md...")

        # Write updated content if not dry run
        if not dry_run and updated_content != current_content:
            if verbose:
                print("💾 Writing updated documentation...")

            # Create backup
            backup_path = self.claude_md_path.with_suffix('.md.backup')
            backup_path.write_text(current_content)

            # Write updated content
            self.claude_md_path.write_text(updated_content)

            # Update hash
            self._update_hash()

            results['changes_detected'] = True

        if verbose:
            print("✅ T - Testing and Validation...")
            self._validate_documentation(updated_content)

        return results

    def _changes_detected(self) -> bool:
        """Check if any changes have been made since last update."""
        current_hash = self._calculate_hash()

        if not self.hash_file.exists():
            return True

        cached_hash = self.hash_file.read_text().strip()
        return current_hash != cached_hash

    def _calculate_hash(self) -> str:
        """Calculate hash of relevant .claude files."""
        hasher = hashlib.md5()

        # Include all relevant markdown files
        for pattern in ['**/*.md', '**/*.yaml', '**/*.json']:
            for file_path in self.claude_dir.glob(pattern):
                if file_path.is_file():
                    hasher.update(file_path.read_bytes())

        return hasher.hexdigest()

    def _update_hash(self):
        """Update the stored hash."""
        current_hash = self._calculate_hash()
        self.hash_file.write_text(current_hash)

    def _update_agents_section(self, content: str, verbose: bool = False) -> tuple[int, str]:
        """Update the Available Agents section."""
        agents_dir = self.claude_dir / "agents"
        if not agents_dir.exists():
            return 0, content

        # Find all agent files
        agent_files = list(agents_dir.glob("*.md"))
        if not agent_files:
            return 0, content

        # Parse agent metadata
        agents_data = []
        for agent_file in agent_files:
            agent_info = self._parse_agent_file(agent_file)
            if agent_info:
                agents_data.append(agent_info)

        # Generate updated agents table
        new_agents_section = self._generate_agents_section(agents_data)

        # Replace in content
        pattern = r'(### \*\*Available Agents\*\*.*?)(?=\n### |\n## |\Z)'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            updated_content = content.replace(match.group(1), new_agents_section + "\n\n")
            if verbose:
                print(f"    ✅ Found and updated agents section with {len(agents_data)} agents")
            return len(agents_data), updated_content
        else:
            if verbose:
                print("    ⚠️ Could not find agents section to replace")
            return 0, content

    def _parse_agent_file(self, agent_file: Path) -> Optional[Dict[str, str]]:
        """Parse agent metadata from markdown file."""
        try:
            content = agent_file.read_text()

            # Extract YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    metadata = yaml.safe_load(parts[1])
                    return {
                        'name': metadata.get('name', agent_file.stem),
                        'description': metadata.get('description', 'No description available'),
                        'use_case': self._extract_use_case(content, metadata)
                    }

            # Fallback: extract from content
            name = agent_file.stem
            description = self._extract_description_from_content(content)
            use_case = self._extract_use_case_from_content(content)

            return {
                'name': name,
                'description': description,
                'use_case': use_case
            }

        except Exception as e:
            print(f"    ⚠️ Error parsing {agent_file}: {e}")
            return None

    def _extract_description_from_content(self, content: str) -> str:
        """Extract description from content without frontmatter."""
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                continue  # Skip title
            if line.strip() and not line.startswith('---'):
                # First non-empty line after title
                return line.strip()
        return "No description available"

    def _extract_use_case_from_content(self, content: str) -> str:
        """Extract use case from content."""
        # Look for patterns like "Use Case:", "Purpose:", etc.
        patterns = [
            r'(?i)use case[:\s]+([^\n]+)',
            r'(?i)purpose[:\s]+([^\n]+)',
            r'(?i)best for[:\s]+([^\n]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()

        return "General analysis and task automation"

    def _extract_use_case(self, content: str, metadata: Dict) -> str:
        """Extract use case from metadata or content."""
        # Try metadata first
        if 'use_case' in metadata:
            return metadata['use_case']

        if 'tags' in metadata:
            tags = metadata['tags']
            if isinstance(tags, list) and tags:
                return tags[0]
            elif isinstance(tags, str):
                return tags

        # Fallback to content parsing
        return self._extract_use_case_from_content(content)

    def _generate_agents_section(self, agents_data: List[Dict[str, str]]) -> str:
        """Generate the updated agents section."""
        lines = [
            "### **Available Agents**",
            "",
            "| Agent | Description | Use Case |",
            "|--------|-------------|---------|"
        ]

        for agent in sorted(agents_data, key=lambda x: x['name']):
            name = agent['name']
            description = agent['description']
            use_case = agent['use_case']
            lines.append(f"| **@{name}** | {description} | {use_case} |")

        return "\n".join(lines)

    def _update_commands_section(self, content: str, verbose: bool = False) -> tuple[int, str]:
        """Update the Custom Commands section."""
        commands_dir = self.claude_dir / "commands"
        if not commands_dir.exists():
            return 0, content

        # Find all command files
        command_files = list(commands_dir.glob("*.md"))
        if not command_files:
            return 0, content

        # Generate updated commands section
        new_commands_section = self._generate_commands_section(command_files)

        # Replace in content
        pattern = r'(### \*\*Custom Commands\*\*.*?)(?=\n### |\n## |\Z)'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            updated_content = content.replace(match.group(1), new_commands_section + "\n\n")
            if verbose:
                print(f"    ✅ Found and updated commands section with {len(command_files)} commands")
            return len(command_files), updated_content
        else:
            if verbose:
                print("    ⚠️ Could not find commands section to replace")
            return 0, content

    def _generate_commands_section(self, command_files: List[Path]) -> str:
        """Generate the updated commands section."""
        lines = [
            "### **Custom Commands**",
            "",
            "The following custom commands are available:",
            ""
        ]

        for cmd_file in sorted(command_files):
            cmd_name = cmd_file.stem
            lines.append(f"- **/{cmd_name}** - Custom command for {cmd_name.replace('-', ' ')}")

        return "\n".join(lines)

    def _update_skills_section(self, content: str, verbose: bool = False) -> tuple[int, str]:
        """Update the Available Skills section."""
        skills_dir = self.claude_dir / "skills"
        if not skills_dir.exists():
            return 0, content

        # Find all skill directories
        skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
        if not skill_dirs:
            return 0, content

        # Generate updated skills section
        new_skills_section = self._generate_skills_section(skill_dirs)

        # Replace in content
        pattern = r'(### \*\*Available Skills\*\*.*?)(?=\n### |\n## |\Z)'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            updated_content = content.replace(match.group(1), new_skills_section + "\n\n")
            if verbose:
                print(f"    ✅ Found and updated skills section with {len(skill_dirs)} skills")
            return len(skill_dirs), updated_content
        else:
            if verbose:
                print("    ⚠️ Could not find skills section to replace")
            return 0, content

    def _generate_skills_section(self, skill_dirs: List[Path]) -> str:
        """Generate the updated skills section."""
        lines = [
            "### **Available Skills**",
            "",
            "The following skills are available:",
            ""
        ]

        for skill_dir in sorted(skill_dirs):
            skill_name = skill_dir.name
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                # Extract description from SKILL.md
                try:
                    content = skill_md.read_text()
                    desc = self._extract_description_from_content(content)
                    lines.append(f"- **{skill_name}** - {desc}")
                except:
                    lines.append(f"- **{skill_name}** - Available skill")
            else:
                lines.append(f"- **{skill_name}** - Available skill")

        return "\n".join(lines)

    def _validate_documentation(self, content: str):
        """Basic validation of the updated documentation."""
        # Check for table formatting consistency
        tables = re.findall(r'\|[^\|]+\|[^\|]+\|[^\|]+\|', content)
        for table in tables:
            if table.count('|') < 4:
                print(f"    ⚠️ Table formatting issue: {table[:50]}...")

        # Check for broken references (exclude trailing backticks from code formatting)
        references = re.findall(r'\.claude/[^)\s`]+', content)
        checked_refs = set()  # Avoid duplicate warnings

        for ref in references:
            # Normalize path (remove trailing slash if present for directories)
            ref_normalized = ref.rstrip('/') if ref.endswith('/') and not ref.endswith('.py') and not ref.endswith('.md') else ref

            if ref_normalized not in checked_refs:
                checked_refs.add(ref_normalized)
                ref_path = self.project_dir / ref_normalized
                if not ref_path.exists():
                    print(f"    ⚠️ Broken reference: {ref_normalized}")
                else:
                    if ref != ref_normalized:
                        # Path was normalized and exists
                        pass

        print("    ✅ Documentation validation complete")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Update CLAUDE.md documentation")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated without making changes")
    parser.add_argument("--agents-only", action="store_true", help="Update only agent-related sections")
    parser.add_argument("--commands-only", action="store_true", help="Update only command-related sections")
    parser.add_argument("--skills-only", action="store_true", help="Update only skill-related sections")
    parser.add_argument("--force", action="store_true", help="Force update even if no changes detected")
    parser.add_argument("--verbose", action="store_true", help="Show detailed change detection process")

    args = parser.parse_args()

    updater = ClaudeDocumentationUpdater()
    results = updater.update_documentation(
        dry_run=args.dry_run,
        agents_only=args.agents_only,
        commands_only=args.commands_only,
        skills_only=args.skills_only,
        force=args.force,
        verbose=args.verbose
    )

    if results['changes_detected'] or args.dry_run:
        print("\n📋 Update Summary:")
        if results['updates_made']:
            for update in results['updates_made']:
                print(f"  ✅ {update}")
        else:
            print("  ℹ️ No updates needed")

        if not args.dry_run:
            print("\n🎉 CLAUDE.md updated successfully!")
        else:
            print("\n🔮 Dry run complete - no changes made")
    else:
        print("✅ Documentation is already up to date!")

if __name__ == "__main__":
    main()