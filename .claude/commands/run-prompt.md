---
name: run-prompt
description: Delegate one or more prompts to fresh sub-task contexts with parallel or sequential execution
argument-hint: <prompt-number(s)-or-name> [--parallel|--sequential]
---

<objective>
Execute one or more prompts from `./prompts/` as delegated sub-tasks with fresh context. Supports single prompt execution, parallel execution of multiple independent prompts, and sequential execution of dependent prompts.
</objective>

<input>
The user will specify which prompt(s) to run via $ARGUMENTS, which can be:

**Single prompt:**

- Empty (no arguments): Run the most recently created prompt (default behavior)
- A prompt number (e.g., "001", "5", "42")
- A partial filename (e.g., "user-auth", "dashboard")

**Multiple prompts:**

- Multiple numbers (e.g., "005 006 007")
- With execution flag: "005 006 007 --parallel" or "005 006 007 --sequential"
- If no flag specified with multiple prompts, default to --sequential for safety
  </input>

<process>
<step1_parse_arguments>
Parse $ARGUMENTS to extract:
- Prompt numbers/names (all arguments that are not flags)
- Execution strategy flag (--parallel or --sequential)

<examples>
- "005" → Single prompt: 005
- "005 006 007" → Multiple prompts: [005, 006, 007], strategy: sequential (default)
- "005 006 007 --parallel" → Multiple prompts: [005, 006, 007], strategy: parallel
- "005 006 007 --sequential" → Multiple prompts: [005, 006, 007], strategy: sequential
</examples>
</step1_parse_arguments>

<step2_resolve_files>
For each prompt number/name:

- If empty or "last": Find with `!ls -t ./prompts/*.md | head -1`
- If a number: Find file matching that zero-padded number (e.g., "5" matches "005-_.md", "42" matches "042-_.md")
- If text: Find files containing that string in the filename

<matching_rules>

- If exactly one match found: Use that file
- If multiple matches found: List them and ask user to choose
- If no matches found: Report error and list available prompts
  </matching_rules>
  </step2_resolve_files>

<step3_execute>
<single_prompt>

1. Read the complete contents of the prompt file
2. Delegate as sub-task using Task tool with subagent_type="general-purpose"
3. Wait for completion
4. Archive prompt to `./prompts/completed/` with metadata
5. Return results
   </single_prompt>

<parallel_execution>

1. Read all prompt files
2. **Spawn all Task tools in a SINGLE MESSAGE** (this is critical for parallel execution):
   <example>
   Use Task tool for prompt 005
   Use Task tool for prompt 006
   Use Task tool for prompt 007
   (All in one message with multiple tool calls)
   </example>
3. Wait for ALL to complete
4. Archive all prompts with metadata
5. Return consolidated results
   </parallel_execution>

<sequential_execution>

1. Read first prompt file
2. Spawn Task tool for first prompt
3. Wait for completion
4. Archive first prompt
5. Read second prompt file
6. Spawn Task tool for second prompt
7. Wait for completion
8. Archive second prompt
9. Repeat for remaining prompts
10. Return consolidated results
    </sequential_execution>
    </step3_execute>
    </process>

<context_strategy>
By delegating to a sub-task, the actual implementation work happens in fresh context while the main conversation stays lean for orchestration and iteration.
</context_strategy>

<output>
<single_prompt_output>
✓ Executed: ./prompts/005-implement-feature.md
✓ Archived to: ./prompts/completed/005-implement-feature.md

<results>
[Summary of what the sub-task accomplished]
</results>
</single_prompt_output>

<parallel_output>
✓ Executed in PARALLEL:

- ./prompts/005-implement-auth.md
- ./prompts/006-implement-api.md
- ./prompts/007-implement-ui.md

✓ All archived to ./prompts/completed/

<results>
[Consolidated summary of all sub-task results]
</results>
</parallel_output>

<sequential_output>
✓ Executed SEQUENTIALLY:

1. ./prompts/005-setup-database.md → Success
2. ./prompts/006-create-migrations.md → Success
3. ./prompts/007-seed-data.md → Success

✓ All archived to ./prompts/completed/

<results>
[Consolidated summary showing progression through each step]
</results>
</sequential_output>
</output>

<critical_notes>

- For parallel execution: ALL Task tool calls MUST be in a single message
- For sequential execution: Wait for each Task to complete before starting next
- Archive prompts only after successful completion
- If any prompt fails, stop sequential execution and report error
- Provide clear, consolidated results for multiple prompt execution
  </critical_notes>
