#!/usr/bin/env python3
"""
Agent Structure Validation
Validates agent files for structural compliance and best practices.
"""

import os
import sys
import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Standard Claude Code tools
STANDARD_TOOLS = {'Task', 'Bash', 'Read', 'Write', 'Grep', 'SlashCommand'}
STANDARD_MODELS = {'opus', 'sonnet', 'haiku'}

def parse_yaml_frontmatter(content: str) -> Tuple[Dict, str]:
    """Parse YAML frontmatter from markdown content"""
    if not content.startswith('---'):
        raise ValueError("Missing YAML frontmatter (must start with ---)")

    parts = content.split('---', 2)
    if len(parts) < 3:
        raise ValueError("Invalid YAML frontmatter format")

    try:
        # Simple YAML parsing without external library
        yaml_content = parts[1].strip()
        metadata = {}
        current_list_key = None

        for line in yaml_content.split('\n'):
            line = line.rstrip()
            if not line or line.startswith('#'):
                continue

            # Handle list items (start with - or spaces followed by -)
            if line.lstrip().startswith('-'):
                item = line.lstrip('- ').strip()
                if current_list_key:
                    metadata[current_list_key].append(item)
                continue

            # Handle key-value pairs
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # Check if this is a list header (next lines will be list items)
                if not value or value == '':
                    current_list_key = key
                    metadata[key] = []
                else:
                    current_list_key = None
                    # Clean up quotes and special characters
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    metadata[key] = value

        body = parts[2].strip()
        return metadata, body
    except Exception as e:
        raise ValueError(f"YAML parsing error: {e}")

def validate_metadata(metadata: Dict) -> List[str]:
    """Validate YAML metadata"""
    errors = []

    # Required fields
    required_fields = ['name', 'description', 'tools']
    for field in required_fields:
        if field not in metadata:
            errors.append(f"Missing required field: {field}")

    # Name validation
    if 'name' in metadata:
        name = metadata['name']
        if not isinstance(name, str) or not name.strip():
            errors.append("Name must be a non-empty string")
        elif not name.replace('-', '').replace('_', '').isalnum():
            errors.append("Name should contain only letters, numbers, hyphens, and underscores")

    # Description validation
    if 'description' in metadata:
        desc = metadata['description']
        if not isinstance(desc, str) or not desc.strip():
            errors.append("Description must be a non-empty string")
        elif len(desc) > 200:
            errors.append("Description should be under 200 characters")

    # Model validation
    if 'model' in metadata:
        model = metadata['model']
        if model not in STANDARD_MODELS:
            errors.append(f"Model must be one of: {', '.join(STANDARD_MODELS)}")

    # Tools validation
    if 'tools' in metadata:
        tools = metadata['tools']
        if not isinstance(tools, list):
            errors.append("Tools must be a list")
        else:
            for tool in tools:
                if tool not in STANDARD_TOOLS:
                    errors.append(f"Unknown tool: {tool}. Available: {', '.join(STANDARD_TOOLS)}")

    # Tags validation
    if 'tags' in metadata:
        tags = metadata['tags']
        if not isinstance(tags, list):
            errors.append("Tags must be a list")
        else:
            for tag in tags:
                if not isinstance(tag, str) or not tag.strip():
                    errors.append("All tags must be non-empty strings")

    return errors

def validate_system_prompt(body: str) -> List[str]:
    """Validate system prompt content"""
    errors = []

    if not body.strip():
        errors.append("System prompt cannot be empty")
        return errors

    # Check for essential sections
    required_sections = ["System Prompt"]
    for section in required_sections:
        if section not in body:
            errors.append(f"Missing required section: {section}")

    # Check for placeholder text
    placeholders = ["[Your prompt here]", "TODO:", "XXX", "PLACEHOLDER"]
    body_lower = body.lower()
    for placeholder in placeholders:
        if placeholder.lower() in body_lower:
            errors.append(f"Contains placeholder text: {placeholder}")

    return errors

def validate_agent_structure(file_path: str) -> List[str]:
    """Complete agent structure validation"""
    errors = []

    # File existence
    path = Path(file_path)
    if not path.exists():
        errors.append(f"File does not exist: {file_path}")
        return errors

    if not path.suffix == '.md':
        errors.append("Agent files must have .md extension")

    # File content
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        errors.append(f"Error reading file: {e}")
        return errors

    # Check file size (should be reasonable)
    if len(content) > 50000:  # 50KB limit
        errors.append("Agent file too large (>50KB). Consider splitting content.")

    # Parse and validate
    try:
        metadata, body = parse_yaml_frontmatter(content)
        errors.extend(validate_metadata(metadata))
        errors.extend(validate_system_prompt(body))
    except ValueError as e:
        errors.append(str(e))

    return errors

def suggest_fixes(errors: List[str]) -> List[str]:
    """Suggest fixes for common errors"""
    suggestions = []

    for error in errors:
        if "Missing required field" in error:
            field = error.split(":")[-1]
            if field == "name":
                suggestions.append("Add: name: my-agent")
            elif field == "description":
                suggestions.append("Add: description: Brief description of agent's purpose")
            elif field == "tools":
                suggestions.append("Add: tools:\\n  - Task\\n  - Read")

        elif "Missing YAML frontmatter" in error:
            suggestions.append("Add YAML frontmatter at the top:\\n---\\nname: my-agent\\ndescription: ...\\ntools:\\n  - Task\\n---")

        elif "Unknown tool" in error:
            suggestions.append(f"Use only standard tools: {', '.join(STANDARD_TOOLS)}")

        elif "Name should contain only" in error:
            suggestions.append("Use names like: security-analyst, code-reviewer, orchestrator")

        elif "System prompt cannot be empty" in error:
            suggestions.append("Add a detailed system prompt describing the agent's role and capabilities")

    return suggestions

def main():
    parser = argparse.ArgumentParser(description="Validate agent file structure")
    parser.add_argument("--file", required=True, help="Path to agent file")
    parser.add_argument("--fix", action="store_true", help="Suggest fixes for errors")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Validate
    errors = validate_agent_structure(args.file)

    # Output
    if args.json:
        output = {
            "file": args.file,
            "valid": len(errors) == 0,
            "errors": errors,
            "suggestions": suggest_fixes(errors) if args.fix else []
        }
        print(json.dumps(output, indent=2))
    else:
        if len(errors) == 0:
            print(f"✅ {args.file}: Valid agent structure")
        else:
            print(f"❌ {args.file}: {len(errors)} validation error(s)")
            print("\nErrors:")
            for error in errors:
                print(f"  • {error}")

            if args.fix:
                print("\nSuggested fixes:")
                for suggestion in suggest_fixes(errors):
                    print(f"  • {suggestion}")

        sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()