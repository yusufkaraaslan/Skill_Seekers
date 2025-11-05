# /update-CLAUDE.md: Automatic Documentation Synchronization

Robust command that detects changes in agents, commands, skills, and project structure, then automatically updates CLAUDE.md to maintain documentation consistency.

## Usage

```bash
/update-CLAUDE.md [options]
```

**Options**:
- `--dry-run`: Show what would be updated without making changes
- `--agents-only`: Update only agent-related sections
- `--commands-only`: Update only command-related sections
- `--skills-only`: Update only skill-related sections
- `--force`: Force update even if no changes detected
- `--verbose`: Show detailed change detection process

## Change Detection System

### **Agents Monitoring**
**Detection Points**:
- New agent files in `.claude/agents/`
- Modified agent descriptions in YAML frontmatter
- Changed tool assignments or model specifications
- Updated tags or capability descriptions

**Auto-Update Actions**:
- Update "Available Agents" table with new/modified agents
- Refresh agent descriptions from YAML metadata
- Synchronize tool lists and model specifications
- Update repository structure diagram

### **Commands Monitoring**
**Detection Points**:
- New command files in `.claude/commands/`
- Modified command usage patterns or parameters
- Updated command descriptions or workflows

**Auto-Update Actions**:
- Add new commands to "Custom Commands" section
- Update command descriptions and usage examples
- Refresh workflow documentation

### **Skills Monitoring**
**Detection Points**:
- New skill directories in `.claude/skills/`
- Modified skill capabilities or descriptions
- Updated skill dependencies or requirements

**Auto-Update Actions**:
- Update "Available Skills" section
- Refresh skill descriptions and use cases
- Synchronize dependency information

### **Structure Monitoring**
**Detection Points**:
- New directories in `.claude/`
- Modified file organization patterns
- Changed relationship between components

**Auto-Update Actions**:
- Update repository structure diagram
- Refresh component relationships
- Add new structural elements

## Update Workflow (A.U.D.I.T. Method)

### **A - Analyze Current State**
```bash
# Scan .claude directory structure
find .claude -type f -name "*.md" | sort

# Parse existing CLAUDE.md sections
grep -n "### \*\*" CLAUDE.md

# Extract current agent metadata
for agent in .claude/agents/*.md; do
    echo "=== $agent ==="
    head -20 "$agent" | grep -E "(name|description|model):"
done
```

### **U - Update Detection**
```bash
# Check for new agents
ls -la .claude/agents/ | grep "\.md$"

# Detect modified agents (by modification time)
find .claude/agents/ -name "*.md" -newer CLAUDE.md

# Parse agent YAML metadata
python3 -c "
import yaml, pathlib
for agent_file in pathlib.Path('.claude/agents').glob('*.md'):
    with open(agent_file) as f:
        content = f.read()
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                metadata = yaml.safe_load(parts[1])
                print(f'{agent_file.name}: {metadata.get(\"description\", \"No description\")}')
"
```

### **D - Documentation Generation**
```bash
# Generate updated agent table
echo "| Agent | Description | Use Case |"
echo "|--------|-------------|---------|"

for agent in .claude/agents/*.md; do
    name=$(basename "$agent" .md)
    desc=$(sed -n '/^description:/p' "$agent" | cut -d: -f2- | xargs)
    use_case=$(sed -n '/^tags:/,/^[^-]/p' "$agent" | grep -E "^- " | head -1 | sed 's/^- //' || echo "General analysis")
    echo "| **@$name** | $desc | $use_case |"
done
```

### **I - Integration with CLAUDE.md**
```bash
# Update specific sections while preserving others
sed -i.bak '/### \*\*Available Agents\*\*/,/### \*\*Agent Creation Workflow\*\*/c\
### **Available Agents**\
\
| Agent | Description | Use Case |\
|--------|-------------|---------|\
| **@orchestrator-agent** | Chief-of-staff for multi-agent coordination | Parallel execution, workflow orchestration |\
| **@referee-agent-csp** | Convergent Synthesis Primitive for deterministic outcome evaluation | Autonomous selection, metric-driven synthesis |\
| **@security-analyst** | Practical security specialist for development workflows. Analyzes code, configurations, and dependencies for common vulnerabilities without requiring security expertise. | Code vulnerability detection, infrastructure security, dependency security analysis |\
\
### **Agent Creation Workflow**' CLAUDE.md
```

### **T - Testing and Validation**
```bash
# Validate YAML syntax in updated sections
python3 -c "
import re
content = open('CLAUDE.md').read()
# Check for table formatting consistency
tables = re.findall(r'\|[^|]+\|[^|]+\|[^|]+\|', content)
for table in tables:
    if table.count('|') != 4:
        print('Table formatting error:', table)
"

# Test markdown rendering
markdownlint CLAUDE.md 2>/dev/null || echo "Minor formatting issues detected"

# Verify all referenced files exist
grep -o '\.claude/[^)]*' CLAUDE.md | while read file; do
    if [ ! -f "$file" ]; then
        echo "Missing referenced file: $file"
    fi
done
```

## Advanced Features

### **Intelligent Change Detection**
```bash
# Calculate content hashes for change detection
generate_hash() {
    find .claude -name "*.md" -exec md5sum {} \; | sort | md5sum
}

CURRENT_HASH=$(generate_hash)
CACHED_HASH=$(cat .claude/.docs_hash 2>/dev/null || echo "")

if [ "$CURRENT_HASH" != "$CACHED_HASH" ]; then
    echo "Changes detected, updating documentation..."
    /update-CLAUDE.md
    echo "$CURRENT_HASH" > .claude/.docs_hash
fi
```

### **Section-Specific Updates**
```bash
# Update only agents section
update_agents_section() {
    local temp_file=$(mktemp)

    # Extract everything before agents section
    sed '/### \*\*Available Agents\*\*/q' CLAUDE.md > "$temp_file"

    # Add new agents section
    echo "### **Available Agents**" >> "$temp_file"
    echo "" >> "$temp_file"
    generate_agents_table >> "$temp_file"
    echo "" >> "$temp_file"

    # Add everything after agents section (skipping old agents section)
    sed -n '/### \*\*Agent Creation Workflow\*\*/,$p' CLAUDE.md >> "$temp_file"

    # Replace original file
    mv "$temp_file" CLAUDE.md
}
```

### **Conflict Resolution**
```bash
# Handle merge conflicts in documentation
resolve_doc_conflicts() {
    if grep -q "<<<<<<< \|======= \|>>>>>>>" CLAUDE.md; then
        echo "Merge conflicts detected in CLAUDE.md"
        echo "Please resolve conflicts and re-run /update-CLAUDE.md"
        return 1
    fi
    return 0
}
```

## Usage Examples

### **Basic Update**
```bash
/update-CLAUDE.md
# Output: Updated 3 agent descriptions, added 1 new command, refreshed structure diagram
```

### **Dry Run Analysis**
```bash
/update-CLAUDE.md --dry-run
# Output: Would update:
#   - Agent table: security-analyst description enhanced
#   - Commands section: add refine-agent command
#   - Structure diagram: add commands/refine-agent.md
```

### **Selective Updates**
```bash
/update-CLAUDE.md --agents-only
# Output: Updated agent descriptions and tool assignments
```

### **Verbose Mode**
```bash
/update-CLAUDE.md --verbose
# Output: Detailed detection and update process with before/after comparisons
```

## Integration Points

### **Git Hooks Integration**
```bash
# .git/hooks/pre-commit
#!/bin/bash
/update-CLAUDE.md --dry-run
if [ $? -eq 1 ]; then
    echo "Documentation updates required. Run /update-CLAUDE.md and commit changes."
    exit 1
fi
```

### **CI/CD Pipeline Integration**
```bash
# GitHub Actions workflow
- name: Update Documentation
  run: |
    /update-CLAUDE.md
    if git diff --quiet CLAUDE.md; then
      echo "No documentation updates needed"
    else
      git config --local user.email "action@github.com"
      git config --local user.name "GitHub Action"
      git add CLAUDE.md
      git commit -m "Auto-update documentation [skip ci]"
      git push
    fi
```

## Validation and Testing

### **Automated Tests**
```bash
# Test change detection accuracy
test_change_detection() {
    # Create test agent
    echo "---\nname: test-agent\ndescription: Test\n---\nTest" > .claude/agents/test-agent.md

    # Run update
    /update-CLAUDE.md

    # Verify agent appears in documentation
    if grep -q "test-agent" CLAUDE.md; then
        echo "✅ Agent detection working"
    else
        echo "❌ Agent detection failed"
    fi

    # Cleanup
    rm .claude/agents/test-agent.md
    /update-CLAUDE.md
}
```

### **Quality Assurance**
- Markdown syntax validation
- Table formatting consistency
- Link verification
- YAML frontmatter validation
- Cross-reference checking

## Error Handling

### **Common Issues**
- **Missing YAML frontmatter**: Attempt to parse structure from content
- **Malformed tables**: Regenerate tables with proper formatting
- **Broken references**: Identify and flag missing files
- **Merge conflicts**: Detect and prompt for manual resolution

### **Recovery Mechanisms**
- Automatic backup creation before updates
- Rollback capability for failed updates
- Partial update recovery
- Conflict resolution guidance

This command ensures CLAUDE.md remains the authoritative, up-to-date source of truth for project capabilities, structure, and usage patterns without requiring manual maintenance.