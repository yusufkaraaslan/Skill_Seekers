#!/usr/bin/env python3
"""
Template Discovery and Listing
Lists all available agent, skill, and command templates.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List

TEMPLATES_DIR = Path(__file__).parent.parent / "assets" / "templates"

def load_template_info(template_path: Path) -> Dict:
    """Load template information"""
    try:
        with open(template_path, 'r') as f:
            data = json.load(f)
        return {
            'file': template_path.name,
            'type': template_path.parent.name,
            'display_name': data.get('display_name', template_path.stem),
            'description': data.get('description', 'No description'),
            'default_model': data.get('default_model', 'sonnet'),
            'default_tools': data.get('default_tools', []),
            'default_tags': data.get('default_tags', []),
            'use_cases': data.get('use_cases', [])
        }
    except Exception as e:
        return {
            'file': template_path.name,
            'type': template_path.parent.name,
            'error': str(e)
        }

def list_templates(template_type: str = None) -> List[Dict]:
    """List all templates or specific type"""
    templates = []

    if template_type:
        template_dir = TEMPLATES_DIR / template_type
        if not template_dir.exists():
            return []

        for template_file in template_dir.glob("*.json"):
            templates.append(load_template_info(template_file))
    else:
        for template_dir in TEMPLATES_DIR.iterdir():
            if template_dir.is_dir():
                for template_file in template_dir.glob("*.json"):
                    templates.append(load_template_info(template_file))

    return sorted(templates, key=lambda x: (x['type'], x['display_name']))

def print_template_table(templates: List[Dict], detailed: bool = False):
    """Print templates in table format"""
    if not templates:
        print("No templates found.")
        return

    # Group by type
    by_type = {}
    for template in templates:
        if 'error' in template:
            continue
        if template['type'] not in by_type:
            by_type[template['type']] = []
        by_type[template['type']].append(template)

    for template_type, type_templates in by_type.items():
        print(f"\n📁 {template_type.title()} Templates:")
        print("=" * 60)

        if detailed:
            for template in type_templates:
                print(f"\n🎯 {template['display_name']}")
                print(f"   File: {template['file']}")
                print(f"   Description: {template['description']}")
                print(f"   Default Model: {template['default_model']}")
                print(f"   Default Tools: {', '.join(template['default_tools']) or 'None'}")
                print(f"   Tags: {', '.join(template['default_tags']) or 'None'}")
                if template['use_cases']:
                    print(f"   Use Cases:")
                    for use_case in template['use_cases']:
                        print(f"     • {use_case}")
        else:
            # Compact table
            max_name = max(len(t['display_name']) for t in type_templates)
            max_desc = max(len(t['description'][:50]) for t in type_templates)

            print(f"{'Name':<{max_name}} {'Description':<{max_desc}} Model   Tools")
            print("-" * (max_name + max_desc + 20))
            for template in type_templates:
                name = template['display_name'][:max_name]
                desc = template['description'][:max_desc]
                tools = len(template['default_tools'])
                print(f"{name:<{max_name}} {desc:<{max_desc}} {template['default_model']:<7} {tools}")

def get_template_details(template_name: str) -> Dict:
    """Get detailed information about a specific template"""
    for template_dir in TEMPLATES_DIR.iterdir():
        if template_dir.is_dir():
            for template_file in template_dir.glob(f"{template_name}.json"):
                return load_template_info(template_file)
    return {}

def main():
    parser = argparse.ArgumentParser(description="List available templates")
    parser.add_argument("--type", choices=["agents", "skills", "commands"], help="Filter by template type")
    parser.add_argument("--detailed", action="store_true", help="Show detailed information")
    parser.add_argument("--template", help="Show details for specific template")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.template:
        # Show specific template details
        template = get_template_details(args.template)
        if not template:
            print(f"❌ Template '{args.template}' not found.")
            sys.exit(1)

        if args.json:
            print(json.dumps(template, indent=2))
        else:
            print(f"🎯 {template['display_name']}")
            print(f"Type: {template['type']}")
            print(f"File: {template['file']}")
            print(f"Description: {template['description']}")
            if 'error' in template:
                print(f"❌ Error: {template['error']}")
            else:
                print(f"Default Model: {template['default_model']}")
                print(f"Default Tools: {', '.join(template['default_tools'])}")
                print(f"Default Tags: {', '.join(template['default_tags'])}")
                if template.get('use_cases'):
                    print("\nUse Cases:")
                    for use_case in template['use_cases']:
                        print(f"  • {use_case}")
    else:
        # List templates
        templates = list_templates(args.type)

        if args.json:
            print(json.dumps(templates, indent=2))
        else:
            print("🎯 Available Templates")
            if args.type:
                print(f"Filter: {args.type}")
            print(f"Found: {len(templates)} templates")

            print_template_table(templates, args.detailed)

            print(f"\n💡 Use --template <name> for details, or --detailed for more information")

if __name__ == "__main__":
    main()