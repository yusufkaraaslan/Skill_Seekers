#!/usr/bin/env python3
"""
Standalone Agent Validator for Testing

This is a test-friendly version of validate-agent.py that accepts
file paths as command-line arguments instead of JSON input from stdin.

Usage:
    python3 validate-agent-standalone.py <agent_file_path>

Exit codes:
- 0: Valid agent
- 1: Internal error
- 2: Validation failed
"""

import sys
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Import validation logic from the main script
# (We'll duplicate it here for standalone usage)

# Claude Code native tools (as of 2025-11-04)
NATIVE_TOOLS = {
    "read_file", "write_file", "edit_file", "list_dir", "search_files",
    "grep_search", "run_command", "task", "browser", "mcp",
    "replace_string_in_file", "create_file", "run_in_terminal",
    "file_search", "semantic_search", "list_code_usages"
}

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
    required = ["name", "description", "tools", "model"]
    
    for field in required:
        if field not in frontmatter:
            errors.append(f"Missing required field: {field}")
    
    return errors

def validate_field_types(frontmatter: Dict[str, Any]) -> List[str]:
    """Validate field types."""
    errors = []
    
    if "name" in frontmatter and not isinstance(frontmatter["name"], str):
        errors.append("Field 'name' must be a string")
    
    if "description" in frontmatter:
        if not isinstance(frontmatter["description"], str):
            errors.append("Field 'description' must be a string")
        elif len(frontmatter["description"]) < 20:
            errors.append("Field 'description' must be at least 20 characters")
    
    if "tools" in frontmatter and not isinstance(frontmatter["tools"], list):
        errors.append("Field 'tools' must be a list")
    
    if "model" in frontmatter and not isinstance(frontmatter["model"], str):
        errors.append("Field 'model' must be a string")
    
    if "delegates_to" in frontmatter and not isinstance(frontmatter["delegates_to"], list):
        errors.append("Field 'delegates_to' must be a list")
    
    return errors

def validate_tools(frontmatter: Dict[str, Any]) -> List[str]:
    """Validate tools against known native tools."""
    errors = []
    
    tools = frontmatter.get("tools", [])
    if not tools:
        errors.append("Agent must specify at least one tool")
        return errors
    
    for tool in tools:
        if not isinstance(tool, str):
            errors.append(f"Tool must be a string, got: {type(tool).__name__}")
            continue
        
        if tool not in NATIVE_TOOLS:
            errors.append(f"Unknown tool: '{tool}' (not in Claude Code native tools)")
    
    return errors

def validate_security_patterns(body: str) -> List[str]:
    """Check for dangerous security patterns in agent body."""
    warnings = []
    
    dangerous_patterns = [
        ("rm -rf", "Dangerous: destructive file deletion command"),
        ("sudo", "Security concern: elevated privileges"),
        ("chmod 777", "Security concern: overly permissive file permissions"),
        ("eval(", "Security concern: code evaluation"),
        ("exec(", "Security concern: code execution"),
    ]
    
    for pattern, message in dangerous_patterns:
        if pattern in body:
            warnings.append(f"{message} found in agent body")
    
    return warnings

def validate_agent_file(file_path: str) -> Tuple[bool, List[str]]:
    """Validate an agent file."""
    errors = []
    
    # Check file exists
    if not os.path.exists(file_path):
        return False, [f"File not found: {file_path}"]
    
    # Read file
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except Exception as e:
        return False, [f"Failed to read file: {e}"]
    
    # Extract YAML frontmatter
    try:
        frontmatter, body = extract_yaml_frontmatter(content)
    except ValueError as e:
        return False, [str(e)]
    
    # Validate required fields
    errors.extend(validate_required_fields(frontmatter))
    
    # Validate field types
    errors.extend(validate_field_types(frontmatter))
    
    # Validate tools
    errors.extend(validate_tools(frontmatter))
    
    # Check for security patterns (warnings only)
    security_warnings = validate_security_patterns(body)
    for warning in security_warnings:
        print(f"⚠️  {warning}", file=sys.stderr)
    
    return len(errors) == 0, errors

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: validate-agent-standalone.py <agent_file_path>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        is_valid, errors = validate_agent_file(file_path)
        
        if not is_valid:
            print("❌ Agent validation failed:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            sys.exit(2)
        
        print(f"✅ Agent validation passed: {Path(file_path).name}")
        sys.exit(0)
        
    except Exception as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
