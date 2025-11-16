# Complete Guide to Using /create-agent

**For New Interns and Team Members**

This guide provides comprehensive instructions for using the `/create-agent` command with all parameters and practical examples for different use cases.

## **Quick Start**

```bash
# Basic usage (recommended for beginners)
/create-agent --mode smart

# Quick agent creation with defaults
/create-agent --mode fast
```

---

## **Parameter Overview**

```bash
/create-agent [parameter-name] [value] [parameter-name] [value] ...
```

## **Core Parameters**

### **1. `--mode` - Creation Strategy**
**Default:** `smart`
**Options:** `smart`, `fast`, `interactive`, `advanced`

#### **Smart Mode (Recommended for Beginners)**
```bash
/create-agent --mode smart
```
**When to Use:** Your first choice for most situations
- Analyzes your repository context automatically
- Asks 2-3 strategic questions based on detected patterns
- Perfect balance of automation and customization

**Example:** Creates a React specialist agent after detecting React in your codebase, then asks about your primary focus (performance, testing, or documentation).

#### **Fast Mode**
```bash
/create-agent --mode fast
```
**When to Use:** When you need an agent quickly
- No questions asked, fully automated
- Uses repository analysis to make smart default choices
- Ideal for experienced users who need quick agents

**Example:** Detects Python backend and automatically creates a code-analyzer agent with Python-specific tools and patterns.

#### **Interactive Mode**
```bash
/create-agent --mode interactive
```
**When to Use:** When you want complete control
- Complete wizard with detailed questions
- Maximum personalization possible
- Best for complex or specialized requirements

**Example:** Walks through every aspect: agent type, tools, delegation patterns, communication style, validation rules, and integration preferences.

#### **Advanced Mode**
```bash
/create-agent --mode advanced
```
**When to Use:** For power users with specific technical requirements
- Direct parameter control without guided questions
- Batch creation capabilities
- Custom template integration

**Example:** Creates multiple agents in sequence using a configuration file with custom templates and specific validation rules.

---

### **2. `--context` - Analysis Scope**
**Default:** `.` (current directory)

#### **Project-Specific Analysis**
```bash
/create-agent --mode smart --context ./frontend
```
**When to Use:** Focus analysis on specific directory
- Analyzes only the frontend folder for React patterns
- Ignores backend code in analysis
- Perfect for monorepos with distinct components

#### **Cross-Repository Analysis**
```bash
/create-agent --mode smart --context ../shared-libs
```
**When to Use:** Create agents for shared dependencies
- Analyzes utility libraries and common patterns
- Creates agents specialized in your organization's shared code
- Ideal for creating standardization agents

#### **External Repository Analysis**
```bash
/create-agent --mode smart --context ~/projects/legacy-system
```
**When to Use:** Modernize legacy systems
- Analyzes old codebase patterns
- Creates modernization specialists
- Helps with migration planning

---

### **3. `--specialization` - Domain Focus**
**No default - optional hint**

#### **Security Focus**
```bash
/create-agent --mode smart --specialization "security analysis"
```
**When to Use:** For security-focused projects
- Prioritizes security patterns and tools
- Adds vulnerability detection capabilities
- Emphasizes compliance and best practices
- **Result:** Agent specializes in OWASP compliance, dependency scanning, and security code review

#### **Performance Focus**
```bash
/create-agent --mode smart --specialization "performance optimization"
```
**When to Use:** For performance-critical applications
- Adds profiling and monitoring tools
- Focuses on bottleneck detection
- Emphasizes optimization strategies
- **Result:** Agent specializes in performance profiling, memory leak detection, and optimization recommendations

#### **Machine Learning Focus**
```bash
/create-agent --mode smart --specialization "ML pipeline development"
```
**When to Use:** For data science and ML projects
- Adds data validation and model evaluation tools
- Focuses on pipeline optimization
- Emphasizes experiment tracking
- **Result:** Agent specializes in ML workflow optimization, model validation, and data pipeline integrity

---

### **4. `--template` - Agent Architecture**
**Default:** Automatically selected based on context

#### **Specialist Template**
```bash
/create-agent --mode fast --template specialist
```
**When to Use:** For domain-specific expertise
- Single domain focus
- Deep knowledge integration
- Tool optimization for specific tasks
- **Example:** Database optimization specialist with query analysis, indexing tools, and performance monitoring

#### **Orchestrator Template**
```bash
/create-agent --mode fast --template orchestrator
```
**When to Use:** For multi-agent coordination
- Delegates to multiple specialists
- Synthesizes results from parallel agents
- Manages complex workflows
- **Example:** Code review orchestrator that delegates to security-analyst, performance-auditor, and test-generator agents

#### **Security Template**
```bash
/create-agent --mode fast --template security
```
**When to Use:** For security-first development
- Pre-configured security tools
- Compliance checking capabilities
- Vulnerability assessment focus
- **Example:** DevSecOps specialist with SAST, dependency scanning, and compliance checking

#### **Custom Template**
```bash
/create-agent --mode advanced --template custom --template-path ./my-templates/research-agent.md
```
**When to Use:** For unique agent requirements
- Custom agent architecture
- Specialized toolsets
- Organization-specific patterns
- **Example:** Research paper analysis agent with academic database integration and citation management

---

### **5. `--validation_level` - Strictness Control**
**Default:** `standard`
**Options:** `strict`, `standard`, `relaxed`

#### **Strict Validation**
```bash
/create-agent --mode advanced --validation_level strict
```
**When to Use:** For production-critical agents
- Enforces all security requirements
- Validates all tool combinations
- Comprehensive structural checks
- Prevents any potentially unsafe operations

#### **Relaxed Validation**
```bash
/create-agent --mode fast --validation_level relaxed
```
**When to Use:** For rapid prototyping and experimentation
- Allows experimental tool combinations
- Minimal structural requirements
- Quick creation for testing
- **Example:** Creating prototype agents for exploration without strict compliance checks

---

### **6. `--dry_run` - Preview Mode**
**Default:** `false`

#### **Preview Agent Creation**
```bash
/create-agent --mode smart --dry_run true
```
**When to Use:** Test before committing
- Shows what would be created
- Validates parameters without file creation
- Perfect for testing complex configurations
- **Output:** Detailed preview of agent structure, tools, and integration points

#### **Batch Testing**
```bash
/create-agent --mode advanced --batch config.json --dry_run true
```
**When to Use:** Test multiple agent configurations
- Validates entire batch before creation
- Identifies potential conflicts
- Ensures compatibility across agents

---

### **7. `--atomic` - Operation Safety**
**Default:** `true`

#### **Atomic Operations (Default)**
```bash
/create-agent --mode smart --atomic true
```
**When to Use:** For safe agent creation
- All-or-nothing file creation
- Automatic rollback on failures
- Leaves system in consistent state
- **Result:** Either complete success or no changes made

#### **Non-Atomic Operations**
```bash
/create-agent --mode fast --atomic false
```
**When to Use:** For debugging and development
- Partial creation for debugging
- Manual cleanup and fixes
- Development of agent creation system
- **Caution:** May leave system in inconsistent state if creation fails

---

## **Real-World Usage Scenarios**

### **Scenario 1: Startup Building React App**
```bash
# Create a React specialist with performance focus
/create-agent --mode smart --context ./src --specialization "React optimization"
```
**Result:** Creates agent that:
- Detects React patterns and performance bottlenecks
- Suggests component optimization strategies
- Analyzes bundle size and loading performance
- Recommends best practices for React development

### **Scenario 2: Enterprise Security Team**
```bash
# Create security orchestrator for large codebase
/create-agent --mode advanced --template orchestrator --specialization "enterprise security" --validation_level strict
```
**Result:** Creates agent that:
- Coordinates multiple security specialists
- Enforces enterprise security policies
- Manages compliance reporting workflows
- Integrates with existing security tools

### **Scenario 3: Data Science Team**
```bash
# Create ML pipeline specialist
/create-agent --mode smart --context ./ml-pipelines --specialization "MLOps" --template specialist
```
**Result:** Creates agent that:
- Optimizes ML pipeline performance
- Validates data integrity and model performance
- Suggests experiment improvements
- Manages model deployment strategies

### **Scenario 4: Legacy System Modernization**
```bash
# Preview modernization agent before creation
/create-agent --mode advanced --context ~/projects/legacy-system --specialization "modernization" --template custom --template-path ./modernization-templates/ --dry_run true
```
**Result:** Shows preview of agent that would:
- Analyze legacy code patterns
- Suggest modern alternatives
- Plan migration strategies
- Estimate modernization effort

### **Scenario 5: Microservices Architecture**
```bash
# Create microservices orchestrator
/create-agent --mode smart --specialization "microservices" --template orchestrator --validation_level standard
```
**Result:** Creates agent that:
- Coordinates across multiple service specialists
- Analyzes service communication patterns
- Suggests architecture improvements
- Monitors system-wide performance

### **Scenario 6: Rapid Prototyping Session**
```bash
# Quick test agent for experimentation
/create-agent --mode fast --validation_level relaxed --atomic false
```
**Result:** Creates agent for:
- Quick code analysis experiments
- Testing new tool combinations
- Prototyping custom workflows
- Rapid iteration without strict requirements

### **Scenario 7: Compliance-Heavy Organization**
```bash
# Create compliance specialist with strict validation
/create-agent --mode advanced --template security --specialization "regulatory compliance" --validation_level strict --dry_run true
```
**Result:** Creates agent that ensures:
- GDPR/CCPA compliance checking
- Audit trail maintenance
- Regulatory reporting automation
- Policy enforcement across codebase

### **Scenario 8: Educational Platform**
```bash
# Create code education specialist
/create-agent --mode smart --specialization "code education" --template specialist --context ./course-materials
```
**Result:** Creates agent that:
- Generates educational code examples
- Creates step-by-step tutorials
- Validates coding assignments
- Suggests learning improvements

---

## **Recommended Parameter Combinations**

### **For Beginners**
```bash
# Safe and easy starting point
/create-agent --mode smart --validation_level standard
```

### **For Development**
```bash
# Balanced development workflow
/create-agent --mode smart --validation_level standard
```

### **For Production**
```bash
# Maximum safety and reliability
/create-agent --mode advanced --validation_level strict --atomic true
```

### **For Experimentation**
```bash
# Quick testing without commitment
/create-agent --mode fast --validation_level relaxed --dry_run true
```

### **For Complex Workflows**
```bash
# Multi-agent coordination
/create-agent --mode advanced --template orchestrator --validation_level strict
```

---

## **Parameter Priority Order**

When multiple parameters are used, they interact in this order:

1. `--mode` (determines interaction style)
2. `--template` (overrides automatic selection)
3. `--validation_level` (affects safety and strictness)
4. `--specialization` (guides content focus)
5. `--context` (determines analysis scope)
6. `--atomic` (affects operation safety)
7. `--dry_run` (enables preview mode)

---

## **Tips for New Users**

### **First Time Using /create-agent**
1. **Start simple:** Use `/create-agent --mode smart`
2. **Use dry_run:** Add `--dry_run true` to preview before creating
3. **Read the output:** The system tells you what it's doing
4. **Ask questions:** If unsure, use interactive mode

### **Common Mistakes to Avoid**
1. **Don't skip validation:** Keep `--validation_level standard` unless you know what you're doing
2. **Don't use non-atomic unless necessary:** Keep `--atomic true` for safety
3. **Don't ignore dry_run:** Always preview complex configurations
4. **Don't use advanced mode initially:** Start with smart or fast mode

### **Getting Help**
- Use `--mode interactive` for guided assistance
- Use `--dry_run true` to test configurations
- Check the generated agent files after creation
- Refer to existing agents in `.claude/agents/` for examples

---

## **Quick Reference Card**

| Parameter | Default | Common Values | When to Use |
|-----------|---------|---------------|-------------|
| `--mode` | `smart` | `fast`, `interactive`, `advanced` | Determines interaction style |
| `--context` | `.` | `./src`, `../shared` | Focus analysis scope |
| `--specialization` | none | `"security"`, `"performance"` | Domain expertise hint |
| `--template` | auto | `specialist`, `orchestrator` | Agent architecture |
| `--validation_level` | `standard` | `strict`, `relaxed` | Safety strictness |
| `--dry_run` | `false` | `true` | Preview mode |
| `--atomic` | `true` | `false` | Operation safety |

---

## **Summary**

The `/create-agent` command is a powerful tool for creating specialized AI agents tailored to your specific needs. Start with the smart mode, use dry_run for testing, and gradually explore more advanced parameters as you become comfortable with the system.

**Remember:** The best agents come from understanding your specific needs and choosing parameters that match your use case. Don't hesitate to experiment with different combinations using the dry_run feature!

---

*For questions or additional help, refer to the agent examples in `.claude/agents/` or ask senior team members for guidance.*