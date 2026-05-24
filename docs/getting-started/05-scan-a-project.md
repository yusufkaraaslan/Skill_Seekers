# Scan an entire project (AI-driven)

`skill-seekers scan` is the fastest way to bootstrap a knowledge base for a
real codebase. Instead of running `create` once per framework, point `scan`
at a project directory and an AI agent figures out the tech stack for you.

## What it does

1. **Collects signals** from the project root: dependency manifests
   (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Gemfile`,
   `build.gradle`, `pom.xml`, `composer.json`, `mix.exs`, …), README,
   Dockerfile / docker-compose / GitHub Actions, sampled source-file
   imports, and the git remote URL.
2. **AI detector** classifies the signals — returns the frameworks,
   libraries, tools and services the project actually uses (with
   versions, ecosystems, and confidence scores).
3. **Resolves each detection** against the local repo `configs/`, then the
   user config dir `~/.config/skill-seekers/configs/`, then the
   [skillseekersweb.com](https://skillseekersweb.com/) API. The detected
   version is pinned into the emitted config (`detected_version` field).
4. **AI-generates** a fresh config for anything that has no existing
   preset, validated by the same schema as the built-in configs.
5. **Always emits `<project>-codebase.json`** — a `type: "local"` config
   pointed at your project root, so you get a skill about *your* code
   alongside the framework skills.
6. **Optional publish**: for each freshly AI-generated config, you're
   asked whether to submit it back to the community registry (opens a
   GitHub issue, no git push required).

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
packages. Use this in CI to keep your skills aligned with the project's
actual dependencies.

```bash
skill-seekers scan ./my-react-app --out ./configs/scanned/
#   Diff vs previous scan:
#     + added       prisma
#     ↻ updated     react   18.2.0 → 18.3.1
#     - removed     moment
```

## Flags

| Flag | Default | Purpose |
|---|---|---|
| `--out <dir>` | `./configs/scanned/` | Where to write emitted configs |
| `--no-fetch` | off | Skip the skillseekersweb.com API fallback during resolution |
| `--no-generate` | off | Skip AI generation for unmapped detections (offline / faster) |
| `--no-publish-prompt` | off | Suppress the interactive "Submit to community registry?" prompt (CI-friendly) |
| `--agent <name>` | `claude` (or `$SKILL_SEEKER_AGENT`) | LOCAL agent for non-API mode |
| `--min-confidence <0-1>` | `0.4` | Drop AI detections below this confidence |
| `--verbose`, `-v` | off | Show each detection with its evidence |

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
