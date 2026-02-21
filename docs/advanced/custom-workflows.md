# Custom Workflows Guide

> **Skill Seekers v3.1.0**  
> **Create custom AI enhancement workflows**

---

## What are Custom Workflows?

Workflows are YAML-defined, multi-stage AI enhancement pipelines:

```yaml
my-workflow.yaml
├── name
├── description
├── variables (optional)
└── stages (1-10)
    ├── name
    ├── type (builtin/custom)
    ├── target (skill_md/references/)
    ├── prompt
    └── uses_history (optional)
```

---

## Basic Workflow Structure

```yaml
name: my-custom
description: Custom enhancement workflow

stages:
  - name: stage-one
    type: builtin
    target: skill_md
    prompt: |
      Improve the SKILL.md by adding...
      
  - name: stage-two
    type: custom
    target: references
    prompt: |
      Enhance the references by...
```

---

## Workflow Fields

### Top Level

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Workflow identifier |
| `description` | No | Human-readable description |
| `variables` | No | Configurable variables |
| `stages` | Yes | Array of stage definitions |

### Stage Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Stage identifier |
| `type` | Yes | `builtin` or `custom` |
| `target` | Yes | `skill_md` or `references` |
| `prompt` | Yes | AI prompt text |
| `uses_history` | No | Access previous stage results |

---

## Creating Your First Workflow

### Example: Performance Analysis

```yaml
# performance.yaml
name: performance-focus
description: Analyze and document performance characteristics

variables:
  target_latency: "100ms"
  target_throughput: "1000 req/s"

stages:
  - name: performance-overview
    type: builtin
    target: skill_md
    prompt: |
      Add a "Performance" section to SKILL.md covering:
      - Benchmark results
      - Performance characteristics
      - Resource requirements
      
  - name: optimization-guide
    type: custom
    target: references
    uses_history: true
    prompt: |
      Create an optimization guide with:
      - Target latency: {target_latency}
      - Target throughput: {target_throughput}
      - Common bottlenecks
      - Optimization techniques
```

### Install and Use

```bash
# Add workflow
skill-seekers workflows add performance.yaml

# Use it
skill-seekers create <source> --enhance-workflow performance-focus

# With custom variables
skill-seekers create <source> \
  --enhance-workflow performance-focus \
  --var target_latency=50ms \
  --var target_throughput=5000req/s
```

---

## Stage Types

### builtin

Uses built-in enhancement logic:

```yaml
stages:
  - name: structure-improvement
    type: builtin
    target: skill_md
    prompt: "Improve document structure"
```

### custom

Full custom prompt control:

```yaml
stages:
  - name: custom-analysis
    type: custom
    target: skill_md
    prompt: |
      Your detailed custom prompt here...
      Can use {variables} and {history}
```

---

## Targets

### skill_md

Enhances the main SKILL.md file:

```yaml
stages:
  - name: improve-skill
    target: skill_md
    prompt: "Add comprehensive overview section"
```

### references

Enhances reference files:

```yaml
stages:
  - name: improve-refs
    target: references
    prompt: "Add cross-references between files"
```

---

## Variables

### Defining Variables

```yaml
variables:
  audience: "beginners"
  focus_area: "security"
  include_examples: true
```

### Using Variables

```yaml
stages:
  - name: customize
    prompt: |
      Tailor content for {audience}.
      Focus on {focus_area}.
      Include examples: {include_examples}
```

### Overriding at Runtime

```bash
skill-seekers create <source> \
  --enhance-workflow my-workflow \
  --var audience=experts \
  --var focus_area=performance
```

---

## History Passing

Access results from previous stages:

```yaml
stages:
  - name: analyze
    type: custom
    target: skill_md
    prompt: "Analyze security features"
    
  - name: document
    type: custom
    target: skill_md
    uses_history: true
    prompt: |
      Based on previous analysis:
      {previous_results}
      
      Create documentation...
```

---

## Advanced Example: Security Review

```yaml
name: comprehensive-security
description: Multi-stage security analysis

variables:
  compliance_framework: "OWASP Top 10"
  risk_level: "high"

stages:
  - name: asset-inventory
    type: builtin
    target: skill_md
    prompt: |
      Document all security-sensitive components:
      - Authentication mechanisms
      - Authorization checks
      - Data validation
      - Encryption usage
      
  - name: threat-analysis
    type: custom
    target: skill_md
    uses_history: true
    prompt: |
      Based on assets: {all_history}
      
      Analyze threats for {compliance_framework}:
      - Threat vectors
      - Attack scenarios
      - Risk ratings ({risk_level} focus)
      
  - name: mitigation-guide
    type: custom
    target: references
    uses_history: true
    prompt: |
      Create mitigation guide:
      - Countermeasures
      - Best practices
      - Code examples
      - Testing strategies
```

---

## Validation

### Validate Before Installing

```bash
skill-seekers workflows validate ./my-workflow.yaml
```

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Missing 'stages'` | No stages array | Add stages: |
| `Invalid type` | Not builtin/custom | Check type field |
| `Undefined variable` | Used but not defined | Add to variables: |

---

## Best Practices

### 1. Start Simple

```yaml
# Start with 1-2 stages
name: simple
description: Simple workflow
stages:
  - name: improve
    type: builtin
    target: skill_md
    prompt: "Improve SKILL.md"
```

### 2. Use Clear Stage Names

```yaml
# Good
stages:
  - name: security-overview
  - name: vulnerability-analysis
  
# Bad
stages:
  - name: stage1
  - name: step2
```

### 3. Document Variables

```yaml
variables:
  # Target audience level: beginner, intermediate, expert
  audience: "intermediate"
  
  # Security focus area: owasp, pci, hipaa
  compliance: "owasp"
```

### 4. Test Incrementally

```bash
# Test with dry run
skill-seekers create <source> \
  --enhance-workflow my-workflow \
  --workflow-dry-run

# Then actually run
skill-seekers create <source> \
  --enhance-workflow my-workflow
```

### 5. Chain for Complex Analysis

```bash
# Use multiple workflows
skill-seekers create <source> \
  --enhance-workflow security-focus \
  --enhance-workflow performance-focus
```

---

## Sharing Workflows

### Export Workflow

```bash
# Get workflow content
skill-seekers workflows show my-workflow > my-workflow.yaml
```

### Share with Team

```bash
# Add to version control
git add my-workflow.yaml
git commit -m "Add custom security workflow"

# Team members install
skill-seekers workflows add my-workflow.yaml
```

### Publish

Submit to Skill Seekers community:
- GitHub Discussions
- Skill Seekers website
- Documentation contributions

---

## See Also

- [Workflows Guide](../user-guide/05-workflows.md) - Using workflows
- [MCP Reference](../reference/MCP_REFERENCE.md) - Workflows via MCP
- [Enhancement Guide](../user-guide/03-enhancement.md) - Enhancement fundamentals
