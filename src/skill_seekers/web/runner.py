"""Job runner — executes a job spec in an isolated subprocess.

Usage: ``python -m skill_seekers.web.runner <spec.json>``

The spec is produced by the web API layer (see app.py). Stdout is streamed
back to the parent JobManager; emit progress with ``progress(nn, "msg")``
which prints a ``[[PROGRESS:nn]]`` marker line.
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

SOURCE_TO_INPUT_KEY: dict[str, str] = {
    "docs": "base_url",
    "wiki": "base_url",
    "github": "repo",
    "video": "url",
    "openapi": "path",
    "rss": "url",
    "confluence": "url",
    "notion": "url",
    "manpage": "path",
}

# Frontend source types -> unified config source types (they differ for a few)
SOURCE_TYPE_MAP: dict[str, str] = {
    "docs": "documentation",
    "notebook": "jupyter",
    "docx": "word",
    "wiki": "documentation",
}


def progress(pct: int, msg: str = "") -> None:
    """Emit a progress marker consumed by JobManager."""
    print(f"[[PROGRESS:{pct}]] {msg}", flush=True)


def _run_cli_main(module_name: str, argv: list[str]) -> int:
    """Run a CLI module's main() with a replaced sys.argv."""
    import importlib

    old_argv = sys.argv
    sys.argv = [module_name.rsplit(".", 1)[-1], *argv]
    try:
        module = importlib.import_module(module_name)
        try:
            result = module.main()
        except SystemExit as exc:
            if exc.code is None:
                return 0
            if isinstance(exc.code, int):
                return exc.code
            print(str(exc.code), flush=True)
            return 1
        return int(result) if isinstance(result, int) else 0
    finally:
        sys.argv = old_argv


def _create_flag_argv(flags: dict[str, Any]) -> list[str]:
    """Translate wizard flags into `create` CLI arguments."""
    argv: list[str] = []
    if flags.get("description"):
        argv += ["--description", str(flags["description"])]
    level = flags.get("enhance_level")
    if level is not None:
        argv += ["--enhance-level", str(level)]
    if flags.get("preset") and flags["preset"] != "standard":
        argv += ["--preset", str(flags["preset"])]
    if flags.get("agent"):
        argv += ["--agent", str(flags["agent"])]
    for wf in flags.get("workflows") or []:
        argv += ["--enhance-workflow", wf]
    if flags.get("max_pages"):
        argv += ["--max-pages", str(flags["max_pages"])]
    if flags.get("rate_limit"):
        argv += ["--rate-limit", str(flags["rate_limit"])]
    if flags.get("workers") and str(flags["workers"]) != "1":
        argv += ["--workers", str(flags["workers"])]
    if flags.get("async_mode"):
        argv += ["--async"]
    if flags.get("merge_mode"):
        argv += ["--merge-mode", str(flags["merge_mode"])]
    if flags.get("skip_codebase"):
        argv += ["--skip-codebase-analysis"]
    for skip in flags.get("local_skips") or []:
        argv.append(str(skip))
    if flags.get("dry_run"):
        argv += ["--dry-run"]
    if flags.get("fresh"):
        argv += ["--fresh"]
    if flags.get("resume"):
        argv += ["--resume"]
    if flags.get("non_interactive"):
        argv += ["--non-interactive"]
    return argv


def run_create(spec: dict[str, Any]) -> int:
    """Build config(s) and run the create pipeline, then package targets."""
    entries: list[dict[str, str]] = spec["entries"]
    name = spec.get("name") or "untitled-skill"
    flags: dict[str, Any] = spec.get("flags") or {}
    targets: list[str] = spec.get("targets") or []
    cwd = Path(spec.get("cwd") or os.getcwd())
    configs_dir = cwd / Path(spec.get("configs_dir") or "configs").expanduser()
    output_path = cwd / Path(spec.get("output_dir") or "output").expanduser() / name

    progress(5, "resolving sources…")

    if len(entries) > 1 or entries[0]["type"] in ("confluence", "notion", "chat"):
        # Unified multi-source: emit a unified config JSON and run via --config
        sources = []
        for e in entries:
            stype = SOURCE_TYPE_MAP.get(e["type"], e["type"])
            key = SOURCE_TO_INPUT_KEY.get(e["type"], "path")
            value = e["input"].strip()
            remote = value.startswith(("https://", "http://"))
            if e["type"] in ("video", "rss", "openapi", "confluence", "notion"):
                key = "url" if remote else "path"
            if key == "path":
                value = str((cwd / Path(value).expanduser()).resolve())
            source = {"type": stype, key: value}
            if e["type"] == "github":
                source["repo"] = (
                    value.removeprefix("https://github.com/")
                    .removeprefix("http://github.com/")
                    .removesuffix(".git")
                    .strip("/")
                )
            if e["type"] == "notion" and remote:
                import re

                match = re.search(r"([a-fA-F0-9]{32}|[a-fA-F0-9-]{36})(?:[?/#]|$)", value)
                if not match:
                    raise ValueError(
                        "Use a Notion page URL containing its page ID, or an export path"
                    )
                source = {"type": stype, "page_id": match.group(1)}
            if e["type"] == "confluence" and remote:
                from urllib.parse import urlsplit

                parts = urlsplit(value)
                segments = parts.path.split("/")
                if "spaces" not in segments or segments.index("spaces") + 1 >= len(segments):
                    raise ValueError("Use a Confluence /spaces/SPACE URL, or an export path")
                source["space_key"] = segments[segments.index("spaces") + 1]
                source["base_url"] = f"{parts.scheme}://{parts.netloc}" + (
                    "/wiki" if parts.path.startswith("/wiki/") else ""
                )
            for option in ("max_pages", "rate_limit"):
                if flags.get(option) not in (None, ""):
                    source[option] = (
                        float(flags[option]) if option == "rate_limit" else int(flags[option])
                    )
            sources.append(source)
        cfg = {
            "name": name,
            "description": flags.get("description") or f"{name} — unified multi-source skill",
            "merge_mode": flags.get("merge_mode") or "rule-based",
            "sources": sources,
        }
        configs_dir.mkdir(parents=True, exist_ok=True)
        # Stable name: re-running the same create (or Retry) overwrites its own
        # config instead of littering configs/ with random files.
        from .paths import atomic_write

        cfg_path = configs_dir / f"{name}-unified.json"
        atomic_write(cfg_path, json.dumps(cfg, indent=2).encode("utf-8"))
        progress(10, f"wrote {cfg_path}")
        argv = ["--config", str(cfg_path), "--name", name, *_create_flag_argv(flags)]
    else:
        e = entries[0]
        progress(10, f"source: {e['type']} · {e['input']}")
        argv = [e["input"], "--name", name, *_create_flag_argv(flags)]

    argv += ["--output", str(output_path), "--non-interactive"]

    progress(15, "launching create pipeline…")
    code = _run_cli_main("skill_seekers.cli.create_command", argv)
    if code != 0:
        return code

    if flags.get("dry_run"):
        progress(100, "dry run complete")
        return 0

    if not (output_path / "SKILL.md").is_file():
        raise RuntimeError(f"Create finished without producing {output_path / 'SKILL.md'}")
    # Package to each requested target
    _write_sidecar(cwd, spec)
    artifact(output_path)
    if targets:
        return run_package(
            {
                "skill_dir": str(output_path),
                "targets": targets,
                "output_dir": str(output_path.parent / "_packages"),
                "flags": flags,
            }
        )
    return 0


def artifact(path: Path) -> None:
    """Publish an output location for the job detail view."""
    print("[[ARTIFACT]] " + json.dumps(str(path.resolve())), flush=True)


def _write_sidecar(cwd: Path, spec: dict[str, Any]) -> None:
    """Record provenance next to the built skill for registry discovery."""
    name = spec.get("name")
    if not name:
        return
    skill_dir = cwd / (spec.get("output_dir") or "output") / name
    if not skill_dir.is_dir():
        return
    meta = {
        "source": ", ".join(e["input"] for e in spec.get("entries", [])),
        "source_type": spec.get("entries", [{}])[0].get("type", "docs"),
        "targets": spec.get("targets", []),
    }
    import contextlib

    with contextlib.suppress(OSError):
        (skill_dir / ".seeker-meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def run_scan(spec: dict[str, Any]) -> int:
    """Run project scan via ScanCommand with a standalone parser namespace."""
    from skill_seekers.cli.parsers.scan_parser import ScanParser
    from skill_seekers.cli.scan_command import ScanCommand

    directory = spec["directory"]
    out = spec.get("out") or "configs/scanned"
    progress(10, f"collecting signals in {directory}…")
    parser = ScanParser().build_standalone(prog="skill-seekers scan")
    argv = [directory, "--out", out, "--no-publish-prompt", "--no-fetch"]
    if spec.get("agent"):
        argv += ["--agent", spec["agent"]]
    args = parser.parse_args(argv)
    progress(20, "detecting frameworks…")
    code = ScanCommand(args).execute()
    progress(90, "scan complete")
    return int(code or 0)


def _package_targets(
    skill_dir: str,
    targets: list[str],
    flags: dict | None = None,
    first: int = 0,
    count: int | None = None,
) -> int:
    """Run the package CLI for each target against ``skill_dir`` in turn.

    ``first``/``count`` let a caller that packages one target at a time report
    progress across the whole job instead of restarting at 10% per target.
    """
    total = count or len(targets)
    for i, target in enumerate(targets):
        progress(10 + int(((first + i) / total) * 85), f"packaging → {target}…")
        argv = [skill_dir, "--target", target, "--no-open", "--yes", "--skip-quality-check"]
        if flags and flags.get("chunk_for_rag"):
            argv += [
                "--chunk-for-rag",
                "--chunk-tokens",
                str(flags.get("chunk_tokens") or 512),
                "--chunk-overlap-tokens",
                str(flags.get("chunk_overlap") or 50),
            ]
        code = _run_cli_main("skill_seekers.cli.package_skill", argv)
        if code != 0:
            return code
    return 0


def run_package(spec: dict[str, Any]) -> int:
    """Package an existing skill dir to one or more targets.

    ``package_skill`` always writes the archive beside the skill dir
    (``skill_path.parent``). For a seeker-built skill that's fine — it lands
    in the workspace's ``output/``. For an externally-installed skill (a
    plugin bundle, ``~/.claude/skills/...``) that would write into a
    location Skill Seekers doesn't own. When ``spec["output_dir"]`` is set,
    stage a copy of the skill dir in a job-unique temp dir under
    ``output_dir`` first, package the copy, then move the resulting
    archive(s) up into ``output_dir`` — so concurrent packaging jobs for the
    same skill never share a staging path, and a failed copy can't leave a
    half-written directory sitting where the next run would collide with it.
    """
    skill_dir = Path(spec["skill_dir"])
    targets: list[str] = list(dict.fromkeys(spec.get("targets") or ["claude"]))

    output_dir = spec.get("output_dir")
    if not output_dir:
        code = _package_targets(str(skill_dir), targets, spec.get("flags"))
        if code == 0:
            artifact(skill_dir.parent)
        return code

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    # Unique per job: concurrent packages of the same skill must not share a path.
    staging = Path(tempfile.mkdtemp(prefix=f".staging-{skill_dir.name}-", dir=out))
    staged = staging / (skill_dir.stem if skill_dir.is_file() else skill_dir.name)
    try:
        if skill_dir.is_file():
            staged.mkdir()
            shutil.copy2(skill_dir, staged / "SKILL.md")
        else:
            shutil.copytree(skill_dir, staged)
        grouped = staging / ".formats"
        code = 0
        for i, target in enumerate(targets):
            code = _package_targets(
                str(staged), [target], spec.get("flags"), first=i, count=len(targets)
            )
            if code != 0:
                break
            # One directory per target, always: adaptors reuse filenames, and a
            # layout that depends on the target count is a trap for consumers.
            target_dir = grouped / target
            target_dir.mkdir(parents=True)
            for item in list(staging.iterdir()):
                if item not in (staged, grouped):
                    shutil.move(str(item), str(target_dir / item.name))
        if code == 0:
            # The CLI writes archives beside the skill dir, i.e. into `staging/`.
            from .paths import state_transaction

            with state_transaction():
                job_suffix = staging.name.rsplit("-", 1)[-1]
                for target_dir in sorted(grouped.iterdir()):
                    dest_dir = out / target_dir.name
                    dest_dir.mkdir(exist_ok=True)
                    artifact(dest_dir)
                    for item in sorted(target_dir.iterdir()):
                        dest = dest_dir / item.name
                        if dest.exists():  # earlier run of the same skill: keep both
                            dest = dest_dir / f"{item.stem}-{job_suffix}{item.suffix}"
                        shutil.move(str(item), str(dest))
                        if dest.is_dir():
                            for file in sorted(dest.rglob("*")):
                                if file.is_file():
                                    artifact(file)
                        else:
                            artifact(dest)
        return code
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def run_enhance(spec: dict[str, Any]) -> int:
    """Enhance an existing skill dir (API or LOCAL agent mode)."""
    skill_dir = spec["skill_dir"]
    argv = [skill_dir, "--timeout", str(spec.get("timeout") or 600)]
    if spec.get("target"):
        argv += ["--target", spec["target"]]
    elif spec.get("agent"):
        argv += ["--agent", spec["agent"]]
    progress(15, "enhancement pass started…")
    return _run_cli_main("skill_seekers.cli.enhance_command", argv)


def run_port(spec: dict[str, Any]) -> int:
    """Install skill(s) into a CLI's global install location."""
    from skill_seekers.web.installer import install_skill_to_cli

    skill_dirs: list[str] = spec["skill_dirs"]
    cli = spec["cli"]
    total = len(skill_dirs)
    failed = 0
    for i, sd in enumerate(skill_dirs):
        progress(10 + int((i / total) * 85), f"installing {Path(sd).name} → {cli}…")
        try:
            dest = install_skill_to_cli(Path(sd), cli, replace=spec.get("replace", False))
            print(f"✓ {Path(sd).name} → {dest}", flush=True)
            artifact(dest)
        except Exception as e:  # noqa: BLE001 — report and continue with other skills
            failed += 1
            print(f"✗ {Path(sd).name}: {e}", flush=True)
    return 1 if failed else 0


def run_fetch_source(spec: dict[str, Any]) -> int:
    """Clone/pull a config source repo via GitConfigRepo."""
    from skill_seekers.services.git_repo import GitConfigRepo

    progress(20, f"fetching {spec['git_url']} ({spec.get('branch', 'main')})…")
    repo = GitConfigRepo()
    path = repo.clone_or_pull(
        source_name=spec["name"],
        git_url=spec["git_url"],
        branch=spec.get("branch", "main"),
        token=os.environ.get(spec.get("token_env") or "", None),
    )
    configs = repo.find_configs(Path(path) if not isinstance(path, Path) else path)
    progress(85, f"{len(configs)} configs found")
    artifact(Path(path))
    return 0


def run_market_sync(spec: dict[str, Any]) -> int:
    """Refresh a marketplace cache in a visible background job."""
    from .market import sync_marketplace

    path = sync_marketplace(spec["git_url"], spec.get("branch", "main"))
    artifact(path)
    return 0


def run_market_install(spec: dict[str, Any]) -> int:
    """Install one marketplace item to explicitly chosen destinations."""
    from .market import install_marketplace_item

    dest = install_marketplace_item(
        Path(spec["path"]),
        spec["kind"],
        Path(spec["cwd"]),
        spec.get("clis", []),
        replace=spec.get("replace", False),
    )
    artifact(dest)
    return 0


def run_publish(spec: dict[str, Any]) -> int:
    """Publish a skill to a registered marketplace."""
    from skill_seekers.services.marketplace_publisher import MarketplacePublisher

    progress(20, f"publishing {spec['skill_dir']} → {spec['marketplace']}…")
    publisher = MarketplacePublisher()
    result = publisher.publish(
        skill_dir=spec["skill_dir"],
        marketplace_name=spec["marketplace"],
        category=spec.get("category", "community"),
    )
    if not result.get("success"):
        print(f"✗ {result.get('message', 'publish failed')}", flush=True)
        return 1
    progress(85, result.get("message", "published"))
    return 0


def run_estimate(spec: dict[str, Any]) -> int:
    """Estimate page count for a source."""
    return _run_cli_main("skill_seekers.cli.estimate_pages", [spec["source"]])


UPLOAD_OPTION_FLAGS = {
    "persist_directory": "--persist-directory",
    "chroma_url": "--chroma-url",
    "embedding_function": "--embedding-function",
    "weaviate_url": "--weaviate-url",
    "cluster_url": "--cluster-url",
    "api_key": "--api-key",
}


def run_upload(spec: dict[str, Any]) -> int:
    """Package for one target, then hand the archive to upload_skill."""
    target = spec["target"]
    out = Path(spec["output_dir"])
    code = run_package(
        {
            "skill_dir": spec["skill_dir"],
            "targets": [target],
            "output_dir": str(out),
            "flags": spec.get("flags"),
        }
    )
    if code != 0:
        return code
    archives = [p for p in (out / target).iterdir() if p.suffix in (".zip", ".gz")]
    if not archives:
        raise RuntimeError(f"packaging for {target} produced no archive under {out / target}")
    newest = max(archives, key=lambda p: p.stat().st_mtime)
    argv = [str(newest), "--target", target]
    for key, flag in UPLOAD_OPTION_FLAGS.items():
        value = (spec.get("options") or {}).get(key)
        if value not in (None, ""):
            argv += [flag, str(value)]
    if (spec.get("options") or {}).get("use_cloud"):
        argv.append("--use-cloud")
    progress(60, f"uploading → {target}…")
    return _run_cli_main("skill_seekers.cli.upload_skill", argv)


def run_translate(spec: dict[str, Any]) -> int:
    progress(10, f"translating → {', '.join(spec['languages'])}…")
    return _run_cli_main(
        "skill_seekers.cli.multilang_support",
        [spec["skill_dir"], "--languages", *spec["languages"]],
    )


def run_update(spec: dict[str, Any]) -> int:
    flag = "--force" if spec.get("apply") else "--check-changes"
    progress(
        10, "checking upstream for changes…" if flag == "--check-changes" else "applying update…"
    )
    return _run_cli_main("skill_seekers.cli.incremental_updater", [spec["skill_dir"], flag])


def run_quality(spec: dict[str, Any]) -> int:
    out = Path(spec["output_dir"])
    out.mkdir(parents=True, exist_ok=True)
    report = out / f"{Path(spec['skill_dir']).name}-quality.json"
    code = _run_cli_main(
        "skill_seekers.cli.quality_metrics",
        [spec["skill_dir"], "--report", "--output", str(report)],
    )
    if code == 0 and report.is_file():
        artifact(report)
    return code


ANALYZE_DEPTH = {"basic": "surface", "c3x": "deep"}
# Run order, not menu order: `guides` consumes the JSON `tests` writes, so the
# tools always execute in this sequence whatever order the request listed them.
ANALYZE_TOOL_ORDER = ("patterns", "tests", "guides", "config", "router", "quality")
# pattern_recognizer's --output is a directory; it writes this file inside it.
PATTERN_RESULT_NAME = "detected_patterns.json"
# Per-tool JSON keys holding the thing the manifest counts.
COUNT_LIST_KEYS = ("patterns", "examples", "guides", "config_files", "configs")
COUNT_TOTAL_KEYS = ("total_patterns_detected", "total_examples", "total_guides", "total_files")


def _analysis_count(tool: str, path: Path) -> float | None:
    """Headline number for an analysis result file (score for quality)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    if tool == "quality":
        metrics = data.get("metrics")
        overall = metrics.get("overall") if isinstance(metrics, dict) else None
        if overall is None:
            score = data.get("overall_score")
            overall = score.get("total_score") if isinstance(score, dict) else score
        return overall if isinstance(overall, (int, float)) else None
    for key in COUNT_LIST_KEYS:
        if isinstance(data.get(key), list):
            return len(data[key])
    for key in COUNT_TOTAL_KEYS:
        if isinstance(data.get(key), int):
            return data[key]
    return None


def _tool_output(path: Path, nested: str | None = None) -> Path | None:
    """Resolve a tool's result: the path itself, or a known file inside it."""
    if path.is_file():
        return path
    if nested and (path / nested).is_file():
        return path / nested
    return None


def _capture_json(module: str, argv: list[str], out: Path) -> int:
    """Run a CLI that prints its JSON report to stdout, saving it to ``out``."""
    with open(out, "w", encoding="utf-8") as stream, contextlib.redirect_stdout(stream):
        return _run_cli_main(module, argv)


def _router_configs(spec: dict[str, Any], target: str) -> list[str]:
    """Sub-skill configs of a skill target built from a unified config."""
    from .paths import read_json

    if spec.get("target", {}).get("kind") != "skill":
        return []
    configs_dir = Path(spec.get("configs_dir") or "configs")
    skill_dir = Path(target)
    sidecar = read_json(skill_dir / ".seeker-meta.json", {})
    stored = sidecar.get("config") if isinstance(sidecar, dict) else None
    config = read_json(Path(stored or configs_dir / f"{skill_dir.name}.json"), {})
    if not isinstance(config, dict):
        return []
    names = [s.get("name") for s in config.get("sources") or [] if isinstance(s, dict)]
    paths = [configs_dir / f"{name}.json" for name in names if name]
    return [str(p) for p in paths if p.is_file()]


@contextlib.contextmanager
def _analysis_target(spec: dict[str, Any]):
    """Yield a local directory to analyse, cloning a repo target first."""
    target = spec["target"]
    if target.get("kind") != "repo":
        yield target["value"]
        return
    repo = target["value"]
    with tempfile.TemporaryDirectory(prefix="seeker-analyze-") as tmp:
        progress(5, f"cloning {repo}…")
        clone = subprocess.run(
            ["git", "clone", "--depth", "1", f"https://github.com/{repo}", tmp],
            capture_output=True,
            text=True,
        )
        if clone.returncode != 0:
            raise RuntimeError(f"git clone failed for {repo}: {clone.stderr.strip()}")
        yield tmp


def run_analyze(spec: dict[str, Any]) -> int:
    """Run the selected C3.x tools over a target and record a manifest."""
    from .analysis_store import slug_for, write_manifest

    root = Path(spec["cwd"])
    slug = slug_for(spec["target"]["value"])
    out_dir = Path(spec["output_dir"]) / "_analysis" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    depth = ANALYZE_DEPTH.get(spec.get("depth", "basic"), "surface")
    ai_mode = spec.get("ai_mode", "off")
    no_ai = ai_mode == "off"
    results: dict[str, Any] = {}
    tools = sorted(
        spec["tools"],
        key=lambda t: (
            ANALYZE_TOOL_ORDER.index(t) if t in ANALYZE_TOOL_ORDER else len(ANALYZE_TOOL_ORDER)
        ),
    )
    with _analysis_target(spec) as target:
        for i, tool in enumerate(tools):
            progress(10 + int((i / len(tools)) * 85), f"{tool}…")
            out = out_dir / f"{tool}.json"
            nested = None
            if tool == "patterns":
                out, nested = out_dir / "patterns", PATTERN_RESULT_NAME
                code = _run_cli_main(
                    "skill_seekers.cli.pattern_recognizer",
                    ["--directory", target, "--output", str(out), "--depth", depth, "--json"],
                )
            elif tool == "tests":
                code = _capture_json(
                    "skill_seekers.cli.test_example_extractor",
                    [
                        target,
                        "--json",
                        "--recursive",
                        "--min-confidence",
                        str(spec.get("min_confidence", 0.7)),
                    ],
                    out,
                )
            elif tool == "guides":
                examples = out_dir / "tests.json"
                if not examples.is_file():
                    print("skipping guides: select the tests tool to feed it", flush=True)
                    code = 0
                else:
                    # --json-output makes the builder print the collection and
                    # ignore --output, so capture stdout instead.
                    argv = ["--input", str(examples), "--json-output"]
                    code = _capture_json(
                        "skill_seekers.cli.how_to_guide_builder",
                        argv + (["--no-ai"] if no_ai else []),
                        out,
                    )
            elif tool == "config":
                code = _run_cli_main(
                    "skill_seekers.cli.config_extractor",
                    [target, "--output", str(out), "--ai-mode", "none" if no_ai else ai_mode],
                )
            elif tool == "quality":
                code = _run_cli_main(
                    "skill_seekers.cli.quality_metrics", [target, "--report", "--output", str(out)]
                )
            elif tool == "router":
                configs = _router_configs(spec, target)
                if not configs:
                    print(
                        "skipping router: target is not a skill with sub-skill configs", flush=True
                    )
                    code = 0
                else:
                    code = _run_cli_main(
                        "skill_seekers.cli.generate_router",
                        [*configs, "--output-dir", str(out_dir)],
                    )
            else:
                print(f"skipping unsupported tool {tool}", flush=True)
                code = 0
            if code != 0:
                return code
            found = _tool_output(out, nested)
            if found:
                artifact(found)
                results[tool] = {"count": _analysis_count(tool, found), "path": str(found)}
    write_manifest(
        root,
        slug,
        {
            "target": spec["target"]["value"],
            "tools": tools,
            "startedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
            "attachedTo": spec.get("attach_to"),
            "results": results,
        },
    )
    return 0


DISPATCH = {
    "create": run_create,
    "scan": run_scan,
    "package": run_package,
    "enhance": run_enhance,
    "port": run_port,
    "fetch": run_fetch_source,
    "publish": run_publish,
    "estimate": run_estimate,
    "market-sync": run_market_sync,
    "install": run_market_install,
    "upload": run_upload,
    "translate": run_translate,
    "update": run_update,
    "quality": run_quality,
    "analyze": run_analyze,
}


def main() -> int:
    """Entry point: load spec, dispatch, report exit code."""
    if len(sys.argv) < 2:
        print("usage: python -m skill_seekers.web.runner <spec.json>", flush=True)
        return 2
    spec_path = Path(sys.argv[1])
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    job_type = spec.get("type")
    handler = DISPATCH.get(job_type)
    if handler is None:
        print(f"unknown job type: {job_type}", flush=True)
        return 2
    try:
        code = handler(spec)
    except Exception as e:  # noqa: BLE001 — surface any failure to the job log
        import traceback

        traceback.print_exc()
        print(f"✗ {type(e).__name__}: {e}", flush=True)
        return 1
    if not code:
        progress(100, "done")
    return int(code or 0)


if __name__ == "__main__":
    sys.exit(main())
