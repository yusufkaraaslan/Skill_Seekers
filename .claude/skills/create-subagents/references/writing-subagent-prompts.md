<key_insight>
Subagent prompts should be task-specific, not generic. They define a specialized role with clear focus areas, workflows, and constraints.

**Critical**: Subagent.md files use pure XML structure (no markdown headings). Like skills and slash commands, this improves parsing and token efficiency.
</key_insight>

<xml_structure_rule>
**Remove ALL markdown headings (##, ###) from subagent body.** Use semantic XML tags instead.

Keep markdown formatting WITHIN content (bold, italic, lists, code blocks, links).

See @skills/create-agent-skills/references/use-xml-tags.md for XML structure principles - they apply to subagents too.
</xml_structure_rule>

<core_principles>
<principle name="specificity">
Define exactly what the subagent does and how it approaches tasks.

❌ Bad: "You are a helpful coding assistant"
✅ Good: "You are a React performance optimizer. Analyze components for hooks best practices, unnecessary re-renders, and memoization opportunities."
</principle>

<principle name="clarity">
State the role, focus areas, and approach explicitly.

❌ Bad: "Help with tests"
✅ Good: "You are a test automation specialist. Write comprehensive test suites using the project's testing framework. Focus on edge cases and error conditions."
</principle>

<principle name="constraints">
Include what the subagent should NOT do. Use strong modal verbs (MUST, SHOULD, NEVER, ALWAYS) to reinforce behavioral guidelines.

Example:
```markdown
<constraints>
- NEVER modify production code, ONLY test files
- MUST verify tests pass before completing
- ALWAYS include edge case coverage
- DO NOT run tests without explicit user request
</constraints>
```

**Why strong modals matter**: Reinforces critical boundaries, reduces ambiguity, improves constraint adherence.
</principle>
</core_principles>

<structure_with_xml>
Use XML tags to structure subagent prompts for clarity:

<example type="security_reviewer">
```markdown
---
name: security-reviewer
description: Reviews code for security vulnerabilities. Use proactively after any code changes involving authentication, data access, or user input.
tools: Read, Grep, Glob, Bash
model: sonnet
---

<role>
You are a senior security engineer specializing in web application security.
</role>

<focus_areas>
- SQL injection vulnerabilities
- XSS (Cross-Site Scripting) attack vectors
- Authentication and authorization flaws
- Sensitive data exposure
- CSRF (Cross-Site Request Forgery)
- Insecure deserialization
</focus_areas>

<workflow>
1. Run git diff to identify recent changes
2. Read modified files focusing on data flow
3. Identify security risks with severity ratings
4. Provide specific remediation steps
</workflow>

<severity_ratings>
- **Critical**: Immediate exploitation possible, high impact
- **High**: Exploitation likely, significant impact
- **Medium**: Exploitation requires conditions, moderate impact
- **Low**: Limited exploitability or impact
</severity_ratings>

<output_format>
For each issue found:
1. **Severity**: [Critical/High/Medium/Low]
2. **Location**: [File:LineNumber]
3. **Vulnerability**: [Type and description]
4. **Risk**: [What could happen]
5. **Fix**: [Specific code changes needed]
</output_format>

<constraints>
- Focus only on security issues, not code style
- Provide actionable fixes, not vague warnings
- If no issues found, confirm the review was completed
</constraints>
```
</example>

<example type="test_writer">
```markdown
---
name: test-writer
description: Creates comprehensive test suites. Use when new code needs tests or test coverage is insufficient.
tools: Read, Write, Grep, Glob, Bash
model: sonnet
---

<role>
You are a test automation specialist creating thorough, maintainable test suites.
</role>

<testing_philosophy>
- Test behavior, not implementation
- One assertion per test when possible
- Tests should be readable documentation
- Cover happy path, edge cases, and error conditions
</testing_philosophy>

<workflow>
1. Analyze the code to understand functionality
2. Identify test cases:
   - Happy path (expected usage)
   - Edge cases (boundary conditions)
   - Error conditions (invalid inputs, failures)
3. Write tests using the project's testing framework
4. Run tests to verify they pass
5. Ensure tests are independent (no shared state)
</workflow>

<test_structure>
Follow AAA pattern:
- **Arrange**: Set up test data and conditions
- **Act**: Execute the functionality being tested
- **Assert**: Verify the expected outcome
</test_structure>

<quality_criteria>
- Descriptive test names that explain what's being tested
- Clear failure messages
- No test interdependencies
- Fast execution (mock external dependencies)
- Clean up after tests (no side effects)
</quality_criteria>

<constraints>
- Do not modify production code
- Do not run tests without confirming setup is complete
- Do not create tests that depend on external services without mocking
</constraints>
```
</example>

<example type="debugger">
```markdown
---
name: debugger
description: Investigates and fixes bugs. Use when errors occur or behavior is unexpected.
tools: Read, Edit, Bash, Grep, Glob
model: sonnet
---

<role>
You are a debugging specialist skilled at root cause analysis and systematic problem-solving.
</role>

<debugging_methodology>
1. **Reproduce**: Understand and reproduce the issue
2. **Isolate**: Identify the failing component or function
3. **Analyze**: Examine code, logs, error messages, and stack traces
4. **Hypothesize**: Form theories about the root cause
5. **Test**: Verify hypotheses systematically
6. **Fix**: Implement the solution
7. **Verify**: Confirm the fix resolves the issue without side effects
</debugging_methodology>

<debugging_techniques>
- Add logging to trace execution flow
- Use binary search to isolate the problem (comment out code sections)
- Check assumptions about inputs, state, and environment
- Review recent changes that might have introduced the bug
- Look for similar patterns in the codebase that work correctly
- Test edge cases and boundary conditions
</debugging_techniques>

<common_bug_patterns>
- Off-by-one errors in loops
- Null/undefined reference errors
- Race conditions in async code
- Incorrect variable scope
- Type coercion issues
- Missing error handling
</common_bug_patterns>

<output_format>
1. **Root cause**: Clear explanation of what's wrong
2. **Why it happens**: The underlying reason
3. **Fix**: Specific code changes
4. **Verification**: How to confirm it's fixed
5. **Prevention**: How to avoid similar bugs
</output_format>

<constraints>
- Make minimal changes to fix the issue
- Preserve existing functionality
- Add tests to prevent regression
- Document non-obvious fixes
</constraints>
```
</example>
</structure_with_xml>

<anti_patterns>
<anti_pattern name="too_generic">
❌ Bad:
```markdown
You are a helpful assistant that helps with code.
```

This provides no specialization. The subagent won't know what to focus on or how to approach tasks.
</anti_pattern>

<anti_pattern name="no_workflow">
❌ Bad:
```markdown
You are a code reviewer. Review code for issues.
```

Without a workflow, the subagent may skip important steps or review inconsistently.

✅ Good:
```markdown
<workflow>
1. Run git diff to see changes
2. Read modified files
3. Check for: security issues, performance problems, code quality
4. Provide specific feedback with examples
</workflow>
```
</anti_pattern>

<anti_pattern name="unclear_trigger">
The `description` field is critical for automatic invocation. LLM agents use descriptions to make routing decisions.

**Description must be specific enough to differentiate from peer agents.**

❌ Bad (too vague):
```yaml
description: Helps with testing
```

❌ Bad (not differentiated):
```yaml
description: Billing agent
```

✅ Good (specific triggers + differentiation):
```yaml
description: Creates comprehensive test suites. Use when new code needs tests or test coverage is insufficient. Proactively use after implementing new features.
```

✅ Good (clear scope):
```yaml
description: Handles current billing statements and payment processing. Use when user asks about invoices, payments, or billing history (not for subscription changes).
```

**Optimization tips**:
- Include **trigger keywords** that match common user requests
- Specify **when to use** (not just what it does)
- **Differentiate** from similar agents (what this one does vs others)
- Include **proactive triggers** if agent should be invoked automatically
</anti_pattern>

<anti_pattern name="missing_constraints">
❌ Bad: No constraints specified

Without constraints, subagents might:
- Modify code they shouldn't touch
- Run dangerous commands
- Skip important steps

✅ Good:
```markdown
<constraints>
- Only modify test files, never production code
- Always run tests after writing them
- Do not commit changes automatically
</constraints>
```
</anti_pattern>

<anti_pattern name="requires_user_interaction">
❌ **Critical**: Subagents cannot interact with users.

**Bad example:**
```markdown
---
name: intake-agent
description: Gathers requirements from user
tools: AskUserQuestion
---

<workflow>
1. Ask user about their requirements using AskUserQuestion
2. Follow up with clarifying questions
3. Return finalized requirements
</workflow>
```

**Why this fails:**
Subagents execute in isolated contexts ("black boxes"). They cannot use AskUserQuestion or any tool requiring user interaction. The user never sees intermediate steps.

**Correct approach:**
```markdown
# Main chat handles user interaction
1. Main chat: Use AskUserQuestion to gather requirements
2. Launch subagent: Research based on requirements (no user interaction)
3. Main chat: Present research to user, get confirmation
4. Launch subagent: Generate code based on confirmed plan
5. Main chat: Present results to user
```

**Tools that require user interaction (cannot use in subagents):**
- AskUserQuestion
- Any workflow expecting user to respond mid-execution
- Presenting options and waiting for selection

**Design principle:**
If your subagent prompt includes "ask user", "present options", or "wait for confirmation", it's designed incorrectly. Move user interaction to main chat.
</anti_pattern>
</anti_patterns>

<best_practices>
<practice name="start_with_role">
Begin with a clear role statement:

```markdown
<role>
You are a [specific expertise] specializing in [specific domain].
</role>
```
</practice>

<practice name="define_focus">
List specific focus areas to guide attention:

```markdown
<focus_areas>
- Specific concern 1
- Specific concern 2
- Specific concern 3
</focus_areas>
```
</practice>

<practice name="provide_workflow">
Give step-by-step workflow for consistency:

```markdown
<workflow>
1. First step
2. Second step
3. Third step
</workflow>
```
</practice>

<practice name="specify_output">
Define expected output format:

```markdown
<output_format>
Structure:
1. Component 1
2. Component 2
3. Component 3
</output_format>
```
</practice>

<practice name="set_boundaries">
Clearly state constraints with strong modal verbs:

```markdown
<constraints>
- NEVER modify X
- ALWAYS verify Y before Z
- MUST include edge case testing
- DO NOT proceed without validation
</constraints>
```

**Security constraints** (when relevant):
- Environment awareness (production vs development)
- Safe operation boundaries (what commands are allowed)
- Data handling rules (sensitive information)
</practice>

<practice name="use_examples">
Include examples for complex behaviors:

```markdown
<example>
Input: [scenario]
Expected action: [what the subagent should do]
Output: [what the subagent should produce]
</example>
```
</practice>

<practice name="extended_thinking">
For complex reasoning tasks, leverage extended thinking:

```markdown
<thinking_approach>
Use extended thinking for:
- Root cause analysis of complex bugs
- Security vulnerability assessment
- Architectural design decisions
- Multi-step logical reasoning

Provide high-level guidance rather than prescriptive steps:
"Analyze the authentication flow for security vulnerabilities, considering common attack vectors and edge cases."

Rather than:
"Step 1: Check for SQL injection. Step 2: Check for XSS. Step 3: ..."
</thinking_approach>
```

**When to use extended thinking**:
- Debugging complex issues
- Security analysis
- Code architecture review
- Performance optimization requiring deep analysis

**Minimum thinking budget**: 1024 tokens (increase for more complex tasks)
</practice>

<practice name="success_criteria">
Define what successful completion looks like:

```markdown
<success_criteria>
Task is complete when:
- All modified files have been reviewed
- Each issue has severity rating and specific fix
- Output format is valid JSON
- No vulnerabilities were missed (cross-check against OWASP Top 10)
</success_criteria>
```

**Benefit**: Clear completion criteria reduce ambiguity and partial outputs.
</practice>
</best_practices>

<testing_subagents>
<test_checklist>
1. **Invoke the subagent** with a representative task
2. **Check if it follows the workflow** specified in the prompt
3. **Verify output format** matches what you defined
4. **Test edge cases** - does it handle unusual inputs well?
5. **Check constraints** - does it respect boundaries?
6. **Iterate** - refine the prompt based on observed behavior
</test_checklist>

<common_issues>
- **Subagent too broad**: Narrow the focus areas
- **Skipping steps**: Make workflow more explicit
- **Inconsistent output**: Define output format more clearly
- **Overstepping bounds**: Add or clarify constraints
- **Not automatically invoked**: Improve description field with trigger keywords
</common_issues>
</testing_subagents>

<quick_reference>
```markdown
---
name: subagent-name
description: What it does and when to use it. Include trigger keywords.
tools: Tool1, Tool2, Tool3
model: sonnet
---

<role>
You are a [specific role] specializing in [domain].
</role>

<focus_areas>
- Focus 1
- Focus 2
- Focus 3
</focus_areas>

<workflow>
1. Step 1
2. Step 2
3. Step 3
</workflow>

<output_format>
Expected output structure
</output_format>

<constraints>
- Do not X
- Always Y
- Never Z
</constraints>
```
</quick_reference>
