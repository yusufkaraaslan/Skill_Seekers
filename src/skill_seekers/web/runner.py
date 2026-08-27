"""Job runner — executes a job spec in an isolated subprocess.

Usage: ``python -m skill_seekers.web.runner <spec.json>``

The spec is produced by the web API layer (see app.py). Stdout is streamed
back to the parent JobManager; emit progress with ``progress(nn, "msg")``
which prints a ``[[PROGRESS:nn]]`` marker line.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
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
        result = module.main()
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
    configs_dir = Path(spec.get("configs_dir") or "configs")
    cwd = Path(spec.get("cwd") or os.getcwd())

    progress(5, "resolving sources…")

    if len(entries) > 1:
        # Unified multi-source: emit a unified config JSON and run via --config
        sources = []
        for e in entries:
            stype = SOURCE_TYPE_MAP.get(e["type"], e["type"])
            key = SOURCE_TO_INPUT_KEY.get(e["type"], "path")
            sources.append({"type": stype, key: e["input"]})
        cfg = {
            "name": name,
            "description": flags.get("description") or f"{name} — unified multi-source skill",
            "merge_mode": flags.get("merge_mode") or "rule-based",
            "sources": sources,
        }
        configs_dir.mkdir(parents=True, exist_ok=True)
        cfg_path = configs_dir / f"{name}-unified.json"
        cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        progress(10, f"wrote {cfg_path}")
        argv = ["--config", str(cfg_path), "--name", name, *_create_flag_argv(flags)]
    else:
        e = entries[0]
        progress(10, f"source: {e['type']} · {e['input']}")
        argv = [e["input"], "--name", name, *_create_flag_argv(flags)]

    progress(15, "launching create pipeline…")
    code = _run_cli_main("skill_seekers.cli.create_command", argv)
    if code != 0:
        return code

    if flags.get("dry_run"):
        progress(100, "dry run complete")
        return 0

    # Package to each requested target
    if targets:
        skill_dir = Path(spec.get("output_dir") or "output") / name
        total = len(targets)
        for i, target in enumerate(targets):
            pct = 80 + int((i / total) * 18)
            progress(pct, f"packaging → {target}…")
            pkg_argv = [str(skill_dir), "--target", target, "--no-open", "--yes"]
            if flags.get("chunk_for_rag"):
                pkg_argv += [
                    "--chunk-for-rag",
                    "--chunk-tokens",
                    str(flags.get("chunk_tokens") or 512),
                    "--chunk-overlap-tokens",
                    str(flags.get("chunk_overlap") or 50),
                ]
            pkg_code = _run_cli_main("skill_seekers.cli.package_skill", pkg_argv)
            if pkg_code != 0:
                print(f"packaging for {target} failed (exit {pkg_code})", flush=True)

    _write_sidecar(cwd, spec)
    return 0


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


def run_package(spec: dict[str, Any]) -> int:
    """Package an existing skill dir to one or more targets.

    ``package_skill`` always writes the archive beside the skill dir
    (``skill_path.parent``). For a seeker-built skill that's fine — it lands
    in the workspace's ``output/``. For an externally-installed skill (a
    plugin bundle, ``~/.claude/skills/...``) that would write into a
    location Skill Seekers doesn't own. When ``spec["output_dir"]`` is set,
    stage a copy of the skill dir there first and package the copy, so the
    archive lands in the workspace instead of at the real source.
    """
    skill_dir = Path(spec["skill_dir"])
    targets: list[str] = spec.get("targets") or ["claude"]
    total = len(targets)

    output_dir = spec.get("output_dir")
    staged: Path | None = None
    package_dir = skill_dir
    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        staged = out / skill_dir.name
        shutil.copytree(skill_dir, staged, dirs_exist_ok=True)
        package_dir = staged

    try:
        for i, target in enumerate(targets):
            progress(10 + int((i / total) * 85), f"packaging → {target}…")
            argv = [
                str(package_dir),
                "--target",
                target,
                "--no-open",
                "--yes",
                "--skip-quality-check",
            ]
            code = _run_cli_main("skill_seekers.cli.package_skill", argv)
            if code != 0:
                return code
        return 0
    finally:
        if staged is not None:
            shutil.rmtree(staged, ignore_errors=True)


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
            dest = install_skill_to_cli(Path(sd), cli)
            print(f"✓ {Path(sd).name} → {dest}", flush=True)
        except Exception as e:  # noqa: BLE001 — report and continue with other skills
            failed += 1
            print(f"✗ {Path(sd).name}: {e}", flush=True)
    return 1 if failed == total else 0


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


DISPATCH = {
    "create": run_create,
    "scan": run_scan,
    "package": run_package,
    "enhance": run_enhance,
    "port": run_port,
    "fetch": run_fetch_source,
    "publish": run_publish,
    "estimate": run_estimate,
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
    progress(100, "done")
    return int(code or 0)


if __name__ == "__main__":
    sys.exit(main())
