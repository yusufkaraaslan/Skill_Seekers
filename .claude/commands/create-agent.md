---
name: create-agent
description: Enhanced agent creation system with atomic operations, validation, and intelligent context analysis. Combines automation efficiency with human strategic input through robust error handling and comprehensive verification.
version: 2.1.0
validation: comprehensive
error_handling: atomic
features: [context-analysis, atomic-operations, comprehensive-validation, agent-registry-integration]
parameters:
  - name: mode
    type: string
    description: Creation mode - 'smart' (context-aware questions), 'fast' (automated), 'interactive' (full wizard), 'advanced' (power-user with full control)
    default: smart
    enum: [smart, fast, interactive, advanced]
  - name: context
    type: string
    description: Target directory or repository path for context analysis
    default: .
  - name: specialization
    type: string
    description: Optional domain specialization hint
    required: false
  - name: template
    type: string
    description: Specific template to use (orchestrator, specialist, referee, security, performance, test, custom)
    required: false
    enum: [orchestrator, specialist, referee, security, performance, test, custom]
  - name: validation_level
    type: string
    description: Validation strictness level
    default: standard
    enum: [strict, standard, relaxed]
  - name: dry_run
    type: boolean
    description: Preview creation without writing files
    default: false
  - name: atomic
    type: boolean
    description: Use atomic operations with rollback capability
    default: true
---

# Create Agent Command

Smart hybrid agent creation that combines repository context analysis with strategic human input to generate personalized AI agents efficiently.

## Usage Examples

```bash
# Smart mode (recommended): Context-aware with 2-3 strategic questions
/create-agent --mode smart

# Fast mode: Fully automated generation with intelligent defaults
/create-agent --mode fast

# Interactive mode: Full wizard with comprehensive questions
/create-agent --mode interactive

# Targeted analysis with domain hints
/create-agent --mode smart --context ./src --specialization "security analysis"

# Template-specific generation
/create-agent --mode smart --template specialist
```

## Phase 1: Repository Context Analysis

The command begins by automatically analyzing the target repository to understand the development context, technology stack, and patterns that will inform intelligent question generation and agent customization.

### Context Mining Capabilities

1. **Technology Stack Detection**
   - Programming languages and frameworks
   - Package management dependencies
   - Development tools and build systems
   - Testing frameworks and methodologies

2. **Code Pattern Analysis**
   - Architectural patterns and design principles
   - Code organization and structure
   - Development methodologies (Agile, DevOps, etc.)
   - Documentation quality and completeness

3. **Security and Compliance Assessment**
   - Security-related files and configurations
   - Compliance frameworks and standards
   - Vulnerability scanning tools
   - Security testing practices

4. **Performance and Quality Metrics**
   - Code complexity and maintainability
   - Testing coverage and quality
   - Performance optimization patterns
   - Error handling and logging practices

## Phase 2: Intelligent Question Generation

Based on the repository context analysis, the command generates 2-3 strategic questions that focus on high-value decisions while avoiding irrelevant or generic inquiries.

### Smart Question Logic

```python
def generate_contextual_questions(context):
    questions = []

    # Security-focused questions for security repositories
    if context.has_security_files:
        questions.append({
            "question": f"Detected security focus in {context.security_files}. What's your primary security priority?",
            "header": "Security Focus",
            "options": [
                {"label": "Vulnerability Detection", "description": "Find and analyze security issues"},
                {"label": "Compliance", "description": "Ensure regulatory compliance"},
                {"label": "DevSecOps Integration", "description": "Security in CI/CD pipelines"}
            ],
            "multiSelect": True
        })

    # Performance questions for complex applications
    if context.complexity_score > 7:
        questions.append({
            "question": f"High complexity detected ({context.complexity_score}/10). What's your optimization priority?",
            "header": "Performance Focus",
            "options": [
                {"label": "Code Quality", "description": "Improve maintainability and readability"},
                {"label": "Performance", "description": "Optimize speed and resource usage"},
                {"label": "Testing", "description": "Enhance test coverage and quality"}
            ]
        })

    # Documentation questions for well-documented projects
    if context.documentation_quality > 7:
        questions.append({
            "question": "Strong documentation detected. What documentation enhancement do you need?",
            "header": "Documentation",
            "options": [
                {"label": "API Documentation", "description": "Generate comprehensive API docs"},
                {"label": "Code Examples", "description": "Create practical usage examples"},
                {"label": "Architecture Guides", "description": "Document system design and patterns"}
            ]
        })

    return questions[:3]  # Maximum 3 strategic questions
```

## Phase 3: Intelligent Agent Generation

Using the repository context and user responses, the command generates a highly personalized agent with:

### Personalized Agent Features

1. **Contextual Framework Selection**
   - Automatically chooses appropriate methodology (M.A.P.S., C.O.G.N.I.T.I.V.E., etc.)
   - Adapts framework complexity to repository needs
   - Integrates domain-specific patterns and practices

2. **Optimized Tool Configuration**
   - Selects tools based on detected development patterns
   - Configures tool-specific parameters for target repository
   - Ensures tool compatibility with existing workflows

3. **Intelligent Delegation Networks**
   - Designs agent relationships based on repository complexity
   - Creates complementary agent partnerships
   - Optimizes delegation patterns for detected use cases

4. **Domain-Specific Customization**
   - Integrates industry-specific knowledge and practices
   - Adapts communication style to project culture
   - Incorporates technology-specific optimization strategies

## Implementation Architecture

### Core Components

1. **Context Analyzer Module**
   ```python
   class RepositoryContextAnalyzer:
       def analyze_technology_stack(self, repo_path: str) -> TechStack
       def detect_code_patterns(self, repo_path: str) -> CodePatterns
       def assess_security_posture(self, repo_path: str) -> SecurityAssessment
       def evaluate_quality_metrics(self, repo_path: str) -> QualityMetrics
   ```

2. **Question Generator Module**
   ```python
   class SmartQuestionGenerator:
       def generate_contextual_questions(self, context: RepositoryContext) -> List[Question]
       def prioritize_questions(self, questions: List[Question]) -> List[Question]
       def validate_question_relevance(self, question: Question, context: RepositoryContext) -> bool
   ```

3. **Agent Generator Module**
   ```python
   class IntelligentAgentGenerator:
       def select_template(self, context: RepositoryContext, user_responses: UserResponses) -> Template
       def customize_framework(self, template: Template, context: RepositoryContext, user_responses: UserResponses) -> Framework
       def configure_tools(self, template: Template, context: RepositoryContext) -> ToolConfiguration
       def design_delegation_network(self, agent_spec: AgentSpec, context: RepositoryContext) -> DelegationNetwork
   ```

## Usage Patterns

### Smart Mode (Recommended)
```bash
/create-agent --mode smart
# Analyzes repository → Asks 2-3 strategic questions → Generates personalized agent
# Time: ~2 minutes
# Personalization: High
# User Effort: Low
```

### Fast Mode
```bash
/create-agent --mode fast
# Automated generation with intelligent defaults
# Time: ~30 seconds
# Personalization: Medium
# User Effort: None
```

### Interactive Mode
```bash
/create-agent --mode interactive
# Full wizard experience with comprehensive customization
# Time: ~5-10 minutes
# Personalization: Very High
# User Effort: High
```

### Targeted Generation
```bash
/create-agent --mode smart --context ./src --specialization "react development"
# Context-specific generation with domain hints
# Time: ~90 seconds
# Personalization: Very High
# User Effort: Low
```

## Error Handling and Fallbacks

### Robust Error Management
1. **Context Analysis Failures**
   - Graceful degradation to generic questions
   - Intelligent defaults based on common patterns
   - User notification with alternative approaches

2. **Question Response Issues**
   - Simplified question alternatives
   - Automatic default selection with explanation
   - Skip logic for non-critical questions

3. **Generation Problems**
   - Fallback to basic template generation
   - Validation with detailed error reporting
   - Manual override options for advanced users

## Success Metrics

### Performance Targets
- **Smart Mode Generation**: <2 minutes total
- **Question Relevance**: >85% contextual accuracy
- **User Satisfaction**: >90% perceived value
- **Agent Quality**: >95% validation pass rate

### Quality Indicators
- **Context Detection Accuracy**: >90% correct technology identification
- **Question Effectiveness**: >80% user responses used in generation
- **Personalization Score**: >85% domain-specific relevance
- **Error Rate**: <5% generation failures

## 🛡️ Enhanced Validation and Atomic Operations

### Comprehensive Validation System

Based on V2's bulletproof architecture, the enhanced create-agent includes multi-layer validation:

#### Layer 1: Input Validation
```python
# Validation requirements
Agent name requirements:
- 3-50 characters
- Alphanumeric, hyphens, underscores only
- Must be unique within project
- Cannot be a reserved name

Content requirements:
- Minimum 500 characters
- Must include required sections:
  - # Agent Name
  - ## Agent Identity
  - ## Core Purpose
  - ## Integration with Existing Agent Ecosystem
- Valid markdown syntax
- Proper YAML frontmatter

Tool requirements:
- Must be from allowed tool set
- Maximum 10 tools per agent
- Tool compatibility validation
```

#### Layer 2: Atomic File Creation
```python
# All-or-nothing operations with rollback
try:
    # Start atomic transaction
    transaction = AtomicAgentCreation()

    # Validate all inputs
    transaction.validate(request)

    # Create files atomically
    transaction.create_files(request)

    # Verify creation
    transaction.verify_creation()

    # Update registry
    transaction.update_registry()

    # Commit transaction
    transaction.commit()

except Exception as e:
    # Automatic rollback
    transaction.rollback()
    raise AgentCreationError(f"Creation failed: {e}")
```

#### Layer 3: Creation Verification
- File existence validation
- Content hash verification
- Structural integrity checks
- YAML frontmatter validation

### Error Handling and Recovery

#### Robust Error Management
```python
# Specific error handling with recovery
Validation Errors:
❌ Agent Creation Failed
🚫 Validation Error: Agent name 'test' already exists
💡 Suggestion: Try 'test-analyst' or 'test-validator'

Permission Errors:
❌ Agent Creation Failed
🚫 Permission Error: Cannot write to .claude/agents/
💡 Fix: Run 'chmod 755 .claude/agents/' and retry

System Errors:
❌ Agent Creation Failed
🚫 System Error: Disk space insufficient
💡 Fix: Free up disk space and retry
```

### Advanced Mode Features

#### Power User Capabilities
```bash
# Advanced mode with full control
/create-agent --mode advanced --template custom --validation-level strict

# Batch creation capabilities
/create-agent --mode advanced --batch agent_configs.json

# Custom template integration
/create-agent --mode advanced --template-path ./custom_templates/
```

#### Enhanced Monitoring
```bash
# Operation health monitoring
/create-agent --health-check

# Recent operations tracking
/create-agent --recent-operations

# System diagnostics
/create-agent --diagnose
```

### Security and Performance

#### Security Features
- Content sanitization for malicious patterns
- YAML frontmatter validation
- Access control verification
- Security vulnerability scanning

#### Performance Optimization
- Parallel processing for validation and creation
- Caching of validation results
- Optimized template processing
- Background operation support

This enhanced smart hybrid approach revolutionizes agent creation by combining the efficiency of automation with the strategic insight of human decision-making, while maintaining bulletproof validation and atomic operations for reliable agent generation.