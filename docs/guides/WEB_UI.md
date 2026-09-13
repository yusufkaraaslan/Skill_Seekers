# Seeker HUD

The HUD is a local React/FastAPI interface to Skill Seekers. Install the API dependencies and build the frontend before launching from a checkout:

```bash
pip install -e ".[ui]"
npm --prefix ui ci
npm --prefix ui run build
skill-seekers ui --no-browser
```

Open `http://127.0.0.1:8770`. The launcher accepts loopback hosts only. For frontend development, run `npm --prefix ui run dev`; Vite serves port 3000 and proxies `/api` to the local backend. The production build lives in `src/skill_seekers/web/dist` and is bundled into release wheels.

## Create and inspect skills

Choose sources in **Create**, set options, then select package formats. Leave formats unchecked to build without packaging. Formats and enhancement agents come from the installed backend's capabilities. **Install** copies a skill into a CLI's skill directory and offers only CLIs detected on this machine; **Package** exports through a platform adaptor. These are separate operations.

Create drafts survive navigation and refresh within the same browser tab. Failed submissions retain entered values. The job preview shows the actual submitted options and saved directories. Settings defaults apply to new jobs; an existing draft keeps its selected agent. Relative output/config directories resolve against the workspace root. Changing these directories changes the inventory being viewed; it does not move existing files.

Open a skill to go to its page at `/skills/<id>`, which loads the complete `SKILL.md` and supporting-file list on the SKILL.md and Files tabs. Saves require the revision originally loaded. If another process changes the file, the save fails and your draft stays open. Copy your draft before reloading to resolve a conflict. Plugin and manually managed skills can be copied or packaged, but cannot be edited, enhanced, or archived through the HUD. The page URL is bookmarkable and shareable; opening a skill from any table, card, or job output goes to the same page.

## Install, organize, and recover

Installation preserves the complete skill folder. Existing destinations require explicit replacement. Installing a skill into its own location is a safe no-op. Skill IDs identify filesystem locations, so identical names from different directories remain separate entries.

The **Move** action organizes skills under a project inside the HUD. It does not change CLI loading scope. Moving to global clears the project assignment. Removing a project preserves its files and clears its assignments.

Deleting a Seeker-owned skill archives its source under `~/.skill-seekers/ui/trash`, and removes only installation copies recorded as belonging to that source. Use **Archived skills → Restore** to recover the source; reinstall CLI copies separately. Restore refuses to overwrite an existing destination.

Current installation destinations follow the documented user skill locations for [Codex](https://learn.chatgpt.com/docs/build-skills), [Cursor](https://cursor.com/docs/skills), [Windsurf](https://docs.devin.ai/desktop/cascade/skills), and [OpenCode](https://opencode.ai/docs/skills/). Shared compatibility directories may be visible to more than one CLI. Earlier HUD versions wrote some formats into rules/instructions/agent directories; existing files there are preserved, but new installs use native skill folders.

## Jobs, configs, and marketplaces

**Jobs** retains the latest 100 finished jobs plus active jobs, with full timestamps, streamed logs, cancellation, retry, output paths, and file downloads. Package jobs always write to `output/_packages/<target>/`, one directory per format, and a repeat run of the same skill keeps both archives. Multi-source creates write a stable `configs/<name>-unified.json` that later runs overwrite. Interrupted jobs become failed after restart. Retry repeats the saved specification; it may require resolving a destination conflict first.

Project scans accept local directories and expose failure/retry states. The config library indexes both the configured workspace directory and fetched source caches; opening a config goes to its page at `/configs/<id>` (Overview, JSON, Validate, Estimate, Sync, Push / Submit, Generate tabs) instead of a drawer. Marketplace browsing reads cached data; **Sync all** refreshes it through background jobs. Install first copies to the workspace, with additional CLI destinations explicitly selected. Existing workspace skills must be archived or renamed before another install with the same directory name.

The MCP screen was folded into **Environment**, which reports real probe results and connection instructions for the MCP tools catalogue alongside Doctor, Servers, and Agents panels. It does not simulate tool execution.

## Pages

Every entity has a URL you can bookmark: `/skills/<id>` (Overview, SKILL.md, Files, Installs, Enhance, Analysis, Export, History), `/configs/<id>` (Overview, JSON, Validate, Estimate, Sync, Push / Submit, Generate), `/workflows/<name>`, `/analyze`, and `/environment` (Doctor, Servers, Agents, MCP tools). Opening a skill from any table, card, or job output goes to its page.

## Job types

`create`, `scan`, `package`, `enhance`, `port`, `fetch`, `publish`, `estimate`, `market-sync`, `install`, `upload`, `translate`, `update`, `quality`, `analyze`, `split`, `push`, `submit`, `sync-check`, `generate-config`, `install-agent`, `server`. Servers started from Environment run as jobs; stopping the server cancels the job.

## Contributor checks

```bash
pytest tests/test_web_api.py tests/test_web_regressions.py -q
npm --prefix ui run lint
npm --prefix ui run build
cd ui
npx playwright install chromium
npm test
```

Browser tests use fixture API responses and temporary browser state. Backend regressions use isolated homes/workspaces and include real subprocess packaging, cancellation, and concurrent persistence. CI gates frontend lint, build, and browser tests. Live remote services and account credentials require separate integration testing.
