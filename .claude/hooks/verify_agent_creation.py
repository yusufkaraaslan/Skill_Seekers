#!/usr/bin/env python3
"""
Agent Creation Verification Hook
Ensures agent creation operations actually succeed and files are properly created.
This hook prevents the catastrophic failure that allowed /create-agent to report success without creating files.
"""

import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime, UTC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentCreationVerificationError(Exception):
    """Specific error for agent creation verification failures."""
    pass

def verify_agent_creation(agent_name: str, agent_path: str = None, expected_content_hash: str = None, operation_id: str = None) -> dict:
    """
    Comprehensive verification that agent creation actually succeeded.
    This is the critical verification that was missing from the original system.
    """

    logger.info(f"Starting agent creation verification: {agent_name}")

    verification_result = {
        "agent_name": agent_name,
        "operation_id": operation_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "verification_passed": False,
        "checks": {},
        "errors": []
    }

    try:
        # Check 1: Agent name validation
        if not agent_name or not agent_name.strip():
            raise AgentCreationVerificationError("Agent name cannot be empty")

        verification_result["checks"]["name_valid"] = True

        # Check 2: Determine agent path if not provided
        if not agent_path:
            agent_path = f".claude/agents/{agent_name}.md"

        agent_file = Path(agent_path)
        verification_result["checks"]["path_determined"] = True
        verification_result["agent_path"] = str(agent_file)

        # Check 3: File existence verification (CRITICAL)
        if not agent_file.exists():
            raise AgentCreationVerificationError(f"Agent file does not exist: {agent_file}")

        verification_result["checks"]["file_exists"] = True
        verification_result["file_size"] = agent_file.stat().st_size

        # Check 4: File is not empty
        if agent_file.stat().st_size == 0:
            raise AgentCreationVerificationError(f"Agent file is empty: {agent_file}")

        verification_result["checks"]["file_not_empty"] = True

        # Check 5: Content verification
        try:
            content = agent_file.read_text(encoding='utf-8')
            if not content.strip():
                raise AgentCreationVerificationError("Agent file content is empty")

            verification_result["checks"]["content_readable"] = True
            verification_result["content_length"] = len(content)

        except UnicodeDecodeError as e:
            raise AgentCreationVerificationError(f"Agent file content is not valid UTF-8: {e}")

        # Check 6: Content hash verification (if provided)
        if expected_content_hash:
            actual_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            if actual_hash != expected_content_hash:
                raise AgentCreationVerificationError(
                    f"Content hash mismatch. Expected: {expected_content_hash[:16]}..., Got: {actual_hash[:16]}..."
                )

            verification_result["checks"]["content_hash_match"] = True
            verification_result["content_hash"] = actual_hash
        else:
            # Generate hash for record keeping
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            verification_result["content_hash"] = content_hash
            verification_result["checks"]["content_hash_generated"] = True

        # Check 7: Basic markdown structure verification
        required_markdown_elements = ["#", "##", "###"]
        missing_elements = [elem for elem in required_markdown_elements if elem not in content]

        if missing_elements:
            raise AgentCreationVerificationError(f"Missing markdown elements: {missing_elements}")

        verification_result["checks"]["markdown_structure"] = True

        # Check 8: YAML frontmatter verification (if present)
        if content.startswith('---'):
            try:
                import yaml
                frontmatter_end = content.find('---', 3)
                if frontmatter_end == -1:
                    raise AgentCreationVerificationError("Invalid YAML frontmatter - missing closing ---")

                frontmatter = content[3:frontmatter_end].strip()
                yaml_data = yaml.safe_load(frontmatter)

                if not yaml_data:
                    raise AgentCreationVerificationError("YAML frontmatter is empty or invalid")

                # Check for required fields
                required_fields = ["name", "description"]
                missing_fields = [field for field in required_fields if field not in yaml_data]

                if missing_fields:
                    raise AgentCreationVerificationError(f"Missing YAML fields: {missing_fields}")

                verification_result["checks"]["yaml_frontmatter"] = True
                verification_result["yaml_fields"] = list(yaml_data.keys())

            except ImportError:
                verification_result["checks"]["yaml_frontmatter"] = "yaml_not_available"
                logger.warning("PyYAML not available for YAML frontmatter validation")
            except Exception as e:
                raise AgentCreationVerificationError(f"YAML frontmatter validation failed: {e}")

        # Check 9: Registry verification
        registry_path = Path(".claude/skills/agent-scaffolding-toolkit/assets/agent_registry.json")
        if registry_path.exists():
            try:
                registry_data = json.loads(registry_path.read_text(encoding='utf-8'))

                if "agents" in registry_data and agent_name in registry_data["agents"]:
                    agent_info = registry_data["agents"][agent_name]

                    # Verify registry entry matches file
                    if agent_info.get("file_path") != str(agent_file):
                        raise AgentCreationVerificationError(
                            f"Registry file path mismatch: {agent_info.get('file_path')} vs {agent_file}"
                        )

                    verification_result["checks"]["registry_entry"] = True
                    verification_result["registry_info"] = agent_info
                else:
                    verification_result["checks"]["registry_entry"] = "missing"
                    logger.warning(f"Agent {agent_name} not found in registry")

            except Exception as e:
                verification_result["checks"]["registry_entry"] = f"error: {e}"
                logger.warning(f"Registry verification failed: {e}")
        else:
            verification_result["checks"]["registry_entry"] = "no_registry"

        # Check 10: Agent discoverability
        agents_dir = Path(".claude/agents")
        agent_files = list(agents_dir.glob("*.md"))

        if agent_file not in agent_files:
            raise AgentCreationVerificationError(f"Agent file not discoverable in agents directory")

        verification_result["checks"]["discoverable"] = True
        verification_result["total_agents"] = len(agent_files)

        # All checks passed
        verification_result["verification_passed"] = True
        verification_result["verification_time"] = datetime.now(UTC).isoformat()

        logger.info(f"Agent creation verification PASSED: {agent_name}")

    except Exception as e:
        verification_result["verification_passed"] = False
        verification_result["errors"].append(str(e))
        verification_result["failure_time"] = datetime.now(UTC).isoformat()

        logger.error(f"Agent creation verification FAILED: {agent_name} - {e}")

        # Don't raise exception - return failure result for calling system to handle

    return verification_result

def main():
    """CLI interface for agent creation verification."""
    if len(sys.argv) < 2:
        print("Usage: python3 verify_agent_creation.py <agent_name> [agent_path] [content_hash] [operation_id]")
        sys.exit(1)

    agent_name = sys.argv[1]
    agent_path = sys.argv[2] if len(sys.argv) > 2 else None
    expected_content_hash = sys.argv[3] if len(sys.argv) > 3 else None
    operation_id = sys.argv[4] if len(sys.argv) > 4 else None

    try:
        result = verify_agent_creation(
            agent_name=agent_name,
            agent_path=agent_path,
            expected_content_hash=expected_content_hash,
            operation_id=operation_id
        )

        # Output result as JSON for programmatic consumption
        print(json.dumps(result, indent=2))

        # Exit with appropriate code
        sys.exit(0 if result["verification_passed"] else 1)

    except Exception as e:
        logger.error(f"Verification script failed: {e}")
        print(json.dumps({
            "error": str(e),
            "verification_passed": False,
            "timestamp": datetime.now(UTC).isoformat()
        }, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()