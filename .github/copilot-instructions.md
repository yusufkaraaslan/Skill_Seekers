# GitHub Copilot Instructions

This file provides custom instructions and context for GitHub Copilot and Copilot Chat users working in this repository.

## How to Use
- **Pin this file in Copilot Chat**: Click "+ Add to chat" and select `.github/copilot-instructions.md` to provide Copilot with project-specific context.
- **Keep this file up to date** with any special coding guidelines, architectural notes, or onboarding tips for AI assistance.

## Project Guidance
- The primary source of AI guidance for this repo is [`CLAUDE.md`](../CLAUDE.md). Please refer to that file for detailed project structure, workflows, and architectural notes.
- For Copilot Chat, you may also pin `CLAUDE.md` directly for maximum context.

## Example Instructions
- Follow the coding standards described in `CLAUDE.md`.
- Use the CLI tools in `cli/` for scraping, packaging, and testing.
- MCP server integration details are in `skill_seeker_mcp/`.
- Test changes using `python3 cli/run_tests.py` or `pytest tests/`.

---

**Tip:** If you are using Copilot Enterprise, your organization may have additional custom instructions or knowledge bases attached to this repository.
