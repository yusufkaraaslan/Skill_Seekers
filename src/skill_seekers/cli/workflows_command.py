#!/usr/bin/env python3
"""
Workflows CLI Command

Manage enhancement workflow presets:
  list      List all workflows (bundled + user)
  show      Print YAML content of a workflow
  copy      Copy a bundled workflow to user dir for editing
  add       Install a custom YAML into user dir
  remove    Delete a user workflow (bundled ones cannot be removed)
  validate  Parse and validate a workflow YAML

Usage:
    skill-seekers workflows list
    skill-seekers workflows show security-focus
    skill-seekers workflows copy security-focus
    skill-seekers workflows add ./my-workflow.yaml
    skill-seekers workflows remove my-workflow
    skill-seekers workflows validate security-focus
"""

import shutil
import sys
from pathlib import Path

import yaml

from skill_seekers.cli.enhancement_workflow import (
    WorkflowEngine,
    list_bundled_workflows,
)

USER_WORKFLOWS_DIR = Path.home() / ".config" / "skill-seekers" / "workflows"


def _ensure_user_dir() -> Path:
    USER_WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    return USER_WORKFLOWS_DIR


def _bundled_yaml_text(name: str) -> str | None:
    """Return raw YAML text of a bundled workflow, or None if not found."""
    from importlib.resources import files as importlib_files

    for suffix in (".yaml", ".yml"):
        try:
            pkg_ref = importlib_files("skill_seekers.workflows").joinpath(name + suffix)
            return pkg_ref.read_text(encoding="utf-8")
        except (FileNotFoundError, TypeError, ModuleNotFoundError):
            continue
    return None


def _workflow_yaml_text(name_or_path: str) -> str | None:
    """Resolve a workflow by name or path and return its raw YAML text."""
    # Try as a file path first
    p = Path(name_or_path)
    if p.suffix in (".yaml", ".yml") and p.exists():
        return p.read_text(encoding="utf-8")

    # Try as a name with .yaml extension
    for suffix in (".yaml", ".yml"):
        candidate = Path(name_or_path + suffix)
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")

    # User dir
    user_file = USER_WORKFLOWS_DIR / (name_or_path + ".yaml")
    if user_file.exists():
        return user_file.read_text(encoding="utf-8")
    user_file_yml = USER_WORKFLOWS_DIR / (name_or_path + ".yml")
    if user_file_yml.exists():
        return user_file_yml.read_text(encoding="utf-8")

    # Bundled
    return _bundled_yaml_text(name_or_path)


def _list_user_workflow_names() -> list[str]:
    """Return names of user workflows (without extension) from USER_WORKFLOWS_DIR."""
    if not USER_WORKFLOWS_DIR.exists():
        return []
    return sorted(p.stem for p in USER_WORKFLOWS_DIR.iterdir() if p.suffix in (".yaml", ".yml"))


def cmd_list() -> int:
    """List all available workflows."""
    bundled = list_bundled_workflows()
    user = _list_user_workflow_names()

    if not bundled and not user:
        print("No workflows found.")
        return 0

    if bundled:
        print("Bundled workflows (read-only):")
        for name in bundled:
            # Load description from YAML
            text = _bundled_yaml_text(name)
            desc = ""
            if text:
                try:
                    data = yaml.safe_load(text)
                    desc = data.get("description", "")
                except Exception:
                    pass
            print(f"  {name:<32}  {desc}")

    if user:
        print("\nUser workflows (~/.config/skill-seekers/workflows/):")
        for name in user:
            user_file = USER_WORKFLOWS_DIR / (name + ".yaml")
            if not user_file.exists():
                user_file = USER_WORKFLOWS_DIR / (name + ".yml")
            desc = ""
            try:
                data = yaml.safe_load(user_file.read_text(encoding="utf-8"))
                desc = data.get("description", "")
            except Exception:
                pass
            print(f"  {name:<32}  {desc}")

    return 0


def cmd_show(name: str) -> int:
    """Print YAML content of a workflow."""
    text = _workflow_yaml_text(name)
    if text is None:
        print(f"Error: Workflow '{name}' not found.", file=sys.stderr)
        print("Use 'skill-seekers workflows list' to see available workflows.", file=sys.stderr)
        return 1
    print(text, end="")
    return 0


def cmd_copy(names: list[str]) -> int:
    """Copy one or more bundled workflows to user dir."""
    rc = 0
    for name in names:
        text = _bundled_yaml_text(name)
        if text is None:
            print(f"Error: Bundled workflow '{name}' not found.", file=sys.stderr)
            bundled = list_bundled_workflows()
            if bundled:
                print(f"Available bundled workflows: {', '.join(bundled)}", file=sys.stderr)
            rc = 1
            continue

        dest = _ensure_user_dir() / (name + ".yaml")
        if dest.exists():
            print(f"Warning: '{dest}' already exists. Overwriting.")

        dest.write_text(text, encoding="utf-8")
        print(f"Copied '{name}' to: {dest}")
        print(
            f"Edit it with your favourite editor, then reference it as '--enhance-workflow {name}'"
        )

    return rc


def cmd_add(file_paths: list[str], override_name: str | None = None) -> int:
    """Install one or more custom YAML workflows into user dir."""
    if override_name and len(file_paths) > 1:
        print("Error: --name cannot be used when adding multiple files.", file=sys.stderr)
        return 1

    rc = 0
    for file_path in file_paths:
        src = Path(file_path)
        if not src.exists():
            print(f"Error: File '{file_path}' does not exist.", file=sys.stderr)
            rc = 1
            continue
        if src.suffix not in (".yaml", ".yml"):
            print(f"Error: '{file_path}' must have a .yaml or .yml extension.", file=sys.stderr)
            rc = 1
            continue

        # Validate before installing
        try:
            text = src.read_text(encoding="utf-8")
            data = yaml.safe_load(text)
            if not isinstance(data, dict):
                raise ValueError("YAML root must be a mapping")
            if "stages" not in data:
                raise ValueError("Workflow must contain a 'stages' key")
        except Exception as exc:
            print(f"Error: Invalid workflow YAML '{file_path}' – {exc}", file=sys.stderr)
            rc = 1
            continue

        dest_name = override_name if override_name else src.stem
        dest = _ensure_user_dir() / (dest_name + ".yaml")

        if dest.exists():
            print(f"Warning: '{dest}' already exists. Overwriting.")

        shutil.copy2(src, dest)
        print(f"Installed workflow '{dest_name}' to: {dest}")

    return rc


def cmd_remove(names: list[str]) -> int:
    """Delete one or more user workflows."""
    rc = 0
    bundled = list_bundled_workflows()
    for name in names:
        if name in bundled:
            print(
                f"Error: '{name}' is a bundled workflow and cannot be removed.",
                file=sys.stderr,
            )
            print("Use 'skill-seekers workflows copy' to create an editable copy.", file=sys.stderr)
            rc = 1
            continue

        removed = False
        for suffix in (".yaml", ".yml"):
            candidate = USER_WORKFLOWS_DIR / (name + suffix)
            if candidate.exists():
                candidate.unlink()
                print(f"Removed workflow: {candidate}")
                removed = True
                break

        if not removed:
            print(f"Error: User workflow '{name}' not found.", file=sys.stderr)
            rc = 1

    return rc


def cmd_validate(name_or_path: str) -> int:
    """Parse and validate a workflow."""
    try:
        engine = WorkflowEngine(name_or_path)
        wf = engine.workflow
        print(f"✅ Workflow '{wf.name}' is valid.")
        print(f"   Description : {wf.description}")
        print(f"   Version     : {wf.version}")
        print(f"   Stages      : {len(wf.stages)}")
        for stage in wf.stages:
            status = "enabled" if stage.enabled else "disabled"
            print(f"     - {stage.name} ({stage.type}, {status})")
        return 0
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error: Invalid workflow – {exc}", file=sys.stderr)
        return 1


def main(argv=None) -> None:
    """Entry point for skill-seekers-workflows."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="skill-seekers-workflows",
        description="Manage enhancement workflow presets",
    )
    subparsers = parser.add_subparsers(dest="action", metavar="ACTION")

    subparsers.add_parser("list", help="List all workflows (bundled + user)")

    show_p = subparsers.add_parser("show", help="Print YAML content of a workflow")
    show_p.add_argument("workflow_name")

    copy_p = subparsers.add_parser("copy", help="Copy bundled workflow(s) to user dir")
    copy_p.add_argument("workflow_names", nargs="+")

    add_p = subparsers.add_parser("add", help="Install custom YAML file(s) into user dir")
    add_p.add_argument("files", nargs="+")
    add_p.add_argument("--name")

    remove_p = subparsers.add_parser("remove", help="Delete user workflow(s)")
    remove_p.add_argument("workflow_names", nargs="+")

    validate_p = subparsers.add_parser("validate", help="Validate a workflow by name or file")
    validate_p.add_argument("workflow_name")

    args = parser.parse_args(argv)

    if args.action is None:
        parser.print_help()
        sys.exit(0)

    rc = 0
    if args.action == "list":
        rc = cmd_list()
    elif args.action == "show":
        rc = cmd_show(args.workflow_name)
    elif args.action == "copy":
        rc = cmd_copy(args.workflow_names)
    elif args.action == "add":
        rc = cmd_add(args.files, getattr(args, "name", None))
    elif args.action == "remove":
        rc = cmd_remove(args.workflow_names)
    elif args.action == "validate":
        rc = cmd_validate(args.workflow_name)
    else:
        parser.print_help()

    sys.exit(rc)


if __name__ == "__main__":
    main()
