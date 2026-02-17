# Enhancement Workflow System

**Date**: 2026-02-16
**Status**: ✅ **IMPLEMENTED** (Core Engine)
**Phase**: 1 of 4 Complete

---

## 🎯 What It Does

Allows users to **customize and automate AI enhancement** with:
- ✅ Sequential stages (each builds on previous)
- ✅ Custom prompts per stage
- ✅ History passing between stages
- ✅ Workflow inheritance (extends other workflows)
- ✅ Post-processing configuration
- ✅ Per-project and global workflows

---

## 🚀 Quick Start

### 1. List Available Workflows

```bash
ls ~/.config/skill-seekers/workflows/
# default.yaml
# security-focus.yaml
# minimal.yaml
# api-documentation.yaml
```

### 2. Use a Workflow

```bash
# Use global workflow
skill-seekers analyze . --enhance-workflow security-focus

# Use custom workflow
skill-seekers analyze . --enhance-workflow .skill-seekers/my-workflow.yaml

# Quick inline stages
skill-seekers analyze . \
  --enhance-stage "security:Analyze for security issues" \
  --enhance-stage "cleanup:Remove boilerplate"
```

### 3. Create Your Own Workflow

**File**: `.skill-seekers/enhancement.yaml`

```yaml
name: "My Custom Workflow"
description: "Tailored for my project's needs"
version: "1.0"

# Inherit from existing workflow
extends: "~/.config/skill-seekers/workflows/security-focus.yaml"

# Override variables
variables:
  focus_area: "api-security"
  detail_level: "comprehensive"

# Add extra stages
stages:
  # Built-in stages from parent workflow run first

  # Your custom stage
  - name: "my_custom_check"
    type: "custom"
    target: "custom_section"
    uses_history: true
    prompt: |
      Based on all previous analysis: {all_history}

      Add my custom checks:
      - Check 1
      - Check 2
      - Check 3

      Output as markdown.

# Post-processing
post_process:
  add_metadata:
    custom_workflow: true
    reviewed_by: "my-team"
```

---

## 📋 Workflow Structure

### Complete Example

```yaml
name: "Workflow Name"
description: "What this workflow does"
version: "1.0"

# Where this workflow applies
applies_to:
  - codebase_analysis
  - doc_scraping
  - github_analysis

# Variables (can be overridden with --var)
variables:
  focus_area: "security"
  detail_level: "comprehensive"

# Sequential stages
stages:
  # Stage 1: Built-in enhancement
  - name: "base_patterns"
    type: "builtin"  # Uses existing enhancement system
    target: "patterns"  # What to enhance
    enabled: true

  # Stage 2: Custom AI prompt
  - name: "custom_analysis"
    type: "custom"
    target: "my_section"
    uses_history: true  # Can see previous stages
    prompt: |
      Based on patterns from previous stage:
      {previous_results}

      Do custom analysis here...

      Variables available:
      - {focus_area}
      - {detail_level}

      Previous stage: {stages[base_patterns]}
      All history: {all_history}

# Post-processing
post_process:
  # Remove sections
  remove_sections:
    - "boilerplate"
    - "generic_warnings"

  # Reorder SKILL.md sections
  reorder_sections:
    - "executive_summary"
    - "my_section"
    - "patterns"

  # Add metadata
  add_metadata:
    workflow: "my-workflow"
    version: "1.0"
```

---

## 🎨 Built-in Workflows

### 1. `security-focus.yaml`

**Purpose**: Security-focused analysis

**Stages**:
1. Base patterns (builtin)
2. Security analysis (checks auth, input validation, crypto, etc.)
3. Security checklist (practical checklist for developers)
4. Security section for SKILL.md

**Use When**: Analyzing security-critical code

**Example**:
```bash
skill-seekers analyze . --enhance-workflow security-focus
```

### 2. `minimal.yaml`

**Purpose**: Fast, essential-only enhancement

**Stages**:
1. Essential patterns only (high confidence)
2. Quick cleanup

**Use When**: You want speed over detail

**Example**:
```bash
skill-seekers analyze . --enhance-workflow minimal
```

### 3. `api-documentation.yaml`

**Purpose**: Focus on API endpoints and documentation

**Stages**:
1. Base analysis
2. Extract API endpoints (routes, methods, params)
3. Generate API reference section

**Use When**: Analyzing REST APIs, GraphQL, etc.

**Example**:
```bash
skill-seekers analyze . --enhance-workflow api-documentation --var api_type=GraphQL
```

### 4. `default.yaml`

**Purpose**: Standard enhancement (same as --enhance-level 3)

**Stages**:
1. Pattern enhancement (builtin)
2. Test example enhancement (builtin)

**Use When**: Default behavior

---

## 🔄 How Sequential Stages Work

```python
# Example: 3-stage workflow

Stage 1: "detect_patterns"
Input: Raw code analysis
AI Prompt: "Find design patterns"
Output: {"patterns": [...]}
History[0] = {"stage": "detect_patterns", "results": {...}}

↓

Stage 2: "analyze_security"
Input: {previous_results} = History[0]  # Can access previous stage
AI Prompt: "Based on patterns: {previous_results}, find security issues"
Output: {"security_findings": [...]}
History[1] = {"stage": "analyze_security", "results": {...}}

↓

Stage 3: "create_checklist"
Input: {all_history} = [History[0], History[1]]  # Can access all stages
       {stages[detect_patterns]} = History[0]  # Access by name
AI Prompt: "Based on all findings: {all_history}, create checklist"
Output: {"checklist": "..."}
History[2] = {"stage": "create_checklist", "results": {...}}

↓

Final Result = Merge all stage outputs
```

---

## 🎯 Context Variables Available in Prompts

```yaml
stages:
  - name: "my_stage"
    prompt: |
      # Current analysis results
      {current_results}

      # Previous stage only (if uses_history: true)
      {previous_results}

      # All previous stages (if uses_history: true)
      {all_history}

      # Specific stage by name (if uses_history: true)
      {stages[stage_name]}

      # Workflow variables
      {focus_area}
      {detail_level}
      {any_variable_defined_in_workflow}

      # Override with --var
      # skill-seekers analyze . --enhance-workflow my-workflow --var focus_area=performance
```

---

## 📝 Workflow Inheritance (extends)

```yaml
# child-workflow.yaml
extends: "~/.config/skill-seekers/workflows/security-focus.yaml"

# Override specific stages
stages:
  # This replaces the stage with same name in parent
  - name: "security_analysis"
    prompt: |
      My custom security analysis prompt...

# Add new stages (merged with parent)
  - name: "extra_check"
    prompt: |
      Additional check...

# Override variables
variables:
  focus_area: "api-security"  # Overrides parent's "security"
```

---

## 🛠️ CLI Usage

### Basic Usage

```bash
# Use workflow
skill-seekers analyze . --enhance-workflow security-focus

# Use custom workflow file
skill-seekers analyze . --enhance-workflow .skill-seekers/my-workflow.yaml
```

### Override Variables

```bash
# Override workflow variables
skill-seekers analyze . \
  --enhance-workflow security-focus \
  --var focus_area=performance \
  --var detail_level=basic
```

### Inline Stages (Quick)

```bash
# Add inline stages (no YAML file needed)
skill-seekers analyze . \
  --enhance-stage "security:Analyze for SQL injection" \
  --enhance-stage "performance:Find performance bottlenecks" \
  --enhance-stage "cleanup:Remove generic sections"

# Format: "stage_name:AI prompt"
```

### Dry Run

```bash
# Preview workflow without executing
skill-seekers analyze . --enhance-workflow security-focus --workflow-dry-run

# Shows:
# - Workflow name and description
# - All stages that will run
# - Variables used
# - Post-processing steps
```

### Save History

```bash
# Save workflow execution history
skill-seekers analyze . \
  --enhance-workflow security-focus \
  --workflow-history output/workflow_history.json

# History includes:
# - Which stages ran
# - What each stage produced
# - Timestamps
# - Metadata
```

---

## 📊 Status & Roadmap

### ✅ Phase 1: Core Engine (COMPLETE)

**Files Created**:
- `src/skill_seekers/cli/enhancement_workflow.py` - Core engine
- `src/skill_seekers/cli/arguments/workflow.py` - CLI arguments
- `~/.config/skill-seekers/workflows/*.yaml` - Default workflows

**Features**:
- ✅ YAML workflow loading
- ✅ Sequential stage execution
- ✅ History passing (previous_results, all_history, stages)
- ✅ Workflow inheritance (extends)
- ✅ Custom prompts with variable substitution
- ✅ Post-processing (remove/reorder sections, add metadata)
- ✅ Dry-run mode
- ✅ History saving

**Demo**:
```bash
python test_workflow_demo.py
```

### 🚧 Phase 2: CLI Integration (TODO - 2-3 hours)

**Tasks**:
- [ ] Integrate into `codebase_scraper.py`
- [ ] Integrate into `doc_scraper.py`
- [ ] Integrate into `github_scraper.py`
- [ ] Add `--enhance-workflow` flag
- [ ] Add `--enhance-stage` flag
- [ ] Add `--var` flag
- [ ] Add `--workflow-dry-run` flag

**Example After Integration**:
```bash
skill-seekers analyze . --enhance-workflow security-focus  # Will work!
```

### 📋 Phase 3: More Workflows (TODO - 2-3 hours)

**Workflows to Create**:
- [ ] `performance-focus.yaml` - Performance analysis
- [ ] `code-quality.yaml` - Code quality and maintainability
- [ ] `documentation.yaml` - Generate comprehensive docs
- [ ] `testing.yaml` - Focus on test coverage and quality
- [ ] `architecture.yaml` - Architectural patterns and design

### 🌐 Phase 4: Workflow Marketplace (FUTURE)

**Ideas**:
- Users can publish workflows
- `skill-seekers workflow search security`
- `skill-seekers workflow install user/workflow-name`
- Community-driven workflow library

---

## 🎓 Example Use Cases

### Use Case 1: Security Audit

```bash
# Analyze codebase with security focus
skill-seekers analyze . --enhance-workflow security-focus

# Result:
# - SKILL.md with security section
# - Security checklist
# - Security score
# - Critical findings
```

### Use Case 2: API Documentation

```bash
# Focus on API documentation
skill-seekers analyze . --enhance-workflow api-documentation

# Result:
# - Complete API reference
# - Endpoint documentation
# - Auth requirements
# - Request/response schemas
```

### Use Case 3: Team-Specific Workflow

```yaml
# .skill-seekers/team-workflow.yaml
name: "Team Code Review Workflow"
extends: "default.yaml"

stages:
  - name: "team_standards"
    type: "custom"
    prompt: |
      Check code against team standards:
      - Naming conventions
      - Error handling patterns
      - Logging standards
      - Comment requirements
```

```bash
skill-seekers analyze . --enhance-workflow .skill-seekers/team-workflow.yaml
```

---

## 🚀 Next Steps

1. **Test the demo**:
   ```bash
   python test_workflow_demo.py
   ```

2. **Create your workflow**:
   ```bash
   nano ~/.config/skill-seekers/workflows/my-workflow.yaml
   ```

3. **Wait for Phase 2** (CLI integration) to use it in actual commands

4. **Give feedback** on what workflows you need!

---

**Status**: Core engine complete, ready for CLI integration! 🎉
