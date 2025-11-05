#!/usr/bin/env python3
"""
PostToolUse Hook: Validate Agent (Strict Validation)

Runs after Write/Edit operations to perform comprehensive agent validation.
This is the fallback for LLM-based validation in PostToolUse hooks.

Exit codes:
- 0: Valid agent, continue
- 1: Internal error, don't block
- 2: Validation failed, block with feedback to Claude
"""

import json
import sys
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Claude Code native tools (as of 2025-11-04)
NATIVE_TOOLS = {
    "read_file", "write_file", "edit_file", "list_dir", "search_files",
    "grep_search", "run_command", "task", "browser", "mcp",
    "create_file", "replace_string_in_file", "file_search", "semantic_search",
    "list_code_usages", "run_in_terminal", "get_errors"
}

def is_agent_file(file_path: str) -> bool:
    """Check if file is an agent definition."""
    return file_path.endswith(".md") and "/.claude/agents/" in file_path

def extract_yaml_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Extract and parse YAML frontmatter from markdown."""
    if not content.startswith("---"):
        raise ValueError("Agent files must start with YAML frontmatter (---)")
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Invalid YAML frontmatter structure (missing closing ---)")
    
    frontmatter_text = parts[1]
    body = parts[2].strip()
    
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML syntax: {e}")
    
    return frontmatter, body

def validate_required_fields(frontmatter: Dict[str, Any]) -> List[str]:
    """Validate required frontmatter fields."""
    errors = []
    
    required_fields = {
        "name": str,
        "type": str,
        "description": str
    }
    
    for field, expected_type in required_fields.items():
        if field not in frontmatter:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(frontmatter[field], expected_type):
            errors.append(f"Field '{field}' must be of type {expected_type.__name__}")
    
    return errors

def validate_description(description: str) -> List[str]:
    """Validate agent description quality."""
    errors = []
    
    if len(description) < 50:
        errors.append(f"Description too short ({len(description)} chars). Must be >= 50 characters to properly explain agent purpose.")
    
    if description.lower().startswith("this agent"):
        errors.append("Description should be actionable, not meta. Avoid starting with 'This agent...'")
    
    return errors

def validate_tools(tools: List[str]) -> List[str]:
    """Validate tool list against native tools."""
    errors = []
    warnings = []
    
    if not isinstance(tools, list):
        errors.append("Field 'tools' must be a list")
        return errors
    
    for tool in tools:
        if not isinstance(tool, str):
            errors.append(f"Tool '{tool}' must be a string")
            continue
        
        # Check if tool exists in native tools
        if tool not in NATIVE_TOOLS:
            warnings.append(f"Warning: Tool '{tool}' not found in Claude Code native tools. Verify this is correct.")
    
    return errors + warnings

def validate_delegation(delegates_to: List[str], agent_name: str) -> List[str]:
    """Validate agent delegation list."""
    errors = []
    
    if not isinstance(delegates_to, list):
        errors.append("Field 'delegates_to' must be a list")
        return errors
    
    # Check for self-delegation
    if agent_name in delegates_to:
        errors.append(f"Agent cannot delegate to itself: {agent_name}")
    
    # Check for circular delegation depth (basic check)
    if len(delegates_to) > 5:
        errors.append(f"Too many delegations ({len(delegates_to)}). Maximum recommended: 5 to avoid complexity.")
    
    return errors

def validate_agent_file(file_path: str) -> Tuple[bool, List[str]]:
    """
    Comprehensive agent validation.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        with open(file_path) as f:
            content = f.read()
    except Exception as e:
        return False, [f"Could not read file: {e}"]
    
    # Extract YAML frontmatter
    try:
        frontmatter, body = extract_yaml_frontmatter(content)
    except ValueError as e:
        return False, [str(e)]
    
    # Validate required fields
    errors.extend(validate_required_fields(frontmatter))
    
    # Validate description
    if "description" in frontmatter:
        errors.extend(validate_description(frontmatter["description"]))
    
    # Validate tools
    if "tools" in frontmatter:
        errors.extend(validate_tools(frontmatter["tools"]))
    
    # Validate delegation
    if "delegates_to" in frontmatter:
        agent_name = frontmatter.get("name", "unknown")
        errors.extend(validate_delegation(frontmatter["delegates_to"], agent_name))
    
    # Validate body content
    if len(body) < 100:
        errors.append(f"Agent body too short ({len(body)} chars). Provide examples and use cases (min 100 chars).")
    
    return len(errors) == 0, errors

def main():
    """Main entry point for PostToolUse validation hook."""
    try:
        # Read hook input
        input_data = json.load(sys.stdin)
        
        tool_input = input_data.get("tool_input", {})
        file_path = tool_input.get("file_path", "")
        
        # Only validate agent files
        if not is_agent_file(file_path):
            sys.exit(0)  # Not an agent file - skip
        
        # Perform validation
        is_valid, errors = validate_agent_file(file_path)
        
        if not is_valid:
            print("❌ Agent validation failed:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            sys.exit(2)  # Block with feedback to Claude
        
        # Valid - continue
        print(f"✅ Agent validation passed: {file_path}", file=sys.stderr)
        sys.exit(0)
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)  # Internal error - don't block
    except Exception as e:
        print(f"Validation hook error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
