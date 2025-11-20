# Context Handoff for Claude Code

Create structured handoff documents to continue work in a fresh context without losing progress.

## The Problem

You're deep in a conversation, made significant progress, but need to start a fresh chat (context getting full, switching tasks, or just want a clean slate). You lose all the context about what was done, what remains, and why decisions were made.

## The Solution

`/whats-next` analyzes the current conversation and creates a structured handoff document (`whats-next.md`) in your working directory. In your next chat, reference it with `@whats-next.md` to continue seamlessly.

## Command

### `/whats-next`

Analyzes the conversation and creates a comprehensive handoff document with:

1. **Original task** - What was initially requested
2. **Work completed** - Everything accomplished in detail
3. **Work remaining** - Specific tasks still needed
4. **Attempted approaches** - What was tried (including failures)
5. **Critical context** - Decisions, constraints, discoveries
6. **Current state** - Exact status of deliverables

**Output format:**
```xml
<original_task>
Implement user authentication with JWT tokens
</original_task>

<work_completed>
- Created auth middleware in middleware/auth.ts:1-45
- Added JWT signing/verification in utils/jwt.ts:1-67
- Updated User model with password hashing in models/User.ts:23-34
- Created login endpoint in routes/auth.ts:12-56
</work_completed>

<work_remaining>
- Add token refresh endpoint in routes/auth.ts
- Implement logout (token blacklist) using Redis
- Add password reset flow (email + token verification)
- Write tests for auth middleware in tests/middleware/auth.test.ts
</work_remaining>

<attempted_approaches>
- Tried using session-based auth first but switched to JWT for statelessness
- Attempted to use Passport.js but found it overkill for this use case
</attempted_approaches>

<critical_context>
- Using jsonwebtoken library (already in dependencies)
- Tokens expire in 24h (configurable via JWT_EXPIRY env var)
- Password hashing uses bcrypt with 10 rounds
- Discovered: User.findByEmail returns null for missing users (handle this in routes)
- Redis connection required for token blacklist (not yet configured)
</critical_context>

<current_state>
- Auth middleware: Complete and tested
- JWT utils: Complete
- Login endpoint: Complete
- Token refresh: Not started
- Logout: Not started
- Password reset: Not started
- Tests: Not started
</current_state>
```

## Why This Works

**Preserves progress:**
- Exact file paths and line numbers for all work
- Comprehensive work completed with reasoning
- Clear remaining tasks with precise locations
- Current state tracking for all deliverables

**Prevents wasted effort:**
- Documents attempted approaches and failures
- Captures dead ends to avoid repeating
- Records what didn't work and why

**Prevents scope creep:**
- Focuses only on completing the original request
- Doesn't add new features or "nice to haves"
- Maintains task boundaries across context switches

**Transfers critical knowledge:**
- Key decisions and trade-offs made
- Technical constraints and gotchas discovered
- Environment details and assumptions
- References to documentation consulted

## Installation

**Install globally** - works in any directory:

```bash
cp whats-next.md ~/.claude/commands/
```

The command works everywhere. Each project gets its own `whats-next.md` in the working directory.

## Usage

**End of current conversation:**
```
You: /whats-next
Claude: [Analyzes conversation, writes whats-next.md]
✓ Created whats-next.md - reference with @whats-next.md in a new chat to continue
```

**Start of new conversation:**
```
You: @whats-next.md continue this work
Claude: [Reads handoff document, understands context, resumes work]
```

## Example Workflow

**Conversation 1 (getting full):**
```
You: "Build a user dashboard with real-time analytics"
Claude: [Works on task, creates components, sets up data fetching...]
You: /whats-next

✓ Created whats-next.md
```

**Conversation 2 (fresh context):**
```
You: @whats-next.md finish this
Claude: [Reads whats-next.md]
"I see we've completed the dashboard layout and real-time data
connection. Still need to add the chart components and error handling.
Continuing from src/components/Dashboard.tsx:67..."
```

## File Structure

**Global (install once):**
```
~/.claude/commands/
  whats-next.md         # Command
```

**Per-project (created when needed):**
```
/your/project/
  whats-next.md         # Handoff document for this project

/another/project/
  whats-next.md         # Different project's handoff
```

## Tips

- Use `/whats-next` when context feels full or cluttered
- Reference with `@whats-next.md` in new chats for seamless continuation
- The file is overwritten each time - it's a snapshot, not a log
- Delete `whats-next.md` when work is complete
- Works great with `/add-to-todos` for long-term task tracking

## Integration

**Combine with todo management:**
- `/whats-next` for immediate continuation (same session/day)
- `/add-to-todos` for longer-term backlog (weeks/months)

Use whats-next.md for "I'll finish this after lunch" and TO-DOS.md for "I'll get to this eventually."

---

**Questions or improvements?** Open an issue or submit a PR.

—TÂCHES
