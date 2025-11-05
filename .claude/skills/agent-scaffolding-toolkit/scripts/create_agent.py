#!/usr/bin/env python3
"""
Interactive Agent Creation Wizard
Creates specialized agents with battle-tested templates in 60 seconds.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# Add templates path
TEMPLATES_DIR = Path(__file__).parent.parent / "assets" / "templates"
# Hardcode absolute path to prevent nested .claude folder creation
AGENTS_DIR = Path("/Users/docravikumar/Code/skill-test/SKILL_SEEKERS/.claude/agents")

def load_template(template_type: str) -> Dict:
    """Load template configuration"""
    template_file = TEMPLATES_DIR / "agents" / f"{template_type}.json"
    if not template_file.exists():
        available = [f.stem for f in TEMPLATES_DIR.glob("agents/*.json")]
        raise ValueError(f"Template '{template_type}' not found. Available: {available}")

    with open(template_file, 'r') as f:
        return json.load(f)

def interactive_wizard() -> Dict:
    """Interactive agent creation wizard"""
    print("🎯 Agent Creation Wizard")
    print("=" * 40)

    # Load available templates
    templates = {f.stem: load_template(f.stem) for f in TEMPLATES_DIR.glob("agents/*.json")}

    print("\n1️⃣  Select Agent Type:")
    for i, (name, template) in enumerate(templates.items(), 1):
        print(f"   {i}. {template['display_name']} - {template['description']}")

    while True:
        try:
            choice = input(f"\nSelect (1-{len(templates)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(templates):
                template_name = list(templates.keys())[idx]
                template = templates[template_name]
                break
            print("❌ Invalid selection. Try again.")
        except ValueError:
            print("❌ Please enter a number.")

    print(f"\n✅ Selected: {template['display_name']}")

    # Agent Configuration
    config = {
        'name': '',
        'description': '',
        'model': template.get('default_model', 'sonnet'),
        'tools': template['default_tools'].copy(),
        'tags': template['default_tags'].copy(),
        'customizations': {}
    }

    # Name
    while not config['name'].strip():
        config['name'] = input("\n2️⃣  Agent name (e.g., security-analyst): ").strip().lower().replace(' ', '-')
        if not config['name']:
            print("❌ Name is required.")

    # Description
    while not config['description'].strip():
        print("\n3️⃣  Agent description (one sentence):")
        config['description'] = input("> ").strip()
        if not config['description']:
            print("❌ Description is required.")

    # Model selection
    print(f"\n4️⃣  Model selection (default: {config['model']}):")
    print("   opus - Maximum reasoning (expensive)")
    print("   sonnet - Balanced performance")
    print("   haiku - Fast, cost-effective")

    model_choice = input("Model (or press Enter for default): ").strip().lower()
    if model_choice in ['opus', 'sonnet', 'haiku']:
        config['model'] = model_choice

    # Tools selection
    print(f"\n5️⃣  Tool selection (default: {', '.join(config['tools'])}):")
    available_tools = ['Task', 'Bash', 'Read', 'Grep', 'Write', 'SlashCommand']

    print("Available tools:")
    for tool in available_tools:
        status = "✅" if tool in config['tools'] else "⬜"
        print(f"   {status} {tool}")

    tools_input = input("Add/remove tools (e.g., '+Write -Task' or press Enter): ").strip()
    if tools_input:
        for change in tools_input.split():
            if change.startswith('+') and change[1:] in available_tools:
                config['tools'].append(change[1:])
            elif change.startswith('-') and change[1:] in config['tools']:
                config['tools'].remove(change[1:])

    # Tags
    print(f"\n6️⃣  Tags (default: {', '.join(config['tags'])}):")
    tags_input = input("Additional tags (comma-separated): ").strip()
    if tags_input:
        config['tags'].extend([tag.strip() for tag in tags_input.split(',') if tag.strip()])

    # Customizations
    print("\n7️⃣  Customizations (optional):")
    for key, prompt in template.get('customization_prompts', {}).items():
        value = input(f"{prompt} (press Enter to skip): ").strip()
        if value:
            config['customizations'][key] = value

    return template_name, config

def generate_agent_file(template_name: str, config: Dict) -> str:
    """Generate the agent markdown file"""
    template = load_template(template_name)

    # YAML frontmatter
    yaml_content = [
        "---",
        f"name: {config['name']}",
        f"description: {config['description']}",
        f"model: {config['model']}",
        "tools:",
    ]

    for tool in sorted(config['tools']):
        yaml_content.append(f"  - {tool}")

    if config['tags']:
        yaml_content.extend([
            "tags:",
        ])
        for tag in sorted(config['tags']):
            yaml_content.append(f"  - {tag}")

    yaml_content.append("---")

    # System prompt
    # Handle template formatting with fallback for missing parameters
    format_params = {
        'name': config['name'],
        'description': config['description'],
        'customizations': ''
    }
    format_params.update(config['customizations'])

    try:
        system_prompt = template['system_prompt_template'].format(**format_params)
    except KeyError as e:
        print(f"⚠️  Missing template parameter: {e}")
        print("Using basic template without customizations...")
        # Fallback to basic template
        basic_template = "You are {name}, {description}."
        system_prompt = basic_template.format(**format_params)

    return "\n".join(yaml_content) + "\n\n### 🎓 System Prompt: " + config['name'].title().replace('-', ' ') + "\n\n" + system_prompt

def create_agent_file(template_name: str, config: Dict) -> str:
    """Create the agent file"""
    # DO NOT create directories - use existing structure
    # The .claude/agents directory should already exist

    # Generate content
    content = generate_agent_file(template_name, config)

    # Write file
    agent_file = AGENTS_DIR / f"{config['name']}.md"

    if agent_file.exists():
        overwrite = input(f"⚠️  Agent '{config['name']}' already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("❌ Agent creation cancelled.")
            return str(agent_file)

    with open(agent_file, 'w') as f:
        f.write(content)

    print(f"✅ Agent created: {agent_file}")
    return str(agent_file)

def main():
    parser = argparse.ArgumentParser(description="Create specialized agents with interactive wizard")
    parser.add_argument("--template", help="Template type (orchestrator, referee, specialist)")
    parser.add_argument("--name", help="Agent name")
    parser.add_argument("--description", help="Agent description")
    parser.add_argument("--model", choices=["opus", "sonnet", "haiku"], help="Model selection")
    parser.add_argument("--tools", help="Tools (comma-separated)")
    parser.add_argument("--non-interactive", action="store_true", help="Non-interactive mode")

    args = parser.parse_args()

    if args.non_interactive and not all([args.template, args.name, args.description]):
        print("❌ Non-interactive mode requires --template, --name, and --description")
        sys.exit(1)

    try:
        if args.non_interactive:
            # Non-interactive mode
            template_name = args.template
            config = {
                'name': args.name,
                'description': args.description,
                'model': args.model or 'sonnet',
                'tools': args.tools.split(',') if args.tools else ['Task', 'Read'],
                'tags': [],
                'customizations': {}
            }
        else:
            # Interactive wizard
            template_name, config = interactive_wizard()

        # Create agent file
        agent_path = create_agent_file(template_name, config)

        # Validate
        print("\n🔍 Validating agent structure...")
        import subprocess
        result = subprocess.run([sys.executable, "validate_agent.py", "--file", agent_path],
                              capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Agent validation passed!")
            print(f"\n🚀 Ready to use: @{config['name']}")
        else:
            print("⚠️  Validation warnings:")
            print(result.stderr)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()