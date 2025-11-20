<overview>
Guidelines for determining prompt complexity, tool usage, and optimization patterns.
</overview>

<complexity_assessment>

<simple_prompts>
Single focused task, clear outcome:

**Indicators:**
- Single artifact output
- No dependencies on other files
- Straightforward requirements
- No decision-making needed

**Prompt characteristics:**
- Concise objective
- Minimal context
- Direct requirements
- Simple verification
</simple_prompts>

<complex_prompts>
Multi-step tasks, multiple considerations:

**Indicators:**
- Multiple artifacts or phases
- Dependencies on research/plan files
- Trade-offs to consider
- Integration with existing code

**Prompt characteristics:**
- Detailed objective with context
- Referenced files
- Explicit implementation guidance
- Comprehensive verification
- Extended thinking triggers
</complex_prompts>

</complexity_assessment>

<extended_thinking_triggers>

<when_to_include>
Use these phrases to activate deeper reasoning in complex prompts:
- Complex architectural decisions
- Multiple valid approaches to evaluate
- Security-sensitive implementations
- Performance optimization tasks
- Trade-off analysis
</when_to_include>

<trigger_phrases>
```
"Thoroughly analyze..."
"Consider multiple approaches..."
"Deeply consider the implications..."
"Explore various solutions before..."
"Carefully evaluate trade-offs..."
```
</trigger_phrases>

<example_usage>
```xml
<requirements>
Thoroughly analyze the authentication options and consider multiple
approaches before selecting an implementation. Deeply consider the
security implications of each choice.
</requirements>
```
</example_usage>

<when_not_to_use>
- Simple, straightforward tasks
- Tasks with clear single approach
- Following established patterns
- Basic CRUD operations
</when_not_to_use>

</extended_thinking_triggers>

<parallel_tool_calling>

<when_to_include>
```xml
<efficiency>
For maximum efficiency, invoke all independent tool operations
simultaneously rather than sequentially. Multiple file reads,
searches, and API calls that don't depend on each other should
run in parallel.
</efficiency>
```
</when_to_include>

<applicable_scenarios>
- Reading multiple files for context
- Running multiple searches
- Fetching from multiple sources
- Creating multiple independent files
</applicable_scenarios>

</parallel_tool_calling>

<context_loading>

<when_to_load>
- Modifying existing code
- Following established patterns
- Integrating with current systems
- Building on research/plan outputs
</when_to_load>

<when_not_to_load>
- Greenfield features
- Standalone utilities
- Pure research tasks
- Standard patterns without customization
</when_not_to_load>

<loading_patterns>
```xml
<context>
<!-- Chained artifacts -->
Research: @.prompts/001-auth-research/auth-research.md
Plan: @.prompts/002-auth-plan/auth-plan.md

<!-- Existing code to modify -->
Current implementation: @src/auth/middleware.ts
Types to extend: @src/types/auth.ts

<!-- Patterns to follow -->
Similar feature: @src/features/payments/
</context>
```
</loading_patterns>

</context_loading>

<output_optimization>

<claude_to_claude>
For Claude-to-Claude consumption:

**Use heavy XML structure:**
```xml
<findings>
  <finding category="security">
    <title>Token Storage</title>
    <recommendation>httpOnly cookies</recommendation>
    <rationale>Prevents XSS access</rationale>
  </finding>
</findings>
```

**Include metadata:**
```xml
<metadata>
  <confidence level="high">Verified in official docs</confidence>
  <dependencies>Cookie parser middleware</dependencies>
  <open_questions>SameSite policy for subdomains</open_questions>
</metadata>
```

**Be explicit about next steps:**
```xml
<next_actions>
  <action priority="high">Create planning prompt using these findings</action>
  <action priority="medium">Validate rate limits in sandbox</action>
</next_actions>
```
</claude_to_claude>

<human_consumption>
For human consumption:
- Clear headings
- Bullet points for scanning
- Code examples with comments
- Summary at top
</human_consumption>

</output_optimization>

<prompt_depth_guidelines>

<minimal>
Simple Do prompts:
- 20-40 lines
- Basic objective, requirements, output, verification
- No extended thinking
- No parallel tool hints
</minimal>

<standard>
Typical task prompts:
- 40-80 lines
- Full objective with context
- Clear requirements and implementation notes
- Standard verification
</standard>

<comprehensive>
Complex task prompts:
- 80-150 lines
- Extended thinking triggers
- Parallel tool calling hints
- Multiple verification steps
- Detailed success criteria
</comprehensive>

</prompt_depth_guidelines>

<why_explanations>

Always explain why constraints matter:

<bad_example>
```xml
<requirements>
Never store tokens in localStorage.
</requirements>
```
</bad_example>

<good_example>
```xml
<requirements>
Never store tokens in localStorage - it's accessible to any
JavaScript on the page, making it vulnerable to XSS attacks.
Use httpOnly cookies instead.
</requirements>
```
</good_example>

This helps the executing Claude make good decisions when facing edge cases.

</why_explanations>

<verification_patterns>

<for_code>
```xml
<verification>
1. Run test suite: `npm test`
2. Type check: `npx tsc --noEmit`
3. Lint: `npm run lint`
4. Manual test: [specific flow to test]
</verification>
```
</for_code>

<for_documents>
```xml
<verification>
1. Validate structure: [check required sections]
2. Verify links: [check internal references]
3. Review completeness: [check against requirements]
</verification>
```
</for_documents>

<for_research>
```xml
<verification>
1. Sources are current (2024-2025)
2. All scope questions answered
3. Metadata captures uncertainties
4. Actionable recommendations included
</verification>
```
</for_research>

<for_plans>
```xml
<verification>
1. Phases are sequential and logical
2. Tasks are specific and actionable
3. Dependencies are clear
4. Metadata captures assumptions
</verification>
```
</for_plans>

</verification_patterns>

<chain_optimization>

<research_prompts>
Research prompts should:
- Structure findings for easy extraction
- Include code examples for implementation
- Clearly mark confidence levels
- List explicit next actions
</research_prompts>

<plan_prompts>
Plan prompts should:
- Reference research explicitly
- Break phases into prompt-sized chunks
- Include execution hints per phase
- Capture dependencies between phases
</plan_prompts>

<do_prompts>
Do prompts should:
- Reference both research and plan
- Follow plan phases explicitly
- Verify against research recommendations
- Update plan status when done
</do_prompts>

</chain_optimization>
