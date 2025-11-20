---
description: Write documentation - READMEs, guides, API docs
argument-hint: [what to document or leave blank for current context]
---

<objective>
Write documentation for $ARGUMENTS (or the current context if no arguments provided).

Help someone understand and use this thing. Optimize for the reader, not the writer.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What's being documented (project, API, library, process)
- Doc type (README, guide, reference, tutorial)
- Target audience skill level
- Specific sections or focus areas

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If doc type unclear:**
- "What type of doc?" with options: README (first impression), How-to guide, API reference, Tutorial (learning by doing), Other

**If audience unclear:**
- "Who's the reader?" with options: Beginner (new to this), Intermediate (knows basics), Advanced (needs reference), Mixed levels, Other

**If scope unclear:**
- "What should this cover?" with options: Quick start only, Full documentation, Specific feature/section, Other

**If context unclear:**
- "What do readers already know?" with options: Nothing (explain everything), Basic concepts, Using similar tools, Domain experts, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to write the docs, or would you like me to ask more questions?"

Options:
1. **Start writing** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "What's the most common use case?", "What do people usually get stuck on?", "Are there prerequisites to install?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start writing" → proceed to writing
</decision_gate>

</intake_gate>

<writing_process>
After intake complete:

1. Lead with what reader needs most (usually Quick Start)
2. Structure for scanning (headers, bullets, code blocks)
3. Include examples for everything non-obvious
4. Anticipate questions and answer them
5. Make code copy-pasteable
</writing_process>

<output_format>
# [Title]

[One sentence: what this is and who it's for]

## Quick Start
[Minimum steps to get something working]

```bash
[Commands or code to copy-paste]
```

## [Main Section]
[Content organized by user goals, not internal structure]

### [Subsection]
[Details with examples]

```
[Code example]
```

## [Additional Sections as needed]

## Troubleshooting
**[Common problem]**
[Solution]

## Reference
[Comprehensive details, API specs, config options]
</output_format>

<constraints>
- Code must be copy-pasteable (no placeholders without explanation)
- Organize by user goals, not internal architecture
- Link to details, don't front-load them
</constraints>

<artifact_output>
Save the documentation to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/writing/`

2. Generate filename from topic:
   - Slugify the project/topic (lowercase, hyphens for spaces)
   - Format: `[topic]-docs.md`
   - Example: `api-integration-docs.md`

3. Write the complete documentation to the file

4. Report to user: "Saved to `artifacts/writing/[filename]`"
</artifact_output>

<success_criteria>
- Reader can get started in under 5 minutes
- Examples actually work
- Questions are answered before they're asked
- Scannable (can find what you need without reading everything)
- No obviously outdated content
- Output saved to artifacts/writing/ directory
</success_criteria>
