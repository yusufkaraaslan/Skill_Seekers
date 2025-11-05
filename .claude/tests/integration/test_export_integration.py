"""
Tests for Skill Seekers export functionality.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_export_single_agent_to_skill(temp_project_dir, create_agent_file, sample_agent_yaml):
    """Test exporting a single agent to SKILL.md format."""
    # Create agent
    agent_path = create_agent_file("export-test", sample_agent_yaml.replace("test-agent", "export-test"))
    
    # Create output directory
    output_dir = temp_project_dir / "output" / "agent-skills"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run export script
    export_script = (
        Path(__file__).parent.parent.parent / "skills" / 
        "agent-scaffolding-toolkit" / "scripts" / "export_to_skill_seekers.py"
    )
    
    result = subprocess.run(
        [
            sys.executable,
            str(export_script),
            "--agents-dir", str(temp_project_dir / ".claude" / "agents"),
            "--output-dir", str(output_dir),
            "--format", "skill"
        ],
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    # Verify export succeeded
    assert result.returncode == 0, f"Export failed: {result.stderr}"
    
    # Verify SKILL.md created
    skill_path = output_dir / "export-test" / "SKILL.md"
    assert skill_path.exists(), "SKILL.md not created"
    
    # Verify SKILL.md content
    skill_content = skill_path.read_text()
    assert "export-test" in skill_content
    assert "Version:" in skill_content
    assert "When to Use This Skill" in skill_content


def test_export_agent_to_config(temp_project_dir, create_agent_file, sample_agent_yaml):
    """Test exporting agent to Skill Seekers config format."""
    agent_path = create_agent_file("config-test", sample_agent_yaml.replace("test-agent", "config-test"))
    
    output_dir = temp_project_dir / "output" / "agent-skills"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    export_script = (
        Path(__file__).parent.parent.parent / "skills" / 
        "agent-scaffolding-toolkit" / "scripts" / "export_to_skill_seekers.py"
    )
    
    result = subprocess.run(
        [
            sys.executable,
            str(export_script),
            "--agents-dir", str(temp_project_dir / ".claude" / "agents"),
            "--output-dir", str(output_dir),
            "--format", "config"
        ],
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    assert result.returncode == 0
    
    # Verify config created
    config_path = output_dir / "config-test" / "config-test.json"
    assert config_path.exists(), "Config file not created"
    
    # Verify config content
    config = json.loads(config_path.read_text())
    assert config['name'] == 'config-test'
    assert config['type'] == 'claude_code_agent'
    assert 'metadata' in config
    assert 'tools' in config['metadata']


def test_export_preserves_agent_definition(temp_project_dir, create_agent_file, sample_agent_yaml):
    """Test that export preserves original agent definition."""
    agent_path = create_agent_file("preserve-test", sample_agent_yaml.replace("test-agent", "preserve-test"))
    
    output_dir = temp_project_dir / "output" / "agent-skills"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    export_script = (
        Path(__file__).parent.parent.parent / "skills" / 
        "agent-scaffolding-toolkit" / "scripts" / "export_to_skill_seekers.py"
    )
    
    result = subprocess.run(
        [
            sys.executable,
            str(export_script),
            "--agents-dir", str(temp_project_dir / ".claude" / "agents"),
            "--output-dir", str(output_dir)
        ],
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    assert result.returncode == 0
    
    # Verify agent_definition.md created
    agent_def_path = output_dir / "preserve-test" / "agent_definition.md"
    assert agent_def_path.exists()
    
    # Verify it matches original
    assert agent_def_path.read_text() == agent_path.read_text()


def test_export_detects_conflicts(temp_project_dir, create_agent_file, sample_agent_yaml):
    """Test conflict detection during export."""
    # Create existing skill directory
    output_dir = temp_project_dir / "output" / "agent-skills"
    existing_skill = output_dir / "conflict-test"
    existing_skill.mkdir(parents=True, exist_ok=True)
    (existing_skill / "SKILL.md").write_text("Existing skill")
    
    # Create agent with same name
    agent_path = create_agent_file("conflict-test", sample_agent_yaml.replace("test-agent", "conflict-test"))
    
    export_script = (
        Path(__file__).parent.parent.parent / "skills" / 
        "agent-scaffolding-toolkit" / "scripts" / "export_to_skill_seekers.py"
    )
    
    result = subprocess.run(
        [
            sys.executable,
            str(export_script),
            "--agents-dir", str(temp_project_dir / ".claude" / "agents"),
            "--output-dir", str(output_dir),
            "--detect-conflicts"
        ],
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    # Should complete but warn about conflicts
    assert "⚠️" in result.stdout or "conflict" in result.stdout.lower()


def test_export_delegation_tracking(temp_project_dir, create_agent_file):
    """Test that delegation relationships are tracked in export."""
    # Create base agent
    base_agent = """---
name: base-export
description: Base agent for export testing
tools: [read_file]
model: claude-3-5-sonnet-20241022
delegates_to: []
version: 1.0
---

# Base Export
"""
    
    # Create delegating agent
    delegating_agent = """---
name: delegating-export
description: Agent that delegates for export testing
tools: [replace_string_in_file]
model: claude-3-5-sonnet-20241022
delegates_to: [base-export]
version: 1.0
---

# Delegating Export
"""
    
    create_agent_file("base-export", base_agent)
    create_agent_file("delegating-export", delegating_agent)
    
    output_dir = temp_project_dir / "output" / "agent-skills"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    export_script = (
        Path(__file__).parent.parent.parent / "skills" / 
        "agent-scaffolding-toolkit" / "scripts" / "export_to_skill_seekers.py"
    )
    
    result = subprocess.run(
        [
            sys.executable,
            str(export_script),
            "--agents-dir", str(temp_project_dir / ".claude" / "agents"),
            "--output-dir", str(output_dir)
        ],
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(temp_project_dir)}
    )
    
    assert result.returncode == 0
    
    # Verify delegation in config
    config_path = output_dir / "delegating-export" / "delegating-export.json"
    config = json.loads(config_path.read_text())
    assert "base-export" in config['metadata']['delegates_to']
    
    # Verify delegation in SKILL.md
    skill_path = output_dir / "delegating-export" / "SKILL.md"
    skill_content = skill_path.read_text()
    assert "base-export" in skill_content
    assert "Delegation" in skill_content
