---
name: create-agent-skills
description: Expert guidance for creating, writing, building, and refining Claude Code Skills. Use when working with SKILL.md files, authoring new skills, improving existing skills, or understanding skill structure, progressive disclosure, workflows, validation patterns, and XML formatting.
---

<objective>
Agent Skills are modular, filesystem-based capabilities that provide domain-specific expertise through progressive disclosure. This Skill teaches you how to create effective Skills that Claude can discover and use successfully.

Skills are organized prompts that get loaded on-demand. All prompting best practices apply, with an emphasis on pure XML structure for consistent parsing and efficient token usage.
</objective>

<quick_start>
<workflow>
1. **Identify the reusable pattern**: What context or procedural knowledge would be useful for similar future tasks?
2. **Create directory and SKILL.md**:
   - Directory name: Follow verb-noun convention: `create-*`, `manage-*`, `setup-*`, `generate-*` (see [references/skill-structure.md](references/skill-structure.md) for details)
   - YAML frontmatter:
     - `name`: Matches directory name, lowercase-with-hyphens, max 64 chars
     - `description`: What it does AND when to use it (third person, max 1024 chars)
3. **If skill requires API credentials**: See [references/api-security.md](references/api-security.md) for credential setup
4. **Write concise instructions**: Assume Claude is smart. Only add context Claude doesn't have. Use pure XML structure.
5. **Test with real usage**: Iterate based on observations.
</workflow>

<example_skill>
```yaml
---
name: process-pdfs
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
---

<objective>
Extract text and tables from PDF files, fill forms, and merge documents using Python libraries.
</objective>

<quick_start>
Extract text with pdfplumber:

```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```
</quick_start>

<advanced_features>
**Form filling**: See [forms.md](forms.md)
**API reference**: See [reference.md](reference.md)
</advanced_features>
```
</example_skill>
</quick_start>

<xml_structure>
<required_tags>
All skills must have these tags:

- **`<objective>`** - What the skill does and why it matters
- **`<quick_start>`** - Immediate, actionable guidance
- **`<success_criteria>`** or **`<when_successful>`** - How to know it worked
</required_tags>

<conditional_tags>
Based on skill complexity, add these tags as needed:

- **`<context>`** - Background/situational information
- **`<workflow>` or `<process>`** - Step-by-step procedures
- **`<advanced_features>`** - Deep-dive topics (progressive disclosure)
- **`<validation>`** - How to verify outputs
- **`<examples>`** - Multi-shot learning
- **`<anti_patterns>`** - Common mistakes to avoid
- **`<security_checklist>`** - Non-negotiable security patterns
- **`<testing>`** - Testing workflows
- **`<common_patterns>`** - Code examples and recipes
- **`<reference_guides>` or `<detailed_references>`** - Links to reference files
</conditional_tags>

<critical_rule>
**Remove ALL markdown headings (#, ##, ###) from skill body content.** Replace with semantic XML tags. Keep markdown formatting WITHIN content (bold, italic, lists, code blocks, links).
</critical_rule>
</xml_structure>

<intelligence_rules>
<simple_skills>
Single domain, straightforward tasks: Use required tags only.

Example: Text extraction, file format conversion, simple API calls
</simple_skills>

<medium_skills>
Multiple patterns, some complexity: Use required tags + workflow/examples as needed.

Example: Document processing with multiple steps, API integration with configuration
</medium_skills>

<complex_skills>
Multiple domains, security concerns, API integrations: Use required tags + conditional tags as appropriate.

Example: Payment processing, authentication systems, multi-step workflows with validation
</complex_skills>

<principle>
Don't over-engineer simple skills. Don't under-specify complex skills. Match tag selection to actual complexity and user needs.
</principle>
</intelligence_rules>

<generation_protocol>
<step_0>
<description>
**Adaptive Requirements Gathering**: Before building, gather requirements through intelligent questioning that infers obvious details and asks about genuine gaps.
</description>

<critical_first_action>
**BEFORE doing anything else**, check if context was provided.

IF no context provided (user just invoked the skill without describing what to build):
→ **IMMEDIATELY use AskUserQuestion** with these exact options:

1. **Create a new skill** - Build a skill from scratch
2. **Update an existing skill** - Modify or improve an existing skill
3. **Get guidance on skill design** - Help me think through what kind of skill I need

**DO NOT** ask "what would you like to build?" in plain text. **USE the AskUserQuestion tool.**

Routing after selection:
- "Create new" → proceed to adaptive intake below
- "Update existing" → enumerate existing skills as numbered list (see below), then gather requirements for changes
- "Guidance" → help user clarify needs before building

<update_existing_flow>
When "Update existing" is selected:

1. **List all skills in chat as numbered list** (DO NOT use AskUserQuestion - there may be many skills):
   - Glob for `~/.claude/skills/*/SKILL.md`
   - Present as numbered list in chat:
     ```
     Available skills:
     1. create-agent-skills
     2. generate-natal-chart
     3. manage-stripe
     ...
     ```
   - Ask: "Which skill would you like to update? (enter number)"

2. After user enters number, read that skill's SKILL.md
3. Ask what they want to change/improve using AskUserQuestion or direct question
4. Proceed with modifications
</update_existing_flow>

IF context was provided (user said "build a skill for X"):
→ Skip this gate. Proceed directly to adaptive intake.
</critical_first_action>

<adaptive_intake>
<analyze_description>
Parse the initial description:
- What's explicitly stated (operations, services, outputs)
- What can be inferred without asking (skill type, complexity, obvious patterns)
- What's genuinely unclear or ambiguous (scope boundaries, edge cases, specific behaviors)

Do NOT ask about things that are obvious from context.
</analyze_description>

<generate_questions>
Use AskUserQuestion to ask 2-4 domain-specific questions based on actual gaps.

Question generation guidance:
- **Scope questions**: "What specific operations?" not "What should it do?"
- **Complexity questions**: "Should this handle [specific edge case]?" based on domain knowledge
- **Output questions**: "What should the user see/get when successful?"
- **Boundary questions**: "Should this also handle [related thing] or stay focused?"

Avoid:
- Questions answerable from the initial description
- Generic questions that apply to all skills
- Yes/no questions when options would be more helpful
- Obvious questions like "what should it be called?" when the name is clear

Each question option should include a description explaining the implications of that choice.
</generate_questions>

<decision_gate>
After receiving answers, present decision gate using AskUserQuestion:

Question: "Ready to proceed with building, or would you like me to ask more questions?"

Options:
1. **Proceed to building** - I have enough context to build the skill
2. **Ask more questions** - There are more details to clarify
3. **Let me add details** - I want to provide additional context

If "Ask more questions" selected → loop back to generate_questions with refined focus
If "Let me add details" → receive additional context, then re-evaluate
If "Proceed" → continue to research_trigger, then step_1
</decision_gate>

<research_trigger>
Detect if the skill involves external APIs or services.

When external service detected, ask using AskUserQuestion:
"This involves [service name] API. Would you like me to research current endpoints and patterns before building?"

Options:
1. **Yes, research first** - Fetch 2024-2025 documentation for accurate implementation
2. **No, proceed with general patterns** - Use common patterns without specific API research

If research requested:
- Use Context7 MCP to fetch current library documentation
- Or use WebSearch for recent API documentation
- Focus on 2024-2025 sources for current patterns
- Store findings for use in content generation

Research findings flow into step_1 analysis and inform code examples in later steps.
</research_trigger>
</adaptive_intake>
</step_0>

<step_1>
**Analyze the domain**: Understand what the skill needs to teach and its complexity level. Incorporate gathered requirements and any research findings from step_0.
</step_1>

<step_2>
**Select XML tags**: Choose required tags + conditional tags based on intelligence rules.
</step_2>

<step_3>
**Write YAML frontmatter**: Validate name (matches directory, verb-noun convention) and description (third person, includes triggers).
</step_3>

<step_4>
**Structure content in pure XML**: No markdown headings in body. Use semantic XML tags for all sections.
</step_4>

<step_5>
**Apply progressive disclosure**: Keep SKILL.md under 500 lines. Split detailed content into reference files.
</step_5>

<step_6>
**Validate structure**:
- YAML frontmatter valid
- Required tags present (objective, quick_start, success_criteria)
- No markdown headings in body
- Proper XML nesting and closing tags
- Reference files linked appropriately
</step_6>

<step_7>
**Test with real usage**: Observe Claude using the skill. Iterate based on actual behavior, not assumptions.
</step_7>

<step_8>
**Create slash command wrapper**: Create a lightweight slash command that invokes the skill.

Location: `~/.claude/commands/{skill-name}.md`

Template:
```yaml
---
description: {Brief description of what the skill does}
argument-hint: [{argument description}]
allowed-tools: Skill({skill-name})
---

<objective>
Delegate {task} to the {skill-name} skill for: $ARGUMENTS

This routes to specialized skill containing patterns, best practices, and workflows.
</objective>

<process>
1. Use Skill tool to invoke {skill-name} skill
2. Pass user's request: $ARGUMENTS
3. Let skill handle workflow
</process>

<success_criteria>
- Skill successfully invoked
- Arguments passed correctly to skill
</success_criteria>
```

The slash command's only job is routing—all expertise lives in the skill.
</step_8>
</generation_protocol>

<yaml_requirements>
<required_fields>
```yaml
---
name: skill-name-here
description: What it does and when to use it (third person, specific triggers)
---
```
</required_fields>

<validation_rules>
See [references/skill-structure.md](references/skill-structure.md) for complete validation rules and naming conventions.
</validation_rules>
</yaml_requirements>

<when_to_use>
<create_skills_for>
- Reusable patterns across multiple tasks
- Domain knowledge that doesn't change frequently
- Complex workflows that benefit from structured guidance
- Reference materials (schemas, APIs, libraries)
- Validation scripts and quality checks
</create_skills_for>

<use_prompts_for>
One-off tasks that won't be reused
</use_prompts_for>

<use_slash_commands_for>
Explicit user-triggered workflows that run with fresh context
</use_slash_commands_for>
</when_to_use>

<reference_guides>
For deeper topics, see reference files:

**Core principles**: [references/core-principles.md](references/core-principles.md)
- XML structure (consistency, parseability, Claude performance)
- Conciseness (context window is shared)
- Degrees of freedom (matching specificity to task fragility)
- Model testing (Haiku vs Sonnet vs Opus)

**Skill structure**: [references/skill-structure.md](references/skill-structure.md)
- XML structure requirements
- Naming conventions
- Writing effective descriptions
- Progressive disclosure patterns
- File organization

**Workflows and validation**: [references/workflows-and-validation.md](references/workflows-and-validation.md)
- Complex workflows with checklists
- Feedback loops (validate → fix → repeat)
- Plan-validate-execute pattern

**Common patterns**: [references/common-patterns.md](references/common-patterns.md)
- Template patterns
- Examples patterns
- Consistent terminology
- Anti-patterns to avoid

**Executable code**: [references/executable-code.md](references/executable-code.md)
- When to use utility scripts
- Error handling in scripts
- Package dependencies
- MCP tool references

**API security**: [references/api-security.md](references/api-security.md)
- Preventing credentials from appearing in chat
- Using the secure API wrapper
- Adding new services and operations
- Credential storage patterns

**Iteration and testing**: [references/iteration-and-testing.md](references/iteration-and-testing.md)
- Evaluation-driven development
- Claude A/B development pattern
- Observing how Claude navigates Skills
- XML structure validation during testing

**Prompting fundamentals**:
- [references/be-clear-and-direct.md](references/be-clear-and-direct.md)
- [references/use-xml-tags.md](references/use-xml-tags.md)
</reference_guides>

<success_criteria>
A well-structured skill has:

- Valid YAML frontmatter with descriptive name and comprehensive description
- Pure XML structure with no markdown headings in body
- Required tags: objective, quick_start, success_criteria
- Conditional tags appropriate to complexity level
- Progressive disclosure (SKILL.md < 500 lines, details in reference files)
- Clear, concise instructions that assume Claude is smart
- Real-world testing and iteration based on observed behavior
- Lightweight slash command wrapper for discoverability
</success_criteria>
