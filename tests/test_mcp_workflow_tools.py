"""Tests for MCP workflow tool implementations (workflow_tools.py).

Covers all 5 tools:
  - list_workflows_tool
  - get_workflow_tool
  - create_workflow_tool
  - update_workflow_tool
  - delete_workflow_tool
"""

from __future__ import annotations

import pytest
import yaml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_WORKFLOW_YAML = """\
name: test-workflow
description: A test workflow
version: "1.0"
stages:
  - name: step_one
    type: builtin
    target: patterns
    enabled: true
"""

INVALID_WORKFLOW_YAML = """\
name: bad-workflow
description: Missing stages key
"""

NOT_YAML = "{{{{invalid yaml::::"


def _text(result_list) -> str:
    """Extract text from the first TextContent element."""
    return result_list[0].text


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def user_dir(tmp_path, monkeypatch):
    """Redirect USER_WORKFLOWS_DIR to a temp path for each test."""
    fake_dir = tmp_path / "user_workflows"
    monkeypatch.setattr(
        "skill_seekers.mcp.tools.workflow_tools.USER_WORKFLOWS_DIR",
        fake_dir,
    )
    return fake_dir


@pytest.fixture()
def bundled_names_empty(monkeypatch):
    """Stub _bundled_names() to return an empty list."""
    monkeypatch.setattr(
        "skill_seekers.mcp.tools.workflow_tools._bundled_names",
        lambda: [],
    )


@pytest.fixture()
def bundled_fixture(monkeypatch):
    """Stub _bundled_names() and _read_bundled() with two fake bundled workflows."""
    bundled = {
        "default": VALID_WORKFLOW_YAML,
        "minimal": "name: minimal\ndescription: Minimal workflow\nstages: []\n",
    }
    monkeypatch.setattr(
        "skill_seekers.mcp.tools.workflow_tools._bundled_names",
        lambda: sorted(bundled.keys()),
    )
    monkeypatch.setattr(
        "skill_seekers.mcp.tools.workflow_tools._read_bundled",
        lambda _name: bundled.get(_name),
    )


# ---------------------------------------------------------------------------
# list_workflows_tool
# ---------------------------------------------------------------------------


class TestListWorkflowsTool:
    def test_empty_returns_empty_list(self, user_dir, bundled_names_empty, monkeypatch):
        monkeypatch.setattr(
            "skill_seekers.mcp.tools.workflow_tools._read_bundled",
            lambda _name: None,
        )
        from skill_seekers.mcp.tools.workflow_tools import list_workflows_tool

        result = list_workflows_tool({})
        assert len(result) == 1
        parsed = yaml.safe_load(_text(result))
        assert parsed == []

    def test_returns_bundled_workflows(self, user_dir, bundled_fixture):
        from skill_seekers.mcp.tools.workflow_tools import list_workflows_tool

        result = list_workflows_tool({})
        parsed = yaml.safe_load(_text(result))
        names = [item["name"] for item in parsed]
        assert "default" in names
        assert "minimal" in names

    def test_bundled_source_label(self, user_dir, bundled_fixture):
        from skill_seekers.mcp.tools.workflow_tools import list_workflows_tool

        result = list_workflows_tool({})
        parsed = yaml.safe_load(_text(result))
        for item in parsed:
            assert item["source"] == "bundled"

    def test_returns_user_workflows(self, user_dir, bundled_names_empty, monkeypatch):
        monkeypatch.setattr(
            "skill_seekers.mcp.tools.workflow_tools._read_bundled",
            lambda _name: None,
        )
        user_dir.mkdir(parents=True)
        (user_dir / "my-workflow.yaml").write_text(VALID_WORKFLOW_YAML, encoding="utf-8")

        from skill_seekers.mcp.tools.workflow_tools import list_workflows_tool

        result = list_workflows_tool({})
        parsed = yaml.safe_load(_text(result))
        assert any(item["name"] == "my-workflow" and item["source"] == "user" for item in parsed)

    def test_user_and_bundled_combined(self, user_dir, bundled_fixture):
        user_dir.mkdir(parents=True)
        (user_dir / "custom.yaml").write_text(VALID_WORKFLOW_YAML, encoding="utf-8")

        from skill_seekers.mcp.tools.workflow_tools import list_workflows_tool

        result = list_workflows_tool({})
        parsed = yaml.safe_load(_text(result))
        sources = {item["source"] for item in parsed}
        assert "bundled" in sources
        assert "user" in sources

    def test_descriptions_extracted(self, user_dir, bundled_fixture):
        from skill_seekers.mcp.tools.workflow_tools import list_workflows_tool

        result = list_workflows_tool({})
        parsed = yaml.safe_load(_text(result))
        default_entry = next(p for p in parsed if p["name"] == "default")
        assert default_entry["description"] == "A test workflow"

    def test_ignores_args_parameter(self, user_dir, bundled_names_empty, monkeypatch):
        monkeypatch.setattr(
            "skill_seekers.mcp.tools.workflow_tools._read_bundled",
            lambda _name: None,
        )
        from skill_seekers.mcp.tools.workflow_tools import list_workflows_tool

        # Tool accepts _args but ignores it
        result = list_workflows_tool({"extra": "ignored"})
        assert len(result) == 1


# ---------------------------------------------------------------------------
# get_workflow_tool
# ---------------------------------------------------------------------------


class TestGetWorkflowTool:
    def test_missing_name_returns_error(self, user_dir, bundled_names_empty, monkeypatch):
        monkeypatch.setattr(
            "skill_seekers.mcp.tools.workflow_tools._read_bundled",
            lambda _name: None,
        )
        from skill_seekers.mcp.tools.workflow_tools import get_workflow_tool

        result = get_workflow_tool({})
        assert "Error" in _text(result)
        assert "'name'" in _text(result)

    def test_empty_name_returns_error(self, user_dir, bundled_names_empty, monkeypatch):
        monkeypatch.setattr(
            "skill_seekers.mcp.tools.workflow_tools._read_bundled",
            lambda _name: None,
        )
        from skill_seekers.mcp.tools.workflow_tools import get_workflow_tool

        result = get_workflow_tool({"name": "  "})
        assert "Error" in _text(result)

    def test_not_found_returns_error_with_available(self, user_dir, bundled_fixture):
        from skill_seekers.mcp.tools.workflow_tools import get_workflow_tool

        result = get_workflow_tool({"name": "nonexistent"})
        text = _text(result)
        assert "not found" in text.lower()
        assert "default" in text or "minimal" in text

    def test_returns_bundled_content(self, user_dir, bundled_fixture):
        from skill_seekers.mcp.tools.workflow_tools import get_workflow_tool

        result = get_workflow_tool({"name": "default"})
        text = _text(result)
        assert "stages" in text

    def test_returns_user_workflow_content(self, user_dir, bundled_names_empty, monkeypatch):
        monkeypatch.setattr(
            "skill_seekers.mcp.tools.workflow_tools._read_bundled",
            lambda _name: None,
        )
        user_dir.mkdir(parents=True)
        (user_dir / "my-wf.yaml").write_text(VALID_WORKFLOW_YAML, encoding="utf-8")

        from skill_seekers.mcp.tools.workflow_tools import get_workflow_tool

        result = get_workflow_tool({"name": "my-wf"})
        assert "stages" in _text(result)

    def test_user_dir_takes_priority_over_bundled(self, user_dir, bundled_fixture):
        """User directory version shadows bundled workflow with same name."""
        user_dir.mkdir(parents=True)
        user_content = "name: default\ndescription: USER VERSION\nstages:\n  - name: x\n    type: builtin\n    target: y\n    enabled: true\n"
        (user_dir / "default.yaml").write_text(user_content, encoding="utf-8")

        from skill_seekers.mcp.tools.workflow_tools import get_workflow_tool

        result = get_workflow_tool({"name": "default"})
        assert "USER VERSION" in _text(result)

    def test_not_found_no_available_shows_none(self, user_dir, bundled_names_empty, monkeypatch):
        monkeypatch.setattr(
            "skill_seekers.mcp.tools.workflow_tools._read_bundled",
            lambda _name: None,
        )
        from skill_seekers.mcp.tools.workflow_tools import get_workflow_tool

        result = get_workflow_tool({"name": "missing"})
        assert "none" in _text(result).lower() or "not found" in _text(result).lower()


# ---------------------------------------------------------------------------
# create_workflow_tool
# ---------------------------------------------------------------------------


class TestCreateWorkflowTool:
    def test_missing_name_returns_error(self, user_dir):
        from skill_seekers.mcp.tools.workflow_tools import create_workflow_tool

        result = create_workflow_tool({"content": VALID_WORKFLOW_YAML})
        assert "Error" in _text(result)
        assert "'name'" in _text(result)

    def test_missing_content_returns_error(self, user_dir):
        from skill_seekers.mcp.tools.workflow_tools import create_workflow_tool

        result = create_workflow_tool({"name": "new-wf"})
        assert "Error" in _text(result)
        assert "'content'" in _text(result)

    def test_invalid_yaml_returns_error(self, user_dir):
        from skill_seekers.mcp.tools.workflow_tools import create_workflow_tool

        result = create_workflow_tool({"name": "new-wf", "content": NOT_YAML})
        assert "Error" in _text(result)

    def test_missing_stages_returns_error(self, user_dir):
        from skill_seekers.mcp.tools.workflow_tools import create_workflow_tool

        result = create_workflow_tool({"name": "new-wf", "content": INVALID_WORKFLOW_YAML})
        assert "Error" in _text(result)
        assert "stages" in _text(result)

    def test_creates_file_in_user_dir(self, user_dir):
        from skill_seekers.mcp.tools.workflow_tools import create_workflow_tool

        result = create_workflow_tool({"name": "new-wf", "content": VALID_WORKFLOW_YAML})
        assert "Error" not in _text(result)
        assert (user_dir / "new-wf.yaml").exists()

    def test_created_file_contains_content(self, user_dir):
        from skill_seekers.mcp.tools.workflow_tools import create_workflow_tool

        create_workflow_tool({"name": "new-wf", "content": VALID_WORKFLOW_YAML})
        content = (user_dir / "new-wf.yaml").read_text(encoding="utf-8")
        assert "stages" in content

    def test_duplicate_name_returns_error(self, user_dir):
        from skill_seekers.mcp.tools.workflow_tools import create_workflow_tool

        create_workflow_tool({"name": "dup-wf", "content": VALID_WORKFLOW_YAML})
        result = create_workflow_tool({"name": "dup-wf", "content": VALID_WORKFLOW_YAML})
        assert "Error" in _text(result)
        assert "already exists" in _text(result)

    def test_success_message_contains_name(self, user_dir):
        from skill_seekers.mcp.tools.workflow_tools import create_workflow_tool

        result = create_workflow_tool({"name": "my-new-wf", "content": VALID_WORKFLOW_YAML})
        assert "my-new-wf" in _text(result)

    def test_creates_user_dir_if_missing(self, tmp_path, monkeypatch):
        fake_dir = tmp_path / "nonexistent_user_dir"
        monkeypatch.setattr(
            "skill_seekers.mcp.tools.workflow_tools.USER_WORKFLOWS_DIR",
            fake_dir,
        )
        from skill_seekers.mcp.tools.workflow_tools import create_workflow_tool

        result = create_workflow_tool({"name": "auto-dir", "content": VALID_WORKFLOW_YAML})
        assert "Error" not in _text(result)
        assert fake_dir.exists()


# ---------------------------------------------------------------------------
# update_workflow_tool
# ---------------------------------------------------------------------------


class TestUpdateWorkflowTool:
    def test_missing_name_returns_error(self, user_dir):
        from skill_seekers.mcp.tools.workflow_tools import update_workflow_tool

        result = update_workflow_tool({"content": VALID_WORKFLOW_YAML})
        assert "Error" in _text(result)
        assert "'name'" in _text(result)

    def test_missing_content_returns_error(self, user_dir):
        from skill_seekers.mcp.tools.workflow_tools import update_workflow_tool

        result = update_workflow_tool({"name": "some-wf"})
        assert "Error" in _text(result)
        assert "'content'" in _text(result)

    def test_invalid_yaml_returns_error(self, user_dir):
        from skill_seekers.mcp.tools.workflow_tools import update_workflow_tool

        result = update_workflow_tool({"name": "some-wf", "content": NOT_YAML})
        assert "Error" in _text(result)

    def test_missing_stages_returns_error(self, user_dir):
        from skill_seekers.mcp.tools.workflow_tools import update_workflow_tool

        result = update_workflow_tool({"name": "some-wf", "content": INVALID_WORKFLOW_YAML})
        assert "Error" in _text(result)

    def test_cannot_update_bundled_only(self, user_dir, bundled_fixture):
        """Bundled-only workflow (not in user dir) cannot be updated."""
        from skill_seekers.mcp.tools.workflow_tools import update_workflow_tool

        result = update_workflow_tool({"name": "default", "content": VALID_WORKFLOW_YAML})
        assert "Error" in _text(result)
        assert "bundled" in _text(result)

    def test_updates_existing_user_workflow(self, user_dir, bundled_names_empty, monkeypatch):
        monkeypatch.setattr(
            "skill_seekers.mcp.tools.workflow_tools._read_bundled",
            lambda _name: None,
        )
        user_dir.mkdir(parents=True)
        (user_dir / "existing.yaml").write_text(VALID_WORKFLOW_YAML, encoding="utf-8")

        updated_content = VALID_WORKFLOW_YAML.replace("A test workflow", "Updated description")
        from skill_seekers.mcp.tools.workflow_tools import update_workflow_tool

        result = update_workflow_tool({"name": "existing", "content": updated_content})
        assert "Error" not in _text(result)
        written = (user_dir / "existing.yaml").read_text(encoding="utf-8")
        assert "Updated description" in written

    def test_can_update_user_copy_of_bundled(self, user_dir, bundled_fixture):
        """User copy of bundled workflow CAN be updated."""
        user_dir.mkdir(parents=True)
        (user_dir / "default.yaml").write_text(VALID_WORKFLOW_YAML, encoding="utf-8")

        updated = VALID_WORKFLOW_YAML.replace("A test workflow", "My custom default")
        from skill_seekers.mcp.tools.workflow_tools import update_workflow_tool

        result = update_workflow_tool({"name": "default", "content": updated})
        assert "Error" not in _text(result)

    def test_success_message_contains_name(self, user_dir, bundled_names_empty, monkeypatch):
        monkeypatch.setattr(
            "skill_seekers.mcp.tools.workflow_tools._read_bundled",
            lambda _name: None,
        )
        user_dir.mkdir(parents=True)
        (user_dir / "my-wf.yaml").write_text(VALID_WORKFLOW_YAML, encoding="utf-8")

        from skill_seekers.mcp.tools.workflow_tools import update_workflow_tool

        result = update_workflow_tool({"name": "my-wf", "content": VALID_WORKFLOW_YAML})
        assert "my-wf" in _text(result)


# ---------------------------------------------------------------------------
# delete_workflow_tool
# ---------------------------------------------------------------------------


class TestDeleteWorkflowTool:
    def test_missing_name_returns_error(self, user_dir):
        from skill_seekers.mcp.tools.workflow_tools import delete_workflow_tool

        result = delete_workflow_tool({})
        assert "Error" in _text(result)
        assert "'name'" in _text(result)

    def test_empty_name_returns_error(self, user_dir):
        from skill_seekers.mcp.tools.workflow_tools import delete_workflow_tool

        result = delete_workflow_tool({"name": "   "})
        assert "Error" in _text(result)

    def test_cannot_delete_bundled(self, user_dir, bundled_fixture):
        from skill_seekers.mcp.tools.workflow_tools import delete_workflow_tool

        result = delete_workflow_tool({"name": "default"})
        assert "Error" in _text(result)
        assert "bundled" in _text(result)

    def test_not_found_user_workflow_returns_error(
        self, user_dir, bundled_names_empty, monkeypatch
    ):
        monkeypatch.setattr(
            "skill_seekers.mcp.tools.workflow_tools._read_bundled",
            lambda _name: None,
        )
        from skill_seekers.mcp.tools.workflow_tools import delete_workflow_tool

        result = delete_workflow_tool({"name": "no-such-wf"})
        assert "Error" in _text(result)
        assert "not found" in _text(result).lower()

    def test_deletes_user_yaml_file(self, user_dir, bundled_names_empty, monkeypatch):
        monkeypatch.setattr(
            "skill_seekers.mcp.tools.workflow_tools._read_bundled",
            lambda _name: None,
        )
        user_dir.mkdir(parents=True)
        wf_file = user_dir / "to-delete.yaml"
        wf_file.write_text(VALID_WORKFLOW_YAML, encoding="utf-8")

        from skill_seekers.mcp.tools.workflow_tools import delete_workflow_tool

        result = delete_workflow_tool({"name": "to-delete"})
        assert "Error" not in _text(result)
        assert not wf_file.exists()

    def test_deletes_user_yml_extension(self, user_dir, bundled_names_empty, monkeypatch):
        monkeypatch.setattr(
            "skill_seekers.mcp.tools.workflow_tools._read_bundled",
            lambda _name: None,
        )
        user_dir.mkdir(parents=True)
        wf_file = user_dir / "to-delete.yml"
        wf_file.write_text(VALID_WORKFLOW_YAML, encoding="utf-8")

        from skill_seekers.mcp.tools.workflow_tools import delete_workflow_tool

        result = delete_workflow_tool({"name": "to-delete"})
        assert "Error" not in _text(result)
        assert not wf_file.exists()

    def test_success_message_contains_path(self, user_dir, bundled_names_empty, monkeypatch):
        monkeypatch.setattr(
            "skill_seekers.mcp.tools.workflow_tools._read_bundled",
            lambda _name: None,
        )
        user_dir.mkdir(parents=True)
        (user_dir / "bye.yaml").write_text(VALID_WORKFLOW_YAML, encoding="utf-8")

        from skill_seekers.mcp.tools.workflow_tools import delete_workflow_tool

        result = delete_workflow_tool({"name": "bye"})
        assert "bye" in _text(result)


# ---------------------------------------------------------------------------
# Round-trip: create → get → update → delete
# ---------------------------------------------------------------------------


class TestWorkflowRoundTrip:
    def test_full_lifecycle(self, user_dir, bundled_names_empty, monkeypatch):
        """Create → list → get → update → delete a workflow end-to-end."""
        monkeypatch.setattr(
            "skill_seekers.mcp.tools.workflow_tools._read_bundled",
            lambda _name: None,
        )
        from skill_seekers.mcp.tools.workflow_tools import (
            create_workflow_tool,
            delete_workflow_tool,
            get_workflow_tool,
            list_workflows_tool,
            update_workflow_tool,
        )

        # 1. Create
        r = create_workflow_tool({"name": "lifecycle", "content": VALID_WORKFLOW_YAML})
        assert "Error" not in _text(r)

        # 2. List — should appear with source=user
        r = list_workflows_tool({})
        parsed = yaml.safe_load(_text(r))
        assert any(p["name"] == "lifecycle" and p["source"] == "user" for p in parsed)

        # 3. Get — returns content
        r = get_workflow_tool({"name": "lifecycle"})
        assert "stages" in _text(r)

        # 4. Update
        updated = VALID_WORKFLOW_YAML.replace("A test workflow", "Updated in lifecycle test")
        r = update_workflow_tool({"name": "lifecycle", "content": updated})
        assert "Error" not in _text(r)
        r = get_workflow_tool({"name": "lifecycle"})
        assert "Updated in lifecycle test" in _text(r)

        # 5. Delete
        r = delete_workflow_tool({"name": "lifecycle"})
        assert "Error" not in _text(r)

        # 6. Get after delete — error
        r = get_workflow_tool({"name": "lifecycle"})
        assert "not found" in _text(r).lower()
