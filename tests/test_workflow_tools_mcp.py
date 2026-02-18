"""Tests for the workflow MCP tools.

Covers:
- list_workflows_tool
- get_workflow_tool
- create_workflow_tool
- update_workflow_tool
- delete_workflow_tool
"""

import textwrap
from unittest.mock import patch

import pytest
import yaml


MINIMAL_YAML = textwrap.dedent("""\
    name: test-workflow
    description: A test workflow
    version: "1.0"
    applies_to:
      - codebase_analysis
    variables: {}
    stages:
      - name: step1
        type: custom
        target: all
        uses_history: false
        enabled: true
        prompt: "Do something useful."
    post_process:
      reorder_sections: []
      add_metadata: {}
""")

INVALID_YAML_NO_STAGES = textwrap.dedent("""\
    name: broken
    description: Missing stages key
    version: "1.0"
""")


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures & helpers
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def tmp_user_dir(tmp_path, monkeypatch):
    """Redirect USER_WORKFLOWS_DIR in workflow_tools to a temp dir."""
    fake_dir = tmp_path / "workflows"
    fake_dir.mkdir()
    monkeypatch.setattr("skill_seekers.mcp.tools.workflow_tools.USER_WORKFLOWS_DIR", fake_dir)
    return fake_dir


def _mock_bundled_names(names=("default", "security-focus")):
    return patch(
        "skill_seekers.mcp.tools.workflow_tools._bundled_names",
        return_value=list(names),
    )


def _mock_bundled_text(mapping: dict):
    def _read(name):
        return mapping.get(name)

    return patch(
        "skill_seekers.mcp.tools.workflow_tools._read_bundled",
        side_effect=_read,
    )


def _text(result) -> str:
    """Extract text from first TextContent in result."""
    if isinstance(result, list) and result:
        item = result[0]
        return item.text if hasattr(item, "text") else str(item)
    return str(result)


# ─────────────────────────────────────────────────────────────────────────────
# list_workflows_tool
# ─────────────────────────────────────────────────────────────────────────────


class TestListWorkflowsTool:
    def test_lists_bundled_and_user(self, tmp_user_dir):
        from skill_seekers.mcp.tools.workflow_tools import list_workflows_tool

        (tmp_user_dir / "my-workflow.yaml").write_text(MINIMAL_YAML, encoding="utf-8")

        bundled_map = {"default": MINIMAL_YAML}
        with _mock_bundled_names(["default"]), _mock_bundled_text(bundled_map):
            result = list_workflows_tool({})

        text = _text(result)
        assert "default" in text
        assert "bundled" in text
        assert "my-workflow" in text
        assert "user" in text

    def test_empty_lists(self, tmp_user_dir):
        from skill_seekers.mcp.tools.workflow_tools import list_workflows_tool

        with _mock_bundled_names([]):
            result = list_workflows_tool({})

        text = _text(result)
        # Should return a valid (possibly empty) YAML list or empty
        data = yaml.safe_load(text)
        assert isinstance(data, (list, type(None)))


# ─────────────────────────────────────────────────────────────────────────────
# get_workflow_tool
# ─────────────────────────────────────────────────────────────────────────────


class TestGetWorkflowTool:
    def test_get_bundled(self):
        from skill_seekers.mcp.tools.workflow_tools import get_workflow_tool

        with patch(
            "skill_seekers.mcp.tools.workflow_tools._read_workflow",
            return_value=MINIMAL_YAML,
        ):
            result = get_workflow_tool({"name": "default"})

        assert "stages" in _text(result)

    def test_get_not_found(self, tmp_user_dir):
        from skill_seekers.mcp.tools.workflow_tools import get_workflow_tool

        with _mock_bundled_names([]):
            result = get_workflow_tool({"name": "ghost"})

        text = _text(result)
        assert "not found" in text.lower() or "Error" in text

    def test_missing_name_param(self):
        from skill_seekers.mcp.tools.workflow_tools import get_workflow_tool

        result = get_workflow_tool({})
        assert "required" in _text(result).lower()

    def test_get_user_workflow(self, tmp_user_dir):
        from skill_seekers.mcp.tools.workflow_tools import get_workflow_tool

        (tmp_user_dir / "custom.yaml").write_text(MINIMAL_YAML, encoding="utf-8")
        result = get_workflow_tool({"name": "custom"})
        assert "stages" in _text(result)


# ─────────────────────────────────────────────────────────────────────────────
# create_workflow_tool
# ─────────────────────────────────────────────────────────────────────────────


class TestCreateWorkflowTool:
    def test_create_new_workflow(self, tmp_user_dir):
        from skill_seekers.mcp.tools.workflow_tools import create_workflow_tool

        result = create_workflow_tool({"name": "new-wf", "content": MINIMAL_YAML})
        text = _text(result)
        assert "Created" in text or "created" in text.lower()
        assert (tmp_user_dir / "new-wf.yaml").exists()

    def test_create_duplicate_fails(self, tmp_user_dir):
        from skill_seekers.mcp.tools.workflow_tools import create_workflow_tool

        (tmp_user_dir / "existing.yaml").write_text(MINIMAL_YAML, encoding="utf-8")
        result = create_workflow_tool({"name": "existing", "content": MINIMAL_YAML})
        assert "already exists" in _text(result).lower()

    def test_create_invalid_yaml(self, tmp_user_dir):
        from skill_seekers.mcp.tools.workflow_tools import create_workflow_tool

        result = create_workflow_tool({"name": "bad", "content": INVALID_YAML_NO_STAGES})
        assert "invalid" in _text(result).lower() or "stages" in _text(result).lower()

    def test_create_missing_name(self):
        from skill_seekers.mcp.tools.workflow_tools import create_workflow_tool

        result = create_workflow_tool({"content": MINIMAL_YAML})
        assert "required" in _text(result).lower()

    def test_create_missing_content(self):
        from skill_seekers.mcp.tools.workflow_tools import create_workflow_tool

        result = create_workflow_tool({"name": "test"})
        assert "required" in _text(result).lower()


# ─────────────────────────────────────────────────────────────────────────────
# update_workflow_tool
# ─────────────────────────────────────────────────────────────────────────────


class TestUpdateWorkflowTool:
    def test_update_user_workflow(self, tmp_user_dir):
        from skill_seekers.mcp.tools.workflow_tools import update_workflow_tool

        (tmp_user_dir / "my-wf.yaml").write_text("old content", encoding="utf-8")

        with _mock_bundled_names([]):
            result = update_workflow_tool({"name": "my-wf", "content": MINIMAL_YAML})

        text = _text(result)
        assert "Updated" in text or "updated" in text.lower()
        assert (tmp_user_dir / "my-wf.yaml").read_text() == MINIMAL_YAML

    def test_update_bundled_refused(self, tmp_user_dir):
        from skill_seekers.mcp.tools.workflow_tools import update_workflow_tool

        with _mock_bundled_names(["default"]):
            result = update_workflow_tool({"name": "default", "content": MINIMAL_YAML})

        assert "bundled" in _text(result).lower()

    def test_update_invalid_yaml(self, tmp_user_dir):
        from skill_seekers.mcp.tools.workflow_tools import update_workflow_tool

        (tmp_user_dir / "my-wf.yaml").write_text(MINIMAL_YAML, encoding="utf-8")

        with _mock_bundled_names([]):
            result = update_workflow_tool({"name": "my-wf", "content": INVALID_YAML_NO_STAGES})

        assert "invalid" in _text(result).lower() or "stages" in _text(result).lower()

    def test_update_user_override_of_bundled_name(self, tmp_user_dir):
        """A user workflow with same name as bundled should be updatable."""
        from skill_seekers.mcp.tools.workflow_tools import update_workflow_tool

        (tmp_user_dir / "default.yaml").write_text("old", encoding="utf-8")

        with _mock_bundled_names(["default"]):
            result = update_workflow_tool({"name": "default", "content": MINIMAL_YAML})

        text = _text(result)
        # User has a file named 'default', so it should succeed
        assert "Updated" in text or "updated" in text.lower()


# ─────────────────────────────────────────────────────────────────────────────
# delete_workflow_tool
# ─────────────────────────────────────────────────────────────────────────────


class TestDeleteWorkflowTool:
    def test_delete_user_workflow(self, tmp_user_dir):
        from skill_seekers.mcp.tools.workflow_tools import delete_workflow_tool

        wf = tmp_user_dir / "to-delete.yaml"
        wf.write_text(MINIMAL_YAML, encoding="utf-8")

        with _mock_bundled_names([]):
            result = delete_workflow_tool({"name": "to-delete"})

        assert "Deleted" in _text(result) or "deleted" in _text(result).lower()
        assert not wf.exists()

    def test_delete_bundled_refused(self, tmp_user_dir):
        from skill_seekers.mcp.tools.workflow_tools import delete_workflow_tool

        with _mock_bundled_names(["default"]):
            result = delete_workflow_tool({"name": "default"})

        assert "bundled" in _text(result).lower()

    def test_delete_nonexistent(self, tmp_user_dir):
        from skill_seekers.mcp.tools.workflow_tools import delete_workflow_tool

        with _mock_bundled_names([]):
            result = delete_workflow_tool({"name": "ghost"})

        assert "not found" in _text(result).lower()

    def test_delete_yml_extension(self, tmp_user_dir):
        from skill_seekers.mcp.tools.workflow_tools import delete_workflow_tool

        wf = tmp_user_dir / "my-wf.yml"
        wf.write_text(MINIMAL_YAML, encoding="utf-8")

        with _mock_bundled_names([]):
            delete_workflow_tool({"name": "my-wf"})

        assert not wf.exists()

    def test_delete_missing_name(self):
        from skill_seekers.mcp.tools.workflow_tools import delete_workflow_tool

        result = delete_workflow_tool({})
        assert "required" in _text(result).lower()
