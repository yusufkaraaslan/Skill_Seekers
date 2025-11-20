---
name: create-subagents
description: Expert guidance for creating, building, and using Claude Code subagents and the Task tool. Use when working with subagents, setting up agent configurations, understanding how agents work, or using the Task tool to launch specialized agents.
---

<objective>
Subagents are specialized Claude instances that run in isolated contexts with focused roles and limited tool access. This skill teaches you how to create effective subagents, write strong system prompts, configure tool access, and orchestrate multi-agent workflows using the Task tool.

Subagents enable delegation of complex tasks to specialized agents that operate autonomously without user interaction, returning their final output to the main conversation.
</objective>

<quick_start>
<workflow>
1. Run `/agents` command
2. Select "Create New Agent"
3. Choose project-level (`.claude/agents/`) or user-level (`~/.claude/agents/`)
4. Define the subagent:
   - **name**: lowercase-with-hyphens
   - **description**: When should this subagent be used?
   - **tools**: Optional comma-separated list (inherits all if omitted)
   - **model**: Optional (`sonnet`, `opus`, `haiku`, or `inherit`)
5. Write the system prompt (the subagent's instructions)
</workflow>

<example>
```markdown
---
name: code-reviewer
description: Expert code reviewer. Use proactively after code changes to review for quality, security, and best practices.
tools: Read, Grep, Glob, Bash
model: sonnet
---

<role>
You are a senior code reviewer focused on quality, security, and best practices.
</role>

<focus_areas>
- Code quality and maintainability
- Security vulnerabilities
- Performance issues
- Best practices adherence
</focus_areas>

<output_format>
Provide specific, actionable feedback with file:line references.
</output_format>
```
</example>
</quick_start>

<file_structure>
| Type | Location | Scope | Priority |
|------|----------|-------|----------|
| **Project** | `.claude/agents/` | Current project only | Highest |
| **User** | `~/.claude/agents/` | All projects | Lower |
| **Plugin** | Plugin's `agents/` dir | All projects | Lowest |

Project-level subagents override user-level when names conflict.
</file_structure>

<configuration>
<field name="name">
- Lowercase letters and hyphens only
- Must be unique
</field>

<field name="description">
- Natural language description of purpose
- Include when Claude should invoke this subagent
- Used for automatic subagent selection
</field>

<field name="tools">
- Comma-separated list: `Read, Write, Edit, Bash, Grep`
- If omitted: inherits all tools from main thread
- Use `/agents` interface to see all available tools
</field>

<field name="model">
- `sonnet`, `opus`, `haiku`, or `inherit`
- `inherit`: uses same model as main conversation
- If omitted: defaults to configured subagent model (usually sonnet)
</field>
</configuration>

<execution_model>
<critical_constraint>
**Subagents are black boxes that cannot interact with users.**

Subagents run in isolated contexts and return their final output to the main conversation. They:
- ✅ Can use tools like Read, Write, Edit, Bash, Grep, Glob
- ✅ Can access MCP servers and other non-interactive tools
- ❌ **Cannot use AskUserQuestion** or any tool requiring user interaction
- ❌ **Cannot present options or wait for user input**
- ❌ **User never sees subagent's intermediate steps**

The main conversation sees only the subagent's final report/output.
</critical_constraint>

<workflow_design>
**Designing workflows with subagents:**

Use **main chat** for:
- Gathering requirements from user (AskUserQuestion)
- Presenting options or decisions to user
- Any task requiring user confirmation/input
- Work where user needs visibility into progress

Use **subagents** for:
- Research tasks (API documentation lookup, code analysis)
- Code generation based on pre-defined requirements
- Analysis and reporting (security review, test coverage)
- Context-heavy operations that don't need user interaction

**Example workflow pattern:**
```
Main Chat: Ask user for requirements (AskUserQuestion)
  ↓
Subagent: Research API and create documentation (no user interaction)
  ↓
Main Chat: Review research with user, confirm approach
  ↓
Subagent: Generate code based on confirmed plan
  ↓
Main Chat: Present results, handle testing/deployment
```
</workflow_design>
</execution_model>

<system_prompt_guidelines>
<principle name="be_specific">
Clearly define the subagent's role, capabilities, and constraints.
</principle>

<principle name="use_pure_xml_structure">
Structure the system prompt with pure XML tags. Remove ALL markdown headings from the body.

```markdown
---
name: security-reviewer
description: Reviews code for security vulnerabilities
tools: Read, Grep, Glob, Bash
model: sonnet
---

<role>
You are a senior code reviewer specializing in security.
</role>

<focus_areas>
- SQL injection vulnerabilities
- XSS attack vectors
- Authentication/authorization issues
- Sensitive data exposure
</focus_areas>

<workflow>
1. Read the modified files
2. Identify security risks
3. Provide specific remediation steps
4. Rate severity (Critical/High/Medium/Low)
</workflow>
```
</principle>

<principle name="task_specific">
Tailor instructions to the specific task domain. Don't create generic "helper" subagents.

❌ Bad: "You are a helpful assistant that helps with code"
✅ Good: "You are a React component refactoring specialist. Analyze components for hooks best practices, performance anti-patterns, and accessibility issues."
</principle>
</system_prompt_guidelines>

<subagent_xml_structure>
Subagent.md files are system prompts consumed only by Claude. Like skills and slash commands, they should use pure XML structure for optimal parsing and token efficiency.

<recommended_tags>
Common tags for subagent structure:

- `<role>` - Who the subagent is and what it does
- `<constraints>` - Hard rules (NEVER/MUST/ALWAYS)
- `<focus_areas>` - What to prioritize
- `<workflow>` - Step-by-step process
- `<output_format>` - How to structure deliverables
- `<success_criteria>` - Completion criteria
- `<validation>` - How to verify work
</recommended_tags>

<intelligence_rules>
**Simple subagents** (single focused task):
- Use role + constraints + workflow minimum
- Example: code-reviewer, test-runner

**Medium subagents** (multi-step process):
- Add workflow steps, output_format, success_criteria
- Example: api-researcher, documentation-generator

**Complex subagents** (research + generation + validation):
- Add all tags as appropriate including validation, examples
- Example: mcp-api-researcher, comprehensive-auditor
</intelligence_rules>

<critical_rule>
**Remove ALL markdown headings (##, ###) from subagent body.** Use semantic XML tags instead.

Keep markdown formatting WITHIN content (bold, italic, lists, code blocks, links).

For XML structure principles and token efficiency details, see @skills/create-agent-skills/references/use-xml-tags.md - the same principles apply to subagents.
</critical_rule>
</subagent_xml_structure>

<invocation>
<automatic>
Claude automatically selects subagents based on the `description` field when it matches the current task.
</automatic>

<explicit>
You can explicitly invoke a subagent:

```
> Use the code-reviewer subagent to check my recent changes
```

```
> Have the test-writer subagent create tests for the new API endpoints
```
</explicit>
</invocation>

<management>
<using_agents_command>
Run `/agents` for an interactive interface to:
- View all available subagents
- Create new subagents
- Edit existing subagents
- Delete custom subagents
</using_agents_command>

<manual_editing>
You can also edit subagent files directly:
- Project: `.claude/agents/subagent-name.md`
- User: `~/.claude/agents/subagent-name.md`
</manual_editing>
</management>

<reference>
**Core references**:

**Subagent usage and configuration**: [references/subagents.md](references/subagents.md)
- File format and configuration
- Model selection (Sonnet 4.5 + Haiku 4.5 orchestration)
- Tool security and least privilege
- Prompt caching optimization
- Complete examples

**Writing effective prompts**: [references/writing-subagent-prompts.md](references/writing-subagent-prompts.md)
- Core principles and XML structure
- Description field optimization for routing
- Extended thinking for complex reasoning
- Security constraints and strong modal verbs
- Success criteria definition

**Advanced topics**:

**Evaluation and testing**: [references/evaluation-and-testing.md](references/evaluation-and-testing.md)
- Evaluation metrics (task completion, tool correctness, robustness)
- Testing strategies (offline, simulation, online monitoring)
- Evaluation-driven development
- G-Eval for custom criteria

**Error handling and recovery**: [references/error-handling-and-recovery.md](references/error-handling-and-recovery.md)
- Common failure modes and causes
- Recovery strategies (graceful degradation, retry, circuit breakers)
- Structured communication and observability
- Anti-patterns to avoid

**Context management**: [references/context-management.md](references/context-management.md)
- Memory architecture (STM, LTM, working memory)
- Context strategies (summarization, sliding window, scratchpads)
- Managing long-running tasks
- Prompt caching interaction

**Orchestration patterns**: [references/orchestration-patterns.md](references/orchestration-patterns.md)
- Sequential, parallel, hierarchical, coordinator patterns
- Sonnet + Haiku orchestration for cost/performance
- Multi-agent coordination
- Pattern selection guidance

**Debugging and troubleshooting**: [references/debugging-agents.md](references/debugging-agents.md)
- Logging, tracing, and correlation IDs
- Common failure types (hallucinations, format errors, tool misuse)
- Diagnostic procedures
- Continuous monitoring
</reference>

<success_criteria>
A well-configured subagent has:

- Valid YAML frontmatter (name matches file, description includes triggers)
- Clear role definition in system prompt
- Appropriate tool restrictions (least privilege)
- XML-structured system prompt with role, approach, and constraints
- Description field optimized for automatic routing
- Successfully tested on representative tasks
- Model selection appropriate for task complexity (Sonnet for reasoning, Haiku for simple tasks)
</success_criteria>
