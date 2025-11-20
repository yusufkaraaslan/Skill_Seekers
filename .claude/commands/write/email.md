---
description: Write an email - any tone, any purpose
argument-hint: [purpose/recipient or leave blank for current context]
---

<objective>
Write an email for $ARGUMENTS (or the current context if no arguments provided).

Clear, appropriate tone, gets the response you need.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- Recipient (who)
- Purpose (inform, request, follow up, apologize, etc.)
- Topic/subject matter
- Tone indicators (formal, casual, firm, warm, etc.)
- Relationship context
- Desired outcome

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If recipient relationship unclear:**
- "What's your relationship?" with options: Never met, Professional acquaintance, Working relationship, Personal connection, Other

**If purpose unclear:**
- "What's the goal?" with options: Request something, Share information, Follow up, Address an issue, Other

**If tone unclear:**
- "What tone?" with options: Formal/professional, Friendly but professional, Casual/warm, Direct/firm, Other

**If outcome unclear:**
- "What do you need from them?" with options: Decision/approval, Information, Action by specific date, Acknowledgment, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to write the email, or would you like me to ask more questions?"

Options:
1. **Start writing** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "Have you contacted them before about this?", "Is there a deadline?", "What's their likely objection?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start writing" → proceed to writing
</decision_gate>

</intake_gate>

<writing_process>
After intake complete:

1. Write subject line (clear, specific)
2. Opening (context, why you're writing)
3. Body (the actual content)
4. Ask (specific action or next step)
5. Close (appropriate sign-off)
6. Cut ruthlessly - shorter is better
</writing_process>

<output_format>
**Subject:** [Clear, specific subject line]

---

[Opening - 1 sentence context]

[Body - the actual content, as concise as possible]

[Ask - specific action you need, with any deadlines]

[Sign-off],
[Name]
</output_format>

<constraints>
- Subject line must be specific (not "Quick question")
- No filler ("I hope this email finds you well")
- Make it easy to say yes
</constraints>

<artifact_output>
Save the email to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/writing/`

2. Generate filename from topic:
   - Slugify the subject/purpose (lowercase, hyphens for spaces)
   - Format: `[topic]-email.md`
   - Example: `project-update-client-email.md`

3. Write the complete email to the file

4. Report to user: "Saved to `artifacts/writing/[filename]`"
</artifact_output>

<success_criteria>
- Recipient knows exactly what you need
- Tone matches relationship and context
- Can be read and acted on in under 60 seconds
- Ask is clear and actionable
- No unnecessary words
- Output saved to artifacts/writing/ directory
</success_criteria>
