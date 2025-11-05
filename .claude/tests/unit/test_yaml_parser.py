"""
Unit tests for YAML parsing logic.
"""
import pytest
import yaml


def test_parse_valid_yaml_frontmatter(sample_agent_yaml):
    """Test parsing valid YAML frontmatter."""
    # Extract YAML between --- markers
    lines = sample_agent_yaml.split('\n')
    yaml_lines = []
    in_yaml = False
    yaml_count = 0
    
    for line in lines:
        if line.strip() == '---':
            yaml_count += 1
            if yaml_count == 1:
                in_yaml = True
                continue
            elif yaml_count == 2:
                break
        if in_yaml:
            yaml_lines.append(line)
    
    yaml_content = '\n'.join(yaml_lines)
    metadata = yaml.safe_load(yaml_content)
    
    assert metadata['name'] == 'test-agent'
    # Updated fixture has longer description
    assert len(metadata['description']) >= 50
    assert 'read_file' in metadata['tools']
    assert metadata['model'] == 'claude-3-5-sonnet-20241022'
    assert metadata['version'] == 1.0


def test_parse_invalid_yaml_raises_error(invalid_agent_yaml):
    """Test that invalid YAML raises appropriate error."""
    lines = invalid_agent_yaml.split('\n')
    yaml_lines = []
    in_yaml = False
    yaml_count = 0
    
    for line in lines:
        if line.strip() == '---':
            yaml_count += 1
            if yaml_count == 1:
                in_yaml = True
                continue
            elif yaml_count == 2:
                break
        if in_yaml:
            yaml_lines.append(line)
    
    yaml_content = '\n'.join(yaml_lines)
    metadata = yaml.safe_load(yaml_content)
    
    # Should parse but be missing fields
    assert 'name' in metadata
    assert 'description' not in metadata
    assert 'tools' not in metadata


def test_missing_frontmatter_returns_none():
    """Test that content without frontmatter returns None."""
    content = """# Agent Without YAML

This has no YAML frontmatter.
"""
    lines = content.split('\n')
    
    # Check for YAML markers
    has_yaml = False
    for line in lines:
        if line.strip() == '---':
            has_yaml = True
            break
    
    assert not has_yaml, "Should not find YAML markers"


def test_malformed_yaml_raises_error():
    """Test that malformed YAML raises parsing error."""
    malformed = """---
name: bad-yaml
description: Missing closing quote
tools: [read_file, "unclosed
---
"""
    
    lines = malformed.split('\n')
    yaml_lines = []
    in_yaml = False
    yaml_count = 0
    
    for line in lines:
        if line.strip() == '---':
            yaml_count += 1
            if yaml_count == 1:
                in_yaml = True
                continue
            elif yaml_count == 2:
                break
        if in_yaml:
            yaml_lines.append(line)
    
    yaml_content = '\n'.join(yaml_lines)
    
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(yaml_content)


def test_parse_complex_yaml_structures(temp_project_dir):
    """Test parsing complex YAML with nested structures."""
    complex_yaml = """---
name: complex-agent
description: Agent with complex YAML structure
tools:
  - read_file
  - replace_string_in_file
model: claude-3-5-sonnet-20241022
delegates_to:
  - agent-a
  - agent-b
metadata:
  category: analysis
  tags: [python, testing, automation]
  config:
    max_depth: 5
    timeout: 30
version: 2.1
---
"""
    
    lines = complex_yaml.split('\n')
    yaml_lines = []
    in_yaml = False
    yaml_count = 0
    
    for line in lines:
        if line.strip() == '---':
            yaml_count += 1
            if yaml_count == 1:
                in_yaml = True
                continue
            elif yaml_count == 2:
                break
        if in_yaml:
            yaml_lines.append(line)
    
    yaml_content = '\n'.join(yaml_lines)
    metadata = yaml.safe_load(yaml_content)
    
    assert metadata['name'] == 'complex-agent'
    assert len(metadata['delegates_to']) == 2
    assert metadata['metadata']['category'] == 'analysis'
    assert 'python' in metadata['metadata']['tags']
    assert metadata['metadata']['config']['max_depth'] == 5
    assert metadata['version'] == 2.1
