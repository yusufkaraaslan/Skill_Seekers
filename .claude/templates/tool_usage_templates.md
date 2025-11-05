# Tool Usage Templates for Enhanced Agent Validation

This document provides comprehensive tool usage templates for orchestrator and referee agents to ensure they meet the enhanced validation requirements.

## Orchestrator Agent Tool Usage Template

### Template 1: Security Audit Orchestration

```markdown
## Security Audit Orchestration Workflow

### Step 1: Context Gathering (MANDATORY)
**Objective**: Understand the codebase structure and security landscape before delegation.

#### Tool Usage:
```
Read: cli/constants.py
Read: requirements.txt
Read: README.md
Read: .claude/agents/security-analyst.md

Grep: pattern="security|auth|password|secret|key|token" path="cli/" output_mode="files_with_matches"
Grep: pattern="import.*requests|import.*urllib|import.*http" path="cli/" output_mode="content"
Grep: pattern="subprocess|os\.system|exec|eval" path="cli/" output_mode="files_with_matches"
```

#### Expected Evidence:
- Files read and their key content summaries
- Security-related files identified
- Network-related imports discovered
- Potential command execution points located

**Analysis**: Found 8 security-related files, 3 HTTP-related imports, and 2 files with subprocess usage. This indicates a web-facing application with potential security vulnerabilities requiring specialized analysis.

### Step 2: Parallel Delegation (MANDATORY)
**Objective**: Deploy specialized security analysts for different domains.

#### Tool Usage:
```
Task: description="Web scraping security analysis" subagent_type="security-analyst" model="haiku"
Task: description="GitHub integration security analysis" subagent_type="security-analyst" model="haiku"
Task: description="PDF processing security analysis" subagent_type="security-analyst" model="haiku"
Task: description="MCP server security analysis" subagent_type="security-analyst" model="haiku"
Task: description="Dependency security analysis" subagent_type="security-analyst" model="haiku"
```

#### Expected Evidence:
- 5 parallel tasks deployed with specific descriptions
- Appropriate model selection (haiku for cost efficiency)
- Clear subagent_type specifications

### Step 3: Progress Monitoring (RECOMMENDED)
**Objective**: Monitor delegated task progress.

#### Tool Usage:
```
Bash: ls -la output/ | head -10
Bash: find output/ -name "*.md" -exec wc -l {} \;
```

#### Expected Evidence:
- Output directory status
- File count and size verification

### Step 4: Result Synthesis (MANDATORY)
**Objective**: Analyze and integrate all security analysis results.

#### Tool Usage:
```
Read: output/web_scraping_security_analysis.md
Read: output/github_integration_security_analysis.md
Read: output/pdf_processing_security_analysis.md
Read: output/mcp_server_security_analysis.md
Read: output/dependency_security_analysis.md

Grep: pattern="CRITICAL|HIGH|MEDIUM|LOW" path="output/*.md" output_mode="content" -n
Grep: pattern="CVE-|vulnerability|issue" path="output/*.md" output_mode="content" -n
```

#### Expected Evidence:
- All 5 analysis reports read and summarized
- Severity classifications extracted
- Vulnerability counts and patterns identified

**Synthesis**: Analyzed 5 security domain reports revealing 10 vulnerabilities: 3 Critical, 3 High, 4 Medium. Cross-domain patterns identified: input validation failures across all components.

### Step 5: Final Report Generation
**Objective**: Generate comprehensive security audit report.

#### Tool Usage:
```
Write: file_path="output/comprehensive_security_audit_report.md" content="# Security Audit Report\n\n## Executive Summary\n..."
```

#### Expected Evidence:
- Structured report with executive summary
- Consolidated findings matrix
- Prioritized remediation roadmap
```

### Template 2: Code Analysis Orchestration

```markdown
## Code Analysis Orchestration Workflow

### Step 1: Context Gathering (MANDATORY)
```
Read: pyproject.toml
Read: setup.py
Read: requirements.txt
Read: .gitignore

Grep: pattern="class\s+\w+|def\s+\w+" path="src/" output_mode="count"
Grep: pattern="import\s+" path="src/" output_mode="content" | head -20
Glob: pattern="src/**/*.py" path="./"
```

**Analysis**: Python project with 15 modules, 45 classes, and 120 functions identified.

### Step 2: Specialized Delegation (MANDATORY)
```
Task: description="Code structure analysis" subagent_type="code-analyst" model="haiku"
Task: description="Security vulnerability scan" subagent_type="security-analyst" model="haiku"
Task: description="Documentation review" subagent_type="documentation-agent" model="haiku"
```

### Step 3: Result Integration (MANDATORY)
```
Read: output/code_structure_analysis.md
Read: output/security_vulnerability_scan.md
Read: output/documentation_review.md

Grep: pattern="TODO|FIXME|XXX" path="src/" output_mode="content"
```

**Synthesis**: Code analysis reveals good structure but 3 security issues and incomplete documentation.
```

## Referee Agent Tool Usage Template

### Template 1: Security Analysis Convergent Synthesis

```markdown
## Security Analysis Referee Synthesis

### Step 1: Load Specification (MANDATORY)
```
Read: security_audit_specification.md
```

**Extracted Criteria**:
- Must identify actual vulnerabilities with evidence
- Must provide CVSS severity ratings
- Must include specific remediation steps
- Must demonstrate tool usage in analysis

### Step 2: Load All Candidates (MANDATORY)
```
Read: candidate_1_security_analysis.md
Read: candidate_2_security_analysis.md
Read: candidate_3_security_analysis.md
```

**Candidate Analysis**:
- Candidate 1: 8 vulnerabilities identified, theoretical analysis
- Candidate 2: 5 vulnerabilities identified, partial tool usage
- Candidate 3: 12 vulnerabilities identified, comprehensive approach

### Step 3: Objective Validation (MANDATORY)
```
Bash: python3 -c "
import json
import re

def analyze_candidate(filename):
    with open(filename) as f:
        content = f.read()

    return {
        'vulnerability_count': len(re.findall(r'vulnerability|CVE-', content, re.IGNORECASE)),
        'severity_levels': len(re.findall(r'(critical|high|medium|low)', content, re.IGNORECASE)),
        'tool_usage': len(re.findall(r'bash:|pip-audit|safety|bandit', content)),
        'remediation_steps': len(re.findall(r'recommend|fix|patch', content, re.IGNORECASE)),
        'evidence_quality': len(re.findall(r'line\s+\d+|file\s*:|found\s+\d+', content, re.IGNORECASE))
    }

candidates = {}
for i in range(1, 4):
    candidates[f'candidate_{i}'] = analyze_candidate(f'candidate_{i}_security_analysis.md')

# Calculate scores
for candidate, metrics in candidates.items():
    metrics['total_score'] = (
        metrics['vulnerability_count'] * 10 +
        metrics['severity_levels'] * 5 +
        metrics['tool_usage'] * 20 +
        metrics['remediation_steps'] * 5 +
        metrics['evidence_quality'] * 3
    )

print(json.dumps(candidates, indent=2))
"
```

**Validation Output**:
```json
{
  "candidate_1": {
    "vulnerability_count": 8,
    "severity_levels": 6,
    "tool_usage": 0,
    "remediation_steps": 4,
    "evidence_quality": 2,
    "total_score": 122
  },
  "candidate_2": {
    "vulnerability_count": 5,
    "severity_levels": 4,
    "tool_usage": 3,
    "remediation_steps": 3,
    "evidence_quality": 5,
    "total_score": 118
  },
  "candidate_3": {
    "vulnerability_count": 12,
    "severity_levels": 10,
    "tool_usage": 8,
    "remediation_steps": 8,
    "evidence_quality": 12,
    "total_score": 268
  }
}
```

### Step 4: Pattern Analysis (MANDATORY)
```
Grep: pattern="bash:" path="candidate_*_security_analysis.md" output_mode="content" -n
Grep: pattern="pip-audit|safety|bandit" path="candidate_*_security_analysis.md" output_mode="content"
Grep: pattern="CVE-\\d{4}-\\d{4}" path="candidate_*_security_analysis.md" output_mode="content"
Grep: pattern="cli/[^:]+:\\d+" path="candidate_*_security_analysis.md" output_mode="content"
```

**Pattern Analysis Results**:
- Candidate 1: No tool usage evidence, theoretical analysis only
- Candidate 2: 3 tool invocations, some file references
- Candidate 3: 8 tool invocations, specific file/line references, CVE numbers

### Step 5: Deterministic Selection
**Selection Logic**: Candidate 3 selected based on highest objective score (268) with comprehensive tool usage evidence.

### Step 6: Structured Output (MANDATORY)
```
Write: file_path="synthesis_results.json" content='{"status": "SUCCESS", "selected_candidate": "candidate_3", "score": 268, "selection_reason": "Highest vulnerability count with comprehensive tool usage evidence and specific file references", "validation_metrics": {"tool_usage_evidence": 8, "file_references": 12, "cve_identified": 6}}'
```

**Final Report**:
- Selected candidate_3 with score 268
- Comprehensive tool usage validation completed
- Structured JSON output generated for programmatic processing
```

### Template 2: Code Implementation Referee Synthesis

```markdown
## Code Implementation Referee Synthesis

### Step 1: Load Specification (MANDATORY)
```
Read: implementation_specification.md
```

**Criteria**: Must implement authentication system, validate inputs, include tests.

### Step 2: Load All Candidates (MANDATORY)
```
Read: candidate_1_implementation.py
Read: candidate_2_implementation.py
Read: candidate_3_implementation.py
```

### Step 3: Code Quality Validation (MANDATORY)
```
Bash: python3 -c "
import ast
import json

def analyze_code_quality(filename):
    with open(filename) as f:
        content = f.read()

    try:
        tree = ast.parse(content)

        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

        docstrings = sum(1 for node in functions + classes if ast.get_docstring(node))

        return {
            'functions_count': len(functions),
            'classes_count': len(classes),
            'docstring_coverage': docstrings / len(functions + classes) if functions + classes else 0,
            'lines_of_code': len(content.splitlines()),
            'complexity_indicators': content.count('if ') + content.count('for ') + content.count('while ')
        }
    except SyntaxError as e:
        return {'error': str(e), 'score': 0}

candidates = {}
for i in range(1, 4):
    candidates[f'candidate_{i}'] = analyze_code_quality(f'candidate_{i}_implementation.py')

print(json.dumps(candidates, indent=2))
"
```

### Step 4: Functional Validation (MANDATORY)
```
Bash: python3 -m pytest test_candidate_*.py -v --tb=short 2>/dev/null || echo "Tests not available"
Bash: python3 candidate_*_implementation.py --help 2>/dev/null || echo "Help not available"
```

### Step 5: Security Validation (MANDATORY)
```
Grep: pattern="eval|exec|subprocess|os\.system" path="candidate_*_implementation.py" output_mode="content" -n
Grep: pattern="password|secret|key.*=.*['\"][^'\"]+['\"]" path="candidate_*_implementation.py" output_mode="content" -n
Bash: bandit -r candidate_*_implementation.py -f json 2>/dev/null || echo "Bandit not available"
```

### Step 6: Selection and Output
```
Write: file_path="implementation_synthesis.json" content='{"status": "SUCCESS", "selected_candidate": "candidate_2", "score": 185, "selection_reason": "Best balance of code quality, functionality, and security practices"}'
```
```

## Tool Usage Validation Checklist

### For Orchestrator Agents:
- [ ] **Context Gathering**: Read relevant files before delegation
- [ ] **Pattern Analysis**: Use Grep to search for relevant patterns
- [ ] **Parallel Delegation**: Use Task tool for concurrent subagent deployment
- [ ] **Result Reading**: Read all subagent outputs before synthesis
- [ ] **Evidence Reporting**: Report specific tools used and results obtained

### For Referee Agents:
- [ ] **Specification Loading**: Read all specification and requirement files
- [ ] **Candidate Loading**: Read ALL candidate files for analysis
- [ ] **Objective Validation**: Execute Bash commands for scoring (no theoretical analysis)
- [ ] **Pattern Analysis**: Use Grep for cross-candidate pattern analysis
- [ ] **Structured Output**: Generate JSON output using Write tool
- [ ] **Evidence Collection**: Report all tool invocations and their outputs

## Common Anti-Patterns to Avoid

### Orchestrator Anti-Patterns:
1. **"I would deploy security analysts..."** → Must actually use Task tool
2. "The codebase appears to have..." → Must actually Read files and Grep patterns
3. "Based on the reports..." → Must actually Read the report files
4. "I will coordinate..." → Must actually demonstrate coordination with tools

### Referee Anti-Patterns:
1. "Candidate 1 seems better because..." → Must use objective validation
2. "The theoretical analysis suggests..." → Must execute actual validation commands
3. "I would select candidate 2 because..." → Must provide objective scoring
4. "The code quality appears to be..." → Must execute actual quality checks

## Validation Success Criteria

### Orchestrator Success:
- Context gathered before delegation (≥ 2 files read)
- Parallel deployment demonstrated (≥ 2 concurrent tasks)
- Results synthesized from actual file reads
- Evidence of tool usage throughout workflow

### Referee Success:
- All candidates loaded and analyzed
- Objective validation executed (Bash commands run)
- Pattern analysis performed (Grep commands executed)
- Structured JSON output generated
- Selection based on quantitative metrics

These templates ensure that orchestrator and referee agents meet the enhanced tool usage validation requirements and provide actual, evidence-based analysis rather than theoretical reasoning.