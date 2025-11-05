# Agent Troubleshooting Guide (Layer 2)

## Overview

This document provides solutions to common issues encountered when creating, validating, and using agents with the Agent Scaffolding Toolkit. The troubleshooting approach follows the same methodology used throughout the project: **check → plan → recheck → pause → create → recheck → refine → recheck → exit**.

## Troubleshooting Methodology

### Applied Mental Models
- **First Principles**: Identify root causes, not symptoms
- **Second Order Effects**: Consider how fixes impact other parts of the system
- **Systems Thinking**: View issues in the context of the entire agent ecosystem
- **Inversion**: Consider what could go wrong with attempted fixes

## Common Issues and Solutions

### 1. Agent Creation Failures

#### Issue: Nested .claude Folders Created
**Symptoms**: Agents created in wrong locations, multiple .claude directories

**Root Cause Analysis (First Principles)**:
- Path calculation errors in create_agent.py
- mkdir(parents=True) creating unwanted directory structures

**Solutions**:
1. **Check**: Verify current directory structure
   ```bash
   find . -name ".claude" -type d
   ```

2. **Plan**: Fix path calculation in create_agent.py
3. **Create**: Use absolute paths and remove automatic directory creation
4. **Recheck**: Confirm agents are created in correct location
5. **Refine**: Update path calculation to prevent future issues

#### Issue: Template Not Found
**Error**: `Template 'xyz' not found. Available: [orchestrator, referee, specialist]`

**Solutions:**
1. Check available templates:
   ```bash
   python scripts/list_templates.py
   ```

2. Use correct template name:
   ```bash
   python scripts/create_agent.py --template specialist --name security-analyst
   ```

3. Create custom template if needed (see Custom Templates section)

#### Issue: Agent File Already Exists
**Error**: `⚠️ Agent 'my-agent' already exists. Overwrite? (y/N):`

**Solutions:**
1. Choose different name:
   ```bash
   python scripts/create_agent.py --name my-agent-v2
   ```

2. Backup and overwrite:
   ```bash
   cp .claude/agents/my-agent.md .claude/agents/my-agent.md.backup
   # Then confirm overwrite with 'y'
   ```

3. Enhance existing agent instead:
   ```bash
   python scripts/enhance_agent.py --agent .claude/agents/my-agent.md --improve-prompt
   ```

### 2. Validation Failures

#### Issue: Missing Required Fields
**Error**: `Missing required field: tools`

**Solutions:**
1. Add required fields to YAML frontmatter:
   ```yaml
   ---
   name: my-agent
   description: Agent description
   tools:
     - Task
     - Read
   ---
   ```

2. Use enhancement script to fix:
   ```bash
   python scripts/enhance_agent.py --agent .claude/agents/my-agent.md --add-tool Task
   ```

#### Issue: Invalid Tool Names
**Error**: `Unknown tool: CustomTool. Available: Task, Bash, Read, Write, Grep, SlashCommand`

**Solutions:**
1. Use only standard Claude Code tools
2. Check tool spelling and capitalization
3. Remove invalid tools:
   ```bash
   python scripts/enhance_agent.py --agent .claude/agents/my-agent.md --remove-tool CustomTool
   ```

#### Issue: System Prompt Too Long
**Error**: `Agent file too large (>50KB)`

**Solutions:**
1. Move detailed examples to references directory
2. Use progressive disclosure pattern
3. Shorten descriptions and examples
4. Focus on essential instructions only

### 3. Agent Performance Issues

#### Issue: Agent Not Responding or Timeout

**Symptoms:**
- Agent takes too long to respond
- Tasks timeout frequently
- Inconsistent behavior

**Diagnostic Steps:**
1. Check model selection:
   ```bash
   grep "model:" .claude/agents/my-agent.md
   ```

2. Verify tools are appropriate for tasks
3. Check prompt clarity and complexity

**Solutions:**
1. **Upgrade to more capable model**:
   ```bash
   python scripts/enhance_agent.py --agent .claude/agents/my-agent.md --model opus
   ```

2. **Simplify prompt**:
   ```bash
   python scripts/enhance_agent.py --agent .claude/agents/my-agent.md --improve-prompt
   ```

3. **Add workflow constraints**:
   ```bash
   python scripts/enhance_agent.py --agent .claude/agents/my-agent.md --add-constraints "Focus on essential tasks only"
   ```

#### Issue: Agent Going Outside Scope

**Symptoms:**
- Agent performs tasks beyond intended scope
- Inconsistent output formats
- Poor task focus

**Solutions:**
1. **Add explicit constraints**:
   ```bash
   python scripts/enhance_agent.py --agent .claude/agents/my-agent.md --add-constraints "Only analyze security, do not suggest architectural changes"
   ```

2. **Improve prompt clarity**:
   ```bash
   python scripts/enhance_agent.py --agent .claude/agents/my-agent.md --improve-prompt
   ```

3. **Refine agent description**:
   Edit the YAML description to be more specific about scope

### 4. Multi-Agent Workflow Issues

#### Issue: Orchestrator Not Delegating Properly

**Symptoms:**
- Orchestrator tries to do work itself
- Parallel execution not happening
- Poor task distribution

**Solutions:**
1. **Ensure Task tool is included**:
   ```bash
   python scripts/enhance_agent.py --agent .claude/agents/orchestrator-agent.md --add-tool Task
   ```

2. **Add delegation instructions**:
   ```bash
   python scripts/enhance_agent.py --agent .claude/agents/orchestrator-agent.md --add-workflow "Multi-agent coordination"
   ```

3. **Review system prompt** for delegation guidance

#### Issue: Referee Agent Not Selecting Objectively

**Symptoms:**
- Subjective selection criteria
- Inconsistent evaluation
- Missing success metrics

**Solutions:**
1. **Add specific evaluation criteria**:
   ```bash
   python scripts/enhance_agent.py --agent .claude/agents/referee-agent.md --add-workflow "Objective evaluation with defined metrics"
   ```

2. **Include constraints**:
   ```bash
   python scripts/enhance_agent.py --agent .claude/agents/referee-agent.md --add-constraints "Use only objective criteria, no subjective judgment"
   ```

### 5. File and System Issues

#### Issue: Permission Denied Errors

**Solutions:**
1. Check file permissions:
   ```bash
   ls -la .claude/agents/
   ```

2. Fix permissions if needed:
   ```bash
   chmod 644 .claude/agents/*.md
   ```

3. Ensure scripts are executable:
   ```bash
   chmod +x scripts/*.py
   ```

#### Issue: Python Script Not Found

**Solutions:**
1. Use full Python path:
   ```bash
   python3 scripts/create_agent.py
   ```

2. Check Python installation:
   ```bash
   which python3
   ```

3. Use virtual environment if configured:
   ```bash
   source venv/bin/activate
   python scripts/create_agent.py
   ```

## Advanced Troubleshooting

### Debug Mode

Enable verbose output for debugging:

```bash
python scripts/create_agent.py --template specialist --name debug-agent --non-interactive --name debug-agent --description "Debug agent" --verbose
```

### Validation Mode

Run comprehensive validation:

```bash
python scripts/validate_agent.py --file .claude/agents/my-agent.md --fix --json
```

### Template Inspection

Examine template structure:

```bash
python scripts/list_templates.py --template orchestrator --detailed
```

## Recovery Procedures

### Recover from Corrupted Agent File

1. **Check for backup**:
   ```bash
   ls .claude/agents/*backup
   ```

2. **Restore from backup**:
   ```bash
   cp .claude/agents/my-agent.md.backup .claude/agents/my-agent.md
   ```

3. **Recreate from template**:
   ```bash
   python scripts/create_agent.py --template specialist --name my-agent-new
   ```

### Reset Agent to Default

1. **Backup current version**:
   ```bash
   cp .claude/agents/my-agent.md .claude/agents/my-agent.md.backup
   ```

2. **Recreate with same name** (confirm overwrite)
3. **Apply customizations** using enhancement script

## Performance Monitoring

### Track Agent Success Rates

Create a simple monitoring script:

```bash
# Log agent usage and results
echo "$(date): my-agent - SUCCESS - 45s" >> agent_performance.log
```

### Monitor Token Usage

Track usage patterns:
- Large prompts indicate need for refinement
- Frequent timeouts suggest model mismatch
- High error rates indicate scope issues

## Getting Help

### Community Resources

1. **Check existing templates** for working examples
2. **Review best practices** documentation
3. **Examine architectural patterns** for guidance

### System Information Collection

When reporting issues, collect:

```bash
# System info
python3 --version
pwd
ls -la .claude/

# Agent info
python scripts/list_templates.py --template your-template --detailed
python scripts/validate_agent.py --file .claude/agents/your-agent.md --json
```

### Common Debugging Commands

```bash
# Validate all agents
for agent in .claude/agents/*.md; do
    python scripts/validate_agent.py --file "$agent"
done

# List all available options
python scripts/create_agent.py --help
python scripts/enhance_agent.py --help
```

This troubleshooting guide should resolve most common issues. For persistent problems, review the agent design against the best practices documentation and consider simplifying the agent scope.