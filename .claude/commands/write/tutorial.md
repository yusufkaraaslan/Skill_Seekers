---
description: Write a tutorial - teach someone to do something step by step
argument-hint: [what to teach or leave blank for current context]
---

<objective>
Write a tutorial for $ARGUMENTS (or the current topic if no arguments provided).

Guide someone from zero to done. They should be able to follow along and succeed.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What skill/outcome to teach
- Target skill level
- Platform/environment (if technical)
- Desired end result

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If skill level unclear:**
- "Who's the reader?" with options: Complete beginner, Some experience, Comfortable with basics, Other

**If outcome unclear:**
- "What will they have at the end?" with options: Working project, New skill, Understanding of concept, Completed task, Other

**If scope unclear:**
- "How comprehensive?" with options: Minimal (just get it working), Standard (cover common cases), Thorough (edge cases + troubleshooting), Other

**If environment unclear (for technical tutorials):**
- "What environment?" with options: Mac, Windows, Linux, Web-based, Platform-agnostic, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to write the tutorial, or would you like me to ask more questions?"

Options:
1. **Start writing** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "What do people usually get stuck on?", "Any prerequisites to install?", "What should they try after completing this?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start writing" → proceed to writing
</decision_gate>

</intake_gate>

<writing_process>
After intake complete:

1. Define:
   - What will they accomplish?
   - What do they need to start?
   - Who is this for? (skill level)
2. Break into clear steps
3. For each step:
   - What to do (action)
   - How to do it (details)
   - How to verify it worked
4. Anticipate where they'll get stuck
5. Test it yourself (or imagine doing so)
</writing_process>

<output_format>
# [Tutorial Title: "How to X" or "Build Y"]

**What you'll build/learn:**
[Clear outcome with screenshot or description]

**Prerequisites:**
- [What they need installed/know]
- [Time estimate]

**Difficulty:** [Beginner/Intermediate/Advanced]

---

## Step 1: [Action]

[Brief explanation of why this step]

```bash
[Exact command or code]
```

[What they should see / how to verify]

## Step 2: [Action]

[Brief explanation]

```bash
[Exact command or code]
```

[Verification]

## Step 3: [Action]

[Continue pattern...]

---

## Troubleshooting

**[Common problem]**
[Solution]

**[Another common problem]**
[Solution]

---

## Next Steps
- [What to learn/build next]
- [Resources for going deeper]
</output_format>

<constraints>
- Every step must be testable (they know if it worked)
- Code must be copy-pasteable (no invisible characters, correct paths)
- No assumed knowledge beyond stated prerequisites
</constraints>

<artifact_output>
Save the tutorial to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/writing/`

2. Generate filename from topic:
   - Slugify the topic (lowercase, hyphens for spaces)
   - Format: `[topic]-tutorial.md`
   - Example: `build-cli-with-rust-tutorial.md`

3. Write the complete tutorial to the file

4. Report to user: "Saved to `artifacts/writing/[filename]`"
</artifact_output>

<success_criteria>
- Someone can follow start-to-finish without getting stuck
- They understand what they did (not just copy-paste magic)
- Common errors are anticipated
- They can extend or modify what they built
- They know where to go next
- Output saved to artifacts/writing/ directory
</success_criteria>
