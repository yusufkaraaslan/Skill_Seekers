#!/usr/bin/env python3
"""
PreToolUse Hook: Check Agent Behavior (Quick Syntax Validation)

Runs before Write/Edit operations to perform quick syntax checks.
This is a lightweight pre-flight check; full validation happens in PostToolUse.
"""

import json
import sys
import os
import re
from pathlib import Path

def is_agent_file(file_path):
    """Check if file is an agent definition."""
    return file_path.endswith(".md") and "/.claude/agents/" in file_path

def quick_syntax_check(file_path):
    """Perform quick YAML frontmatter syntax check."""
    try:
        if not os.path.exists(file_path):
            # File doesn't exist yet (new creation) - skip
            return True, None
        
        with open(file_path) as f:
            content = f.read()
        
        # Check for YAML frontmatter
        if not content.startswith("---"):
            return False, "Agent files must start with YAML frontmatter (---)"
        
        # Quick regex check for basic structure
        parts = content.split("---", 2)
        if len(parts) < 3:
            return False, "Invalid YAML frontmatter structure (missing closing ---)"
        
        frontmatter = parts[1]
        
        # Check for required fields (basic regex - not full YAML parse)
        required = ["name:", "type:", "description:"]
        for field in required:
            if field not in frontmatter:
                return False, f"Missing required field in frontmatter: {field.replace(':', '')}"
        
        return True, None
        
    except Exception as e:
        return False, f"Syntax check error: {e}"

def main():
    """Main entry point for PreToolUse hook."""
    try:
        # Read hook input
        input_data = json.load(sys.stdin)
        
        tool_input = input_data.get("tool_input", {})
        file_path = tool_input.get("file_path", "")
        
        # Only validate agent files
        if not is_agent_file(file_path):
            sys.exit(0)  # Not an agent file - skip
        
        # Perform quick syntax check
        is_valid, error_msg = quick_syntax_check(file_path)
        
        if not is_valid:
            print(f"⚠️  Quick syntax check failed: {error_msg}", file=sys.stderr)
            print("Proceeding to PostToolUse for full validation...", file=sys.stderr)
            # Don't block here - let PostToolUse handle it
            sys.exit(0)
        
        # Valid - continue
        sys.exit(0)
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(0)  # Don't block on hook errors
    except Exception as e:
        print(f"PreToolUse hook error: {e}", file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()
