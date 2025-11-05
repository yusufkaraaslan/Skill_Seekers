# /refine-agent: Multi-Mental Model Agent Refinement

Automated agent refinement workflow using multiple mental models and systematic validation.

## Usage

```bash
/refine-agent <agent-name> [focus-area]
```

**Parameters**:
- `agent-name`: Name of agent to refine (e.g., "security-analyst", "orchestrator-agent")
- `focus-area`: Optional focus for refinement (e.g., "security", "orchestration", "validation")

## Workflow Automation

This command implements the proven **check → plan → recheck → pause → create → recheck → refine → recheck → exit** methodology enhanced with multiple mental models:

### Applied Mental Models

1. **First Principles**: Break down to fundamental agent capabilities
2. **Second Order Effects**: Consider impact of changes on user workflows
3. **Interdependencies**: Map tool integrations and agent interactions
4. **Systems Thinking**: View agent in context of entire development ecosystem
5. **Inversion**: Identify what users want to avoid in agent behavior

### Automated Workflow Steps

#### **CHECK Phase** (First Principles + Systems Thinking)
- [ ] Analyze current agent structure and capabilities
- [ ] **Tool Usage Gap Analysis**: Check for mandatory tool usage enforcement
- [ ] Identify gaps between intended vs actual functionality
- [ ] Map user journey scenarios and pain points
- [ ] Assess integration with Claude Code native tools
- [ ] **Evidence Required**: Report tool usage enforcement status

#### **PLAN Phase** (Second Order Effects + Interdependencies)
- [ ] Design enhanced capabilities considering cascading impacts
- [ ] **Tool Enforcement Strategy**: Plan mandatory tool usage requirements
- [ ] Plan tool integration strategies with evidence clauses
- [ ] Define measurable success criteria including tool usage metrics
- [ ] Create structured improvement roadmap
- [ ] **Evidence Required**: Show planned tool usage patterns

#### **RECHECK Phase** (Systems Thinking)
- [ ] Validate plan against system requirements
- [ ] Check for unintended consequences
- [ ] Verify integration points with existing agents

#### **PAUSE Phase** (Inversion)
- [ ] Consider what could go wrong with proposed changes
- [ ] Identify failure modes and mitigation strategies
- [ ] Challenge assumptions about user needs

#### **CREATE Phase** (First Principles)
- [ ] Implement enhanced agent definition
- [ ] **Add MANDATORY TOOL USAGE section with orchestrator-style enforcement**
- [ ] Build practical capabilities with concrete examples
- [ ] **Add Evidence Required clauses throughout workflow**
- [ ] **Include Example Proper Usage with tool invocations**
- [ ] Add tool integration patterns
- [ ] Include constraint management
- [ ] **Evidence Required**: Show actual tool integration examples

#### **RECHECK Phase** (All Models)
- [ ] Validate YAML structure compliance
- [ ] Test agent against user scenarios
- [ ] Verify tool integration works correctly

#### **REFINE Phase** (Continuous Improvement)
- [ ] Optimize based on validation results
- [ ] Enhance documentation and examples
- [ ] Add edge case handling

#### **FINAL RECHECK Phase** (Holistic Validation)
- [ ] Complete system validation
- [ ] Cross-model verification
- [ ] Final quality assurance

#### **EXIT**: Documentation and lessons learned

## Example Outputs

### Before Refinement
```yaml
name: security-analyst
description: Security analysis specialist
model: sonnet
tools:
  - Read
  - Task
tags:
---
System prompt: You are security-analyst, Security analysis specialist.
```

### After Refinement
```yaml
name: security-analyst
description: Practical security specialist for development workflows. Analyzes code, configurations, and dependencies for common vulnerabilities without requiring security expertise.
model: sonnet
tools:
  - Read
  - Grep
  - Bash
  - Task
tags:
  - security
  - vulnerability-analysis
  - code-review
  - dependency-security
  - devsecops
---
[Comprehensive 172-line system prompt with M.A.P.S. methodology, specific vulnerability patterns, practical examples, and integration patterns]
```

## Validation Criteria

- **Structural**: Valid YAML frontmatter with required fields
- **Functional**: Agent fulfills intended purpose effectively
- **Integration**: Works seamlessly with Claude Code tools
- **Usability**: Provides actionable, practical value to users
- **Maintainability**: Clear documentation and examples

## Integration with Agent Scaffolding Toolkit

This command works synergistically with the agent scaffolding toolkit:
- Uses existing validation scripts for structural compliance
- Leverages template patterns for consistency
- Maintains compatibility with agent creation workflow
- Updates documentation automatically

## Usage Examples

```bash
# Refine security-analyst agent (as we just did)
/refine-agent security-analyst

# Refine test-generator with tool usage gap focus
/refine-agent test-generator tool-usage

# Refine orchestrator-agent with focus on coordination
/refine-agent orchestrator-agent orchestration

# Refine custom agent for specific domain
/refine-agent data-analyst data-processing

# Refine all agents (batch mode) - includes tool usage gap analysis
/refine-agent --all

# Refine with specific tool usage gap template
/refine-agent performance-auditor tool-enforcement
```

## Success Metrics

- Enhanced agent capability and usability
- **100% tool usage compliance** across all refined agents
- Improved user satisfaction and adoption
- Reduced manual refinement effort
- Consistent application of mental models
- Systematic validation and quality assurance
- **Measurable outputs** (files created, commands executed, validation completed)
- **Elimination of theoretical-only** agent behaviors

## Tool Usage Gap Success Indicators

### **Before Refinement** (Theoretical-Only Agents)
```yaml
❌ "Provides comprehensive analysis..." (no tools)
❌ "Generates detailed reports..." (no evidence)
❌ "Offers recommendations..." (no execution)
```

### **After Refinement** (Tool-Enforced Agents)
```yaml
✅ "MUST use Read tool to analyze source files"
✅ "Evidence Required: Show actual commands executed"
✅ "Example: Bash: python3 -m pytest tests/ -v"
```

### **Validation Metrics**
- **MANDATORY TOOL USAGE sections**: 100% compliance
- **Evidence Required clauses**: 100% coverage
- **Example Proper Usage**: 100% completion
- **Tool execution evidence**: Measurable and verifiable

This ensures that the `/refine-agent` command can systematically transform theoretical agents into practical, tool-enforced specialists that produce measurable, actionable outcomes.

## Tool Usage Gap Analysis Methodology

### **The Tool Usage Gap Problem**

Many agents provide theoretical knowledge without requiring actual tool usage, resulting in:
- Planning without execution
- Knowledge transfer without file creation
- Analysis without validation commands
- Recommendations without implementation evidence

### **Orchestrator-Style Tool Enforcement Template**

When refining agents, add this proven structure to bridge tool usage gaps:

```markdown
## MANDATORY TOOL USAGE REQUIREMENTS

**CRITICAL: You MUST use actual tools for [domain] analysis, not theoretical assessment.**

##### Context Gathering Tools (Mandatory)
- **Read tool**: MUST read [specific file types] and understand [domain context]
- **Grep tool**: MUST search for [specific patterns] and [domain relationships]
- **Evidence Required**: Report specific files analyzed and patterns discovered

##### Analysis Tools (Mandatory)
- **Bash tool**: MUST execute [specific commands] and validation tools
- **Evidence Required**: Show actual analysis commands executed and their results

##### Example Proper Usage:
```
Step 1: Context Gathering
Read: [specific files relevant to domain]
Grep: pattern="[domain-specific pattern]" path="[target]" output_mode="content" -n

Found [count] [domain elements]...

Step 2: Analysis
Bash: [domain-specific analysis commands]

Analysis results: [specific outcomes]...
```
```

### **Tool Usage Validation Checklist**

During refinement, ensure agents have:

**✅ MANDATORY TOOL USAGE section**
- Explicit tool requirements with "MUST" language
- Clear distinction between theoretical and practical analysis

**✅ Evidence Required clauses**
- Specific evidence requirements for each tool usage step
- Accountability mechanisms for tool execution

**✅ Example Proper Usage section**
- Concrete tool invocations with realistic examples
- Step-by-step workflow showing actual tool usage

**✅ Domain-specific tool patterns**
- Read/Grep for context gathering relevant to domain
- Bash/Write for execution and file creation
- Domain-specific validation commands

### **Tool Usage Gap Detection Patterns**

Use these checks during the CHECK phase:

```bash
# Check for mandatory tool usage sections
grep -l "MANDATORY TOOL USAGE" .claude/agents/*.md

# Check for evidence required clauses
grep -l "Evidence Required" .claude/agents/*.md

# Check for example usage sections
grep -c "Example Proper Usage" .claude/agents/*.md
```

### **Integration with Multi-Mental Model Refinement**

The tool usage gap analysis integrates seamlessly with the existing methodology:

- **First Principles**: Tools are fundamental to agent execution
- **Second Order Effects**: Tool enforcement prevents theoretical-only outputs
- **Interdependencies**: Tool usage affects agent orchestration patterns
- **Systems Thinking**: Tool integration impacts entire development ecosystem
- **Inversion**: Avoid agents that don't produce tangible results

This systematic approach ensures that refined agents consistently use tools to produce measurable, actionable outcomes rather than theoretical knowledge alone.

This command transforms the manual, error-prone agent refinement process into a systematic, repeatable workflow that consistently produces high-quality, user-centric agents with mandatory tool usage enforcement.