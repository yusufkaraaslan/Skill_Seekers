---
description: Comprehensive investigation of a topic - thorough analysis with sources
argument-hint: [topic or leave blank for current context]
---

<objective>
Conduct a deep-dive investigation into $ARGUMENTS (or the current topic if no arguments provided).

Go beyond surface-level understanding. Synthesize multiple sources into comprehensive knowledge.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- The topic to investigate
- Specific questions to answer
- Depth required
- How this knowledge will be used

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If questions unclear:**
- "What do you need to understand?" with options: How it works, When to use it, Why it exists, Limitations/gotchas, All of the above, Other

**If depth unclear:**
- "How deep should I go?" with options: Overview (key points only), Solid understanding (main concepts), Comprehensive (thorough coverage), Other

**If application unclear:**
- "How will this be used?" with options: Inform implementation, Make architecture decision, Evaluate feasibility, General knowledge, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to start the deep dive, or would you like me to ask more questions?"

Options:
1. **Start research** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups, then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start research" → proceed to research
</decision_gate>

</intake_gate>

<process>
After intake complete:

1. Define the scope and key questions to answer
2. Gather information from multiple angles:
   - How it works (mechanics)
   - Why it exists (history, motivation)
   - How it's used (patterns, best practices)
   - Where it fails (limitations, edge cases)
   - What's next (trends, evolution)
3. Synthesize into coherent understanding
4. Identify remaining unknowns
</process>

<output_format>
## Deep Dive: [Topic]

### Strategic Summary
[2-3 sentences: what this is, key insight, main implication for our work]

### Key Questions
- [Question this research answers]
- [Question this research answers]

### Overview
[2-3 paragraph synthesis of what this is and why it matters]

### How It Works
[Detailed explanation of mechanics, architecture, or process]

### History & Context
[Why it exists, what problem it solved, how it evolved]

### Patterns & Best Practices
- [Pattern/practice 1]: [when and why]
- [Pattern/practice 2]: [when and why]
- [Pattern/practice 3]: [when and why]

### Limitations & Edge Cases
- [Limitation]: [workaround or mitigation]
- [Edge case]: [how to handle]

### Current State & Trends
[Where things are heading, recent developments, community direction]

### Key Takeaways
1. [Most important insight]
2. [Second most important insight]
3. [Third most important insight]

### Remaining Unknowns
- [ ] [Question that still needs answering]
- [ ] [Question that still needs answering]

### Implementation Context
<claude_context>
<application>
- when_to_use: [situations where this applies]
- when_not_to_use: [situations to avoid this]
- prerequisites: [what must be true to use this]
</application>
<technical>
- libraries: [relevant packages/tools]
- patterns: [code patterns to follow]
- gotchas: [common mistakes, edge cases]
</technical>
<integration>
- works_with: [complementary technologies]
- conflicts_with: [incompatible approaches]
- alternatives: [other options to consider]
</integration>
</claude_context>

**Next Action:** Apply this knowledge to implementation, research specific aspect deeper, or run /plan/project
</output_format>

<artifact_output>
Save the research to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/research/`

2. Generate filename from topic:
   - Slugify the topic (lowercase, hyphens for spaces)
   - Format: `[topic]-deep-dive.md`
   - Example: `kubernetes-networking-deep-dive.md`

3. Write the complete research to the file

4. Report to user: "Saved to `artifacts/research/[filename]`"
</artifact_output>

<success_criteria>
- Answers the key questions thoroughly
- Goes beyond surface-level (not just "what" but "why" and "when")
- Identifies limitations honestly
- Synthesizes into actionable understanding
- Implementation context is specific enough for Claude to apply
- Clear about what's still unknown
- Output saved to artifacts/research/ directory
</success_criteria>
