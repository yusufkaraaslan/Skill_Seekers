# Workflows Guide

> **Skill Seekers v3.1.0**  
> **Enhancement workflow presets for specialized analysis**

---

## What are Workflows?

Workflows are **multi-stage AI enhancement pipelines** that apply specialized analysis to your skills:

```
Basic Skill ──▶ Workflow: Security-Focus ──▶ Security-Enhanced Skill
                    Stage 1: Overview
                    Stage 2: Vulnerability Analysis
                    Stage 3: Best Practices
                    Stage 4: Compliance
```

---

## Built-in Presets

Skill Seekers includes 5 built-in workflow presets:

| Preset | Stages | Best For |
|--------|--------|----------|
| `default` | 2 | General improvement |
| `minimal` | 1 | Light touch-up |
| `security-focus` | 4 | Security analysis |
| `architecture-comprehensive` | 7 | Deep architecture review |
| `api-documentation` | 3 | API documentation focus |

---

## Using Workflows

### List Available Workflows

```bash
skill-seekers workflows list
```

**Output:**
```
Bundled Workflows:
  - default (built-in)
  - minimal (built-in)
  - security-focus (built-in)
  - architecture-comprehensive (built-in)
  - api-documentation (built-in)

User Workflows:
  - my-custom (user)
```

### Apply a Workflow

```bash
# During skill creation
skill-seekers create <source> --enhance-workflow security-focus

# Multiple workflows (chained)
skill-seekers create <source> \
  --enhance-workflow security-focus \
  --enhance-workflow api-documentation
```

### Show Workflow Content

```bash
skill-seekers workflows show security-focus
```

**Output:**
```yaml
name: security-focus
description: Security analysis workflow
stages:
  - name: security-overview
    prompt: Analyze security features and mechanisms...
    
  - name: vulnerability-analysis
    prompt: Identify common vulnerabilities...
    
  - name: best-practices
    prompt: Document security best practices...
    
  - name: compliance
    prompt: Map to security standards...
```

---

## Workflow Presets Explained

### Default Workflow

**Stages:** 2
**Purpose:** General improvement

```yaml
stages:
  - name: structure
    prompt: Improve overall structure and organization
  - name: content
    prompt: Enhance content quality and examples
```

**Use when:** You want standard enhancement without specific focus.

---

### Minimal Workflow

**Stages:** 1
**Purpose:** Light touch-up

```yaml
stages:
  - name: cleanup
    prompt: Basic formatting and cleanup
```

**Use when:** You need quick, minimal enhancement.

---

### Security-Focus Workflow

**Stages:** 4
**Purpose:** Security analysis and recommendations

```yaml
stages:
  - name: security-overview
    prompt: Identify and document security features...
    
  - name: vulnerability-analysis
    prompt: Analyze potential vulnerabilities...
    
  - name: security-best-practices
    prompt: Document security best practices...
    
  - name: compliance-mapping
    prompt: Map to OWASP, CWE, and other standards...
```

**Use for:**
- Security libraries
- Authentication systems
- API frameworks
- Any code handling sensitive data

**Example:**
```bash
skill-seekers create oauth2-server --enhance-workflow security-focus
```

---

### Architecture-Comprehensive Workflow

**Stages:** 7
**Purpose:** Deep architectural analysis

```yaml
stages:
  - name: system-overview
    prompt: Document high-level architecture...
    
  - name: component-analysis
    prompt: Analyze key components...
    
  - name: data-flow
    prompt: Document data flow patterns...
    
  - name: integration-points
    prompt: Identify external integrations...
    
  - name: scalability
    prompt: Document scalability considerations...
    
  - name: deployment
    prompt: Document deployment patterns...
    
  - name: maintenance
    prompt: Document operational concerns...
```

**Use for:**
- Large frameworks
- Distributed systems
- Microservices
- Enterprise platforms

**Example:**
```bash
skill-seekers create kubernetes/kubernetes \
  --enhance-workflow architecture-comprehensive
```

---

### API-Documentation Workflow

**Stages:** 3
**Purpose:** API-focused enhancement

```yaml
stages:
  - name: endpoint-catalog
    prompt: Catalog all API endpoints...
    
  - name: request-response
    prompt: Document request/response formats...
    
  - name: error-handling
    prompt: Document error codes and handling...
```

**Use for:**
- REST APIs
- GraphQL services
- SDKs
- Library documentation

**Example:**
```bash
skill-seekers create https://api.example.com/docs \
  --enhance-workflow api-documentation
```

---

## Chaining Multiple Workflows

Apply multiple workflows sequentially:

```bash
skill-seekers create <source> \
  --enhance-workflow security-focus \
  --enhance-workflow api-documentation
```

**Execution order:**
1. Run `security-focus` workflow
2. Run `api-documentation` workflow on results
3. Final skill has both security and API focus

**Use case:** API with security considerations

---

## Custom Workflows

### Create Custom Workflow

Create a YAML file:

```yaml
# my-workflow.yaml
name: performance-focus
description: Performance optimization workflow

variables:
  target_latency: "100ms"
  target_throughput: "1000 req/s"

stages:
  - name: performance-overview
    type: builtin
    target: skill_md
    prompt: |
      Analyze performance characteristics of this framework.
      Focus on:
      - Benchmark results
      - Optimization opportunities
      - Scalability limits
    
  - name: optimization-guide
    type: custom
    uses_history: true
    prompt: |
      Based on the previous analysis, create an optimization guide.
      Target latency: {target_latency}
      Target throughput: {target_throughput}
      
      Previous results: {previous_results}
```

### Install Workflow

```bash
# Add to user workflows
skill-seekers workflows add my-workflow.yaml

# With custom name
skill-seekers workflows add my-workflow.yaml --name perf-guide
```

### Use Custom Workflow

```bash
skill-seekers create <source> --enhance-workflow performance-focus
```

### Update Workflow

```bash
# Edit the file, then:
skill-seekers workflows add my-workflow.yaml --name performance-focus
```

### Remove Workflow

```bash
skill-seekers workflows remove performance-focus
```

---

## Workflow Variables

Pass variables to workflows at runtime:

### In Workflow Definition

```yaml
variables:
  target_audience: "beginners"
  focus_area: "security"
```

### Override at Runtime

```bash
skill-seekers create <source> \
  --enhance-workflow my-workflow \
  --var target_audience=experts \
  --var focus_area=performance
```

### Use in Prompts

```yaml
stages:
  - name: customization
    prompt: |
      Tailor content for {target_audience}.
      Focus on {focus_area} aspects.
```

---

## Inline Stages

Add one-off enhancement stages without creating a workflow file:

```bash
skill-seekers create <source> \
  --enhance-stage "performance:Analyze performance characteristics"
```

**Format:** `name:prompt`

**Multiple stages:**
```bash
skill-seekers create <source> \
  --enhance-stage "perf:Analyze performance" \
  --enhance-stage "security:Check security" \
  --enhance-stage "examples:Add more examples"
```

---

## Workflow Dry Run

Preview what a workflow will do without executing:

```bash
skill-seekers create <source> \
  --enhance-workflow security-focus \
  --workflow-dry-run
```

**Output:**
```
Workflow: security-focus
Stages:
  1. security-overview
     - Will analyze security features
     - Target: skill_md
     
  2. vulnerability-analysis
     - Will identify vulnerabilities
     - Target: skill_md
     
  3. best-practices
     - Will document best practices
     - Target: skill_md
     
  4. compliance
     - Will map to standards
     - Target: skill_md

Execution order: Sequential
Estimated time: ~4 minutes
```

---

## Workflow Validation

Validate workflow syntax:

```bash
# Validate bundled workflow
skill-seekers workflows validate security-focus

# Validate file
skill-seekers workflows validate ./my-workflow.yaml
```

---

## Copying Workflows

Copy bundled workflows to customize:

```bash
# Copy single workflow
skill-seekers workflows copy security-focus

# Copy multiple
skill-seekers workflows copy security-focus api-documentation minimal

# Edit the copy
nano ~/.config/skill-seekers/workflows/security-focus.yaml
```

---

## Best Practices

### 1. Start with Default

```bash
# Default is good for most cases
skill-seekers create <source>
```

### 2. Add Specific Workflows as Needed

```bash
# Security-focused project
skill-seekers create auth-library --enhance-workflow security-focus

# API project
skill-seekers create api-framework --enhance-workflow api-documentation
```

### 3. Chain for Comprehensive Analysis

```bash
# Large framework: architecture + security
skill-seekers create kubernetes/kubernetes \
  --enhance-workflow architecture-comprehensive \
  --enhance-workflow security-focus
```

### 4. Create Custom for Specialized Needs

```bash
# Create custom workflow for your domain
skill-seekers workflows add ml-workflow.yaml
skill-seekers create ml-framework --enhance-workflow ml-focus
```

### 5. Use Variables for Flexibility

```bash
# Same workflow, different targets
skill-seekers create <source> \
  --enhance-workflow my-workflow \
  --var audience=beginners

skill-seekers create <source> \
  --enhance-workflow my-workflow \
  --var audience=experts
```

---

## Troubleshooting

### "Workflow not found"

```bash
# List available
skill-seekers workflows list

# Check spelling
skill-seekers create <source> --enhance-workflow security-focus
```

### "Invalid workflow YAML"

```bash
# Validate
skill-seekers workflows validate ./my-workflow.yaml

# Common issues:
# - Missing 'stages' key
# - Invalid YAML syntax
# - Undefined variable references
```

### "Workflow stage failed"

```bash
# Check stage details
skill-seekers workflows show my-workflow

# Try with dry run
skill-seekers create <source> \
  --enhance-workflow my-workflow \
  --workflow-dry-run
```

---

## Workflow Support Across All Scrapers

Workflows are supported by **all 5 scrapers** in Skill Seekers:

| Scraper | Command | Workflow Support |
|---------|---------|------------------|
| Documentation | `scrape` | ✅ Full support |
| GitHub | `github` | ✅ Full support |
| Local Codebase | `analyze` | ✅ Full support |
| PDF | `pdf` | ✅ Full support |
| Unified/Multi-Source | `unified` | ✅ Full support |
| Create (Auto-detect) | `create` | ✅ Full support |

### Using Workflows with Different Sources

```bash
# Documentation website
skill-seekers scrape https://docs.example.com --enhance-workflow security-focus

# GitHub repository
skill-seekers github --repo owner/repo --enhance-workflow api-documentation

# Local codebase
skill-seekers analyze --directory ./my-project --enhance-workflow architecture-comprehensive

# PDF document
skill-seekers pdf --pdf manual.pdf --enhance-workflow minimal

# Unified config (multi-source)
skill-seekers unified --config configs/multi-source.json --enhance-workflow security-focus

# Auto-detect source type
skill-seekers create ./my-project --enhance-workflow security-focus
```

---

## Workflows in Config Files

Unified configs support defining workflows at the top level:

```json
{
  "name": "my-skill",
  "description": "Complete skill with security enhancement",
  "workflows": ["security-focus", "api-documentation"],
  "workflow_stages": [
    {
      "name": "cleanup",
      "prompt": "Remove boilerplate and standardize formatting"
    }
  ],
  "workflow_vars": {
    "focus_area": "performance",
    "detail_level": "comprehensive"
  },
  "sources": [
    {"type": "docs", "base_url": "https://docs.example.com/"}
  ]
}
```

**Priority:** CLI flags override config values

```bash
# Config has security-focus, CLI overrides with api-documentation
skill-seekers unified config.json --enhance-workflow api-documentation
```

---

## Summary

| Approach | When to Use |
|----------|-------------|
| **Default** | Most cases |
| **Security-Focus** | Security-sensitive projects |
| **Architecture** | Large frameworks, systems |
| **API-Docs** | API frameworks, libraries |
| **Custom** | Specialized domains |
| **Chaining** | Multiple perspectives needed |

---

## Next Steps

- [Custom Workflows](../advanced/custom-workflows.md) - Advanced workflow creation
- [Enhancement Guide](03-enhancement.md) - Enhancement fundamentals
- [MCP Reference](../reference/MCP_REFERENCE.md) - Workflows via MCP
