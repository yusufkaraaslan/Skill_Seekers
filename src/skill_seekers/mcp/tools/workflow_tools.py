"""
MCP Tool Implementations for Workflow Management

5 tools:
  list_workflows   – list all workflows (bundled + user) with source info
  get_workflow     – return full YAML of a named workflow
  create_workflow  – write a new YAML to user dir
  update_workflow  – overwrite an existing user workflow
  delete_workflow  – remove a user workflow by name
"""

from __future__ import annotations

from pathlib import Path

import yaml

try:
    from mcp.types import TextContent
except ImportError:
    # Graceful degradation for testing without mcp installed
    class TextContent:  # type: ignore[no-redef]
        def __init__(self, type: str, text: str):
            self.type = type
            self.text = text


USER_WORKFLOWS_DIR = Path.home() / ".config" / "skill-seekers" / "workflows"


def _ensure_user_dir() -> Path:
    USER_WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    return USER_WORKFLOWS_DIR


def _bundled_names() -> list[str]:
    from importlib.resources import files as importlib_files

    try:
        pkg = importlib_files("skill_seekers.workflows")
        names = []
        for item in pkg.iterdir():
            name = str(item.name)
            if name.endswith((".yaml", ".yml")):
                names.append(name.removesuffix(".yaml").removesuffix(".yml"))
        return sorted(names)
    except Exception:
        return []


def _user_names() -> list[str]:
    if not USER_WORKFLOWS_DIR.exists():
        return []
    return sorted(p.stem for p in USER_WORKFLOWS_DIR.iterdir() if p.suffix in (".yaml", ".yml"))


def _read_bundled(name: str) -> str | None:
    from importlib.resources import files as importlib_files

    for suffix in (".yaml", ".yml"):
        try:
            pkg_ref = importlib_files("skill_seekers.workflows").joinpath(name + suffix)
            return pkg_ref.read_text(encoding="utf-8")
        except (FileNotFoundError, TypeError, ModuleNotFoundError):
            continue
    return None


def _read_workflow(name: str) -> str | None:
    """Read YAML text: user dir first, then bundled."""
    for suffix in (".yaml", ".yml"):
        p = USER_WORKFLOWS_DIR / (name + suffix)
        if p.exists():
            return p.read_text(encoding="utf-8")
    return _read_bundled(name)


def _validate_yaml(text: str) -> dict:
    """Parse and basic-validate workflow YAML; returns parsed dict."""
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("Workflow YAML root must be a mapping")
    if "stages" not in data:
        raise ValueError("Workflow must contain a 'stages' key")
    return data


# ──────────────────────────────────────────────────────────────────────────────
# Tool implementations
# ──────────────────────────────────────────────────────────────────────────────


def list_workflows_tool(_args: dict) -> list:
    """Return all workflows with name, description, and source."""
    result: list[dict[str, str]] = []

    for name in _bundled_names():
        desc = ""
        text = _read_bundled(name)
        if text:
            try:
                data = yaml.safe_load(text)
                desc = data.get("description", "")
            except Exception:
                pass
        result.append({"name": name, "description": desc, "source": "bundled"})

    for name in _user_names():
        desc = ""
        text = _read_workflow(name)
        if text:
            try:
                data = yaml.safe_load(text)
                desc = data.get("description", "")
            except Exception:
                pass
        result.append({"name": name, "description": desc, "source": "user"})

    output = yaml.dump(result, default_flow_style=False, sort_keys=False)
    return [TextContent(type="text", text=output)]


def get_workflow_tool(args: dict) -> list:
    """Return full YAML content of a named workflow."""
    name = args.get("name", "").strip()
    if not name:
        return [TextContent(type="text", text="Error: 'name' parameter is required.")]

    text = _read_workflow(name)
    if text is None:
        bundled = _bundled_names()
        user = _user_names()
        available = bundled + [f"{n} (user)" for n in user]
        msg = (
            f"Error: Workflow '{name}' not found.\n"
            f"Available workflows: {', '.join(available) if available else 'none'}"
        )
        return [TextContent(type="text", text=msg)]

    return [TextContent(type="text", text=text)]


def create_workflow_tool(args: dict) -> list:
    """Write a new workflow YAML to the user directory."""
    name = args.get("name", "").strip()
    content = args.get("content", "")

    if not name:
        return [TextContent(type="text", text="Error: 'name' parameter is required.")]
    if not content:
        return [TextContent(type="text", text="Error: 'content' parameter is required.")]

    # Validate
    try:
        _validate_yaml(content)
    except Exception as exc:
        return [TextContent(type="text", text=f"Error: Invalid workflow YAML – {exc}")]

    dest = _ensure_user_dir() / (name + ".yaml")
    if dest.exists():
        return [
            TextContent(
                type="text",
                text=f"Error: Workflow '{name}' already exists in user dir. Use update_workflow to overwrite.",
            )
        ]

    dest.write_text(content, encoding="utf-8")
    return [TextContent(type="text", text=f"Created workflow '{name}' at: {dest}")]


def update_workflow_tool(args: dict) -> list:
    """Overwrite an existing user workflow. Cannot update bundled workflows."""
    name = args.get("name", "").strip()
    content = args.get("content", "")

    if not name:
        return [TextContent(type="text", text="Error: 'name' parameter is required.")]
    if not content:
        return [TextContent(type="text", text="Error: 'content' parameter is required.")]

    if name in _bundled_names() and name not in _user_names():
        return [
            TextContent(
                type="text",
                text=(
                    f"Error: '{name}' is a bundled workflow and cannot be updated. "
                    "Use create_workflow with a different name, or copy it first with "
                    "'skill-seekers workflows copy'."
                ),
            )
        ]

    # Validate
    try:
        _validate_yaml(content)
    except Exception as exc:
        return [TextContent(type="text", text=f"Error: Invalid workflow YAML – {exc}")]

    dest = _ensure_user_dir() / (name + ".yaml")
    dest.write_text(content, encoding="utf-8")
    return [TextContent(type="text", text=f"Updated workflow '{name}' at: {dest}")]


def delete_workflow_tool(args: dict) -> list:
    """Remove a user workflow by name. Bundled workflows cannot be deleted."""
    name = args.get("name", "").strip()
    if not name:
        return [TextContent(type="text", text="Error: 'name' parameter is required.")]

    if name in _bundled_names():
        return [
            TextContent(
                type="text",
                text=f"Error: '{name}' is a bundled workflow and cannot be deleted.",
            )
        ]

    for suffix in (".yaml", ".yml"):
        candidate = USER_WORKFLOWS_DIR / (name + suffix)
        if candidate.exists():
            candidate.unlink()
            return [TextContent(type="text", text=f"Deleted user workflow: {candidate}")]

    return [TextContent(type="text", text=f"Error: User workflow '{name}' not found.")]
