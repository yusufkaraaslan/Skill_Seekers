#!/usr/bin/env python3
"""
Automation script to generate Cline rules from Django documentation.

Usage:
    python generate_clinerules.py --project /path/to/project
    python generate_clinerules.py --project . --with-mcp
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and return success status."""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print(f"❌ ERROR: {description} failed with code {result.returncode}")
        return False

    print(f"✅ SUCCESS: {description}")
    return True


def setup_mcp_server(project_path: Path) -> bool:
    """Set up MCP server configuration for Cline."""
    print(f"\n{'='*60}")
    print(f"STEP: Configuring MCP Server")
    print(f"{'='*60}")

    # Create MCP config
    mcp_config = {
        "mcpServers": {
            "skill-seekers": {
                "command": "python",
                "args": [
                    "-m",
                    "skill_seekers.mcp.server_fastmcp",
                    "--transport",
                    "stdio"
                ],
                "env": {}
            }
        }
    }

    # Save to project
    vscode_dir = project_path / ".vscode"
    vscode_dir.mkdir(exist_ok=True)

    mcp_config_file = vscode_dir / "mcp_config.json"
    with open(mcp_config_file, 'w') as f:
        json.dump(mcp_config, f, indent=2)

    print(f"✅ Created: {mcp_config_file}")
    print(f"\nTo activate in Cline:")
    print(f"1. Open Cline panel in VS Code")
    print(f"2. Settings → MCP Servers → Load Configuration")
    print(f"3. Select: {mcp_config_file}")
    print(f"4. Reload VS Code window")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Generate Cline rules from Django documentation"
    )
    parser.add_argument(
        "--project",
        type=str,
        default=".",
        help="Path to your project directory (default: current directory)",
    )
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Skip scraping step (use existing output/django)",
    )
    parser.add_argument(
        "--with-mcp",
        action="store_true",
        help="Set up MCP server configuration",
    )
    parser.add_argument(
        "--modular",
        action="store_true",
        help="Create modular rules files (.clinerules.models, .clinerules.views, etc.)",
    )
    args = parser.parse_args()

    project_path = Path(args.project).resolve()
    output_dir = Path("output/django")

    print("=" * 60)
    print("Cline Rules Generator for Django")
    print("=" * 60)
    print(f"Project: {project_path}")
    print(f"Modular rules: {args.modular}")
    print(f"MCP integration: {args.with_mcp}")
    print("=" * 60)

    # Step 1: Scrape Django documentation (unless skipped)
    if not args.skip_scrape:
        if not run_command(
            [
                "skill-seekers",
                "scrape",
                "--config",
                "configs/django.json",
            ],
            "Scraping Django documentation",
        ):
            return 1
    else:
        print(f"\n⏭️  SKIPPED: Using existing {output_dir}")

        if not output_dir.exists():
            print(f"❌ ERROR: {output_dir} does not exist!")
            print(f"Run without --skip-scrape to generate documentation first.")
            return 1

    # Step 2: Package for Cline
    if not run_command(
        [
            "skill-seekers",
            "package",
            str(output_dir),
            "--target",
            "markdown",
        ],
        "Packaging for Cline",
    ):
        return 1

    # Step 3: Copy rules to project
    print(f"\n{'='*60}")
    print(f"STEP: Copying rules to project")
    print(f"{'='*60}")

    markdown_output = output_dir.parent / "django-markdown"
    source_skill = markdown_output / "SKILL.md"

    if not source_skill.exists():
        print(f"❌ ERROR: {source_skill} does not exist!")
        return 1

    if args.modular:
        # Split into modular files
        print("Creating modular rules files...")

        with open(source_skill, 'r') as f:
            content = f.read()

        # Split by major sections
        sections = content.split('\n## ')

        # Core rules (first part)
        core_rules = project_path / ".clinerules"
        with open(core_rules, 'w') as f:
            f.write(sections[0])
        print(f"✅ Created: {core_rules}")

        # Try to extract specific sections (simplified)
        # In a real implementation, this would be more sophisticated
        models_content = next((s for s in sections if 'Model' in s), None)
        if models_content:
            models_rules = project_path / ".clinerules.models"
            with open(models_rules, 'w') as f:
                f.write('## ' + models_content)
            print(f"✅ Created: {models_rules}")

        views_content = next((s for s in sections if 'View' in s), None)
        if views_content:
            views_rules = project_path / ".clinerules.views"
            with open(views_rules, 'w') as f:
                f.write('## ' + views_content)
            print(f"✅ Created: {views_rules}")

    else:
        # Single file
        dest_file = project_path / ".clinerules"
        shutil.copy(source_skill, dest_file)
        print(f"✅ Copied: {dest_file}")

    # Step 4: Set up MCP server (optional)
    if args.with_mcp:
        if not setup_mcp_server(project_path):
            print("⚠️  WARNING: MCP setup failed, but rules were created successfully")

    print(f"\n{'='*60}")
    print(f"✅ SUCCESS: Cline rules generated!")
    print(f"{'='*60}")
    print(f"\nNext steps:")
    print(f"1. Open project in VS Code: code {project_path}")
    print(f"2. Install Cline extension (if not already)")
    print(f"3. Reload VS Code window: Cmd+Shift+P → 'Reload Window'")
    print(f"4. Open Cline panel (sidebar icon)")
    print(f"5. Start autonomous task:")
    print(f"   'Create a Django blog app with posts and comments'")

    if args.with_mcp:
        print(f"\n📡 MCP Server configured at:")
        print(f"   {project_path / '.vscode' / 'mcp_config.json'}")
        print(f"   Load in Cline: Settings → MCP Servers → Load Configuration")

    return 0


if __name__ == "__main__":
    sys.exit(main())
