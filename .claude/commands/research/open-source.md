---
description: Find open-source solutions - libraries, tools, projects that solve this
argument-hint: [problem/need or leave blank for current context]
---

<objective>
Find open-source solutions for $ARGUMENTS (or the current topic if no arguments provided).

Search for existing libraries, tools, and projects that solve the problem. Don't build what already exists.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What problem needs solving
- Language/framework requirements
- License requirements
- Integration constraints

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If language unclear:**
- "What language/framework?" with options: Python, JavaScript/Node, Swift, Go, Rust, Language agnostic, Other

**If license unclear:**
- "License requirements?" with options: Any open source, Permissive only (MIT/Apache), GPL OK, Commercial use required, Other

**If maintenance unclear:**
- "How important is maintenance?" with options: Must be actively maintained, Recent activity OK, Abandoned OK if it works, Other

**If integration unclear:**
- "Must integrate with?" with options: Nothing specific, Existing codebase, Specific framework, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to search for open-source solutions, or would you like me to ask more questions?"

Options:
1. **Start search** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups, then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start search" → proceed to research
</decision_gate>

</intake_gate>

<process>
After intake complete:

1. Define what we need (problem, requirements, constraints)
2. Search for open-source options
3. Evaluate each option
4. Assess build vs. use tradeoffs
5. Recommend best option or confirm need to build
</process>

<output_format>
## Open Source Research: [Need]

### Strategic Summary
[2-3 sentences: what's available, recommendation, key consideration]

### What we need
[Problem to solve, key requirements]

### License requirements
[MIT/Apache/GPL-compatible/etc.]

### Options Found

**[Option 1: package-name]**
- **Repo:** [GitHub URL]
- **What it does:** [Brief description]
- **Stars/Downloads:** [Popularity indicators]
- **Last updated:** [Date]
- **License:** [License type]
- **Fits our need:** [Yes/Partial/No] - [why]
- **Concerns:** [Issues, gaps, risks]

**[Option 2: package-name]**
[Same structure...]

**[Option 3: package-name]**
[Same structure...]

### Comparison
| Aspect | Option 1 | Option 2 | Option 3 |
|--------|----------|----------|----------|
| Solves problem | Y/Partial/N | | |
| Maintained | Y/N | | |
| License OK | Y/N | | |
| Easy to integrate | Y/N | | |

### Build vs. Use Analysis
**Use existing:**
- Pros: [Proven solution, community support, faster start]
- Cons: [Less control, potential bloat, dependency risk]

**Build custom:**
- Pros: [Exact fit, full control, no dependencies]
- Cons: [Complexity to build, maintenance burden]

**Recommendation:**
[Use Option X / Build custom] because [reasoning]

### Implementation Context
<claude_context>
<if_use>
- package: [exact package name and version]
- install: [installation command]
- docs: [documentation URL]
- examples: [example code or reference]
- gotchas: [known issues, quirks, workarounds]
</if_use>
<if_build>
- scope: [what to build]
- approach: [technical approach]
- reference: [can use Option X as reference for patterns]
- complexity: [S/M/L]
</if_build>
<integration>
- imports: [how to import/require]
- patterns: [usage patterns]
- testing: [how to test integration]
</integration>
</claude_context>

**Next Action:** Prototype with chosen library, evaluate deeper, or spec out custom build
</output_format>

<artifact_output>
Save the research to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/research/`

2. Generate filename from topic:
   - Slugify the topic (lowercase, hyphens for spaces)
   - Format: `[topic]-open-source.md`
   - Example: `midi-libraries-open-source.md`

3. Write the complete research to the file

4. Report to user: "Saved to `artifacts/research/[filename]`"
</artifact_output>

<success_criteria>
- Search is thorough (not just first result)
- Maintenance status is verified (not abandoned)
- License compatibility is checked
- Build vs. use tradeoff is honest
- Implementation context has exact package info Claude needs
- Recommendation saves complexity without creating technical debt
- Output saved to artifacts/research/ directory
</success_criteria>
