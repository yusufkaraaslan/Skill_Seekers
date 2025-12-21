#!/usr/bin/env python3
"""
Install skills to AI coding agent directories.

This module provides functionality to install Skill Seekers-generated skills
to various AI coding agents (Claude Code, Cursor, VS Code, Amp, Goose, etc.)
by copying skill directories to agent-specific installation paths.

Usage:
    skill-seekers install-agent <skill_directory> --agent <agent_name> [--force] [--dry-run]

Examples:
    # Install to specific agent
    skill-seekers install-agent output/react/ --agent cursor

    # Install to all agents at once
    skill-seekers install-agent output/react/ --agent all

    # Force overwrite existing installation
    skill-seekers install-agent output/react/ --agent claude --force

    # Preview installation without making changes
    skill-seekers install-agent output/react/ --agent cursor --dry-run
"""

import argparse
import shutil
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple, Union
from difflib import get_close_matches


# Agent installation paths
# Global paths (install to home directory): Use ~/.{agent}/skills/
# Project paths (install to current directory): Use .{agent}/skills/
AGENT_PATHS = {
    'claude': '~/.claude/skills/',           # Global (home)
    'cursor': '.cursor/skills/',             # Project-relative
    'vscode': '.github/skills/',             # Project-relative
    'copilot': '.github/skills/',            # Same as VSCode
    'amp': '~/.amp/skills/',                 # Global
    'goose': '~/.config/goose/skills/',      # Global
    'opencode': '~/.opencode/skills/',       # Global
    'letta': '~/.letta/skills/',             # Global
    'aide': '~/.aide/skills/',               # Global
    'windsurf': '~/.windsurf/skills/',       # Global
}


def get_agent_path(agent_name: str, project_root: Optional[Path] = None) -> Path:
    """
    Resolve the installation path for a given agent.

    Handles both global paths (~/.<agent>/skills/) and project-relative paths
    (.cursor/skills/, .github/skills/).

    Args:
        agent_name: Name of the agent (e.g., 'claude', 'cursor')
        project_root: Optional project root directory for project-relative paths
                     (defaults to current working directory)

    Returns:
        Absolute path to the agent's skill installation directory

    Raises:
        ValueError: If agent_name is not recognized
    """
    agent_name = agent_name.lower()

    if agent_name not in AGENT_PATHS:
        raise ValueError(f"Unknown agent: {agent_name}")

    path_template = AGENT_PATHS[agent_name]

    # Handle home directory expansion (~)
    if path_template.startswith('~'):
        return Path(path_template).expanduser()

    # Handle project-relative paths
    if project_root is None:
        project_root = Path.cwd()

    return project_root / path_template


def get_available_agents() -> list:
    """
    Get list of all supported agent names.

    Returns:
        List of agent names (lowercase)
    """
    return sorted(AGENT_PATHS.keys())


def validate_agent_name(agent_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate an agent name and provide suggestions if invalid.

    Performs case-insensitive matching and fuzzy matching to suggest
    similar agent names if the provided name is invalid.

    Args:
        agent_name: Agent name to validate

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if agent name is valid, False otherwise
        - error_message: None if valid, error message with suggestions if invalid
    """
    # Special case: 'all' is valid for installing to all agents
    if agent_name.lower() == 'all':
        return True, None

    # Case-insensitive check
    if agent_name.lower() in AGENT_PATHS:
        return True, None

    # Agent not found - provide suggestions
    available = get_available_agents()

    # Try fuzzy matching (find similar names)
    suggestions = get_close_matches(agent_name.lower(), available, n=1, cutoff=0.6)

    error_msg = f"Unknown agent '{agent_name}'\n\n"

    if suggestions:
        error_msg += f"Did you mean: {suggestions[0]}?\n\n"

    error_msg += "Available agents:\n  "
    error_msg += ", ".join(available + ['all'])
    error_msg += f"\n\nUsage:\n  skill-seekers install-agent <skill_directory> --agent {suggestions[0] if suggestions else 'claude'}"

    return False, error_msg


def validate_skill_directory(skill_dir: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate that a directory is a valid skill directory.

    A valid skill directory must:
    - Exist
    - Be a directory
    - Contain a SKILL.md file

    Args:
        skill_dir: Path to skill directory

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not skill_dir.exists():
        return False, f"Skill directory does not exist: {skill_dir}"

    if not skill_dir.is_dir():
        return False, f"Path is not a directory: {skill_dir}"

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return False, f"SKILL.md not found in {skill_dir}"

    return True, None


def install_to_agent(
    skill_dir: Union[str, Path],
    agent_name: str,
    force: bool = False,
    dry_run: bool = False
) -> Tuple[bool, str]:
    """
    Install a skill to a specific agent's directory.

    Copies the skill directory to the agent's installation path, excluding
    backup files and temporary files.

    Args:
        skill_dir: Path to skill directory
        agent_name: Name of agent to install to
        force: If True, overwrite existing installation without asking
        dry_run: If True, preview installation without making changes

    Returns:
        Tuple of (success, message)
        - success: True if installation succeeded, False otherwise
        - message: Success message or error description
    """
    # Convert to Path
    skill_dir = Path(skill_dir).resolve()
    skill_name = skill_dir.name

    # Validate skill directory
    is_valid, error_msg = validate_skill_directory(skill_dir)
    if not is_valid:
        return False, f"❌ {error_msg}"

    # Validate agent name
    is_valid, error_msg = validate_agent_name(agent_name)
    if not is_valid:
        return False, f"❌ {error_msg}"

    # Get agent installation path
    try:
        agent_base_path = get_agent_path(agent_name.lower())
    except ValueError as e:
        return False, f"❌ {str(e)}"

    # Target path: {agent_base_path}/{skill_name}/
    target_path = agent_base_path / skill_name

    # Check if already exists
    if target_path.exists() and not force:
        error_msg = f"❌ Skill already installed\n\n"
        error_msg += f"Location: {target_path}\n\n"
        error_msg += "Options:\n"
        error_msg += f"  1. Overwrite: skill-seekers install-agent {skill_dir} --agent {agent_name} --force\n"
        error_msg += f"  2. Remove:    rm -rf {target_path}\n"
        error_msg += f"  3. Rename:    mv {skill_dir} {skill_dir.parent / (skill_name + '-v2')}"
        return False, error_msg

    # Dry run mode - just preview
    if dry_run:
        msg = f"🔍 DRY RUN - No changes will be made\n\n"
        msg += f"Would install skill: {skill_name}\n"
        msg += f"   Source: {skill_dir}\n"
        msg += f"   Target: {target_path}\n\n"

        # Calculate total size
        total_size = sum(f.stat().st_size for f in skill_dir.rglob('*') if f.is_file())

        msg += f"Files to copy:\n"
        msg += f"   SKILL.md ({(skill_dir / 'SKILL.md').stat().st_size / 1024:.1f} KB)\n"

        references_dir = skill_dir / 'references'
        if references_dir.exists():
            ref_files = list(references_dir.rglob('*.md'))
            ref_size = sum(f.stat().st_size for f in ref_files)
            msg += f"   references/ ({len(ref_files)} files, {ref_size / 1024:.1f} KB)\n"

        for subdir in ['scripts', 'assets']:
            subdir_path = skill_dir / subdir
            if subdir_path.exists():
                files = list(subdir_path.rglob('*'))
                if files:
                    msg += f"   {subdir}/ ({len(files)} files)\n"
                else:
                    msg += f"   {subdir}/ (empty)\n"

        msg += f"\nTotal size: {total_size / 1024:.1f} KB\n\n"
        msg += f"To actually install, run:\n"
        msg += f"  skill-seekers install-agent {skill_dir} --agent {agent_name}"

        return True, msg

    # Create parent directories if needed
    try:
        agent_base_path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        return False, f"❌ Permission denied: {agent_base_path}\n\nTry: sudo mkdir -p {agent_base_path} && sudo chown -R $USER {agent_base_path}"

    # Copy skill directory
    def ignore_files(directory, files):
        """Filter function for shutil.copytree to exclude unwanted files."""
        ignored = []
        for f in files:
            # Exclude backup files
            if f.endswith('.backup'):
                ignored.append(f)
            # Exclude Python cache
            elif f == '__pycache__':
                ignored.append(f)
            # Exclude macOS metadata
            elif f == '.DS_Store':
                ignored.append(f)
            # Exclude hidden files (except .github for vscode)
            elif f.startswith('.') and f not in ['.github', '.cursor']:
                ignored.append(f)
        return ignored

    try:
        # Remove existing if force mode
        if target_path.exists() and force:
            shutil.rmtree(target_path)

        # Copy directory
        shutil.copytree(skill_dir, target_path, ignore=ignore_files)

        # Success message
        msg = f"✅ Installation complete!\n\n"
        msg += f"Skill '{skill_name}' installed to {agent_name}\n"
        msg += f"Location: {target_path}\n\n"

        # Agent-specific restart instructions
        if agent_name.lower() == 'claude':
            msg += "Restart Claude Code to load the new skill."
        elif agent_name.lower() == 'cursor':
            msg += "Restart Cursor to load the new skill."
        elif agent_name.lower() in ['vscode', 'copilot']:
            msg += "Restart VS Code to load the new skill."
        else:
            msg += f"Restart {agent_name.capitalize()} to load the new skill."

        return True, msg

    except PermissionError as e:
        return False, f"❌ Permission denied: {e}\n\nTry: sudo mkdir -p {agent_base_path} && sudo chown -R $USER {agent_base_path}"
    except Exception as e:
        return False, f"❌ Installation failed: {e}"


def install_to_all_agents(
    skill_dir: Union[str, Path],
    force: bool = False,
    dry_run: bool = False
) -> Dict[str, Tuple[bool, str]]:
    """
    Install a skill to all available agents.

    Attempts to install the skill to all agents in AGENT_PATHS,
    collecting results for each agent.

    Args:
        skill_dir: Path to skill directory
        force: If True, overwrite existing installations
        dry_run: If True, preview installations without making changes

    Returns:
        Dictionary mapping agent names to (success, message) tuples
    """
    results = {}

    for agent_name in get_available_agents():
        success, message = install_to_agent(skill_dir, agent_name, force=force, dry_run=dry_run)
        results[agent_name] = (success, message)

    return results


def main() -> int:
    """
    Main entry point for install-agent CLI.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        prog="skill-seekers-install-agent",
        description="Install skills to AI coding agent directories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Install to specific agent
  skill-seekers install-agent output/react/ --agent cursor

  # Install to all agents
  skill-seekers install-agent output/react/ --agent all

  # Force overwrite
  skill-seekers install-agent output/react/ --agent claude --force

  # Preview installation
  skill-seekers install-agent output/react/ --agent cursor --dry-run

Supported agents:
  claude, cursor, vscode, copilot, amp, goose, opencode, letta, aide, windsurf, all
        """
    )

    parser.add_argument(
        "skill_directory",
        help="Path to skill directory (e.g., output/react/)"
    )

    parser.add_argument(
        "--agent",
        required=True,
        help="Agent name (use 'all' to install to all agents)"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing installation without asking"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview installation without making changes"
    )

    args = parser.parse_args()

    # Convert skill directory to Path
    skill_dir = Path(args.skill_directory)
    skill_name = skill_dir.name

    # Handle 'all' agent
    if args.agent.lower() == 'all':
        print(f"\n📋 Installing skill to all agents: {skill_name}\n")

        if args.dry_run:
            print("🔍 DRY RUN MODE - No changes will be made\n")

        results = install_to_all_agents(skill_dir, force=args.force, dry_run=args.dry_run)

        # Print results
        installed_count = 0
        failed_count = 0
        skipped_count = 0

        for agent_name, (success, message) in results.items():
            if success:
                if args.dry_run:
                    print(f"⏳ Would install to {agent_name}...")
                else:
                    agent_path = get_agent_path(agent_name)
                    print(f"⏳ Installing to {agent_name}...   ✅ {agent_path / skill_name}")
                installed_count += 1
            else:
                # Check if it's a permission error or skip
                if "Permission denied" in message:
                    print(f"⏳ Installing to {agent_name}...   ❌ Permission denied")
                    failed_count += 1
                elif "does not exist" in message or "SKILL.md not found" in message:
                    # Validation error - only show once
                    print(message)
                    return 1
                else:
                    print(f"⏳ Installing to {agent_name}...   ⚠️  Skipped (not installed)")
                    skipped_count += 1

        # Summary
        print(f"\n📊 Summary:")
        if args.dry_run:
            print(f"   Would install: {installed_count} agents")
        else:
            print(f"   ✅ Installed: {installed_count} agents")
        if failed_count > 0:
            print(f"   ❌ Failed:    {failed_count} agent(s) (permission denied)")
        if skipped_count > 0:
            print(f"   ⚠️  Skipped:  {skipped_count} agent(s) (not installed)")

        if not args.dry_run:
            print("\nRestart your agents to load the skill.")

        if failed_count > 0:
            print("\nFix permission errors:")
            print("   sudo mkdir -p ~/.amp && sudo chown -R $USER ~/.amp")

        return 0 if installed_count > 0 else 1

    # Single agent installation
    agent_name = args.agent

    print(f"\n📋 Installing skill: {skill_name}")
    print(f"   Agent:  {agent_name}")

    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made\n")

    success, message = install_to_agent(skill_dir, agent_name, force=args.force, dry_run=args.dry_run)

    print(message)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
