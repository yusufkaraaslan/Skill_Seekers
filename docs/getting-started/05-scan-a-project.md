# Scan an entire project (AI-driven)

`skill-seekers scan` is the fastest way to bootstrap a knowledge base for a
real codebase. Instead of running `create` once per framework, point `scan`
at a project directory and an AI agent figures out the tech stack for you.

## What it does

1. **Collects signals** from the project root with per-kind byte budgets
   (24 KB manifests / 6 KB README / 6 KB CI / 28 KB source samples — total
   64 KB capped so no single fat file crowds others out):
   - **~50 manifest types**: `package.json`, `pyproject.toml`, `Pipfile`,
     `environment.yml`, `Cargo.toml`, `go.mod`, `Gemfile`, `build.gradle`,
     `pom.xml`, `composer.json`, `mix.exs`, `flake.nix`, `deno.json`,
     `deps.edn`, `dune-project`, `BUILD.bazel`, `project.godot`, …
   - README, Dockerfile, docker-compose, GitHub Actions, GitLab CI, Makefile
   - First 2 KB of each sampled source file (across `src/`, `lib/`, `app/`,
     `cmd/`, `crates/`, `packages/`, `apps/`, `services/`, `backend/`,
     `frontend/`, plus root-level files for Django / flat-layout Python)
   - The git remote URL
2. **AI detector** classifies the signals — returns the frameworks,
   libraries, tools and services the project actually uses (with
   versions, ecosystems, and confidence scores). Canonical-name resolver
   handles CJK + European-language suffixes ("Godot 引擎" → `godot`,
   "React フレームワーク" → `react`).
3. **Resolves each detection** in order:
   - **Out-dir cache** — if `<out_dir>/<slug>.json` already exists from a
     prior scan, reuse it (just re-stamps `metadata.detected_version`,
     preserves any manual edits)
   - **Local repo / user dir** — `./configs/<name>.json` then
     `~/.config/skill-seekers/configs/<name>.json`
   - **Community API** — `https://api.skillseekersweb.com/api/configs/<name>`
   - **AI generation** — last resort, subject to `--max-ai-generations` cap
4. **AI-generates** a fresh config for unmapped detections (capped at
   `--max-ai-generations` to prevent monorepo surprise bills), validated
   against the unified schema and the registry name regex. With
   `--probe-urls`, HEAD-checks the URLs and re-prompts on 4xx/5xx.
5. **Always emits `<project>-codebase.json`** — a `type: "local"` config
   pointed at your project root, so you get a skill about *your* code
   alongside the framework skills.
6. **Archives stale configs**: a framework that disappears from detections
   is MOVED (not deleted — your hand edits are preserved) to
   `out_dir/.archived/<UTC-timestamp>/`.
7. **Optional async publish** (opt-in): for each freshly AI-generated
   config, you're asked whether to submit it back to the community
   registry. Pre-checks `GITHUB_TOKEN`. Searches for existing open issues
   first (idempotency — no duplicate submissions on re-runs). Retries
   transient failures with backoff.

## Workflow

```bash
# Step 1 — scan
skill-seekers scan ./my-react-app --out ./configs/scanned/

# Step 2 — review what was emitted, edit if needed
ls ./configs/scanned/
#   react.json
#   typescript.json
#   vite.json
#   tailwind.json
#   jest.json
#   my-react-app-codebase.json

# Step 3 — build skills from the configs you actually want
skill-seekers create ./configs/scanned/react.json
skill-seekers create ./configs/scanned/my-react-app-codebase.json
```

## Re-scanning

Run `scan` again with the same `--out` and it diffs against the prior
results — reporting **added** packages, **version bumps**, and **removed**
packages. Removed configs are MOVED to `.archived/<UTC-timestamp>/`
(never deleted) so manual edits aren't lost. Use this in CI to keep
your skills aligned with the project's actual dependencies.

```bash
skill-seekers scan ./my-react-app --out ./configs/scanned/
#   Diff vs previous scan:
#     + added       prisma
#     ↻ updated     react   18.2.0 → 18.3.1
#     - removed     moment
#   📦 Archived 1 stale config(s) → 2026-05-25T14-30-00Z/
```

The `.archived/` directory grows on each cleanup pass. Auto-prune
isn't applied — `rm -rf out_dir/.archived/` whenever you're confident
you don't need the old versions.

## Stale config cleanup (archive)

`out_dir/.archived/<UTC-timestamp>/` contains every config that
disappeared from detections during a re-scan. The move-not-delete
policy means a user-edited config never gets silently lost:

```bash
ls out_dir/.archived/
#   2026-05-25T14-30-00Z/  ← scan removed `moment`
#   2026-05-26T09-15-22Z/  ← scan removed `aws-sdk-v2`
```

To clean up: `rm -rf out_dir/.archived/`. Or keep them as a history
of which dependencies you've dropped.

## Cost control on monorepos

A project with 30 unmapped detections would trigger 30 AI generation
calls (up to 2 retries each, so 60 LLM hits). `--max-ai-generations`
caps this. The first N unmapped detections get AI-generated; the rest
are listed in the report as `unresolved` for you to inspect manually:

```bash
# Cap to 5 AI generations
skill-seekers scan ./my-monorepo --max-ai-generations 5

# Or preview cost first without firing any AI generation
skill-seekers scan ./my-monorepo --dry-run --verbose
#   🔍 DRY RUN — no files written, no AI generation invoked.
#   Configs:
#     ✅ 12 resolved      (from local / user / API)
#     🤖 18 AI-generated  (preview — would invoke AI)
#     📂 1 codebase config
```

## URL probing (catch AI hallucinations)

The AI sometimes invents plausible-looking but invalid `base_url`s for
niche libraries. `--probe-urls` HEAD-checks every URL in each generated
config; on 4xx/5xx, re-prompts the AI with feedback. If still unreachable
after the retry, stamps `metadata._url_unverified` so you see what to fix:

```bash
skill-seekers scan ./my-project --probe-urls
```

Adds 5-10 seconds per AI-generated config. Worth it on production scans.

## Flags

| Flag | Default | Purpose |
|---|---|---|
| `--out <dir>` | `./configs/scanned/` | Where to write emitted configs |
| `--no-fetch` | off | Skip the skillseekersweb.com API fallback during resolution |
| `--no-generate` | off | Skip AI generation for unmapped detections (offline / faster) |
| `--no-publish-prompt` | off | Suppress the interactive "Submit to community registry?" prompt (CI-friendly) |
| `--agent <name>` | `claude` (or `$SKILL_SEEKER_AGENT`) | LOCAL agent for non-API mode |
| `--min-confidence <0-1>` | `0.4` | Drop AI detections below this confidence |
| `--max-ai-generations <N>` | `10` | Cap AI generation count. Pass `0` to disable. Prevents surprise bills on monorepos. |
| `--dry-run` | off | Preview what scan would emit without writing or invoking AI |
| `--probe-urls` | off | HEAD-check AI-generated URLs; re-prompt on 4xx/5xx; stamp `_url_unverified` on confirmed-bad URLs |
| `--verbose`, `-v` | off | Show each detection with its evidence + INFO-level logging |

## When to use `scan` vs `create`

- **`scan <dir>`** — you have a project and want to know *what skills it
  needs*. Bootstraps a directory of configs.
- **`create <source>`** — you already know what you want a skill *for*
  (a URL, repo, PDF, or config). Builds one skill at a time.

`scan` produces configs; `create` consumes them. You'll typically run
`scan` once per project, then `create` on a handful of the emitted
configs.

## Privacy note

`scan` sends a bounded excerpt (~64 KB total) of your manifests, README,
CI configs, and **first 2 KB of each sampled source file** to the
configured AI agent. The whole-file sampling means actual source code
is in the prompt — small chunks, not full files, but it is your code.

If you don't want **any** AI call:

- `skill-seekers scan ./path --no-fetch --no-generate` — still calls the
  AI **detector** to identify frameworks; only skips the network/AI
  paths for individual config generation. Not fully local.
- `skill-seekers create ./path --enhance-level 0` — runs the local
  codebase analysis layer (deterministic; no AI), and skips the
  enhancement layer entirely. This is the fully-local flow.

The earlier docs implied `create ./path` was AI-free by default; it
isn't — the default enhancement level (2) sends content to the AI.
`--enhance-level 0` is the switch that keeps everything local.
